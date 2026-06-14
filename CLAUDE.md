# Trading Agent — 투자 분석 통합 홈

투자 분석 하네스 **2개**가 이 폴더에 산다 — 트레이딩(2차 시장)과 IPO(신규상장, 미국·한국). 의사결정 저널·교훈(`decisions/`)은 두 하네스 **공용**이다(전체 투자 관점의 단일 학습 루프 — 전 판단 에이전트가 같은 교훈 풀을 읽는다). 작업공간은 분리: 트레이딩 `_workspace/`, IPO `_workspace_ipo/`. 보고서는 `reports/` 공용(IPO 산출물은 `{회사}_IPO_{날짜}/`). 다른 폴더에서 연 세션은 전역 스킬 `invest-router`가 이 홈으로 라우팅한다.

## 하네스 1: 투자전략 트레이딩 (2차 시장, TradingAgents 구조)

**목표:** 한 종목을 거시 레짐 판정(L0, risk-on/off·유동성·바벨) + 데이터 고정(SSOT) → 분석가 4렌즈 병렬(거시 배경) → Bull/Bear 2라운드 토론 → 리서치 판정(역발상) → 거래 계획 → 리스크 3성향 토론(바벨·상관) → 포트폴리오 매니저 최종 게이트(거시·역발상) → 의사결정 저널 기록까지, [TradingAgents](https://github.com/tauricresearch/tradingagents)의 트레이딩 펌 구조 + 뉴로퓨전/월가아재 톱다운 매크로로 자동 수행하고 복기로 학습하는 파이프라인.

**트리거:** 종목 트레이딩/매매/투자전략 분석 요청("{티커} 트레이딩 분석", "사야 돼 팔아야 돼", "거래해도 될까", "거시 레짐/시장 국면", 후속 "다시 실행/거시만 다시/토론 한 라운드 더/거래계획만 다시/복기") 시 `trading-strategy` 스킬을 사용하라. 단순 주가 조회·일반 투자 상식 질문은 직접 응답 가능.

**실행 모드:** 서브 에이전트 (파이프라인 + 팬아웃/팬인 + 생성-검증). Bull/Bear R1과 리스크 3성향은 상호 격리(독립 관점 보존), 데이터는 `_workspace/` 파일로만 전달. 계층별 모델 라우팅(저부하 데이터·팟캐스트·해설=sonnet, 분석·생성·판단 코어=opus).

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-06-10 | 초기 구성 (에이전트 11 + 스킬 7 + 수집 스크립트) | 전체 | TradingAgents(tauricresearch) 구조 이식 — 분석가 팀 4 + 토론 리서처 2 + 매니저 + 트레이더 + 리스크 3성향 + PM 게이트 + 복기 학습 루프 |
| 2026-06-11 | 업스트림 동기화 4건: ① Phase 1에 pending 자동 결산(중간점검+알파) ② 내부자 거래 의무 점검 ③ 복기·저널에 벤치마크 대비 알파 ④ VWMA20 지표 + 지정학·원자재 매크로 테마 | trading-strategy, news.md, trade-reflection, risk-gate, journal.md, collect_market_data.py, technical.md | 원본 TradingAgents 기능 반영도 감사 — 실질 누락 3건 + 경미 2건 보강 |
| 2026-06-11 | IPO 하네스 통합 이관(에이전트 7·스킬 9·docs/ipo) + decisions/ 저널·교훈 공용화(두 하네스 단일 학습 루프) | 전체, decisions/journal.md·lessons.md | 투자 관련 자산을 단일 홈으로 정리 (사용자 요청) |
| 2026-06-11 | 팟캐스트 옵션 추가: Phase 7에 최종 보고 후 **필수 질문**(①대본+오디오 ②대본만 ③만들지 않음) — Stud_stock_analyzer의 podcast-producer·podcast-script·notebooklm-audio(+generate_audio.py) 이식, 두 하네스 겸용으로 일반화(반전 단계: 트레이딩=교차 반박·리스크 상충 / IPO=팩트체크) | trading-strategy, agents/podcast-producer(신규), skills/podcast-script·notebooklm-audio(신규) | 투자 팟캐스트 기능 요청 — 생성 여부는 반드시 사용자에게 확인 |
| 2026-06-14 | 계층별 모델 라우팅 적용(저부하 계층 sonnet, 생성·판단 코어 opus 유지) | CLAUDE.md, trading-strategy/ipo-analysis, 일부 에이전트 정의 | 개선백로그 #1 — model-and-reasoning-choice 노트의 통찰을 실행에 반영 |
| 2026-06-14 | 뉴로퓨전/월가아재 톱다운 보강(4축): ① **L0 거시 레짐 레이어 신설**(macro-strategist 에이전트 + macro-regime 스킬, L1과 병렬·종목 무관·risk-on/off·유동성·성장물가 사분면·바벨 기울기 판정) ② **바벨·상관 리스크**(risk-gate 평가축 ⑦ + barbell-correlation refs, risk-debater·portfolio-manager) ③ **시장구조·포지셔닝**(market-structure refs: 옵션MM 감마·자금흐름·breadth, sentiment/technical 주입) ④ **컨센서스 역발상 메타인지**(contrarian-check 공용 스킬, macro/research-manager/portfolio 참조). 방법론 원천 docs/neurofusion/ 4편(유동성·연준/거시레짐/밸류·버블/포트폴리오·리스크). 11명 5계층 → 12명 6계층 | macro-strategist·macro-regime·contrarian-check(신규), trading-strategy 오케스트레이터, risk-gate·analyst-toolkit(+market-structure·barbell-correlation refs), sentiment/technical/news/trader/risk-debater/research-manager/portfolio-manager 정의, docs/neurofusion/ | 가장 신뢰하는 월가아재(뉴로퓨전 대표)의 향후 전략·보고서로 trading-agent 보강 (사용자 요청) — 종목 단독 분석 위에 톱다운 거시·자산배분·역발상 레이어 |
| 2026-06-15 | **입문자용 쉬운 해설판 레이어 추가**(두 하네스 공용): report-explainer 에이전트 + plain-language 스킬(+references/glossary.md 트레이딩·IPO 공용 용어사전) 신설. Phase 7에 표준 산출물 단계 추가 — 최종 결정을 결론·수치 100% 보존한 채 전문용어 첫 등장 풀이·정확한 비유·행동 가이드 구조로 옮긴 `쉬운해설_{회사}.md`(`_workspace/08_plain_explanation.md`)를 팟캐스트 묻기 전에 생성. 충실성 자가 점검 의무 | report-explainer·plain-language(신규), trading-strategy 오케스트레이터(Phase 7·데이터표·테스트) | NVDA 리포트가 함축적·전문용어 과다로 초보 독자 이해 불가 — 정밀 리포트는 보존하고 별도 해설판 추가 (사용자 요청) |

## 하네스 2: IPO 적대적 투자 분석 (범용 — 미국·한국)

**목표:** 신규상장(IPO) 기업을 — 미국(SEC EDGAR)·한국(DART) 어느 시장이든 — 강세·약세 적대적 분석 → 공시(S-1/FWP·증권신고서) 팩트체크 → IPO 판정(공모가 대비 가치) → 판결 red-team → IPO 진입 타이밍 전략(IPO pop·이벤트 분할·가설훼손·리스크 한도·투자자 접근성) → 전략 red-team → 의사결정 저널 기록까지 산출하고, 상장 후 복기로 교훈을 축적하는 6전문가 파이프라인 + 학습 루프. (첫 적용 사례: SpaceX/SPCX — 시드 노트 `docs/ipo/spcx-seed.txt`.)

**트리거:** IPO/상장/공모주 관련 분석 요청("{회사} 상장 분석", "IPO 분석", "공모주 분석", "청약할까", "수요예측 결과 반영", "IPO 진입 시점", "따상 추격", "상장 강세 약세 비교", "공모가 대비 가치", 후속 "강세론만 다시"/"진입전략만 다시"/"최신 공시로 스냅샷만"/"복기"/"결과 반영") 시 `ipo-analysis` 스킬을 사용하라. 단순 IPO 상식 질문은 직접 응답 가능.

**실행 모드:** 서브 에이전트 (병렬 팬아웃 + 파이프라인). Bull·Bear는 상호 격리(적대적 독립성), 데이터는 `_workspace_ipo/` 파일로만 전달(트레이딩 하네스의 `_workspace/`와 분리). 스냅샷 숫자 모순은 Phase 1.6에서 ⛔하드 실패. 계층별 모델 라우팅(저부하 데이터·팟캐스트·해설=sonnet, 분석·생성·판단 코어=opus). **학습 루프:** 판정은 공용 `decisions/journal.md`(append-only)에 기록, 복기(`ipo-reflection`)가 공용 `decisions/lessons.md`에 교훈을 쌓는다.

**fork 베이스:** `Stud_stock_analyzer`(2차 시장 하네스, 커밋 fa2b0a9)를 fork + IPO 특화. 공통 자산 드리프트 추적과 트레이딩 하네스와의 전략 골격 정렬(리스크 한도·학습 루프)은 `docs/ipo/UPSTREAM_SYNC.md`, 구축 계획·근거는 `docs/ipo/HARNESS_PLAN.md`(v2, Codex 비판검증 반영) 참조.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-06-09 | 초기 구성 (에이전트 7 + 스킬 8) | 전체 | Stud_stock_analyzer fork + IPO 특화. 신규 ipo-snapshot/ipo-timing/ipo-analysis, 기존 5스킬 IPO 모드 분기. 팟캐스트 3종 제외 |
| 2026-06-10 | 분석·종합 스킬 방법론 고도화: 내재 기대치 역산(bull/bear), 약속 감사·상장 동기 분석(bear), 논거 카드에 컨센서스 대비·반증 신호, 가치 시나리오·프리모템(schema), 중요도 우선 검증·체리피킹·상충 매트릭스(fact-check), 기대값 표·크럭스·기저율 정직 표기·선택적 종합 금지(judge 6원칙), EV 재계산·EV→행동 정합(verdict-review), ipo-timing 가설훼손 체크포인트를 판결 반증 조건에서 도출 | skills/bull-case·bear-case·fact-check·investment-judge·verdict-review·ipo-timing·ipo-analysis·report-schema, agents 4종 | 스킬 품질 개선 (Mauboussin 기대치 투자·Tetlock 캘리브레이션·포렌식 리서치 반영) |
| 2026-06-11 | trading-agent 전략 골격 정렬: 학습 루프(journal/lessons/ipo-reflection 복기/Phase R/pending 결산/전 판단 에이전트 lessons 읽기) + 리스크 한도 수치화(1회 캠페인 잠재 손실 ≤2% 골격, 비중 상한 3/7/15 = 공통 상한의 IPO 할인, 진입 보류 게이트 비대칭비 1.5·EV≤0, Part B 수치 게이트·교훈 점검) | skills/ipo-reflection(신규)·ipo-timing·ipo-analysis·verdict-review, agents 5종, decisions/ | 전체 투자 관점의 일관적 전략 방향 — 트레이딩 하네스와 정렬 |
| 2026-06-11 | 범용 IPO 하네스로 일반화: SpaceX 잔재 일반화(진입표·가치앵커·세그먼트 예시화), 한국 IPO 분기(DART 정정 증권신고서 최신순, kr_ipo 블록: 수요예측·의무보유확약·청약 구조·상장일 60~400%·환매청구권, 한국 게이트 0차 청약·따상 금지·T+2·세제), data-collector 스킬 참조 오류(market-snapshot→ipo-snapshot) 수정 | skills/ipo-analysis·ipo-snapshot·ipo-timing·fact-check·bull-case·bear-case·data-sources, agents/data-collector·execution-strategist | 미국·국내 어느 IPO에도 적용 가능한 범용화 (사용자 요청) |
| 2026-06-11 | trading-agent로 통합 이관: 에이전트·스킬을 공용 `.claude/`로, 작업공간 `_workspace/`→`_workspace_ipo/`, 보고서 `reports/{회사}_IPO_{날짜}/`, 저널·교훈 공용화, 문서는 docs/ipo/로 | 전체 | 투자 관련 자산 단일 홈 정리 (사용자 요청) |
| 2026-06-11 | 팟캐스트 옵션 추가: Phase 6에 최종 보고 후 **필수 질문**(①대본+오디오 ②대본만 ③만들지 않음) — 공용 podcast-producer 사용, 출력 `_workspace_ipo/04_podcast_script.md` → `reports/{회사}_IPO_{날짜}/팟캐스트대본·팟캐스트.mp3` | ipo-analysis | 투자 팟캐스트 기능 요청 — 생성 여부는 반드시 사용자에게 확인 |
| 2026-06-14 | 계층별 모델 라우팅 적용(저부하 계층 sonnet, 생성·판단 코어 opus 유지) | CLAUDE.md, trading-strategy/ipo-analysis, 일부 에이전트 정의 | 개선백로그 #1 — model-and-reasoning-choice 노트의 통찰을 실행에 반영 |
| 2026-06-15 | **입문자용 쉬운 해설판 레이어 추가**(트레이딩과 공용): Phase 6에 표준 산출물 단계 추가 — IPO 판정을 결론·수치 100% 보존한 채 공모가·free float·락업·따상·수요예측 등 용어 첫 등장 풀이·비유·행동 가이드 구조로 옮긴 `쉬운해설_{회사}.md`(`_workspace_ipo/05_plain_explanation.md`)를 팟캐스트 묻기 전에 생성. 공용 report-explainer 에이전트 + plain-language 스킬 사용 | ipo-analysis 오케스트레이터(Phase 6·데이터표·테스트), report-explainer·plain-language(트레이딩 하네스에서 신규, 공용) | 신규상장 리포트도 전문용어 과다로 초보 이해 곤란 — 트레이딩과 동일하게 해설판 공용 적용 (사용자 요청) |
