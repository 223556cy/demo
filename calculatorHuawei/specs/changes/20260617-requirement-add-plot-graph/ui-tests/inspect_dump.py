import sys
import os
import json

# Default dump file (can be overridden by 1st arg)
dump_path = sys.argv[1] if len(sys.argv) > 1 else 'specs/changes/20260617-requirement-add-plot-graph/ui-tests/dump_graph2.json'

try:
    with open(dump_path, 'r', encoding='utf-8') as f:
        obj = json.load(f)
    print('top keys:', list(obj.keys())[:10])
    print('len children:', len(obj.get('children', [])))

    count = 0
    def walk(n, depth=0):
        global count
        if isinstance(n, dict):
            a = n.get('attributes', {})
            t = a.get('text', '')
            b = a.get('bounds', '')
            c = a.get('clickable', '')
            if t and t.strip():
                print(f'  text={t!r} bounds={b} clickable={c}')
                count += 1
                if count > 50:
                    return
            for ch in n.get('children', []):
                walk(ch, depth+1)
                if count > 50:
                    return
    walk(obj)
    print('total with text:', count)
except Exception as e:
    print('ERROR:', e)
    traceback.print_exc()
sys.exit(0)
