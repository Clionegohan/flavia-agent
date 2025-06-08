"""レシピ提案サービス - 特売情報とRAG情報を統合"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime
import asyncio

from ...rag.context_builder import ContextBuilder
from ...rag.preference_parser import PreferenceParser
from ...rag.web_sale_fetcher import WebSaleFetcher
from ...exceptions import RecipeGenerationError


class RecipeService:
    """特売情報とユーザー嗜好を組み合わせたレシピ提案サービス"""
    
    def __init__(self):
        self.context_builder = ContextBuilder()
        self.preference_parser = PreferenceParser()
        self.sale_fetcher = WebSaleFetcher()
    
    async def suggest_recipe_with_sales(self, 
                                      user_request: str,
                                      sale_url: str,
                                      target_date: Optional[str] = None,
                                      use_webfetch: bool = True) -> Dict[str, any]:
        """
        特売情報を活用したレシピ提案のメインメソッド
        
        Args:
            user_request: ユーザーからのリクエスト
            sale_url: 特売情報のURL
            target_date: 対象日付（YYYY-MM-DD）
            use_webfetch: WebFetchツールを使用するか
            
        Returns:
            レシピ提案結果と処理情報
        """
        try:
            # 1. 日付の設定
            if not target_date:
                target_date = datetime.now().strftime("%Y-%m-%d")
            
            # 2. ユーザーの嗜好コンテキストを構築
            user_context = self.context_builder.build_recipe_context()
            
            # 3. 特売情報の取得
            if use_webfetch:
                sale_result = await self._fetch_sale_info_with_webfetch(
                    sale_url, target_date
                )
            else:
                # キャッシュから取得または手動入力
                sale_result = await self._get_cached_or_manual_sale_info(
                    sale_url, target_date
                )
            
            if not sale_result["success"]:
                return {
                    "success": False,
                    "error": sale_result["error"],
                    "fallback_available": True
                }
            
            sale_info = sale_result["sale_info"]
            
            # 4. 統合プロンプトの作成
            integrated_prompt = self.sale_fetcher.create_recipe_prompt_with_sales(
                sale_info, user_request, user_context
            )
            
            # 5. レシピ生成（プレースホルダー実装）
            recipe_response = f"統合プロンプトに基づくレシピ提案:\n{integrated_prompt[:200]}..."
            
            # 6. 結果の整理
            return {
                "success": True,
                "recipe": recipe_response,
                "sale_info": {
                    "store": sale_info.store_name,
                    "date": sale_info.date,
                    "items_count": len(sale_info.items),
                    "featured_items": self._get_featured_items(sale_info)
                },
                "user_considerations": self._extract_user_considerations(),
                "cost_estimate": self._estimate_cost(sale_info, recipe_response)
            }
            
        except Exception as e:
            raise RecipeGenerationError(
                f"レシピ生成中にエラーが発生しました: {str(e)}",
                details={"request": user_request, "url": sale_url, "date": target_date}
            )
    
    async def _fetch_sale_info_with_webfetch(self, url: str, 
                                           target_date: str) -> Dict[str, any]:
        """WebFetchツールを使用して特売情報を取得"""
        
        # WebFetchの指示を取得
        fetch_instruction = self.sale_fetcher.get_webfetch_instruction(url, target_date)
        
        try:
            # 実際のWebFetch実行
            # 注意: この部分は実際の使用時にWebFetchツールの結果を受け取る
            # 現在はプレースホルダーとして構造を示す
            
            # WebFetchツールの実行結果を待つ
            # webfetch_result = await self._execute_webfetch(
            #     fetch_instruction["url"], 
            #     fetch_instruction["prompt"]
            # )
            
            # テスト用のプレースホルダー応答
            webfetch_result = {
                "content": "特売情報の取得が必要です。WebFetchツールを実行してください。",
                "instruction": fetch_instruction
            }
            
            return {
                "success": False,
                "error": "WebFetch実行が必要",
                "instruction": fetch_instruction,
                "webfetch_result": webfetch_result
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"特売情報の取得に失敗: {str(e)}"
            }
    
    async def _get_cached_or_manual_sale_info(self, url: str, 
                                            target_date: str) -> Dict[str, any]:
        """キャッシュから特売情報を取得または手動入力を促す"""
        
        # キャッシュから読み込み
        cached_info = self.sale_fetcher.load_cached_sale_info()
        
        if cached_info and cached_info.date == target_date:
            return {
                "success": True,
                "sale_info": cached_info
            }
        
        # キャッシュがない場合は手動入力を促す
        return {
            "success": False,
            "error": "特売情報のキャッシュがありません。WebFetchまたは手動入力が必要です。"
        }
    
    def suggest_recipe_without_sales(self, user_request: str) -> Dict[str, any]:
        """特売情報なしでのレシピ提案"""
        
        try:
            # ユーザーコンテキストのみを使用
            user_context = self.context_builder.build_recipe_context()
            
            # シンプルなプロンプト作成
            prompt = f"""
# レシピ提案

## ユーザー情報
{user_context}

## リクエスト
{user_request}

## 要件
- ユーザーの苦手な食材は使用しない
- 利用可能な調理器具で作れるレシピ
- 健康目標に配慮した内容
- 調理時間の制約を考慮

上記に基づいて最適なレシピを提案してください。
"""
            
            # レシピ生成（プレースホルダー実装）
            response = f"個人化レシピ提案:\n{prompt[:200]}..."
            
            return {
                "success": True,
                "recipe": response,
                "user_considerations": self._extract_user_considerations(),
                "note": "特売情報は使用せずに提案しました"
            }
            
        except Exception as e:
            raise RecipeGenerationError(
                f"レシピ生成に失敗: {str(e)}",
                details={"request": user_request}
            )
    
    def _get_featured_items(self, sale_info) -> List[str]:
        """注目の特売商品を抽出"""
        featured = []
        
        # カテゴリ別に主要商品を選出
        categories = {}
        for item in sale_info.items:
            cat = item.category or "その他"
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(item)
        
        # 各カテゴリから1-2個選出
        for category, items in categories.items():
            if category in ["肉類", "野菜", "魚介類"]:
                featured.extend([f"{item.name}({item.price})" for item in items[:2]])
        
        return featured[:8]  # 最大8個
    
    def _extract_user_considerations(self) -> Dict[str, List[str]]:
        """ユーザーの制約・考慮事項を抽出"""
        data = self.preference_parser.parse_all_preferences()
        
        return {
            "避けるべき食材": data.disliked_foods,
            "健康目標": data.health_goals[:3],
            "調理制約": [
                f"平日調理時間: {data.profile.cooking_time_available.get('weekday', '30分')}",
                f"使用不可器具: {', '.join(data.cooking_equipment.get('not_available', [])[:3])}"
            ],
            "最近のトレンド": data.recent_trends[:3]
        }
    
    def _estimate_cost(self, sale_info, recipe_response: str) -> Dict[str, any]:
        """レシピのコスト概算"""
        
        # レシピから使用食材を抽出（簡易版）
        used_ingredients = []
        total_estimated_cost = 0
        
        # 特売商品の使用をチェック
        sale_items_used = []
        for item in sale_info.items:
            if item.name in recipe_response:
                sale_items_used.append(item)
                # 価格から数値を抽出
                try:
                    price = int(''.join(filter(str.isdigit, item.price)))
                    total_estimated_cost += price
                except:
                    pass
        
        return {
            "special_items_used": [f"{item.name}({item.price})" for item in sale_items_used],
            "estimated_total": f"約{total_estimated_cost}円" if total_estimated_cost > 0 else "計算不可",
            "cost_efficiency": "高" if len(sale_items_used) >= 2 else "中" if len(sale_items_used) == 1 else "低"
        }
    
    def process_webfetch_result(self, webfetch_content: str, url: str, 
                              target_date: str, user_request: str) -> Dict[str, any]:
        """WebFetchの結果を処理してレシピ提案"""
        
        try:
            # WebFetchの結果を解析
            sale_info, status_message = self.sale_fetcher.analyze_web_content(
                webfetch_content, url, "", target_date
            )
            
            if not sale_info:
                return {
                    "success": False,
                    "error": status_message,
                    "fallback_suggestion": "特売情報なしでのレシピ提案に切り替えますか？"
                }
            
            # ユーザーコンテキストを取得
            user_context = self.context_builder.build_recipe_context()
            
            # 統合プロンプトの作成
            integrated_prompt = self.sale_fetcher.create_recipe_prompt_with_sales(
                sale_info, user_request, user_context
            )
            
            # レシピ生成（プレースホルダー実装）
            recipe_response = f"WebFetch結果ベースレシピ:\n{integrated_prompt[:200]}..."
            
            return {
                "success": True,
                "recipe": recipe_response,
                "sale_info": {
                    "store": sale_info.store_name,
                    "date": sale_info.date,
                    "items_count": len(sale_info.items),
                    "featured_items": self._get_featured_items(sale_info)
                },
                "processing_note": status_message
            }
            
        except Exception as e:
            raise RecipeGenerationError(
                f"WebFetch結果の処理に失敗: {str(e)}",
                details={"url": url, "date": target_date}
            )