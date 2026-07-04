# Pre-Ship 점검 대상 — 2026-07-03 하네스 감사 보완 구현 (독립 검증 1회차)

## 대상 (In Scope)
2026-07-03 하네스 전면 감사 후 보완 구현분 — 미커밋 상태의 하네스 정의 자산:
- **트레이딩 코어 (메인 세션 수정):** `.claude/skills/trading-strategy/SKILL.md`(Phase S/M/P 신설·Phase 1.6·Phase 5 병렬 4+1·커밋·회전 규칙), `risk-gate`, `trade-planning`, `contrarian-check`, `trade-reflection`, `macro-regime`, `market-snapshot` 스킬; `fact-checker`(모드 2 신설), `portfolio-manager`, `research-manager`, `market-data-engineer`, `macro-strategist`, `data-collector` 에이전트
- **신규 자산:** `portfolio-risk-analyst`·`idea-scanner` 에이전트, `portfolio-risk`·`idea-scan` 스킬, `decisions/portfolio.json`·`watchlist.md`·`calibration.md`
- **IPO 하네스 (exec-ipo 위임 수정):** `ipo-analysis/SKILL.md`(+`references/data-sources.md`), `execution-strategist`·`bull-analyst`·`bear-analyst` 에이전트, `verdict-review`·`bull-case`·`bear-case`·`investment-judge`·`ipo-reflection` 스킬
- **공시 하네스 (exec-filings 위임 수정):** `filings-analysis/SKILL.md`, `plain-language/SKILL.md`, `report-explainer`·`podcast-producer` 에이전트
- **CLAUDE.md** 변경 이력 2026-07-03 행 3건의 사실성

## 제외 (Out of Scope)
- `_workspace/`·`_workspace_ipo/`·`_workspace_filings/`·`reports/` 분석 산출물 (과거 실행 결과물)
- `raws/` 대량 diff — OCR 변환 노이즈(소스 메타데이터·페이지 마커·워터마크) 정리로 확인됨, 하네스 정의와 무관
- `decisions/journal.md`·`lessons.md` 내용 자체 (append-only 기록물; 포맷 규칙 정합만 검증)

## 검증 초점 (handoff 브리프에서 지정된 취약 지점)
1. trading-strategy Phase S/M/P ↔ 기존 Phase 0 표·데이터 전달 표 정합
2. fact-checker 모드 2 ↔ 오케스트레이터 Phase 1.6 프롬프트 입출력 일치
3. portfolio-risk 산식·기본값(동시 꼬리 손실 등) ↔ risk-gate·trade-planning 수치 무모순
4. exec 위임분 ↔ 메인 수정분 교차 참조(예: calibration.md 포맷이 trade-reflection·ipo-reflection에서 동일)

## 방법
격리 검토자 5명 병렬(critic×2, code-reviewer×1, verifier×2) — 작업 맥락 미공유, 상호 격리, 읽기 전용.
"무엇을 고쳤는지"가 아니라 "현재 파일 상태가 정합한지"를 공격하게 한다.
타당성 게이트 → 수용·반영 → 2회차 반복. (사용자 전역 독립 검증 프로토콜 [HARD])
