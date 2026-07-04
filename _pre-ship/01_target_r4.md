# 검증 대상 — 수집 레이어 기계 판정 (codex R4 잔여 반영, 2026-07-04 23시 구현분)

## 스코프
베이스 커밋 `52bd300` 위의 미커밋 워킹트리 변경 6파일:

1. `.claude/skills/market-snapshot/scripts/collect_market_data.py` (+257) — session 블록 기계 판정(judge_session, DST 근사), 이중 소스 교차(cross_check_close: stooq→nasdaq 체인, 허용 오차 1%), 미국 티커 yfinance 실패 시 Stooq 1차 폴백 자동화, `--market/--xcheck-tolerance/--no-xcheck/--now-utc` 옵션
2. `scripts/harness_doctor.py` (+43) — 스냅샷 v1.1 session 블록 누락 FAIL, last_close_is_final=false·stale_feed_suspect=true WARN, cross_check mismatch↔결정문 DEGRADED_DATA 정합 검사
3. `.claude/skills/market-snapshot/SKILL.md` (+26) — 스키마 v1.1(session 필수 복사), 세션별 가격 서술 문구 규칙, cross_check 처리 규정, 자가 점검 체크리스트 2항목
4. `.claude/agents/market-data-engineer.md` (+5) — 규율 4 교체(세션 기계값 복사 [HARD]) + 규율 5 신설(이중 소스 교차 처리), 에러 핸들링 Stooq 자동 폴백 반영
5. `.claude/skills/trading-strategy/SKILL.md` (+3) — Phase 1.6 fact-checker 점검축 ① 보강 + ⑤(수집 레이어 정합) 신설
6. `CLAUDE.md` (+1) — 변경 이력 행

## 사전 기계 테스트 결과 (검토자 참고)
- 세션 판정 6케이스(--now-utc 주입, US 4세션 + KR 2세션) 전부 PASS
- 라이브 AAPL: 수집 OK, session=weekend, cross_check=match (stooq)
- doctor 3하네스 회귀 없음 (trading FAIL 2 = 구 MKIF 실행분의 기존 True Positive 그대로)
- 두 스크립트 py_compile OK

## 배경
SOL 반도체ETF 사고(2026-06-24)의 근본 원인 "세션을 LLM이 추정"을 코드로 이관하는 작업. 세션 판정·소스 폴백이 프롬프트 규율로만 존재하던 것을 수집 스크립트의 결정적 판정으로 옮김. 휴장일 캘린더는 의도적으로 내장하지 않음(외부 의존 없이 결정적 — 근사 한계는 calendar_status로 정직 표기).
