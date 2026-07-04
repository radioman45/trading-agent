# r4 독립 검증 최종 판정 — 수집 레이어 기계 판정 (2026-07-05)

대상: `_pre-ship/01_target_r4.md` (베이스 52bd300 위 수집 레이어 기계 판정 구현 + 검증 반영분)
프로토콜: 독립 검증 2라운드(글로벌 [HARD]) — 1회차 격리 3렌즈 → 타당성 게이트 → 반영 → 2회차 신규 격리 2렌즈 → 타당성 게이트 → 반영.

## 1회차 (r4-code·r4-wiring·r4-sim — 02_findings_r4-*.md)
⛔0 / 🟡 총 14건(중복 제거) 수용, 기각·변형 3건.

수용 핵심:
- 폴백 견고화: fetch_stooq_daily full 컬럼 검증(+폴백 경로 클린 실패)·sort_index·지표 계산 try 래핑
- --from-csv 시장 미해소 exit 2 (US 디폴트 오판 금지)
- judge_session: 미래 데이터 anomaly 가드, 평일 휴장 intraday_data_gap 신호(SOL 실패 클래스의 잔여 침묵 케이스)
- doctor: v1.1 최상위 세션 허위 WARN 제거, 기계 session 존재 시 schema 라벨 무관 발동(옵트아웃 차단), fail-safe 파싱, session 복사 충실성 대조, 폴백/스킵 상태 가시화
- **DEGRADED_DATA 체인 봉합**: risk-gate ①에 cross_check mismatch 트리거(선언 3곳 존재·부여 게이트 부재였음)
- SKILL/에이전트: 구 최상위 market_session 규율 제거, 블록 전체 복사 명시, 폴백 confidence ≤ medium·fast_info 유실 규정, 세션별 서술 문구에 gap 케이스

기각·변형:
- nasdaq을 폴백 1차로 체인(r4-code 🟡2): **변형 수용** — nasdaq chart는 종가만 제공(21일)이라 지표 원천 불가. 폴백은 Stooq 가용 시에만 동작함을 문서에 정직 명시, 차단 시 클린 실패 → 에이전트 웹 폴백(기존 규정).
- as_of UTC 의미 변경(r4-code 🟡6): **의도 확인 후 유지** — --now-utc 주입 재현성 우선, 주석 명시. doctor freshness와 최대 1일 어긋남은 INFO라 수용.
- from-csv 비숫자 별칭 오판(r4-code 🟢): 1회차엔 관례상 무해로 보류 → 2회차 r4b-regression #4가 실측 반증(KR 데이터 US 오판) → 확신 신호 가드로 수용.

## 2회차 (r4b-regression·r4b-fresh — 02_findings_r4b-*.md)
⛔0 / 🟡 9건 수용(생략 우회 차단·anomaly 분기·indicators 부재 가시화·별칭 가드·PM/fact-checker 입력 배선·mismatch FAIL 승격·단일 소스 라벨 정직화·복사 대조 확장·엣지 문구 규정).

변형 1건: 00_indicators.json fail_if_missing 일괄 추가(r4b-regression #3) → **맥락 인지형으로 변형** — SKILL의 수동 작성 경로(calendar_status:manual)가 문서화된 강등 경로이므로, 자기선언 session=FAIL / manual=WARN / 블록 없음=WARN 3분기.

유지(기각 아님, 관찰 과제):
- market_session 복사 불일치 WARN 등급(스크립트 실행~스냅샷 작성 시각 지연으로 정당 케이스 존재 — 두 검토자 모두 방어 가능 인정)
- 우발 mismatch의 정정 루프 과빈번 위험 — 허용 오차 1%가 흡수(라이브 AAPL diff 0.0%), 실측 관찰 과제
- skipped_error를 별도 검증 모드(UNVERIFIED_SINGLE_SOURCE)로 승격 — risk-gate ① 웹 교차 조건부 DEGRADED로 갈음(현재 dormant)
- 장중 미확정 봉 제외 지표 재계산(스크립트 개선) — 문서 명시 의무로 갈음, 후속 과제

## 기계 테스트 결과 (최종)
- 세션 판정 6케이스(US 4세션+KR 2세션, --now-utc 주입) PASS
- 신규 가드: from-csv 시장 미해소·별칭 exit 2 / 빈 CSV 클린 에러 / 미래 데이터 anomaly PASS
- doctor 합성 9케이스: v1.1 해피패스(허위 WARN 0)·복사 불일치 FAIL·라벨 옵트아웃 FAIL·fail-safe 파싱·생략 우회 FAIL·기계 기준 경고·anomaly FAIL·indicators 부재 3분기·플래그 변조 FAIL·mismatch 미표기 FAIL 전부 기대 일치
- 라이브 AAPL 2회: 수집 OK, session=weekend(7/5 일요일), cross_check=match(secondary=nasdaq — Stooq는 안티봇 차단 실측)
- 3하네스 회귀: trading FAIL 2(구 실행분 기존 True Positive 그대로)·ipo WARN 1·filings GREEN — 기준선과 동일, 회귀 0

## 최종: 커밋 승인
2라운드 요건 충족. 2회 반복 후 잔여 지적 전건 반영 또는 근거 있는 유지 판정.
