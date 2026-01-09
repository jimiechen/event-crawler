# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from pathlib import Path

# 项目根目录 - 使用绝对路径确保打包时路径正确
ROOT_DIR = Path(os.path.abspath(os.path.dirname(__name__)))
BACKEND_DIR = ROOT_DIR.parent / 'stock-monitor-backend'
RESOURCES_DIR = ROOT_DIR / 'resources'

block_cipher = None

# 收集所有需要的文件和目录
datas = [
    # Chrome 扩展
    (str(RESOURCES_DIR / 'chrome-extension'), 'chrome-extension'),
    
    # CSV 数据文件
    (str(RESOURCES_DIR / 'csv-data'), 'csv-data'),
    
    # 配置文件
    (str(RESOURCES_DIR / 'configs'), 'configs'),
    
    # 后端静态文件
    (str(BACKEND_DIR / 'static'), 'static'),
    
    # 后端配置
    (str(BACKEND_DIR / 'config'), 'config'),
    
    # 后端应用代码
    (str(BACKEND_DIR / 'app'), 'app'),
]

# 收集隐藏导入
hiddenimports = [
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    'fastapi',
    'fastapi.middleware',
    'fastapi.middleware.cors',
    'fastapi.middleware.gzip',
    'fastapi.middleware.httpsredirect',
    'fastapi.middleware.trustedhost',
    'fastapi.responses',
    'fastapi.staticfiles',
    'sqlalchemy',
    'sqlalchemy.dialects',
    'sqlalchemy.dialects.mysql',
    'sqlalchemy.dialects.postgresql',
    'playwright',
    'playwright.async_api',
    'playwright.sync_api',
    'loguru',
    'pydantic',
    'pydantic_settings',
    'aiofiles',
    'APScheduler',
    'pandas',
    'numpy',
    'redis',
    'aioredis',
]

# 排除不需要的模块
excludes = [
    'tkinter',
    'matplotlib',
    'IPython',
    'jupyter',
    'notebook',
]

# PyInstaller 配置
a = Analysis(
    [str(ROOT_DIR / 'src' / 'launcher.py')],
    pathex=[str(ROOT_DIR), str(BACKEND_DIR)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='StockMonitor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='StockMonitor',
)

# macOS 特定配置
if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='StockMonitor.app',
        icon=str(RESOURCES_DIR / 'icons' / 'app_icon.icns') if (RESOURCES_DIR / 'icons' / 'app_icon.icns').exists() else None,
        bundle_identifier='com.stockmonitor.app',
        info_plist={
            'CFBundleName': 'StockMonitor',
            'CFBundleDisplayName': 'Stock Monitor',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'LSMinimumSystemVersion': '10.13.0',
        },
    )