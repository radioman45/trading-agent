# Trading Agent — 3하네스 전체 구조 다이어그램

작성: 2026-07-04 (독립 검증 2라운드 완료 시점) · 갱신: 2026-07-05 (수집 레이어 기계 판정 — session 블록·이중 소스 교차·DEGRADED_DATA 체인 배선 + CRYPTO 시장 모드 — always_open 24/7·크립토 교차 체인). 규칙 상세는 각 오케스트레이터 스킬(`trading-strategy` / `ipo-analysis` / `filings-analysis`)이 SSOT — 이 문서는 구조 조감도다.

## 하네스 1: 투자전략 트레이딩 (trading-strategy)

14명 6계층 + 소싱·포트폴리오 레이어. L0∥L1 병렬 → 검증 게이트 → 4렌즈 팬아웃 → 2라운드 토론 → 거래 계획 → 리스크 4자 병렬 → PM 게이트 → 저널.

```mermaid
flowchart TB
  U["사용자: {티커} 트레이딩 분석"] --> P0["Phase 0: 모드 판정 + 워크스페이스 회전"]
  P0 --> P1["Phase 1: 입력·세션 앵커·pending 결산·보유 확인<br/>(크립토) 매매 수단 확인 — 직접 티커 vs 현물 ETF<br/>00_input.md"]

  subgraph PAR1["Phase 1 병렬 (상호 독립)"]
    MS["L0 macro-strategist (opus)<br/>00_macro_regime.md — 레짐·바벨"]
    MDE["L1 market-data-engineer (sonnet)<br/>00_market_snapshot.json·OHLCV·지표 (SSOT, v1.1)<br/>시장 3종 자동 감지: KR · US · CRYPTO(always_open 24/7)<br/>수집 스크립트가 session·cross_check 기계 판정<br/>(세션 LLM 재판정 금지 — 블록 전체 복사, Stooq 폴백 자동·US만)<br/>교차: US stooq→nasdaq / CRYPTO coinbase→binance / KR 네이버·KRX(LLM)"]
  end
  P1 --> MS
  P1 --> MDE

  MS --> G16{"Phase 1.6 사실 검증 게이트 [DEGRADED — 정정 1회]<br/>fact-checker (sonnet) → 00_factcheck.md<br/>시점(기계 session 앵커)·산술·출처·SSOT충돌·수집 레이어 정합<br/>재실패 시 '미확인' 강등 → 검증 모드 DEGRADED_DATA"}
  MDE --> G16
  G16 -->|"⛔ 발견: 소스 1회 재호출"| MS

  G16 -->|PASS| P2
  subgraph P2["Phase 2 분석가 4렌즈 병렬·상호 격리 (opus)"]
    FA["fundamental-analyst<br/>01_fundamental_report.md"]
    TA["technical-analyst<br/>01_technical_report.md"]
    NA["news-analyst<br/>01_news_report.md"]
    SA["sentiment-analyst<br/>01_sentiment_report.md"]
  end

  P2 --> R1["Phase 3 R1: bull ∥ bear 논지 (격리)<br/>02_bull/bear_thesis.md"]
  R1 --> R2["R2: 교차 반박 (파일로만 교차)<br/>02_bull/bear_rebuttal.md"]
  R2 --> RM["research-manager 판정 (opus)<br/>03_research_plan.md — 방향·무효화·확신도(표준 앵커)"]

  RM --> TR["Phase 4 trader (opus)<br/>04_trade_plan.md — 손절 먼저 비중 역산 + 꼬리 검산"]

  TR --> P5
  subgraph P5["Phase 5 병렬·상호 격리"]
    RD["risk-debater ×3 (공격 ∥ 중립 ∥ 보수)<br/>05_risk_*.md"]
    PRA["portfolio-risk-analyst (opus)<br/>05_portfolio_impact.md — 보유 북 영향<br/>모드: PORTFOLIO_AWARE / SINGLE_TRADE_ONLY / PORTFOLIO_STALE"]
  end

  P5 --> PM["Phase 6 portfolio-manager 최종 게이트 (opus)<br/>APPROVE / CONDITIONAL_APPROVE / REVISE / REJECT<br/>06_final_decision.md — 판정 요약 박스(검증·포트폴리오 모드) + 경고 대장<br/>검증 모드: factcheck '미확인' 또는 cross_check mismatch·단일소스 미검증 → DEGRADED_DATA<br/>+ journal append · 거시·역발상·포트폴리오·기회비용 게이트"]
  PM -->|"REVISE (1회): trader/RM 재작성<br/>+ 비중 변경 시 PRA 재계산"| TR
  PM --> P7["Phase 7: reports/ 복사 + decisions/ 커밋 + 요약 보고"]
  P7 --> DOC{"harness doctor --harness trading [DEGRADED — 사후·정정 1회]<br/>09_doctor.json → 닥터리포트 보존<br/>산출물 존재·산술·판정-게이트 모순·모드 정합<br/>+ session 복사 충실성(생략·변조 FAIL)·mismatch↔DEGRADED_DATA 정합"}
  DOC -->|"라벨 모순 FAIL: PM 1회 재호출<br/>케이스별 처방(⛔+승인 = REVISE 해소 마커 또는 REVISE/REJECT,<br/>미스라벨 = 라벨만 정정) + 저널 정정 append"| PM
  DOC --> EXP["report-explainer (sonnet)<br/>08_plain → 쉬운해설 (표준 산출물)"]
  EXP --> POD["팟캐스트 (선택 — 반드시 묻기)<br/>podcast-producer (sonnet) + notebooklm-audio"]
```

**별도 진입 모드:**

```mermaid
flowchart LR
  S["Phase S 아이디어 스캔<br/>idea-scanner (opus): 레짐 → 후보·워치리스트"] --> WLF["decisions/watchlist.md"]
  M["Phase M 포지션 점검<br/>열린 결정의 무효화 트리거 모니터링"] --> JR["journal 결과: 줄 [중간점검]"]
  P["Phase P 상태 갱신<br/>보유 등록·체결 반영"] --> PJ["decisions/portfolio.json + journal 실행: 줄 (동시 갱신)"]
  R["Phase R 복기<br/>portfolio-manager (trade-reflection)"] --> LC["journal 결과 확정 + lessons + calibration 1행<br/>커밋 전 기입 확인 게이트"]
```

## 하네스 2: IPO 적대적 투자 분석 (ipo-analysis)

6전문가 파이프라인 + 학습 루프. 미국(EDGAR)·한국(DART) 범용.

```mermaid
flowchart TB
  U2["사용자: {회사} IPO/공모주 분석"] --> Q0["Phase 0: 모드 판정 + pending 결산"]
  Q0 --> Q1["Phase 1: 입력·세션 앵커<br/>00_orchestrator_input.md"]
  Q1 --> DC["Phase 1.5 data-collector (sonnet)<br/>00_ipo_snapshot.json — 공모가·주식수·free float·락업 SSOT"]
  DC --> A16{"Phase 1.6 스냅샷 audit [DEGRADED — 수복 3회]<br/>self_check + 시점 가드<br/>3회 후 FAIL 필드는 unavailable 강등·진행"}
  A16 -->|FAIL| DC

  A16 -->|PASS| Q2
  subgraph Q2["Phase 2 병렬·상호 격리 (opus)"]
    BU["bull-analyst<br/>01_bull_report.md — 내재 기대치·옵션가치"]
    BE["bear-analyst<br/>01_bear_report.md — 기대치 공격·락업 오버행"]
  end

  Q2 --> FC2["Phase 3 fact-checker (opus)<br/>02_factchecker_annotations.md — 공시 대조·상충 매트릭스"]
  FC2 -->|"⛔스냅샷 오류"| DC
  FC2 --> JD["Phase 4 investment-judge (opus)<br/>03_judge_verdict.md — BUY/HOLD/SELL + 확신도(상장 후 12개월 벤치마크 초과수익 확률)"]
  JD --> VR1{"Phase 4.5 verdict-reviewer Part A<br/>판결 red-team (재작성 루프 1회)<br/>재작성 시 변경 수치 재검증 — SSOT 대조·EV 산술 스팟체크"}
  VR1 -->|"⛔치명: 재작성"| JD
  VR1 --> ES["Phase 4.7 execution-strategist (opus)<br/>03c_ipo_entry_plan.md — 실행 게이트·이벤트 분할·가설훼손·리스크 한도"]
  ES --> VR2{"Phase 4.8 verdict-reviewer Part B<br/>전략 red-team (재작성 루프 1회)<br/>재작성 시 변경 수치 재검증 — 비중·잠재손실·비대칭비 스팟체크"}
  VR2 -->|"⛔치명: 재작성"| ES
  VR2 --> Q6["Phase 6: reports/ 7종 복사 + journal append + decisions/ 커밋<br/>+ harness doctor --harness ipo [DEGRADED — 사후·수복 1회] → 닥터리포트<br/>+ 쉬운해설 (report-explainer) + 팟캐스트 (선택)"]
  Q6 -.->|"부분 재실행으로 판정/계획 변경 시 Phase 6 재진입<br/>(저널 정정 항목 + reports 재복사)"| Q6
  Q6 -.-> QR["Phase R 복기 — verdict-reviewer (ipo-reflection)<br/>journal 결과 확정 + lessons + calibration<br/>커밋 전 3파일 갱신 확인 게이트"]
```

## 하네스 3: 공시 보고서 체계 분석 (filings-analysis)

제공 파일만·이해 목적 — **매매 판단·저널 기록 없음** (매매 판단은 트레이딩 하네스로).

```mermaid
flowchart TB
  U3["사용자: 공시 원문 제공 (10-K/10-Q·DART 보고서)"] --> D0["D0 filings-archivist (opus)<br/>00_filings_facts.json — 사실 SSOT 고정"]
  D0 --> D06{"D0.6 disclosure-auditor 추출 게이트 [DEGRADED — 1회 수복 후 강등·진행]<br/>수치·단위·기간·산술·출처 (⛔ 시 재작성)"}
  D06 -->|"⛔"| D0

  D06 -->|PASS| D1
  subgraph D1["D1 4렌즈 병렬·상호 격리 (opus)"]
    FIN["financial-statement-analyst<br/>01_financial_report.md"]
    MDA["mdna-analyst<br/>01_mdna_report.md"]
    SEG["segment-analyst<br/>01_segment_report.md"]
    RSK["risk-disclosure-analyst<br/>01_risk_report.md"]
  end

  D1 --> D2["D2 [선택] industry-analyst<br/>산업 자가진단 22질문 (기본 off)"]
  D2 --> D3["D3 filings-synthesizer (opus)<br/>03_synthesis.md — 렌즈 일치·상충 종합"]
  D1 --> D3
  D3 --> D35{"D3.5 disclosure-auditor 종합 red-team<br/>과대해석·상충 누락·단정 (⛔ 시 재작성)"}
  D35 -->|"⛔"| D3
  D35 --> D4["D4 report-explainer (sonnet)<br/>04_plain — 쉬운해설 ('다음 공시에서 확인할 것')"]
  D4 --> P6F["Phase 6: reports/ 복사<br/>+ harness doctor --harness filings [DEGRADED — 사후·수복 1회]<br/>필수 산출물 + 매매언어 경계 휴리스틱 → 닥터리포트"]
  P6F --> PODF["[선택] podcast-producer<br/>갈등 축 = 렌즈 상충 (매매 발언 금지)"]
```

## 공용 자산 · 학습 루프 (트레이딩 + IPO)

```mermaid
flowchart LR
  subgraph HARNESS["판정 생산자"]
    TH["트레이딩 Phase 6<br/>portfolio-manager"]
    IH["IPO Phase 6<br/>오케스트레이터"]
  end

  subgraph DEC["decisions/ — 공용 학습 코퍼스 (append-only·커밋 의무)"]
    J["journal.md<br/>전 판정 기록 (REVISE·최종 쌍 = 1결정)"]
    LS["lessons.md<br/>일반화 교훈"]
    CAL["calibration.md<br/>확신도 p vs 결과 o · Brier·버킷<br/>지평·확정 트리거 컬럼 (만기 전 조기 확정 금지)"]
    PF["portfolio.json<br/>보유 SSOT"]
    WL["watchlist.md"]
  end

  TH --> J
  IH --> J
  J --> REF["복기 (Phase R)<br/>트레이딩: portfolio-manager / IPO: verdict-reviewer"]
  REF --> LS
  REF --> CAL
  LS -->|"시작 시 '적용 대상' 교훈 읽기"| ALL["차기 실행의 전 판단 에이전트<br/>(bull·bear·judge·RM·trader·PM·execution)"]

  subgraph SHARED["3하네스 공용 에이전트·스킬"]
    RE["report-explainer + plain-language<br/>(쉬운해설 — 3하네스)"]
    PP["podcast-producer + podcast-script·notebooklm-audio<br/>(팟캐스트 — 3하네스, 사용자 동의 시만)"]
    FCX["fact-checker (2모드: IPO 검증 / 트레이딩 L0·L1 게이트)"]
    CC["contrarian-check 스킬<br/>(역발상 메타인지 — L0·L3·L5)"]
    HD["scripts/harness_doctor.py<br/>(기계 검증 — 3하네스 공용, 사후 DEGRADED·수복 1회<br/>결정적 불변조건만 — LLM 게이트 대체 아님·보완)"]
  end
```

**격리 원칙 요약:** Bull↔Bear(R1)·리스크 3성향·4렌즈는 서로의 산출물을 보지 않는다(독립 관점 = 정보량). 데이터 전달은 워크스페이스 파일로만(트레이딩 `_workspace/`, IPO `_workspace_ipo/`, 공시 `_workspace_filings/`). 생성-검증 분리: 자기 산출물을 자기가 검증하지 않는다(fact-checker·verdict-reviewer·disclosure-auditor가 격리 검증).
