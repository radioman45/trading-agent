# CRYPTO 모드 독립 검증 1회차 — 코드 정확성 렌즈 (cr1-code, code-reviewer 격리)

판정: REQUEST CHANGES 조건부 (⛔0 / 🟡2 / 🟢4 + Open 1). 해피패스(BTC/ETH/SOL-USD·현물 ETF)는 정확·회귀 0. 분류기 35케이스·UTC 경계·API 가드 실행 검증.

## 🟡 (수용·반영 완료)
- **F1**: is_crypto_symbol의 base.isalpha()가 숫자 포함 토큰(1INCH-USD 등)을 US로 침묵 오분류 → base 영숫자 허용(+최소 1알파벳) 반영.
- **F2**: CRYPTO_QUOTES에 GBP/AUD/CAD/CHF/CNY/HKD/SGD 부재 → BTC-GBP 등이 US로 침묵 오분류 → 집합 확장 반영. (US 클래스 표기는 쿼트 1자라 무충돌 — 검토자 35케이스 + 메인 12케이스 재검증 PASS)

## 🟢 (F3 수용·반영 / F4·F5 관찰 유지)
- **F3**: USDT 쿼트 티커의 coinbase 조회가 풀심볼이라 죽은 다리(Coinbase USDT 페어 미상장) → {base}-USD로 조회(coinbase(USD 근사) 라벨) 반영.
- **F4**: binance 지역 차단(451) 가능성 — 실패 시 skipped_error 강등으로 정직 처리(비차단), 유지.
- **F5**: 크립토 교차가 당일 진행 봉끼리 비교 — 순간 변동 >1%면 mismatch 오탐 가능하나 허용 오차가 흡수(실측 0.014%), 설계 수용.
- **Open**: yfinance 크립토 인덱스 tz 가정(UTC) — 현 환경 실측 정합, 버전 이관 시 재확인 과제.

## 긍정 관찰
CRYPTO/US/KR 세션 키 집합 완전 동일(하류·doctor 무충돌), 대시-클래스 US 티커 오탐 0(BRK-A/B 등 11종), UTC 자정 경계 정확(23:59/00:01/지연/미래 전부), API 에러 가드 견고, from-csv 가드 회귀 0, doctor INFO 강등 게이밍 불가(기계값 우선).

## 비고
- 같은 라운드의 cr1-ops(배선·운영 시뮬레이션 렌즈)는 **보고 전 사용자에 의해 중지됨** — 미수신. 2회차도 미실시(사용자 중단 결정). 배선·운영 렌즈 검증은 다음 세션 과제로 handoff에 기록.
