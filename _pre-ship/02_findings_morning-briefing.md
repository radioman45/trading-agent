# morning-briefing 스킬·루틴 격리 검토 (2026-07-05, mb-review — critic 1렌즈)

판정: REVISE 조건부 (⛔0 / 🟡3 / 🟢6) → 3 MAJOR 전부 반영 후 등록. 경량 정보 산출물(매매 판단 없음)이라 1라운드 1렌즈로 비례 축소 — 실질 2차 검증은 첫 정기 실행(2026-07-06 월 07:04 KST)의 산출물 확인이 담당.

## 🟡 (수용·반영 완료)
- **M1 UTC→KST 오프바이원**: cron UTC 22시 실행 시 컨테이너 date(UTC)가 KST 전날을 보여줘 UTC 일요일=KST 월요일이 "일=미실행"에 오매칭(주간 프리뷰 소실) + 날짜 스탬프 하루 밀림 → §0에 KST(UTC+9) 계산 명문화·UTC 요일 분기 금지 + 요일 표에 UTC↔KST 대조 각주 + 루틴 프롬프트에도 이중 명시.
- **M2 KR 티커 접미사**: holdings의 0167A0·088980이 순수 yfinance 원라이너에서 무반환(SOL 18.7% 상시 미확보) → §2에 `.KS`(→`.KQ`) 접미사 의무 + 번들 스크립트(KR 자동 접미사) 폴백 명시.
- **M3 의존성 부트스트랩**: yfinance 미설치 시 침묵 뉴스판 강등 → §2 서두에 import 확인·pip install 의무(침묵 강등 금지·사유 명시).

## 🟢 (반영)
^TNX 스케일 sanity check(4~6% 범위) / Gmail 수신자(yh.lee223@gmail.com)·같은 날짜 초안 중복 가드 / 최후 폴백(git+Gmail 동시 실패 시 전문을 세션 출력 — 브리핑 증발 금지) / 발행 최소선(대시보드·트리거·뉴스 중 1 필수 — 빈 브리핑 금지) / 트리거 목록은 저널에서 매일 재구성(스킬 목록은 2026-07-05 스냅샷 예시 명시) / 한국 휴장 스테일 표기.

## 관찰 유지(비차단)
매매 언어 경계 기계 검사 없음(filings doctor 휴리스틱과 비대칭 — 경량 산출물 수용), 일일 main 커밋 히스토리 소음·Gmail 초안 누적(사용자 수신 습관 확인 후 재론), 클라우드 env의 yfinance 사전 설치 여부·push 자격증명은 첫 실행에서 실측.

## 등록 정보
루틴 `trig_015fdsgFhaSPfAa3j33oKkEv` — cron `0 22 * * 0-5`(UTC) = KST 월~토 07시, sonnet, 소스 github.com/radioman45/trading-agent(푸시 필수), Gmail MCP 연결. 관리: https://claude.ai/code/routines
