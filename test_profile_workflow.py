from MathBlast_Universal import save_profile, load_profiles, set_current_profile, get_current_profile, PROFILES_FILE, CURRENT_PROFILE_FILE
import json, os

name = 'AutoTest'
print('Creating profile:', name)
ok = save_profile(name, 2, 5)
print('save_profile returned', ok)

profiles = load_profiles()
print('Profiles keys:', list(profiles.keys()))

# set as current
set_current_profile(name)
print('current profile readback:', get_current_profile())

# print file contents
try:
    with open(PROFILES_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    print('profiles.json contains:', json.dumps(data.get(name, {}), indent=2))
except Exception as e:
    print('Failed to read profiles.json:', e)

try:
    with open(CURRENT_PROFILE_FILE, 'r', encoding='utf-8') as f:
        print('current_profile.txt contents:', f.read().strip())
except Exception as e:
    print('Failed to read current_profile.txt:', e)
