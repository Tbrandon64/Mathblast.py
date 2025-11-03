"""
Profile debug helper
Runs a verbose save/load cycle and prints file paths and JSON contents so you can inspect what's happening.
Run from the workspace root:
    python profile_debug_patch.py
"""
import json
import os
import traceback

try:
    from MathBlast_Universal import save_profile, load_profiles, set_current_profile, get_current_profile, PROFILES_FILE, CURRENT_PROFILE_FILE
except Exception as e:
    print('Failed to import from MathBlast_Universal:', e)
    traceback.print_exc()
    raise

print('PROFILES_FILE =', PROFILES_FILE)
print('CURRENT_PROFILE_FILE =', CURRENT_PROFILE_FILE)
print('PROFILES_FILE exists:', os.path.exists(PROFILES_FILE))
print('CURRENT_PROFILE_FILE exists:', os.path.exists(CURRENT_PROFILE_FILE))

# show current contents
try:
    with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('\n--- profiles.json contents ---')
    print(json.dumps(data, indent=2))
except Exception as e:
    print('Could not read profiles.json:', e)

# create a test profile
name = 'Debug_AutoTest'
print(f"\nSaving profile '{name}'...")
ok = save_profile(name, 3, 7, stats={'debug': True})
print('save_profile returned:', ok)

# reload and print
profiles = load_profiles()
print('\n--- Reloaded profiles keys ---')
print(list(profiles.keys()))
if name in profiles:
    print('\nSaved profile data:')
    print(json.dumps(profiles[name], indent=2))
else:
    print('\nSaved profile not found in loaded profiles')

# set and read current profile
print('\nSetting current profile to', name)
set_current_profile(name)
print('get_current_profile() ->', get_current_profile())

# final file dumps
print('\nFinal files:')
for p in [PROFILES_FILE, CURRENT_PROFILE_FILE]:
    try:
        with open(p, 'r', encoding='utf-8') as f:
            content = f.read()
        print(f'--- {p} ---\n', content)
    except Exception as e:
        print(f'Could not read {p}:', e)
