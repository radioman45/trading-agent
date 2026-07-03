---
name: filings-intake
description: 공시 분석용 단일 진실 소스(SSOT, 00_filings_facts.json) 추출 방법론. 제공된 공시 원문(미국 10-K/10-Q, 한국 DART 분기/반기/사업보고서)에서 회사정보·보고기간·통화·단위·재무 3표 핵심값·세그먼트·주식수를 외부 호출 없이 추출해 고정한다. filings-archivist 에이전트가 SSOT를 작성할 때, 또는 "공시 사실 고정", "SSOT 추출", "filings intake"를 요청받을 때 반드시 이 스킬을 사용한다.
---

# Filings Intake — 공시 SSOT 추출

공시 분석 파이프라인의 **단일 진실 소스(SSOT)**를 만든다. 4렌즈 분석가와 종합가가 각자 공시에서 숫자를 뽑으면 보고서마다 값·단위·기간이 달라진다. 이 스킬은 분석 시작 시점에 **제공된 공시 원문에서 객관적 사실값을 한 번만 고정**해, 모두가 같은 사실 위에서 서로 다른 해석을 하게 만든다.

**핵심 원칙 1 — 제공 파일만.** SSOT의 모든 값은 사용자가 제공한 공시 원문에서 실제로 읽은 것이어야 한다. 외부 웹·기억·다른 기간 공시에서 끌어오지 않는다. 못 찾으면 `unavailable`. 이 하네스의 가치는 "이 문서가 실제로 말하는 것"의 정확한 추출이다.

**핵심 원칙 2 — 정확도보다 일관성, 그러나 단위는 정확도.** 스냅샷은 "관점"이 아니라 "사실"이다. 다만 단위·기간 오인은 일관성의 문제가 아니라 1000배·기간혼동 왜곡이므로, 단위·기간만큼은 자가검산으로 정확성을 보장한다.

## 1. 공시 유형 감지

제공 파일과 `00_input.md`로 공시 유형을 판별하고, 해당 구조 매핑 reference를 읽는다:

| 유형 | 시장 | 구조 매핑 |
|------|------|----------|
| 10-K (연차) / 10-Q (분기) | 미국 (SEC) | `references/us-filings.md` |
| 사업보고서(연차)/반기보고서/분기보고서 | 한국 (DART) | `references/kr-filings.md` |

10-K↔사업보고서, 10-Q↔분기/반기보고서가 대응한다. 통화·단위·재무제표 위치가 다르므로 reference의 매핑 표를 따른다.

## 2. 추출 절차

1. 공시 원문을 Read로 직접 읽는다(PDF는 페이지 지정, 큰 파일은 재무제표·주석 페이지를 우선).
2. reference의 매핑에 따라 항목별 위치를 찾아 값을 읽는다.
3. **단위를 정규화한다.** 원문 표기 단위(예: "in millions", "단위: 백만원")를 확인해 모든 수치를 **원 단위 정수**로 변환한다. 정규화한 값과 원문 표기를 함께 기록한다.
4. **기간을 라벨링한다.** 각 손익·현금흐름 값이 분기(3개월)인지 누적(YTD)인지 연간인지 명시하고, 비교기간(전년동기/전기말) 값도 함께 고정한다.
5. 모든 값에 **출처(공시 내 위치)**를 붙인다.

## 3. JSON 스키마 (필수)

산출물은 `_workspace_filings/00_filings_facts.json`. 모든 수치 필드는 `{value, unit_raw, currency, period_label, as_of, source, confidence}` 구조다(`confidence`: `"high"|"medium"|"low"|"unavailable"`). `value`는 항상 원 단위 정수, `unit_raw`는 원문 표기(예: "백만 USD").

```json
{
  "schema_version": "1.0",
  "as_of": "2026-06-25",
  "company": "Micron Technology, Inc.",
  "ticker": "MU",
  "market": "US",
  "filing": {
    "type": "10-Q",
    "fiscal_period": "FY2026 Q3",
    "period_end": "2026-05-29",
    "comparative_period_end": "2025-05-30",
    "filed_date": "2026-06-xx",
    "currency": "USD",
    "reporting_unit_raw": "in millions except per share",
    "source_file": "sources/IR-Micron/Micron_10Q.pdf"
  },

  "income_statement": {
    "revenue":            { "value": null, "unit_raw": "백만 USD", "currency": "USD", "period_label": "Q (3M)", "as_of": "2026-05-29", "source": "10-Q p.X Consolidated Statements of Operations", "confidence": "high",
                            "comparative": { "value": null, "period_label": "Q (3M) 전년동기", "as_of": "2025-05-30" } },
    "cost_of_goods_sold": { "value": null, "unit_raw": "백만 USD", "currency": "USD", "period_label": "Q (3M)", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" },
    "gross_profit":       { "value": null, "unit_raw": "백만 USD", "currency": "USD", "period_label": "Q (3M)", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" },
    "operating_income":   { "value": null, "unit_raw": "백만 USD", "currency": "USD", "period_label": "Q (3M)", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" },
    "net_income":         { "value": null, "unit_raw": "백만 USD", "currency": "USD", "period_label": "Q (3M)", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" },
    "eps_diluted":        { "value": null, "unit_raw": "USD/주", "currency": "USD", "period_label": "Q (3M)", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" }
  },

  "balance_sheet": {
    "as_of": "2026-05-29",
    "comparative_as_of": "2025-08-28",
    "total_assets":        { "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "10-Q p.X Balance Sheets", "confidence": "high" },
    "cash_and_equivalents":{ "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" },
    "inventories":         { "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" },
    "accounts_receivable": { "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "medium" },
    "total_debt":          { "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "10-Q p.X (단기+장기차입)", "confidence": "medium" },
    "total_equity":        { "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" }
  },

  "cash_flow": {
    "period_label": "YTD (누적)",
    "operating_cash_flow": { "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "10-Q p.X Cash Flows", "confidence": "high" },
    "capex":               { "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "10-Q p.X", "confidence": "high" },
    "free_cash_flow":      { "value": null, "unit_raw": "백만 USD", "currency": "USD", "as_of": "2026-05-29", "source": "OCF−CapEx 계산", "confidence": "medium" }
  },

  "segments": [
    { "name": "예: Compute and Networking", "revenue": { "value": null, "unit_raw": "백만 USD", "period_label": "Q (3M)", "as_of": "2026-05-29", "source": "10-Q 세그먼트 주석", "confidence": "high" },
      "operating_income": { "value": null, "unit_raw": "백만 USD", "as_of": "2026-05-29", "source": "10-Q 세그먼트 주석", "confidence": "medium" } }
  ],

  "shares": {
    "diluted_weighted_avg": { "value": null, "currency": null, "period_label": "Q (3M)", "as_of": "2026-05-29", "source": "10-Q 손익 하단", "confidence": "high" }
  },

  "data_quality": {
    "unavailable_fields": [],
    "arithmetic_checks": [],
    "notes": "스키마 예시. 실제 추출 시 value를 원문에서 채우고 source 위치를 갱신할 것. 항목명·세그먼트는 회사·공시에 맞게 조정."
  }
}
```

스키마 규칙:
- `value`는 **항상 원 단위 정수**(축약 금지). 단위 미상이면 `unavailable`.
- 항목명은 회사·공시에 맞게 조정한다(위 예시는 미국 10-Q 기준). 한국 DART는 `references/kr-filings.md`의 계정 매핑을 따른다(연결 우선).
- 공시에 없는 표(예: 10-Q에 부문 영업이익 미공시)는 해당 필드를 `unavailable`로 둔다.
- `segments`는 회사 공시의 보고부문 수만큼 배열로 둔다. 부문이 단일이면 빈 배열 + `notes`에 "단일 보고부문".

## 4. 작성 전 검증 체크리스트 [HARD]

SSOT 저장 직전 확인한다:

- [ ] 유효한 JSON인가 — `python -m json.tool _workspace_filings/00_filings_facts.json`.
- [ ] `filing`의 type·fiscal_period·period_end·currency·reporting_unit_raw·source_file이 채워졌는가.
- [ ] **단위 자가검산:** 정규화한 `value`를 `unit_raw`로 되돌려 원문 표기와 일치하는가(예: 8,460,000,000 ÷ 1e6 = 8,460 백만 ✓).
- [ ] **산술 정합:** 매출−매출원가=매출총이익, 자산=부채+자본, 세그먼트 매출 합≈전사 매출(반올림 명시). 불일치를 `data_quality.arithmetic_checks`에 기록.
- [ ] **기간 정합:** 손익·현금흐름의 `period_label`(분기/누적/연간)이 원문과 일치하고 비교기간이 함께 고정됐는가.
- [ ] 모든 수치에 `source`(공시 내 위치)와 `as_of`가 있는가.
- [ ] 못 구한 값이 `unavailable` + `unavailable_fields`에 반영됐는가(추측으로 채우지 않았는가).
