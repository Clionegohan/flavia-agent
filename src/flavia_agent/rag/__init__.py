"""RAG (Retrieval-Augmented Generation) functionality for personal preference management"""

from .preference_parser import PreferenceParser, PreferenceData
from .context_builder import ContextBuilder
from .sale_info_fetcher import SaleInfoFetcher, SaleInfo, SaleItem

__all__ = [
    'PreferenceParser',
    'PreferenceData', 
    'ContextBuilder',
    'SaleInfoFetcher',
    'SaleInfo',
    'SaleItem'
]