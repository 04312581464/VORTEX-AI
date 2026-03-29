# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['vortex_minimal_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('Tools', 'Tools'), ('prompts.py', '.'), ('business_uuid_auth.py', '.'), ('first_time_users.json', '.'), ('.env', '.')],
    hiddenimports=['livekit.agents', 'livekit.agents.cli', 'livekit.plugins', 'livekit.plugins.google', 'livekit.plugins.noise_cancellation', 'google.generativeai', 'aiohttp', 'websockets', 'requests', 'PIL', 'PIL.ImageGrab', 'pyautogui', 'mss', 'cv2', 'numpy', 'torch', 'transformers', 'sklearn', 'scipy', 'matplotlib', 'plotly', 'pygetwindow', 'psutil', 'cryptography', 'openai', 'langchain', 'faiss', 'tiktoken', 'tokenizers', 'opencv_python', 'sounddevice', 'soundfile', 'pyttsx3', 'speech_recognition', 'pydub', 'reportlab', 'python_docx', 'openpyxl', 'selenium', 'beautifulsoup4', 'lxml', 'bs4', 'scrapy', 'httpx', 'aiofiles', 'jinja2', 'click', 'rich', 'pydantic', 'sqlalchemy', 'pymongo', 'redis', 'celery', 'gunicorn', 'uvicorn', 'fastapi', 'flask'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pandas', 'tkinter'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='VortexAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
