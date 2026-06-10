# Trading Agent — 투자 분석 통합 홈

Claude Code 멀티에이전트 하네스로 구동되는 **투자 의사결정 시스템**. 두 개의 하네스가 한 폴더에 살고, 하나의 의사결정 저널·교훈으로 학습한다.

> ⚠️ **면책:** 이 저장소의 모든 산출물은 AI 에이전트가 공개 자료와 명시된 가정으로 생성한 시뮬레이션이며, 특정 종목의 매수·매도 권유가 아니다. 투자 결정과 그 결과의 책임은 전적으로 사용자 본인에게 있다.

## 두 하네스

| | 트레이딩 (2차 시장) | IPO (신규상장) |
|---|---|---|
| 오케스트레이터 스킬 | `trading-strategy` | `ipo-analysis` |
| 대상 | 이미 상장·거래 중인 종목 (미국·한국) | 상장 예정/직후 공모주 (미국 SEC·한국 DART) |
| 구조 | [TradingAgents](https://github.com/tauricresearch/tradingagents) 이식 — 데이터 SSOT → 분석가 4렌즈 병렬 → Bull/Bear 2라운드 토론 → 리서치 판정 → 거래 계획 → 리스크 3성향 토론 → PM 최종 게이트 (에이전트 11) | 적대적 분석 — IPO 스냅샷(하드 게이트) → Bull∥Bear 격리 → 공시 팩트체크 → 심판 판정 → 판결 red-team → 진입 타이밍 전략 → 전략 red-team (전문가 6) |
| 핵심 게이트 | 손익비 ≥ 1.5, 1회 손실 ≤ 계좌 2%, 비중 상한 5/10/15%, ⛔치명 지적 시 APPROVE 불가 | 진입 보류 게이트(비대칭비 < 1.5·EV ≤ 0), 잠재 손실 ≤ 2% 골격, 비중 상한 3/7/15%(IPO 할인), 스냅샷 산식 모순 = ⛔하드 실패 |
| 작업공간 | `_workspace/` | `_workspace_ipo/` |
| 보고서 | `reports/{회사}_{날짜}/` | `reports/{회사}_IPO_{날짜}/` |

두 하네스는 **같은 전략 골격**(손실부터 정하는 역산, 수치화된 게이트, 결과론 금지 복기)을 공유한다 — 정렬표는 `docs/ipo/UPSTREAM_SYNC.md`.

## 빠른 시작

이 폴더에서 Claude Code 세션을 열고:

```
삼성전자 트레이딩 분석해줘          → trading-strategy 파이프라인
{회사} 공모주 분석해줘 / 청약할까   → ipo-analysis 파이프라인
지난 {종목} 결정 복기해줘           → 복기 모드 (저널 갱신 + 교훈 추출)
거래계획만 다시 / 진입전략만 다시    → 부분 재실행
```

**다른 폴더에서도** 전역 스킬 `invest-router`(`~/.claude/skills/`)가 투자 분석 요청을 이 홈으로 라우팅한다 — 비싼 파이프라인이므로 실행 전 반드시 진행 의사를 확인한다.

## 분석이 끝나면

1. **요약 보고** — 최종 판정·확신도·채택 계획·잔여 리스크.
2. **의사결정 저널 기록** — `decisions/journal.md`에 append-only로 기록(후향적 정당화 방지).
3. **팟캐스트 (선택)** — 반드시 묻는다: **① 대본 + 오디오(MP3) / ② 대본만 / ③ 만들지 않음.** 대본은 NotebookLM 스타일 두 호스트(준호·선희) 대화로 각색되고, 오디오는 `notebooklm-py`로 NotebookLM Audio Overview를 생성한다(최초 1회 `notebooklm login` 필요).

## 학습 루프

```
판정 → decisions/journal.md (append-only)
            ↓ 상장/보유 기간 경과
복기 (trade-reflection / ipo-reflection) — 결과론 금지, 벤치마크 알파 기준
            ↓
decisions/lessons.md (가설 1회 / 교훈 2회+, 적용 대상 지정)
            ↓
다음 분석에서 전 판단 에이전트가 자기 대상 교훈을 읽음
```

파이프라인 시작 시 `결과: (미기록)` 항목은 자동 중간점검(pending 결산)된다.

## 폴더 구조

```
trading-agent/
├── CLAUDE.md              # 하네스 포인터 + 변경 이력 (세션마다 로드)
├── README.md              # 이 문서
├── .claude/
│   ├── agents/            # 19개 — 트레이딩 11 + IPO 7 + podcast-producer
│   └── skills/            # 18개 — 트레이딩 7 + IPO 9 + podcast-script·notebooklm-audio
├── decisions/             # ★ 공용 학습 루프 (append-only)
│   ├── journal.md         #   모든 최종 판정 (트레이딩 + IPO)
│   └── lessons.md         #   복기에서 추출된 교훈
├── docs/
│   ├── decision-flow.md   # 트레이딩 의사결정 흐름도 (mermaid)
│   ├── model-and-reasoning-choice.md
│   └── ipo/               # IPO 하네스 문서 (HARNESS_PLAN, UPSTREAM_SYNC, codex-review, 시드)
├── scripts/               # 보조 스크립트 (예: load-dart-key.ps1)
├── _workspace/            # 트레이딩 중간 산출물 (보존 — 감사 추적·부분 재실행)
├── _workspace_ipo/        # IPO 중간 산출물
└── reports/               # 최종 보고서 (회사·날짜별 폴더)
```

## 요구 사항

| 항목 | 용도 | 필수 여부 |
|------|------|----------|
| Python + `yfinance` | 시세·기술지표 수집 (`market-snapshot` 번들 스크립트) | 트레이딩 필수 |
| DART API 키 (`.env` / `scripts/load-dart-key.ps1`) | 한국 공시 조회 (`k-dart`) | 한국 종목·한국 IPO 권장 |
| `notebooklm-py[browser]` + `notebooklm login` | 팟캐스트 오디오(MP3) 생성 | 선택 (대본만이면 불필요) |

## 운영 원칙 (요약)

- **격리가 정보량의 원천** — Bull/Bear R1, 리스크 3성향은 서로의 산출물을 보지 않는다. 데이터는 `_workspace*/` 파일로만 전달.
- **숫자는 의견이 아니다** — SSOT 스냅샷, 산식 검산, IPO 스냅샷 모순은 하드 실패.
- **손실부터 정한다** — 손절/가설훼손과 허용 손실을 먼저, 비중은 역산.
- **게이트 미달이면 "보류"가 정답** — 억지 진입 계획은 검토관이 잡는다.
- **결과론 금지** — 복기는 결과가 아니라 당시 정보 기준의 의사결정 품질을 평가한다.
- 모든 에이전트는 `model: opus`. 하네스 수정 이력은 `CLAUDE.md` 변경 이력 테이블에 기록.
