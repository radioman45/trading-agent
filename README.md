# Trading Agent — 투자 분석 통합 홈

Claude Code 멀티에이전트 하네스로 구동되는 **투자 분석 시스템**. 세 개의 하네스가 한 폴더에 살고, 트레이딩·IPO 하네스는 하나의 의사결정 저널·교훈·캘리브레이션으로 학습한다.

> ⚠️ **면책:** 이 저장소의 모든 산출물은 AI 에이전트가 공개 자료와 명시된 가정으로 생성한 시뮬레이션이며, 특정 종목의 매수·매도 권유가 아니다. 투자 결정과 그 결과의 책임은 전적으로 사용자 본인에게 있다.

## 문서가 어디에 있나 (SSOT 계층)

이 README는 **입구 문서**다. 숫자(에이전트·스킬 수, 단계 구성)를 여기에 중복 기록하지 않는다 — 문서 간 drift가 곧 실행 drift가 되기 때문이다. 기준은 다음 한 곳씩이다:

| 무엇 | 단일 기준(SSOT) |
|------|----------------|
| 실행 규칙·Phase·게이트 | 각 오케스트레이터 스킬 — `.claude/skills/{trading-strategy, ipo-analysis, filings-analysis}/SKILL.md` |
| 전체 구조 조감도 | `docs/harness-architecture.md` (Mermaid) |
| 운영 지침·트리거·변경 이력 | `CLAUDE.md` |
| 에이전트·스킬 목록 | `.claude/agents/`, `.claude/skills/` 디렉토리 자체 |
| 보유 현황·저널·교훈·캘리브레이션 | `decisions/` (`portfolio.json`·`journal.md`·`lessons.md`·`calibration.md`) |

## 세 하네스

| | 트레이딩 (2차 시장) | IPO (신규상장) | 공시 분석 (Filings) |
|---|---|---|---|
| 오케스트레이터 스킬 | `trading-strategy` | `ipo-analysis` | `filings-analysis` |
| 대상 | 상장·거래 중인 종목 (미국·한국) | 상장 예정/직후 공모주 (SEC·DART) | 제공된 공시 원문 (10-K/10-Q·DART 보고서) |
| 산출 | 거래 계획 + 최종 게이트 판정 | IPO 판정 + 진입 타이밍 전략 | 공시·펀더멘털 **이해 리포트** (매매 판단 없음) |
| 작업공간 | `_workspace/` | `_workspace_ipo/` | `_workspace_filings/` |
| 보고서 | `reports/{회사}_{날짜}/` | `reports/{회사}_IPO_{날짜}/` | `reports/{회사}_공시분석_{날짜}/` |
| 저널 기록 | O (공용 학습 루프) | O (공용 학습 루프) | X (이해 목적 — 매매 판단은 트레이딩 하네스로) |

트레이딩·IPO는 **같은 전략 골격**(손실부터 정하는 역산, 수치화된 게이트, 결과론 금지 복기)을 공유한다 — 정렬표는 `docs/ipo/UPSTREAM_SYNC.md`.

## 빠른 시작

이 폴더에서 Claude Code 세션을 열고:

```
삼성전자 트레이딩 분석해줘          → trading-strategy 파이프라인
뭐 살까 / 아이디어 스캔             → 능동 소싱 (레짐 → 후보 발굴)
{회사} 공모주 분석해줘 / 청약할까   → ipo-analysis 파이프라인
이 10-Q 분석해줘 / 공시 읽어줘      → filings-analysis 파이프라인
지난 {종목} 결정 복기해줘           → 복기 모드 (저널 갱신 + 교훈 추출)
거래계획만 다시 / 진입전략만 다시    → 부분 재실행
```

**다른 폴더에서도** 전역 스킬 `invest-router`(`~/.claude/skills/`)가 투자 분석 요청을 이 홈으로 라우팅한다 — 비싼 파이프라인이므로 실행 전 반드시 진행 의사를 확인한다.

## 분석이 끝나면

1. **판정 요약 박스** — 최종 보고서 첫 화면에서 판정(APPROVE/CONDITIONAL_APPROVE/REVISE/REJECT)·검증 모드(FULLY_VERIFIED/DEGRADED_DATA)·포트폴리오 모드·경고 집계를 즉시 확인할 수 있다.
2. **기계 검증(harness doctor)** — `scripts/harness_doctor.py`가 필수 산출물·산술·라벨 정합을 결정적으로 검사한 결과(`닥터리포트_{날짜}.json`)가 보고서 폴더에 함께 남는다.
3. **의사결정 저널 기록** — `decisions/journal.md`에 append-only로 기록(후향적 정당화 방지), 직후 커밋.
4. **팟캐스트 (선택)** — 반드시 묻는다: **① 대본 + 오디오(MP3) / ② 대본만 / ③ 만들지 않음.** 오디오는 `notebooklm-py`로 생성(최초 1회 `notebooklm login` 필요).

## 학습 루프 (트레이딩·IPO 공용)

```
판정 → decisions/journal.md (append-only)
            ↓ 상장/보유 기간 경과
복기 (trade-reflection / ipo-reflection) — 결과론 금지, 벤치마크 알파 기준
            ↓
decisions/lessons.md (가설 1회 / 교훈 2회+, 적용 대상 지정)
decisions/calibration.md (확신도 vs 적중률 — 지평·확정 트리거 컬럼, 만기 전 조기 확정 금지)
            ↓
다음 분석에서 전 판단 에이전트가 자기 대상 교훈을 읽음
```

파이프라인 시작 시 `결과: (미기록)` 항목은 자동 중간점검(pending 결산)된다. `decisions/` 갱신은 커밋과 한 몸이다.

## 폴더 구조

```
trading-agent/
├── CLAUDE.md              # 하네스 포인터 + 트리거 + 변경 이력 (세션마다 로드)
├── README.md              # 이 문서 (입구 — 숫자·규칙은 SSOT 참조)
├── .claude/
│   ├── agents/            # 에이전트 정의 (목록은 디렉토리가 기준)
│   └── skills/            # 스킬 (오케스트레이터 3종 = 실행 규칙 SSOT)
├── decisions/             # ★ 공용 학습 루프 + 세션 간 상태 (append-only)
│   ├── journal.md         #   모든 최종 판정 (트레이딩 + IPO)
│   ├── lessons.md         #   복기에서 추출된 교훈
│   ├── calibration.md     #   확신도 캘리브레이션 대장
│   ├── portfolio.json     #   보유 현황 SSOT ("보유 등록"으로 갱신)
│   └── watchlist.md       #   아이디어 스캔 워치리스트
├── docs/                  # 구조 조감도·방법론 원천 (harness-architecture, neurofusion, ipo)
├── scripts/               # harness_doctor.py (기계 검증) 등 보조 스크립트
├── sources/               # 사용자 제공 공시 원문 (filings 하네스 입력)
├── _workspace*/           # 하네스별 중간 산출물 (보존 — 감사 추적·부분 재실행)
└── reports/               # 최종 보고서 (회사·날짜별 폴더)
```

## 요구 사항

| 항목 | 용도 | 필수 여부 |
|------|------|----------|
| Python + `yfinance` | 시세·기술지표 수집 (`market-snapshot` 번들 스크립트) + harness doctor | 트레이딩 필수 |
| DART API 키 (`.env` / `scripts/load-dart-key.ps1`) | 한국 공시 조회 (`k-dart`) | 한국 종목·한국 IPO 권장 |
| `notebooklm-py[browser]` + `notebooklm login` | 팟캐스트 오디오(MP3) 생성 | 선택 (대본만이면 불필요) |

## 운영 원칙 (요약)

- **격리가 정보량의 원천** — Bull/Bear R1, 리스크 3성향, 공시 4렌즈는 서로의 산출물을 보지 않는다. 데이터는 `_workspace*/` 파일로만 전달.
- **숫자는 의견이 아니다** — SSOT 스냅샷, 산식 검산, IPO 스냅샷 모순은 하드 실패. 기계로 잡을 수 있는 것은 doctor가 잡는다(LLM 검증은 보완재).
- **라벨은 실체와 일치한다** — 게이트는 BLOCKING/DEGRADED/ADVISORY로 정직하게 명명하고, 강등·조건부 승인·보유 미등록은 라벨(DEGRADED_DATA·CONDITIONAL_APPROVE·SINGLE_TRADE_ONLY)로 전면에 드러낸다.
- **손실부터 정한다** — 손절/가설훼손과 허용 손실을 먼저, 비중은 역산.
- **게이트 미달이면 "보류"가 정답** — 억지 진입 계획은 검토관이 잡는다. 단, 관망도 기대 비용을 명시한다(기회비용도 손실이다).
- **결과론 금지** — 복기는 결과가 아니라 당시 정보 기준의 의사결정 품질을 평가한다.
- 모델 라우팅·하네스 수정 이력은 `CLAUDE.md`가 기준(저부하 계층 sonnet · 분석·판단 코어 opus).
