# 트레이딩 하네스 전체 구조 (뉴로퓨전/월가아재 톱다운 보강 후)

> 12명 6계층. 2026-06-14 보강(L0 거시 레짐 + 바벨·상관 + 시장구조 + 역발상).
> 실선 = 데이터 흐름(파일), 점선 = 스킬 참조, `<-.->` = R2에서만 교차(R1은 격리).

```mermaid
flowchart TD
    IN["사용자 요청<br/>{티커} 트레이딩 분석"] --> ORCH(["trading-strategy<br/>오케스트레이터"])

    subgraph P1["Phase 1 · L0 거시 ∥ L1 데이터 (병렬)"]
        direction LR
        MS["macro-strategist<br/>거시 레짐 판정"]
        MDE["market-data-engineer<br/>스냅샷 SSOT"]
    end

    subgraph P2["Phase 2 · L2 분석가 4렌즈 (병렬 · 거시 배경)"]
        direction LR
        FA["fundamental"]
        TA["technical"]
        NA["news"]
        SA["sentiment"]
    end

    subgraph P3["Phase 3 · L3 리서치 토론"]
        BULL["bull-researcher"]
        BEAR["bear-researcher"]
        RM["research-manager<br/>판정 + 역발상"]
    end

    TRD["Phase 4 · L4<br/>trader 거래계획"]

    subgraph P5["Phase 5~6 · L5 리스크 3성향 (격리) → 게이트"]
        RA["risk 공격"]
        RN["risk 중립"]
        RC["risk 보수"]
        PM["portfolio-manager<br/>거시·바벨·역발상 게이트"]
    end

    REF["학습 · trade-reflection<br/>복기 → lessons"]

    ORCH --> P1
    MS -- "00_macro_regime.md" --> P2
    MDE -- "스냅샷 SSOT" --> P2
    P2 --> BULL
    P2 --> BEAR
    BULL <-. "R2 교차반박" .-> BEAR
    BULL --> RM
    BEAR --> RM
    RM -- "03_research_plan" --> TRD
    MS -. "레짐 배경" .-> RM
    TRD -- "04_trade_plan" --> RA & RN & RC
    RA --> PM
    RN --> PM
    RC --> PM
    MS -. "거시·바벨 게이트" .-> PM
    PM -- "06_final_decision + journal" --> REF
    REF -. "lessons.md 주입" .-> ORCH

    %% 스킬 연결 (점선)
    MS -.skill.-> SK1["macro-regime<br/>+ contrarian-check"]
    SA -.skill.-> SK2["analyst-toolkit<br/>+ market-structure"]
    TA -.skill.-> SK2
    RM -.skill.-> SK3["research-debate<br/>+ contrarian-check"]
    RA -.skill.-> SK4["risk-gate<br/>+ barbell-correlation"]
    PM -.skill.-> SK4

    classDef new fill:#2d5a27,stroke:#7cb342,color:#fff
    classDef skill fill:#1a1a2e,stroke:#666,color:#bbb,stroke-dasharray: 4
    class MS,SK1 new
    class SK1,SK2,SK3,SK4 skill
```

## 계층 요약

| 계층 | 에이전트 | 산출물 | 스킬 |
|------|---------|--------|------|
| L0 거시 | macro-strategist | `00_macro_regime.md` | macro-regime, contrarian-check |
| L1 데이터 | market-data-engineer | `00_market_snapshot.json` 외 | market-snapshot |
| L2 분석 | fundamental ∥ technical ∥ news ∥ sentiment | `01_*_report.md` | analyst-toolkit (+market-structure) |
| L3 리서치 | bull ↔ bear → research-manager | `02_*`, `03_research_plan.md` | research-debate, contrarian-check |
| L4 실행 | trader | `04_trade_plan.md` | trade-planning |
| L5 게이트 | risk ×3 → portfolio-manager | `05_risk_*`, `06_final_decision.md`, journal | risk-gate (+barbell-correlation), contrarian-check |
| 학습 | portfolio-manager(복기) | `decisions/lessons.md` | trade-reflection |

방법론 원천: `docs/neurofusion/method_{liquidity_fed,macro_regime,structure_valuation,portfolio_risk}.md`
