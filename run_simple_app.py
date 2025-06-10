#!/usr/bin/env python3
"""Flavia AI 料理アシスタント - シンプル版 起動スクリプト"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

def main():
    """アプリケーション起動"""
    try:
        # Streamlit アプリを起動
        os.system(f"streamlit run {project_root}/src/flavia/ui/simple_app.py --server.port=8501")
    except KeyboardInterrupt:
        print("\n👋 Flavia を終了しました")
    except Exception as e:
        print(f"❌ 起動エラー: {e}")

if __name__ == "__main__":
    main()