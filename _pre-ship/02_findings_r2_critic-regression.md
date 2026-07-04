# 회귀 감사 최종 보고 (r2-critic-regression, 2026-07-04 — 회귀·구용어 잔재 사냥)

**판정: 회귀 없음 — 🔴0 / 🟡0 / 🟢3.** 이번 편집 묶음은 잘 실행된 정합성 수정 패스다. 사냥 대상(끊긴 표·중복 문장·모순 앵커·댕글링 교차참조·정의 자산의 구용어 잔재)은 거의 전부 부재했다. 확신도 앵커 통일("12개월 벤치마크 초과수익")이 6개 정의 파일에 일관 반영됐고, 교차 배선(05_portfolio_impact·00_factcheck·`실행:` 필드·calibration·"삼성 사례")은 전부 실재·정합한다. 남은 것은 실행에 지장 없는 문서 라벨 잔재 3건뿐이다.

---

## ① 발견 결함 목록 (심각도순)

**🟢 사소-1 — `ipo-analysis/SKILL.md:154` "Phase 6-7 진화" 라벨 오류 (이번 편집이 신규 도입)**
- 근거: diff에서 `-7. Phase 7 진화` → `+7. Phase 6-7 진화`로 바뀜. 그러나 IPO 하네스의 마지막 번호 단계는 **Phase 6**이고 그다음은 Phase R(복기)다 — **Phase 7은 없다**(있는 건 트레이딩 하네스). 원본 "Phase 7"은 fork 잔재였는데 "6"이 아니라 "6-7"로 고쳐 여전히 없는 Phase를 가리킨다.
- 왜 문제: 최종 보고 말미 "고치고 싶은 점?" 질문 항목 라벨이 존재하지 않는 단계를 참조. 실행 무영향(코스메틱). 권고: "Phase 6 진화" 또는 라벨 삭제.

**🟢 사소-2 — `ipo-analysis/SKILL.md:20` "1단계부터 전체 실행" 구 라벨 잔재**
- 근거: Phase 0 모드 표 셀. 이번 편집이 섹션 헤더의 "1단계/2단계/3단계" 보조 라벨을 전부 제거해 "Phase N" 체계로 통일했는데, 이 표 셀만 구 "N단계" 표현이 남음. 같은 표 인접 행은 "처음부터"(:21)·"해당 단계만"(:22)을 쓴다.
- 왜 문제: 의미 전달엔 지장 없으나 파일 내 번호 체계 통일성이 깨짐. 권고: "Phase 1부터".

**🟢 사소-3 — `ipo-analysis/references/data-sources.md:37` `밸류에이션 배수` 2차 시장 잔재 (신규 절과 경미 긴장)**
- 근거: 이번 편집이 같은 파일 상단 SSOT 절에 "2차 시장의 주가·PER·P/S·EV/EBITDA 같은 거래 멀티플은 IPO 스냅샷에 없다"를 명시 추가했는데(diff), §2 미국 데이터 소스 :37은 여전히 "웹 검색으로 … P/E·P/S·EV/EBITDA 등 **밸류에이션 배수**" 수집을 지시 — 상단 신규 절과 미세 충돌.
- 왜 문제: SSOT 절 청소는 완료했으나 병렬 "재무 데이터" 수집 지침에서 동일 언어를 놓친 **불완전 청소**. 다만 IPO 밸류에이션은 comps·공모가 기준 멀티플을 정당하게 쓰므로 명백한 오류는 아님(영향 낮음).

*(참고 — 결함 아님, 비대칭·개선 여지)*
- IPO Phase 5 공백(4.8 → 6, Phase 5 없음): pre-existing 코스메틱. 편집 전에도 데이터 표가 `3.9 → 6`으로 건너뛰었음 → 회귀 아님.
- 워크스페이스 회전 규칙 비대칭: 트레이딩은 `_workspace_prev/{티커}_{날짜}/` + 5개 초과 시 `_archive/` 이동 규칙을 얻었으나 IPO는 여전히 단순 `_workspace_ipo_prev/`. 2026-07-03 IPO 변경 이력이 회전 규칙을 주장하지 않아 회귀 아님.
- IPO 저널 `실행:` 필드 갱신은 IPO에 Phase P가 없어 "트레이딩 하네스 Phase P와 동일 경로"에 의존(journal:15에 문서화됨). 하네스 간 결합이나 결함 아님.
- fact-checker: 파일에서 모드 2(트레이딩)가 모드 1(IPO, "기본")보다 물리적으로 먼저 배치됨 — 가독성 quirk, 결함 아님.

---

## ② 문제없음을 확인한 범위 (무엇을 어떻게)

- **정의 자산 diff 전량 정독**: CLAUDE.md, 오케스트레이터 2종(trading-strategy·ipo-analysis), 편집 스킬 14종(risk-gate·trade-planning·trade-reflection·ipo-reflection·contrarian-check·investment-judge·verdict-review·bull-case·bear-case·research-debate·macro-regime·market-snapshot·plain-language + references data-sources·report-schema), 편집 에이전트 13종. 편집 지점 원문 맥락을 각각 확인.
- **Phase 번호 체계**: `[0-9]단계`·`Phase [0-9]\.[0-9]` grep. IPO 데이터 표가 `3.5/3.7/3.9` → `4.5/4.7/4.8`로 헤더에 맞춰 수정된 것 확인(기존 불일치 해소). 에이전트 description 전부 정합. 잔존 구 "N단계"는 사소-2 1건뿐.
- **확신도 앵커**: investment-judge·research-debate·risk-gate 저널 포맷·report-schema·research-manager·portfolio-manager + calibration.md p 사건 정의 대조 — "12개월 벤치마크 초과수익"으로 통일 확인. 정의 자산의 "6~12개월" 잔재 0건(journal·reports·docs·_workspace 히트는 append-only 역사기록·산출물이라 결함 아님).
- **교차 배선**: 05_portfolio_impact.md, 00_factcheck.md, `실행:` 필드, calibration.md 포맷(b6cbc8a 커밋 실물), portfolio-risk-analyst 재호출 지침(:43) ↔ risk-gate REVISE 행 ↔ trading Phase 6 REVISE 루프 — 전부 일관.
- **2차 시장 언어 잔재**: `밸류에이션 배수`·`손절가`·`현재가` grep. IPO 컨텍스트는 전부 부정문("IPO엔 없다") 처리 확인. market-data-engineer·fundamental-analyst의 `밸류에이션 배수`는 트레이딩 하네스라 정당(오검출). 실 잔재는 사소-3 1건.
- **교차참조 정확성**: "삼성 사례"(contrarian-check:40·risk-gate:187·portfolio-manager:302·research-manager) → lessons.md:45-48에 실재하며 인용 수치까지 일치. verdict-review Part B ⓑ의 `ipo-timing:96` 인용 → 해당 줄이 실제 명시하는 것 확인.
- **b6cbc8a 커밋(decisions/)**: journal.md 헤더·IPO 포맷·`실행:` 필드, calibration.md 버킷 경계·p 사건 정의, lessons.md 삼성 교훈 실물 확인.

---

## ③ 못 본 것 (미확인 범위)

- **분석 산출물·원문(`_workspace*/`, `reports/`, `raws/`, `_archive/`)**: diff 대부분(70,832 삭제)이 여기 몰려 있으나 임무 범위(정의 자산)가 아니라 정독하지 않음. 이 파일들의 "6~12개월"·"손절가"는 과거 실행 산출물이라 정의 결함 아님(검증 제외 판정).
- **filings 하네스 신규 파일(untracked)**: filings-analysis 스킬·filings 에이전트 8종은 미추적 상태로 이번 diff에 없음. CLAUDE.md 서술과 podcast-producer/report-explainer/plain-language의 filings 분기가 이 미추적 파일들과 정합하는지는 **미확인**(파일 실재만 git status로 확인, 내부 배선 미검증).
- **`docs/anti-hallucination-verification-plan.md` 실재 여부**: 다수 편집이 이 경로를 인용하나 파일 존재 미확인.
- **runtime 동작**: 정적 텍스트 정합만 검증, 실제 파이프라인 실행 안 함(읽기 전용 임무).

**요약: ACCEPT. 반려 사유(끊긴 배선·모순 규칙·없는 산출물 참조) 없음. 남은 3건은 전부 라벨/문구 잔재로 실행 무영향 — IPO SKILL.md:154·:20, data-sources.md:37 3곳만 1회 정리 편집으로 마감 가능.**
