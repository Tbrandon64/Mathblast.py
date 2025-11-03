import os
app_data = os.path.join(os.getenv('APPDATA') or os.path.expanduser('~'), 'MathBlast')
print('APP_DATA_DIR=', app_data)
print('PROFILES_FILE=', os.path.join(app_data, 'profiles.json'))
print('exists=', os.path.exists(os.path.join(app_data, 'profiles.json')))
