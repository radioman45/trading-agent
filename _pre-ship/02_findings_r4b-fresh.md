# r4 독립 검증 2회차 — 신선한 전체 렌즈 (r4b-fresh, critic 신규 격리)

판정: REVISE (CRITICAL 0 / MAJOR 3 / MINOR 4 + 공백 2). 코어 로직(세션·교차·가드)은 6흐름 실행 실증으로 견고, 하위 호환·타 하네스 무해(렌즈 C 정합), CLAUDE.md 이력 행 정확(렌즈 D 정합). 결함은 전부 레이어 간 배선.

## MAJOR
- **A-1. mismatch→DEGRADED_DATA 체인에 강제력 없음**: risk-gate ①은 cross_check mismatch를 트리거로 선언하는데 판정자(PM)에게 아무도 00_indicators.json을 안 줌(Phase 6 프롬프트·portfolio-manager.md 입력 목록 누락). doctor 보완 검사는 WARN이라 Phase 7 정정 루프(FAIL만 강제) 미발동 → mismatch 시 FULLY_VERIFIED로 남는 soft continuation 재현.
- **A-2. 최고 신호 플래그(stale_feed_suspect·intraday_data_gap) 복사 충실성 미강제**: 복사 대조가 3필드뿐 — 기계 true 플래그를 스냅샷이 누락하면 machine 레이어 완전 침묵(합성 Case C). [주: 검토 시점이 r4b-regression 반영 전 스냅샷 — 생략 우회는 반영으로 기봉합, 값 변조 케이스만 잔여였음]
- **A-3. 읽기 목록 스테일**: Phase 1.6 fact-checker 읽기 목록에도 00_indicators.json 부재(점검축 ⑤가 참조하는데).

## MINOR
market_session 복사 불일치 WARN(시각 지연으로 정당 — 설계 선택 인정) / requested_at_utc 복사 대조 없음 / last_close_is_final=None(anomaly) 시 가격 서술 문구 미규정 / 수동 폴백 시 requested_at_utc 누락 위험.

## 공백
- 단일 소스 경로(skipped_primary_is_fallback·skipped_error)가 FULLY_VERIFIED로 라벨 가능(이중 교차 미수행인데 "완전 검증").
- 장중(final=false) 미확정 봉으로 기술지표 전체 산출되나 경고 없음.

## 반영 (메인 세션 타당성 게이트)
- A-1 수용: Phase 6 프롬프트·portfolio-manager.md 입력에 00_indicators.json 배선 + doctor mismatch-without-DEGRADED WARN→**FAIL** 승격(risk-gate 하드룰과 정합, 정정 루프 발동) + Phase 7 ⓑ에 검증 모드 미스라벨 포함·load-bearing 재점검 연동.
- A-2 수용(잔여분): 복사 대조 목록에 stale_feed_suspect·intraday_data_gap FAIL 추가(+requested_at_utc WARN — MINOR 동시 해소). 생략 우회는 r4b-regression 반영으로 기봉합.
- A-3 수용: Phase 1.6 읽기 목록에 00_indicators.json 추가.
- 공백 1 수용: risk-gate ①에 "cross_check 미수행 + 스냅샷 웹 교차 기록 없음 → DEGRADED_DATA"(단일 소스 미검증을 완전 검증으로 표기 금지).
- 공백 2 수용(문서): SKILL 서술 규칙에 final=false 시 기술지표 미확정 봉 포함 명시 의무 + None 시 가격 서술 금지.
- MINOR 4 수용: SKILL 수동 작성 필수 3키 명시. / market_session WARN 유지(검토자도 방어 가능 인정).
- Open question(우발 mismatch의 정정 루프 과빈번)은 허용 오차 1%가 흡수 — 관찰 과제로 유지.
