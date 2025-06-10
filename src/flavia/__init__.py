"""
Flavia AI - シンプル料理パートナー

個人化されたAI料理アシスタント
"""

__version__ = "0.3.0"
__author__ = "Flavia Development Team"

from .core.agent import FlaviaAgent
from .core.data_manager import PersonalDataManager

__all__ = [
    "FlaviaAgent",
    "PersonalDataManager",
]