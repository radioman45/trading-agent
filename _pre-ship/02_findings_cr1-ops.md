# CRYPTO 모드 독립 검증 1회차 — 배선·운영 시뮬레이션 렌즈 (cr1-ops, critic 격리)

판정: REQUEST CHANGES 조건부 (⛔0 / 🟡2 / 🟢5 + Open 3). BTC-USD 풀 파이프라인(Phase 0→7)을 정의 파일만으로 드라이런. cr1-code와 중복 0. 핵심 패턴: 크립토 문구가 수집 레이어 4파일 + 오케스트레이터 프롬프트에서 멈추고, L4 트레이더·L5 리스크/포트폴리오·복기·분석가 참조에는 0건 — 하류가 주식 전제를 상속. 메인 세션이 전 인용처(trade-planning:50-54, trader:16·27, fundamental.md:31-42, technical.md, risk-gate:22·26·56, barbell-correlation:31·40, portfolio-risk:31, data-sources:18-25, market-data-engineer:14, trading-strategy:57·85·89·103, sentiment.md, 00_input 스키마)를 직접 재확인 — 전부 실재. 타당성 게이트 통과.

## 🟡 (수용·반영 완료)
- **M1**: 거래계획 비용/세제 의무 섹션이 미국/한국 이진 분기 — 크립토에 주식 양도세 22%를 강제할 구조 → trade-planning §2 크립토 항(가상자산 과세 시행 확인 의무·거래 경로별 수수료·24/7 유동성 갭·ETF면 미국 기준) + trader.md 규율·시작 행동(매매 수단 확인) + 00_input.md 스키마에 "(크립토면) 매매 수단" 필드(Open2 함께 봉합) 반영.
- **M2**: FA 크립토 렌즈가 오케스트레이터 프롬프트에만 존재, fundamental.md 레드플래그 의무(전부 재무제표)와 충돌 → fundamental.md에 "크립토 자산 특칙" 섹션 정식 편입(재무 3표·레드플래그 미적용 명시 + 공급/온체인/수급/규제 4축 의무 대체 + MVRV류 밸류 앵커 + 데이터 소스) 반영.

## 🟢 (m3~m6 수용·반영 / m7 관찰 유지)
- **m3**: 미확정봉 고지 의무(market-snapshot:133)가 technical 소비자에 미배선(크립토 상시 발동) → technical.md 입력 절에 session.last_close_is_final 줄 + Phase 2 technical 프롬프트에 고지 지시 반영.
- **m4**: 바벨 다리 태깅에 크립토 슬롯 없음 → risk-gate 축⑦·barbell-correlation §4·portfolio-risk barbell_leg에 "크립토 = 공격 다리(위기 상관 수렴 — '디지털 골드=방어' 프레이밍 금지)" + macro_drivers 예시 반영.
- **m5**: DEGRADED_DATA 트리거 열거에 skipped_crypto_quote·skipped_kr 누락 → risk-gate Part B 열거 확장(웹 교차 기록 있으면 비강등 조건 유지) + Phase 1.6 축⑤에 동일 점검 반영.
- **m6**: data-sources.md 감지표 크립토 행 부재(SKILL.md:35 주장과 불일치)·market-data-engineer:14 "미국/한국" 스테일 → 감지표 크립토 행 + 크립토 소스 요약 + 서술 갱신 반영.
- **m7 (관찰 유지)**: sentiment.md 크립토 심리 지표(펀딩비·미결제약정) 미언급, glossary.md 크립토 용어 미수록 — 우아한 열화(검토자 판정)·승인 조건 밖. 첫 크립토 실전 실행에서 실제 열화 관찰 시 보강.

## Open (1 반영 / 2 봉합 / 3 관찰)
- **Open1**: Phase 1.6 축① "미개장/장중" 주식 용어가 크립토 always_open을 거짓양성 ⛔할 위험(MEDIUM) → 축①에 크립토 정상 상태 명시(당일 UTC 봉 상시 미확정 = 정상, ⛔ 대상은 직전 UTC 마감 봉과 모순되는 서술) 반영. 실측 1회 확인은 첫 크립토 실전 실행에서.
- **Open2**: 매매 수단이 스냅샷 market 필드로만 간접 전달 → M1의 00_input.md 필드 신설로 봉합.
- **Open3**: news/sentiment의 크립토 소스 실커버리지 — 런타임 관찰 과제.

## 긍정 관찰 (검토자)
사이징 산식 자기 스케일링(변동성 조정 상한이 크립토 고변동에서 올바르게 축소 — 주식 상수 오작동 없음), 벤치마크 체인 정합(스냅샷 BTC=S&P500 → 복기 알파 → calibration 앵커 무모순), doctor 크립토 경로 게이밍 불가, SINGLE_TRADE_ONLY 강등 정상, macro 레이어 크립토 분기 불요.

## 비고
- 이 파일로 **1회차 완결**(cr1-code + cr1-ops). **2회차는 사용자 결정으로 생략** — 잔여 위험은 m7·Open3(런타임 관찰)과 첫 크립토 실전 실행(풀 파이프라인 실증, 사용자 "다음에" 결정)으로 이관.
- 반영 완료 표기된 항목의 재반영 금지.
