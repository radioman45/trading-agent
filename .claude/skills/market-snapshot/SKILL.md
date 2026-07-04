---
name: market-snapshot
description: 트레이딩 분석용 공통 시장 스냅샷(00_market_snapshot.json)과 일봉 OHLCV·기술지표(00_ohlcv_daily.csv, 00_indicators.json) 수집 방법론. 분석 대상의 시장(한국/미국)을 감지하고 주가·시가총액·발행주식수·환율·벤치마크·재무 핵심값·밸류에이션 배수·기술지표를 단일 진실 소스(SSOT)로 고정한다. market-data-engineer 에이전트가 스냅샷을 작성할 때, 또는 "시장 스냅샷", "데이터 고정", "기술지표 수집", "market snapshot"을 요청받을 때 반드시 이 스킬을 사용한다.
---

# Market Snapshot — 공통 시장 스냅샷 + 기술지표 수집

> ⚠️ **사실 검증 규율 [HARD] (2026-06-24 할루시네이션 사고 반영):** ① **시점 가드** — 현재 시각 기준 *마감된 세션*의 종가만 `close`로 고정. 미개장/장중이면 단정 말고 `confidence:"unavailable"` 또는 직전 마감일 값+`as_of`. 한국·미국 세션 거래일을 `source`에 명시(혼동 금지). 세션 서술은 스냅샷 `session` 블록(스크립트 기계 판정, 아래 v1.1 규정)이 담당한다 — 별도 최상위 `market_session` 필드는 만들지 않는다. ② **산술 정합** — 등락률·시총(=가격×주식수)·비중합 검산 후 저장. ③ **출처 실재성** — 실제 조회 출처만(날조 금지), 못 구하면 `unavailable`. 상세 `docs/anti-hallucination-verification-plan.md`.
>
> **세션 판정은 스크립트가 한다 (2026-07-04, codex R4):** 수집 스크립트가 `session` 블록(market_session·data_as_of·last_close_is_final·staleness)을 **코드로 기계 판정**해 `00_indicators.json`에 남긴다. 너는 이 블록을 스냅샷 최상위 `session`으로 **그대로 복사**한다 — 세션을 스스로 재판정하지 않는다(기계값과 다른 세션 서술 금지). `last_close_is_final: false`면 그 마지막 행 값은 확정 종가가 아니다 — `price`에는 직전 확정 종가를 쓰고 `as_of`를 그 거래일로 명시한다.

트레이딩 파이프라인의 **단일 진실 소스(SSOT)**를 만든다. 분석가 4명과 하류 전체가 각자 데이터를 수집하면 같은 종목의 주가·시총이 보고서마다 달라진다. 이 스킬은 분석 시작 시점에 **객관적 사실값을 한 번만 고정**해, 모든 에이전트가 같은 사실 위에서 서로 다른 해석을 하게 만든다.

**핵심 원칙: 정확도보다 일관성.** 스냅샷은 "관점"이 아니라 "사실"이므로 모든 에이전트가 함께 읽어도 적대적 독립성을 해치지 않는다. 해석·전망·목표가는 고정하지 않는다 — 그건 분석가·리서처·트레이더의 몫이다.

## 1. 기술 데이터 수집 (스크립트 — 가장 먼저)

번들 스크립트가 OHLCV·기술지표·기본 시세를 한 번에 수집한다. 손으로 찾기 전에 **반드시 먼저 실행**한다:

```bash
python .claude/skills/market-snapshot/scripts/collect_market_data.py --ticker {티커} --out-dir _workspace
```

- 한국 6자리 코드(예: `005930`)는 `.KS`(KOSPI) → `.KQ`(KOSDAQ) 순서로 자동 시도한다.
- 산출: `_workspace/00_ohlcv_daily.csv`(1년 일봉), `_workspace/00_indicators.json`(SMA/EMA/MACD/RSI/볼린저/ATR/기간수익률/최대낙폭/52주고저/거래량 + `fast_info` 기본 시세 + **`session`·`cross_check` 블록**).
- **`session` 블록(기계 판정):** market_session(`pre_open|regular|post_close|weekend`)·`data_as_of`·`last_close_is_final`·`staleness_calendar_days`·`stale_feed_suspect`·`intraday_data_gap`·`requested_at_utc` 등. 휴장일 캘린더는 내장하지 않으므로(`calendar_status: approx_no_holiday_calendar`) `stale_feed_suspect: true`는 "휴장이었는지 피드 지연인지 확인하라"는 신호다 — 웹 확인 후 `data_quality.notes`에 원인을 남긴다. `intraday_data_gap: true`(장중 세션인데 당일 봉 없음)는 **평일 휴장 또는 피드 미갱신** 신호 — 같은 방식으로 원인을 확인·기록하고, 그날을 "장중"으로 서술하지 않는다.
- **`cross_check` 블록(이중 소스):** 미국 티커는 마지막 종가를 독립 2차 소스(stooq → nasdaq 체인)와 같은 거래일로 대조한다(허용 오차 기본 1%). `mismatch`면 값 채택 전 원인 규명 — 채택값·대안값을 `data_quality.conflicts[]`에 기록하고 `price.confidence`는 최대 `"medium"`, 최종 결정문 검증 모드는 `DEGRADED_DATA` 대상이다. 한국 티커는 `skipped_kr` — §3의 네이버 증권·KRX 교차가 2차 소스 역할을 한다(교차 결과를 conflicts에 동일하게 기록).
- yfinance 전체 실패 시 미국 티커는 스크립트가 Stooq를 1차 소스로 **자동 폴백**하고 `source_primary`에 사유를 기록한다(이때 cross_check는 `skipped_primary_is_fallback`). 폴백은 **단일 소스**(2차 교차 없음)다 — `price.confidence`는 최대 `"medium"`, `fast_info`가 비므로 시총·주식수는 웹 출처로 채우고 교차한다. Stooq가 안티봇 차단 중이면 폴백도 클린 실패(status:error)로 끝난다 — 이후는 에이전트 에러 핸들링(웹 시세 수집). 한국 티커 폴백은 에이전트 정의의 에러 핸들링(korean-stock-search)을 따른다.
- 종료 코드 1(수집 실패) 시 1회 재시도. 재실패하면 기술 데이터 없이 진행하고 `data_quality.notes`에 명시한다.
- 수동 CSV가 있으면 `--from-csv {경로} --market {US|KR}`로 지표만 재계산할 수 있다. `--market` 미지정 시 티커가 시장 확신 신호(KR: `.KS`/`.KQ`/6자리, US: 1~5자 알파벳)를 주지 못하면 스크립트가 exit 2로 거부한다 — US 디폴트로 세션을 오판하지 않기 위함. 교차 검증은 skipped.
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
  "schema_version": "1.1",
  "as_of": "2026-06-10",
  "company": "엔비디아",
  "ticker": "NVDA",
  "market": "US",
  "exchange": "NASDAQ",
  "reporting_currency": "USD",
  "identifiers": { "fiscal_year_end": "01-31" },

  "session": {
    "market": "US",
    "tz": "America/New_York (DST approx)",
    "requested_at_utc": "2026-06-10T07:12:00Z",
    "requested_at_local": "2026-06-10T03:12",
    "market_session": "pre_open",
    "calendar_status": "approx_no_holiday_calendar",
    "data_as_of": "2026-06-09",
    "expected_last_trading_date": "2026-06-09",
    "staleness_calendar_days": 1,
    "last_close_is_final": true,
    "stale_feed_suspect": false,
    "intraday_data_gap": false
  },

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
- **`session` 블록(v1.1 필수):** `00_indicators.json`의 `session` 블록을 **모든 필드 그대로**(서브셋 금지) 복사한다(재판정 금지). 스크립트가 실패해 블록이 없으면 같은 필드를 수동으로 채우되(`market_session`·`data_as_of`·`requested_at_utc` 3키는 필수) `calendar_status: "manual"`로 표기한다. harness doctor가 블록 누락(00_indicators.json에 기계 session이 있으면 schema_version 라벨과 무관하게)과 **기계값과의 불일치·생략**(data_as_of·last_close_is_final·stale_feed_suspect·intraday_data_gap은 FAIL)을 잡는다.
- **세션별 가격 서술 문구(하류 보고서 표현 규칙):** `pre_open`="전일 종가 기준" / `regular`="장중 지연 가능 시세 — 종가 아님" / `post_close`="당일 종가(확정)" / `weekend·휴장`="최근 거래일({data_as_of}) 종가 기준". 단 `regular`인데 `intraday_data_gap: true`면 "장중" 서술 금지 — "휴장 또는 피드 지연 의심, 최근 거래일({data_as_of}) 종가 기준"으로 쓴다. `last_close_is_final: null`(미판정 — `anomaly` 동반)이면 데이터·판정 시각 정합을 확인하기 전까지 가격 서술 자체를 하지 않는다. "오늘/현재" 수식어는 `session.market_session`과 일치할 때만 사용. 또한 `last_close_is_final: false`면 기술지표 전체(SMA/RSI/MACD 등)가 미확정 봉을 포함해 산출된 값이다 — 하류 기술적 분석 보고서는 이를 명시한다.
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
- [ ] `session` 블록이 `00_indicators.json`에서 **모든 필드 그대로** 복사됐는가. `last_close_is_final: false`인데 그 값을 `price`로 쓰지 않았는가. `stale_feed_suspect` 또는 `intraday_data_gap`이 `true`면 원인(휴장/피드 지연)을 `data_quality.notes`에 남겼는가.
- [ ] `cross_check.status`가 `mismatch`면 `data_quality.conflicts[]`에 기록하고 `price.confidence ≤ "medium"`인가. `skipped_primary_is_fallback`(단일 소스 폴백)이면 `price.confidence ≤ "medium"` + 웹 교차를 했는가. (한국 종목은 네이버·KRX 교차 결과가 이 역할)
- [ ] `price`, `market_cap`, `shares_outstanding`, `fx.USDKRW`, `benchmark.primary`가 채워졌거나 `unavailable`로 명시됐는가.
- [ ] `financials` 5개 라인이 채워졌거나 `unavailable`인가.
- [ ] 모든 수치 필드에 `as_of`와 `source`가 있는가.
- [ ] `technicals_ref.generated`가 실제 스크립트 성공 여부와 일치하는가.
- [ ] 미확보 필드가 `unavailable_fields`에, 상충이 `conflicts`에 반영됐는가.
