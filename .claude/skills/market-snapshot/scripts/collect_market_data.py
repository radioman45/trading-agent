# -*- coding: utf-8 -*-
"""시장 데이터 수집 + 기술지표 계산 스크립트.

market-data-engineer 에이전트가 스냅샷 작성 시 사용한다.
yfinance로 일봉 OHLCV(기본 1년)를 받아 CSV로 저장하고,
기술지표(SMA/EMA/MACD/RSI/볼린저/ATR/수익률/낙폭)를 JSON으로 출력한다.

사용법:
  python collect_market_data.py --ticker NVDA --out-dir _workspace
  python collect_market_data.py --ticker 005930 --out-dir _workspace   # 한국 6자리 → .KS/.KQ 자동 시도
  python collect_market_data.py --from-csv _workspace/00_ohlcv_daily.csv --out-dir _workspace  # 수동 CSV로 지표만 재계산

출력:
  {out-dir}/00_ohlcv_daily.csv   — 일봉 OHLCV
  {out-dir}/00_indicators.json   — 기술지표 + 기본 시세 정보
종료 코드: 0=성공, 1=수집 실패(지표 미계산), 2=인자 오류
모든 진단은 stdout 한 줄 JSON으로도 보고한다 (status: ok|error).
"""
import argparse
import json
import math
import sys
from datetime import date
from pathlib import Path

import pandas as pd


def _round(v, n=4):
    if v is None:
        return None
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    if math.isnan(f) or math.isinf(f):
        return None
    return round(f, n)


def fetch_ohlcv(ticker: str, period: str):
    """yfinance로 OHLCV를 받는다. 한국 6자리 코드면 .KS → .KQ 순서로 시도."""
    import yfinance as yf

    candidates = [ticker]
    if ticker.isdigit() and len(ticker) == 6:
        candidates = [f"{ticker}.KS", f"{ticker}.KQ"]

    last_err = None
    for sym in candidates:
        try:
            t = yf.Ticker(sym)
            df = t.history(period=period, interval="1d", auto_adjust=False)
            if df is not None and not df.empty and len(df) >= 30:
                return sym, t, df
            last_err = f"{sym}: 데이터 없음 또는 30일 미만 ({0 if df is None else len(df)}행)"
        except Exception as e:  # noqa: BLE001 — 후보별 실패는 다음 후보로
            last_err = f"{sym}: {e}"
    raise RuntimeError(f"OHLCV 수집 실패 — {last_err}")


def fast_info_dict(t):
    """yfinance fast_info에서 스냅샷에 유용한 기본 시세값만 추출 (실패 시 None)."""
    out = {}
    try:
        fi = t.fast_info
        for key, attr in [
            ("last_price", "last_price"),
            ("market_cap", "market_cap"),
            ("shares_outstanding", "shares"),
            ("year_high", "year_high"),
            ("year_low", "year_low"),
            ("currency", "currency"),
            ("exchange", "exchange"),
        ]:
            try:
                out[key] = getattr(fi, attr)
            except Exception:  # noqa: BLE001
                out[key] = None
    except Exception:  # noqa: BLE001
        return {}
    return {k: (v if isinstance(v, str) or v is None else _round(v)) for k, v in out.items()}


def compute_indicators(df: pd.DataFrame) -> dict:
    """일봉 DataFrame(Open/High/Low/Close/Volume)으로 기술지표를 계산한다."""
    close = df["Close"].astype(float)
    high = df["High"].astype(float)
    low = df["Low"].astype(float)
    vol = df["Volume"].astype(float)
    last = close.iloc[-1]

    # 이동평균
    sma = {n: close.rolling(n).mean().iloc[-1] for n in (20, 50, 200)}
    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()

    # VWMA(20) — 거래량 가중 이동평균 (거래량 0 구간은 _round가 inf/nan을 None 처리)
    vwma20 = ((close * vol).rolling(20).sum() / vol.rolling(20).sum()).iloc[-1]

    # MACD(12,26,9)
    macd_line = ema12 - ema26
    signal = macd_line.ewm(span=9, adjust=False).mean()
    hist = macd_line - signal

    # RSI(14) — Wilder 방식
    delta = close.diff()
    gain = delta.clip(lower=0).ewm(alpha=1 / 14, adjust=False).mean()
    loss = (-delta.clip(upper=0)).ewm(alpha=1 / 14, adjust=False).mean()
    rs = gain / loss.replace(0, float("nan"))
    rsi = (100 - 100 / (1 + rs)).iloc[-1]

    # 볼린저(20, 2σ)
    mid = close.rolling(20).mean().iloc[-1]
    std = close.rolling(20).std().iloc[-1]
    bb_upper, bb_lower = mid + 2 * std, mid - 2 * std
    bb_pos = (last - bb_lower) / (bb_upper - bb_lower) if bb_upper != bb_lower else None

    # ATR(14) — Wilder 방식
    tr = pd.concat(
        [high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1
    ).max(axis=1)
    atr = tr.ewm(alpha=1 / 14, adjust=False).mean().iloc[-1]

    # 기간 수익률 — 데이터가 살짝 모자라면(영업일 수 편차) 첫 행으로 근사
    def ret(days):
        if len(close) > days:
            return (last / close.iloc[-1 - days] - 1) * 100
        if len(close) >= days * 0.9:
            return (last / close.iloc[0] - 1) * 100
        return None

    # 최대 낙폭 (수집 기간 내)
    cummax = close.cummax()
    max_dd = ((close / cummax) - 1).min() * 100

    # 52주 고저 (수집 기간 기준)
    hi52, lo52 = close.max(), close.min()

    return {
        "last_close": _round(last),
        "last_date": str(df.index[-1].date()),
        "rows": len(df),
        "sma": {f"sma{n}": _round(v) for n, v in sma.items()},
        "price_vs_sma_pct": {
            f"sma{n}": _round((last / v - 1) * 100, 2) if v and not math.isnan(v) else None
            for n, v in sma.items()
        },
        "vwma20": _round(vwma20),
        "macd": {
            "line": _round(macd_line.iloc[-1]),
            "signal": _round(signal.iloc[-1]),
            "histogram": _round(hist.iloc[-1]),
            "cross": "golden" if hist.iloc[-1] > 0 >= hist.iloc[-2] else
                     "dead" if hist.iloc[-1] < 0 <= hist.iloc[-2] else "none",
        },
        "rsi14": _round(rsi, 2),
        "bollinger": {
            "upper": _round(bb_upper), "mid": _round(mid), "lower": _round(bb_lower),
            "position_0to1": _round(bb_pos, 3),
        },
        "atr14": _round(atr),
        "atr14_pct_of_price": _round(atr / last * 100, 2) if last else None,
        "returns_pct": {
            "1w": _round(ret(5), 2), "1m": _round(ret(21), 2), "3m": _round(ret(63), 2),
            "6m": _round(ret(126), 2), "1y": _round(ret(252), 2),
        },
        "max_drawdown_pct": _round(max_dd, 2),
        "high_52w": _round(hi52), "low_52w": _round(lo52),
        "pct_from_52w_high": _round((last / hi52 - 1) * 100, 2),
        "volume": {
            "last": _round(vol.iloc[-1], 0),
            "avg20": _round(vol.rolling(20).mean().iloc[-1], 0),
            "last_vs_avg20": _round(vol.iloc[-1] / vol.rolling(20).mean().iloc[-1], 2)
            if vol.rolling(20).mean().iloc[-1] else None,
        },
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ticker", help="티커 (예: NVDA, 005930, 005930.KS)")
    ap.add_argument("--from-csv", help="기존 OHLCV CSV로 지표만 계산 (yfinance 생략)")
    ap.add_argument("--period", default="1y", help="수집 기간 (기본 1y, 예: 2y)")
    ap.add_argument("--out-dir", default="_workspace", help="출력 디렉토리")
    args = ap.parse_args()

    if not args.ticker and not args.from_csv:
        print(json.dumps({"status": "error", "error": "--ticker 또는 --from-csv 필요"}, ensure_ascii=False))
        sys.exit(2)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "00_ohlcv_daily.csv"
    json_path = out_dir / "00_indicators.json"

    meta = {"as_of": str(date.today()), "source": None, "ticker_resolved": None, "fast_info": {}}

    try:
        if args.from_csv:
            df = pd.read_csv(args.from_csv, index_col=0, parse_dates=True)
            meta["source"] = f"manual_csv:{args.from_csv}"
            meta["ticker_resolved"] = args.ticker or "unknown"
        else:
            sym, t, df = fetch_ohlcv(args.ticker, args.period)
            df.to_csv(csv_path, encoding="utf-8")
            meta["source"] = "yfinance"
            meta["ticker_resolved"] = sym
            meta["fast_info"] = fast_info_dict(t)
    except Exception as e:  # noqa: BLE001 — 수집 실패를 JSON으로 보고
        print(json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False))
        sys.exit(1)

    result = {"status": "ok", **meta, "indicators": compute_indicators(df)}
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "csv": str(csv_path), "json": str(json_path),
                      "ticker": meta["ticker_resolved"], "rows": result["indicators"]["rows"],
                      "last_close": result["indicators"]["last_close"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
