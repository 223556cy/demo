#!/usr/bin/env python3
# parse_ui.py — UI dump 解析工具 (Issue #24)
# 用于: 读取 uidump.json, 输出所有 text 节点
import json
import sys
import re
from pathlib import Path

UIDUMP_FILE = Path(__file__).parent / "uidump.json"

def parse(dump_file=UIDUMP_FILE):
    """解析 UI dump, 提取所有 text 字段"""
    if not Path(dump_file).exists():
        print(f"❌ 文件不存在: {dump_file}")
        sys.exit(1)
    with open(dump_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _extract(data)

def _extract(node, out=None):
    if out is None:
        out = []
    if isinstance(node, dict):
        attrs = node.get("attributes", {})
        if attrs.get("text"):
            out.append(attrs["text"])
        for v in node.values():
            _extract(v, out)
    elif isinstance(node, list):
        for item in node:
            _extract(item, out)
    return out

def find_node(text, dump_file=UIDUMP_FILE):
    """递归查找指定 text 的节点, 返回中心坐标 (x, y)"""
    if not Path(dump_file).exists():
        return None
    with open(dump_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    return _find_node(data, text)

def _find_node(node, text):
    if isinstance(node, dict):
        if node.get("attributes", {}).get("text") == text:
            bounds = node.get("attributes", {}).get("bounds", "")
            m = re.match(r"\[(\d+),(\d+)\]\[(\d+),(\d+)\]", bounds)
            if m:
                x1, y1, x2, y2 = map(int, m.groups())
                return ((x1 + x2) // 2, (y1 + y2) // 2)
        for v in node.values():
            r = _find_node(v, text)
            if r:
                return r
    elif isinstance(node, list):
        for item in node:
            r = _find_node(item, text)
            if r:
                return r
    return None

if __name__ == "__main__":
    texts = parse()
    print(f"找到 {len(texts)} 个 text 节点:")
    for t in texts:
        print(f"  - {t}")
