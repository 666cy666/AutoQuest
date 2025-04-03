# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],  # 主入口文件
    pathex=[],
    binaries=[],
    datas=[
        ('Api', 'Api'),  # API目录
        ('Config', 'Config'),  # 配置文件目录
        ('Log', 'Log'),  # 日志目录
        ('Output', 'Output'),  # 输出目录
        ('Util', 'Util'),  # 工具类目录
        ('main.ipynb', '.'),  # Jupyter notebook文件
    ],
    hiddenimports=[
        'DrissionPage',
        'selenium',
        'PIL',
        'cv2',
        'numpy',
        'injector',
        'PyQt6',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        '_pytest',
        'pytest',
        'doctest',
        'pdb',
        'pydoc',
        'pyreadline',
    ],  # 排除不需要的模块以减小体积
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# 优化文件大小
a.datas = [d for d in a.datas if not d[0].startswith('tcl')]
a.datas = [d for d in a.datas if not d[0].startswith('tk')]

pyz = PYZ(
    a.pure,
    a.zipped_data,
    cipher=block_cipher
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='app',  # 生成的exe名称
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 设置为False以去除黑框
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Doc/images/icon.ico',  # 暂时注释掉图标
) 