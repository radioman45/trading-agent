엌[# Codex Trading Harness Review

작성일: 2026-07-04

범위: `trading-agent` 저장소의 Trading, IPO, Filings 하네스 운영 설계와 현재 산출물 기준 개선안.

비목표: 이 문서는 구현 변경을 하지 않는다. 코드, 프롬프트, 스크립트, 에이전트 정의를 수정하지 않고 개선 방향만 정리한다.

## 1. 요약 판단

현재 하네스는 단순한 다중 에이전트 프롬프트 묶음보다 훨씬 낫다. 역할 분리, 파일 기반 fan-out/fan-in, fact-check gate, risk committee, portfolio impact, journal/calibration 같은 감사 가능한 구조가 있다.

그러나 신뢰도의 병목은 에이전트 수나 보고서 길이가 아니라, 실패 조건을 시스템이 얼마나 기계적으로 강제하느냐에 있다. 현재는 핵심 검증 중 상당수가 LLM 프롬프트 절차와 문서 규율에 의존한다. 따라서 운영자가 보기에는 매우 엄격해 보이지만, 실제로는 "경고 후 진행", "downgrade 후 진행", "조건부 승인"으로 흡수되는 경로가 많다.

가장 중요한 개선 방향은 다음 세 가지다.

1. 문서와 실행 규칙의 단일 기준을 만들고 drift를 없앤다.
2. 하드 게이트를 프롬프트가 아니라 기계적 검증으로 강제한다.
3. portfolio-aware, fact-checked, approved 같은 라벨을 실제 충족 조건과 일치시킨다.

## 2. 관찰 근거

주요 근거 파일:

- `README.md`: 하네스 수, 에이전트 수, 스킬 수, 모델 설명이 현재 구조와 맞지 않는다.
- `CLAUDE.md`: Trading, IPO, Filings 3개 하네스를 설명하며 최근 hallucination guard와 audit fix를 기록한다.
- `docs/harness-architecture.md`: orchestrator skills를 SSOT로 둔다고 명시한다.
- `.claude/skills/trading-strategy/SKILL.md`: Trading orchestration, fact-check, risk, portfolio, report generation 절차를 정의한다.
- `.claude/skills/ipo-analysis/SKILL.md`: IPO collector, snapshot audit, fact-check, red-team, verdict 절차를 정의한다.
- `.claude/skills/filings-analysis/SKILL.md`: filings-only, no trading decision, extraction gate, red-team 절차를 정의한다.
- `.claude/skills/risk-gate/SKILL.md`: risk committee와 PM gate 판정 기준을 정의한다.
- `.claude/skills/portfolio-risk/SKILL.md`: portfolio impact와 downgraded mode를 정의한다.
- `.claude/skills/market-snapshot/scripts/collect_market_data.py`: 실제 자동 수집 스크립트는 yfinance 중심이며 세션/공식 fallback 검증이 제한적이다.
- `docs/anti-hallucination-verification-plan.md`: SOL 환각 사고와 향후 scriptify 필요성을 기록한다.
- `_workspace/00_factcheck.md`, `_workspace/06_final_decision.md`: 실제 산출물에서 warning이 남아 있어도 최종 승인으로 이어질 수 있음을 보여준다.
- `decisions/portfolio.json`: 현재 holdings가 비어 있어 portfolio-aware 판단이 제한된다.
- `decisions/calibration.md`: calibration scaffold는 있으나 확정 outcome과 Brier 계산이 아직 충분하지 않다.

## 3. 핵심 리스크

### R1. SSOT 혼선

문서상 기준이 여러 곳에 흩어져 있다. `README.md`, `CLAUDE.md`, `docs/harness-architecture.md`, 각 `SKILL.md`가 서로 다른 수준의 진실을 말한다.

문제:

- README는 "두 개의 하네스"라고 설명하지만 현재 구조는 Trading, IPO, Filings 세 개다.
- README의 agents/skills 수와 모델 설명이 실제 파일 상태와 맞지 않는다.
- `docs/harness-architecture.md`는 orchestrator skills가 SSOT라고 하지만 사용자는 README나 CLAUDE를 먼저 볼 가능성이 높다.

영향:

- 새 실행자나 에이전트가 오래된 문서를 기준으로 잘못 실행할 수 있다.
- 하네스가 프롬프트 기반일수록 문서 drift는 곧 실행 drift가 된다.
- "무엇이 반드시 실행되어야 하는지"가 모호해진다.

개선안:

- `HARNESS_MANIFEST.md` 또는 `HARNESS_MANIFEST.json`을 단일 manifest로 둔다.
- manifest에는 harness 목록, phase 목록, 필수 산출물, optional 산출물, gate semantics, active agent/skill 수, model policy를 기록한다.
- README는 manifest 요약만 포함하게 한다.
- `CLAUDE.md`는 운영 지침, `docs/harness-architecture.md`는 설계 설명, `SKILL.md`는 실행 절차로 역할을 나눈다.
- manifest와 실제 파일 구조가 다르면 검증 실패로 표시한다.

수용 기준:

- 하네스 개수, agent 수, skill 수가 자동 집계와 일치한다.
- README에 직접 숫자를 중복 기록하지 않는다.
- 새 하네스 추가 시 manifest 변경 없이는 완료로 볼 수 없다.

## 4. Gate Semantics 개선

### R2. "Hard gate"가 실제로는 soft continuation인 문제

현재 Trading fact-check는 문제가 있으면 source를 한 번 재호출하고, 그래도 실패하면 값을 `미확인`으로 낮춘 뒤 계속 진행한다. IPO와 Filings도 일정 횟수 후 unavailable 또는 downgrade로 진행할 수 있다.

이 방식은 throughput에는 좋지만, 투자 의사결정 하네스에서 `HARD`, `PASS`, `APPROVE` 같은 표현과 결합되면 위험하다. 사용자는 "막혔어야 할 문제"가 조건부 승인으로 흡수된 사실을 놓칠 수 있다.

개선안:

- gate를 세 등급으로 분리한다.
  - `BLOCKING`: 실패 시 최종 투자 판단 생성 금지
  - `DEGRADED`: 최종 판단은 가능하지만 라벨에 degraded mode 필수 표시
  - `ADVISORY`: 경고로만 남김
- 현재 `[HARD]`라고 되어 있으나 downgrade 후 진행 가능한 항목은 `DEGRADED`로 이름을 바꾼다.
- 최종 보고서 첫 화면에 mode를 강제 표시한다.
  - `FULLY_VERIFIED`
  - `DEGRADED_DATA`
  - `SINGLE_TRADE_ONLY`
  - `RESEARCH_ONLY`
  - `BLOCKED`
- `APPROVE`는 `FULLY_VERIFIED` 또는 명시적으로 허용된 degraded profile에서만 가능하게 한다.

수용 기준:

- gate failure가 있을 때 최종 산출물의 decision label이 자동으로 제한된다.
- `BLOCKING` 실패가 있으면 `APPROVE`가 나오지 않는다.
- downgrade된 항목은 final decision 상단에 요약된다.

## 5. 기계적 검증 레이어

### R3. 검증이 LLM 판정에 과도하게 의존

현재 하네스의 핵심 검증은 대부분 agent가 파일을 읽고 판단하는 방식이다. 실제 자동 스크립트는 제한적이며, 시장 데이터 스크립트와 NotebookLM audio 정도가 중심이다.

문제:

- 산술 합계 오류, 날짜/세션 오류, source count 부족, stale data, missing artifact는 스크립트로 잡아야 한다.
- LLM fact-checker는 유용하지만 마지막 방어선이 되면 안 된다.
- 같은 원자료를 여러 agent가 다르게 해석해도 mechanical reconciliation이 부족하다.

개선안:

- `harness doctor` 성격의 검증 스크립트를 둔다.
- 검증 대상:
  - 필수 workspace 파일 존재 여부
  - report 파일 존재 여부
  - phase별 산출물 freshness
  - `as_of`, `market_session`, `source_url`, `retrieved_at` 존재 여부
  - 숫자 합계, 퍼센트 범위, 음수/양수 부호 일관성
  - 가격 stale 여부
  - official source 또는 fallback source 충족 여부
  - portfolio 파일 로딩 여부
  - final decision이 gate 결과와 모순되지 않는지
- 검증 결과는 사람이 읽는 Markdown뿐 아니라 machine-readable JSON으로 남긴다.

수용 기준:

- Trading full run 후 `harness doctor`가 green이어야 `APPROVE` 라벨을 사용할 수 있다.
- doctor 실패 시 final report 생성은 가능해도 decision label은 `BLOCKED` 또는 `DEGRADED`로 제한된다.
- doctor 결과가 `reports/`에 함께 보존된다.

## 6. Market Data와 Anti-Hallucination

### R4. live market data 검증 경계가 약함

`collect_market_data.py`는 yfinance 중심이다. 문서에는 Stooq/KRX fallback, 세션 상태, 날짜 anchor, arithmetic assert 같은 보강 방향이 기록되어 있으나 코드 레벨 보장은 제한적이다.

문제:

- 장 시작 전, 휴장일, 지연 데이터, ticker mismatch 같은 문제가 다시 발생할 수 있다.
- agent가 "오늘 시장"을 말할 때 실제로 어떤 시각의 어떤 소스를 기준으로 했는지 약하다.
- live data와 LLM 추론이 섞이면 사실과 해석의 경계가 흐려진다.

개선안:

- 모든 market snapshot에 다음 필드를 의무화한다.
  - `ticker`
  - `exchange`
  - `requested_at`
  - `data_as_of`
  - `market_session`
  - `source_primary`
  - `source_secondary`
  - `staleness_seconds`
  - `calendar_status`
  - `price_currency`
- 한국장은 KRX calendar 또는 공식 영업일 캘린더를 기준으로 session을 판정한다.
- 장전/장중/장후/휴장일에 따라 허용 문구를 분리한다.
  - 장전: "전일 종가 기준"
  - 장중: "지연 가능 실시간 데이터"
  - 장후: "당일 종가 확정 여부 확인 필요"
  - 휴장: "최근 거래일 기준"
- source fallback은 prompt 지시가 아니라 수집 레이어에서 명시적으로 기록한다.
- 가격/등락률/거래량은 최소 2개 소스 불일치 허용 범위를 정의한다.

수용 기준:

- market snapshot에 session과 staleness가 없으면 macro/trader phase로 넘기지 않는다.
- "오늘", "현재", "장중" 표현은 session 필드와 일치할 때만 허용한다.
- source mismatch가 임계값을 넘으면 `DEGRADED_DATA`로 내려간다.

## 7. Portfolio Layer 강화

### R5. Portfolio-aware claim이 현재 보장되지 않음

portfolio-risk 설계는 좋지만 `decisions/portfolio.json`이 비어 있으면 downgraded mode로 동작한다. 이 상태에서는 실제 포트폴리오 concentration, correlation, aggregate tail loss를 계산할 수 없다.

문제:

- portfolio-aware 판단처럼 보이지만 실제로는 single-campaign risk만 본다.
- 사용자가 보유 종목을 등록하지 않은 상태에서도 PM gate가 portfolio impact를 충분히 반영한 것처럼 보일 수 있다.
- 현재 산출물에는 `_workspace/05_portfolio_impact.md`가 항상 보장되지 않는 흔적이 있다.

개선안:

- `portfolio.json` 상태에 따라 final label을 강제한다.
  - holdings 있음: `PORTFOLIO_AWARE`
  - holdings 없음: `SINGLE_TRADE_ONLY`
  - holdings stale: `PORTFOLIO_STALE`
- Trading run의 필수 산출물에 `_workspace/05_portfolio_impact.md`를 넣는다.
- holdings가 비어 있어도 portfolio-impact 파일은 생성하되, "actual holdings unavailable"을 명시한다.
- portfolio state에 `last_reviewed_at`, `source`, `cash_pct`, `holdings[].as_of`를 추가하는 운영 규칙을 둔다.
- PM gate는 portfolio mode를 checklist 최상단에서 확인한다.

수용 기준:

- holdings가 비어 있으면 최종 결론에 "portfolio-aware" 표현을 금지한다.
- portfolio impact 파일이 없으면 PM gate가 `APPROVE`를 낼 수 없다.
- portfolio stale이면 신규 매수 비중 cap을 자동 제한한다.

## 8. PM Gate와 Warning Accumulation

### R6. 경고 누적이 조건부 승인으로 흡수되는 문제

현재 risk committee가 여러 경고를 내도 fatal이 없으면 PM이 조건을 붙여 승인할 수 있다. 이는 빠른 의사결정에는 좋지만, 여러 독립 경고가 같은 방향을 가리킬 때 과신을 만들 수 있다.

개선안:

- warning accumulation rule을 추가한다.
  - 같은 축에서 major warning 2개 이상: `REVISE`
  - 서로 다른 축에서 major warning 3개 이상: 기본 `REVISE`, PM override 시 별도 justification 필요
  - load-bearing fact 미확인 1개 이상: `DEGRADED_DATA`, position cap 적용
  - thesis-critical source 미확인: `BLOCKING` 또는 `REJECT`
- PM final decision에 다음 항목을 의무화한다.
  - accepted warnings
  - rejected warnings
  - warning-to-condition mapping
  - why not revise
  - max position under uncertainty
- `APPROVE`와 `CONDITIONAL_APPROVE`를 분리한다.

수용 기준:

- 경고가 조건으로 흡수될 때 원래 경고 ID가 최종 보고서에 남는다.
- PM이 `REVISE`하지 않은 이유를 명시하지 않으면 doctor 실패.
- major warning 누적 기준을 넘으면 일반 `APPROVE`가 불가능하다.

## 9. Calibration과 Learning Loop

### R7. 학습 루프가 아직 성능 피드백으로 닫히지 않음

`decisions/calibration.md`와 `journal.md`는 좋은 시작점이지만, 확정 outcome과 Brier 계산이 충분히 쌓이지 않았다. 따라서 현재는 "학습하는 구조"이지 "성능이 검증된 구조"는 아니다.

개선안:

- 모든 확률 판단에 `horizon`, `resolution_date`, `resolution_source`, `owner`를 붙인다.
- 만기 도래 전에는 Brier를 계산하지 않는다.
- 만기 도래 후 unresolved 항목을 자동으로 추려내는 review queue를 만든다.
- calibration bucket별로 최소 표본 수를 요구한다.
- future run에서 lesson을 참조할 때, lesson의 evidence grade를 표시한다.
  - `A`: 다수 outcome으로 검증
  - `B`: 단일 사건 회고
  - `C`: 원칙적 추론
  - `D`: 미검증 가설

수용 기준:

- calibration row는 `p`, `o`, `brier`, `horizon`, `resolution_date`를 갖는다.
- unresolved가 일정 기간 넘으면 final report에 "learning debt"로 표시한다.
- lesson이 trading decision을 막는 근거로 쓰이면 evidence grade가 필요하다.

## 10. Artifact Completeness

### R8. 설계상 필수 산출물과 실제 산출물이 어긋날 수 있음

Trading skill은 factcheck, portfolio impact, final decision, final report, plain explanation 등을 정의한다. 그러나 기존 workspace/report 흔적을 보면 최신 규칙이 모든 실행에서 일관되게 반영되었다고 보기 어렵다.

개선안:

- phase별 required artifact matrix를 만든다.
- 예시:
  - Phase 0: `_workspace/00_input.md`
  - Phase 1: `_workspace/01_macro.md`, `_workspace/01_market_data.md`
  - Phase 1.6: `_workspace/00_factcheck.md`
  - Phase 2: lens reports
  - Phase 3: bull/bear reports
  - Phase 4: trade plan
  - Phase 5: risk x3, `_workspace/05_portfolio_impact.md`
  - Phase 6: `_workspace/06_final_decision.md`
  - Phase 7: reports copied to `reports/`
- 각 artifact에 run id를 포함한다.
- final report는 같은 run id의 파일만 참조한다.

수용 기준:

- 누락 artifact가 있으면 run status는 incomplete다.
- 서로 다른 run id의 파일이 섞이면 doctor 실패.
- report copy 누락은 approval 실패가 아니라 publication failure로 별도 표시한다.

## 11. Cost와 Complexity 관리

### R9. 복잡성이 신뢰도처럼 보이는 착시

현재 agent/skill 수가 많고, 대부분 고성능 모델을 쓰는 방향이다. 감사 추적에는 장점이 있지만 비용, 지연, 중복 판단, 책임 경계 흐림을 만든다.

개선안:

- 실행 모드를 세분화한다.
  - `quick-triage`: 데이터 스냅샷, red flag, no trade decision
  - `standard`: core research, fact-check, risk, PM
  - `full-committee`: 모든 lens, bull/bear, risk x3, portfolio, report
  - `postmortem`: journal, calibration, lessons 전용
- easy explainer와 podcast prompt는 기본 non-blocking optional로 둔다.
- 동일한 판단을 반복하는 agent는 phase 목적을 재정의하거나 병합한다.
- full-committee는 포지션 규모, thesis uncertainty, 사용자 명시 요청에 따라만 실행한다.

수용 기준:

- 사용자가 full run을 요청하지 않아도 기본적으로 과도한 비용이 발생하지 않는다.
- quick mode에서는 투자 권고 문구를 금지한다.
- full mode에서는 누락된 검증이 있으면 decision label이 제한된다.

## 12. IPO Harness 개선

### R10. IPO verdict도 red-team 이후 재검증 깊이가 제한적

IPO harness는 snapshot audit, fact-check, bull/bear, verdict reviewer가 있어 구조가 좋다. 다만 red-team rewrite가 최대 1회에 그치고, 그 후 기계적 재검증이 충분히 강제되지 않는다.

개선안:

- IPO snapshot의 필수 수치 필드를 schema로 고정한다.
  - 공모가 범위
  - 확정 공모가
  - 수요예측 경쟁률
  - 의무보유확약
  - 일반청약 경쟁률
  - 유통가능물량
  - 상장일
  - 주관사
  - peer valuation
- red-team 후에는 rewritten verdict를 다시 fact-check한다.
- unavailable 필드가 thesis-critical이면 final verdict를 `NO_DECISION` 또는 `INSUFFICIENT_DATA`로 제한한다.

수용 기준:

- IPO final verdict는 critical field completeness score를 표시한다.
- snapshot audit fail 후 unavailable이 남으면 verdict label이 자동 제한된다.
- red-team critical issue가 해소되지 않으면 `APPROVE/SUBSCRIBE` 성격의 결론 금지.

## 13. Filings Harness 개선

### R11. "Provided files only" 원칙은 좋지만 provenance 강제가 필요

Filings harness는 no trading decision, provided files only를 명시해 범위가 가장 깨끗하다. 다만 extracted claim이 원문 어느 위치에서 왔는지 추적이 더 강해야 한다.

개선안:

- 모든 주요 claim에 source anchor를 붙인다.
  - file name
  - page 또는 section
  - quote span
  - extraction confidence
- 추론과 원문 사실을 분리한다.
  - `extracted_fact`
  - `derived_interpretation`
  - `open_question`
- no-trading-decision rule 위반을 doctor가 검사한다.
- filings synthesis가 trading harness로 넘어갈 경우 별도 handoff 파일을 만들고, "이 문서는 투자 판단이 아니다"를 유지한다.

수용 기준:

- source anchor 없는 핵심 claim은 final report에 들어갈 수 없다.
- buy/sell/hold 표현이 있으면 filings doctor 실패.
- derived interpretation은 extracted fact와 연결되어야 한다.

## 14. Report UX와 Safety Labeling

### R12. 최종 보고서가 조건과 제한을 충분히 전면화해야 함

현재 final decision은 조건을 포함하지만, 사용자가 첫 화면에서 "얼마나 검증된 결정인지"를 즉시 파악하기 어렵다.

개선안:

최종 보고서 상단에 다음 summary box를 강제한다.

- Decision: `APPROVE`, `CONDITIONAL_APPROVE`, `REVISE`, `REJECT`, `NO_DECISION`
- Verification mode: `FULLY_VERIFIED`, `DEGRADED_DATA`, `SINGLE_TRADE_ONLY`, `RESEARCH_ONLY`
- Blocking issues: count and labels
- Major warnings: count and labels
- Portfolio mode: `PORTFOLIO_AWARE`, `SINGLE_TRADE_ONLY`, `PORTFOLIO_STALE`
- Data freshness: timestamp and session
- Max suggested risk: position size cap and loss cap
- User action required: yes/no

수용 기준:

- 사용자는 보고서 첫 20줄 안에서 decision confidence와 제한 조건을 볼 수 있다.
- caveat가 본문 하단에만 묻히지 않는다.
- warning count와 label이 final decision과 모순되지 않는다.

## 15. 권장 우선순위

### P0. 즉시 정리

1. README/CLAUDE/docs/SKILL 간 SSOT 정리
2. gate 용어 정리: `BLOCKING`, `DEGRADED`, `ADVISORY`
3. portfolio-empty 상태에서 `portfolio-aware` 표현 금지
4. final report 상단에 verification mode 표시
5. artifact completeness matrix 정의

### P1. 신뢰도 상승

1. `harness doctor` 설계
2. market snapshot schema와 stale/session 검증
3. warning accumulation rule
4. PM override justification
5. calibration resolution queue

### P2. 운영 효율

1. quick/standard/full/postmortem 실행 모드 분리
2. optional 산출물 분리
3. 중복 agent 역할 정리
4. report publication failure와 analysis failure 분리
5. model policy 비용 최적화

## 16. 최소 개선 패키지

가장 적은 변경으로 신뢰도를 크게 올리는 패키지는 다음이다.

1. Manifest 도입
   - harness, phase, required artifact, gate type, final label policy를 한 파일에 기록한다.

2. Final label policy 도입
   - `APPROVE`가 나오기 위한 최소 조건을 문서화한다.
   - 조건 미충족 시 자동으로 `CONDITIONAL_APPROVE`, `REVISE`, `NO_DECISION`으로 낮춘다.

3. Portfolio mode 명시
   - holdings가 비어 있으면 `SINGLE_TRADE_ONLY`.
   - portfolio impact 파일은 항상 생성.

4. Doctor 설계 문서화
   - 구현은 나중에 하더라도 어떤 검증을 기계화할지 먼저 고정한다.

5. Report summary box 표준화
   - decision, verification mode, warning count, portfolio mode, freshness를 상단에 고정한다.

## 17. 하지 말아야 할 개선

- agent 수를 더 늘리는 것부터 시작하지 않는다. 문제는 위원 수가 아니라 강제 검증 부재다.
- 모든 경고를 fatal로 만들지 않는다. 그러면 실무 사용성이 떨어진다.
- LLM reviewer를 하나 더 붙여 mechanical validation을 대체하지 않는다.
- portfolio holdings가 없는 상태에서 portfolio-aware UX를 유지하지 않는다.
- README에 수동 숫자와 절차를 계속 중복 기록하지 않는다.

## 18. 최종 평가

이 하네스는 감사 가능한 투자 리서치 시스템으로 발전할 가능성이 크다. 특히 role separation, fact-check loop, risk committee, journal/calibration scaffold는 방향이 맞다.

하지만 현재 가장 큰 약점은 "엄격해 보이는 절차"와 "실제로 강제되는 불변조건" 사이의 간격이다. 투자 판단에서는 이 간격이 곧 리스크다.

다음 단계의 목표는 더 많은 agent를 붙이는 것이 아니라, 다음 문장을 사실로 만드는 것이다.

> 승인된 결론은 반드시 동일 run의 필수 산출물, 검증된 데이터 freshness, portfolio mode, warning threshold, final gate policy를 모두 통과했다.

이 문장이 기계적으로 검증되면, 현재 하네스는 보고서 생성 자동화가 아니라 신뢰 가능한 decision-support harness에 가까워진다.
