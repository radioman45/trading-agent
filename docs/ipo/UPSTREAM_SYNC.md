# Upstream Sync Manifest — IPO 하네스

> **위치 이력:** `spcx/` → `trading-agent-ipo-spcx/` → **2026-06-11 `trading-agent/`로 통합 이관.** 현재 IPO 하네스 자산은 `trading-agent/.claude/`(공용), 작업공간 `_workspace_ipo/`, 문서는 `docs/ipo/`에 있다. 아래 표의 "spcx에서의 변경" 표기는 이관 전 기록이다.

이 하네스는 `Stud_stock_analyzer`의 2차 시장 투자 분석 하네스를 **fork + IPO 특화**한 것이다. 공통 자산이 두 곳에 사본으로 존재하므로 드리프트를 추적하기 위해 이 매니페스트를 둔다.

- **베이스 출처:** `C:\Users\yhlee\Desktop\myprojects\Stud_stock_analyzer\.claude`
- **베이스 커밋:** `fa2b0a9` (2026-06-02) — 홈 git repo(`C:\Users\yhlee`) 기준
- **fork 시점:** 2026-06-09

## 복사한 자산 (그대로 가져온 뒤 IPO 분기)

| 대상 | 베이스 원본 | spcx에서의 변경 |
|------|-------------|----------------|
| agents/bull-analyst.md | 동일 | 경로 참조만(ipo-analysis), 오케스트레이터가 "IPO 모드"로 호출 |
| agents/bear-analyst.md | 동일 | 〃 |
| agents/fact-checker.md | 동일 | 경로 참조, IPO 소싱은 fact-check 스킬에서 |
| agents/investment-judge.md | 동일 | 경로 참조, IPO 판정은 investment-judge 스킬에서 |
| agents/verdict-reviewer.md | 동일 | 경로 참조, IPO 축은 verdict-review 스킬에서 |
| agents/data-collector.md | 동일 | **IPO 의무 추가**(EDGAR 최신·free_float 4필드·self_check), 스킬→ipo-snapshot |
| agents/execution-strategist.md | 동일 | **IPO 모드 추가**(게이트·가설훼손), 스킬→ipo-timing |
| skills/bull-case | 동일 | **## IPO 모드** 섹션 추가 |
| skills/bear-case | 동일 | **## IPO 모드** 섹션 추가 |
| skills/investment-judge | 동일 | **## IPO 판정 모드** 섹션 추가 |
| skills/fact-check | 동일 | **IPO 검증 소싱 규칙** 추가 |
| skills/verdict-review | 동일 | **⑨ IPO 정합성**(Part A) + **ⓗ IPO 실행 게이트**(Part B) 추가 |
| skills/ipo-analysis/references/data-sources.md | investment-analysis/references/ | 경로/파일명만 IPO화 |
| skills/ipo-analysis/references/report-schema.md | 〃 | **IPO 변형** 섹션 추가 |

## 신규 작성 (베이스 파생 후 전면 재작성)

| 대상 | 파생 원본 | 핵심 차이 |
|------|-----------|----------|
| skills/ipo-snapshot | market-snapshot | 거래가 대신 공모 구조·free_float 4필드·락업·self_check |
| skills/ipo-timing | execution-strategy | 실행 게이트·가격발견·안정조작·이벤트 분할·가설훼손 |
| skills/ipo-analysis | investment-analysis | 팟캐스트 제거, Phase 1.6 스냅샷 audit·하드 실패, IPO 트리거 |

## 미복사 (이번 범위 제외)

- ~~agents/podcast-producer.md~~
- ~~skills/podcast-script, skills/notebooklm-audio~~

> **2026-06-11 갱신:** 팟캐스트 3종은 통합 홈(trading-agent)으로 복사·일반화됨 — 두 하네스(트레이딩/IPO) 겸용, 최종 보고 후 필수 질문(대본+오디오/대본만/안 함)으로 트리거. 더 이상 미복사 아님.

## 전략 골격 정렬 — trading-agent 하네스 (2026-06-11)

`trading-agent`(TradingAgents 구조 이식, 2차 시장 트레이딩 하네스)와 **전체 투자 관점의 일관적 전략 방향**을 공유하도록 다음 골격을 정렬했다. 어느 한쪽의 원칙이 바뀌면 다른 쪽도 같이 검토할 것:

| 공통 골격 | trading-agent (2차 시장) | 이 하네스 (IPO 등가물) |
|-----------|--------------------------|------------------------|
| 1회 손실 한도 | 1회 거래 손실 ≤ 계좌 2% (손절폭 역산) | 1회 캠페인 잠재 손실(최대 비중×하방 시나리오) ≤ 2% 골격, 보수형 강제 |
| 비중 상한 | 보수 5% / 중립 10% / 공격 15% | IPO 할인 적용: 보수 ~3% / 중립 ~7% / 공격 ~15% |
| 진입 게이트 | 손익비 < 1.5 → "보류 + 성립 조건" | 비대칭비(상방/가치앵커 하방) < 1.5 또는 EV ≤ 0 → "진입 보류 + 성립 조건" |
| 손절 | 기술적 무효화 + 1.5 ATR | 가격 손절 대신 가설훼손 체크포인트(판결 반증 조건에서 도출) |
| 학습 루프 | journal.md·lessons.md·trade-reflection·pending 결산 | decisions/journal.md·lessons.md·ipo-reflection·Phase 0 pending 결산 (동일 포맷 준용) |
| 교훈 위반 | PM이 정당화 의무 점검 | verdict-reviewer가 Part A ⑧·Part B ⓖ에서 점검 |

## 재동기화 체크리스트 (베이스가 수정되면)

1. 베이스 최신 커밋과 위 "베이스 커밋"을 비교(`git log fa2b0a9..HEAD -- Desktop/myprojects/Stud_stock_analyzer/.claude`).
2. 공통 로직(에이전트 원칙·검토 축·면책·스키마)의 수정이 spcx에도 필요한지 판단.
3. 필요하면 해당 파일에 반영하되 **IPO 분기 섹션은 보존**한다.
4. 이 매니페스트의 "베이스 커밋"을 갱신한다.
