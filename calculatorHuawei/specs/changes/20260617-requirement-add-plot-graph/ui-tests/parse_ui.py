#!/usr/bin/env python3
"""Parse HarmonyOS UI dump JSON and find element coordinates."""
import json
import sys

def find_text(node, target_text, results=None):
    if results is None:
        results = []
    if not isinstance(node, dict):
        return results
    attrs = node.get('attributes', {})
    if attrs.get('text', '') == target_text:
        results.append({
            'text': target_text,
            'bounds': attrs.get('bounds', ''),
            'clickable': attrs.get('clickable', ''),
            'accessibilityId': attrs.get('accessibilityId', '')
        })
    for child in node.get('children', []):
        find_text(child, target_text, results)
    return results

def parse_bounds(bounds_str):
    """Parse '[x1,y1][x2,y2]' → (x1, y1, x2, y2)"""
    import re
    m = re.match(r'\[(\d+),(\d+)\]\[(\d+),(\d+)\]', bounds_str)
    if not m:
        return None
    return tuple(int(x) for x in m.groups())

def center(bounds_str):
    b = parse_bounds(bounds_str)
    if b is None:
        return None
    x1, y1, x2, y2 = b
    return ((x1 + x2) // 2, (y1 + y2) // 2)

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'dump.json'
    target = sys.argv[2] if len(sys.argv) > 2 else '📈'
    with open(path) as f:
        data = json.load(f)
    matches = find_text(data, target)
    if not matches:
        print(f'NOT_FOUND: {target!r}')
        sys.exit(1)
    for m in matches:
        c = center(m['bounds'])
        if c:
            print(f"FOUND: {target!r} bounds={m['bounds']} center=({c[0]},{c[1]}) clickable={m['clickable']}")
