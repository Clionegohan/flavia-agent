"""特売情報を取得・解析するモジュール"""

from typing import List, Dict, Optional, Any
from datetime import datetime
import re
from dataclasses import dataclass

from ..utils.file_utils import safe_write_text_file, safe_read_text_file, get_storage_path


@dataclass
class SaleItem:
    """特売商品情報"""
    name: str
    price: str
    original_price: Optional[str] = None
    discount_rate: Optional[str] = None
    category: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SaleInfo:
    """特売情報データ"""
    store_name: str
    date: str
    items: List[SaleItem]
    url: str
    fetched_at: datetime


class SaleInfoFetcher:
    """特売情報の取得・管理クラス"""
    
    def __init__(self):
        self.storage_path = get_storage_path()
        self.cache_file = self.storage_path / "sale_cache.json"
    
    def fetch_sale_info(self, url: str, store_name: str = "") -> Optional[SaleInfo]:
        """
        WebFetchツールを使って特売情報を取得
        注意: この関数は実際にはWebFetchツールを呼び出す部分で使用される
        """
        # この部分は後でWebFetchツールと連携する際に実装
        # 現在はプレースホルダー
        pass
    
    def parse_sale_content(self, content: str, store_name: str, url: str) -> SaleInfo:
        """取得した特売情報のコンテンツを解析"""
        items = []
        
        # 一般的な特売情報のパターンを解析
        # 価格パターン: "商品名 ○○円" "○○円（税込）" 
        price_patterns = [
            r'([^0-9]+)\s*(\d+)円',
            r'([^0-9]+)\s*¥(\d+)',
            r'([^0-9]+)\s*(\d+)円\s*\(税込\)',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                item_name = match[0].strip()
                price = f"{match[1]}円"
                
                # 商品名の清理
                item_name = self._clean_item_name(item_name)
                
                if self._is_valid_food_item(item_name):
                    category = self._categorize_item(item_name)
                    items.append(SaleItem(
                        name=item_name,
                        price=price,
                        category=category
                    ))
        
        # 重複除去
        unique_items = []
        seen_names = set()
        for item in items:
            if item.name not in seen_names:
                unique_items.append(item)
                seen_names.add(item.name)
        
        return SaleInfo(
            store_name=store_name or "不明なスーパー",
            date=datetime.now().strftime("%Y-%m-%d"),
            items=unique_items,
            url=url,
            fetched_at=datetime.now()
        )
    
    def _clean_item_name(self, name: str) -> str:
        """商品名の清理"""
        # 不要な文字や記号を除去
        name = re.sub(r'[★☆♪※【】\[\]◆◇○●△▲]', '', name)
        name = re.sub(r'\s+', ' ', name)  # 複数のスペースを1つに
        name = name.strip()
        
        # 一般的な宣伝文句を除去
        remove_words = ['特価', '特売', '新商品', '限定', 'セール', 'お買い得', 'おすすめ']
        for word in remove_words:
            name = name.replace(word, '')
        
        return name.strip()
    
    def _is_valid_food_item(self, name: str) -> bool:
        """食材として有効かチェック"""
        if len(name) < 2:
            return False
        
        # 明らかに食材でないものを除外
        invalid_keywords = [
            '送料', '配送', '手数料', 'ポイント', 'クーポン', 
            '割引', 'セール', '特典', '会員', 'お知らせ'
        ]
        
        for keyword in invalid_keywords:
            if keyword in name:
                return False
        
        return True
    
    def _categorize_item(self, name: str) -> str:
        """商品をカテゴリ分類"""
        categories = {
            '肉類': ['肉', '牛', '豚', '鶏', 'チキン', 'ハム', 'ソーセージ', 'ベーコン'],
            '魚介類': ['魚', 'サーモン', '鮭', 'まぐろ', 'さば', 'えび', 'かに', '刺身', '寿司'],
            '野菜': ['野菜', 'キャベツ', '大根', 'にんじん', 'じゃがいも', 'たまねぎ', 'トマト', 'きゅうり', 'レタス'],
            '果物': ['りんご', 'みかん', 'バナナ', 'いちご', 'ぶどう', 'メロン', 'すいか'],
            '米・パン': ['米', 'パン', '食パン', 'ご飯'],
            '麺類': ['うどん', 'そば', 'パスタ', 'ラーメン', '中華麺'],
            '調味料': ['醤油', '味噌', '砂糖', '塩', '油', 'ドレッシング', 'ソース'],
            '乳製品': ['牛乳', 'チーズ', 'ヨーグルト', 'バター'],
            '卵・豆腐': ['卵', '豆腐', '納豆']
        }
        
        name_lower = name.lower()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in name_lower:
                    return category
        
        return 'その他'
    
    def filter_items_by_preferences(self, sale_info: SaleInfo, 
                                  liked_categories: List[str],
                                  disliked_items: List[str]) -> List[SaleItem]:
        """ユーザーの好みに基づいて特売商品をフィルタリング"""
        filtered_items = []
        
        for item in sale_info.items:
            # 苦手な食材をチェック
            is_disliked = False
            for disliked in disliked_items:
                if disliked in item.name:
                    is_disliked = True
                    break
            
            if is_disliked:
                continue
            
            # 好みのカテゴリかチェック
            if not liked_categories or item.category in liked_categories:
                filtered_items.append(item)
        
        return filtered_items
    
    def get_recommended_items(self, sale_info: SaleInfo, 
                            user_preferences: Dict[str, Any]) -> List[SaleItem]:
        """ユーザーの嗜好に基づいて推奨商品を選出"""
        # ユーザーの好みデータから推奨カテゴリを抽出
        liked_categories = []
        
        # 料理の好みから推測
        cuisine_prefs = user_preferences.get('cuisine_preferences', [])
        for pref in cuisine_prefs:
            if pref.rating >= 4:  # 4つ星以上
                if '和食' in pref.name:
                    liked_categories.extend(['魚介類', '野菜', '米・パン', '調味料'])
                elif '中華' in pref.name:
                    liked_categories.extend(['肉類', '野菜', '麺類'])
                elif '洋食' in pref.name or 'イタリアン' in pref.name:
                    liked_categories.extend(['肉類', 'パスタ', 'チーズ'])
        
        # 重複除去
        liked_categories = list(set(liked_categories))
        
        # 苦手な食材
        disliked_items = user_preferences.get('disliked_foods', [])
        
        # フィルタリング実行
        recommended = self.filter_items_by_preferences(
            sale_info, liked_categories, disliked_items
        )
        
        # 価格やカテゴリで並び替え（推奨度順）
        def recommendation_score(item: SaleItem) -> int:
            score = 0
            
            # カテゴリによる重み付け
            if item.category in ['肉類', '野菜', '米・パン']:
                score += 10  # 基本的な食材は優先
            
            # 価格の魅力度（仮の実装）
            try:
                price = int(re.findall(r'\d+', item.price)[0])
                if price < 200:
                    score += 5
                elif price < 500:
                    score += 3
            except:
                pass
            
            return score
        
        recommended.sort(key=recommendation_score, reverse=True)
        return recommended[:10]  # 上位10個を返す
    
    def save_sale_info(self, sale_info: SaleInfo) -> bool:
        """特売情報をキャッシュに保存"""
        try:
            import json
            from pathlib import Path
            
            # ディレクトリが存在しない場合は作成
            self.storage_path.mkdir(parents=True, exist_ok=True)
            
            # SaleInfoをdict形式に変換
            data = {
                'store_name': sale_info.store_name,
                'date': sale_info.date,
                'url': sale_info.url,
                'fetched_at': sale_info.fetched_at.isoformat(),
                'items': [
                    {
                        'name': item.name,
                        'price': item.price,
                        'original_price': item.original_price,
                        'discount_rate': item.discount_rate,
                        'category': item.category,
                        'notes': item.notes
                    }
                    for item in sale_info.items
                ]
            }
            
            # JSONファイルに保存
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"特売情報の保存に失敗: {e}")
            return False
    
    def load_cached_sale_info(self) -> Optional[SaleInfo]:
        """キャッシュされた特売情報を読み込み"""
        try:
            import json
            
            if not self.cache_file.exists():
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # dictからSaleInfoオブジェクトに変換
            items = [
                SaleItem(
                    name=item_data['name'],
                    price=item_data['price'],
                    original_price=item_data.get('original_price'),
                    discount_rate=item_data.get('discount_rate'),
                    category=item_data.get('category'),
                    notes=item_data.get('notes')
                )
                for item_data in data['items']
            ]
            
            return SaleInfo(
                store_name=data['store_name'],
                date=data['date'],
                items=items,
                url=data['url'],
                fetched_at=datetime.fromisoformat(data['fetched_at'])
            )
            
        except Exception as e:
            print(f"キャッシュの読み込みに失敗: {e}")
            return None