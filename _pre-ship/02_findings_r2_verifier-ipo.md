# 독립 검증 보고 — IPO·공시 계열 반영 정합 (r2-verifier-ipo, 2026-07-04)

**총평: 11개 항목 전부 반영됨. 불완전·미반영·회귀발견 0건. 🔴/🟡 0건, 🟢 잔여 3건(범위 밖·비회귀).**

## ① 항목별 판정표

| # | 항목 | 판정 | 근거 (파일:줄 + 왜) |
|---|------|------|---------------------|
| 1 | IPO 확신도 앵커 통일 | **반영됨** | `.claude/skills/investment-judge/SKILL.md:41` "표준 앵커: **12개월 내 벤치마크 대비 초과수익 확률**(IPO는 상장 후 12개월 내)", `:69` "상장 후 12개월 내 벤치마크 대비 초과수익을 낼 주관 확률 — **공모가 대비가 아니라** 벤치마크 알파가 캘리브레이션 채점 기준". `report-schema.md:59`·`:110` 동일 통일. `:67`·`:112`의 "공모가 대비 가치"는 확신도 앵커가 아니라 가치 정합 개념(정상). |
| 2 | IPO 단계 Phase 체계 통일 | **반영됨** | `ipo-analysis/SKILL.md` 헤더(:6~12) 산문 서술, "N단계" 없음. 데이터전달표(:174~188) "단계" 열=1.5/2/3/4/4.5/4.7/4.8. 에이전트 7종 description 전부 Phase: bull `:3`=P2, bear `:3`=P2, data-collector `:3`=P1.5, fact-checker `:3`=P3, investment-judge `:3`=P4, verdict-reviewer `:3`=P4.5/4.8+R, execution-strategist `:3`=P4.7. **`3.5/3.7/3.9단계` 리포 전체 grep 0건.** |
| 3 | fact-checker fork 잔재 | **반영됨** | `agents/fact-checker.md:45` "공모가·발행신주·상장후 주식수·시총·free float 4필드·락업·환율·세그먼트 재무 — **신규상장엔 거래 주가·거래 멀티플이 없다**". "주가·밸류에이션 배수" 소거. |
| 4 | investment-judge fork 잔재 | **반영됨** | `agents/investment-judge.md:15` "공모가·상장후 주식수·시총·free float·락업·환율·재무 핵심값…(**신규상장엔 거래 주가·거래 멀티플이 없다**)". "밸류에이션 배수" 없음. |
| 5 | data-collector fork 잔재 | **반영됨** | `agents/data-collector.md:7` 제목 "**IPO 데이터 수집가**", `:21` "공모가(밴드/확정)·발행신주·…·세그먼트 재무 핵심값만". "벤치마크·밸류에이션 배수만" 자기모순 소거. |
| 6 | execution-strategist 에러 핸들링 | **반영됨** | `agents/execution-strategist.md:46` "**기준가(상장 전=예비/확정 공모가, 상장 후 재분석=현재가)**·환율이 없으면…상대% 기준". "현재가" 단일 전제 → 분기. |
| 7 | verdict-reviewer 출력 열거 | **반영됨** | `agents/verdict-reviewer.md:47` "**8축 + ⑨ IPO 정합성**", `:49` "…편향 + **ⓗ IPO 실행 게이트**". 둘 다 포함. |
| 8 | ipo-analysis 저널 `실행` 필드 | **반영됨** | `ipo-analysis/SKILL.md:133` "…채택 진입 계획(게이트/비중/잠재 손실)·**`실행: (미체결)`**·가설훼손…·`결과: (미기록 — 복기 시 갱신)`". |
| 9 | ipo-reflection 커밋 스텝 | **반영됨** | `ipo-reflection/SKILL.md:48` "7. **학습 코퍼스 커밋:** `git add decisions/ && git commit -m "복기: {회사} IPO"` — 단독 실행 시에도 생략 금지". |
| 10 | ipo-reflection calibration 라벨 | **반영됨** | `ipo-reflection/SKILL.md:43` "| … | **확신도(p)** | **결과(o: 1/0.5/0)** | Brier (p−o)² |". 정렬됨. |
| 11 | filings-analysis 도식 팟캐스트 | **반영됨** | `filings-analysis/SKILL.md:18` 도식에 "**[선택]  podcast-producer ── 팟캐스트(05_podcast_script.md+MP3) — 사용자 동의 시만**" 존재. 데이터전달표(:158) 정합. |

## ② 회귀·잔여 결함 목록 (심각도순)

수정 지점 ±30줄 및 대상 10파일 전문 정독 — 끊긴 표·중복 문장·번호 연쇄 오류·앞뒤 앵커 모순 **없음**. 🔴/🟡 0건. 범위 밖 경미 부정합 3건(비회귀):

- 🟢 **`skills/verdict-review/SKILL.md:86` + `agents/verdict-reviewer.md:39`** — 확신도 정의를 점검하는 검토관 루브릭이 여전히 일반형 템플릿("결론 방향이 맞을 주관 확률")을 제시. 항목 1의 벤치마크-알파 앵커와 미세 불일치. 단 항목 1 명시 범위 밖이고 `investment-judge/SKILL.md:41`이 "다른 정의 시 표준 앵커 병기"를 허용하므로 설계 여유 내. 검토관 템플릿에 "표준 앵커 병기 요구" 덧대면 완전 정합. 판정 영향 없음.
- 🟢 **`agents/execution-strategist.md:9`** — 역할 서두에 "어디서 **손절**하고" 2차 시장 언어 잔재. 단 `:36`이 "IPO엔 손절가·목표가·손익비를 쓰지 않는다 — 가치 앵커·가설훼손으로 관리"로 정정하므로 실무 충돌 없음.
- 🟢 **`ipo-analysis/SKILL.md:20`** — Phase 0 모드표 "**1단계부터** 전체 실행"에 구어체 단계 표현("처음부터" 뜻). 파이프라인 라벨 아님. 순수 미관.

## ③ 검증 범위 / 한계

- **전문 정독(±30줄 회귀 충족):** investment-judge/SKILL, report-schema, ipo-analysis/SKILL, agents/{fact-checker, investment-judge, data-collector, execution-strategist, verdict-reviewer}, ipo-reflection/SKILL, filings-analysis/SKILL.
- **전수 grep:** 단계 번호(`\d단계`/`3.5·3.7·3.9`)·확신도 앵커(방향·공모가 대비·절대수익·맞을 확률)를 `.claude` 트리 전체 실행. 발견된 `단계` 매치는 전부 스킬 내부 절차 카운트(fact-check 4단계, plain-language 4단계, macro-regime 7단계, "4단계 분할 진입" 등)로 파이프라인 라벨과 무관 확인. **구 IPO 단계 번호 잔재 0건.**
- **한계:** (ㄱ) bull/bear-analyst는 본문 전문이 아니라 `Phase|단계|3.5|3.7|3.9` grep만 수행(매치=description Phase 2 1건). (ㄴ) `decisions/calibration.md` 실파일 헤더의 바이트 단위 일치는 미확인(항목 10은 SKILL 내 라벨 정합만 요구, 충족). (ㄷ) 런타임 준수 여부는 정적 검증 범위 밖.
