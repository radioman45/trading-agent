# r4 독립 검증 1회차 — 실행 시뮬레이션 렌즈 (r4-sim, critic 격리)

판정: REVISE (CRITICAL 0 / MAJOR 5 / MINOR 3). 코드는 기계적으로 건전(DST·세션 수학·주말·정상 평일·하네스 격리 클린), 그러나 강제 레이어가 해피패스에서 자기모순.

## 시나리오 판정
A(정상 미국)=정합(단 발견1 거짓 WARN 동반) / B(mismatch)=결함(발견2) / C(Stooq 폴백)=결함(발견3) / D(주말)=정합·평일 휴장=결함(발견5) / E(한국)=정합(비대칭은 어드바이저리) / F(--from-csv)=결함(발견4) / G(IPO·filings)=정합(신규 코드 전량 check_trading_snapshot 격리, 회귀 없음)

## MAJOR
1. **모든 정상 v1.1 스냅샷에서 최상위 market_session 거짓 WARN** (doctor:130-132 vs v1.1 중첩 이전; 실행 재현). SKILL에 세션 지시 2개 공존(기존 HARD 최상위 자유형식 vs 신규 블록 복사). 처방: v1.1이면 session.market_session 인정 + SKILL 구 문구 삭제. [r4-wiring 🟡1·🟡3과 동일]
2. **mismatch→DEGRADED_DATA 강제 고리 끊김** — risk-gate:56(검증 모드 부여 유일 게이트)은 factcheck "미확인"만 트리거. 규율대로 confidence=medium 처리하면 FULLY_VERIFIED인데 doctor는 영구 WARN. 처방: risk-gate ①에 mismatch 트리거 추가(또는 fact-checker ⑤가 미해소 mismatch를 "미확인" 등가 승격). [r4-wiring 🟡2와 동일]
3. **skipped_primary_is_fallback = 가장 미검증인데 가장 조용** — doctor 분기 없음(INFO조차), 폴백 단일 소스 confidence 강등 규칙 없음, fast_info={} 무언 유실(시총·주식수 1차 후보 소멸). 처방: doctor WARN 분기 + 폴백 confidence ≤ medium 규칙 + fast_info 유실 명시.
4. **--from-csv에서 --market·--ticker 생략 시 KR을 US 세션으로 조용히 오판** (collect:428 detect_market 디폴트 US; SKILL 자체 예시 :30이 --market 생략). 처방: 시장 미해소 시 exit 2 또는 market_unresolved 기록(US 디폴트 금지), SKILL 예시에 --market.
5. **평일 휴장 장중 실행: session="regular" 오라벨 + suspect 무발화** — Memorial Day 월 장중: expected=금, last=금 ⇒ suspect=False, 문구 규칙은 금요일 확정 종가를 "장중 지연 시세—종가 아님"으로 오라벨(final=true와 정면 모순). 트리거 창 좁고 부분 자기힌트나 조용+SOL 실패 클래스라 MAJOR 유지. 처방: regular인데 오늘 봉 없음이면 별도 suspect 신호.

## MINOR
- schema_version 강제 승격 없음 — "1.0"으로 두면 doctor·Phase1.6 ⑤ 모두 무언 no-op(옵트아웃). [r4-code 🟡4와 동일 뿌리]
- 스냅샷 session 예시가 expected_last_trading_date 누락(11필드 중 8필드 — "그대로 복사"와 모호).
- 부분 재실행 시 snapshot.session vs indicators.session 불일치 무가드.

## 공백
단일소스 폴백 강등 규칙 부재 / cross_check 스킵 상태 4종 doctor 무출력(감사 가시성) / 트레이딩 v1.1 강제 가드 없음 / doctor가 스냅샷 측 mismatch 기록(conflicts·강등) 미검사 / KR 교차는 명예제도(US와 비대칭, 회귀는 아님).

## Open Questions
mismatch를 "미확인" 등가로 승격 vs 별도 DEGRADED 트리거 / 스킵 상태 INFO 여부 / indicators.session 11필드 권위본 vs 스냅샷 8필드.
