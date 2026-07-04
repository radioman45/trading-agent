# 검토자: critic-wiring (격리 critic, opus) — 1회차

**렌즈:** trading-strategy 오케스트레이터 배선 정합성
**판정: ACCEPT-WITH-RESERVATIONS. 🔴 0 · 🟡 2 · 🟢 1**

## 발견 결함
- 🟡-1 **REVISE 루프가 portfolio-risk-analyst를 재호출하지 않음 → 05_portfolio_impact.md 스테일 (내적 모순)**
  - trading-strategy/SKILL.md:147 REVISE는 "트레이더 또는 리서치 매니저"만 재호출. risk-gate/SKILL.md:71 동일.
  - portfolio-risk-analyst.md:43은 "REVISE 루프에서 비중이 바뀌면 편입 후 스냅샷만 재계산"으로 자신의 재호출을 전제 — 트리거하는 오케스트레이터 스텝 부재.
  - risk-gate/SKILL.md:58 PM 재점검은 05_portfolio_impact.md의 편입 후 수치를 읽는데 재계산 안 됨. 테스트 시나리오(trading-strategy:251)가 명세대로 실행 불가.
  - 스테일 방향이 보수적(더 큰 포지션 기준)이라 치명은 아님.
  - 권고: SKILL.md:147와 risk-gate:71에 "트레이더가 비중 수정 시 portfolio-risk-analyst 경량 재계산 1회 재호출" 추가.
- 🟡-2 **Phase 7 reports/ 복사 목록에 05_portfolio_impact.md 누락** (trading-strategy/SKILL.md:151) — PM 게이트 1차 입력이 딜리버러블에서 빠짐. 권고: `포트폴리오영향_{회사}.md` 추가 (00_factcheck는 🟢 수준).
- 🟢-3 **파일 번호 07/08 역전**: 08_plain_explanation(step 4, :156)이 07_podcast_script(step 5, :168)보다 먼저 생성. 기능 무해.

## 문제없음 확인
- 참조 실재성 100%: subagent 17종·스킬 13종·collect_market_data.py·decisions/ 5파일 실존.
- fact-checker 모드 2 배선: fact-checker.md:11-22 ↔ Phase 1.6(SKILL.md:80-86) 입출력 정확 일치, 모드 분기 명시.
- Phase 5 병렬 4개 출력 경로 삼자 일치. Phase 0 모드표 7종 ↔ Phase 1~7·R·S·M·P 일대일. 고아/유령 파일 없음. decisions/ 커밋 배선 완비.

## 미확인
- 방향 REVISE(리서치 매니저 재호출) 시 하류 재실행 연쇄가 "부분 재실행 의존성"(SKILL.md:43)으로 충분한지 — 명시 모순은 없음.
- 포트폴리오 레이어가 실제 실행으로 검증된 적 있는지(현 _workspace/에 05_portfolio_impact.md 부재 — 런타임 상태).
