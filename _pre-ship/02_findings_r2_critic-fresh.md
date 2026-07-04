# 실행 시뮬레이션 감사 — 트레이딩·IPO·공시 하네스 (r2-critic-fresh, 2026-07-04, 동적 경로)

**감사 모드:** THOROUGH → 3건 이상 실질 결함으로 ADVERSARIAL 전환(저널·부분재실행 경로를 인접 하네스까지 확대 점검).
**사전 예측 대비:** 5개 예측 중 3개 적중 — 부분 재실행 스테일 오염 ✅, 저널 이중 기록원 ✅, 격리 vs 파일전달 모순 ❌(깨끗함). 경로 불일치는 대부분 정합했으나 저널 append 계약에서 정의 충돌을 새로 발견.

---

## ① 발견 결함 (심각도순)

### 🔴→🟡 F1. 트레이딩 저널 append 계약이 두 정의 파일에서 충돌 → 실측 이중 기록
**근거(정의 충돌):**
- `risk-gate/SKILL.md:68-72` 판정 규칙 표는 **APPROVE·REJECT에만** "저널 기록"을 명시, **REVISE는 미명시**(REVISE는 Phase 6 내부 중간 상태).
- 그러나 `portfolio-manager.md:29` "**저널 기록은 의무다. 판정 직후 ... 1건을 덧붙인다**"(무조건) + 오케스트레이터 `trading-strategy/SKILL.md:144`(무조건 append).

**실패 시나리오(실측 확인):** `decisions/journal.md`에 REVISE+APPROVE 이중 항목이 실재 — NVDA(`journal.md:54,66`), MKIF 6/24(`journal.md:78,90`), MU(`journal.md:112,124`). PM이 중간 REVISE에도 저널을 썼다. 현재는 REVISE 항목 `결과:` 줄을 수동으로 "복기는 APPROVE 항목에 기록"(`journal.md:63`)으로 채워 봉합 중 — 정의가 아니라 사람 개입.

**자동화 위험:** Phase 1 pending 결산(`trading-strategy/SKILL.md:49`)은 `결과:(미기록`을 스캔. REVISE 항목 append 직후~복기 전 창에서 새 파이프라인이 돌면 REVISE·APPROVE 두 미기록 항목을 이중 결산 → 캘리브레이션 이중 계상. 저널 포맷(`risk-gate/SKILL.md:112`)에 supersede/링크 필드 없음.

**부분 재실행이 악화:** Phase 0 의존성(`trading-strategy/SKILL.md:43`) "리스크 토론 갱신 → 최종 게이트만", "거래계획만 다시 → 리스크 토론부터"가 전부 Phase 6로 회귀 → 무조건 append. 별도 세션의 "리스크 검토만 다시"는 첫 항목과 연결 안 된 중복 생성.
**심각도:** 학습 코퍼스 오염 실측이나 수동 봉합+사람 감지 가능 → 🟡, 자동 결산 미봉합 시점에선 🔴 상승. **확신도 HIGH.**

### 🟡 F2. IPO 부분 재실행은 정반대 결함 — 저널·reports 스테일
**근거:** IPO Phase 0 의존성(`ipo-analysis/SKILL.md:25`) "심판만 바뀌면 → 판결검토 → 진입전략 → **전략검토(4.8)**"에서 끝남. 저널 append·reports 복사가 있는 **Phase 6이 체인에 없음**. 테스트 시나리오(`:213`)도 "→ 03c/03d 갱신 → 보고"로 종료.
**실패 시나리오:** 최초 실행이 저널에 `HOLD 70%` append 후, "강세론만 다시"가 팩트체크·심판까지 캐스케이드(`:22`)해 `03_judge_verdict.md`가 `BUY 55%`로 바뀌어도, 저널은 append-only(`:133`)라 옛 `HOLD 70%` 고정+정정 항목 규칙 없음. `reports/.../투자판단_{회사}.md`도 옛 분석 유지. 복기(`:162`)가 옛 판정 기준 채점 → 학습 오염.
**구조적 비대칭:** 같은 "재분석 후 저널 정합" 문제를 트레이딩은 Phase 6 재진입(→중복), IPO는 미진입(→스테일)으로 정반대 미정의. **확신도 HIGH.**

### 🟡 F3. 보유 상태 이중 기록원(portfolio.json ↔ journal 실행 줄)이 한쪽 경로에서만 정합
**근거:** Phase P 두 진입점의 저널 정합이 다름 —
- "보유 등록/갱신"(`trading-strategy/SKILL.md:201`): **portfolio.json만** 갱신.
- "체결 반영/실제로 샀어"(`:202`): journal `실행:` 줄 **+** portfolio.json 둘 다.

**실패 시나리오:** 사용자가 MKIF APPROVE 후 실매수하고 "보유 등록"으로 portfolio.json에만 넣으면 저널 `실행:`은 "(미체결)" 유지 → 복기가 체결 기록 없음으로 보고(`portfolio-manager.md:41`) **미진입(가상·기회비용)으로 오채점**. 두 기록원 교차검증 규칙 부재. **확신도 MEDIUM**(특정 사용자 경로 의존, 현재 portfolio.json은 `holdings:[]`라 미발현).

### 🟡 F4. 캘리브레이션 측정 leg가 정의상 강제되나 검증 게이트 부재 — 코퍼스상 미봉합
**근거:** 복기 정의(`trading-strategy/SKILL.md:178`, `portfolio-manager.md:43`, `ipo-analysis/SKILL.md:162`)는 "calibration.md 1행 추가+버킷 재계산"을 명령하나, Phase R/PM 모드2 어디에도 수행 검증 게이트 없음(호출 후 바로 커밋).
**실패 시나리오(실측):** journal에 `[복기 2026-06-26]` 확정 5건+(삼성 `:29`, SPCX×2 `:40,51`, NVDA `:75`)인데 `decisions/calibration.md` 데이터 행은 **0건**(header만, `:7-8`). "복기→1행 추가"가 반복 누락됐고 게이트가 못 잡음. 과신 교정 목적이 닫히지 않음. **확신도 HIGH.**

### 🟢 G1. 트레이딩 Phase 1.6 게이트가 "한쪽만 생성" 케이스 미규정
`:90` "둘 다 미생성이면 건너뜀"만 규정. snapshot 실패(`:72`)+macro 성공 시 한쪽만 존재하는데 fact-checker(`:81`)는 두 파일 다 읽고 산술②·SSOT충돌④는 snapshot 요구 → 없는 파일 참조 동작 미정의. 가용분만 점검할 가능성 높아 🟢.

### 🟢 G2. 워크스페이스 회전 규칙이 단일 티커 가정 — 다티커 동시 운용과 불일치
`:41` 회전 규칙 `_workspace_prev/{티커}_{날짜}/`는 단일 티커 전제. 실제 `_workspace/`엔 MKIF(7/01) 풀런+`_entry_2026-07-03_{AGNC,MKIF,SOLAI}`(각 indicators/ohlcv만) 공존 — 정의 밖 임시 스테이징. 같은 날 배치 운용 미대응(런타임 잔재라 🟢).

---

## ② 문제없음을 확인한 경로
- **market-data-engineer 3종 산출 계약:** agent def(`market-data-engineer.md:41-42`)가 snapshot+ohlcv+indicators 모두 산출 명시 → technical-analyst(`:99`)·portfolio-risk-analyst(`:28`) 입력 계약 충족.
- **fact-checker 듀얼모드 크로스와이어 없음:** `fact-checker.md:9,15`가 자기 워크스페이스만 읽고 "`_workspace_ipo/`의 어떤 파일도 읽지 않는다" 명시.
- **REVISE 루프 재계산 계약 일치:** portfolio-risk-analyst(`:43` 편입 후만 재계산·보유/변동성 재수집 불필요)가 오케스트레이터 Phase 6 REVISE 루프(`trading-strategy/SKILL.md:147`)와 정합.
- **병렬 격리 vs 파일 전달 무모순:** Phase 2·3R1·5, 공시 D1, IPO Phase 2가 전부 공유 SSOT read-only + 개별 파일 write → write 충돌·격리 위반 없음.
- **IPO Bull/Bear 동시 실패 중단 규칙 존재:** `ipo-analysis/SKILL.md:196`.
- **공시 하네스는 저널 미기록** → F1~F4 무관(reports 스테일만, 학습 코퍼스 오염 없음).

---

## ③ 못 본 것 (미확인 / 한계)
- **reports/ 재복사가 부분 재실행에서 실제 스킵되는지**는 양 오케스트레이터 미명시라 추론(F2). 실행 로그 미확인.
- **risk-debater ×3 호출 model 미지정**(`:135-137`): agent frontmatter 기본값 의존인데 `risk-debater.md` 미독 → 라우팅 실행 가능성 미확인.
- **filings 에이전트 정의**(archivist/auditor/4렌즈) 입출력은 데이터 표만 대조, 각 agent def 원문 미독.
- **`_entry_2026-07-03_*` 생성 주체·용도** 미확인(배치 스크립트 vs 수동).
- F3 실제 발현 빈도는 사용자 습관 의존이라 정량화 불가.
