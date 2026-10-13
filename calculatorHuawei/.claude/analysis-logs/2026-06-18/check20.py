import json, glob, os
files = sorted(glob.glob(r'D:/huawei/my_sessions/sessions/hermes/rev-01/2026/06/*.jsonl'))
print('Total:', len(files))
for f in files:
    name = os.path.basename(f)
    if name.startswith('2026-06-17') or name.startswith('2026-06-18'):
        try:
            with open(f, encoding='utf-8', errors='ignore') as fp:
                content = fp.read()
        except:
            continue
        if 'issue 20' in content.lower() or '582ffba' in content or 'factorial-button' in content:
            for kw in ['factorial-button', '582ffba', 'Issue #20', '#20']:
                idx = content.find(kw)
                if idx >= 0:
                    snippet = content[max(0, idx-100):idx+300].replace('\n', ' ')
                    print(f'{name}: {kw}')
                    print(f'  CTX: {snippet[:400]}')
                    print()
                    break