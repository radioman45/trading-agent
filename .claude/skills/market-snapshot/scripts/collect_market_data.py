# -*- coding: utf-8 -*-
"""시장 데이터 수집 + 기술지표 계산 스크립트.

market-data-engineer 에이전트가 스냅샷 작성 시 사용한다.
yfinance로 일봉 OHLCV(기본 1년)를 받아 CSV로 저장하고,
기술지표(SMA/EMA/MACD/RSI/볼린저/ATR/수익률/낙폭)를 JSON으로 출력한다.

수집 레이어 기계 판정 (2026-07-04, codex R4 반영 / 2026-07-05 CRYPTO 모드):
  - session 블록: 시장(KR/US/CRYPTO) 세션 상태를 코드로 판정해 기록한다 — LLM이 세션을 추정하지 않게 한다.
    KR/US = pre_open/regular/post_close/weekend, CRYPTO = always_open(24/7, UTC 일봉 마감 —
    당일 UTC 봉은 항상 미확정).
  - cross_check 블록: 미국 티커는 stooq→nasdaq, 크립토(USD/USDT 쿼트)는 coinbase→binance 체인과
    이중 소스 교차 검증(허용 오차 기본 1%), 불일치는 mismatch로 기록한다.
    한국 티커(skipped_kr)·비달러 쿼트 크립토(skipped_crypto_quote)는 LLM 레이어 교차 담당.
  - yfinance 전체 실패 시 미국 티커는 Stooq를 1차 소스로 자동 폴백하고 source_primary에 기록한다
    (크립토·한국 티커는 폴백 없음 — 클린 실패 후 에이전트 에러 핸들링).

사용법:
  python collect_market_data.py --ticker NVDA --out-dir _workspace
  python collect_market_data.py --ticker 005930 --out-dir _workspace   # 한국 6자리 → .KS/.KQ 자동 시도
  python collect_market_data.py --from-csv _workspace/00_ohlcv_daily.csv --market KR --out-dir _workspace  # 수동 CSV 재계산(--market 필수적 권장)
  옵션: --market {US,KR} (감지 무시 강제), --xcheck-tolerance 1.0, --no-xcheck,
        --now-utc 2026-07-04T05:00:00 (세션 판정 시각 주입 — 테스트·재현용)

출력:
  {out-dir}/00_ohlcv_daily.csv   — 일봉 OHLCV
  {out-dir}/00_indicators.json   — 기술지표 + 기본 시세 + session/cross_check 블록
종료 코드: 0=성공, 1=수집 실패(지표 미계산), 2=인자 오류
모든 진단은 stdout 한 줄 JSON으로도 보고한다 (status: ok|error).
"""
import argparse
import io
import json
import math
import sys
import urllib.request
from datetime import date, datetime, timedelta, timezone
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


# 크립토 쿼트 통화 집합 — yfinance 크립토 표기({BASE}-{QUOTE})의 QUOTE 판별용.
# BRK-B·BF-B 같은 미국 주식 클래스 표기(대시 뒤 1글자)는 통화 코드가 아니라서 걸러진다.
CRYPTO_QUOTES = {"USD", "USDT", "USDC", "KRW", "EUR", "JPY", "GBP", "AUD",
                 "CAD", "CHF", "CNY", "HKD", "SGD", "BTC", "ETH"}


def is_crypto_symbol(sym: str) -> bool:
    """yfinance 크립토 표기(BTC-USD, 1INCH-USD, ETH-KRW 등)인지 판별한다.
    base는 영숫자 허용(1INCH·0X 등 숫자 포함 토큰) — 단 최소 한 글자는 알파벳."""
    sym = (sym or "").upper()
    if "-" not in sym or "." in sym:
        return False
    base, quote = sym.rsplit("-", 1)
    return (quote in CRYPTO_QUOTES and base.isalnum() and 2 <= len(base) <= 6
            and any(c.isalpha() for c in base))


def detect_market(ticker: str, resolved: str = "") -> str:
    """티커 형태로 시장을 감지한다. .KS/.KQ 또는 6자리 숫자 = KR,
    {BASE}-{쿼트통화}(예 BTC-USD) = CRYPTO, 그 외 US."""
    sym = (resolved or ticker or "").upper()
    if sym.endswith(".KS") or sym.endswith(".KQ"):
        return "KR"
    if is_crypto_symbol(sym):
        return "CRYPTO"
    base = sym.split(".")[0]
    if base.isdigit() and len(base) == 6:
        return "KR"
    return "US"


def _nth_sunday(year: int, month: int, n: int) -> date:
    d = date(year, month, 1)
    first_sunday = 1 + (6 - d.weekday()) % 7  # Mon=0..Sun=6
    return date(year, month, first_sunday + 7 * (n - 1))


def _us_eastern_offset(now_utc: datetime) -> timedelta:
    """미국 동부 UTC 오프셋. DST = 3월 둘째 일요일 ~ 11월 첫째 일요일(현지 02:00 전환).
    전환 시각 ±수 시간의 경계 오차는 세션 판정 목적상 허용(calendar_status에 approx 명시)."""
    et_guess = (now_utc - timedelta(hours=5)).date()
    dst_start = _nth_sunday(et_guess.year, 3, 2)
    dst_end = _nth_sunday(et_guess.year, 11, 1)
    return timedelta(hours=-4) if dst_start <= et_guess < dst_end else timedelta(hours=-5)


def _prev_weekday(d: date) -> date:
    d -= timedelta(days=1)
    while d.weekday() >= 5:
        d -= timedelta(days=1)
    return d


def judge_session(market: str, now_utc: datetime, last_data_date) -> dict:
    """수집 시점의 시장 세션과 데이터 신선도를 기계 판정한다.

    휴장일 캘린더는 내장하지 않는다(외부 의존 없이 결정적으로 동작) — 대신
    expected_last_trading_date와의 격차를 stale_feed_suspect로 드러내고,
    calendar_status로 근사 한계를 정직하게 라벨링한다.

    CRYPTO는 24/7 시장이라 거래소 세션 개념이 없다 — 일봉은 UTC 자정 마감이며,
    당일 UTC 봉은 항상 진행 중(미확정)이다. weekend/pre_open/intraday_data_gap은 적용되지 않는다.
    """
    if market == "CRYPTO":
        local_date = now_utc.date()
        expected = local_date - timedelta(days=1)  # 마지막으로 마감된 UTC 일봉
        out = {
            "market": market,
            "tz": "UTC (24/7 continuous)",
            "requested_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "requested_at_local": now_utc.strftime("%Y-%m-%dT%H:%M"),
            "market_session": "always_open",
            "calendar_status": "continuous_24_7",
            "data_as_of": str(last_data_date) if last_data_date else None,
            "expected_last_trading_date": str(expected),
            "staleness_calendar_days": (local_date - last_data_date).days if last_data_date else None,
            "last_close_is_final": None,
            "stale_feed_suspect": None,
            "intraday_data_gap": None,  # 세션 개념 없음 — 지연은 stale_feed_suspect가 담당
        }
        if last_data_date:
            if last_data_date > local_date:
                out["staleness_calendar_days"] = None
                out["anomaly"] = "last_data_date가 판정 시각보다 미래 — now_utc 주입 값 확인 필요"
                return out
            # 당일 UTC 봉은 진행 중 — 마지막 행이 오늘이면 그 값은 확정 종가가 아니다
            out["last_close_is_final"] = last_data_date < local_date
            out["stale_feed_suspect"] = last_data_date < expected
        return out

    if market == "KR":
        offset, tz_label = timedelta(hours=9), "Asia/Seoul (UTC+9)"
        open_hm, close_hm = (9, 0), (15, 30)
    else:
        offset, tz_label = _us_eastern_offset(now_utc), "America/New_York (DST approx)"
        open_hm, close_hm = (9, 30), (16, 0)

    local = now_utc + offset
    local_date, hm = local.date(), (local.hour, local.minute)
    if local.weekday() >= 5:
        session = "weekend"
    elif hm < open_hm:
        session = "pre_open"
    elif hm < close_hm:
        session = "regular"
    else:
        session = "post_close"

    # 오늘 기준 "마지막으로 마감됐어야 할 거래일" (주말만 제외한 근사 — 휴장일이면 suspect가 뜬다)
    if local.weekday() >= 5:
        expected = _prev_weekday(local_date)
    elif session == "post_close":
        expected = local_date
    else:
        expected = _prev_weekday(local_date)

    out = {
        "market": market,
        "tz": tz_label,
        "requested_at_utc": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "requested_at_local": local.strftime("%Y-%m-%dT%H:%M"),
        "market_session": session,
        "calendar_status": "approx_no_holiday_calendar",
        "data_as_of": str(last_data_date) if last_data_date else None,
        "expected_last_trading_date": str(expected),
        "staleness_calendar_days": (local_date - last_data_date).days if last_data_date else None,
        "last_close_is_final": None,
        "stale_feed_suspect": None,
    }
    out["intraday_data_gap"] = None
    if last_data_date:
        if last_data_date > local_date:
            # 판정 시각보다 미래의 데이터 — 과거 --now-utc 주입 등. 신선도 판정은 무의미하므로 미판정 처리
            out["staleness_calendar_days"] = None
            out["anomaly"] = "last_data_date가 판정 시각보다 미래 — now_utc 주입 값 확인 필요"
            return out
        # 마지막 행이 오늘(현지)이고 장이 안 끝났으면 그 값은 확정 종가가 아니다 — SOL 사고 재발 방지의 핵심 필드
        out["last_close_is_final"] = (last_data_date < local_date) or (
            last_data_date == local_date and session == "post_close"
        )
        out["stale_feed_suspect"] = last_data_date < expected
        # 장중(regular)인데 당일 봉이 없으면 평일 휴장 또는 피드 미갱신 — 세션 라벨만 믿으면 안 되는 상태
        out["intraday_data_gap"] = last_data_date < local_date if session == "regular" else False
    return out


def _http_get(url: str, accept: str = "*/*", timeout: int = 20) -> str:
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)", "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", errors="replace")


def fetch_stooq_daily(symbol_base: str, full: bool = False) -> pd.DataFrame:
    """Stooq 일봉 CSV(미국: {base}.us). 실패(안티봇 HTML 포함)는 예외로 던진다.
    full=True는 지표 계산용(폴백 1차) — OHLCV 필수 컬럼까지 검증. 교차 검증용은 Close만 필요."""
    url = f"https://stooq.com/q/d/l/?s={symbol_base.lower()}.us&i=d"
    text = _http_get(url)
    if text.lstrip().startswith("<"):
        raise RuntimeError("stooq가 CSV 대신 HTML 반환(안티봇 챌린지 추정)")
    sdf = pd.read_csv(io.StringIO(text))
    if "Close" not in sdf.columns or sdf.empty:
        raise RuntimeError(f"stooq 응답에 데이터 없음: {url}")
    if full:
        need = [c for c in ("Open", "High", "Low", "Close", "Volume") if c not in sdf.columns]
        if need:
            raise RuntimeError(f"stooq 폴백에 지표 계산 필수 컬럼 누락: {', '.join(need)}")
    sdf["Date"] = pd.to_datetime(sdf["Date"])
    return sdf.set_index("Date").sort_index()


def fetch_nasdaq_daily(symbol_base: str, end_date: date) -> pd.DataFrame:
    """Nasdaq 공개 chart API 일봉 종가(NASDAQ·NYSE). 주식 → ETF 순서로 assetclass 시도."""
    start = end_date - timedelta(days=21)
    last_err = "빈 응답"
    for assetclass in ("stocks", "etf"):
        url = (f"https://api.nasdaq.com/api/quote/{symbol_base.upper()}/chart"
               f"?assetclass={assetclass}&fromdate={start}&todate={end_date}")
        try:
            payload = json.loads(_http_get(url, accept="application/json"))
            rows = (payload.get("data") or {}).get("chart") or []
            if not rows:
                last_err = f"{assetclass}: chart 비어 있음"
                continue
            recs = [(pd.to_datetime(r["z"]["dateTime"], format="%m/%d/%Y"),
                     float(str(r["z"]["close"]).replace(",", "").replace("$", "")))
                    for r in rows]
            return pd.DataFrame(recs, columns=["Date", "Close"]).set_index("Date")
        except Exception as e:  # noqa: BLE001 — 다음 assetclass 시도
            last_err = f"{assetclass}: {e}"
    raise RuntimeError(f"nasdaq chart 실패 — {last_err}")


def fetch_coinbase_daily(product: str) -> pd.DataFrame:
    """Coinbase Exchange 공개 candles API 일봉 종가(무인증). product 예: BTC-USD.
    반환 행: [time(버킷 시작 UTC), low, high, open, close, volume] 최신순."""
    url = f"https://api.exchange.coinbase.com/products/{product.upper()}/candles?granularity=86400"
    rows = json.loads(_http_get(url, accept="application/json"))
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"coinbase candles 비어 있음/오류 응답: {url}")
    recs = [(pd.to_datetime(int(r[0]), unit="s"), float(r[4])) for r in rows]
    return pd.DataFrame(recs, columns=["Date", "Close"]).set_index("Date").sort_index()


def fetch_binance_daily(base: str, quote: str) -> pd.DataFrame:
    """Binance 공개 klines API 일봉 종가(무인증). USD 쿼트는 USDT로 근사(통상 괴리 <0.3%)."""
    symbol = f"{base}{'USDT' if quote == 'USD' else quote}".upper()
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1d&limit=30"
    rows = json.loads(_http_get(url, accept="application/json"))
    if not isinstance(rows, list) or not rows:
        raise RuntimeError(f"binance klines 비어 있음/오류 응답: {url}")
    recs = [(pd.to_datetime(int(r[0]), unit="ms"), float(r[4])) for r in rows]
    return pd.DataFrame(recs, columns=["Date", "Close"]).set_index("Date").sort_index()


def _close_by_date(frame: pd.DataFrame) -> pd.Series:
    """Close 시리즈를 tz 제거·자정 정규화 날짜 인덱스로 변환 (yfinance는 tz-aware 인덱스)."""
    idx = pd.DatetimeIndex(frame.index)
    if idx.tz is not None:
        idx = idx.tz_localize(None)
    return pd.Series(frame["Close"].to_numpy(dtype=float), index=idx.normalize())


def cross_check_close(df: pd.DataFrame, ticker: str, market: str,
                      tolerance_pct: float, end_date: date) -> dict:
    """1차 소스(yfinance) 종가를 독립 2차 소스와 같은 날짜로 대조한다.
    체인: US = stooq → nasdaq / CRYPTO(USD·USDT 쿼트) = coinbase → binance."""
    out = {
        "primary": "yfinance", "secondary": None, "compared_date": None,
        "primary_close": _round(df["Close"].iloc[-1], 4), "secondary_close": None,
        "diff_pct": None, "tolerance_pct": tolerance_pct, "status": None,
    }
    if market == "KR":
        out["status"] = "skipped_kr"  # KRX·네이버 교차는 LLM 레이어 담당 (스킬 §3)
        return out
    sym = (ticker or "").upper()
    if market == "CRYPTO":
        base, quote = sym.rsplit("-", 1) if "-" in sym else (sym, "")
        if quote not in ("USD", "USDT"):
            out["status"] = "skipped_crypto_quote"  # KRW 등 비달러 쿼트는 업비트 등 LLM 교차 담당
            return out
        # Coinbase는 USDT 페어 다수 미상장 — USDT 쿼트도 USD 페어로 조회(USDT≈USD, 교차 목적상 근사 허용)
        cb_product = f"{base}-USD"
        chain = (("coinbase" if quote == "USD" else "coinbase(USD 근사)",
                  lambda: fetch_coinbase_daily(cb_product)),
                 ("binance(USDT 근사)" if quote == "USD" else "binance",
                  lambda: fetch_binance_daily(base, quote)))
    else:
        chain = (("stooq", lambda: fetch_stooq_daily(sym.split(".")[0])),
                 ("nasdaq", lambda: fetch_nasdaq_daily(sym.split(".")[0], end_date)))
    errors = []
    for name, fetch in chain:
        try:
            sdf = fetch()
        except Exception as e:  # noqa: BLE001 — 다음 소스 시도
            errors.append(f"{name}: {e}")
            continue
        pser, sser = _close_by_date(df), _close_by_date(sdf)
        common = pser.index.intersection(sser.index)
        if len(common) == 0:
            errors.append(f"{name}: 공통 거래일 없음")
            continue
        d = common.max()
        p = float(pser.loc[[d]].iloc[-1])
        s = float(sser.loc[[d]].iloc[-1])
        out.update({
            "secondary": name, "compared_date": str(d.date()),
            "primary_close": _round(p, 4), "secondary_close": _round(s, 4),
            "diff_pct": _round(abs(p - s) / p * 100, 3) if p else None,
        })
        out["status"] = ("match" if out["diff_pct"] is not None and out["diff_pct"] <= tolerance_pct
                         else "mismatch")
        return out
    out["status"] = "skipped_error: " + " | ".join(errors)
    return out


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
    ap.add_argument("--market", choices=["US", "KR", "CRYPTO"], help="시장 강제 지정 (감지 무시)")
    ap.add_argument("--xcheck-tolerance", type=float, default=1.0,
                    help="이중 소스 종가 허용 오차 %% (기본 1.0)")
    ap.add_argument("--no-xcheck", action="store_true", help="이중 소스 교차 검증 생략")
    ap.add_argument("--now-utc", help="세션 판정 시각 주입 (예: 2026-07-04T05:00:00 — 테스트·재현용)")
    args = ap.parse_args()

    if not args.ticker and not args.from_csv:
        print(json.dumps({"status": "error", "error": "--ticker 또는 --from-csv 필요"}, ensure_ascii=False))
        sys.exit(2)

    if args.from_csv and not args.market:
        # 시장 미해소 상태에서 US 디폴트로 세션을 오판하지 않는다 (KR CSV 재계산 오라벨 방지).
        # 티커가 있어도 확신 신호(KR: .KS/.KQ/6자리, US: 1~5자 알파벳)가 없으면 --market을 요구한다
        t = (args.ticker or "").upper()
        base = t.split(".")[0]
        positive_kr = t.endswith((".KS", ".KQ")) or (base.isdigit() and len(base) == 6)
        positive_crypto = is_crypto_symbol(t)
        positive_us = (not positive_crypto) and base.isalpha() and 1 <= len(base) <= 5
        if not (positive_kr or positive_us or positive_crypto):
            print(json.dumps({"status": "error",
                              "error": f"--from-csv에 --market 필요 — 티커 '{args.ticker or ''}'로 시장 확신 불가 (US 디폴트 금지)"},
                             ensure_ascii=False))
            sys.exit(2)

    try:
        now_utc = (datetime.strptime(args.now_utc.rstrip("Z"), "%Y-%m-%dT%H:%M:%S")
                   if args.now_utc else datetime.now(timezone.utc).replace(tzinfo=None))
    except ValueError:
        print(json.dumps({"status": "error", "error": f"--now-utc 형식 오류: {args.now_utc} (YYYY-MM-DDTHH:MM:SS)"},
                         ensure_ascii=False))
        sys.exit(2)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "00_ohlcv_daily.csv"
    json_path = out_dir / "00_indicators.json"

    # as_of는 UTC 날짜(now_utc 기준) — --now-utc 주입과 정합하는 재현성 우선. 현지 날짜와 최대 1일 차 허용
    meta = {"as_of": str(now_utc.date()), "source": None, "source_primary": None,
            "source_secondary": None, "ticker_resolved": None, "fast_info": {}}

    try:
        if args.from_csv:
            df = pd.read_csv(args.from_csv, index_col=0, parse_dates=True)
            if df.empty:
                raise RuntimeError(f"CSV에 데이터 행 없음: {args.from_csv}")
            meta["source"] = meta["source_primary"] = f"manual_csv:{args.from_csv}"
            meta["ticker_resolved"] = args.ticker or "unknown"
        else:
            try:
                sym, t, df = fetch_ohlcv(args.ticker, args.period)
                df.to_csv(csv_path, encoding="utf-8")
                meta["source"] = meta["source_primary"] = "yfinance"
                meta["ticker_resolved"] = sym
                meta["fast_info"] = fast_info_dict(t)
            except Exception as yf_err:  # noqa: BLE001 — 미국 티커는 Stooq를 1차 소스로 자동 폴백
                market_guess = args.market or detect_market(args.ticker or "")
                if market_guess != "US":
                    raise  # 한국(KRX·korean-stock-search)·크립토(웹 시세) 폴백은 LLM 레이어 담당 — 에이전트 정의 참조
                # Stooq가 안티봇 챌린지를 반환하면 폴백도 클린 실패(status:error)로 끝난다 —
                # 이후는 에이전트 에러 핸들링(웹 시세 수집) 담당. Nasdaq chart는 종가만 제공해 지표 원천 불가
                df = fetch_stooq_daily((args.ticker or "").split(".")[0], full=True)
                if len(df) < 30:
                    raise RuntimeError(f"stooq 폴백 데이터 부족({len(df)}행) — 원 오류: {yf_err}")
                df.to_csv(csv_path, encoding="utf-8")
                meta["source"] = meta["source_primary"] = f"stooq (yfinance 실패 폴백: {yf_err})"
                meta["ticker_resolved"] = f"{(args.ticker or '').split('.')[0].lower()}.us"
    except Exception as e:  # noqa: BLE001 — 수집 실패를 JSON으로 보고
        print(json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False))
        sys.exit(1)

    market = args.market or detect_market(args.ticker or "", meta["ticker_resolved"] or "")
    last_data_date = df.index[-1].date() if hasattr(df.index[-1], "date") else None
    session = judge_session(market, now_utc, last_data_date)

    if args.no_xcheck or args.from_csv:
        xcheck = {"status": "skipped_by_flag" if args.no_xcheck else "skipped_manual_csv",
                  "tolerance_pct": args.xcheck_tolerance}
    elif str(meta["source_primary"]).startswith("stooq"):
        xcheck = {"status": "skipped_primary_is_fallback", "primary": "stooq",
                  "tolerance_pct": args.xcheck_tolerance}
    else:
        xcheck = cross_check_close(df, meta["ticker_resolved"] or args.ticker, market,
                                   args.xcheck_tolerance, now_utc.date())
    if str(meta["source_primary"]) == "yfinance" and xcheck.get("secondary"):
        meta["source_secondary"] = xcheck["secondary"]

    try:
        indicators = compute_indicators(df)
    except Exception as e:  # noqa: BLE001 — 폴백 데이터 스키마 문제 등도 클린 JSON으로 보고
        print(json.dumps({"status": "error", "error": f"지표 계산 실패: {e}",
                          "source_primary": meta["source_primary"]}, ensure_ascii=False))
        sys.exit(1)

    result = {"status": "ok", **meta, "session": session, "cross_check": xcheck,
              "indicators": indicators}
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "ok", "csv": str(csv_path), "json": str(json_path),
                      "ticker": meta["ticker_resolved"], "rows": result["indicators"]["rows"],
                      "last_close": result["indicators"]["last_close"],
                      "market_session": session["market_session"],
                      "data_as_of": session["data_as_of"],
                      "last_close_is_final": session["last_close_is_final"],
                      "cross_check": xcheck["status"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
