---
name: ipo-snapshot
description: IPO(신규상장) 분석용 공통 스냅샷(ipo_snapshot.json) 수집 방법론 — 미국(SEC EDGAR)·한국(DART) 범용. 거래 이력이 없는 IPO는 주가 대신 공모가·발행신주·상장후 주식수·시가총액·유통물량(free float)·락업/의무보유확약·지수편입·세그먼트 재무·(한국이면) 수요예측 경쟁률·청약 구조를 단일 진실 소스(SSOT)로 고정한다. data-collector가 IPO 스냅샷을 작성할 때, 또는 "IPO 스냅샷", "공모 데이터 고정", "상장 스냅샷", "공모주 데이터 정리"를 요청받을 때 반드시 이 스킬을 사용한다.
---

# IPO Snapshot — 신규상장 공통 스냅샷 수집

IPO 분석 파이프라인의 **단일 진실 소스(SSOT)**를 만든다. 일반 2차 시장 종목과 달리 IPO에는 **거래 이력·과거 멀티플·시장 가격이 없다.** 따라서 스냅샷은 "현재 주가"가 아니라 **공모 구조**(공모가·발행 신주·상장 후 주식수·유통물량·락업·지수편입)와 세그먼트 재무를 고정한다.

**핵심 원칙: 정확도보다 일관성, 그리고 정합성.** 스냅샷은 "관점"이 아니라 "사실"이므로 Bull·Bear가 함께 읽어도 적대적 독립성을 해치지 않는다. 해석·전망·목표가는 고정하지 않는다 — 그건 Bull/Bear/Judge의 몫이다. **단, IPO 숫자는 서로 산술적으로 맞아야 한다** — 시총 = 공모가 × 상장후 주식수, 조달 = 공모가 × 신주. 이 정합성을 self-check로 검증한다.

## 1. 소싱 규칙 — 하드코딩 금지, 최신 문서 우선 [중요]

IPO 조건은 상장 직전까지 계속 바뀐다(초기 S-1 → S-1/A 개정 → FWP → 최종 투자설명서 424B). **구버전 링크를 그대로 신뢰하지 마라.**

1. **EDGAR 최신순 탐색:** 발행사 CIK로 EDGAR 제출 목록을 **최신 제출일순**으로 확인한다. (`database-lookup`의 SEC EDGAR, 또는 WebSearch로 `SEC EDGAR {회사} S-1` 후 filing index 진입. 차단 시 `insane-search`.)
2. **문서 우선순위:** 최종 투자설명서(424B) > 최신 S-1/A > FWP(Free Writing Prospectus) > 초기 S-1 > 보도자료 > 언론. 같은 항목이 여러 문서에 다르면 **상위 문서 값 채택 + 하위 문서값을 alternative로 기록**.
3. **상태 태그 필수:** 상장(가격 확정) 전이면 가격 관련 값은 모두 `source_status: "preliminary"`. 가격 확정(보통 상장 전일) 후 최종 투자설명서가 나오면 `"final"`. 보도 기반은 `"press"`, 추정은 `"estimate"`.
4. **시드는 시드일 뿐:** `_workspace_ipo/00_orchestrator_input.md`나 사용자 노트의 숫자는 출발 힌트이며, 반드시 1차 출처로 교차하고 다르면 1차 출처를 채택한 뒤 차이를 `data_quality.notes`에 적는다.
5. **한국 IPO(`market: "KR"`)는 DART 최신순:** 공모가 확정 [기재정정]증권신고서·투자설명서 > 최신 [기재정정]증권신고서 > 최초 증권신고서(지분증권) > 보도. `k-dart` 스킬/DART OpenAPI로 최신 제출일순을 확인한다. 수요예측 전 희망공모가 밴드는 `source_status: "preliminary"`, 수요예측 후 확정 공모가는 `"final"`.

## 2. JSON 스키마 (필수)

산출물은 `_workspace_ipo/00_ipo_snapshot.json`. 모든 수치 필드는 `{value, currency, as_of, source, source_doc, source_status, confidence}` 구조다 (`source_status`: `"preliminary"|"final"|"press"|"estimate"`, `confidence`: `"high"|"medium"|"low"|"unavailable"`).

```json
{
  "schema_version": "ipo-1.0",
  "as_of": "2026-06-09",
  "company": "Space Exploration Technologies Corp. (SpaceX)",
  "ticker": "SPCX",
  "market": "US",
  "exchange": "Nasdaq / Nasdaq Texas",
  "reporting_currency": "USD",

  "listing": {
    "pricing_date":  { "value": "2026-06-11", "as_of": "2026-06-09", "source": "FWP", "source_doc": "FWP 2026-06-04", "source_status": "preliminary", "confidence": "high" },
    "trading_start": { "value": "2026-06-12", "as_of": "2026-06-09", "source": "FWP", "source_doc": "FWP 2026-06-04", "source_status": "preliminary", "confidence": "high" },
    "ipo_price":          { "value": 135, "currency": "USD", "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP 2026-06-04", "source_status": "preliminary", "confidence": "high" },
    "shares_offered_new": { "value": 555555556, "currency": null, "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "primary_pct":        { "value": 100, "currency": null, "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "greenshoe":          { "value": 83333333, "currency": null, "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" },
    "gross_proceeds_est": { "value": 75000000000, "currency": "USD", "as_of": "2026-06-04", "source": "보도/FWP 역산", "source_doc": "Reuters", "source_status": "press", "confidence": "medium" }
  },

  "post_ipo_shares": {
    "class_a":             { "value": 7488063555, "currency": null, "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "class_b":             { "value": 5602790410, "currency": null, "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "total":               { "value": 13090853965, "currency": null, "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "total_with_greenshoe":{ "value": 13174187298, "currency": null, "as_of": "2026-06-04", "source": "FWP 역산", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" }
  },

  "valuation": {
    "market_cap_at_ipo":      { "value": 1767265285275, "currency": "USD", "as_of": "2026-06-04", "source": "ipo_price×total 계산", "source_doc": "derived", "source_status": "preliminary", "confidence": "high" },
    "market_cap_with_greenshoe": { "value": 1778515285230, "currency": "USD", "as_of": "2026-06-04", "source": "derived", "source_doc": "derived", "source_status": "preliminary", "confidence": "medium" }
  },

  "free_float": {
    "base_offering_float_pct":     { "value": 4.24, "as_of": "2026-06-04", "source": "shares_offered_new / total", "source_doc": "derived", "source_status": "preliminary", "confidence": "high" },
    "with_overallotment_float_pct":{ "value": 4.85, "as_of": "2026-06-04", "source": "(new+greenshoe)/(total+greenshoe)", "source_doc": "derived", "source_status": "preliminary", "confidence": "high" },
    "reported_float_claim_pct":    { "value": 7, "as_of": "2026-06-03", "source": "Reuters", "source_doc": "Reuters", "source_status": "press", "confidence": "low" },
    "reconciliation_required": true,
    "reconciliation_note": "보도 7%는 신주only 4.24%(또는 초과배정 포함 4.85%)와 약 360M주 차이. 신주만으로 설명 안 됨 — fact-checker가 7% 정의(분모·포함 물량)를 규명하거나 미해결로 표기."
  },

  "lockup": {
    "musk":          { "value": "366일", "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "select_insiders":{ "value": "2026 Q4 실적 후 ~ 2027 Q2 실적 후 단계적", "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" },
    "other_shares":  { "value": "2026 Q2 실적 후 ~ IPO+180일 단계적 조기 해제", "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" },
    "registration_rights_shares": { "value": 9200000000, "currency": null, "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" },
    "rule144_after90d_shares":    { "value": 12200000000, "currency": null, "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" },
    "rule144_note": "‘90일 후 ~12.2B주 재판매 가능’은 전량 자유유통이 아니라 별도 락업 제한 적용 대상. free_float 7%와 충돌하지 않음(락업이 실제 유통을 제약)."
  },

  "index_inclusion": {
    "candidates": { "value": ["MSCI 조기편입 가능성"], "as_of": "2026-06-03", "source": "Reuters", "source_doc": "Reuters", "source_status": "estimate", "confidence": "low" }
  },

  "segment_financials": {
    "latest_annual": "FY2025",
    "connectivity_revenue_2025":       { "value": 11400000000, "currency": "USD", "as_of": "2025-12-31", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "connectivity_adj_ebitda_2025":    { "value": 7200000000, "currency": "USD", "as_of": "2025-12-31", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "connectivity_operating_income_2025": { "value": 4400000000, "currency": "USD", "as_of": "2025-12-31", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "high" },
    "connectivity_adj_ebitda_q1_2026": { "value": 2100000000, "currency": "USD", "as_of": "2026-03-31", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" },
    "starlink_subscribers":            { "value": 10300000, "currency": null, "as_of": "2026-03-31", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" }
  },

  "use_of_proceeds": { "value": ["AI 컴퓨팅 인프라", "발사 인프라·발사체", "위성망 확장"], "as_of": "2026-06-04", "source": "FWP", "source_doc": "FWP", "source_status": "preliminary", "confidence": "medium" },

  "fx": {
    "USDKRW": { "value": 1380.0, "currency": "KRW", "as_of": "2026-06-09", "source": "FRED", "source_doc": "FRED", "source_status": "final", "confidence": "high" }
  },

  "self_check": {
    "market_cap_recompute": { "expected": 1767265285275, "formula": "135 × 13090853965", "pass": true },
    "proceeds_recompute":   { "expected": 75000000010,  "formula": "135 × 555555556", "pass": true },
    "free_float_recompute": { "base_pct": 4.24, "with_oa_pct": 4.85, "reported_claim_pct": 7, "gap_shares": 360800000, "reconciled": false },
    "overall": "PASS"
  },

  "data_quality": {
    "unavailable_fields": [],
    "conflicts": [],
    "notes": "예시 값(SpaceX 시드 기반 — docs/ipo/spcx-seed.txt). 실제 수집 시 EDGAR/DART 최신 문서로 교차하고 source_status·as_of를 갱신할 것. 상장 전이면 가격 관련 전부 preliminary."
  }
}
```

스키마 규칙:
- `market: "US"`라도 `fx.USDKRW`를 채워 한국 투자자 원화 환산 기준을 제공한다.
- 주식수 필드의 `currency`는 `null`.
- 큰 정수(시총·주식수)는 축약 없이 정수로 기록한다.
- 가격 관련 값은 상장 전이면 **반드시** `source_status: "preliminary"`.
- `market: "KR"`이면 아래 `kr_ipo` 블록을 추가한다(미확보 필드는 `unavailable`).

### 한국 IPO 추가 블록 (`kr_ipo`, `market: "KR"`일 때 필수)

각 필드는 동일한 `{value, as_of, source, source_doc, source_status, confidence}` 구조다:

- `band_low` / `band_high`: 희망공모가 밴드 (수요예측 전 — `preliminary`)
- `final_price`: 확정 공모가 (수요예측 후 [기재정정]증권신고서 기준 — `final`)
- `demand_forecast_ratio`: 기관 수요예측 경쟁률 (예: 850:1)
- `lockup_commitment_pct`: 의무보유확약 비율 + 기간 분포(15일·1/3/6개월)를 note에
- `retail_subscription_ratio`: 일반청약 경쟁률 (청약 마감 후에만)
- `allocation_structure`: 일반청약 균등/비례 구조·배정 물량
- `listing_day_price_range`: 상장일 가격 범위 = 공모가의 60~400% (제도 고정값)
- `underwriter_putback`: 환매청구권(풋백옵션) 유무·조건 (특례상장 등 해당 시)

한국 IPO의 `lockup` 블록은 미국식 계약 락업 대신 **최대주주 보호예수·기관 의무보유확약·상장주선인 의무인수분**을 주체별로 기재한다. greenshoe가 없는 구조면 `listing.greenshoe`는 `null` + note. `reporting_currency`는 `KRW`, `fx.USDKRW`는 비교 목적일 때만 기재.

## 3. free_float 정합성 — 단일 값 금지 [중요]

IPO에서 "유통물량"은 보도와 공시가 자주 어긋난다. **하나의 숫자로 박지 말고** 4개로 분리해 fact-checker/Judge가 갭을 인지하게 한다:

- `base_offering_float_pct` = `shares_offered_new / total` (신주only)
- `with_overallotment_float_pct` = `(new + greenshoe) / (total + greenshoe)`
- `reported_float_claim_pct` = 보도된 값(출처·status: press) — 신주only와 다르면 갭 명기
- `reconciliation_required: true` + note — 갭 사유(분모 차이, 추가 유통 물량, 추정 등)를 fact-checker가 규명

## 4. 생산자 숫자 self-check (저장 직전 필수)

스냅샷을 저장하기 전, JSON의 `self_check` 블록을 직접 계산해 채운다:

- `market_cap_recompute`: `ipo_price.value × post_ipo_shares.total.value`가 `valuation.market_cap_at_ipo.value`와 오차 <1%인가 → `pass`
- `proceeds_recompute`: `ipo_price.value × shares_offered_new.value`가 `gross_proceeds_est`와 합리적으로 일치하는가
- `free_float_recompute`: base/with_oa/reported를 재계산하고 `gap_shares`, `reconciled`(보도값이 공모로 설명되는지) 기록
- `overall`: 위 산술이 모두 맞으면 `"PASS"`, 시총·조달 산식이 어긋나면 `"FAIL"`

**`overall: "FAIL"`이면** 스냅샷을 그대로 내보내지 말고 `data_quality.notes`에 실패 항목을 적는다 — Phase 1.6 스냅샷 audit이 이를 ⛔하드 실패로 잡아 재수집을 트리거한다.

## 5. 미확보·상충·차단 처리 (data_quality)

**추측으로 채우지 않는다.**
- **미확보:** `value: null`, `confidence: "unavailable"`, `data_quality.unavailable_fields`에 필드 경로 추가.
- **상충:** 상위 문서값을 본 필드에, 하위/대안값과 사유를 `data_quality.conflicts[]`에 `{field, chosen, alternative, reason}`로 기록.
- **접근 차단(402/403/봇):** `insane-search` 우회 → 실패 시 미확보 표기.

## 6. 작성 전 검증 체크리스트

- [ ] 유효한 JSON인가 (`python -m json.tool _workspace_ipo/00_ipo_snapshot.json`).
- [ ] `as_of`, `company`, `ticker`, `market`, `exchange`가 채워졌는가.
- [ ] `listing`(공모가·신주·상장일), `post_ipo_shares`(total), `valuation.market_cap_at_ipo`가 채워졌거나 `unavailable`인가.
- [ ] `free_float`가 4필드로 분리되고 `reconciliation_required`/`note`가 있는가.
- [ ] `lockup`(musk/insiders/other + rule144_note)이 채워졌는가.
- [ ] 모든 가격 관련 값이 상장 전이면 `source_status: "preliminary"`인가.
- [ ] `self_check`를 직접 계산해 채웠고 `overall`이 PASS인가 (FAIL이면 notes에 사유).
- [ ] 모든 수치 필드에 `as_of`·`source`·`source_doc`이 있는가.
