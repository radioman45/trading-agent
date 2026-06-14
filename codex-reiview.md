# Codex Review — Trading Agent Critical Improvements

작성일: 2026-06-15
대상: `trading-agent` 하네스 구조, 실행 산출물, 검증 체계

## 결론

현재 `trading-agent`는 일반 애플리케이션보다 Claude Code 멀티에이전트 투자 분석 하네스에 가깝다. 구조적 아이디어는 강하다. Bull/Bear 격리, SSOT, 리스크 게이트, IPO 전용 스냅샷, 복기 루프는 방향이 맞다.

하지만 가장 큰 약점은 좋은 규칙이 실제 실행 가능한 통제로 고정되어 있지 않다는 점이다. 하드 게이트가 문서와 프롬프트에만 있고 코드 검증으로 강제되지 않기 때문에, 에이전트가 `거의 충족`, `성향 정의로 수용`, `잔여 리스크로 명시` 같은 자연어 판단으로 게이트를 우회할 수 있다.

## 핵심 리스크

### 1. 하드 게이트가 자연어로 완화된다

`trade-planning`과 `risk-gate`는 손익비, ATR, 비중, 손실 한도를 하드 게이트처럼 정의한다. 그러나 실제 산출물에서는 경계값 미달이 승인으로 처리된다.

대표 사례:

- `_workspace/04_trade_plan.md`에서 `손절 폭 >= 1.5 ATR` 체크가 존재한다.
- 같은 파일에서 중립/공격 손절은 `1.49 ATR`로 표기된다.
- `_workspace/06_final_decision.md`는 이를 `반올림 경계 사실상 충족`으로 보고 APPROVE한다.

이건 단순 반올림 문제가 아니다. 투자 하네스의 핵심 안전장치가 모델의 문장 해석에 맡겨져 있다는 신호다.

개선:

- `scripts/validate_workspace.py`를 추가한다.
- 다음 조건을 기계적으로 검사한다.
  - 거래 손익비 `>= 1.5`
  - 손절 폭 `>= 1.5 ATR`
  - 1회 손실 `<= 계좌 2%`
  - 성향별 비중 상한 준수
  - IPO EV `> 0` 또는 진입 보류
  - IPO 비대칭비 `>= 1.5` 또는 진입 보류
  - IPO `self_check.overall == PASS`
- 실패 시 `APPROVE`, 보고서 복사, 저널 append를 금지한다.

### 2. 게이트 실패와 잔여 리스크가 섞인다

`_workspace_ipo/03d_execution_review.md`는 중립형 5%, 공격형 10%가 -65% tail 기준 계좌 2% 손실 골격을 초과한다고 적으면서도 재작성 불필요로 처리한다. 계획이 이를 숨기지 않았다는 이유로 치명이 아니라고 판단한다.

이 방식은 위험하다. 하드 한도는 명시했다고 해서 통과되는 것이 아니다. 명시는 disclosure이고, 한도 준수는 control이다.

개선:

- `잔여 리스크`와 `게이트 실패`를 분리한다.
- 다음 항목은 잔여 리스크로 넘기지 않는다.
  - 산식 오류
  - 하드 한도 초과
  - 손절/가설훼손 조건 누락
  - 방향 판정과 실행 계획 불일치
  - IPO 스냅샷 self-check 실패
- 예외가 필요하면 `policy_override`를 구조화해 요구한다.
  - 어떤 게이트를 넘었는가
  - 왜 넘겼는가
  - 누가 승인했는가
  - 어떤 상한을 대신 적용하는가

### 3. 도구 계약이 실제 환경과 맞지 않는다

여러 스킬과 에이전트가 `insane-search`, `database-lookup`, `WebSearch`, `k-dart` 같은 도구를 전제로 한다. 일부는 현재 Codex 환경에서 직접 호출 가능한 도구가 아니다.

문제:

- 프롬프트는 존재하지 않는 도구를 쓰라고 지시한다.
- 에이전트는 도구 실패를 데이터 미확보로 처리하지만, 실패 원인이 "도구 부재"인지 "외부 접근 차단"인지 구분하지 못한다.
- 결과적으로 데이터 품질 저하가 구조적으로 반복될 수 있다.

개선:

- `docs/tool-contract.md`를 추가한다.
- 도구별로 다음을 명시한다.
  - 현재 환경에서 실제 사용 가능한가
  - 대체 경로는 무엇인가
  - 실패 시 confidence를 어떻게 낮출 것인가
  - 어떤 데이터는 도구 부재 시 분석을 중단해야 하는가
- 문서와 프롬프트에서 없는 도구명은 제거하거나 실제 사용 가능한 스킬/스크립트로 치환한다.

### 4. 소스와 산출물의 버전관리 경계가 흐리다

현재 `.claude`, `docs`, `scripts`, `_workspace`, `_workspace_ipo`, `reports`, `decisions`, `raws`, `.omx`가 같은 작업 트리에 섞인다. 일부 산출물은 git 추적 대상이고, 일부는 미추적이다.

문제:

- 하네스 정의 변경과 실행 결과 변경이 같은 diff에 섞인다.
- `_workspace`는 현재 실행 캐시인데 git 추적 상태로 계속 바뀐다.
- `reports`는 일부만 추적되어 아카이브 정책이 모호하다.
- `.omx` 런타임 상태와 로그가 미추적 상태로 남는다.
- Windows 환경에서 LF/CRLF 변환 경고가 대량 발생해 diff 품질을 떨어뜨린다.

개선:

- 저장소 파일을 네 범주로 나눈다.
  - 시스템 소스: `.claude/`, `docs/`, `scripts/`, `README.md`, `CLAUDE.md`
  - 실행 캐시: `_workspace/`, `_workspace_ipo/`, `_workspace_prev/`, `_workspace_ipo_prev/`
  - 보존 산출물: `reports/`, `decisions/`
  - 로컬 런타임: `.omx/`, `.env`, 임시 로그
- `.gitignore`와 `.gitattributes`를 갱신한다.
- 최소 `.gitattributes` 예:

```gitattributes
* text=auto eol=lf
*.md text eol=lf
*.json text eol=lf
*.csv text eol=lf
*.ps1 text eol=crlf
*.mp3 binary
*.xlsx binary
```

### 5. 문서 drift가 이미 발생했다

현재 파일 기준:

- `.claude/agents`: 20개
- `.claude/skills`: 20개

그러나 README는 agents 19개, skills 18개로 설명한다. 또 `docs/decision-flow.md`는 11명/5계층 기준이고, 현재 `trading-strategy`는 12명/6계층 구조다.

문제:

- 운영자가 문서만 보고 실행 구조를 오해할 수 있다.
- 하네스 개선이 문서와 비동기화되면 다음 수정자가 잘못된 전제를 이어받는다.

개선:

- `scripts/audit_harness.py`를 추가한다.
- 검사 항목:
  - agents/skills 실제 개수
  - README에 적힌 개수와 일치 여부
  - Mermaid 흐름도 계층 수와 오케스트레이터 스킬 설명 일치 여부
  - 각 agent frontmatter의 `name`, `description`, `model` 존재 여부
  - 스킬 frontmatter의 `name`, `description` 존재 여부
  - 문서 링크/dead path 검사

### 6. 의존성 명세가 없다

실제 코드에는 Python 의존성이 있다.

- `collect_market_data.py`: `pandas`, `yfinance`
- `generate_audio.py`: `notebooklm-py[browser]`, `playwright`

README에는 요구 사항이 설명되어 있지만 `requirements.txt`나 `pyproject.toml`이 없어 재현 가능한 설치가 어렵다.

개선:

- 최소 `requirements.txt`를 추가한다.

```txt
pandas
yfinance
notebooklm-py[browser]
```

- Playwright 브라우저 설치는 README 또는 `scripts/setup.ps1`에서 별도 안내한다.
- smoke test를 추가한다.
  - `python .claude/skills/market-snapshot/scripts/collect_market_data.py --help`
  - `python .claude/skills/notebooklm-audio/scripts/generate_audio.py --help`
  - `python -m json.tool _workspace/00_market_snapshot.json`
  - `python -m json.tool _workspace_ipo/00_ipo_snapshot.json`

### 7. 저널이 사람에게는 좋지만 캘리브레이션에는 약하다

`decisions/journal.md`는 사람이 읽기 좋다. 하지만 확신도와 성과를 장기적으로 검증하기에는 구조화가 부족하다.

현재 문제:

- 확신도 정의가 문장 안에 묻힌다.
- 결과 갱신이 markdown 라인 수정에 의존한다.
- 벤치마크, 기간, 알파, 결과 상태를 자동 집계하기 어렵다.
- "60% 확신도"가 실제로 60% 수준의 캘리브레이션을 보였는지 측정할 수 없다.

개선:

- `decisions/journal.jsonl`을 병행한다.
- 권장 필드:

```json
{
  "id": "2026-06-14-NVDA-trading",
  "date": "2026-06-14",
  "harness": "trading",
  "ticker": "NVDA",
  "decision": "APPROVE",
  "direction": "watch",
  "confidence": 0.60,
  "confidence_definition": "신규 매수가 6~12개월 내 S&P500 대비 알파를 못 낼 확률",
  "horizon": "6-12m",
  "benchmark": "S&P500",
  "entry_basis": "conditional",
  "max_position_pct": {
    "conservative": 0.05,
    "neutral": 0.10,
    "aggressive": 0.12
  },
  "result_status": "pending",
  "result_alpha_pct": null
}
```

### 8. IPO 스냅샷의 PASS가 너무 좁은 산술만 본다

`_workspace_ipo/00_ipo_snapshot.json`의 `self_check.overall`은 PASS다. 이는 시총, 조달, free float 산식 같은 핵심 산술에는 유효하다. 그러나 스냅샷 안에는 OCR 기반 preliminary 값, press 기반 값, EDGAR 직접 교차 미확보 값도 많다.

문제:

- `PASS`가 전체 데이터 신뢰도를 과대 대표할 수 있다.
- 사용자는 self_check PASS를 보고 "스냅샷 전체가 검증됐다"고 오해할 수 있다.

개선:

- `self_check`를 두 단계로 나눈다.
  - `arithmetic_check`: 산식 검산
  - `source_check`: 1차 출처 직접 검증
- 최상위 `overall` 대신 다음처럼 분리한다.

```json
{
  "self_check": {
    "arithmetic": "PASS",
    "source_coverage": "PARTIAL",
    "blocking_issues": [],
    "nonblocking_issues": [
      "AI segment financials not directly verified in EDGAR",
      "free_float reported 7% unresolved"
    ]
  }
}
```

### 9. REVISE 루프가 “해소 여부만 점검”이라 부분 최적화 위험이 있다

현재 REVISE 후에는 지정된 지시 해소 여부만 점검한다. 이는 무한 루프를 막는 장점이 있지만, 수정 중 새 오류가 생겨도 놓칠 수 있다.

개선:

- 재호출 후에는 "지시 해소 여부"와 "새로운 하드 게이트 위반 없음"을 함께 검사한다.
- 자동 검증기가 있으면 이 문제는 대부분 해결된다.

### 10. 팟캐스트는 선택 산출물인데 오케스트레이터 계약에는 필수 질문으로 묶여 있다

`trading-strategy`와 `ipo-analysis`는 최종 보고 후 팟캐스트 생성 여부를 반드시 묻도록 되어 있다. 산출물 경험 측면에서는 좋지만, 자동 실행/배치 실행에는 방해가 될 수 있다.

개선:

- 입력에 `podcast_mode`를 둔다.
  - `ask`
  - `script`
  - `audio`
  - `none`
- 기본값은 대화형 세션에서만 `ask`, 비대화형 실행에서는 `none`으로 둔다.

## 권장 실행 순서

### 1단계: 검증기를 먼저 만든다

가장 먼저 `scripts/validate_workspace.py`를 만든다. 문서 정리보다 중요하다. 이 검증기가 없으면 하네스의 안전 규칙은 계속 자연어 판정에 의존한다.

검증 대상:

- `_workspace/00_market_snapshot.json`
- `_workspace/04_trade_plan.md`
- `_workspace/06_final_decision.md`
- `_workspace_ipo/00_ipo_snapshot.json`
- `_workspace_ipo/03_judge_verdict.md`
- `_workspace_ipo/03c_ipo_entry_plan.md`
- `_workspace_ipo/03d_execution_review.md`
- `decisions/journal.md`

### 2단계: 버전관리 경계를 정리한다

- `.gitignore`
- `.gitattributes`
- 산출물 보존 정책 문서

### 3단계: 의존성 및 smoke test를 추가한다

- `requirements.txt` 또는 `pyproject.toml`
- `scripts/smoke_test.ps1`
- JSON 유효성 검사
- 스크립트 help 검사

### 4단계: 문서 drift를 정리한다

- README의 agents/skills 수 갱신
- `docs/decision-flow.md`를 12명/6계층으로 갱신
- `CLAUDE.md`와 README의 모델 라우팅 설명 통일

### 5단계: 저널 구조화를 추가한다

- `decisions/journal.jsonl`
- markdown journal과 JSONL의 id 연결
- pending 결산 자동화 기준을 JSONL 중심으로 이동

## 최종 평가

`trading-agent`는 이미 단순 프롬프트 모음 수준을 넘어 투자 의사결정 하네스의 형태를 갖추고 있다. 다만 현재 품질은 "문서화된 엄격함"에 비해 "실행상 엄격함"이 부족하다.

가장 중요한 개선 방향은 에이전트에게 더 많은 지시를 쓰는 것이 아니다. 반대로, 에이전트가 해석할 여지를 줄이고 기계가 검증할 수 있는 부분을 코드로 빼내는 것이다.

핵심 원칙:

- 산식은 모델에게 맡기지 말고 코드가 검산한다.
- 하드 게이트는 자연어로 완화하지 않는다.
- 잔여 리스크와 게이트 실패를 구분한다.
- 시스템 소스와 실행 산출물의 경계를 분리한다.
- 확신도는 기록하고, 시간이 지나면 캘리브레이션한다.

