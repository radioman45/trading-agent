# 검토자: critic-numbers (격리 critic, opus) — 1회차

**렌즈:** 사이징·리스크 산식 정합성 (정량 리스크)
**판정: ACCEPT-WITH-RESERVATIONS. 🔴 0 · 🟡 2 · 🟢 3**

## 발견 결함
- 🟡-1 **trading-strategy 워크드 예시가 "동시 꼬리 손실(집계, 한도 10%)"에 "캠페인 한도 2%"를 잘못 적용**
  - trading-strategy/SKILL.md:251 "동시 꼬리 손실 계좌 -3.1% (캠페인 한도 2% 초과) 🚩" — 그러나 집계 한도는 10%(portfolio-risk/SKILL.md:68,82; portfolio-risk-analyst.md:20), 2%는 신규 캠페인 단독 꼬리 검산 한도(trade-planning:27). -3.1%는 산술상 단일 캠페인 값(35%×8.9%)인데 라벨은 집계·한도는 단독으로 뒤섞임.
  - 권고: "신규 캠페인 꼬리 검산 -3.1%(한도 2% 초과)"로 라벨 정정 또는 집계 시나리오로 값·한도 재작성.
- 🟡-2 **IPO 확신도 앵커(공모가 대비/방향 적중) ↔ 공용 calibration.md 채점(벤치마크 알파 부호) 사건 불일치**
  - 트레이딩 앵커 "12개월 내 벤치마크 대비 초과수익 확률"(research-manager.md:23, risk-gate:102) vs IPO 앵커 "공모가 대비"·"방향이 맞을 주관 확률"(investment-judge:41,69; report-schema.md:59,110). calibration.md:3 채점은 벤치마크 알파 부호 단일 규칙, ipo-reflection:39도 알파 채점 → IPO 행은 p와 o의 사건이 달라 Brier가 사과-오렌지.
  - 권고: (i) IPO 앵커를 벤치마크 상대로 통일 또는 (ii) calibration.md에 하네스별 채점 기준 분리 명시.
- 🟢-1 사이징 산식 분모 0 가드 명시 부재(1.5 ATR 규율로 암묵 방지; ATR=0 경계 미보증) — trade-planning:26,27,37. 권고: "분모>0" 구속 한 줄.
- 🟢-2 research-debate/SKILL.md:83 예시 "6~12개월" vs 표준 앵커 "12개월" 지평 드리프트. 권고: "12개월"로 정렬.
- 🟢-3 calibration.md:7 열 라벨 `확신도(p)`/`결과(o: 1/0.5/0)` vs ipo-reflection:43 서술 표기 미세 차이(구조 동일, 파싱 무해).

## 문제없음 확인 (요지)
- 이중 게이트 = min(R식, 꼬리식, 성향 상한) + 구속 게이트 명시(trade-planning:28,33) — 무모순, 숫자 검산 통과.
- 계좌 2% 한도·비대칭비 1.5·비중 상한(공통 5/10/15 → IPO 3/7/15)·동시 꼬리 10%: 전 파일 일관.
- portfolio.json 스키마 ↔ portfolio-risk 스킬·analyst 선언 완전 일치. 보유 0 = 강등 모드 처리 실재.
- 기회비용 게이트: 생산(research-manager:24, trading-strategy:122)→소비(portfolio-manager:22, risk-gate:63)→기록(risk-gate:107) 폐루프.
- contrarian-check 방향 중립(:57-62) 정합.

## 미확인
- barbell-correlation.md·docs/neurofusion/method_portfolio_risk.md 원문(상관 0.8/0.5/0.2·RC 산식의 원천 정합).
- 관망(HOLD)을 알파 부호로 채점하는 규칙의 세부 정합(🟡-2와 인접).
