# 검증 대상 — CRYPTO 시장 모드 확장 (2026-07-05)

## 스코프
베이스 커밋 `26080ab` 위의 미커밋 워킹트리 변경 5파일:

1. `.claude/skills/market-snapshot/scripts/collect_market_data.py` — is_crypto_symbol/detect_market CRYPTO 분기, judge_session CRYPTO 브랜치(always_open·UTC 마감·anomaly 가드), fetch_coinbase_daily·fetch_binance_daily 신설, cross_check_close 크립토 체인(coinbase→binance, skipped_crypto_quote), from-csv 가드 크립토 확신 신호, --market CRYPTO 선택지
2. `scripts/harness_doctor.py` — always_open이면 last_close_is_final=false를 INFO 강등(그 외 무변경)
3. `.claude/skills/market-snapshot/SKILL.md` — 시장 감지 3종(CRYPTO 규칙·상장 래퍼 우선 원칙), session/cross_check 크립토 서술, CRYPTO 수집 절차(유통량→shares_outstanding, financials unavailable, 벤치마크 규칙), always_open 서술 문구
4. `.claude/agents/market-data-engineer.md` — 규율 5 skipped_crypto_quote + 규율 6 CRYPTO 특칙 신설
5. `.claude/skills/trading-strategy/SKILL.md` — Phase 1 크립토 매매 수단 확인, 시장 3종, FA 프롬프트 크립토 렌즈 분기, description 크립토 트리거
6. `CLAUDE.md` — 변경 이력 행

## 사전 기계 테스트 (검토자 참고)
- 시장 감지 14케이스 PASS (BTC-USD/ETH-USD/SOL-USD/DOGE-USDT/BTC-KRW→CRYPTO, BRK-B/BF-B/GC=F→US, 005930/088980.KS→KR)
- 라이브 BTC-USD: 수집 OK, always_open, 당일 UTC 봉 final=false, coinbase match(diff 0.014%), binance 단독 검증(0.08%)
- 크립토는 fast_info 시총·주식수 null 실측 → 웹 교차 규정으로 커버
- doctor 크립토 합성 스냅샷: session OK·final INFO(상시 정상)·mcap(가격×유통량) 검산 통과·copy 지적 없음
- US/KR 세션·from-csv 가드·3하네스 회귀 0

## 설계 판단 (검토 시 참고)
- 크립토 intraday_data_gap=None(세션 개념 없음 — 지연은 stale_feed_suspect가 담당)
- binance는 USD 쿼트를 USDT로 근사(통상 괴리 <0.3%, 허용 오차 1% 내) — 2차 체인이라 수용
- 크립토 Stooq 폴백 없음(yfinance 실패 시 클린 실패 → 에이전트 웹 폴백)
- doctor 나머지 검사(복사 충실성·mismatch FAIL·옵트아웃 차단)는 시장 무관 동일 적용
