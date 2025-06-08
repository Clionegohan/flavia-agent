"""Flavia エージェント用カスタム例外クラス"""


class FlaviaException(Exception):
    """Flaviaエージェントのベース例外クラス"""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class RecipeGenerationError(FlaviaException):
    """レシピ生成に関するエラー"""
    pass


class DataParsingError(FlaviaException):
    """データ解析に関するエラー"""
    pass


class LearningSystemError(FlaviaException):
    """学習システムに関するエラー"""
    pass


class ContextBuildingError(FlaviaException):
    """コンテキスト構築に関するエラー"""
    pass


class PreferenceError(FlaviaException):
    """嗜好データに関するエラー"""
    pass


class SaleInfoError(FlaviaException):
    """特売情報取得に関するエラー"""
    pass