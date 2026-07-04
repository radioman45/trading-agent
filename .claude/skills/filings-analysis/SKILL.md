---
name: filings-analysis
description: 공시 보고서 체계 분석 하네스 오케스트레이터. 제공된 기업 공시 원문(미국 10-K/10-Q, 한국 DART 분기/반기/사업보고서)을 외부 호출 없이 체계적으로 해부해, 매수/매도 판단이 아닌 '공시·펀더멘털 이해 리포트'를 산출하는 파이프라인을 조율한다. 아키비스트가 SSOT로 사실을 고정하고, 감사관이 추출을 검증한 뒤, 4렌즈(재무제표·MD&A·세그먼트·리스크)가 병렬 해부하고, (선택) 산업 22질문 심화 후, 종합가가 입체 리포트로 통합하고, 감사관이 종합을 red-team 검증하며, 쉬운 해설판까지 만든다. "공시 분석", "10-K 분석", "10-Q 분석", "사업보고서 분석", "분기보고서 분석", "DART 보고서 분석", "공시 보고서 체계적으로 분석", "{회사} 공시 해부", "재무제표 분석해줘", "이 공시 읽어줘"를 요청받으면 반드시 이 스킬을 사용한다. 후속 요청도 처리: "다시 분석", "재실행", "업데이트", "SSOT만 다시", "재무 렌즈만 다시", "MD&A만 다시", "세그먼트만 다시", "리스크만 다시", "산업까지 깊게", "산업만 다시", "종합만 다시", "검증만 다시", "쉬운 해설만", "다른 분기 추가", "이전 결과 기반으로". 단, 일반 회계·공시 상식 질문은 직접 응답해도 된다.
---

# Filings Analysis — 공시 보고서 체계 분석 하네스

제공된 공시 원문을 외부 호출 없이 체계적으로 해부해, **매수/매도 판단이 아닌 '이해 리포트'**를 만든다. **9명의 에이전트가 분업**한다(8 전용 + report-explainer 공용):

```
[D0 인입]    filings-archivist ── 제공 공시에서 사실 추출 → SSOT(00_filings_facts.json)
[D0.6 검증]  disclosure-auditor(추출 게이트) ── SSOT를 원문과 대조(할루시네이션 차단) — 팬아웃 전 [HARD]
[D1 해부]    financial ∥ mdna ∥ segment ∥ risk ── 4렌즈 병렬(같은 공시, 다른 렌즈, 상호 격리)
[D2 심화]    industry-analyst ── (선택) 산업 22질문 프레임 — 사용자가 원할 때만
[D3 종합]    filings-synthesizer ── 4렌즈+SSOT(+산업) → 입체 이해 리포트(03_synthesis.md)
[D3.5 검증]  disclosure-auditor(종합 red-team) ── 과대해석·신규주장·상충누락·경계위반 감사
[D4 해설]    report-explainer ── 쉬운 해설판(04_plain_explanation.md)
[선택]       podcast-producer ── 팟캐스트(05_podcast_script.md+MP3) — 사용자 동의 시만
```

**실행 모드: 서브 에이전트 (파이프라인 + 팬아웃/팬인 + 생성-검증).** 4렌즈는 서로의 산출물을 보지 않는다(독립 렌즈가 종합의 정보량 원천) — 파일로만 전달한다. 생성과 검증을 분리한다(작성자가 자기 결과를 검증하지 않는다 — disclosure-auditor가 격리 감사). 계층별 라우팅: 추출·해부·종합·검증 코어=opus, 해설=sonnet.

**제1원칙 — 제공 파일만.** 모든 사실은 사용자가 제공한 공시 원문에서만 나온다. 외부 웹·기억을 끌어오지 않는다(산업 선택 레이어만 예외적으로 태그된 일반지식 허용). 이것이 재현성·감사추적과 할루시네이션 차단의 근간이다.

**제2원칙 — 이해가 목적, 판단이 아니다.** 어떤 에이전트도 "사라/팔라"를 결론으로 내지 않는다. 매매 판단이 필요하면 trading-strategy 하네스로 간다.

## Phase 0: 컨텍스트 확인

`_workspace_filings/`와 사용자 요청을 대조해 실행 모드를 결정한다:

| 상황 | 모드 | 행동 |
|------|------|------|
| `_workspace_filings/` 없음 | **초기 실행** | Phase 1부터 전체 |
| 있음 + 새 공시 지정 | **새 실행** | 기존을 `_workspace_filings_prev/`로 이동 후 전체 |
| 있음 + 부분 수정 요청 | **부분 재실행** | 해당 에이전트만 재호출, 하류는 의존성 따라 갱신 |

**부분 재실행 의존성:** SSOT 갱신("SSOT만 다시") → 추출 게이트 재검증 → 4렌즈부터 전체 재실행. 특정 렌즈 갱신 → 종합부터 하류. 산업 추가("산업까지 깊게") → industry-analyst 실행 후 종합 갱신. 종합 갱신 → 종합 red-team + 해설 갱신. "다른 분기 추가" → 새 공시를 입력에 더해 초기 실행처럼(이전 분기 SSOT는 비교 참고로 보존).

## Phase 1: 입력 수집 + 현재시각 앵커

1. 분석 대상 공시를 확인한다 — 회사명, 공시 파일 경로(보통 `sources/` 하위), 공시 유형(10-K/10-Q/사업·반기·분기보고서), 시장(US/KR). 파일 경로가 불명확하면 사용자에게 묻는다.
   - **현재 시각 앵커 [HARD]:** 진행 전 현재 날짜를 `date`로 확인해 `00_input.md`에 기록한다(공시의 보고기간과 현재 시점을 혼동하지 않기 위함 — 할루시네이션 방지).
   - **제공 파일 실재 확인:** 지정된 공시 파일이 실제로 존재하고 비어있지 않은지 확인한다(0 byte·플레이스홀더면 사용자에게 알리고 다른 파일 확인).
2. `_workspace_filings/00_input.md` 작성:
   ```markdown
   # 공시 분석 입력
   - 회사: {회사명} ({티커, 있으면}) / 시장: {US|KR}
   - 공시: {유형} {회계기간} / 파일: {경로}
   - 함께 제공된 보조 자료: {컨콜 요약 등 또는 "없음"}
   - 분석 시점(현재): {YYYY-MM-DD}
   - 산업 심화 레이어: {요청됨 | 미요청(기본)}
   ```

## Phase 2: SSOT 추출 (D0)

```
# 추출·구조화 코어 → opus
Agent(subagent_type="filings-archivist", model="opus",
      prompt="_workspace_filings/00_input.md를 읽고 .claude/skills/filings-intake/SKILL.md 방법론으로
      제공된 공시 원문만 읽어 _workspace_filings/00_filings_facts.json(SSOT)을 작성하라.
      외부 수치 금지·제공 원문만, 단위는 원 단위 정수로 정규화하고 source에 공시 내 위치를 남겨라.
      못 찾은 값은 unavailable. 저장 전 작성 전 검증 체크리스트를 통과시켜라.")
```
완료 대기. 실패(파일 손상 등) 시 1회 재시도, 재실패면 사용자에게 보고하고 중단(SSOT 없이는 진행 불가).

## Phase 2.6: 추출 게이트 (D0.6 — 팬아웃 전 필수) [등급: DEGRADED — 1회 수복 후 강등·진행]

> SSOT가 오염되면 4렌즈·종합 전체가 무너진다. 제공 원문과 직접 대조하는 격리 검증으로 **분석가 팬아웃 전에** 차단한다(생성-검증 분리).

```
# 원문 대조 검증 코어 → opus
Agent(subagent_type="disclosure-auditor", model="opus",
      prompt="추출 게이트 모드(Part A). .claude/skills/disclosure-review/SKILL.md Part A로
      _workspace_filings/00_filings_facts.json을 제공 공시 원문과 직접 대조 검증해 _workspace_filings/00_audit.md를 작성하라.
      수치 일치·할루시네이션·단위 정규화·기간 정합·산술·출처 실재성을 점검하고 ⛔치명 0건이면 PASS.")
```
- **PASS(⛔ 0건):** Phase 3으로.
- **⛔ 발견:** filings-archivist를 **1회 재호출**해 지적된 필드만 원문에서 재추출 → 재검증. 재실패 시 해당 수치를 "미확인"으로 강등하고 하류·최종 보고에 명시. 재검증은 1회 제한.

## Phase 3: 4렌즈 병렬 해부 (D1 — 팬아웃)

**4명을 한 메시지에서 동시 호출한다**(`run_in_background: true`, 전부 `model: "opus"`). 각자 자기 렌즈만, 서로의 산출물을 읽지 않는다:

```
Agent(subagent_type="financial-statement-analyst", model="opus", prompt="00_input.md·00_filings_facts.json·제공 공시 원문을 읽고 filings-lens-toolkit 스킬(+references/financial.md)로 _workspace_filings/01_financial_report.md 작성")
Agent(subagent_type="mdna-analyst",                model="opus", prompt="00_input.md·00_filings_facts.json·제공 공시 원문(MD&A 섹션)을 읽고 filings-lens-toolkit 스킬(+references/mdna.md)로 _workspace_filings/01_mdna_report.md 작성")
Agent(subagent_type="segment-analyst",             model="opus", prompt="00_input.md·00_filings_facts.json·제공 공시 원문(부문 주석)을 읽고 filings-lens-toolkit 스킬(+references/segment.md)로 _workspace_filings/01_segment_report.md 작성")
Agent(subagent_type="risk-disclosure-analyst",     model="opus", prompt="00_input.md·00_filings_facts.json·제공 공시 원문(위험요인·주석)을 읽고 filings-lens-toolkit 스킬(+references/risk.md)로 _workspace_filings/01_risk_report.md 작성")
```

4편 완료 대기. 일부 실패 시 1회 재시도, 재실패면 그 렌즈 없이 진행(종합에 "근거 제한" 전파). 어느 보고서든 `⛔SSOT 오류` 플래그가 있으면 filings-archivist를 재호출해 SSOT를 갱신하고 Phase 3을 재실행한다.

## Phase 4: 산업 심화 (D2 — 선택)

`00_input.md`의 "산업 심화 레이어"가 요청됨일 때만 실행한다(기본은 건너뜀):
```
Agent(subagent_type="industry-analyst", model="opus",
      prompt="00_input.md·00_filings_facts.json·01_segment_report.md(+다른 렌즈)·제공 공시의 사업/경쟁 서술을 읽고
      industry-diagnostic 스킬(22질문)로 _workspace_filings/02_industry_report.md 작성.
      공시 1차, 외부 지식은 [공시 외 일반지식 — 검증 필요] 태그 필수.")
```

## Phase 5: 종합 (D3)

```
Agent(subagent_type="filings-synthesizer", model="opus",
      prompt="00_filings_facts.json·01_financial_report.md·01_mdna_report.md·01_segment_report.md·01_risk_report.md·(있으면)02_industry_report.md·00_input.md를 읽고
      filings-synthesis 스킬로 _workspace_filings/03_synthesis.md 작성. 렌즈 간 일치·상충 표 필수, 매수/매도 결론 금지, 근거 강도 표기.")
```

## Phase 5.5: 종합 red-team (D3.5)

```
Agent(subagent_type="disclosure-auditor", model="opus",
      prompt="종합 red-team 모드(Part B). disclosure-review 스킬 Part B로 _workspace_filings/03_synthesis.md를
      4렌즈·SSOT와 대조 감사해 _workspace_filings/03b_synthesis_review.md 작성. 신규주장·과대해석·상충누락·경계위반·내적일관성 점검.")
```
**재작성 루프(생성-검증, 최대 1회):** ⛔치명이면 filings-synthesizer를 1회 재호출해 해당 부분만 수정 → auditor가 해소만 재점검. 미해소·잔여는 "검토 잔여 지적"으로 최종 산출물에 보존.

## Phase 6: 산출물 정리 + 보고

1. 완성본을 `reports/{회사}_공시분석_{YYYY-MM-DD}/`에 복사: `SSOT_{회사}.json`(00), `추출검증_{회사}.md`(00_audit — 추출 게이트 감사서), 4렌즈 보고서, (있으면)`산업분석_{회사}.md`(02), `이해리포트_{회사}.md`(03 — 본체), `종합검증_{회사}.md`(03b).
   - **기계 검증 (harness doctor) [등급: DEGRADED — 사후 검증·수복 1회]:** `python scripts/harness_doctor.py --harness filings`를 실행하고 결과(`_workspace_filings/09_doctor.json`)를 `reports/{회사}_공시분석_{날짜}/닥터리포트_{날짜}.json`으로 복사한다. FAIL(필수 산출물 누락)이면 원인 산출자를 1회 재호출해 수복하고, 매매 판단 언어 경계 검출(휴리스틱 WARN)은 원문을 확인해 실제 위반이면 해당 산출자를 재호출한다. 미해소 건은 **요약 보고 최상단에 명시**한다. 사후 검증이므로 BLOCKING이 아니다 — LLM 게이트(disclosure-auditor)를 대체하지 않고 보완한다.
2. `_workspace_filings/`는 보존한다(감사 추적·부분 재실행용).
3. 사용자 요약 보고: **공시 한 줄 정체(회사·유형·기간) + 이번 공시 핵심 변화 Top 3 + 렌즈 간 핵심 상충 1개 + 다음 공시 관전 포인트 + 산출물 경로**. 면책: 이 산출물은 공시 이해 자료이며 매수/매도 판단이 아님을 1줄 명시.
   - **오케스트레이터 레드플래그 자가점검 [HARD] (보고 전):** 중계하는 핵심 수치가 — 🚩SSOT/렌즈로 역추적되는가(원문 근거) 🚩단위·기간이 맞는가(분기 vs 누적, 백만 vs 천) 🚩"이해 리포트" 경계를 넘은 매매 결론이 섞이지 않았는가 — 를 점검한다. 검증 불가하면 단정하지 말고 "미확인"으로 전달한다.
4. **쉬운 해설판 (표준 산출물 — 입문자용, 생략 금지):** report-explainer를 호출해 종합 리포트를 입문자용 companion으로 옮긴다.
   ```
   # 충실 번역(결론·수치 보존, 저부하) → sonnet
   Agent(subagent_type="report-explainer", model="sonnet",
         prompt="공시 분석 하네스 해설 모드. _workspace_filings/03_synthesis.md(필수)·00_filings_facts.json을 읽고
         plain-language 스킬로 _workspace_filings/04_plain_explanation.md를 작성하라. 수치·근거 강도를 왜곡하지 말고,
         공시용어(10-K/10-Q/MD&A/세그먼트/우발채무 등) 첫 등장 풀이 + 정확한 비유 + '이 공시에서 무엇을 읽어야 하나' 가이드 구조로. 매매 권고 추가 금지. 출력 전 충실성 자가 점검 필수.")
   ```
   완성본을 `reports/{회사}_공시분석_{YYYY-MM-DD}/쉬운해설_{회사}.md`로 복사. 실패 시 1회 재시도, 재실패면 해설판 없이 진행하고 보고에 누락 명시.
5. **팟캐스트 (반드시 묻기 — 생략 금지):** 해설판 생성 후 AskUserQuestion으로 묻는다 — "이번 공시 분석으로 이해 팟캐스트를 만들까요?" 옵션: **① 대본 + 오디오(MP3)** (NotebookLM 로그인 필요, 생성 수 분~십수 분 소요) / **② 대본만** / **③ 만들지 않음**. ③이면 아무것도 만들지 않고 6으로.
   - **대본 (①·② 공통):**
     ```
     # 선택형 저부하 산출 → sonnet
     Agent(subagent_type="podcast-producer", model="sonnet",
           prompt="공시 하네스 대본 모드. _workspace_filings/03_synthesis.md(필수)·03b_synthesis_review.md를 읽고(디테일은 4렌즈 01_financial/mdna/segment/risk_report.md), podcast-script 스킬로 _workspace_filings/05_podcast_script.md를 작성하라. 갈등 축은 4렌즈 간 일치·상충과 red-team이 남긴 논점이다. 매매 판단·종목 추천 발언 금지(이해 목적) — 결론은 '이 공시가 말하는 현재 상태' 이해로 닫는다. 하단에 NotebookLM 생성 지침 섹션 필수.")
     ```
     완성본을 `reports/{회사}_공시분석_{YYYY-MM-DD}/팟캐스트대본_{회사}.md`로 복사.
   - **오디오 (① 선택 시):** notebooklm-audio 스킬을 따른다 — `--check-only` 사전 점검(코드 2=미인증·3=미설치면 오디오 생략 + 설정 안내, 대본은 보존). 통과 시 번들 스크립트로 생성: `--out "reports/{회사}_공시분석_{YYYY-MM-DD}/팟캐스트_{회사}.mp3" --source _workspace_filings/03_synthesis.md --source _workspace_filings/05_podcast_script.md --format debate --language ko --instructions "{대본의 NotebookLM 생성 지침을 그대로}"`. 실패 시 1회 재시도, 재실패면 대본만 산출물로 보고.
6. 진화: "결과나 팀 구성에서 고치고 싶은 점이 있나요?" 한 번 묻는다(강요 금지).

## 데이터 전달 프로토콜 (파일 기반)

| 단계 | 생산자 | 파일 | 소비자 |
|------|--------|------|--------|
| 입력 | 오케스트레이터 | `00_input.md` | 전원 |
| D0 | filings-archivist | `00_filings_facts.json` (SSOT) | 전원 |
| D0.6 | disclosure-auditor | `00_audit.md` | 오케스트레이터(게이트), 사용자(감사추적) |
| D1 | 4렌즈 | `01_{financial,mdna,segment,risk}_report.md` | synthesizer, industry-analyst |
| D2 | industry-analyst | `02_industry_report.md` | synthesizer |
| D3 | filings-synthesizer | `03_synthesis.md` | auditor, report-explainer, 사용자(본체) |
| D3.5 | disclosure-auditor | `03b_synthesis_review.md` | synthesizer(재작성 신호), 사용자 |
| D4 | report-explainer | `04_plain_explanation.md` → `reports/.../쉬운해설_{회사}.md` | 사용자 |
| 6 팟캐스트(선택 — 사용자 동의 시만) | podcast-producer | `05_podcast_script.md` → `reports/.../팟캐스트대본·팟캐스트.mp3` | 사용자, notebooklm-audio 스킬 |

## 에러 핸들링

- **에이전트 실패:** 1회 재시도 → 재실패 시 그 산출물 없이 진행하고 하류·최종 보고에 누락 명시.
- **SSOT 추출 실패:** archivist 재실패면 중단(SSOT 없이는 분석 불가) — 사용자에게 공시 파일 상태를 알린다.
- **제공 파일 부재·손상:** 추측으로 메우지 않고 사용자에게 보고.
- **데이터 미수록:** 삭제·추측 금지. "공시 미수록"으로 표기해 하류 전달.
- **상충 데이터:** 어느 쪽도 지우지 않고 출처(공시 위치) 병기.
- **⛔SSOT 오류:** archivist 1회 재호출 → SSOT 갱신 → 하류 재실행.
- **외부 호출 유혹 차단:** 어떤 에이전트도 제공 파일 밖에서 수치를 가져오지 않는다(산업 레이어의 태그된 일반지식만 예외).

## 테스트 시나리오

**정상 흐름(미국 10-Q):** "sources/IR-Micron의 Micron 10-Q 분석해줘" → Phase 0(초기) → 입력 기록(US, 10-Q, 산업 미요청) → SSOT 추출(제공 PDF만) → 추출 게이트 PASS → 4렌즈 병렬 해부 → (산업 건너뜀) → 종합 이해 리포트 → 종합 red-team(적정) → reports/ 정리 + 요약 보고 → 쉬운 해설판.

**산업 심화 흐름:** "...10-Q 분석하고 산업까지 깊게" → 입력에 산업 요청 기록 → ... 4렌즈 후 industry-analyst 가동(22질문, 외부 지식 태그) → 종합에 산업 맥락 장 포함.

**추출 게이트 차단 흐름:** archivist가 "백만 달러"를 "천 달러"로 오인(1000배 축소) → 추출 게이트가 원문 대조로 단위 오류 ⛔ 적발 → archivist 1회 재추출(단위 수정) → 재검증 PASS → 정상 진행.

**상충 발견 흐름:** MD&A 렌즈는 "수요 강세" 강조하나 segment 렌즈는 핵심 부문 역성장, risk 렌즈는 신규 소송 → 종합가가 §4 상충 표에 나란히 제시 → red-team이 "상충 누락 없음, 균형 적정" 확인 → 사용자에게 상충을 핵심 정보로 보고.

**부분 재실행 흐름:** "재무 렌즈만 다시" → Phase 0(부분) → financial-statement-analyst만 재호출 → 종합부터 하류(종합·red-team·해설) 갱신 → 보고.

**한국 DART 흐름:** "삼성전자 분기보고서 분석"(sources/에 DART 보고서) → 입력(KR) → archivist가 kr-filings.md 매핑으로 연결재무제표·백만원 단위 정규화 → 이후 동일.

**에러 흐름:** mdna 렌즈가 재시도까지 실패 → 3렌즈로 종합(종합가가 "경영진 서술 관점 부재" 명시) → red-team이 한계 확인 → 정상 종결, 최종 보고에 누락 명시.
