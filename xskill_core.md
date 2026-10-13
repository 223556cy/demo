## 核心 AID 3 阶段跨 skill 数据流图

```mermaid
graph LR
    classDef skill fill:#fff3e0,stroke:#fb8c00,stroke-width:2px,color:#000;
    classDef step fill:#e8f5e9,stroke:#43a047,color:#000;
    classDef file fill:#e3f2fd,stroke:#1e88e5,color:#000;
    classDef call fill:#f3e5f5,stroke:#8e24aa,color:#000;
    classDef flow fill:#fffde7,stroke:#fbc02d,stroke-width:2px,color:#000;
    subgraph N1["📦 aid-applying"]
        direction TB
        N2["⚙️ step3-0<br/>环境检查"]:::step
        N3["⚙️ step3-1<br/>确认应用条件"]:::step
        N4["⚙️ step3-2<br/>代码应用"]:::step
        N5["⚙️ step3-3<br/>更新任务状态"]:::step
        N6["⚙️ step3-4<br/>产出应用报告"]:::step
        N7["📄 apply-report.md"]:::file
        N8["🎯 skill(harmonyos-ui-test)"]:::call
        N9["🎯 skill(tdd-enforcer)"]:::call
        N10["🎯 skill(harmonyos-ui-test)"]:::call
    end
    subgraph N11["📦 aid-implementing"]
        direction TB
        N12["⚙️ step2-1<br/>任务分解"]:::step
        N13["⚙️ step2-2<br/>任务排序"]:::step
        N14["⚙️ step2-3<br/>产出 tasks.md"]:::step
        N15["📄 tasks.md"]:::file
    end
    subgraph N16["📦 aid-planning"]
        direction TB
        N17["⚙️ step1<br/>用户意图理解"]:::step
        N18["⚙️ step1-1<br/>Git 分支检查 推荐"]:::step
        N19["⚙️ step2<br/>需求理解"]:::step
        N20["📄 proposal.md"]:::file
        N21["📄 参考proposal-template.md"]:::file
        N22["⚙️ step3<br/>需求澄清"]:::step
        N23["⚙️ step4<br/>需求spec设计"]:::step
        N24["📄 delta-spec.md"]:::file
        N25["📄 delta-spec.md"]:::file
        N26["⚙️ step5<br/>针对需求的代码仓理解"]:::step
        N27["📄 info.md"]:::file
        N28["⚙️ step6<br/>需求复杂度评估"]:::step
        N29["⚙️ step7<br/>架构设计"]:::step
        N30["📄 new-arch.md"]:::file
        N31["📄 delta-spec.md和info.md"]:::file
        N32["📄 分析新增功能对关联的arch.md"]:::file
        N33["⚙️ step8<br/>组件设计"]:::step
        N34["📄 delta-design.md"]:::file
        N35["⚙️ step9<br/>设计审视"]:::step
        N36["🎯 skill(rq-parse)"]:::call
        N37["🎯 skill(rq-clarify)"]:::call
        N38["🎯 skill(rq-codebase)"]:::call
        N39["🎯 skill(mod-design)"]:::call
    end
    subgraph N40["📦 harmonyos-ui-test"]
        N40
    end
    subgraph N41["📦 mod-design"]
        N41
    end
    subgraph N42["📦 rq-clarify"]
        N42
    end
    subgraph N43["📦 rq-codebase"]
        N43
    end
    subgraph N44["📦 rq-parse"]
        N44
    end
    subgraph N45["📦 tdd-enforcer"]
        N45
    end
    N46["📄 delta-design.md"]:::file
    N47["📄 proposal.md"]:::file
    N6 -->|产出| N7
    linkStyle 0 stroke:#43a047,stroke-width:1.5px;
    N1 ==>|调用| N8
    linkStyle 1 stroke:#8e24aa,stroke-width:2.5px;
    N1 ==>|调用| N9
    linkStyle 2 stroke:#8e24aa,stroke-width:2.5px;
    N1 ==>|调用| N10
    linkStyle 3 stroke:#8e24aa,stroke-width:2.5px;
    N14 -->|产出| N15
    linkStyle 4 stroke:#43a047,stroke-width:1.5px;
    N19 -->|产出| N20
    linkStyle 5 stroke:#43a047,stroke-width:1.5px;
    N19 -->|产出| N21
    linkStyle 6 stroke:#43a047,stroke-width:1.5px;
    N22 -->|产出| N20
    linkStyle 7 stroke:#43a047,stroke-width:1.5px;
    N23 -->|产出| N24
    linkStyle 8 stroke:#43a047,stroke-width:1.5px;
    N23 -->|产出| N25
    linkStyle 9 stroke:#43a047,stroke-width:1.5px;
    N26 -->|产出| N27
    linkStyle 10 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N30
    linkStyle 11 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N30
    linkStyle 12 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N30
    linkStyle 13 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N20
    linkStyle 14 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N31
    linkStyle 15 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N32
    linkStyle 16 stroke:#43a047,stroke-width:1.5px;
    N29 -->|产出| N30
    linkStyle 17 stroke:#43a047,stroke-width:1.5px;
    N33 -->|产出| N34
    linkStyle 18 stroke:#43a047,stroke-width:1.5px;
    N33 -->|产出| N34
    linkStyle 19 stroke:#43a047,stroke-width:1.5px;
    N16 ==>|调用| N36
    linkStyle 20 stroke:#8e24aa,stroke-width:2.5px;
    N16 ==>|调用| N37
    linkStyle 21 stroke:#8e24aa,stroke-width:2.5px;
    N16 ==>|调用| N38
    linkStyle 22 stroke:#8e24aa,stroke-width:2.5px;
    N16 ==>|调用| N39
    linkStyle 23 stroke:#8e24aa,stroke-width:2.5px;
    N46 -.->|消费| N11
    linkStyle 24 stroke:#1e88e5,stroke-width:2.5px,stroke-dasharray:5 5;
    N47 -.->|消费| N11
    linkStyle 25 stroke:#1e88e5,stroke-width:2.5px,stroke-dasharray:5 5;
    N16 ==>|→| N11
    linkStyle 26 stroke:#616161,stroke-width:2.5px;
    N11 ==>|→| N1
    linkStyle 27 stroke:#616161,stroke-width:2.5px;
    N8 ==>|调用| N40
    linkStyle 28 stroke:#8e24aa,stroke-width:2.5px;
    N9 ==>|调用| N45
    linkStyle 29 stroke:#8e24aa,stroke-width:2.5px;
    N10 ==>|调用| N40
    linkStyle 30 stroke:#8e24aa,stroke-width:2.5px;
    N36 ==>|调用| N44
    linkStyle 31 stroke:#8e24aa,stroke-width:2.5px;
    N37 ==>|调用| N42
    linkStyle 32 stroke:#8e24aa,stroke-width:2.5px;
    N38 ==>|调用| N43
    linkStyle 33 stroke:#8e24aa,stroke-width:2.5px;
    N39 ==>|调用| N41
    linkStyle 34 stroke:#8e24aa,stroke-width:2.5px;

    %% 图例:
    %% 📦 skill  ⚙️ step  📄 file  🎯 skill() call
    %% 🟢 实线绿 = 产出   🔵 虚线蓝 = 消费   🟣 双线紫 = sub-skill 调用   ⬛ 双线灰 = 顶层 AID flow
```
