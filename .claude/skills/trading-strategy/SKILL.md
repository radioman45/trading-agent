---
name: trading-strategy
description: 투자전략 트레이딩 하네스 오케스트레이터(TradingAgents 구조 + 뉴로퓨전/월가아재 톱다운 보강). 거시 전략가가 시장 레짐(risk-on/off·유동성·바벨)을 먼저 판정하고, 시장 데이터 엔지니어가 스냅샷·기술지표로 고정하며, 분석가 4명(기본적·기술적·뉴스·심리)이 병렬 분석, Bull/Bear 리서처가 2라운드 토론, 리서치 매니저가 판정해 투자 계획 수립, 트레이더가 거래 계획(진입·손절·비중·목표) 변환, 리스크 토론자 3성향(공격/중립/보수)+포트폴리오 리스크 분석가가 병렬 평가, 포트폴리오 매니저가 거시·바벨·역발상·포트폴리오 게이트로 최종 APPROVE/CONDITIONAL_APPROVE/REVISE/REJECT 판정 후 의사결정 저널에 기록하는 파이프라인을 조율한다. "트레이딩 분석", "투자전략 분석", "{티커} 매매 판단", "사야 돼 팔아야 돼", "트레이딩 전략 세워줘", "거래해도 될까", "포지션 잡아도 될까", "투자 분석", "거시 레짐", "시장 국면" 요청 시 반드시 이 스킬을 사용한다. 능동 모드도 처리한다: "아이디어 스캔", "종목 발굴", "뭐 살까", "살 만한 종목", "워치리스트", "포지션 점검", "트리거 점검", "보유 등록", "포트폴리오 등록", "체결 반영", "실제로 샀어". 후속 요청도 처리한다: "다시 실행", "재실행", "업데이트", "거시만 다시", "레짐 갱신", "분석가 보고서만 다시", "토론 한 라운드 더", "강세론/약세론 보강", "판정만 다시", "거래계획만 다시", "리스크 검토만 다시", "최종 결정만 다시", "이전 결과 기반으로", "결과 개선", "복기", "결과 반영". 단, 단순 주가 조회나 일반 투자 상식 질문은 직접 응답해도 된다.
---

# Trading Strategy — 투자전략 트레이딩 하네스

[TradingAgents](https://github.com/tauricresearch/tradingagents)의 멀티에이전트 트레이딩 펌 구조 + 뉴로퓨전/월가아재 톱다운 매크로 보강. **14명의 전문가가 6계층 + 능동 소싱·포트폴리오 레이어**로 분업한다:

```
[소싱(별도 진입)] idea-scanner ── 레짐→후보 발굴·워치리스트 (티커 없는 "뭐 살까" 요청 시)
[L0 거시]     macro-strategist ── 시장 레짐(risk-on/off·유동성·사분면·바벨) 판정  ┐
[L1 데이터]   market-data-engineer ── 스냅샷+기술지표 SSOT 고정                  ┘ (병렬, 종목 무관 vs 종목 사실)
[L2 분석]     fundamental ∥ technical ∥ news ∥ sentiment ── 4렌즈 병렬 (거시 레짐을 배경으로)
[L3 리서치]   bull ↔ bear 2라운드 토론 → research-manager 판정(역발상·기회비용) → 투자 계획
[L4 실행]     trader ── 거래 계획 (진입·손절·비중·목표·손익비·꼬리 검산)
[L5 게이트]   risk-debater ×3 (공격∥중립∥보수) ∥ portfolio-risk-analyst (보유 북 영향)
                → portfolio-manager 최종 판정(거시·역발상·포트폴리오·기회비용 게이트)
                                                  └─ decisions/journal.md 기록
[공용]        contrarian-check ── 역발상 메타인지 (L0·L3·L5 판단 에이전트가 참조)
[학습 루프]   trade-reflection ── 결과 복기 → decisions/lessons.md·calibration.md → 다음 실행에 주입
[상태]        decisions/portfolio.json(보유 SSOT)·watchlist.md ── 세션 간 지속
```

**실행 모드: 서브 에이전트 (파이프라인 + 팬아웃/팬인 + 생성-검증).** 에이전트 팀이 아니다 — Bull/Bear 라운드 1과 리스크 토론자 3명은 서로의 산출물을 **봐서는 안 되므로**(독립 관점이 정보량의 원천), 실시간 통신 대신 파일로만 전달한다. L0 거시와 L1 데이터는 서로 의존하지 않아 **병렬**로 실행한다(거시는 종목 무관, 스냅샷은 종목 사실). 토론의 교차는 라운드 2에서 오케스트레이터가 파일을 건네는 방식으로 통제한다. 계층별 라우팅: 저부하=sonnet, 생성·판단 코어=opus 명시. **톱다운 원칙:** 레짐이 종목 선택보다 상위 게이트 — 좋은 종목도 투자 환경이 불리하면 무력하다.

**게이트 등급 (라벨-실체 일치, 2026-07-04):** 게이트는 실패 시 행동으로 3등급을 구분해 부른다 — **BLOCKING**(실패 시 파이프라인 중단. 예: 공시 하네스 D0 SSOT 추출 실패, IPO Bull·Bear 양측 실패), **DEGRADED**(수복 실패 시 해당 수치를 "미확인"/unavailable로 강등하고 진행하되 최종 보고·검증 모드에 표기 의무. 예: Phase 1.6, IPO 스냅샷 audit — 수복 3회 후 강등·진행이므로 DEGRADED다), **ADVISORY**(경고 기록만). 강등 후 진행을 허용하는 게이트를 "하드 게이트"라 부르면 라벨이 실체를 과장한다 — 사용자가 조건부 승인 속에 흡수된 문제를 놓치게 되므로, 등급을 정직하게 명명한다.

## Phase 0: 컨텍스트 확인

`_workspace/`와 사용자 요청을 대조해 실행 모드를 결정한다:

| 상황 | 모드 | 행동 |
|------|------|------|
| `_workspace/` 없음 | **초기 실행** | Phase 1부터 전체 |
| 있음 + 새 종목 지정 | **새 실행** | 기존을 `_workspace_prev/{티커}_{날짜}/`로 이동 후 전체 |
| 있음 + 부분 수정 요청 | **부분 재실행** | 해당 에이전트만 재호출, 하류는 의존성 따라 갱신 |
| "복기"/"결과 반영" | **복기 모드** | Phase R로 — 파이프라인 실행 안 함 |
| 티커 없이 "뭐 살까"/"아이디어 스캔"/"종목 발굴"/"워치리스트" | **스캔 모드** | Phase S로 — 파이프라인 실행 안 함 |
| "포지션 점검"/"트리거 점검" | **모니터링 모드** | Phase M으로 — 열린 결정의 무효화 트리거 점검 |
| "보유 등록/갱신"/"체결 반영"/"실제로 샀어" | **상태 갱신 모드** | Phase P로 — `decisions/portfolio.json`·journal 실행 줄 갱신 |

**워크스페이스 회전 규칙:** 새 실행 시 기존 `_workspace/` 내용물은 `_workspace_prev/{티커}_{날짜}/` 하위 폴더로 이동한다(임의 접미사 `_prev_1/2` 금지). `_workspace_prev/` 하위가 5개를 넘으면 가장 오래된 것을 `_archive/`로 옮긴다 — 감사 추적은 보존하되 활성 경로를 오염시키지 않는다.

**부분 재실행 의존성:** 거시 레짐 갱신("거시만 다시"/"레짐 갱신") → 하류 전체가 배경 레짐을 다시 읽으므로 분석가부터 재실행(스냅샷은 유지 가능). 스냅샷 갱신 → 전체 재실행(최상류). 분석가 보고서 갱신 → 토론부터 하류 전체. 토론/판정 갱신 → 트레이더부터. 거래 계획 갱신 → 리스크 토론부터. 리스크 토론 갱신 → 최종 게이트만. "토론 한 라운드 더" → R3 append 후 판정부터 하류.

## Phase 1: 입력 수집 + L0 거시·L1 데이터 고정 (병렬)

1. 분석 대상(회사명/티커) 확인. 없으면 사용자에게 묻는다. 사용자 맥락(성향·기간·보유 여부)은 선택 — 없으면 3성향 분기로 진행.
   - **현재 시각·세션 앵커 고정 [HARD]:** 진행 전 **현재 날짜·시각(요일 포함)과 대상 시장의 세션 상태**(개장 전 / 장중 / 마감)를 `date` 등으로 확인해 `00_input.md`에 기록한다. 모든 하류 에이전트는 이 앵커 기준으로 "마감된 세션의 수치만 사실"로 다룬다(할루시네이션 방지 — `docs/anti-hallucination-verification-plan.md`).
2. **Pending 결산 점검 (자동):** `decisions/journal.md`에 `결과: (미기록` 항목이 있으면 본 파이프라인 진행 전에 결산한다. 항목별 티커로 수집 스크립트를 실행(`--out-dir _workspace/_pending`)해 결정 시점 대비 등락률을 구하고, 같은 기간 벤치마크 등락(당시 결정의 스냅샷/reports에 기록된 `benchmark.primary` 레벨 대조, 또는 벤치마크 티커로 스크립트 실행)으로 **알파**를 산출해 해당 항목의 `결과:` 줄을 갱신한다 — 형식: `결과: [중간점검 {YYYY-MM-DD}] 결정 후 {±X}%, 벤치마크 {±Y}% (알파 {±Z}%p) — 복기 미실시`. 이 줄 외에는 수정 금지. 갱신 내용을 사용자에게 1줄씩 보고하고 복기(Phase R)를 제안한다 — 특히 이번 분석 대상과 같은 티커면 교훈이 이번 실행에 반영되도록 복기를 먼저 권한다. 교훈 추출과 결과 확정은 복기에서만 한다.
3. **보유 현황 확인:** `decisions/portfolio.json`을 읽는다. holdings가 있으면 `00_input.md`에 보유 요약(종목 수·현금 비중·이번 대상 기보유 여부)을 기재하고, 비어 있으면 "보유 미등록 — 포트폴리오 영향 분석은 강등 모드"를 기재한다(최초 1회 "보유 등록"을 최종 보고에서 권고).
4. `_workspace/00_input.md` 작성:
   ```markdown
   # 분석 입력
   - 대상: {회사명} ({티커}) / 분석 시점: {YYYY-MM-DD} / 시장: {US|KR}
   - 사용자 맥락: {성향/기간/보유 여부 또는 "일반 분석 — 3성향 분기"}
   - 보유 현황: {portfolio.json 요약 또는 "미등록"}
   ```
5. **L0 거시 + L1 데이터를 한 메시지에서 병렬 호출**한다(서로 의존하지 않음 — 거시는 종목 무관, 스냅샷은 종목 사실):
   ```
   # L0 거시 레짐 (생성·판단 코어) → opus
   Agent(subagent_type="macro-strategist", model="opus", run_in_background=true,
         prompt="_workspace/00_input.md를 읽고 .claude/skills/macro-regime/SKILL.md 방법론으로
         _workspace/00_macro_regime.md를 작성하라. 종목 무관 시장 레짐(risk-on/off·사분면·유동성 국면·
         정치재정·바벨 기울기)을 판정하고, contrarian-check로 역발상 섹션을 포함하라. 무효화 조건 필수.")

   # L1 데이터 SSOT (저부하·스크립트 주도) → sonnet
   Agent(subagent_type="market-data-engineer", model="sonnet", run_in_background=true,
         prompt="_workspace/00_input.md를 읽고 .claude/skills/market-snapshot/SKILL.md 방법론으로
         스크립트(.claude/skills/market-snapshot/scripts/collect_market_data.py)를 먼저 실행한 뒤 _workspace/00_market_snapshot.json을 작성하라.
         사실만 고정하고 판단은 넣지 마라. 못 구한 값은 confidence: unavailable로 명시하라.")
   ```
   둘 다 완료 대기. **market-data-engineer 실패** 시 1회 재시도, 재실패하면 스냅샷 없이 진행하되 최종 보고에 "SSOT 미생성 — 보고서 간 수치 불일치 가능"을 명시한다. **macro-strategist 실패** 시 1회 재시도, 재실패하면 거시 레짐 없이 진행하되 분석가·게이트에 "거시 레짐 미생성 — 종목 단독 분석"을 전파하고 최종 보고에 명시한다(파이프라인은 계속된다 — 거시는 배경 레이어이지 차단 게이트가 아니다).

## Phase 1.6: 사실 검증 게이트 (L0·L1 — 팬아웃 전 필수) [등급: DEGRADED]

> 신설 사유(2026-06-24): 거시 에이전트가 **개장 전 세션 종가를 날조**해 L0가 하류 17개 산출물을 오염시킨 사고. L0는 최상류 배경이라 오염 시 전체가 무너지므로, **분석가 팬아웃 전에** 격리 검증으로 차단한다(생성-검증 분리 — 작성 에이전트가 자기 검증하지 않는다). 상세 `docs/anti-hallucination-verification-plan.md`.

`00_macro_regime.md`와 `00_market_snapshot.json`을 독립 검증자로 점검한다(저부하 → sonnet):
```
Agent(subagent_type="fact-checker", model="sonnet",
      prompt="검증 모드. _workspace/00_macro_regime.md·00_market_snapshot.json과 00_input.md의 현재시각·세션 앵커를 읽고 다음만 점검해 _workspace/00_factcheck.md에 결함 목록을 작성하라(분석·의견 금지):
      ① 시점 가드: 미개장/장중 세션의 종가·등락률을 관측사실로 단정한 곳(특히 '오늘/어제/내일/방금' 날짜) — 앵커 기준 마감 안 된 세션 수치는 ⛔.
      ② 산술 정합: 등락률 vs 레벨(신규≈직전×(1+chg)), 시총=가격×주식수, 비중합≤100% 불일치 ⛔.
      ③ 출처 실재성: [출처] 표기 중 검증 불가·날조 의심 표본 점검.
      ④ SSOT 충돌: macro의 지수/가격 수치가 스냅샷과 모순되면 ⛔.
      각 항목 심각도(⛔치명/⚠️경고)와 위치를 명시. 치명 0건이면 'PASS'.")
```
- **PASS(⛔ 0건):** Phase 2로 진행.
- **⛔ 발견:** 해당 소스 에이전트(macro-strategist 또는 market-data-engineer)를 **1회 재호출**해 결함만 수정 → 재검증. 재실패 시 해당 수치를 "미확인"으로 강등하고 하류·최종 보고에 명시(파이프라인은 계속). 재검증은 1회로 제한(무한 루프 방지). **강등이 발생하면 최종 결정문 검증 모드는 `DEGRADED_DATA`가 된다**(risk-gate Part B 요약 박스) — 강등 수치가 결론을 떠받치는(load-bearing) 사실이면 일반 APPROVE 불가(해당 수치 확인을 조건화한 CONDITIONAL_APPROVE 또는 REVISE).
- macro·snapshot 둘 다 미생성(상류 실패)이면 이 게이트는 건너뛴다. **한쪽만 생성**이면 있는 파일만 점검한다 — 없는 파일은 `00_factcheck.md`에 "미생성"으로 명시하고, 스냅샷 의존 항목(②의 스냅샷 대조, ④ SSOT 충돌)은 생략한다.

## Phase 2: 분석가 팀 — 4렌즈 병렬 (팬아웃)

**4명을 한 메시지에서 동시 호출한다** (`run_in_background: true`, 전부 `model: "opus"`). 각자 자기 영역만, 서로의 산출물을 읽지 않는다. **전원 `00_macro_regime.md`(있으면)를 배경 레짐으로 읽되 재판정하지 않는다:**

```
# 향후 sonnet A/B 후보(현재는 품질 보호 위해 opus)
Agent(subagent_type="fundamental-analyst", prompt="00_input.md·00_market_snapshot.json·00_macro_regime.md(있으면, 밸류 국면 배경)를 읽고 analyst-toolkit 스킬(+references/fundamental.md)로 _workspace/01_fundamental_report.md 작성")
Agent(subagent_type="technical-analyst",   prompt="00_indicators.json·00_ohlcv_daily.csv·스냅샷·00_macro_regime.md(있으면)를 읽고 analyst-toolkit 스킬(+references/technical.md, 대형주·지수면 market-structure.md)로 _workspace/01_technical_report.md 작성. 지표 재계산 금지")
Agent(subagent_type="news-analyst",        prompt="스냅샷·00_macro_regime.md(있으면, 거시는 종목 전이 경로로만)를 읽고 analyst-toolkit 스킬(+references/news.md)로 타임라인·이벤트 캘린더 포함 _workspace/01_news_report.md 작성")
Agent(subagent_type="sentiment-analyst",   prompt="스냅샷·00_macro_regime.md(있으면)를 읽고 analyst-toolkit 스킬(+references/sentiment.md, market-structure.md)로 정량 심리·쏠림·시장구조 포지셔닝 판정 포함 _workspace/01_sentiment_report.md 작성")
```

4편 완료 대기. 일부 실패 시 1회 재시도, 재실패면 그 보고서 없이 진행(하류에 "근거 제한" 전파). 어느 보고서든 `⛔스냅샷 오류` 플래그가 있으면 market-data-engineer를 재호출해 스냅샷을 갱신하고 Phase 2를 재실행한다.

## Phase 3: 리서치 토론 (2라운드) + 판정

**R1 — 논지 (병렬, 격리):** bull과 bear를 동시 호출. **서로의 산출물 금지** 명시:
```
Agent(subagent_type="bull-researcher", prompt="분석가 4편+스냅샷으로 research-debate 스킬의 R1 논지를 _workspace/02_bull_thesis.md에 작성. bear 산출물 금지")
Agent(subagent_type="bear-researcher", prompt="...R1 논지를 _workspace/02_bear_thesis.md에 작성. bull 산출물 금지")
```

**R2 — 교차 반박 (병렬):** 양쪽 논지가 완성된 후에만:
```
Agent(subagent_type="bull-researcher", prompt="02_bear_thesis.md를 읽고 research-debate 스킬 R2로 _workspace/02_bull_rebuttal.md 작성. 상대의 가장 강한 논거부터 정면 반박")
Agent(subagent_type="bear-researcher", prompt="02_bull_thesis.md를 읽고 ... _workspace/02_bear_rebuttal.md 작성")
```

**판정 — research-manager:**
```
Agent(subagent_type="research-manager", prompt="토론 4편+분석가 4편+스냅샷+00_macro_regime.md(있으면)를 읽고 research-debate 스킬 평가 기준으로 판정해 _workspace/03_research_plan.md 작성. 방향·무효화 조건·확신도(표준 앵커 정의) 의무. 관망 판정이면 '관망의 기대 비용'(기회비용) 명시 의무")
```

## Phase 4: 트레이더 — 거래 계획

```
Agent(subagent_type="trader", prompt="03_research_plan.md·스냅샷·01_technical_report.md·01_news_report.md·00_input.md를 읽고 trade-planning 스킬로 _workspace/04_trade_plan.md 작성. 손절 먼저 비중 역산, 손익비 1.5 미만이면 보류 결론")
```

## Phase 5: 리스크 토론 3성향 + 포트폴리오 영향 — 병렬 (팬아웃)

**같은 risk-debater를 성향 파라미터만 바꿔 3회 + portfolio-risk-analyst 1회, 총 4개를 한 메시지에서 동시 호출.** 서로의 산출물을 읽지 않는다:
```
Agent(subagent_type="risk-debater", prompt="성향: 공격(aggressive). 04_trade_plan.md·00_macro_regime.md(있으면)를 risk-gate 스킬 Part A로 평가해 _workspace/05_risk_aggressive.md 작성. 다른 토론자 산출물 금지")
Agent(subagent_type="risk-debater", prompt="성향: 중립(neutral). ... _workspace/05_risk_neutral.md")
Agent(subagent_type="risk-debater", prompt="성향: 보수(conservative). ... _workspace/05_risk_conservative.md")
Agent(subagent_type="portfolio-risk-analyst", model="opus", prompt="decisions/portfolio.json(없으면 강등 모드)·04_trade_plan.md·스냅샷·00_indicators.json·00_ohlcv_daily.csv·00_macro_regime.md(있으면)를 읽고 portfolio-risk 스킬로 _workspace/05_portfolio_impact.md 작성. 편입 전/후 집중·리스크 기여·동시 꼬리 손실 측정. 판정 금지 — 측정과 관찰만")
```

## Phase 6: 최종 게이트 + 저널

```
Agent(subagent_type="portfolio-manager", prompt="리스크 3편·05_portfolio_impact.md·04_trade_plan.md·03_research_plan.md·스냅샷·00_factcheck.md(있으면 — 강등 수치 확인용)·00_macro_regime.md(있으면)·00_input.md(+있으면 decisions/journal.md·lessons.md·portfolio.json)를 읽고 risk-gate 스킬 Part B 게이트로 _workspace/06_final_decision.md 작성(상단 판정 요약 박스 — 검증·포트폴리오 모드 포함 — + 실행 카드 5줄 의무) + decisions/journal.md에 1건 append")
```

**REVISE 루프 (생성-검증, 최대 1회):** 판정이 REVISE면 지시 대상(트레이더 또는 리서치 매니저)을 1회 재호출해 해당 산출물을 수정하게 한다. 수정으로 **비중이 바뀌었으면 portfolio-risk-analyst를 1회 재호출**해 `05_portfolio_impact.md`의 편입 후 스냅샷만 재계산시킨다(보유·변동성 재수집 불필요 — 에이전트의 재호출 지침 참조. 이걸 건너뛰면 PM이 옛 비중 기준의 스테일 수치로 재점검하게 된다). 그 후 portfolio-manager가 해소 여부만 재점검해 최종 판정한다(미해소면 REJECT). 재REVISE 금지 — 무한 루프 방지.

## Phase 7: 산출물 정리 + 보고

1. 완성본을 `reports/{회사}_{YYYY-MM-DD}/`에 복사: `거시레짐_{날짜}.md`(00_macro_regime, 있으면), `팩트체크_{날짜}.md`(00_factcheck, 있으면), 분석가 4편, 토론 4편, `투자계획_{회사}.md`(03), `거래계획_{회사}.md`(04), 리스크 3편, `포트폴리오영향_{회사}.md`(05_portfolio_impact, 있으면), `최종결정_{회사}.md`(06).
   - **기계 검증 (harness doctor) [등급: DEGRADED — 사후 검증·정정 1회]:** `python scripts/harness_doctor.py --harness trading`을 실행하고 결과(`_workspace/09_doctor.json`)를 `reports/{회사}_{날짜}/닥터리포트_{날짜}.json`으로 복사한다. **라벨 모순 FAIL**(⛔치명+승인, 조건부인데 일반 APPROVE, 모드 미스라벨)이면 portfolio-manager를 1회 재호출해 결정문 라벨을 정정한다 — 저널에 이미 기록됐으면 기존 항목 본문은 수정 금지, 정정 항목을 append(IPO 하네스 Phase 6 재진입 규칙과 동형). 정정 후 doctor 재실행으로 해소 확인. 그 외 FAIL·미해소 건은 **요약 보고 최상단에 명시**한다(FAIL 방치 + `FULLY_VERIFIED` 표기 금지 — 라벨은 기계 검증과 일치해야 한다). 판정·저널 확정 후에 도는 사후 검증이므로 BLOCKING이 아니다 — doctor는 결정적 불변조건(산출물 존재·산술·라벨 정합)만 보고, LLM 게이트(fact-checker 등)를 대체하지 않고 보완한다.
2. `_workspace/`는 보존한다(감사 추적·부분 재실행용).
   - **학습 코퍼스 커밋 [HARD]:** 저널 기록 직후 `git add decisions/ && git commit -m "저널: {티커} {판정} 기록"`을 실행한다. 저널·교훈·캘리브레이션은 이 시스템의 유일한 축적 자산인데 무커밋 상태는 단일 실패점이다(Edit 실수 한 번에 복구 불가). 커밋 실패(권한 등) 시 보고에 명시하고 계속한다.
3. 사용자 요약 보고: **거시 레짐 한 줄(risk-on/off·바벨 기울기) + 최종 판정(APPROVE/CONDITIONAL_APPROVE/REVISE/REJECT + 검증·포트폴리오 모드, doctor FAIL 있으면 최상단 명시) + 방향·확신도 + 채택 거래 계획 1줄(진입/손절/비중/목표) + 토론에서 살아남은 핵심 논거 + 수용한 잔여 리스크 + 산출물 경로**. 면책: 이 산출물은 투자 참고 자료이며 투자 결정의 책임은 사용자에게 있음을 1줄 명시.
   - **오케스트레이터 레드플래그 자가점검 [HARD] (보고 전):** 결론을 떠받치는 핵심 정량 주장을 중계하기 전에 — 🚩"오늘/어제/내일/방금" 날짜가 붙은 수치(세션 마감 여부 확인) 🚩급등/급반등·라운드넘버 🚩"방증한다/증명한다"류 단정(증거가 관측인지 가정인지) — 을 점검한다. 검증 불가하면 단정하지 말고 **"미확인"으로 명시**해 전달한다(에이전트 산출을 무비판 중계 금지). 또한 **외부 산출(MP3 등) 생성 후엔 파일 mtime·크기로 실제 갱신을 확인**한다(도구 'ok' ≠ 실제 반영).
4. **쉬운 해설판 (표준 산출물 — 입문자용, 생략 금지):** 요약 보고 후 report-explainer를 호출해 최종 결정을 투자 입문자용 companion 문서로 충실히 옮긴다. 전문 리포트는 그대로 보존되고, 이건 그 위에 얹는 쉬운 번역본이다.
   ```
   # 충실 번역(결론·수치 보존이 생명, 저부하 산출) → sonnet
   Agent(subagent_type="report-explainer", model="sonnet",
         prompt="트레이딩 하네스 해설 모드. _workspace/06_final_decision.md(필수)·04_trade_plan.md·03_research_plan.md·00_macro_regime.md(있으면)를 읽고, plain-language 스킬로 _workspace/08_plain_explanation.md를 작성하라. 판정·확신도·진입/손절/비중/목표 수치를 한 글자도 왜곡하지 말고, 전문용어 첫 등장 풀이 + 정확한 비유 + 행동 가이드(신규/보유자·진입/철회 트리거) + 용어 풀이 구조로. 출력 전 충실성 자가 점검 필수.")
   ```
   완성본을 `reports/{회사}_{YYYY-MM-DD}/쉬운해설_{회사}.md`로 복사. 실패 시 1회 재시도, 재실패면 해설판 없이 진행(전문 리포트는 보존)하고 보고에 누락 명시.
5. **팟캐스트 (반드시 묻기 — 생략 금지):** 해설판 생성 후, 판정이 무엇이든(REJECT 포함) AskUserQuestion으로 묻는다 — "이번 분석으로 투자 팟캐스트를 만들까요?" 옵션: **① 대본 + 오디오(MP3)** (NotebookLM 로그인 필요, 생성 수 분~십수 분 소요) / **② 대본만** / **③ 만들지 않음**. 사용자가 ③이면 아무것도 만들지 않고 6으로.
   - **대본 (①·② 공통):**
     ```
     # 선택형 저부하 산출 → sonnet
     Agent(subagent_type="podcast-producer", model="sonnet",
           prompt="트레이딩 하네스 대본 모드. _workspace/06_final_decision.md(필수)·03_research_plan.md·04_trade_plan.md를 읽고(디테일은 02_* 토론 원본), podcast-script 스킬로 _workspace/07_podcast_script.md를 작성하라. 최종 판정·확신도·채택 계획 수치 왜곡 금지. 하단에 NotebookLM 생성 지침 섹션 필수.")
     ```
     완성본을 `reports/{회사}_{YYYY-MM-DD}/팟캐스트대본_{회사}.md`로 복사.
   - **오디오 (① 선택 시):** notebooklm-audio 스킬을 따른다 — 먼저 `--check-only` 사전 점검(코드 2=미인증·3=미설치면 오디오 생략 + 설정 안내, 대본은 보존). 통과 시 번들 스크립트로 생성: `--out "reports/{회사}_{YYYY-MM-DD}/팟캐스트_{회사}.mp3" --source _workspace/06_final_decision.md --source _workspace/07_podcast_script.md --format debate --language ko --instructions "{대본의 NotebookLM 생성 지침을 그대로}"`. 실패 시 1회 재시도, 재실패면 대본만 산출물로 보고.
6. 진화: "결과나 팀 구성에서 고치고 싶은 점이 있나요?" 한 번 묻는다(강요 금지).

## Phase R: 복기 모드 (별도 진입)

사용자가 결과를 가져오면 파이프라인을 돌리지 않고:
```
Agent(subagent_type="portfolio-manager", prompt="복기 모드. trade-reflection 스킬로 decisions/journal.md의 {대상 결정}과 사용자 제공 결과를 4축 대조하고, journal의 결과: 줄 갱신 + 캘리브레이션 대장(decisions/calibration.md) 1행 추가·버킷 재계산 + 일반화 가능한 교훈만 decisions/lessons.md에 append하라. 결과론 금지. 관망 결정도 동일하게 알파로 채점한다(기회비용도 손실이다)")
```
복기 완료 후, **커밋 전에 `decisions/calibration.md`에 이번 복기 1행이 실제 추가됐는지 확인한다** — 누락이면 portfolio-manager에 1회 보완을 지시한다(복기 완료분이 대장에 0행으로 남았던 실측 누락의 재발 방지). 확인 후 학습 코퍼스를 커밋한다: `git add decisions/ && git commit -m "복기: {대상}"`.

## Phase S: 아이디어 스캔 모드 (별도 진입 — 능동 소싱)

티커 없이 "뭐 살까"/"아이디어 스캔"/"종목 발굴"/"워치리스트" 요청 시. 파이프라인을 돌리지 않는다:
1. `_workspace/00_macro_regime.md`가 없거나 7일 이상 낡았으면 macro-strategist(opus)를 먼저 실행해 갱신한다.
2. ```
   Agent(subagent_type="idea-scanner", model="opus", prompt="idea-scan 스킬로 00_macro_regime.md를 앵커 삼아 _workspace/00_idea_scan.md 작성 + decisions/watchlist.md 갱신. 후보 발굴이지 추천이 아님을 명시")
   ```
3. 사용자에게 상위 후보를 보고하고, 하나를 고르면 그 티커로 풀 파이프라인(Phase 1~7)을 제안한다. 워치리스트 갱신분은 `git add decisions/ && git commit -m "워치리스트: 스캔 {날짜}"`로 커밋.

## Phase M: 포지션 점검 모드 (별도 진입 — 트리거 모니터링)

"포지션 점검"/"트리거 점검" 요청 시, 또는 사용자가 주기 실행을 원하면 안내(예: 스케줄 기능으로 주 1회):
1. `decisions/journal.md`에서 열린 결정(결과 미확정 + 실행 기록 있는 항목 우선)의 **무효화 조건·철회 트리거**를 수집한다.
2. 각 티커·벤치마크로 수집 스크립트를 실행(`--out-dir _workspace/_pending` — pending 결산과 동일 경로)해 현재 레벨을 확인한다.
3. 트리거별 상태를 판정해 보고한다: **발동** / **근접**(트리거까지 ±3% 이내) / 정상. 발동 항목은 "지연 없는 행동" 원칙(lessons의 NVDA 교훈)을 인용해 결정 촉구 — 판단을 대신하지 않되, 트리거는 결정 당시의 자신이 만든 규칙임을 상기시킨다.
4. journal 해당 항목 `결과:` 줄에 `[중간점검 {날짜}]` 형식으로 갱신(기존 규약과 동일), `git add decisions/ && git commit`.

## Phase P: 상태 갱신 모드 (별도 진입 — 보유·체결 기록)

- **"보유 등록/갱신":** 사용자와 짧은 인터뷰(보유 종목·비중 또는 평가액·평단·현금 비중)로 `decisions/portfolio.json`을 작성/갱신한다(스키마: portfolio-risk 스킬). 비중 합 검산 후 저장·커밋. 등록/갱신 종목에 열린 journal 항목(`실행:` 미체결)이 있으면 `실행:` 줄도 함께 갱신한다 — 저널은 미체결인데 보유만 등록되면 복기·pending 결산이 미진입(가상 채점)으로 오채점한다(이중 기록원 정합).
- **"체결 반영"/"실제로 샀어":** 해당 journal 항목의 `실행:` 줄을 갱신(체결일/체결가/실제 비중)하고 `portfolio.json`의 holdings에 반영한다. 이후 복기·pending 결산은 체결가 기준 실현/평가 손익으로 채점된다. 저장·커밋. 계획과 체결의 괴리(가격·비중)가 크면 1줄로 드러낸다 — 계획-실행 드리프트도 복기 대상이다.

## 데이터 전달 프로토콜 (파일 기반)

| 단계 | 생산자 | 파일 | 소비자 |
|------|--------|------|--------|
| 입력 | 오케스트레이터 | `00_input.md` | 전원 |
| 소싱(스캔 모드) | idea-scanner | `00_idea_scan.md`, `decisions/watchlist.md` | 사용자, (선택 시) 파이프라인 입력 |
| 상태 | 오케스트레이터(상태 갱신 모드) | `decisions/portfolio.json` | portfolio-risk-analyst, portfolio-manager |
| L0 | macro-strategist | `00_macro_regime.md` | 분석가 4명(배경), research-manager, risk-debater, portfolio-manager, idea-scanner |
| L1 | market-data-engineer | `00_market_snapshot.json`, `00_ohlcv_daily.csv`, `00_indicators.json` | 전원 (SSOT) |
| L1.6 게이트 | fact-checker(트레이딩 검증 모드) | `00_factcheck.md` | 오케스트레이터(PASS/⛔ 분기) |
| L2 | 분석가 4명 | `01_{fundamental,technical,news,sentiment}_report.md` | bull, bear, research-manager, trader(기술·뉴스), risk-debater |
| L3-R1 | bull / bear | `02_bull_thesis.md` / `02_bear_thesis.md` | 상대(R2에서만), research-manager |
| L3-R2 | bull / bear | `02_bull_rebuttal.md` / `02_bear_rebuttal.md` | research-manager |
| L3 판정 | research-manager | `03_research_plan.md` | trader, risk-debater, portfolio-manager |
| L4 | trader | `04_trade_plan.md` | risk-debater ×3, portfolio-manager |
| L5 토론 | risk-debater ×3 | `05_risk_{aggressive,neutral,conservative}.md` | portfolio-manager |
| L5 포트폴리오 | portfolio-risk-analyst | `05_portfolio_impact.md` | portfolio-manager |
| L5 게이트 | portfolio-manager | `06_final_decision.md`, `decisions/journal.md` | 사용자, (다음 실행의) 전원 |
| 기계 검증 | `scripts/harness_doctor.py` (스크립트) | `09_doctor.json` → `reports/.../닥터리포트_{날짜}.json` | 오케스트레이터(보고 시 FAIL 명시), 사용자 |
| 학습 | portfolio-manager(복기) | `decisions/lessons.md`, `decisions/calibration.md` | (다음 실행의) 전원 |
| 해설(표준 — 입문자용) | report-explainer | `08_plain_explanation.md` → `reports/.../쉬운해설_{회사}.md` | 사용자 |
| 팟캐스트(선택 — 사용자 동의 시만) | podcast-producer | `07_podcast_script.md` → `reports/.../팟캐스트대본·팟캐스트.mp3` | 사용자, notebooklm-audio 스킬 |

## 에러 핸들링

- **에이전트 실패:** 1회 재시도 → 재실패 시 그 산출물 없이 진행하고 하류와 최종 보고에 누락 명시(예: 심리 보고서 누락 → 토론·리스크에 "심리 관점 부재" 전파).
- **거시 레짐 미생성:** macro-strategist 재실패 시 거시 레짐 없이 진행한다 — 거시는 배경 레이어이지 차단 게이트가 아니다. 하류에 "거시 레짐 미생성 — 종목 단독 분석"을 전파하고 portfolio-manager는 레짐 게이트를 건너뛰되 보수적으로 기운다.
- **데이터 미확보:** 삭제·추측 금지. "미확보"로 표기해 하류 전달, 판정·게이트가 확신도에 반영.
- **상충 데이터:** 어느 쪽도 지우지 않고 출처 병기.
- **⛔스냅샷 오류:** market-data-engineer 1회 재호출 → 스냅샷 갱신 → 하류 전체 재실행.
- **접근 차단:** `insane-search` 우회 → 실패 시 미확보 표기.

## 테스트 시나리오

**정상 흐름:** "엔비디아 트레이딩 분석해줘" → Phase 0(초기) → 입력 기록 → L0 거시 레짐 + L1 스냅샷+지표 병렬 → L2 분석가 4편 병렬(레짐 배경) → L3 토론 R1(격리)→R2(교차)→판정(역발상 보정, 예: 매수, 확신도 60%) → L4 거래 계획(3성향) → L5 리스크 3편 병렬(바벨·상관 축) → 게이트(거시·역발상 점검) APPROVE + 저널 기록 → reports/ 정리 + harness doctor GREEN 확인 → 요약 보고 → 쉬운 해설판 생성(입문자용 companion) → 팟캐스트 묻기.

**거시 역풍 흐름:** macro-strategist가 "risk-off(고점 낮추는 구조), 유동성 긴축" 판정 → 분석가·토론은 종목 강세 논거 유지하나 research-manager가 레짐 역풍을 반영해 확신도 하향 → risk-debater 보수 성향이 상관 연쇄·레짐 역풍 ⛔ 지적 → portfolio-manager가 거시 게이트에서 "레짐 역풍 + 컨센서스 쏠림"으로 비중 축소 REVISE 또는 보류 → 저널에 레짐 조건을 진입 트리거로 기록.

**REVISE 흐름:** 트레이더가 실적 발표 D-2에 일괄 진입 설계 + 공격형 비중 상한 초과 → 보수·중립 토론자가 ⛔치명 지적 → portfolio-manager가 REVISE(분할 진입 + 비중 8% 상한 지시) → 트레이더 1회 재작성 → 게이트 해소 확인 → APPROVE.

**보류 흐름:** research-manager가 "관망" 판정 → 트레이더는 "진입 보류 + 진입 조건(가격/이벤트)" 계획 → 리스크 토론은 보류 타당성 평가 → 게이트 APPROVE(보류 승인) → 저널에 진입 조건을 모니터링 트리거로 기록.

**에러 흐름:** sentiment-analyst가 커뮤니티 접근 차단으로 재시도까지 실패 → 보고서 3편으로 토론 진행(bull/bear가 "근거 제한: 심리" 명시) → research-manager가 확신도 상한 제한 → 정상 종결, 최종 보고에 누락 명시.

**복기 흐름:** 한 달 뒤 "지난 NVDA 결정 복기해줘, 현재 -8%" → Phase R → journal 대조: 무효화 조건(SMA50 이탈)이 이미 발동했는데 미청산 → 교훈 "철회 트리거 발동 시 행동 지연" lessons.md 기록 + calibration.md에 확신도-결과 1행 추가 → decisions/ 커밋 → 다음 실행에서 trader·portfolio-manager가 반영.

**아이디어 스캔 흐름:** 티커 없이 "요즘 뭐 살 만해?" → Phase S → 레짐 확인(3일 전 판정, 신선) → idea-scanner가 레짐(risk-off·방어 기울기)을 번역해 인컴·원자재 후보 6개 스캔, 1차 필터로 2개 기각(사유 워치리스트 기록) → 상위 3개 + 촉매 제시 → 사용자가 1개 선택 → 해당 티커로 풀 파이프라인 시작.

**포트폴리오 집중 REVISE 흐름:** 저변동 인컴 종목에 공격형 35% 배분 계획 → portfolio-risk-analyst가 "한국 장기금리 노출 합산 52% 🚩, 신규 캠페인 꼬리 검산 계좌 -3.1%(캠페인 한도 2% 초과), 동시 꼬리 손실 합 -11%(집계 한도 10% 초과) 🚩" 측정 → portfolio-manager가 포트폴리오 게이트에서 REVISE(비중 22% 상한 + 금리 노출 분산 조건) → 트레이더 재작성 → portfolio-risk-analyst가 편입 후 스냅샷 재계산 → 꼬리 검산(2%)·집계 한도(10%) 통과 확인 후 APPROVE.
