import sys
import os
from pathlib import Path

def get_project_root() -> Path:
    """动态获取项目根目录（兼容开发模式和打包模式）"""
    if getattr(sys, 'frozen', False):
        # 打包后，根目录是 exe 所在目录
        return Path(sys.executable).parent
    else:
        # 开发模式（src/my_package/config/ 下）
        work_dir = Path(__file__).resolve().parent
        return work_dir.parent.parent.parent

# 定义关键路径
ROOT_DIR = get_project_root()
DATA_DIR = ROOT_DIR / "data"
WEIGHT_DIR = DATA_DIR / "weight"
OUTPUT_DIR = DATA_DIR / "output"
LOG_DIR = DATA_DIR / "logs"
DOC_DIR = ROOT_DIR / "docs"

os.makedirs(WEIGHT_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

setting_path = DATA_DIR / "setting.json"
log_path = LOG_DIR / "log.txt"
icon_path = DOC_DIR / "pngs" / "icon.ico"
icon_png_path = DOC_DIR / "pngs" / "icon.png"
payment_qr_path = DOC_DIR / "pngs" / "payment_qr.png"