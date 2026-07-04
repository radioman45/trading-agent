# 검토자: reviewer-ipo (격리 code-reviewer, opus) — 1회차

**렌즈:** IPO 하네스 fork 잔재 + 참조 무결성
**판정: 🔴 0 · 🟡 5 · 🟢 3** — 전부 문서 정합 수준(실행은 안 깨짐)

## 발견 결함
- 🟡-1 **단계 번호 삼중 불일치**: execution-strategist.md:3 "3.7단계", verdict-reviewer.md:3 "3.5/3.9단계" ↔ ipo-analysis/SKILL.md:98,107,114 "Phase 4.5/4.7/4.8" ↔ 데이터 표(:173-188)는 1/2/3단계와 4.5/4.7/4.8 혼용. 권고: 한 체계로 통일.
- 🟡-2 **fact-checker.md:45 스냅샷 검증 필드에 IPO에 없는 "주가·밸류에이션 배수" 열거** (data-sources.md:14가 "거래 멀티플 없음" 명시; fact-check/SKILL.md:23은 올바름). 권고: IPO 필드로 치환.
- 🟡-3 **investment-judge.md:15 SSOT 필드에 "밸류에이션 배수" 잔재** (스킬:63-71 IPO 모드가 교정하나 에이전트 인라인 잔존). 권고: 삭제/치환.
- 🟡-4 **data-collector.md:21 "벤치마크·밸류에이션 배수만 담는다" 자기모순** (line 17 IPO 의무와 충돌; IPO 스냅샷 스키마엔 없음). 권고: IPO 필드로 치환. (+line 7 제목 "시장 데이터 수집가" 🟢)
- 🟡-5 **execution-strategist.md:46 에러 핸들링이 "현재가" 존재를 전제** (IPO 스냅샷엔 공모가만; 본문 :17은 올바름). 권고: "예비 공모가/기준 진입가"로 치환 또는 상장 전/후 분기.
- 🟢-6 execution-strategist.md:9,26,30 "손절" 은유 톤(:25,36이 교정 — 실질 무해).
- 🟢-7 report-schema.md:8-12 공통 헤더 기본값 2차 시장(단 :93-121 IPO 변형 체인 정상).
- 🟢-8 verdict-reviewer.md:47,49 출력 열거가 ⑨/ⓗ 생략(스킬·오케스트레이터가 명시 — 인라인만 불완전).

## 문제없음 확인 (요지)
- 참조 경로 무결성: 스킬 11종·에이전트 9종·references 2종 실재, report-schema 풀패스 정상.
- 데이터 전달 표 생산자→소비자 정합. Bull·Bear 동시 실패 중단(:196)·단독 실패(:195) 규칙 무모순.
- verdict-review Part A 8축+⑨ / Part B 7축+ⓗ 내부·오케스트레이터 일치.
- 저널 IPO 포맷 ↔ Phase 6 기록(:133) ↔ ipo-reflection(:38) 일치, calibration 포맷 일치(:41-46), decisions/ 커밋 :134·:165.
- IPO 핵심 스킬 특화 완료 — 일봉 기술지표 요구 잔재 없음.

## 미확인
- 런타임 실행 정합(정적 검토만). podcast/plain-language IPO 분기 내부(범위 밖). 외부 스킬 실동작.
