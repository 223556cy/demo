#!/usr/bin/env python3
"""Parse UI tree JSON file and display all nodes with text."""
import json
import sys

def walk(node, depth=0):
    attrs = node.get('attributes', {})
    text = attrs.get('text', '')
    cls = attrs.get('type', '')
    bounds = attrs.get('bounds', '')
    clickable = attrs.get('clickable', '')
    rid = attrs.get('id', '')

    if text or clickable == 'true':
        indent = '  ' * depth
        print(f"{indent}text='{text}' class={cls} bounds={bounds} clickable={clickable} id={rid}")

    for child in node.get('children', []):
        walk(child, depth + 1)

with open(sys.argv[1], 'r', encoding='utf-8') as f:
    data = json.load(f)

walk(data)
