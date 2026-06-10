# SpaceX IPO 투자 분석 하네스 — 구축 계획 (v2, Codex 비판검증 반영)

> 작성일: 2026-06-09 · 대상: SpaceX(SPCX) IPO (2026-06-12 상장) · 시드 입력: `spcx.txt`
> 결정: ① spcx/ 전용 자체완결 ② 산출물 분석+전략 7종(팟캐스트 제외) ③ 구축+검증만(실분석 별도)
> v2 변경: Codex 독립 비판검증(2026-06-09) 반영 — 7개 지적 중 🔴3·🟡3 수용, 🟡1 부분수용

---

## 0. v1 → v2 핵심 변경 (왜 바뀌었나)

v1의 핵심 가정 **"2차 시장 로직 2곳(snapshot·timing)만 IPO용으로 바꾸면 된다"** 는 과소평가였다. IPO에는 거래 히스토리·애널리스트 컨센서스·과거 멀티플·시장 가격이 **없고**, 결론은 공모 배정·첫 거래 가격발견·유통물량·안정조작·락업·지수편입·**한국 투자자 실제 접근성**이 지배한다. 따라서:

1. **IPO 모드 분기 대상 확대**: snapshot·timing뿐 아니라 `report-schema`, `bull-case`, `bear-case`, `investment-judge`, `verdict-review`까지 IPO 모드로 분기한다.
2. **ipo-timing 재설계**: "상장일 시장가 매수 비중"이 아니라 "배정 가능성 → 상장일 주문 가능성 → 첫 거래 후 유동성 → 안정조작 종료 → 락업/지수 이벤트" 순서.
3. **free_float 정합성**: 보도 7%와 신주 4.24%의 모순을 단일 값으로 박지 않고 4개 필드로 분리·재대조.
4. **데이터 최신성**: 구버전 S-1 하드코딩 금지, EDGAR 최신순 탐색 + preliminary/final 상태 명시.
5. **검증 강화**: 스냅샷 직후 audit 단계, 숫자 모순은 하드 실패(재수집), 검증에 실제 스냅샷 스모크 테스트 포함.
6. **fork 드리프트 완화**: upstream 동기화 매니페스트 추가(fork 결정은 유지).

---

## 1. 목표

SpaceX IPO를 **강세(Bull)·약세(Bear) 적대적 분석 → 팩트체크 검증 → 종합 심판(Judge) → 판결 red-team → IPO 진입 타이밍 전략 → 전략 red-team**까지 자동 산출하는 IPO 특화 파이프라인을 `spcx/.claude/`에 구축한다. 기존 `Stud_stock_analyzer/` 하네스를 베이스로 가져오되 **IPO 모드로 분기**한다.

---

## 2. 재사용 vs IPO 모드 분기 매트릭스 (v2)

| 자산 | 종류 | 처리 | IPO 모드에서 바뀌는 것 |
|------|------|------|----------------------|
| `bull-analyst` | 에이전트 | 재사용 | 프롬프트에 IPO 모드 지시 |
| `bear-analyst` | 에이전트 | 재사용 | 프롬프트에 IPO 모드 지시 |
| `fact-checker` | 에이전트 | 재사용 + IPO 소싱 | EDGAR 최신순 탐색, preliminary/final 구분, 스냅샷 숫자 재계산 |
| `investment-judge` | 에이전트 | 재사용 | IPO 판정 프레임 지시 |
| `verdict-reviewer` | 에이전트 | 재사용 | IPO 체크 항목 추가 |
| `data-collector` | 에이전트 | 재사용 + IPO 인지 | ipo-snapshot 스킬 호출 + 숫자 self-check |
| `execution-strategist` | 에이전트 | **IPO 모드 추가** | ipo-timing 스킬 호출 |
| `market-snapshot`→**`ipo-snapshot`** | 스킬 | **신규** | §4 |
| `execution-strategy`→**`ipo-timing`** | 스킬 | **신규** | §5 |
| `bull-case` | 스킬 | **IPO 모드 분기** | 현재가/PER/기술적지표 → SOTP·EV배분·옵션프리미엄·메가IPO 비교·지수수급(§5.5) |
| `bear-case` | 스킬 | **IPO 모드 분기** | 락업 오버행·free float 변동성·안정조작 종료·key-man·옵션프리미엄 지배(§5.5) |
| `investment-judge`(스킬) | 스킬 | **IPO 모드 분기** | "12개월 BUY/HOLD/SELL+목표가" → IPO 판정 프레임(§5.5) |
| `report-schema`(references) | 스킬참조 | **IPO 변형 추가** | 현재가·목표가·손절가·reward/risk → 공모가·가치앵커·진입구간·가설훼손(§5.5) |
| `verdict-review` | 스킬 | **IPO 분기(Part A·B)** | 판결/전략 감사에 IPO 정합성 축 추가(§5.5) |
| `fact-check` | 스킬 | 재사용 + IPO 소싱 규칙 | §4 소싱 규칙 |
| `investment-analysis`→**`ipo-analysis`** | 오케스트레이터 | **spcx 튜닝 복제** | 팟캐스트 제거, 스냅샷 audit·IPO 단계 반영 |
| `podcast-*`, `notebooklm-audio` | 에이전트·스킬 | **제외** | — |

---

## 3. 파이프라인 (spcx 전용, v2)

```
[입력] spcx.txt(시드) + EDGAR 최신 S-1/A·FWP·최종 투자설명서 + 신뢰 보도
  │
  Phase 0   컨텍스트 확인 (_workspace/ 초기/새/부분 재실행)
  Phase 1   입력 수집 → 00_orchestrator_input.md (분석시점·상장일·시드 요약)
  Phase 1.5 data-collector → 00_ipo_snapshot.json   [ipo-snapshot] + 생산자 숫자 self-check
  Phase 1.6 스냅샷 audit (fact-checker 우선검증) → 숫자 모순/free_float 미정합 시 ⛔하드 실패 → 재수집
  │
  Phase 2   bull-analyst ∥ bear-analyst (격리·적대적, IPO 모드)
  Phase 3   fact-checker → 02_factchecker_annotations.md (EDGAR 최신순, preliminary/final 명시)
  Phase 4   investment-judge → 03_judge_verdict.md (IPO 판정 프레임 + 확신도 정의)
  Phase 4.5 verdict-reviewer(판결 모드) → 03b (⛔치명 시 1회 재작성)
  │
  Phase 4.7 execution-strategist(IPO 모드) → 03c_ipo_entry_plan.md  [ipo-timing]
  Phase 4.8 verdict-reviewer(전략 모드) → 03d (⛔치명 시 1회 재작성)
  │
  Phase 6   산출물 정리 → reports/SpaceX_2026-06-09/ (7종) + _workspace/ 보존 + 요약 보고
```

**하드 실패 규칙(신규):** 스냅샷 단계의 **숫자 모순**(시총≠주가×주식수, free_float 미정합 등)은 "잔여 리스크"로 넘기지 않고 산출을 실패 처리 → data-collector 재수집(숫자는 의견이 아니라 결정적 값이므로 반복 허용). 판단·추론 수준 결함만 1회 재작성 루프 + 잔여 지적 표기.

---

## 4. 신규 ① `ipo-snapshot` 스킬 (data-collector용, v2)

**산출:** `_workspace/00_ipo_snapshot.json`. 모든 수치 `{value, currency, as_of, source, source_doc, source_status, confidence}` (`source_status`: `"preliminary"|"final"|"press"|"estimate"`).

### 4-1. 소싱 규칙 (하드코딩 금지)
- **EDGAR accession 최신순 탐색** 후 우선순위: 최종 투자설명서(424B) > S-1/A > FWP > 초기 S-1 > 보도.
- spcx.txt 값은 **시드**일 뿐. 1차 출처로 교차 검증하고, 시드와 다르면 1차 출처 채택 + 차이 기록.
- 상장 전(6/11 이전)이면 모든 가격 관련 값은 `source_status: preliminary`로 명시.

### 4-2. 핵심 필드
- `listing`: exchange(Nasdaq/Nasdaq Texas), pricing_date(2026-06-11, preliminary), trading_start(2026-06-12), ipo_price($135, preliminary), shares_offered_new(555.6M, 100% primary), greenshoe(83.3M), gross_proceeds_est(~$75B)
- `post_ipo_shares`: class_a(7,488,063,555) / class_b(5,602,790,410) / total(13,090,853,965) / total_with_greenshoe(13,174,187,298)
- `valuation`: market_cap_at_ipo(~$1.767T) / with_greenshoe(~$1.779T)
- **`free_float` (4필드 분리 — 단일 값 금지):**
  - `base_offering_float`: 신주only 555.6M / 13.0909B = **4.24%**
  - `with_overallotment_float`: (555.6M+83.3M) / 13.1742B = **4.85%**
  - `reported_float_claim`: ~7% (출처: Reuters, status: press) — 신주만으로는 설명 안 됨(약 360.8M주 갭)
  - `reconciliation_required`: true + note(보도 7%와 공모 4.24%의 차이를 fact-checker가 규명)
- `lockup`: musk(366일) / select(2026 Q4 실적 후~2027 Q2 실적 후 단계적) / other(2026 Q2 실적 후~IPO+180일 조기 단계적) / registration_rights(~9.2B주) / **rule144_after90d(~12.2B주, "단 별도 락업 제한 적용 — 90일 후 전량 자유유통 아님")**
- `index_inclusion`: MSCI 조기편입 가능성(status: estimate)
- `segment_financials`: Connectivity 2025 매출($11.4B)·Adj EBITDA($7.2B)·영업이익($4.4B), Q1 2026 Adj EBITDA($2.1B)·영업이익($1.2B), Starlink 가입자(~10.3M, 2026 Q1)
- `use_of_proceeds`: AI 컴퓨팅 인프라 / 발사 인프라·발사체 / 위성망 확장

### 4-3. 생산자 숫자 self-check (산출 직후 JSON에 기록)
- `market_cap ≈ ipo_price × total_shares` (오차 <1%) 확인
- `gross_proceeds ≈ ipo_price × shares_offered_new` 확인
- free_float 3종 재계산값 명시 + reported_claim과의 갭 명기
- 실패 시 `self_check: FAIL` → Phase 1.6에서 하드 실패 트리거

---

## 5. 신규 ② `ipo-timing` 스킬 (execution-strategist용, v2 재설계)

2차 시장처럼 "현재가 기준 진입·손절"이 아니라 **IPO 실행 구조 순서**로 설계한다.

### 5-1. 실행 가능성 게이트 (먼저 답해야 할 것)
- **공모가 확정 전/후 구분**: 6/11 가격 확정 전엔 진입가 자체가 미정 → 시나리오로만.
- **한국 개인투자자 접근성(필수 체크리스트):**
  - 증권사별 미국 신규상장 종목 **거래 가능 시점**(상장 당일 즉시 vs 수일 지연 — 증권사마다 다름)
  - 청약 배정 가능성(국내 리테일은 일반적으로 미국 IPO 공모 배정 곤란 → 사실상 상장 후 시장가 매수)
  - 환전(원→달러) 마감 시간 / 통합증거금 여부
  - 미국 정규장 시간대(한국 야간), 프리마켓 매수 가능 여부
  - 미국 주식 **T+1 결제**, 양도세(22%, 연 250만원 공제)
- 이 게이트에서 "상장일 매수 불가/지연"이면 진입 전략의 1차 구간 자체가 무효 → 후속 구간 중심으로 재배치.

### 5-2. 가격발견·안정조작 인지
- **Nasdaq IPO Cross**: 첫 거래가는 단일 개장가격 형성 메커니즘으로 결정 → 시초가 변동성·주문 유형 주의.
- **IPO halt / 변동성 정지** 가능성.
- **인수단 greenshoe 안정조작**: 상장 초기 인위적 가격 지지 구간이 끝나면 하방 압력 가능 → 진입 타이밍에 반영.
- when-issued/그레이마켓 신호(있으면 참고).

### 5-3. 이벤트 기반 분할 진입 (실행 게이트 통과 가정)
| 구간 | 비중(예시) | 핵심 판단 |
|------|-----------|-----------|
| 1차 상장 직후 | 0~20% | IPO pop 과열·안정조작 구간이면 생략/축소. 관찰 포지션 |
| 2차 상장 2~4주 | 20~30% | 안정조작 종료·리테일/지수기대 1회 소화 후 가격대 확인 |
| 3차 2Q26 실적 전후 | 30~40% | Starlink 가입자·ARPU·Connectivity 마진·AI 적자·CapEx 확인 |
| 4차 락업해제·지수수급 소화 후 | 잔여 20~30% | 오버행을 시장이 흡수하는지 확인 |

### 5-4. 손절 대신 가설 훼손 관리
$135→$48은 이미 -64%라 가격 손절은 늦음. 7개 가설훼손 체크포인트: ①가입자 증가율 급락 ②ARPU 하락이 가입자 증가 추월 ③Connectivity EBITDA 마진 급락 ④AI/xAI 매출 없이 적자·CapEx만 확대 ⑤Starship 일정 지연+CapEx 동시 증가 ⑥락업 물량 흡수 실패 ⑦지수편입 기대 선반영 후 편입 시 매도 이벤트화. 가치 앵커: 현 실적 기반 Starlink 바닥 $5~17/주, 공격적 포워드 $34~48/주.

### 5-5. 성향별(보수/중립/공격) 차등
분할 횟수·구간 비중·pop 진입 적극성·실행 게이트 허용도를 성향별 산출(미지정 시 3종 모두).

---

## 5.5. 분석 스킬 IPO 모드 분기 (신규, Codex 지적 #1 대응)

거래 히스토리·컨센서스·과거 멀티플이 없으므로 분석 스킬을 다음으로 분기한다.

- **`report-schema` (IPO 변형):** 현재가/목표가/손절가/12개월 reward·risk → **공모가·가치앵커(바닥/포워드)·진입구간·가설훼손 조건·확신도 정의**. 2차 시장 필드는 N/A 처리.
- **`bull-case` (IPO 모드):** PER·기술적지표 대신 **SOTP/EV 배분**(Starlink·Starship·Space·AI/xAI), 옵션프리미엄 정당화 논리, **메가 IPO 비교**(지수편입 수요·희소 free float 프리미엄·리테일 수요).
- **`bear-case` (IPO 모드):** 옵션프리미엄 지배(바닥가치가 매수가 대부분 방어 못함), 락업 오버행 타임라인, free float 희소→변동성, 안정조작 종료 리스크, key-man, 미검증 세그먼트(AI/xAI 적자).
- **`investment-judge` (IPO 모드):** "12개월 BUY/HOLD/SELL+목표가" 대신 **IPO 판정 프레임** — (ㄱ) 공모가 대비 가치 정합(바닥 vs 옵션프리미엄), (ㄴ) 진입 가치 구간, (ㄷ) 확신도가 무엇의 확률인지 정의. 단일 목표가 단정 금지.
- **`verdict-review` (IPO 분기):** Part A(판결) 8축 + IPO 정합성 축(공모 구조·락업·free float·접근성 반영 여부), Part B(전략) 7축 + IPO 실행 게이트 점검.

---

## 6. 파일 구조 (구축 후, v2)

```
spcx/
├── spcx.txt                      # 시드 입력 (보존)
├── HARNESS_PLAN.md               # 이 문서 (v2)
├── UPSTREAM_SYNC.md              # fork 동기화 매니페스트 (신규, §아래)
├── CLAUDE.md                     # 하네스 포인터 + 변경 이력 (신규)
└── .claude/
    ├── agents/  (7개: bull/bear/fact-checker/judge/verdict-reviewer/data-collector/execution-strategist)
    └── skills/
        ├── ipo-analysis/         # 오케스트레이터 (신규)
        ├── ipo-snapshot/  ipo-timing/   # 신규 ①②
        ├── bull-case/ bear-case/ investment-judge/  # 복사 + IPO 모드 분기
        ├── fact-check/ verdict-review/              # 복사 + IPO 소싱/분기
        └── references/ (report-schema IPO 변형, data-sources IPO 소싱 규칙 포함)
```

**`UPSTREAM_SYNC.md` (fork 드리프트 완화):** 복사한 각 자산의 출처 경로 + 복사 시점 + 베이스 커밋 해시를 기록. 향후 원본 수정 시 재동기화 체크리스트로 사용. (팟캐스트 3종은 미복사 명시.)

---

## 7. 검증 계획 (v2 — 스모크 테스트 포함, 단 전체 실분석은 제외)

1. **구조 검증** — 에이전트 위치, frontmatter, 상호 참조, 커맨드 미생성.
2. **트리거 검증** — should-trigger("SpaceX 상장 분석", "SPCX IPO 진입 시점", 후속 "진입전략만 다시") + should-NOT-trigger near-miss.
3. **드라이런** — Phase 순서·데이터 dead link·입출력 매칭·하드 실패 경로.
4. **스냅샷 스모크 테스트(신규, Codex #6 대응)** — `ipo-snapshot`을 **실제 1회 실행**해: ⓐ EDGAR 최신 문서 접근 성공 여부, ⓑ 시총=주가×주식수·조달=주가×신주 재계산 통과, ⓒ free_float 4필드 분리·갭 명기, ⓓ self_check PASS 확인. (이는 "검증"이며 bull/bear/judge 전체 실분석이 아님 — 사용자 범위 결정과 양립.)
5. **한국 투자자 접근성 체크리스트 존재 검증** — ipo-timing이 5-1 게이트를 실제로 산출하는지.

---

## 8. 빌드 태스크 목록 (v2)

1. 재사용 자산(7 에이전트 + 6 스킬 + references) `spcx/.claude/`로 복사, `UPSTREAM_SYNC.md` 기록
2. `ipo-snapshot` 스킬 신규 (§4: 4필드 free_float, 소싱 규칙, self-check)
3. `ipo-timing` 스킬 신규 (§5: 실행 게이트·가격발견·안정조작·4단계·가설훼손)
4. `report-schema` IPO 변형 + `bull-case`/`bear-case`/`investment-judge`/`verdict-review` IPO 모드 분기 (§5.5)
5. `fact-check`/`data-sources`에 EDGAR 최신순·preliminary/final 소싱 규칙 추가
6. `execution-strategist`·`data-collector` 에이전트 IPO 모드 지침 추가
7. 오케스트레이터 `ipo-analysis` 작성 (팟캐스트 제거, Phase 1.6 스냅샷 audit·하드 실패 규칙 반영)
8. `spcx/CLAUDE.md` 하네스 포인터 + 변경 이력 등록
9. Phase 7 검증(구조·트리거·드라이런·**스냅샷 스모크 테스트**·접근성 체크) 수행 및 보고

---

## 9. 변경 이력

| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-06-09 | 구축 계획 수립(v1) | HARNESS_PLAN.md | SpaceX IPO 분석 하네스 신규 구축 계획 |
| 2026-06-09 | Codex 비판검증 반영(v2) | HARNESS_PLAN.md | 🔴3(특화범위·IPO방법론·free_float)·🟡3 수용 — IPO 모드 분기 확대, ipo-timing 재설계, 숫자 정합성·소싱 최신성·검증 강화, fork 동기화 매니페스트 |
| 2026-06-09 | 하네스 구축+검증 완료 | .claude/agents(7)·skills(8)·CLAUDE.md·UPSTREAM_SYNC.md | 9개 빌드 태스크 완료. 검증 통과: 구조·frontmatter·dead link 0·JSON self_check PASS(시총·조달 오차 0%, free_float 4필드). SpaceX 실분석은 미실행(범위 결정) |
