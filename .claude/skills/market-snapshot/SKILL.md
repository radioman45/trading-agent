---
name: market-snapshot
description: 트레이딩 분석용 공통 시장 스냅샷(00_market_snapshot.json)과 일봉 OHLCV·기술지표(00_ohlcv_daily.csv, 00_indicators.json) 수집 방법론. 분석 대상의 시장(한국/미국)을 감지하고 주가·시가총액·발행주식수·환율·벤치마크·재무 핵심값·밸류에이션 배수·기술지표를 단일 진실 소스(SSOT)로 고정한다. market-data-engineer 에이전트가 스냅샷을 작성할 때, 또는 "시장 스냅샷", "데이터 고정", "기술지표 수집", "market snapshot"을 요청받을 때 반드시 이 스킬을 사용한다.
---

# Market Snapshot — 공통 시장 스냅샷 + 기술지표 수집

> ⚠️ **사실 검증 규율 [HARD] (2026-06-24 할루시네이션 사고 반영):** ① **시점 가드** — 현재 시각 기준 *마감된 세션*의 종가만 `close`로 고정. 미개장/장중이면 단정 말고 `confidence:"unavailable"` 또는 직전 마감일 값+`as_of`. 한국·미국 세션 거래일을 `source`에 명시(혼동 금지). 스냅샷에 `market_session` 필드(예 "KR 개장 전"/"마감")를 남긴다. ② **산술 정합** — 등락률·시총(=가격×주식수)·비중합 검산 후 저장. ③ **출처 실재성** — 실제 조회 출처만(날조 금지), 못 구하면 `unavailable`. 상세 `docs/anti-hallucination-verification-plan.md`.

트레이딩 파이프라인의 **단일 진실 소스(SSOT)**를 만든다. 분석가 4명과 하류 전체가 각자 데이터를 수집하면 같은 종목의 주가·시총이 보고서마다 달라진다. 이 스킬은 분석 시작 시점에 **객관적 사실값을 한 번만 고정**해, 모든 에이전트가 같은 사실 위에서 서로 다른 해석을 하게 만든다.

**핵심 원칙: 정확도보다 일관성.** 스냅샷은 "관점"이 아니라 "사실"이므로 모든 에이전트가 함께 읽어도 적대적 독립성을 해치지 않는다. 해석·전망·목표가는 고정하지 않는다 — 그건 분석가·리서처·트레이더의 몫이다.

## 1. 기술 데이터 수집 (스크립트 — 가장 먼저)

번들 스크립트가 OHLCV·기술지표·기본 시세를 한 번에 수집한다. 손으로 찾기 전에 **반드시 먼저 실행**한다:

```bash
python .claude/skills/market-snapshot/scripts/collect_market_data.py --ticker {티커} --out-dir _workspace
```

- 한국 6자리 코드(예: `005930`)는 `.KS`(KOSPI) → `.KQ`(KOSDAQ) 순서로 자동 시도한다.
- 산출: `_workspace/00_ohlcv_daily.csv`(1년 일봉), `_workspace/00_indicators.json`(SMA/EMA/MACD/RSI/볼린저/ATR/기간수익률/최대낙폭/52주고저/거래량 + `fast_info` 기본 시세).
- 종료 코드 1(수집 실패) 시 1회 재시도. 재실패하면 기술 데이터 없이 진행하고 `data_quality.notes`에 명시한다.
- 수동 CSV가 있으면 `--from-csv {경로}`로 지표만 재계산할 수 있다.
- `fast_info`(last_price·market_cap·shares_outstanding)는 스냅샷 코어값의 **1차 후보**다 — 아래 웹 출처와 교차 확인 후 채택하고, 상충하면 `data_quality.conflicts[]`에 병기한다.

## 2. 시장 자동 감지

`references/data-sources.md`의 "시장 자동 감지" 규칙으로 한국/미국을 판별하고 다음을 확정한다:

- `market`: `"KR"` 또는 `"US"`
- `exchange`: `"KOSPI"` | `"KOSDAQ"` | `"NYSE"` | `"NASDAQ"` 등
- `reporting_currency`: `"KRW"` | `"USD"`

티커가 모호하면 웹 검색 한 번으로 상장 거래소를 확정한 뒤 진행한다.

## 3. 수집 절차 (항목별)

데이터 소스 우선순위·도구는 `references/data-sources.md`를 따른다:

| 항목 | 미국 | 한국 |
|------|------|------|
| 주가·시총·발행주식수 | 스크립트 fast_info + WebSearch(거래소·IR) 교차 | 스크립트 fast_info + 네이버 증권·KRX 교차, 차단 시 `insane-search` |
| 환율(USDKRW) | `database-lookup` FRED 또는 WebSearch | 동일 |
| 벤치마크 지수 레벨 | S&P500(또는 섹터 ETF), WebSearch | KOSPI/KOSDAQ, WebSearch |
| 재무 핵심값 | SEC EDGAR(10-K/10-Q) via `database-lookup` | DART(`k-dart` 스킬) 사업/분기보고서 |
| 밸류에이션 배수 | WebSearch, IR 교차 | 네이버 증권·KRX |

모든 값에 **시점(`as_of`)과 출처(`source`)**를 반드시 붙인다.

## 4. JSON 스키마 (필수)

산출물은 `_workspace/00_market_snapshot.json`. 모든 수치 필드는 `{value, currency, as_of, source, confidence}` 구조다(`confidence`: `"high"|"medium"|"low"|"unavailable"`).

```json
{
  "schema_version": "1.0",
  "as_of": "2026-06-10",
  "company": "엔비디아",
  "ticker": "NVDA",
  "market": "US",
  "exchange": "NASDAQ",
  "reporting_currency": "USD",
  "identifiers": { "fiscal_year_end": "01-31" },

  "price":              { "value": 206.36, "currency": "USD", "as_of": "2026-06-09", "source": "yfinance 종가, NASDAQ 교차", "confidence": "high" },
  "market_cap":         { "value": 4998245574783, "currency": "USD", "as_of": "2026-06-09", "source": "yfinance fast_info", "confidence": "high" },
  "shares_outstanding": { "value": 24221000000, "currency": null, "as_of": "2026-06-09", "source": "yfinance fast_info, 10-Q 교차", "confidence": "high" },

  "fx": {
    "USDKRW": { "value": 1380.5, "currency": "KRW", "as_of": "2026-06-09", "source": "FRED", "confidence": "high" }
  },

  "benchmark": {
    "primary": { "name": "S&P500", "level": 6500.0, "as_of": "2026-06-09", "source": "WebSearch", "confidence": "high" }
  },

  "financials": {
    "latest_period": "FY2026 Q1",
    "period_type": "quarterly",
    "revenue":              { "value": 44060000000, "currency": "USD", "as_of": "2026-04-30", "source": "10-Q(2026-05 제출)", "confidence": "high" },
    "operating_income":     { "value": 21640000000, "currency": "USD", "as_of": "2026-04-30", "source": "10-Q", "confidence": "high" },
    "net_income":           { "value": 18780000000, "currency": "USD", "as_of": "2026-04-30", "source": "10-Q", "confidence": "high" },
    "total_debt":           { "value": 8460000000, "currency": "USD", "as_of": "2026-04-30", "source": "10-Q", "confidence": "medium" },
    "cash_and_equivalents": { "value": 53690000000, "currency": "USD", "as_of": "2026-04-30", "source": "10-Q", "confidence": "high" }
  },

  "valuation": {
    "pe":        { "value": 45.2, "as_of": "2026-06-09", "source": "WebSearch", "confidence": "medium" },
    "ps":        { "value": 26.1, "as_of": "2026-06-09", "source": "WebSearch", "confidence": "medium" },
    "ev_ebitda": { "value": null, "as_of": null, "source": null, "confidence": "unavailable" }
  },

  "technicals_ref": {
    "indicators_file": "_workspace/00_indicators.json",
    "ohlcv_file": "_workspace/00_ohlcv_daily.csv",
    "generated": true
  },

  "data_quality": {
    "unavailable_fields": ["valuation.ev_ebitda"],
    "conflicts": [],
    "notes": "예시 값임. 실제 수집 시 시점·출처를 갱신할 것."
  }
}
```

스키마 규칙:
- `market: "US"`인 경우에도 `fx.USDKRW`를 채워 한국 투자자 원화 환산 기준을 제공한다.
- `shares_outstanding.currency`는 통화 없는 값이므로 `null`.
- `benchmark.primary.name`: 한국=KOSPI/KOSDAQ, 미국=S&P500(또는 분석 대상 섹터 ETF).
- `value`가 큰 정수(시총·매출)는 원 단위 정수로 기록한다(축약 금지).
- `technicals_ref.generated`: 스크립트 성공 시 `true`, 실패 시 `false`(이때 두 파일 경로는 무시된다).

## 5. 미확보·상충·차단 처리 (data_quality)

**추측으로 채우지 않는다.**

- **미확보:** 해당 필드 `value: null`, `confidence: "unavailable"`, `data_quality.unavailable_fields`에 필드 경로 추가.
- **출처 상충:** 어느 쪽도 지우지 않는다. 본 필드엔 채택값, `data_quality.conflicts[]`에 `{ "field": "...", "chosen": <값>, "alternative": <값>, "reason": "..." }` 기록.
- **접근 차단(402/403/봇):** `insane-search` 우회 → 실패 시 미확보 표기.

## 6. 작성 전 검증 체크리스트

스냅샷 저장 직전 확인한다:

- [ ] 유효한 JSON인가 — `python -m json.tool _workspace/00_market_snapshot.json`으로 확인.
- [ ] `as_of`(최상위), `company`, `ticker`, `market`, `exchange`, `reporting_currency`가 모두 채워졌는가.
- [ ] `price`, `market_cap`, `shares_outstanding`, `fx.USDKRW`, `benchmark.primary`가 채워졌거나 `unavailable`로 명시됐는가.
- [ ] `financials` 5개 라인이 채워졌거나 `unavailable`인가.
- [ ] 모든 수치 필드에 `as_of`와 `source`가 있는가.
- [ ] `technicals_ref.generated`가 실제 스크립트 성공 여부와 일치하는가.
- [ ] 미확보 필드가 `unavailable_fields`에, 상충이 `conflicts`에 반영됐는가.
