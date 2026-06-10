# 의사결정 흐름도 — 투자전략 트레이딩 하네스

[TradingAgents](https://github.com/tauricresearch/tradingagents) 구조를 이식한 파이프라인의 에이전트 의사결정 과정. 에이전트 11명이 5계층(데이터 고정 → 분석 → 리서치 토론 → 실행 설계 → 리스크 게이트)으로 분업하고, 의사결정 저널·복기가 학습 루프를 닫는다.

```mermaid
flowchart TD
    %% ── 노드 선언 ──
    U["사용자 요청<br/>티커 트레이딩 분석"]
    O["오케스트레이터<br/>trading-strategy 스킬"]
    P{"journal에 결과<br/>미기록 결정 있음?"}
    PEND["Pending 자동 결산<br/>현재가·벤치마크 알파 중간점검<br/>→ 복기 제안"]

    subgraph L1["L1 · 데이터 고정"]
        MDE["market-data-engineer<br/>사실 고정자 — 해석 금지"]
        SSOT[("SSOT<br/>00_market_snapshot.json<br/>00_indicators.json · OHLCV")]
    end

    subgraph L2["L2 · 분석가 4렌즈 — 병렬 · 상호 격리"]
        FA["fundamental<br/>재무·밸류에이션"]
        TA["technical<br/>추세·가격레벨·ATR"]
        NA["news<br/>이벤트 캘린더·내부자 거래·거시"]
        SA["sentiment<br/>심리·쏠림·수급"]
    end
    REP["분석가 보고서 4편<br/>강세·약세 신호 양쪽 의무"]

    subgraph L3["L3 · 리서치 토론 — R1 격리 → R2 교차"]
        BULL["bull-researcher<br/>R1 강세 논지"]
        BEAR["bear-researcher<br/>R1 약세 논지"]
        BULLR["bull R2<br/>약세론 정면 반박"]
        BEARR["bear R2<br/>강세론 정면 반박"]
        RM["research-manager 판정<br/>증거 구체성 · 반박 생존력 · 가정 투명성"]
    end
    PLAN["투자 계획 03<br/>방향(매수/관망/매도) · 무효화 조건 · 확신도"]

    subgraph L4["L4 · 실행 설계"]
        TR["trader<br/>손절 먼저 → 비중 역산<br/>손익비 1.5 미만 = 보류"]
    end
    TP["거래 계획 04<br/>진입·손절·비중·목표 — 성향 3분기"]

    subgraph L5["L5 · 리스크 게이트 — 3성향 병렬 · 상호 격리"]
        RA["공격 성향<br/>기회비용도 리스크"]
        RN["중립 성향<br/>가정의 현실성"]
        RC["보수 성향<br/>최악 생존"]
        PM["portfolio-manager<br/>치명 지적 · 리스크 한도 · 교훈 위반 점검"]
    end
    DEC{"최종 판정"}
    FIX["trader 또는 research-manager<br/>지시 반영 재작성"]
    PM2{"해소 확인"}
    FIN["최종 결정 06<br/>+ reports/ 정리 + 사용자 보고"]
    REJ["REJECT<br/>거부 사유 · 재고 조건 기록"]
    J[("decisions/journal.md<br/>append only")]

    subgraph LOOP["학습 루프"]
        REF["복기 trade-reflection<br/>4축 대조 + 알파 · 결과론 금지"]
        LES[("decisions/lessons.md<br/>일반화된 교훈만")]
    end

    %% ── 흐름 ──
    U --> O
    O --> P
    P -- 있음 --> PEND
    PEND --> MDE
    P -- 없음 --> MDE
    MDE --> SSOT

    SSOT --> FA & TA & NA & SA
    FA & TA & NA & SA --> REP
    REP -. "⛔스냅샷 오류 플래그 → 스냅샷 갱신·하류 재실행" .-> MDE

    REP --> BULL & BEAR
    BEAR -- 논지 전달 --> BULLR
    BULL -- 논지 전달 --> BEARR
    BULL & BEAR & BULLR & BEARR --> RM
    RM --> PLAN

    PLAN --> TR
    TR --> TP

    TP --> RA & RN & RC
    RA & RN & RC --> PM
    PM --> DEC
    DEC -- APPROVE --> FIN
    DEC -- "REVISE — 1회 한정" --> FIX
    FIX --> PM2
    PM2 -- 해소 --> FIN
    PM2 -- 미해소 --> REJ
    DEC -- REJECT --> REJ

    FIN --> J
    REJ --> J
    J --> REF
    REF --> LES
    LES -. "다음 실행 시 전 판단 에이전트가 읽음" .-> O
```

## 읽는 법

- **격리가 설계의 핵심이다.** L2 분석가 4명, L3의 R1 논지, L5의 3성향은 서로의 산출물을 보지 못한다. 독립 관점의 충돌이 정보량의 원천이며, 교차는 R2에서 오케스트레이터가 파일을 건네는 방식으로만 일어난다. 데이터 전달은 전부 `_workspace/` 파일 기반이다.
- **게이트가 두 번 있다.** trader의 손익비 1.5 게이트(미달이면 계획 자체를 내지 않고 "보류 + 성립 조건"이 결론)와 portfolio-manager의 최종 게이트(⛔치명 지적이 하나라도 있으면 APPROVE 불가). REVISE는 1회만 허용되고 미해소면 REJECT — 무한 루프 방지.
- **학습 루프가 시스템을 닫는다.** 모든 판정(거부 포함)이 journal에 append되고, 복기가 벤치마크 대비 알파 기준으로 의사결정 품질을 평가해(결과론 금지) lessons.md에 교훈을 쌓으며, 다음 실행에서 전 판단 에이전트가 이를 읽는다. Pending 자동 결산이 이 루프의 시작점을 자동화한다.

상세 실행 규칙은 `.claude/skills/trading-strategy/SKILL.md`(오케스트레이터), 각 단계 방법론은 해당 스킬(`market-snapshot`, `analyst-toolkit`, `research-debate`, `trade-planning`, `risk-gate`, `trade-reflection`) 참조.
