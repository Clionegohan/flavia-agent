#!/usr/bin/env python3
"""
Flavia AI - メインエントリーポイント

新しい構造でのStreamlitアプリケーション起動
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをPythonパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

if __name__ == "__main__":
    import streamlit.web.cli as stcli
    import sys
    
    # Streamlitアプリケーションのパス
    app_path = str(project_root / "src" / "flavia" / "ui" / "streamlit_app.py")
    
    # コマンドライン引数の設定
    sys.argv = [
        "streamlit",
        "run", 
        app_path,
        "--server.port=8501",
        "--server.address=localhost"
    ]
    
    # Streamlit起動
    stcli.main()