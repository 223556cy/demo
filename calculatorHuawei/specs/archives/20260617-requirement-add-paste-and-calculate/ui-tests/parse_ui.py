#!/usr/bin/env python3
# parse_ui.py — UI 树解析工具
# 用于解析 hdc uitest dumpLayout 输出的 JSON

import json
import sys
from pathlib import Path

def extract_components(node, parent_pos=None, out=None):
    """递归提取所有 UI 组件"""
    if out is None:
        out = []
    if isinstance(node, dict):
        comp = {
            "text": node.get("text", ""),
            "type": node.get("type", ""),
            "id": node.get("id", ""),
            "bounds": node.get("bounds", ""),
            "clickable": node.get("clickable", False),
            "enabled": node.get("enabled", True)
        }
        if any([comp["text"], comp["id"], comp["clickable"]]):
            out.append(comp)
        for v in node.values():
            extract_components(v, parent_pos, out)
    elif isinstance(node, list):
        for item in node:
            extract_components(item, parent_pos, out)
    return out

def find_text(components, target):
    """查找包含指定文本的组件"""
    for c in components:
        if target in c["text"]:
            return c
    return None

def find_clickable(components):
    """查找所有可点击组件"""
    return [c for c in components if c["clickable"]]

def main():
    if len(sys.argv) < 2:
        print("usage: parse_ui.py <uidump.json> [text]")
        sys.exit(1)

    dump_file = Path(sys.argv[1])
    if not dump_file.exists():
        print(f"file not found: {dump_file}")
        sys.exit(1)

    with open(dump_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    components = extract_components(data)
    print(f"total components: {len(components)}")
    print(f"clickable: {len(find_clickable(components))}")
    print()

    if len(sys.argv) > 2:
        target = sys.argv[2]
        c = find_text(components, target)
        if c:
            print(f"found '{target}': {c}")
        else:
            print(f"not found: '{target}'")
        return 0 if c else 1

    # 默认输出所有有文本的组件
    for c in components:
        if c["text"]:
            print(f"  [{c['type']}] {c['text']} (clickable={c['clickable']})")

    return 0

if __name__ == "__main__":
    sys.exit(main())
