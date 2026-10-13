import json
import os
import re

def parse_agent_trace(jsonl_path):
    print(f"🚀 开始构建执行轨迹树 (Langfuse Style) : {jsonl_path}\n")
    
    if not os.path.exists(jsonl_path):
        print(f"❌ 找不到文件: {jsonl_path}")
        return

    # 1. 定义树的结构
    tree = {
        "goal": "未找到初始目标",
        "skills": []
    }
    
    current_skill = {"name": "Global (Root)", "actions": []}
    tree["skills"].append(current_skill)
    
    pending_tools = {}
    
    # 🌟 核心：全局产物池，用来追踪依赖！
    # 只要被 Write/Edit 过，就加入池子。后续工具如果参数里出现了这个文件名，说明它构成了“数据消费”。
    global_artifacts = set()
    
    # 辅助函数：从长路径提取文件名
    def basename(path): return str(path).split('/')[-1].split('\\')[-1]

    # 2. 读取并构建内存树结构
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        is_first_msg = True
        for line in f:
            if not line.strip(): continue
            try:
                record = json.loads(line)
            except: continue
            
            msg = record.get("message", {})
            if not msg: continue
            
            role = msg.get("role")
            content = msg.get("content")
            
            # 【User 消息：Goal 与 环境反馈】
            if role == "user":
                if isinstance(content, str):
                    if is_first_msg:
                        tree["goal"] = content.strip().split('\n')[0][:80] + "..."
                        is_first_msg = False
                    else:
                        current_skill["actions"].append({
                            "type": "human_reply", 
                            "desc": content.strip()[:60]
                        })
                        
                elif isinstance(content, list):
                    for block in content:
                        if block.get("type") == "tool_result":
                            t_id = block.get("tool_use_id")
                            is_err = block.get("is_error", False)
                            t_content = str(block.get("content", ""))
                            
                            if t_id in pending_tools:
                                tool_node = pending_tools[t_id]
                                tool_node["results"].append({
                                    "is_err": is_err,
                                    "desc": "Exit Code 1 / Error" if is_err else t_content[:50].replace('\n', ' ')
                                })
                                
                                # 🌟 依赖判定：产物生成 (Produce)
                                t_name = tool_node["name"]
                                if not is_err and t_name in ["Write", "Edit", "TodoWrite"]:
                                    filepath = tool_node["args"].get("file_path", "")
                                    fname = basename(filepath)
                                    if fname:
                                        tool_node["produces"].append(fname)
                                        global_artifacts.add(fname)
                                        
            # 【Assistant 消息：Thought, ToolCall, Skill 容器】
            elif role == "assistant":
                if isinstance(content, list):
                    for block in content:
                        if block.get("type") in ["thinking", "text"]:
                            text = block.get("thinking") or block.get("text", "")
                            current_skill["actions"].append({
                                "type": "thought",
                                "desc": text[:60].replace('\n', ' ') + "..."
                            })
                            
                        elif block.get("type") == "tool_use":
                            t_id = block.get("id")
                            t_name = block.get("name")
                            t_input = block.get("input", {})
                            
                            # 🌟 依赖判定：数据消费 (Consume)
                            consumes = []
                            input_str = json.dumps(t_input)
                            # 如果参数/命令中出现了我们之前产出过的文件名，说明产生了依赖！
                            for artifact in global_artifacts:
                                if artifact in input_str:
                                    consumes.append(artifact)
                                    
                            # 解析是普通动作还是切 Skill
                            if t_name == "Skill":
                                skill_name = t_input.get("skill", "unknown_skill")
                                current_skill = {"name": skill_name, "actions": []}
                                tree["skills"].append(current_skill)
                                
                                # Skill 的调用本身也记为一个动作，带上参数里的依赖
                                tool_node = {"name": f"Sub-Skill({skill_name})", "args": t_input, "results": [], "produces": [], "consumes": consumes}
                                pending_tools[t_id] = tool_node
                                current_skill["actions"].append({"type": "tool_call", "node": tool_node})
                            else:
                                if t_name == "Read":
                                    # Read 直接就是消费
                                    consumes.append(basename(t_input.get("file_path", "")))
                                    
                                tool_node = {"name": t_name, "args": t_input, "results": [], "produces": [], "consumes": list(set(consumes))}
                                pending_tools[t_id] = tool_node
                                current_skill["actions"].append({"type": "tool_call", "node": tool_node})

    # ==========================================
    # 3. Langfuse 式控制台渲染
    # ==========================================
    print(f"ROOT: [Session Execution Trace]")
    print(f"│")
    print(f"├── 🎯 [v_goal] {tree['goal']}")
    
    for i, skill in enumerate(tree["skills"]):
        if not skill["actions"]: continue
        
        is_last_skill = (i == len(tree["skills"]) - 1)
        s_prefix = "└──" if is_last_skill else "├──"
        s_line = " " if is_last_skill else "│"
        
        print(f"│")
        print(f"{s_prefix} 📦 [v_skill/stage: {skill['name']}]")
        
        for j, act in enumerate(skill["actions"]):
            is_last_act = (j == len(skill["actions"]) - 1)
            a_prefix = "    └──" if is_last_act else "    ├──"
            a_line = "    " if is_last_act else "    │"
            
            if act["type"] == "thought":
                print(f"{s_line}{a_prefix} 🧠 [v_thought] {act['desc']}")
            
            elif act["type"] == "human_reply":
                print(f"{s_line}{a_prefix} 👤 [v_human] {act['desc']}")
                
            elif act["type"] == "tool_call":
                node = act["node"]
                args_preview = str(node['args'])[:40].replace('\n', '')
                print(f"{s_line}{a_prefix} 🛠️ [v_tool_call] {node['name']}({args_preview}...)")
                
                # 绘制依赖、结果、产物
                details = []
                for c in node['consumes']: details.append(("📥 [v_depend: Consume]", c))
                for r in node['results']:
                    icon = "🚨 [v_error]" if r['is_err'] else "💬 [v_result]"
                    details.append((icon, r['desc']))
                for p in node['produces']: details.append(("📄 [v_artifact: Produce]", p))
                
                for k, (icon, desc) in enumerate(details):
                    is_last_det = (k == len(details) - 1)
                    d_prefix = "    └──" if is_last_det else "    ├──"
                    print(f"{s_line}{a_line}{d_prefix} {icon} {desc}")

if __name__ == "__main__":
    parse_agent_trace("D:\\huawei\\my_sessions\\sessions\\claude-code\\dev-01\\_raw\\D--huawei-Demo-worktrees-issue-26\\2026-06-17\\264c5a16-f4f1-48ff-9f40-d215e1cc2567.jsonl")