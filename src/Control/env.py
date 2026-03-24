import os
import sys

def get_project_root() -> str:
    """
    统一获取项目根目录：
    1. 如果是打包后的 exe (frozen)，从 exe 位置向上查找项目根目录
    2. 如果是开发模式 python main.py，使用 dist 目录
    """
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        # Phantom Courier.exe 在 bin/ 目录下，向上找两级就是项目根目录
        return os.path.dirname(exe_dir)
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        # 开发模式下，使用 dist 目录
        return os.path.join(project_root, 'dist')
