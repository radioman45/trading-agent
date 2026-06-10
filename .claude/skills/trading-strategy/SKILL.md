---
name: trading-strategy
description: 투자전략 트레이딩 하네스 오케스트레이터(TradingAgents 구조). 한 종목을 시장 데이터 엔지니어가 스냅샷·기술지표로 고정하고, 분석가 4명(기본적·기술적·뉴스·심리)이 병렬 분석, Bull/Bear 리서처가 2라운드 토론, 리서치 매니저가 판정해 투자 계획 수립, 트레이더가 거래 계획(진입·손절·비중·목표) 변환, 리스크 토론자 3성향(공격/중립/보수)이 병렬 평가, 포트폴리오 매니저가 최종 APPROVE/REVISE/REJECT 판정 후 의사결정 저널에 기록하는 파이프라인을 조율한다. "트레이딩 분석", "투자전략 분석", "{티커} 매매 판단", "사야 돼 팔아야 돼", "트레이딩 전략 세워줘", "거래해도 될까", "포지션 잡아도 될까", "투자 분석" 요청 시 반드시 이 스킬을 사용한다. 후속 요청도 처리한다: "다시 실행", "재실행", "업데이트", "분석가 보고서만 다시", "토론 한 라운드 더", "강세론/약세론 보강", "판정만 다시", "거래계획만 다시", "리스크 검토만 다시", "최종 결정만 다시", "이전 결과 기반으로", "결과 개선", "복기", "결과 반영". 단, 단순 주가 조회나 일반 투자 상식 질문은 직접 응답해도 된다.
---

# Trading Strategy — 투자전략 트레이딩 하네스

[TradingAgents](https://github.com/tauricresearch/tradingagents)의 멀티에이전트 트레이딩 펌 구조를 이식한 하네스. **11명의 전문가가 5계층**으로 분업한다:

```
[L1 데이터]   market-data-engineer ── 스냅샷+기술지표 SSOT 고정
[L2 분석]     fundamental ∥ technical ∥ news ∥ sentiment ── 4렌즈 병렬 분석
[L3 리서치]   bull ↔ bear 2라운드 토론 → research-manager 판정 → 투자 계획
[L4 실행]     trader ── 거래 계획 (진입·손절·비중·목표·손익비)
[L5 게이트]   risk-debater ×3 (공격∥중립∥보수) → portfolio-manager 최종 판정
                                                  └─ decisions/journal.md 기록
[학습 루프]   trade-reflection ── 결과 복기 → decisions/lessons.md → 다음 실행에 주입
```

**실행 모드: 서브 에이전트 (파이프라인 + 팬아웃/팬인 + 생성-검증).** 에이전트 팀이 아니다 — Bull/Bear 라운드 1과 리스크 토론자 3명은 서로의 산출물을 **봐서는 안 되므로**(독립 관점이 정보량의 원천), 실시간 통신 대신 파일로만 전달한다. 토론의 교차는 라운드 2에서 오케스트레이터가 파일을 건네는 방식으로 통제한다. 모든 Agent 호출에 `model: "opus"` 명시.

## Phase 0: 컨텍스트 확인

`_workspace/`와 사용자 요청을 대조해 실행 모드를 결정한다:

| 상황 | 모드 | 행동 |
|------|------|------|
| `_workspace/` 없음 | **초기 실행** | Phase 1부터 전체 |
| 있음 + 새 종목 지정 | **새 실행** | 기존을 `_workspace_prev/`로 이동 후 전체 |
| 있음 + 부분 수정 요청 | **부분 재실행** | 해당 에이전트만 재호출, 하류는 의존성 따라 갱신 |
| "복기"/"결과 반영" | **복기 모드** | Phase R로 — 파이프라인 실행 안 함 |

**부분 재실행 의존성:** 스냅샷 갱신 → 전체 재실행(최상류). 분석가 보고서 갱신 → 토론부터 하류 전체. 토론/판정 갱신 → 트레이더부터. 거래 계획 갱신 → 리스크 토론부터. 리스크 토론 갱신 → 최종 게이트만. "토론 한 라운드 더" → R3 append 후 판정부터 하류.

## Phase 1: 입력 수집 + 데이터 고정

1. 분석 대상(회사명/티커) 확인. 없으면 사용자에게 묻는다. 사용자 맥락(성향·기간·보유 여부)은 선택 — 없으면 3성향 분기로 진행.
2. **Pending 결산 점검 (자동):** `decisions/journal.md`에 `결과: (미기록` 항목이 있으면 본 파이프라인 진행 전에 결산한다. 항목별 티커로 수집 스크립트를 실행(`--out-dir _workspace/_pending`)해 결정 시점 대비 등락률을 구하고, 같은 기간 벤치마크 등락(당시 결정의 스냅샷/reports에 기록된 `benchmark.primary` 레벨 대조, 또는 벤치마크 티커로 스크립트 실행)으로 **알파**를 산출해 해당 항목의 `결과:` 줄을 갱신한다 — 형식: `결과: [중간점검 {YYYY-MM-DD}] 결정 후 {±X}%, 벤치마크 {±Y}% (알파 {±Z}%p) — 복기 미실시`. 이 줄 외에는 수정 금지. 갱신 내용을 사용자에게 1줄씩 보고하고 복기(Phase R)를 제안한다 — 특히 이번 분석 대상과 같은 티커면 교훈이 이번 실행에 반영되도록 복기를 먼저 권한다. 교훈 추출과 결과 확정은 복기에서만 한다.
3. `_workspace/00_input.md` 작성:
   ```markdown
   # 분석 입력
   - 대상: {회사명} ({티커}) / 분석 시점: {YYYY-MM-DD}
   - 사용자 맥락: {성향/기간/보유 여부 또는 "일반 분석 — 3성향 분기"}
   ```
4. **market-data-engineer 단독 호출:**
   ```
   Agent(subagent_type="market-data-engineer", model="opus",
         prompt="_workspace/00_input.md를 읽고 .claude/skills/market-snapshot/SKILL.md 방법론으로
         스크립트(collect_market_data.py)를 먼저 실행한 뒤 _workspace/00_market_snapshot.json을 작성하라.
         사실만 고정하고 판단은 넣지 마라. 못 구한 값은 confidence: unavailable로 명시하라.")
   ```
   실패 시 1회 재시도. 재실패하면 스냅샷 없이 진행하되 최종 보고에 "SSOT 미생성 — 보고서 간 수치 불일치 가능"을 명시한다.

## Phase 2: 분석가 팀 — 4렌즈 병렬 (팬아웃)

**4명을 한 메시지에서 동시 호출한다** (`run_in_background: true`, 전부 `model: "opus"`). 각자 자기 영역만, 서로의 산출물을 읽지 않는다:

```
Agent(subagent_type="fundamental-analyst", prompt="00_input.md·00_market_snapshot.json을 읽고 analyst-toolkit 스킬(+references/fundamental.md)로 _workspace/01_fundamental_report.md 작성")
Agent(subagent_type="technical-analyst",   prompt="00_indicators.json·00_ohlcv_daily.csv·스냅샷을 읽고 analyst-toolkit 스킬(+references/technical.md)로 _workspace/01_technical_report.md 작성. 지표 재계산 금지")
Agent(subagent_type="news-analyst",        prompt="스냅샷을 읽고 analyst-toolkit 스킬(+references/news.md)로 타임라인·이벤트 캘린더 포함 _workspace/01_news_report.md 작성")
Agent(subagent_type="sentiment-analyst",   prompt="스냅샷을 읽고 analyst-toolkit 스킬(+references/sentiment.md)로 정량 심리·쏠림 판정 포함 _workspace/01_sentiment_report.md 작성")
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
Agent(subagent_type="research-manager", prompt="토론 4편+분석가 4편+스냅샷을 읽고 research-debate 스킬 평가 기준으로 판정해 _workspace/03_research_plan.md 작성. 방향·무효화 조건·확신도(정의 포함) 의무")
```

## Phase 4: 트레이더 — 거래 계획

```
Agent(subagent_type="trader", prompt="03_research_plan.md·스냅샷·01_technical_report.md·01_news_report.md·00_input.md를 읽고 trade-planning 스킬로 _workspace/04_trade_plan.md 작성. 손절 먼저 비중 역산, 손익비 1.5 미만이면 보류 결론")
```

## Phase 5: 리스크 토론 — 3성향 병렬 (팬아웃)

**같은 risk-debater를 성향 파라미터만 바꿔 3회 동시 호출.** 서로의 산출물을 읽지 않는다:
```
Agent(subagent_type="risk-debater", prompt="성향: 공격(aggressive). 04_trade_plan.md를 risk-gate 스킬 Part A로 평가해 _workspace/05_risk_aggressive.md 작성. 다른 토론자 산출물 금지")
Agent(subagent_type="risk-debater", prompt="성향: 중립(neutral). ... _workspace/05_risk_neutral.md")
Agent(subagent_type="risk-debater", prompt="성향: 보수(conservative). ... _workspace/05_risk_conservative.md")
```

## Phase 6: 최종 게이트 + 저널

```
Agent(subagent_type="portfolio-manager", prompt="리스크 3편·04_trade_plan.md·03_research_plan.md·스냅샷·00_input.md(+있으면 decisions/journal.md·lessons.md)를 읽고 risk-gate 스킬 Part B 게이트로 _workspace/06_final_decision.md 작성 + decisions/journal.md에 1건 append")
```

**REVISE 루프 (생성-검증, 최대 1회):** 판정이 REVISE면 지시 대상(트레이더 또는 리서치 매니저)을 1회 재호출해 해당 산출물을 수정하게 하고, portfolio-manager가 해소 여부만 재점검해 최종 판정한다(미해소면 REJECT). 재REVISE 금지 — 무한 루프 방지.

## Phase 7: 산출물 정리 + 보고

1. 완성본을 `reports/{회사}_{YYYY-MM-DD}/`에 복사: 분석가 4편, 토론 4편, `투자계획_{회사}.md`(03), `거래계획_{회사}.md`(04), 리스크 3편, `최종결정_{회사}.md`(06).
2. `_workspace/`는 보존한다(감사 추적·부분 재실행용).
3. 사용자 요약 보고: **최종 판정(APPROVE/REVISE/REJECT) + 방향·확신도 + 채택 거래 계획 1줄(진입/손절/비중/목표) + 토론에서 살아남은 핵심 논거 + 수용한 잔여 리스크 + 산출물 경로**. 면책: 이 산출물은 투자 참고 자료이며 투자 결정의 책임은 사용자에게 있음을 1줄 명시.
4. **팟캐스트 (반드시 묻기 — 생략 금지):** 요약 보고 직후, 판정이 무엇이든(REJECT 포함) AskUserQuestion으로 묻는다 — "이번 분석으로 투자 팟캐스트를 만들까요?" 옵션: **① 대본 + 오디오(MP3)** (NotebookLM 로그인 필요, 생성 수 분~십수 분 소요) / **② 대본만** / **③ 만들지 않음**. 사용자가 ③이면 아무것도 만들지 않고 5로.
   - **대본 (①·② 공통):**
     ```
     Agent(subagent_type="podcast-producer", model="opus",
           prompt="트레이딩 하네스 대본 모드. _workspace/06_final_decision.md(필수)·03_research_plan.md·04_trade_plan.md를 읽고(디테일은 02_* 토론 원본), podcast-script 스킬로 _workspace/07_podcast_script.md를 작성하라. 최종 판정·확신도·채택 계획 수치 왜곡 금지. 하단에 NotebookLM 생성 지침 섹션 필수.")
     ```
     완성본을 `reports/{회사}_{YYYY-MM-DD}/팟캐스트대본_{회사}.md`로 복사.
   - **오디오 (① 선택 시):** notebooklm-audio 스킬을 따른다 — 먼저 `--check-only` 사전 점검(코드 2=미인증·3=미설치면 오디오 생략 + 설정 안내, 대본은 보존). 통과 시 번들 스크립트로 생성: `--out "reports/{회사}_{YYYY-MM-DD}/팟캐스트_{회사}.mp3" --source _workspace/06_final_decision.md --source _workspace/07_podcast_script.md --format debate --language ko --instructions "{대본의 NotebookLM 생성 지침을 그대로}"`. 실패 시 1회 재시도, 재실패면 대본만 산출물로 보고.
5. 진화: "결과나 팀 구성에서 고치고 싶은 점이 있나요?" 한 번 묻는다(강요 금지).

## Phase R: 복기 모드 (별도 진입)

사용자가 결과를 가져오면 파이프라인을 돌리지 않고:
```
Agent(subagent_type="portfolio-manager", prompt="복기 모드. trade-reflection 스킬로 decisions/journal.md의 {대상 결정}과 사용자 제공 결과를 4축 대조하고, journal의 결과: 줄 갱신 + 일반화 가능한 교훈만 decisions/lessons.md에 append하라. 결과론 금지")
```

## 데이터 전달 프로토콜 (파일 기반)

| 단계 | 생산자 | 파일 | 소비자 |
|------|--------|------|--------|
| 입력 | 오케스트레이터 | `00_input.md` | 전원 |
| L1 | market-data-engineer | `00_market_snapshot.json`, `00_ohlcv_daily.csv`, `00_indicators.json` | 전원 (SSOT) |
| L2 | 분석가 4명 | `01_{fundamental,technical,news,sentiment}_report.md` | bull, bear, research-manager, trader(기술·뉴스), risk-debater |
| L3-R1 | bull / bear | `02_bull_thesis.md` / `02_bear_thesis.md` | 상대(R2에서만), research-manager |
| L3-R2 | bull / bear | `02_bull_rebuttal.md` / `02_bear_rebuttal.md` | research-manager |
| L3 판정 | research-manager | `03_research_plan.md` | trader, risk-debater, portfolio-manager |
| L4 | trader | `04_trade_plan.md` | risk-debater ×3, portfolio-manager |
| L5 토론 | risk-debater ×3 | `05_risk_{aggressive,neutral,conservative}.md` | portfolio-manager |
| L5 게이트 | portfolio-manager | `06_final_decision.md`, `decisions/journal.md` | 사용자, (다음 실행의) 전원 |
| 학습 | portfolio-manager(복기) | `decisions/lessons.md` | (다음 실행의) 전원 |
| 팟캐스트(선택 — 사용자 동의 시만) | podcast-producer | `07_podcast_script.md` → `reports/.../팟캐스트대본·팟캐스트.mp3` | 사용자, notebooklm-audio 스킬 |

## 에러 핸들링

- **에이전트 실패:** 1회 재시도 → 재실패 시 그 산출물 없이 진행하고 하류와 최종 보고에 누락 명시(예: 심리 보고서 누락 → 토론·리스크에 "심리 관점 부재" 전파).
- **데이터 미확보:** 삭제·추측 금지. "미확보"로 표기해 하류 전달, 판정·게이트가 확신도에 반영.
- **상충 데이터:** 어느 쪽도 지우지 않고 출처 병기.
- **⛔스냅샷 오류:** market-data-engineer 1회 재호출 → 스냅샷 갱신 → 하류 전체 재실행.
- **접근 차단:** `insane-search` 우회 → 실패 시 미확보 표기.

## 테스트 시나리오

**정상 흐름:** "엔비디아 트레이딩 분석해줘" → Phase 0(초기) → 입력 기록 → L1 스냅샷+지표 → L2 분석가 4편 병렬 → L3 토론 R1(격리)→R2(교차)→판정(예: 매수, 확신도 60%) → L4 거래 계획(3성향) → L5 리스크 3편 병렬 → 게이트 APPROVE + 저널 기록 → reports/ 정리 + 요약 보고.

**REVISE 흐름:** 트레이더가 실적 발표 D-2에 일괄 진입 설계 + 공격형 비중 상한 초과 → 보수·중립 토론자가 ⛔치명 지적 → portfolio-manager가 REVISE(분할 진입 + 비중 8% 상한 지시) → 트레이더 1회 재작성 → 게이트 해소 확인 → APPROVE.

**보류 흐름:** research-manager가 "관망" 판정 → 트레이더는 "진입 보류 + 진입 조건(가격/이벤트)" 계획 → 리스크 토론은 보류 타당성 평가 → 게이트 APPROVE(보류 승인) → 저널에 진입 조건을 모니터링 트리거로 기록.

**에러 흐름:** sentiment-analyst가 커뮤니티 접근 차단으로 재시도까지 실패 → 보고서 3편으로 토론 진행(bull/bear가 "근거 제한: 심리" 명시) → research-manager가 확신도 상한 제한 → 정상 종결, 최종 보고에 누락 명시.

**복기 흐름:** 한 달 뒤 "지난 NVDA 결정 복기해줘, 현재 -8%" → Phase R → journal 대조: 무효화 조건(SMA50 이탈)이 이미 발동했는데 미청산 → 교훈 "철회 트리거 발동 시 행동 지연" lessons.md 기록 → 다음 실행에서 trader·portfolio-manager가 반영.
