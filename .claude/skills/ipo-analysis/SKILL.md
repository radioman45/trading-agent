---
name: ipo-analysis
description: IPO(신규상장) 투자 분석 하네스 오케스트레이터 — 미국(SEC)·한국(DART) IPO 범용. 상장 예정/직후 기업을 강세(Bull)·약세(Bear) 적대적 분석가가 독립 분석하고, 팩트체커가 공시(S-1/FWP·증권신고서) 사실관계를 검증한 뒤, 심판(Judge)이 IPO 판정(공모가 대비 가치·진입가치구간)을 내리고, 판결 검토관이 그 추론을 red-team 검증하며, 실행 전략가가 IPO 진입 타이밍 전략(IPO pop·이벤트 기반 분할·가설훼손 관리·리스크 한도·투자자 접근성)으로 변환하고, 판정을 decisions/journal.md에 기록해 상장 후 복기로 교훈을 축적하는 파이프라인을 조율한다. "{회사} 상장 분석", "IPO 분석", "공모주 분석", "국내 공모주 분석", "청약할까", "수요예측 결과 반영", "상장 강세 약세 비교", "IPO 진입 시점", "상장일 매수 전략", "IPO pop 대응", "따상 추격", "공모가 대비 가치"를 요청받으면 반드시 이 스킬을 사용한다. 후속 요청도 처리: "다시 분석", "재실행", "업데이트", "강세론만 다시", "약세 보강", "판결 검토만 다시", "진입전략만 다시", "IPO 타이밍만 다시", "스냅샷 갱신", "최신 공시로 다시", "이전 결과 기반으로", "결론 수정", "복기", "결과 반영", "교훈 정리". 단, 일반 IPO 상식 질문은 직접 응답해도 된다.
---

# IPO Analysis — 신규상장 적대적 투자 분석 하네스

상장 예정/직후 기업을 **여섯 명의 전문가**가 분업해 분석한다. 한 명은 옹호(Bull), 한 명은 반대(Bear), 한 명은 공시 사실을 검증(Fact-check), 한 명이 IPO 판정(Judge), 한 명이 그 판결의 추론을 red-team 검증(Verdict Review), 마지막 한 명이 판결을 **IPO 진입 타이밍 전략**으로 변환(Execution)한다. 거래 계획도 같은 검토관이 한 번 더 감사한다.

**왜 IPO 전용인가:** IPO에는 거래 이력·과거 멀티플·시장 가격이 없다. 결론은 공모 구조·첫 거래 가격발견·유통물량·안정조작·락업·지수편입·**한국 투자자 실제 접근성**이 지배한다. 그래서 스냅샷(`ipo-snapshot`)과 진입 전략(`ipo-timing`)이 2차 시장 버전과 다르고, 분석 스킬들도 IPO 모드로 분기한다.

**실행 모드: 서브 에이전트 (병렬 팬아웃 + 파이프라인).** Bull과 Bear는 서로의 보고서를 **봐서는 안 되므로**(적대적 독립성), 파일로만 데이터를 주고받는다. 계층별 라우팅: 저부하=sonnet, 생성·판단 코어=opus 명시.

## Phase 0: 컨텍스트 확인

작업 시작 전 `_workspace_ipo/` 상태를 확인해 실행 모드를 결정한다.

| 상황 | 모드 | 행동 |
|------|------|------|
| `_workspace_ipo/` 없음 | **초기 실행** | 새로 생성, Phase 1부터 전체 실행 |
| `_workspace_ipo/` 있음 + 새 대상/새 공시 | **새 실행** | 기존 `_workspace_ipo/`를 `_workspace_ipo_prev/`로 이동 후 처음부터 |
| `_workspace_ipo/` 있음 + 부분 수정("강세론만 다시", "진입전략만 다시", "최신 공시로 스냅샷만") | **부분 재실행** | 해당 단계만 재호출, 하류 단계는 그 결과로 다시 흐름 |
| "복기", "결과 반영", "그 IPO 어땠는지", "교훈 정리" | **복기 모드** | Phase R로 직행 — 파이프라인 재실행 없음 |

부분 재실행 의존성: 보고서가 바뀌면 → 팩트체크 → 심판 → 판결검토 → 진입전략 → 전략검토를 순차 갱신. 심판만 바뀌면 → 판결검토 → 진입전략 → 전략검토. "진입전략만 다시"면 진입전략 → 전략검토. **스냅샷(`00_ipo_snapshot.json`)이 갱신되면** 그 위의 모든 분석이 무효 → Bull/Bear부터 전체 하류 재실행. **부분 재실행 후 Phase 6 재진입:** 재실행으로 판정(BUY/HOLD/SELL·확신도) 또는 채택 진입 계획이 바뀌었으면 Phase 6을 재진입한다 — reports/에 갱신 파일 재복사 + 저널에 정정 항목 1건 append(기존 항목은 본문 수정 금지, 그 `결과:` 줄에 `[대체됨 → {날짜} 정정 항목]` 기입 — 복기·캘리브레이션은 최신 항목 기준) + decisions/ 커밋. 판정·계획이 그대로면 갱신 산출물만 재복사한다(스테일 저널·reports 방지).

**Pending 자동 결산 (모든 모드 공통, 시작 시):** `decisions/journal.md`에 `결과: (미기록` 항목이 있으면, 해당 종목의 상장(거래 개시) 여부를 확인한다. 상장 후면 현재가·공모가·같은 기간 벤치마크 등락을 확인해 그 항목의 `결과:` 줄만 `결과: [중간점검 {YYYY-MM-DD}] 공모가 대비 {±X}%, 벤치마크 {±Y}% (알파 {±Z}%p)`로 갱신하고, 사용자에게 복기(Phase R)를 한 번 제안한다(강요 금지). 상장 전이면 건너뛴다.

## Phase 1: 입력 수집

1. 분석 대상(회사/티커)과 **상장일·공모 정보**를 확인한다. 시드 노트(예: `docs/ipo/spcx-seed.txt`)가 있으면 요약해 넣되, 숫자는 "시드"로만 표기(1차 출처로 교차 예정).
   - **현재 시각·세션 앵커 [HARD]:** 진행 전 현재 날짜·시각을 확인해 입력에 기록한다. 아직 발생하지 않은 일(미확정 공모가, 상장 전 거래가, 마감 안 된 세션 종가)을 *확정 사실*로 쓰지 않는다 — 모든 하류 에이전트가 이 앵커로 시점을 판정한다(할루시네이션 방지 — `docs/anti-hallucination-verification-plan.md`).
2. 사용자 맥락(선택): 투자 기간, 리스크 허용도, 보유 목적. 없으면 보수/중립/공격 3성향 모두 산출.
3. `_workspace_ipo/00_orchestrator_input.md`에 기록:

```markdown
# IPO 분석 입력
- 대상: {회사명} ({티커})
- 시장/거래소: {예: US / Nasdaq}
- 상장(거래개시) 예정일: {YYYY-MM-DD}
- 공모가 확정 예정일: {YYYY-MM-DD}
- 분석 시점: {오늘}
- 모드: **IPO** (상장 전/직후)
- 시드 요약: {시드 노트에서 추출한 공모 조건 — "시드값, 1차 출처 교차 필요"로 표기}
- 사용자 맥락: {투자 성향/기간 또는 "일반 분석"}
```

## Phase 1.5: IPO 스냅샷 (데이터 고정)

**data-collector를 단독 호출**한다. Bull/Bear보다 먼저 실행해 공통 스냅샷을 완성한다.

```
# 저부하(데이터 수집) → sonnet
Agent(subagent_type="data-collector", model="sonnet",
      prompt="_workspace_ipo/00_orchestrator_input.md를 읽고, .claude/skills/ipo-snapshot/SKILL.md 방법론으로 _workspace_ipo/00_ipo_snapshot.json을 작성하라. 이것은 IPO(상장 전/직후) 분석이다 — 거래가가 아니라 공모가·발행신주·상장후 주식수·시총·free_float(4필드 분리)·락업·지수편입·세그먼트 재무를 고정하라. EDGAR 최신 문서(424B>S-1/A>FWP) 우선, 상장 전 가격값은 source_status:preliminary. 저장 직전 self_check(시총=공모가×주식수, 조달=공모가×신주, free_float 재계산·갭)를 직접 계산해 채워라. 투자 판단·전망은 넣지 마라.")
```

## Phase 1.6: 스냅샷 audit (숫자 정합성 — 하드 게이트)

스냅샷의 `self_check.overall`을 확인한다.
- **`PASS`** → Phase 2로 진행.
- **`FAIL`** 또는 시총/조달 산식이 어긋나거나 `self_check`가 비어 있음 → **⛔하드 실패.** data-collector를 재호출해 숫자를 바로잡는다(숫자는 의견이 아니라 결정적 값이므로 PASS될 때까지 **최대 3회** 반복 허용). 3회 후에도 FAIL이면 그 사실을 최종 보고에 명시하고, 산술 불일치 필드를 `unavailable`로 처리한 채 진행.
- `free_float.reconciliation_required: true`는 **하드 실패가 아니다**(보도-공시 갭은 fact-checker가 Phase 3에서 규명). 단 audit 메모에 "free_float 갭 미해결 — 팩트체크 대상"으로 남긴다.

> 숫자 모순은 "잔여 리스크"로 하류에 넘기지 않는다 — IPO 전체 분석이 틀린 시총·유통물량 위에 세워지면 무의미하기 때문이다.

> **시점 가드 추가 점검 [HARD] (2026-06-24 사고 반영):** audit 시 산술뿐 아니라 **시점**도 본다 — 스냅샷이 미확정 공모가·상장 전 거래가·마감 안 된 세션 수치를 `source_status:preliminary`/`unavailable` 없이 *확정값*으로 담았으면 ⛔. 출처가 이번 실행에서 실제 조회한 EDGAR/DART 문서인지(날조 의심 표본) 확인. 위반 시 data-collector 재호출.

## Phase 2: 강세·약세 병렬 분석 (격리, IPO 모드)

**bull-analyst와 bear-analyst를 동시에, 서로 격리하여 호출**한다(한 메시지에 함께, `run_in_background: true`). 각 호출에 `model: "opus"`.

```
Agent(subagent_type="bull-analyst", model="opus", run_in_background=true,
      prompt="_workspace_ipo/00_orchestrator_input.md와 00_ipo_snapshot.json을 읽고, .claude/skills/bull-case/SKILL.md의 'IPO 모드'로 강세 보고서를 _workspace_ipo/01_bull_report.md에 작성하라. IPO이므로 PER·기술적지표 대신 공모가 내재 기대치 역산·SOTP/EV 배분(스냅샷 segment_financials의 사업부 구조 기반)·옵션프리미엄 정당화·메가IPO 비교(지수편입 수요·희소 free float·리테일, 한국 IPO면 수요예측 경쟁률·확약 신호)를 축으로. 논거 카드에 컨센서스 대비·반증 신호를, 말미에 가치 시나리오(정량)와 프리모템을 포함하라. decisions/lessons.md가 존재하면 적용 대상(bull/전체) 교훈을 먼저 읽고 과거 실패 패턴을 반복하지 마라. bear의 작업물은 보지 마라.")
Agent(subagent_type="bear-analyst", model="opus", run_in_background=true,
      prompt="_workspace_ipo/00_orchestrator_input.md와 00_ipo_snapshot.json을 읽고, .claude/skills/bear-case/SKILL.md의 'IPO 모드'로 약세 보고서를 _workspace_ipo/01_bear_report.md에 작성하라. 공모가 내재 기대치 공격(기저율 대조·약속 감사·상장 동기)·옵션프리미엄 지배(바닥가치가 매수가 대부분 방어 못함)·락업/의무보유확약 오버행 타임라인·free float 희소→변동성·안정조작 종료·key-man·미검증 세그먼트를 축으로. 논거 카드에 컨센서스 대비·반증 신호를, 말미에 가치 시나리오(정량)와 프리모템을 포함하라. decisions/lessons.md가 존재하면 적용 대상(bear/전체) 교훈을 먼저 읽고 과거 실패 패턴을 반복하지 마라. bull의 작업물은 보지 마라.")
```

두 보고서가 완성될 때까지 기다린 뒤 Phase 3으로.

## Phase 3: 팩트체크 (공시 검증)

```
Agent(subagent_type="fact-checker", model="opus",
      prompt="_workspace_ipo/01_bull_report.md, 01_bear_report.md, 00_ipo_snapshot.json을 읽고, .claude/skills/fact-check/SKILL.md 방법론으로 양측을 동등 검증해 _workspace_ipo/02_factchecker_annotations.md에 작성하라. 결론을 떠받치는 핵심(load-bearing) 주장부터 깊게 검증하고, 양측이 같은 사실을 다르게 인용한 항목은 상충 매트릭스로 정리하라. IPO 소싱 규칙: 미국이면 EDGAR 최신 문서(424B/S-1/A/FWP), 한국이면 DART 정정 증권신고서·투자설명서 최신순으로 대조하고 preliminary/final을 구분하라. 특히 스냅샷의 free_float 갭(reconciliation_required)을 규명하고, rule144·의무보유확약류 '재판매 가능' 주장이 별도 락업 제한 대상인지 확인하라. 스냅샷 숫자에 오류가 있으면 ⛔스냅샷 오류로 표기.")
```

검증 흐름은 선형(Bull/Bear에 되돌려 재작성 안 함). 단 fact-checker가 `⛔스냅샷 오류`를 보고하면 오케스트레이터가 data-collector를 1회 재호출해 스냅샷 갱신 → Bull/Bear부터 하류 재실행.

## Phase 4: 심판 (IPO 판정)

```
Agent(subagent_type="investment-judge", model="opus",
      prompt="_workspace_ipo/01_bull_report.md, 01_bear_report.md, 02_factchecker_annotations.md, 00_ipo_snapshot.json을 읽고, .claude/skills/investment-judge/SKILL.md의 'IPO 판정 모드'로 _workspace_ipo/03_judge_verdict.md를 작성하라. 단일 목표가 단정 금지 — (ㄱ)공모가 대비 가치 정합(바닥 vs 옵션프리미엄), (ㄴ)진입 가치 구간, (ㄷ)크럭스(결정적 쟁점) 식별, (ㄹ)기대값 표(시나리오×확률×페이오프, 공모가 기준, 확률 근거=기저율→사례 조정), (ㅁ)BUY/HOLD/SELL+확신도(무엇의 확률인지 정의)로 판정하라. EV와 결론의 정합을 명시하라. decisions/lessons.md가 존재하면 적용 대상(judge/전체) 교훈을 반영하고, 위반 시 정당화를 명시하라.")
```

## Phase 4.5: 판결 검토 (red-team, Part A)

```
Agent(subagent_type="verdict-reviewer", model="opus",
      prompt="_workspace_ipo/03_judge_verdict.md를 대상으로, 01_bull/01_bear/02_factcheck/00_ipo_snapshot을 대조 입력으로 읽고, .claude/skills/verdict-review/SKILL.md의 Part A 8축 + 'IPO 정합성'(공모구조·락업·free float·접근성 반영 여부)으로 감사해 _workspace_ipo/03b_verdict_review.md에 작성하라. ⛔치명이 있으면 '재작성 필요' 판정 + Judge 수정 지시.")
```

**재작성 루프(최대 1회):** "재작성 필요"(⛔치명≥1)면 investment-judge를 1회 재호출(검토서를 입력으로)해 `03_judge_verdict.md` 재작성, 재검토는 반복 안 함. "재작성 불필요"면 잔여 지적을 Phase 6에서 전달. 검토관이 1회 재시도 후에도 실패하면 검토 없이 진행하되 "판결 검토 미수행" 명시.

## Phase 4.7: 진입 전략 (IPO 타이밍 변환)

```
Agent(subagent_type="execution-strategist", model="opus",
      prompt="_workspace_ipo/03_judge_verdict.md·00_ipo_snapshot.json·03b_verdict_review.md·00_orchestrator_input.md를 읽고, .claude/skills/ipo-timing/SKILL.md 방법론으로 _workspace_ipo/03c_ipo_entry_plan.md를 작성하라. IPO이므로 현재가 손절이 아니라 ①실행 가능성 게이트(투자자 접근성·공모가 확정 전후, 한국 IPO면 청약 경로·수요예측 신호 포함) ②가격발견·안정조작 ③이벤트 기반 분할 진입(상장일·2~4주·첫 실적·락업/확약·지수, 한국 IPO면 0차 청약 구간 검토) ④가설훼손 관리(가치 앵커는 판결의 '공모가 대비 가치 정합'에서 인용, 체크포인트는 판결의 반증 조건·크럭스에서 1:1 도출 — 새 조건 생성 금지) ⑤리스크 한도(잠재 손실=최대 비중×하방 시나리오를 표면화, 1회 캠페인 ≤계좌 2% 골격, 비대칭비 1.5 미만·EV 0 이하면 진입 보류) 순으로. 성향별(보수/중립/공격) 차등. decisions/lessons.md가 존재하면 적용 대상(execution/전체) 교훈을 반영하라. 판결과 반대 방향 금지.")
```

## Phase 4.8: 전략 검토 (red-team, Part B)

```
Agent(subagent_type="verdict-reviewer", model="opus",
      prompt="_workspace_ipo/03c_ipo_entry_plan.md를 대상으로, 03_judge_verdict.md·00_ipo_snapshot.json·03b_verdict_review.md·00_orchestrator_input.md를 대조 입력으로 읽고, .claude/skills/verdict-review/SKILL.md의 Part B 7축 + 'IPO 실행 게이트 점검'(상장일 매수 가능성·안정조작·분할 정합성·리스크 한도 수치: 비중 상한/잠재 손실/비대칭비 게이트)으로 감사해 _workspace_ipo/03d_execution_review.md에 작성하라. decisions/lessons.md가 존재하면 교훈 위반 정당화 여부도 점검하라. ⛔치명이 있으면 '재작성 필요'.")
```

**재작성 루프(최대 1회):** Phase 4.5와 동일 패턴 — "재작성 필요"면 execution-strategist를 1회 재호출(`03d`를 입력으로)해 `03c_ipo_entry_plan.md` 수정, 재검토 없이 Phase 6으로. 검토관 실패 시 "전략 검토 미수행" 명시.

## Phase 6: 산출물 정리 및 보고

1. **모든 단계 보고서**를 `reports/{회사}_IPO_{YYYY-MM-DD}/`에 복사(7종):
   - `강세보고서_{회사}.md` ← `01_bull_report.md`
   - `약세보고서_{회사}.md` ← `01_bear_report.md`
   - `팩트체크_{회사}.md` ← `02_factchecker_annotations.md`
   - `투자판단_{회사}.md` ← `03_judge_verdict.md` (최종 판정)
   - `판결검토_{회사}.md` ← `03b_verdict_review.md`
   - `IPO진입전략_{회사}.md` ← `03c_ipo_entry_plan.md`
   - `전략검토_{회사}.md` ← `03d_execution_review.md`
2. **의사결정 저널 기록:** `decisions/journal.md`에 이번 판정을 1건 append한다(파일 상단의 항목 포맷 준수 — 판정·확신도(정의)·공모 기준·크럭스·핵심 논거·채택 진입 계획(게이트/비중/잠재 손실)·`실행: (미체결)`·가설훼손 체크포인트·잔여 리스크·`결과: (미기록 — 복기 시 갱신)`). **기존 항목은 수정 금지(append-only)** — 후향적 정당화를 막는 장치다.
   - **학습 코퍼스 자동 커밋 [중요]:** 저널 기록 직후 `git add decisions/ && git commit -m "저널: {회사} IPO {판정} 기록"`으로 커밋한다. 학습 코퍼스(journal·lessons)는 이 하네스가 과거로부터 배우는 유일한 축적 자산인데, 무커밋 상태로 방치하면 단일 실패점(작업공간 유실 시 학습 전부 소실)이 된다.
3. `_workspace_ipo/`는 **삭제하지 않고 보존**(작업 원본·감사 추적·부분 재실행용). `00_ipo_snapshot.json`도 보존.
4. 사용자 요약 보고: 최종 판정(BUY/HOLD/SELL + 확신도 + 정의), 핵심 강세/약세 1줄씩, 팩트체크가 바꾼 것(특히 free_float 갭 규명 결과), **판결 검토 결과**(적정성 + 재작성 여부 + 잔여 지적), **IPO 진입전략 핵심**(실행 게이트 결과 + 성향별 1차 구간 유효성 + 잠재 손실/진입 보류 게이트 + 가설훼손 요지 + 전략 검토 결과), 저널 기록 완료, 산출물 경로.
   - **오케스트레이터 레드플래그 자가점검 [HARD] (보고 전):** 핵심 정량 주장 중계 전 — 🚩"오늘/어제/내일/방금" 날짜 수치(시점 확인) 🚩미확정 공모가·상장 전 거래가를 확정처럼 단정 🚩"방증한다"류 단정(관측 vs 가정) — 을 점검하고, 검증 불가하면 **"미확인"으로 명시**해 전달한다. 외부 산출(MP3 등) 생성 후엔 파일 mtime·크기로 실제 갱신을 확인한다(도구 'ok' ≠ 실제 반영).
5. **쉬운 해설판 (표준 산출물 — 입문자용, 생략 금지):** 요약 보고 후 report-explainer를 호출해 IPO 판정을 투자 입문자용 companion 문서로 충실히 옮긴다. 전문 리포트 7종은 그대로 보존되고, 이건 그 위에 얹는 쉬운 번역본이다.
   ```
   # 충실 번역(결론·수치 보존이 생명, 저부하 산출) → sonnet
   Agent(subagent_type="report-explainer", model="sonnet",
         prompt="IPO 하네스 해설 모드. _workspace_ipo/03_judge_verdict.md(필수)·03c_ipo_entry_plan.md·02_factchecker_annotations.md를 읽고, plain-language 스킬로 _workspace_ipo/05_plain_explanation.md를 작성하라. BUY/HOLD/SELL·확신도·공모가 대비 가치·진입 구간·잠재 손실을 한 글자도 왜곡하지 말고, 전문용어(공모가·free float·락업·따상·수요예측 등) 첫 등장 풀이 + 정확한 비유 + 행동 가이드(청약/상장일·진입/철회 트리거) + 용어 풀이 구조로. 출력 전 충실성 자가 점검 필수.")
   ```
   완성본을 `reports/{회사}_IPO_{YYYY-MM-DD}/쉬운해설_{회사}.md`로 복사. 실패 시 1회 재시도, 재실패면 해설판 없이 진행(전문 리포트는 보존)하고 보고에 누락 명시.
6. **팟캐스트 (반드시 묻기 — 생략 금지):** 해설판 생성 후, 판정이 무엇이든 AskUserQuestion으로 묻는다 — "이번 IPO 분석으로 투자 팟캐스트를 만들까요?" 옵션: **① 대본 + 오디오(MP3)** (NotebookLM 로그인 필요, 생성 수 분~십수 분 소요) / **② 대본만** / **③ 만들지 않음**. ③이면 아무것도 만들지 않고 7로.
   - **대본 (①·② 공통):**
     ```
     # 선택형 저부하 산출 → sonnet
     Agent(subagent_type="podcast-producer", model="sonnet",
           prompt="IPO 하네스 대본 모드. _workspace_ipo/03_judge_verdict.md(필수)·03c_ipo_entry_plan.md를 읽고(디테일은 01_bull_report.md/01_bear_report.md), podcast-script 스킬로 _workspace_ipo/04_podcast_script.md를 작성하라. BUY/HOLD/SELL·확신도·진입 전략 수치 왜곡 금지. 하단에 NotebookLM 생성 지침 섹션 필수.")
     ```
     완성본을 `reports/{회사}_IPO_{YYYY-MM-DD}/팟캐스트대본_{회사}.md`로 복사.
   - **오디오 (① 선택 시):** notebooklm-audio 스킬을 따른다 — `--check-only` 사전 점검(코드 2=미인증·3=미설치면 오디오 생략 + 설정 안내, 대본은 보존). 통과 시 번들 스크립트로 생성: `--out "reports/{회사}_IPO_{YYYY-MM-DD}/팟캐스트_{회사}.mp3" --source _workspace_ipo/03_judge_verdict.md --source _workspace_ipo/04_podcast_script.md --format debate --language ko --instructions "{대본의 NotebookLM 생성 지침을 그대로}"`. 실패 시 1회 재시도, 재실패면 대본만 산출물로 보고.
7. 진화: "결과나 팀 구성에서 고치고 싶은 점이 있나요?"를 한 번 묻는다(강요 금지).

## Phase R: 복기 모드 (별도 진입 — 학습 루프)

사용자가 "복기", "결과 반영", "그 IPO 어땠는지", "교훈 정리"를 요청하면 파이프라인을 재실행하지 않고 복기만 수행한다. 대상 종목이 아직 상장 전이면 복기 불가를 알리고 종료한다.

```
Agent(subagent_type="verdict-reviewer", model="opus",
      prompt="decisions/journal.md에서 복기 대상 판정을 찾고(사용자 미지정 시 `결과:` 미기록 항목을 제시해 확인), .claude/skills/ipo-reflection/SKILL.md 방법론으로 복기하라. 상장 후 가격 전개·같은 기간 벤치마크를 수집해 공모가 대비·기준 진입가 대비 수익률과 알파를 산출하고, 4축 대조(논거·크럭스 적중 / 반증·가설훼손 작동 / 진입 설계 적합 / 누락 변수) 후 journal의 해당 항목 `결과:` 줄만 갱신하고, 일반화 가능한 교훈만 decisions/lessons.md에 append하라(1회 관찰은 '가설' 등급). 결과론 금지 — 평가 대상은 결과가 아니라 당시 정보 기준의 의사결정 품질이다.")
```

복기가 journal `결과:` 줄 갱신 + lessons append + calibration.md 1행 추가를 마치면, **커밋 전 세 파일의 실제 갱신을 확인**한다(누락 시 1회 보완 지시 — 복기 완료분이 캘리브레이션 대장에 0행으로 남았던 실측 누락의 재발 방지). 그 후 **학습 코퍼스 자동 커밋 [중요]:** `git add decisions/ && git commit -m "복기: {회사} IPO {판정} 결과 반영"`으로 커밋한다 — 무커밋 방치는 유일한 축적 자산(학습 코퍼스)의 단일 실패점이다.

복기 결과(수익률·알파·의사결정 품질 평가·새 교훈)를 사용자에게 요약 보고한다. 이 교훈은 다음 실행에서 전 판단 에이전트가 읽는다.

## 데이터 전달 프로토콜 (파일 기반)

모든 에이전트는 `_workspace_ipo/` 하위 약속된 파일로만 소통한다(적대적 독립성 보존).

| 단계 | 생산자 | 파일 | 소비자 |
|------|--------|------|--------|
| 입력 | 오케스트레이터 | `00_orchestrator_input.md` | 전원 |
| 1.5 | data-collector | `00_ipo_snapshot.json` | bull, bear, fact-checker, judge, verdict-reviewer, execution-strategist |
| 1.6 | 오케스트레이터 | (audit, 파일 없음 — self_check 게이트) | — |
| 2 | bull-analyst | `01_bull_report.md` | fact-checker, judge, verdict-reviewer |
| 2 | bear-analyst | `01_bear_report.md` | fact-checker, judge, verdict-reviewer |
| 3 | fact-checker | `02_factchecker_annotations.md` | judge, verdict-reviewer |
| 4 | investment-judge | `03_judge_verdict.md` | verdict-reviewer, execution-strategist, 사용자 |
| 4.5 | verdict-reviewer (Part A) | `03b_verdict_review.md` | 오케스트레이터(재작성 루프), execution-strategist, 사용자 |
| 4.7 | execution-strategist | `03c_ipo_entry_plan.md` | verdict-reviewer(Part B), 사용자 |
| 4.8 | verdict-reviewer (Part B) | `03d_execution_review.md` | 오케스트레이터(재작성 루프), 사용자 |
| 6 | 오케스트레이터 | `decisions/journal.md` (append) | Phase 0 pending 결산, Phase R 복기 |
| R | verdict-reviewer (복기) | `journal.md` 결과 줄 갱신 + `decisions/lessons.md` (append) | 차기 실행의 전 판단 에이전트 |
| 6 해설(표준 — 입문자용) | report-explainer | `05_plain_explanation.md` → `reports/.../쉬운해설_{회사}.md` | 사용자 |
| 6 팟캐스트(선택 — 사용자 동의 시만) | podcast-producer | `04_podcast_script.md` → `reports/.../팟캐스트대본·팟캐스트.mp3` | 사용자, notebooklm-audio 스킬 |

**학습 루프:** `decisions/lessons.md`는 모든 판단 에이전트(bull/bear/judge/execution/verdict-reviewer)가 시작 시 자기 `적용 대상` 교훈만 골라 읽는다. 교훈과 정면 충돌하는 판단·계획은 정당화를 명시해야 한다(검토관이 점검).

## 에러 핸들링

- **스냅샷 숫자 모순(Phase 1.6):** ⛔하드 실패 → data-collector 재수집(최대 3회). 산술이 안 맞는 분석은 무의미하므로 잔여 리스크로 넘기지 않는다.
- **에이전트 실패:** 1회 재시도. 재실패 시 그 산출물 없이 진행하고 최종 보고에 누락 명시(예: 약세 부재 시 심판이 "한쪽 관점 부재로 신뢰도 제한").
- **Bull·Bear 양측 모두 실패:** 양측 모두 재시도 후에도 실패 시, 빈 입력으로 하류(팩트체크·심판)를 진행하지 말고 **파이프라인을 중단**한다. 스냅샷을 재확인한 뒤 사용자에게 상황을 보고한다 — 양측 관점이 모두 없으면 판정 자체가 성립하지 않기 때문이다.
- **데이터 미확보:** 삭제·추측 금지. "미확보"/"검증불가"로 표기해 하류 전달. 상장 전 미확정 값은 "preliminary"로.
- **상충 데이터:** 어느 쪽도 지우지 않는다. 상위 문서값 채택 + 출처 병기.
- **접근 차단:** `insane-search` 우회 → 실패 시 미확보 표기.

## 테스트 시나리오

**정상 흐름:** "SpaceX 상장 분석해줘" → Phase 0(초기) → 입력 기록(상장일·시드) → Phase 1.5 data-collector가 `00_ipo_snapshot.json` 생성(self_check PASS) → Phase 1.6 audit 통과 → Bull∥Bear(IPO 모드, 스냅샷 공유) → 팩트체크(EDGAR 최신, free_float 갭 규명) → 심판(예: HOLD 60%, "공모가 대비 옵션프리미엄 지배") → Phase 4.5 판결검토(재작성 불필요) → Phase 4.7 진입전략(실행 게이트 + 성향별 4단계 분할 + 가설훼손) → Phase 4.8 전략검토(재작성 불필요) → reports/에 7종 + 요약 보고 → 쉬운 해설판 생성(입문자용 companion) → 팟캐스트 묻기.

**스냅샷 하드 실패 흐름:** data-collector가 시총을 공모가×주식수와 다르게 적어 self_check FAIL → Phase 1.6이 ⛔하드 실패로 재호출 → 산식 일치시켜 PASS → 진행.

**free_float 갭 규명 흐름:** 스냅샷 reported_claim 7% vs base 4.24% → audit이 "갭 미해결, 팩트체크 대상" 메모 → Phase 3 fact-checker가 7%의 분모/포함 물량을 규명하거나 "미해결 쟁점"으로 → 심판이 free float 불확실성을 변동성 리스크로 반영.

**판결 재작성 흐름:** 심판이 옵션프리미엄을 무시하고 단일 목표가를 단정 → 판결검토가 'IPO 정합성'·확신도 정의를 ⛔치명으로 잡고 "재작성 필요" → investment-judge 1회 재호출 → 가치앵커 기반 판정으로 재작성 → 진입전략으로 진행.

**진입전략 재작성 흐름:** 전략가가 한국 투자자 접근성 게이트를 누락하고 "상장일 일괄매수"를 제시 → Phase 4.8 Part B가 'IPO 실행 게이트'·분할 정합성을 ⛔치명으로 잡음 → execution-strategist 1회 재호출 → 게이트 + 분할로 정정.

**진입전략만 재실행:** "공격형 비중 더 보수적으로, 진입전략만 다시" → Phase 0(부분 재실행) → execution-strategist만 피드백과 재호출 → Phase 4.8 → `03c`/`03d` 갱신 → 채택 진입 계획이 바뀌었으므로 Phase 6 재진입(reports/ 재복사 + 저널 정정 항목 append + decisions/ 커밋) → 보고.

**최신 공시로 스냅샷 갱신:** "최종 투자설명서 나왔으니 스냅샷부터 다시" → 부분 재실행이지만 스냅샷은 최상류 → data-collector 재호출(424B, source_status:final) → Phase 1.6 → Bull/Bear부터 전체 하류 재실행.

**한국 IPO 흐름:** "{회사} 코스닥 상장 분석해줘" → 시장 감지 KR → data-collector가 DART 정정 증권신고서 최신순으로 스냅샷 작성(`kr_ipo`: 공모가 밴드/확정가·수요예측 경쟁률·의무보유확약·청약 구조·상장일 가격범위 60~400%) → Bull∥Bear(확약·수요예측 신호 반영) → 팩트체크(DART 대조) → 판정 → 진입전략(0차 청약 구간 검토 + 원화·T+2·거래세) → 검토 → reports/ 7종 + journal 기록.

**복기 흐름(학습 루프):** 상장 수개월 후 "그 IPO 복기해줘" → Phase R → verdict-reviewer가 ipo-reflection으로 가격·벤치마크 수집(공모가 대비 -12%, 알파 -18%p 등) → 4축 대조("가설훼손 2번이 떴는데 3차 진입을 진행했다" 등) → journal `결과:` 갱신 + lessons에 L-1 append → 다음 분석에서 execution-strategist가 그 교훈을 읽고 반영.
