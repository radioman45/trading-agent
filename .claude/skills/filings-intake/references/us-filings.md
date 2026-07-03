# 미국 공시 구조 매핑 (10-K / 10-Q)

미국 SEC 정기공시의 섹션 구조와 SSOT 추출 위치. 10-K(연차)와 10-Q(분기)는 항목 번호와 상세도가 다르다.

## 1. 문서 구조 (Item 매핑)

| 영역 | 10-K | 10-Q |
|------|------|------|
| 사업 개요 | Part I, Item 1 "Business" | (없음 — 10-K 참조) |
| 위험요인 | Part I, Item 1A "Risk Factors" | Part II, Item 1A (변경분만) |
| 경영진 논의 | Part II, Item 7 "MD&A" | Part I, Item 2 "MD&A" |
| 재무제표 | Part II, Item 8 (감사받은 연차) | Part I, Item 1 (검토받은 분기, "Condensed Consolidated") |
| 소송 | Part I, Item 3 "Legal Proceedings" | Part II, Item 1 |
| 시장위험 정량공시 | Part II, Item 7A | Part I, Item 3 |

> 10-Q는 "Condensed"(요약) 재무제표 + 직전 10-K 대비 변경 중심이다. 위험요인·사업개요가 빈약하면 "10-K 참조" 구조임을 인지하고 그 한계를 명시한다.

## 2. 재무제표 위치 및 계정 매핑

10-Q Part I Item 1의 표 3종(통상 문서 앞부분):

| SSOT 필드 | 미국 표/계정 (영문) | 비고 |
|-----------|---------------------|------|
| revenue | Statements of Operations → "Revenue" / "Net sales" | 분기·누적 2열 동시 게재 |
| cost_of_goods_sold | "Cost of goods sold" / "Cost of sales" | |
| gross_profit | "Gross margin" / "Gross profit" | 없으면 revenue−COGS 계산 |
| operating_income | "Operating income" | |
| net_income | "Net income" | 비지배지분 주의 |
| eps_diluted | "Diluted earnings per share" | |
| total_assets | Balance Sheets → "Total assets" | 기말 vs 직전 회계연도말 2열 |
| cash_and_equivalents | "Cash and equivalents" (+단기투자는 별도) | |
| inventories | "Inventories" | |
| accounts_receivable | "Receivables" / "Accounts receivable, net" | |
| total_debt | "Current debt" + "Long-term debt" 합산 | 합산 항목임을 source에 명시 |
| total_equity | "Total shareholders' equity" | |
| operating_cash_flow | Cash Flows → "Net cash provided by operating activities" | 보통 누적(YTD) |
| capex | "Expenditures for property, plant and equipment" | 부호 주의(유출은 음수 표기) |

## 3. 단위·기간 규칙

- **단위:** 표 머리글 "(in millions, except per share)" 또는 "(in thousands)"를 반드시 확인. EPS는 단위 미적용(달러/주).
- **기간:** 손익·현금흐름은 "Three Months Ended"(분기)와 "Nine/Six Months Ended"(누적)를 함께 싣는다 — SSOT에는 **분기(3M)를 기본**으로 고정하되 누적도 필요시 별도 기록. `period_label`에 명시.
- **재무상태표 기준일:** 분기말 vs 직전 회계연도말(예: 5월말 vs 8월말). `as_of`/`comparative_as_of` 구분.
- **회계연도:** 일부 기업은 비역년 회계연도(예: Micron 8월말 결산). `filing.fiscal_period`에 FY 표기.

## 4. 세그먼트·주석 위치

- **세그먼트:** Notes의 "Segment Information" / "Reportable Segments" — 부문별 revenue, 가능하면 operating income, 지역별("Revenue by geography"), 주요 고객(10% 이상 고객 공시).
- **위험·우발:** "Commitments and Contingencies", "Legal Proceedings", "Related Party Transactions", "Subsequent Events" 주석.
- **자사주·배당·부채:** "Debt", "Equity"/"Stockholders' Equity", 현금흐름표 재무활동.

## 5. 흔한 함정

- 분기값과 누적값을 혼동하지 말 것(가장 흔한 오류).
- "Net income attributable to [회사]"(지배지분)와 총순이익 구분.
- non-GAAP 조정치(Adjusted)는 GAAP 표가 아니라 MD&A·보도자료에 있다 — SSOT는 **GAAP 기본**, non-GAAP는 MD&A 렌즈가 별도로 다룬다.
- 부호: 현금흐름표의 CapEx·자사주매입은 음수로 표기된다 — 절대값으로 정규화하고 의미를 source에 명시.
