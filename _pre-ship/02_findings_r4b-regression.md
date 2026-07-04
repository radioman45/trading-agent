# r4 독립 검증 2회차 — 수정 회귀 렌즈 (r4b-regression, code-reviewer 신규 격리)

판정: REQUEST CHANGES (⛔0 / 🟡4 / 🟢1). 전부 실행 검증(crafted 워크스페이스 실측).

## 🟡경고
1. **doctor가 collector의 anomaly 신호 무시** — 미래 데이터(anomaly 존재)가 "session 블록 OK"로 통과(실측 Scenario C). 수정: anomaly 분기 추가.
2. **반-SOL 경고(.final/.stale/.gap)가 기계값이 아닌 LLM 스냅샷(sess) 기반** — LLM이 필드 생략 시 경고 미발동+복사검사 스킵+필수 3종에도 없음 → 무경고 통과(실측 Scenario B). bool vs 문자열 변조는 정상 검출(D). 수정: 경고를 ind_sess 기준 발동 + 기계값 non-null 신선도 필드 생략 시 FAIL.
3. **00_indicators.json 부재가 기계 레이어 전체를 조용히 비활성화** — 복사 충실성·cross_check 검사 전부 스킵 + 부재 자체가 FAIL 아님(실측 Scenario E). 수정: 부재 가시화(자기선언 session은 FAIL).
4. **--from-csv 가드 구멍** — 비확신 별칭(--ticker samsung)이 US 디폴트 우회 통과(실측 F5b: KR 데이터가 US 세션으로 오판). 수정: 확신 신호 없으면 --market 요구.

## 🟢사소
5. 빈 --from-csv가 try 밖 IndexError(클린 JSON 계약 위반, 회귀 아님). 수정: df.empty 가드.

## 정상 확인
fetch_stooq full/폴백·sort_index·cross_check 분기·tz 교집합·judge_session 9시나리오·doctor 분기 순서·--now-utc 처리 전부 정상.

## 반영 (메인 세션 타당성 게이트 통과 → 전건 수용)
- #1: doctor session 검사에 anomaly FAIL 분기 (+ 복사 생략 목록에 anomaly 포함)
- #2: 신선도 경고를 기계값(ind_sess) 우선 발동 + 기계 non-null 신선도 필드(final/stale/gap/anomaly) 스냅샷 생략 시 FAIL
- #3: 부재/파싱 불가 가시화 3분기 — 자기선언 session FAIL / calendar_status:manual WARN(문서화된 강등 경로 존중 — fail_if_missing 일괄 추가 대신 맥락 인지형으로 변형 수용) / 둘 다 없으면 WARN
- #4: --from-csv에서 --market 미지정 시 확신 신호(KR: .KS/.KQ/6자리, US: 1~5자 알파벳) 없으면 exit 2
- #5: df.empty 가드(클린 에러 JSON)
- 전건 합성 테스트로 발동 실증 + 3하네스 회귀 무변화 확인
