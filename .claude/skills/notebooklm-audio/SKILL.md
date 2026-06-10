---
name: notebooklm-audio
description: 마크다운 보고서/대본을 Google NotebookLM의 Audio Overview(팟캐스트 오디오)로 자동 생성하는 스킬. teng-lin/notebooklm-py CLI를 구동해 노트북 생성→소스 추가→오디오 생성(deep-dive/brief/critique/debate, 50+ 언어)→MP3 다운로드를 수행한다. "NotebookLM으로 팟캐스트 생성", "대본을 오디오로", "MP3로 만들어", "노트북LM 오디오", "팟캐스트 음성 생성"을 요청받거나 투자 하네스(trading-strategy/ipo-analysis)가 팟캐스트 오디오를 만들 때 반드시 이 스킬을 사용한다. 단, 대본(텍스트) 작성 자체는 podcast-script 스킬이 담당한다.
---

# NotebookLM Audio — 마크다운 → 팟캐스트 오디오

이 스킬은 이미 작성된 마크다운(최종 투자 보고서, 팟캐스트 대본 등)을 **실제 팟캐스트 오디오(MP3)** 로 변환한다. 비공식 라이브러리 `notebooklm-py`의 CLI를 번들 스크립트로 구동한다.

## 핵심 사실 — NotebookLM은 대본을 그대로 낭독하지 않는다

NotebookLM의 Audio Overview는 **소스(문서)를 받아 자체적으로 오디오를 재생성**한다. 우리가 쓴 준호/선희 대본을 글자 그대로 읽어주는 것이 아니다. 따라서 전략은:
- **대본과 최종 보고서를 둘 다 소스로 넣어** NotebookLM이 사실(보고서)과 원하는 구성·결론(대본)을 모두 참고하게 한다.
- **`--format debate`** 로 두 진행자의 토론 형식을 유도한다(강세 vs 약세에 가장 잘 맞는다).
- **`--instructions`(한국어 지침)** 로 "강세·약세를 토론하되 최종 결론은 {판정}임을 분명히 전달"처럼 결론을 못박는다.

대본은 그래서 두 역할을 한다: ① 사람이 읽는 산출물, ② NotebookLM 생성을 유도하는 소스.

## 사전 요구 (사용자가 1회 직접 수행)

NotebookLM은 Google 계정 로그인이 필요하고, 로그인은 대화형이라 **에이전트가 대신 할 수 없다.** 처음 한 번만 사용자가 설정한다:

```bash
pip install "notebooklm-py[browser]"
playwright install chromium
notebooklm login      # 브라우저가 열리며 Google 로그인
```

Claude Code 세션 안에서는 프롬프트에 **`! notebooklm login`** 을 입력하면 이 세션에서 로그인할 수 있다. 자격증명은 로컬에 저장되어 이후 재사용된다(API 키 불필요).

## 워크플로우

### 1. 사전 점검 (인증·설치 확인 — 비대화형)

생성 전 반드시 확인한다. 미설치·미인증이면 오디오를 건너뛰고 사용자에게 설정을 안내한다.

```bash
python .claude/skills/notebooklm-audio/scripts/generate_audio.py --check-only \
  --out _tmp.mp3 --source <임의의_존재하는_md>
```
- 종료 코드 `0` = 준비됨 → 생성 진행
- 종료 코드 `2` = 미인증 → `notebooklm login` 안내 후 오디오 생략(대본은 이미 산출됨)
- 종료 코드 `3` = CLI 미설치 → pip 설치 안내 후 오디오 생략

또는 CLI로 직접: `notebooklm auth check --test --json` (성공 시 종료 코드 0).

### 2. 오디오 생성 + 다운로드

번들 스크립트가 노트북 생성→소스 추가→생성(--wait)→다운로드를 한 번에 수행한다. 소스는 하네스별 최종 보고서 + 대본:

```bash
# 트레이딩 예시
python .claude/skills/notebooklm-audio/scripts/generate_audio.py \
  --out "reports/<회사>_<날짜>/팟캐스트_<회사>.mp3" \
  --source "_workspace/06_final_decision.md" \
  --source "_workspace/07_podcast_script.md" \
  --title "<회사> 투자 분석" \
  --format debate --length default --language ko \
  --instructions "강세와 약세를 토론하되 최종 결론은 {판정}(확신도 {N}%)임을 분명히 전달"

# IPO 예시: --out "reports/<회사>_IPO_<날짜>/팟캐스트_<회사>.mp3"
#           --source "_workspace_ipo/03_judge_verdict.md" --source "_workspace_ipo/04_podcast_script.md"
```

생성 완료 후 스크립트는 `{"status":"ok","output":"...mp3",...}` JSON을 stdout으로 출력한다.

## 옵션 가이드

| 옵션 | 값 | 비고 |
|------|-----|------|
| `--format` | deep-dive \| brief \| critique \| **debate** | 적대적 강세/약세에는 debate |
| `--length` | short \| default \| long | 기본 default(중간) |
| `--language` | ko / en / ... (50+) | 한국어 ko |
| `--instructions` | 자유 텍스트(한국어) | 결론·톤을 못박는 핵심 유도 |
| `--source` | 파일 경로(반복) | 보고서+대본 둘 다 권장 |
| `--gen-timeout` | 초 (기본 1800) | 오디오 생성은 수 분~십수 분 소요 |

## 에러 핸들링 / 폴백

- **미인증/미설치(코드 2·3):** 치명적 실패가 아니다. 대본(.md)은 이미 산출되었으므로, 사용자에게 설정 방법을 안내하고 "설정 후 재실행하면 오디오 생성"이라고 알린다. 대본만으로도 NotebookLM 웹/다른 TTS에 수동 투입 가능하다.
- **생성 실패(코드 1):** `notebooklm-py`는 비공식 API라 변경·레이트리밋으로 깨질 수 있다. stderr를 사용자에게 전달하고, 대본은 보존한다. 한 번 재시도 후에도 실패하면 대본만 산출물로 보고한다.
- **언어/포맷 미지원:** 해당 옵션을 기본값(ko/debate)으로 낮춰 재시도한다.

## 재사용성

이 스킬은 투자 분석에 종속되지 않는다. 어떤 마크다운(리서치 보고서, 회의록, 학습 자료)이든 `--source`로 넣으면 NotebookLM 오디오로 만들 수 있다. 투자 하네스에서는 podcast-producer가 대본을 쓴 뒤, 사용자가 "대본+오디오"를 선택한 경우에만 오케스트레이터가 이 스킬을 호출한다.
