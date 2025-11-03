MathBlast - Changes

2025-11-03 - Automated fixes and improvements
- Fixed NameError and import guards for Kivy/Tkinter.
- Added safe profile storage in %APPDATA%/MathBlast/profiles.json with atomic writes.
- Added Settings UI: create/load/delete profiles.
- Added current profile persistence (current_profile.txt) and visible profile label in main UI.
- Added AdaptiveEngine to adjust difficulty and integrated multiplier into problem generation.
- Added font scaling helper and applied to main UI; recomputes SCALE_FACTOR at runtime.
- Added Windows per-monitor DPI awareness calls to improve scaling on Windows.
- Added ONNX handwriting recognizer stub to avoid runtime NameErrors when ONNX isn't installed.
