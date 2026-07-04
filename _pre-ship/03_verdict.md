# 독립 검증 판정 — 1회차 (2026-07-03)

**대상:** 2026-07-03 하네스 감사 보완 구현 (트레이딩·IPO·공시 3하네스 정의 자산, 미커밋 변경분)
**방법:** 격리 검토자 5명 병렬(critic×2·code-reviewer·verifier×2, opus, 상호 격리·작업 맥락 미공유) → 메인 타당성 게이트(전 지적 원문 재확인) → 수용분 반영
**결과 파일:** `02_findings_{critic-wiring, critic-numbers, reviewer-ipo, verifier-loop, verifier-filings}.md`

## 집계: 🔴 1 · 🟡 13 · 🟢 11 (중복 제외)

## 타당성 게이트 판정 및 조치

### ✅ 수용 → 반영 완료 (19건)
| # | 출처 | 지적 | 조치 |
|---|------|------|------|
| 1 | verifier-loop 🔴 | 학습 코퍼스(decisions/) 전체 무버전 — 규칙 4곳 실재하나 실행 0 | `git add decisions/ && git commit` 실행 (이 판정서 직후) |
| 2 | critic-wiring 🟡 | REVISE 루프가 portfolio-risk-analyst 재호출 안 함 → 05_portfolio_impact 스테일 | trading-strategy:147·risk-gate:71에 "비중 변경 시 편입 후 재계산 1회 재호출" 배선 |
| 3 | critic-wiring 🟡 | Phase 7 복사 목록에 05_portfolio_impact 누락 | 복사 목록에 포트폴리오영향·팩트체크(있으면) 추가 |
| 4 | critic-numbers 🟡 | :251 워크드 예시가 집계 한도(10%)에 캠페인 한도(2%)를 잘못 라벨 | 예시를 "신규 캠페인 꼬리 검산 -3.1%(2%) + 동시 꼬리 합 -11%(10%)"로 분리 정정 |
| 5 | critic-numbers 🟡 | IPO 확신도 앵커(공모가 대비/방향)와 calibration 채점(벤치마크 알파) 사건 불일치 | IPO 앵커를 "상장 후 12개월 내 벤치마크 대비 초과수익 확률"로 통일 — investment-judge SKILL:41,69 + report-schema:59,110 |
| 6 | reviewer-ipo 🟡 | 단계 번호 삼중 불일치(에이전트 3.5/3.7/3.9단계 vs Phase 4.5/4.7/4.8 vs 표 1/2/3) | Phase 체계로 통일 — 헤더 "N단계" 제거, 표 2/3/4, 에이전트 7종 description 정정 |
| 7 | reviewer-ipo 🟡 | fact-checker.md:45 IPO에 없는 "주가·밸류에이션 배수" 검증 지시 | IPO 필드(공모가·상장후 주식수·free float 4필드·락업 등)로 치환 |
| 8 | reviewer-ipo 🟡 | investment-judge.md:15 "밸류에이션 배수" SSOT 잔재 | IPO 필드로 치환 |
| 9 | reviewer-ipo 🟡 | data-collector.md:21 "벤치마크·밸류에이션 배수만" 자기모순(+:7 제목) | IPO 스냅샷 필드로 치환, 제목 "IPO 데이터 수집가" |
| 10 | reviewer-ipo 🟡 | execution-strategist.md:46 에러 핸들링이 "현재가" 전제 | "기준가(상장 전=공모가/상장 후=현재가)"로 분기 |
| 11 | reviewer-ipo 🟢 | verdict-reviewer.md:47,49 출력 열거에 ⑨/ⓗ 생략 | "8축+⑨", "…편향+ⓗ" 추가 |
| 12 | verifier-loop 🟡 | 확신도 버킷 경계 미정의 | calibration.md에 고정 경계(<50/[50,60)/…/[90,100], 좌폐우개) + p 사건 정의·관망 환산 규칙 명시 |
| 13 | verifier-loop 🟡 | IPO 저널 포맷에 실행: 필드 부재(첫 체결 시 기록 경로 없음) | journal.md IPO 템플릿에 `실행:` 줄 추가 + 헤더 "실행·결과 줄만 갱신 가능"으로 정정 + ipo-analysis:133 기록 항목에 실행 추가 |
| 14 | verifier-loop 🟢 | ipo-reflection에 자체 커밋 단계 없음(비대칭) | step 7 커밋 추가 |
| 15 | critic-numbers 🟢 | 사이징 산식 분모 0 가드 부재 | trade-planning에 "산식 성립 조건(분모>0)" 추가 |
| 16 | critic-numbers 🟢 | research-debate:83 예시 지평 "6~12개월" 드리프트 | 표준 앵커 "12개월"로 정렬 |
| 17 | critic-numbers 🟢 | ipo-reflection:43 calibration 열 라벨 축약 | `확신도(p)`/`결과(o: 1/0.5/0)`로 정렬 |
| 18 | verifier-filings 🟢 | filings-analysis 도식에 팟캐스트 단계 누락 | 도식에 `[선택] podcast-producer` 줄 추가 |
| 19 | critic-wiring 🟡 부속 | :251 테스트 시나리오가 재계산 없이 "해소 확인" | 시나리오에 "portfolio-risk-analyst 편입 후 재계산" 삽입(#4와 동일 편집) |

### ⏸️ 보류 — 사용자 확인 안건 (2건)
- **calibration 백필** (verifier-loop 🟡): 삼성·NVDA 복기 완료분의 calibration 1행이 비어 있음(대장이 복기보다 늦게 신설된 탓). 과거 판정의 p/o 채점은 데이터 생성이라 자동 반영 범위 밖 — 복기 보완 실행(portfolio-manager 복기 모드) 승인 여부를 사용자에게 묻는다.
- **07/08 파일 번호 역전** (critic-wiring 🟢): 08_plain이 07_podcast보다 먼저 생성. 번호는 유형 식별자이고 기존 산출물·참조와 얽혀 있어 개명 리스크 > 이득 — 유지 권고.

### ❌ 기각 (근거 재확인 결과 실질 결함 아님, 5건)
- "14명 6계층" 카운팅(verifier-filings 🟢): 공용 에이전트 포함 방식의 서술 근사 — 사실 오류 아님.
- 손절 은유 톤(reviewer-ipo 🟢): execution-strategist 본문 :25,36이 명시 교정 — 실질 무해.
- report-schema 기본 헤더 2차 시장(reviewer-ipo 🟢): IPO 변형(:93-121) 체인 정상.
- pending 결산 자동 집계 부재(verifier-loop 🟡): trading-strategy:49가 이미 복기 제안을 배선("같은 티커면 복기 먼저 권한다") — 확정·집계를 복기에만 두는 것은 설계 의도(결과론 차단).
- 기존 저널 인스턴스의 실행:/기회비용 줄 부재(verifier-loop 🟡 일부): 포맷 후행 신설 + 전 항목 미체결 — append-only 원칙상 소급 수정 대상 아님.

### 미해소 관찰 (결함 아님, 기록)
- 포트폴리오 레이어(Phase 5 병렬 4+1)가 실전 실행으로 검증된 적 없음(현 _workspace/에 05_portfolio_impact 부재) — 다음 실전 실행에서 확인 권장.
- _workspace_prev/ 평면 파일·_archive/ 구접미사 폴더는 과거 관행 잔재(감사추적 보존, 규칙은 향후 적용).

## 다음 단계
1. **독립 검증 2회차**: 이번 수정 19건을 대상으로 격리 검토자 재소집(신규 에이전트 — 회귀·수정 정합 확인) → 타당성 게이트 → 판정 확정. → **아래 2회차 섹션으로 완료(2026-07-04)**
2. 사용자 최종 확인(보류 2건 포함) → **Mermaid 전체 구조 다이어그램**.

---

# 독립 검증 판정 — 2회차 (2026-07-04)

**대상:** 1회차 수용 19건의 반영 결과(반영 정합·회귀) + 1회차 렌즈 밖 잔여 결함
**방법:** **신규** 격리 검토자 4명 병렬(verifier×2·critic×2, 전원 opus, 상호 격리·1회차와 별개 인스턴스 — r2-verifier-trading·r2-verifier-ipo·r2-critic-regression·r2-critic-fresh) → 메인 타당성 게이트(전 지적 원문 재확인) → 수용분 반영
**결과 파일:** `01_target_r2.md`, `02_findings_r2_{verifier-trading, verifier-ipo, critic-regression, critic-fresh}.md`

## 1회차 반영 정합 판정: **19/19 반영됨 · 회귀 0건**
- r2-verifier-trading: 트레이딩 계열 9항목 전부 반영됨(커밋 b6cbc8a 실물, 재계산 배선 3파일 정합, 한도 분리, 분모 가드, 12개월 앵커, calibration 스펙, journal 실행 필드). 편집 지점 ±30줄 회귀 없음.
- r2-verifier-ipo: IPO·공시 계열 11항목 전부 반영됨(확신도 앵커 통일, Phase 체계 grep 0건 잔재, fork 잔재 4건 소거, ⑨/ⓗ, 커밋 스텝, 라벨, 팟캐스트 도식). 대상 10파일 전문 정독 회귀 없음.
- r2-critic-regression: 정의 자산 diff 전량 정독 + 전수 grep — 끊긴 배선·모순 규칙·없는 산출물 참조 0건. "잘 실행된 정합성 수정 패스" 판정.

## 신규 지적 집계(중복 제거): 🔴 0 · 🟡 4 · 🟢 8

## 타당성 게이트 판정 및 조치 (2회차)

### ✅ 수용 → 반영 완료 (9건)
| # | 출처 | 심각도 | 지적 | 조치 |
|---|------|--------|------|------|
| R2-1 | critic-fresh F1 | 🟡 | 트레이딩 저널 append 계약 충돌(risk-gate REVISE 행만 저널 미명시 vs PM·오케스트레이터 무조건 기록) → journal에 REVISE·APPROVE 이중 항목 실재(NVDA·MKIF·MU), pending 결산 이중 계상 위험 | **REVISE 중간 판정 규칙 신설** — risk-gate 저널 포맷(append 직후 `결과:` 줄 `[REVISE — 최종 확정은 후속 항목에 기록]` 즉시 기입, REVISE·최종 쌍=1결정, 집계는 최종만) + REVISE 행 "저널 기록" 명시 + portfolio-manager.md:29 동일 규칙 |
| R2-2 | critic-fresh F2 | 🟡 | IPO 부분 재실행 체인이 Phase 6 미도달 → 판정 바뀌어도 저널·reports 스테일(트레이딩과 정반대 비대칭) | ipo-analysis:25에 **Phase 6 재진입 규칙** 신설(판정/계획 변경 시 reports 재복사 + 저널 정정 항목 append + 기존 항목 `결과:` 줄 `[대체됨 →]` + 커밋) + :213 테스트 시나리오 정합 |
| R2-3 | critic-fresh F3 | 🟡 | "보유 등록" 경로가 portfolio.json만 갱신 → journal `실행:` 미체결 방치로 복기 오채점 가능(이중 기록원 어긋남) | trading-strategy Phase P "보유 등록/갱신"에 열린 journal 항목 `실행:` 줄 동시 갱신 규칙 추가 |
| R2-4 | critic-fresh F4 + verifier-trading 🟡 | 🟡 | 복기가 calibration 1행 추가를 명령하나 수행 검증 게이트 부재 — 실측: 복기 확정 6건인데 calibration 대장 0행 | trading-strategy Phase R·ipo-analysis Phase R에 **커밋 전 calibration(IPO는 journal·lessons 포함 3파일) 실제 갱신 확인 게이트** 추가(누락 시 1회 보완 지시). 백필 자체는 보류 안건(아래) |
| R2-5 | critic-regression 사소-1 | 🟢 | ipo-analysis:154 "Phase 6-7 진화" — 존재하지 않는 Phase 7 참조(이번 편집이 신규 도입한 라벨 오류) | "진화:"로 정정(Phase 라벨 제거) |
| R2-6 | critic-regression 사소-2 = verifier-ipo 🟢 | 🟢 | ipo-analysis:20 "1단계부터 전체 실행" 구 라벨 잔재 | "Phase 1부터 전체 실행" |
| R2-7 | critic-regression 사소-3 | 🟢 | data-sources.md:37 "밸류에이션 배수" 수집 지시가 상단 신규 SSOT 절과 긴장(불완전 청소) | "비교기업(comps)의 … (대상 IPO 기업 자체엔 거래 멀티플이 없다 — comps·공모가 기준 환산만)"로 명확화 |
| R2-8 | verifier-ipo 🟢 | 🟢 | verdict-review:86·verdict-reviewer:39 확신도 루브릭이 일반형 템플릿 제시 — 표준 앵커와 미세 불일치 | 수정 제안 문구를 표준 앵커(+병기 규칙)로 교체, 검토관 원칙에 표준 앵커 병기 점검 추가 |
| R2-9 | critic-fresh G1 | 🟢 | 트레이딩 Phase 1.6 게이트가 macro/snapshot "한쪽만 생성" 케이스 미규정 | "한쪽만 생성이면 있는 파일만 점검(없는 파일 '미생성' 명시, 스냅샷 의존 항목 생략)" 추가 |

### ⏸️ 보류 — 사용자 확인 안건 (1회차 2건 + 갱신)
- **calibration 백필 (범위 갱신):** 1회차에 "삼성·NVDA 2행"으로 알았으나 2회차 실측 결과 **복기 확정 6건**(삼성 58%·SPCX 70%·SPCX 64%·NVDA 60%·MKIF 60%·SOL 62%, 전부 `[복기 2026-06-26]`)이 대장에 미기입. SPCX 70% 항목은 "진입 불가로 봉인·최종 복기는 64% 항목"이라 실질 백필 대상은 **5행**. 실행 여부 사용자 확인.
- **07/08 파일 번호 역전:** 유지 권고(1회차와 동일).

### ❌ 기각 (2건)
- execution-strategist.md:9 "손절" 서두 잔재(verifier-ipo 🟢): **1회차 기각 건과 동일 사안 재지적** — 새 근거 없음(:36이 "IPO엔 손절가를 쓰지 않는다"로 명시 교정, 검토자 스스로 실무 충돌 없음 인정) → 재기각.
- journal 기존 항목의 "6~12개월" 표기(verifier-trading 🟢): append-only 규약상 의도된 상태(기존 항목 소급 수정 금지) — 1회차 기각 5번과 동일 논리. 결함 아님.

### 미해소 관찰 (결함 아님, 기록)
- **다티커 동시 운용 vs 워크스페이스 회전 규칙**(critic-fresh G2): 회전 규칙이 단일 티커 전제인데 `_workspace/`에 `_entry_2026-07-03_{AGNC,MKIF,SOLAI}` 임시 스테이징 폴더가 정의 밖으로 실재(생성 주체 미확인). 같은 날 배치 운용을 지원하려면 설계 결정 필요 — 사용자 안건으로 승격 가능.
- F3(보유 등록 경로)은 현재 portfolio.json `holdings:[]`라 미발현 — 규칙은 이번에 봉합됨.
- IPO 워크스페이스 회전은 트레이딩과 달리 단순 `_workspace_ipo_prev/`(critic-regression 관찰) — 회귀 아님, 필요 시 향후 정렬.

## 최종 판정
**✅ 통과(조건부)** — 🔴 0. 1회차 수용 19건 전부 반영·회귀 없음이 3검토자 교차 확인됐고, 2회차 신규 🟡 4건은 전부 이번 세션에서 봉합. 남은 것은 실행 안건(calibration 백필)과 커밋 결정뿐.
**검사 범위/한계:** 정의 자산(.claude/·CLAUDE.md·decisions/) 정적 검증만 — 런타임 파이프라인 실행 검증 아님. filings 하네스 신규(untracked) 파일 내부 배선은 이번 범위 밖(critic-regression 명시). raws/·_workspace*/ 산출물은 검증 제외.
