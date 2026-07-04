# r4 독립 검증 1회차 — 코드 정확성 렌즈 (r4-code, code-reviewer 격리)

대상: collect_market_data.py(+257)·harness_doctor.py(+43), 베이스 52bd300 워킹트리
방법: diff·전체 정독 + 실제 실행 검증(세션 12케이스, doctor 6케이스, Stooq/Nasdaq 라이브, py_compile)
총평: ⛔치명 확정 없음. 🟡경고 6건(그중 3건이 "조용히 틀린 데이터/크래시" 위험), 🟢사소 3건. 권장 REQUEST CHANGES(차단 근거 경고 1·4).

## 🟡경고 1 — Stooq 폴백이 compute_indicators 크래시 유발, try 밖이라 클린 에러 JSON 미출력 (확신 HIGH)
- fetch_stooq_daily(collect:147-157)는 Close 존재만 검증, High/Low/Volume 미검증.
- compute_indicators(df) 호출(:445)은 수집 try/except(402-426) 바깥. df["Volume"]·["High"]·["Low"] 무조건 참조(277-279).
- 실패 시나리오: Stooq가 Volume 없는 CSV 반환 → KeyError('Volume') 미포착 트레이스백(exit 1, status:error JSON 없음) → 에이전트 stdout 파싱 실패. Volume 없는 60행 df로 KeyError 재현됨.
- 권장: fetch_stooq_daily에서 {Open,High,Low,Close,Volume} 필수 컬럼 검증(폴백이 except 안에서 클린 실패), 또는 compute_indicators를 try로 감싸기.

## 🟡경고 2 — 폴백-1차 경로에 nasdaq 폴백 부재 → 현재 Stooq 안티봇 차단 하에서 죽은 경로 (확신 HIGH)
- cross_check는 stooq→nasdaq 체인(:203-204)인데 yfinance 실패 폴백-1차(:418)는 stooq만.
- 실측: 현재 Stooq .us 일봉 CSV는 안티봇 JS 챌린지(HTML) 반환 → 가드 발동 → US 티커 yfinance 실패 시 폴백 전체 하드 실패. Nasdaq chart API는 정상(AAPL 13행, 오름차순, close/volume) 실측.
- 권장: 폴백-1차에도 stooq→nasdaq 체인 적용.

## 🟡경고 3 — Stooq 폴백 df sort_index 부재 → 정렬 뒤집히면 조용히 틀린 last_close (확신 MEDIUM, 추정)
- set_index("Date")만 하고 정렬 안 함(:157). 순서 의존적 compute_indicators(.iloc[-1], rolling)로 직접 유입.
- 내림차순 반환 시 last_close·전 지표가 가장 오래된 봉을 조용히 반영 — SOL 날조와 동일 실패 클래스. 교차검증 경로는 common.max()라 무관, 폴백-1차만 취약.
- 권장: fetch_stooq_daily 끝 .sort_index() 한 줄.

## 🟡경고 4 — doctor session 강제가 LLM 작성 필드 schema_version에 종속 → 미탐 + fail-open (확신 HIGH)
- harness_doctor:137-141 ver>=(1,1)일 때만 발동. schema_version은 LLM이 스냅샷에 쓰는 값.
- 실측 C: session 부분/오복사 + schema_version "1.0" → 무지적. 실측 F: "v1.1" 파싱 불가 → ValueError → (1,0) → 조용히 무력화(fail-open).
- 권장: session 키 존재 시 버전 무관 완전성 검사, 파싱 실패는 fail-safe.

## 🟡경고 5 — judge_session: last_data_date 미래 미가드 → 음수 staleness + 잘못된 final=false (확신 HIGH, 영향 제한적)
- 실측: --now-utc 2020-01-02 + 2026 데이터 → staleness=-2373, final=False. 프로덕션은 안전, 과거 시각 주입 테스트 시 무의미 값.
- 권장: last_data_date > local_date면 clamp/플래그.

## 🟡경고 6 — as_of 의미 변경: machine-local → UTC (확신 HIGH, 영향 작음)
- :254→255 date.today() → now_utc.date(). KST 저녁 실행 시 as_of 하루 이름. doctor freshness(:197)는 여전히 machine-local 비교 → 최대 1일 어긋남(INFO라 영향 작음). 의도 확인 권장.

## 🟢사소
- from-csv + 비숫자 한국 티커 별칭("MKIF")은 US로 오판해 US 타임존 세션 판정 — 세션 라벨만 영향, 관례상 무해.
- DST 경계 근사(전환일 ±수 시간) — calendar_status:approx로 정직 표기, 수용 가능.
- cross_check p=0 → mismatch — 방어적으로 타당.

## 긍정 관찰
- _round의 NaN/inf→None 일관 처리(JSON NaN 누출 없음), 세션 12케이스 실측 통과(장중 final=False 정확), Stooq 안티봇 가드 정확 포착, _close_by_date tz 정규화+common.max() 강건(Nasdaq match 실측), --now-utc 오류 클린 exit 2, doctor cross_check 검사가 LLM 복사본 아닌 indicators.json 직독(강건).
