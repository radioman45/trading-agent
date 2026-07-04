# r4 독립 검증 1회차 — 배선 정합 렌즈 (r4-wiring, critic 격리)

결론: 🟡경고 3건 + 🟢사소 2건 (⛔치명 0건). session/cross_check 키·값 집합 자체는 레이어 간 정합. 실질 모순 3건.

## 🟡경고 1 — doctor top-level market_session 검사 ↔ v1.1 nested session 미화해 → 정상 v1.1 스냅샷마다 허위 WARN + 자기모순 (HIGH)
- harness_doctor:130-134가 최상위 market_session을 검사하는데 v1.1 예시 JSON에는 최상위가 없고 session.market_session만 있음.
- 규격을 지킨 v1.1 스냅샷은 snapshot:market_session=WARN과 snapshot:session=OK를 동시에 냄. :136 주석("구 1.0 실행분은 위 WARN 유지")의 가정이 오해.
- 권장: top-level 검사를 ver<(1,1)로 게이팅하거나 nested 폴백 추가.

## 🟡경고 2 — mismatch→confidence 강등→DEGRADED_DATA 체인의 마지막 링크가 risk-gate에 부재 → mismatch 실행마다 doctor 영구 WARN (HIGH)
- 새 규정 3곳(market-snapshot:27, market-data-engineer 규율5, doctor:211)이 mismatch→medium→DEGRADED_DATA 대상 선언.
- 검증 모드를 실제 부여하는 유일한 게이트 risk-gate Part B ①(:56)은 "00_factcheck.md에 '미확인' 강등" 트리거만 규정 — cross_check·medium 언급 0건.
- 규정을 완벽히 따라도: conflicts 기록+medium 강등 → Phase 1.6 ⑤ 통과 → factcheck '미확인' 없음 → FULLY_VERIFIED → doctor WARN 상시 발화.
- 권장: risk-gate ①에 트리거 추가 — "00_indicators.json cross_check가 mismatch면 DEGRADED_DATA".

## 🟡경고 3 — market-snapshot SKILL:8 구 HARD 규율이 top-level 자유형식 market_session을 계속 지시 (경고1과 한 뿌리)
- :8 "스냅샷에 market_session 필드(예 "KR 개장 전"/"마감")를 남긴다" ↔ nested enum 규정(:10/:26/예시)·:127 서술 문구 enum 키잉과 미화해 공존. 어느 해석이든 한 레이어와 불일치.
- 권장: :8 해당 절을 session 블록(기계 판정 enum)으로 대체 서술.

## 🟢사소 1 — 에이전트 규율4 필드 열거에 requested_at_utc 누락 (doctor 필수 3키와 불일치)
- 수동 작성 경로(스크립트 전체 실패)에서 이 열거를 필수 목록으로 읽으면 doctor FAIL. 권장: 열거에 포함 또는 "블록 전체" 명시.

## 🟢사소 2 — "기계값 그대로 복사 [HARD]"가 존재만 검사되고 동일성 미검사
- doctor가 snapshot.session ↔ indicators.session 일치 미대조(이미 indicators.json 로드 중이라 저비용). 3키만 갖춘 날조 session 블록이 통과. schema_version "1.0" 표기로 검사 전체 우회 가능(r4-code 🟡4와 동일 뿌리).
- 권장(선택): 동일성 대조 추가.

## 정합 확인된 항목
- 스크립트 산출 키/값 ↔ 문서 참조 정합, 하위 호환 OK(1.0 부당 FAIL 없음, cross_check 키 없으면 조용히 스킵), cross_check 검사는 trading 전용(IPO/filings 누수 없음), CLAUDE.md 이력 행 서술 일치, Phase 1.6 ⑤ ↔ doctor 정합.

미확인: v1.1에서 최상위 market_session 병기 의도 여부 — 어느 쪽이든 한 파일은 수정 대상.
