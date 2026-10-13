## 解析结果
- Top flow: aid-init → aid-planning → aid-implementing → aid-applying → aid-archiving → aid-monitor
- 跨 skill 文件边: 2
- 跨 skill skill() 调用边: 11

## Mermaid 图

```mermaid
graph LR
    classDef skill fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,color:#000;
    classDef step fill:#e8f5e9,stroke:#43a047,color:#000;
    classDef file fill:#e3f2fd,stroke:#1e88e5,color:#000;
    classDef call fill:#f3e5f5,stroke:#8e24aa,color:#000;
    classDef flow fill:#fffde7,stroke:#fbc02d,stroke-width:2px,color:#000;
    subgraph N1["📦 aid-analysis-locate-…"]
        direction TB
    end
    subgraph N2["📦 aid-analysis-log-sca…"]
        direction TB
    end
    subgraph N3["📦 aid-analysis-output"]
        direction TB
    end
    subgraph N4["📦 aid-analysis-phenome…"]
        direction TB
    end
    subgraph N5["📦 aid-analysis-root-ca…"]
        direction TB
    end
    subgraph N6["📦 aid-analysis-spec-co…"]
        direction TB
    end
    subgraph N7["📦 aid-applying"]
        direction TB
        N8["⚙️ step3-0<br/>环境检查"]:::step
        N9["⚙️ step3-1<br/>确认应用条件"]:::step
        N10["⚙️ step3-2<br/>代码应用"]:::step
        N11["⚙️ step3-3<br/>更新任务状态"]:::step
        N12["⚙️ step3-4<br/>产出应用报告"]:::step
        N13["📄 apply-report.md"]:::file
        N14["🎯 skill(harmonyos-ui-test)"]:::call
        N15["🎯 skill(tdd-enforcer)"]:::call
        N16["🎯 skill(harmonyos-ui-test)"]:::call
    end
    subgraph N17["📦 aid-archiving"]
        direction TB
    end
    subgraph N18["📦 aid-code-root-cause"]
        direction TB
    end
    subgraph N19["📦 aid-implementing"]
        direction TB
        N20["⚙️ step2-1<br/>任务分解"]:::step
        N21["⚙️ step2-2<br/>任务排序"]:::step
        N22["⚙️ step2-3<br/>产出 tasks.md"]:::step
        N23["📄 tasks.md"]:::file
    end
    subgraph N24["📦 aid-init"]
        direction TB
    end
    subgraph N25["📦 aid-monitor"]
        direction TB
    end
    subgraph N26["📦 aid-planning"]
        direction TB
        N27["⚙️ step1<br/>用户意图理解"]:::step
        N28["⚙️ step1-1<br/>Git 分支检查 推荐"]:::step
        N29["⚙️ step2<br/>需求理解"]:::step
        N30["📄 proposal.md"]:::file
        N31["📄 参考proposal-template.md"]:::file
        N32["⚙️ step3<br/>需求澄清"]:::step
        N33["⚙️ step4<br/>需求spec设计"]:::step
        N34["📄 delta-spec.md"]:::file
        N35["📄 delta-spec.md"]:::file
        N36["⚙️ step5<br/>针对需求的代码仓理解"]:::step
        N37["📄 info.md"]:::file
        N38["⚙️ step6<br/>需求复杂度评估"]:::step
        N39["⚙️ step7<br/>架构设计"]:::step
        N40["📄 new-arch.md"]:::file
        N41["📄 delta-spec.md和info.md"]:::file
        N42["📄 分析新增功能对关联的arch.md"]:::file
        N43["⚙️ step8<br/>组件设计"]:::step
        N44["📄 delta-design.md"]:::file
        N45["⚙️ step9<br/>设计审视"]:::step
        N46["🎯 skill(rq-parse)"]:::call
        N47["🎯 skill(rq-clarify)"]:::call
        N48["🎯 skill(rq-codebase)"]:::call
        N49["🎯 skill(mod-design)"]:::call
    end
    subgraph N50["📦 aid-reviewing"]
        direction TB
    end
    subgraph N51["📦 dfr-fmea-harmony"]
        direction TB
    end
    subgraph N52["📦 harmonyos-ui-test"]
        direction TB
    end
    subgraph N53["📦 mod-design"]
        direction TB
    end
    subgraph N54["📦 prd-generator"]
        direction TB
    end
    subgraph N55["📦 rq-clarify"]
        direction TB
    end
    subgraph N56["📦 rq-codebase"]
        direction TB
    end
    subgraph N57["📦 rq-parse"]
        direction TB
    end
    subgraph N58["📦 tdd-enforcer"]
        direction TB
    end
    N59["📄 delta-design.md"]:::file
    N60["📄 proposal.md"]:::file
    N12 -->|产出| N13
    linkStyle 0 stroke:#43a047,stroke-width:1.5px;
    N7 ==>|调用| N14
    linkStyle 1 stroke:#8e24aa,stroke-width:2.5px;
    N7 ==>|调用| N15
    linkStyle 2 stroke:#8e24aa,stroke-width:2.5px;
    N7 ==>|调用| N16
    linkStyle 3 stroke:#8e24aa,stroke-width:2.5px;
    N22 -->|产出| N23
    linkStyle 4 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N30
    linkStyle 5 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N31
    linkStyle 6 stroke:#43a047,stroke-width:1.5px;
    N32 -->|产出| N30
    linkStyle 7 stroke:#43a047,stroke-width:1.5px;
    N33 -->|产出| N34
    linkStyle 8 stroke:#43a047,stroke-width:1.5px;
    N33 -->|产出| N35
    linkStyle 9 stroke:#43a047,stroke-width:1.5px;
    N36 -->|产出| N37
    linkStyle 10 stroke:#43a047,stroke-width:1.5px;
    N39 -->|产出| N40
    linkStyle 11 stroke:#43a047,stroke-width:1.5px;
    N39 -->|产出| N40
    linkStyle 12 stroke:#43a047,stroke-width:1.5px;
    N39 -->|产出| N40
    linkStyle 13 stroke:#43a047,stroke-width:1.5px;
    N39 -->|产出| N30
    linkStyle 14 stroke:#43a047,stroke-width:1.5px;
    N39 -->|产出| N41
    linkStyle 15 stroke:#43a047,stroke-width:1.5px;
    N39 -->|产出| N42
    linkStyle 16 stroke:#43a047,stroke-width:1.5px;
    N39 -->|产出| N40
    linkStyle 17 stroke:#43a047,stroke-width:1.5px;
    N43 -->|产出| N44
    linkStyle 18 stroke:#43a047,stroke-width:1.5px;
    N43 -->|产出| N44
    linkStyle 19 stroke:#43a047,stroke-width:1.5px;
    N26 ==>|调用| N46
    linkStyle 20 stroke:#8e24aa,stroke-width:2.5px;
    N26 ==>|调用| N47
    linkStyle 21 stroke:#8e24aa,stroke-width:2.5px;
    N26 ==>|调用| N48
    linkStyle 22 stroke:#8e24aa,stroke-width:2.5px;
    N26 ==>|调用| N49
    linkStyle 23 stroke:#8e24aa,stroke-width:2.5px;
    N59 -.->|消费| N19
    linkStyle 24 stroke:#1e88e5,stroke-width:2.5px,stroke-dasharray:5 5;
    N60 -.->|消费| N19
    linkStyle 25 stroke:#1e88e5,stroke-width:2.5px,stroke-dasharray:5 5;
    N24 ==>|→| N26
    linkStyle 26 stroke:#616161,stroke-width:2.5px;
    N26 ==>|→| N19
    linkStyle 27 stroke:#616161,stroke-width:2.5px;
    N19 ==>|→| N7
    linkStyle 28 stroke:#616161,stroke-width:2.5px;
    N7 ==>|→| N17
    linkStyle 29 stroke:#616161,stroke-width:2.5px;
    N17 ==>|→| N25
    linkStyle 30 stroke:#616161,stroke-width:2.5px;
    N14 ==>|调用| N52
    linkStyle 31 stroke:#8e24aa,stroke-width:2.5px;
    N15 ==>|调用| N58
    linkStyle 32 stroke:#8e24aa,stroke-width:2.5px;
    N16 ==>|调用| N52
    linkStyle 33 stroke:#8e24aa,stroke-width:2.5px;
    N46 ==>|调用| N57
    linkStyle 34 stroke:#8e24aa,stroke-width:2.5px;
    N47 ==>|调用| N55
    linkStyle 35 stroke:#8e24aa,stroke-width:2.5px;
    N48 ==>|调用| N56
    linkStyle 36 stroke:#8e24aa,stroke-width:2.5px;
    N49 ==>|调用| N53
    linkStyle 37 stroke:#8e24aa,stroke-width:2.5px;

    %% 图例:
    %% 📦 skill  ⚙️ step  📄 file  🎯 skill() call
    %% 🟢 实线绿 = 产出   🔵 虚线蓝 = 消费   🟣 双线紫 = sub-skill 调用   ⬛ 双线灰 = 顶层 AID flow
```
