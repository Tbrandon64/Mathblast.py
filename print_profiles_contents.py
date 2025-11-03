import json, os
path = os.path.join(os.getenv('APPDATA') or os.path.expanduser('~'), 'MathBlast', 'profiles.json')
print('path=', path)
try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('type=', type(data))
    print(json.dumps(data, indent=2))
except Exception as e:
    print('error reading:', e)
