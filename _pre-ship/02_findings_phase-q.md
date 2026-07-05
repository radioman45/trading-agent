# Phase Q(포트폴리오 점검 모드) 독립 검증 — 2라운드 기록 (2026-07-05)

대상: Phase Q 신설 6파일(trading-strategy·portfolio-risk·risk-gate 스킬, portfolio-manager·portfolio-risk-analyst 에이전트, collect_market_data.py) + 보유 등록(4e35433) 위 워킹트리. 프로토콜: 격리 다관점 → 메인 세션 타당성 게이트 → 반영, 2회 반복.

## 1회차 (격리 2렌즈 병렬)

**q1-wiring (배선·정의 정합, critic):** REQUEST CHANGES — MAJOR 1·🟢 3.
**q1-ops (운영 드라이런 — 실보유 데이터, critic):** REVISE — MAJOR 3·minor 5·gap 3. 3+ MAJOR로 ADVERSARIAL 격상.

수용·반영 (전 인용처 메인 재검증 후):
- **M1 (ops, 실증):** 한국 신형 영숫자 코드 `0167A0`(2대 보유 SOL ETF 18.7%)가 detect_market/fetch_ohlcv에서 US 오분류 → 수집 실패. → 스크립트에 `is_kr_new_code`(6자 영숫자·숫자 시작·알파벳 포함 → KR) 신설, 3지점(감지·OHLCV `.KS/.KQ` 접미사·from-csv 가드) 배선 + Phase Q step 2에 접미사/`--market KR` 재시도 힌트. **기계 테스트:** 감지 매트릭스 20케이스 PASS(US 클래스·크립토·선물 오탐 0), 라이브 0167A0(자동 `.KS` 해소·KR 세션·skipped_kr)·AAPL 회귀(US·cross match) PASS.
- **M3 (wiring MAJOR-1 = ops M3, 독립 이중 발견):** 저널 "포트폴리오 점검" 항목이 `결과: (미기록`을 가지면 Phase 1 pending 결산(티커 단위 스크립트 결산)·Phase M sweep이 티커 없는 항목을 오수집 — NVDA·MKIF·MU에서 봉합한 이중 계상과 동일 클래스. → 삼중 방어: risk-gate 저널 포맷에 "포트폴리오 점검 항목 규칙"(티커 없는 헤더 + `실행:`/`결과:` 줄 금지) + PM 모드 3 명문화 + Phase 1·Phase M sweep 제외 가드 + journal.md 서문 예외 1줄.
- **M2 (ops):** Q-2가 티커별 수집한 지표·OHLCV가 PRA에 미배선(전 종목 σ가 [추정] 대표치로 강등될 위험) → Phase Q step 4 프롬프트·PRA 모드 2 입력·portfolio-risk 스킬에 `_portfolio/{티커}/00_indicators.json` 실측 경로 명시.
- minor: FX 소싱(웹 `KRW=X`), 시세 폴백 우선순위 3단계 고정, `PRICE_STALE`(종목)/`PORTFOLIO_STALE`(북) 명명 분리, 현금 절대액 재정규화 규칙, 스키마 `shares` 문서화, 라우팅 near-miss 스코핑("전체 비중 조정", "내 포트폴리오 봐줘" 추가).

관찰 유지(비차단): 레짐 기준일 표준 필드(m4 — LLM 파싱 feasible 실증), 동일 날짜 reports 덮어쓰기, `_workspace/_portfolio/` 정리 주체, macro_drivers 의미 그룹핑은 LLM 판단 의존.

## 2회차 (신규 격리 1렌즈 — 수정 정합 + 신선한 눈)

**q2-fresh (critic):** REQUEST CHANGES 조건부 — MAJOR 2·🟢 3. 1회차 반영분 자체의 회귀는 0 확인(sweep 가드-리터럴 매칭 정합, 3파일 규칙 4곳 무모순, is_kr_new_code 29케이스 오탐 0).

수용·반영:
- **M-1 (게이팅):** Phase Q 재평가가 `shares`·`valuation`에 하드 의존하나 Phase P 인터뷰·스키마가 보장하지 않음(미래 weight-only 등록 시 재평가 불가·무폴백) → ⓐ Phase P 인터뷰를 주수 우선 수집 + valuation 블록 기록으로 갱신 ⓑ Phase Q 에러 절에 shares 부재 폴백(등록 비중 + PRICE_STALE, PRICE_STALE 합 >30%면 북 PORTFOLIO_STALE 강등·재등록 권고) ⓒ 스키마 "둘 수 있다" → "Phase Q 사용 시 사실상 필수" 승격.
- 🟢: journal.md 서문에 점검 항목 예외 1줄, 스키마 예시 티커 MKIF→088980 정합.

**백로그(수용하되 이번 미구현 — 정직 기재):** M-2 harness_doctor에 Phase Q 검사 경로(`10_portfolio_scan` 존재·모드 라벨 vs as_of 정합·비중 합 검산) 부재 — PRA→PM 생성-검증 분리와 산술 자가검산 의무는 존재하나 기계 결정성 없음. 2026-07-04 기계 검증 원칙과의 간격으로 기록, 차기 doctor 확장 시 최우선.

기록만: is_kr_new_code 이론 오탐 표면(`12345A`류 — 실존 미국 티커 없음), Phase Q 쉬운해설 미생성(경량 진단 설계 — 제품 판단), "리밸런싱 권고" 라벨의 실행 지시 오독 여지(3중 방어 확인 — 회부 원칙·판단 금지·보고 안내).

## 종합
2라운드 완료. 게이팅 결함 전부 봉합(M1 기계 실증, M3 삼중 방어, M2 배선, 2회차 M-1 생산-소비 정합). 잔여는 M-2 doctor 백로그와 관찰 항목. 반영 완료 표기 항목의 재반영 금지.
