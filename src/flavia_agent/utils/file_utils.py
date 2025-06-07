"""File handling utilities for personal data management"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
import json


def ensure_directory(path: Path) -> None:
    """ディレクトリが存在しない場合は作成する"""
    path.mkdir(parents=True, exist_ok=True)


def safe_read_text_file(file_path: Path) -> str:
    """テキストファイルを安全に読み込む"""
    try:
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        return ""
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return ""


def safe_write_text_file(file_path: Path, content: str) -> bool:
    """テキストファイルを安全に書き込む"""
    try:
        ensure_directory(file_path.parent)
        file_path.write_text(content, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error: Could not write to {file_path}: {e}")
        return False


def append_to_file(file_path: Path, content: str, add_timestamp: bool = True) -> bool:
    """ファイルに内容を追記する"""
    try:
        ensure_directory(file_path.parent)
        
        if add_timestamp:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = f"[{timestamp}] {content}"
        
        with open(file_path, 'a', encoding='utf-8') as f:
            f.write(content + '\n')
        return True
    except Exception as e:
        print(f"Error: Could not append to {file_path}: {e}")
        return False


def backup_file(file_path: Path) -> Optional[Path]:
    """ファイルのバックアップを作成する"""
    if not file_path.exists():
        return None
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f'.{timestamp}.backup')
        backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
        return backup_path
    except Exception as e:
        print(f"Warning: Could not create backup for {file_path}: {e}")
        return None


def get_personal_data_path() -> Path:
    """個人データディレクトリのパスを取得する"""
    return Path(__file__).parent.parent / "data" / "personal"


def get_storage_path() -> Path:
    """ストレージディレクトリのパスを取得する"""
    return Path(__file__).parent.parent / "data" / "storage"


def load_json_file(file_path: Path) -> Dict[str, Any]:
    """JSONファイルを読み込む"""
    try:
        if file_path.exists():
            return json.loads(file_path.read_text(encoding='utf-8'))
        return {}
    except Exception as e:
        print(f"Warning: Could not load JSON from {file_path}: {e}")
        return {}


def save_json_file(file_path: Path, data: Dict[str, Any]) -> bool:
    """JSONファイルに保存する"""
    try:
        ensure_directory(file_path.parent)
        file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error: Could not save JSON to {file_path}: {e}")
        return False