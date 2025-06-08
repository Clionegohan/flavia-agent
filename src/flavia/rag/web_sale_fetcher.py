"""Webベースの特売情報取得システム"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
import re
from dataclasses import dataclass

from .sale_info_fetcher import SaleInfoFetcher, SaleInfo, SaleItem
from ..utils.file_utils import safe_write_text_file, get_storage_path


class WebSaleFetcher(SaleInfoFetcher):
    """Web特売情報の取得・解析に特化したクラス"""
    
    def __init__(self):
        super().__init__()
        self.web_fetch_available = True  # WebFetchツールが利用可能
    
    def fetch_and_analyze_sale_info(self, url: str, store_name: str = "", 
                                  target_date: Optional[str] = None) -> Tuple[Optional[SaleInfo], str]:
        """
        WebFetchツールを使って特売情報を取得・解析
        
        Args:
            url: チラシページのURL
            store_name: 店舗名
            target_date: 対象日付（YYYY-MM-DD形式）
            
        Returns:
            (SaleInfo, status_message): 特売情報と処理状況メッセージ
        """
        if not target_date:
            target_date = datetime.now().strftime("%Y-%m-%d")
        
        # WebFetchツールを使用する際のプロンプト
        fetch_prompt = self._build_fetch_prompt(target_date)
        
        # 実際のWebFetch実行は呼び出し元で行う必要がある
        # ここでは解析用のメソッドを提供
        return None, f"WebFetch実行準備完了。URL: {url}, 対象日: {target_date}"
    
    def _build_fetch_prompt(self, target_date: str) -> str:
        """WebFetchツール用のプロンプトを構築"""
        return f"""
このページから以下の情報を抽出してください：

1. 特売・セール情報の日付範囲
   - 対象日: {target_date}
   - この日付が含まれているかチェック

2. 特売商品リスト
   - 商品名
   - 価格（通常価格と特価の両方があれば）
   - 割引率や「○○円引き」などの情報
   - 商品カテゴリ（肉、魚、野菜、etc.）

3. ページの構造
   - チラシ情報がどこに表示されているか
   - 動的読み込みが必要かどうか
   - 他のページへのリンクが必要かどうか

4. 取得可能な食材情報
   - 肉類、魚介類、野菜、果物、調味料等
   - それぞれの価格と特売情報

特に食材に関する情報を重点的に抽出してください。
日付が合わない場合はその旨を明記してください。
"""
    
    def analyze_web_content(self, content: str, url: str, store_name: str, 
                          target_date: str) -> Tuple[Optional[SaleInfo], str]:
        """WebFetchで取得したコンテンツを解析"""
        
        # 1. 日付チェック
        date_status = self._check_date_validity(content, target_date)
        if not date_status["valid"]:
            return None, f"日付が一致しません: {date_status['message']}"
        
        # 2. 特売商品の抽出
        sale_items = self._extract_sale_items_from_web(content)
        
        if not sale_items:
            return None, "特売商品情報が見つかりませんでした"
        
        # 3. SaleInfoオブジェクトの作成
        sale_info = SaleInfo(
            store_name=store_name or self._extract_store_name(content, url),
            date=target_date,
            items=sale_items,
            url=url,
            fetched_at=datetime.now()
        )
        
        # 4. キャッシュに保存
        self.save_sale_info(sale_info)
        
        return sale_info, f"特売情報を取得しました。{len(sale_items)}件の商品"
    
    def _check_date_validity(self, content: str, target_date: str) -> Dict[str, any]:
        """コンテンツから日付情報を抽出して妥当性をチェック"""
        
        # 日付パターンの検索
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{1,2})/(\d{1,2})',  # MM/DD形式
            r'(\d{1,2})月(\d{1,2})日',
            r'本日|今日',
            r'明日',
            r'(\d{1,2})日\s*\(.*?\)',  # 7日(金)のような形式
        ]
        
        found_dates = []
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        
        for pattern in date_patterns:
            matches = re.findall(pattern, content)
            found_dates.extend(matches)
        
        # 特別なキーワードチェック
        today = datetime.now()
        if '本日' in content or '今日' in content:
            if target_dt.date() == today.date():
                return {"valid": True, "message": "本日の特売情報"}
        
        if '明日' in content:
            tomorrow = today + timedelta(days=1)
            if target_dt.date() == tomorrow.date():
                return {"valid": True, "message": "明日の特売情報"}
        
        # 具体的な日付との照合
        target_month = target_dt.month
        target_day = target_dt.day
        
        for match in found_dates:
            if len(match) == 2:  # MM/DD または 月日形式
                try:
                    month = int(match[0])
                    day = int(match[1])
                    if month == target_month and day == target_day:
                        return {"valid": True, "message": f"{month}月{day}日の特売情報"}
                except ValueError:
                    continue
        
        # 範囲指定（○日〜○日）もチェック
        range_pattern = r'(\d{1,2})日.*?(\d{1,2})日'
        range_matches = re.findall(range_pattern, content)
        for start_day, end_day in range_matches:
            try:
                start = int(start_day)
                end = int(end_day)
                if start <= target_day <= end:
                    return {"valid": True, "message": f"{start}日〜{end}日の特売期間"}
            except ValueError:
                continue
        
        return {"valid": False, "message": "指定日の特売情報が見つかりません"}
    
    def _extract_sale_items_from_web(self, content: str) -> List[SaleItem]:
        """Webコンテンツから特売商品を抽出"""
        items = []
        
        # 改良された価格パターン
        price_patterns = [
            # 基本的な価格パターン
            r'([^0-9\n]+?)\s*(\d{1,4})\s*円',
            r'([^0-9\n]+?)\s*¥\s*(\d{1,4})',
            r'([^0-9\n]+?)\s*(\d{1,4})\s*円\s*\(税込\)',
            
            # 特売表示付き
            r'([^0-9\n]+?)\s*特価\s*(\d{1,4})\s*円',
            r'([^0-9\n]+?)\s*セール\s*(\d{1,4})\s*円',
            r'([^0-9\n]+?)\s*(\d{1,4})\s*円\s*特価',
            
            # 割引表示
            r'([^0-9\n]+?)\s*(\d{1,4})\s*円\s*(\d+%\s*OFF|半額)',
            r'([^0-9\n]+?)\s*通常\s*(\d{1,4})\s*円\s*→\s*(\d{1,4})\s*円',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, content, re.MULTILINE)
            for match in matches:
                if len(match) >= 2:
                    item_name = self._clean_item_name(match[0])
                    price = f"{match[1]}円"
                    
                    # 割引情報があれば抽出
                    discount_info = ""
                    if len(match) > 2:
                        discount_info = match[2]
                    
                    if self._is_valid_food_item(item_name) and len(item_name) > 1:
                        category = self._categorize_item(item_name)
                        
                        items.append(SaleItem(
                            name=item_name,
                            price=price,
                            discount_rate=discount_info if discount_info else None,
                            category=category,
                            notes="Web取得"
                        ))
        
        # 重複除去（より厳密に）
        unique_items = {}
        for item in items:
            # 商品名の正規化
            normalized_name = re.sub(r'\s+', '', item.name.lower())
            if normalized_name not in unique_items:
                unique_items[normalized_name] = item
        
        return list(unique_items.values())
    
    def _extract_store_name(self, content: str, url: str) -> str:
        """コンテンツまたはURLから店舗名を抽出"""
        
        # コンテンツから店舗名のパターンを検索
        store_patterns = [
            r'([\w\s]+)店',
            r'店舗名[：:]\s*([\w\s]+)',
            r'<title[^>]*>([^<]+)</title>',
        ]
        
        for pattern in store_patterns:
            match = re.search(pattern, content)
            if match:
                store_name = match.group(1).strip()
                if len(store_name) > 0 and len(store_name) < 20:
                    return store_name
        
        # URLから推測
        if 'universe' in url:
            return 'ユニバース'
        elif 'aeon' in url:
            return 'イオン'
        elif 'ito-yokado' in url:
            return 'イトーヨーカドー'
        
        return '不明なスーパー'
    
    def create_recipe_prompt_with_sales(self, sale_info: SaleInfo, 
                                      user_request: str, 
                                      user_context: str) -> str:
        """特売情報とユーザー情報を統合したレシピ提案プロンプト"""
        
        # 特売商品のカテゴリ別整理
        categorized_items = {}
        for item in sale_info.items:
            category = item.category or "その他"
            if category not in categorized_items:
                categorized_items[category] = []
            categorized_items[category].append(f"{item.name}({item.price})")
        
        prompt_parts = [
            "# 特売情報を活用したレシピ提案",
            "",
            f"## 今日の特売情報 - {sale_info.store_name} ({sale_info.date})",
        ]
        
        # カテゴリ別に特売商品を表示
        for category, items in categorized_items.items():
            prompt_parts.append(f"### {category}")
            for item in items[:5]:  # 各カテゴリ最大5つ
                prompt_parts.append(f"- {item}")
        
        prompt_parts.extend([
            "",
            "## ユーザー情報",
            user_context,
            "",
            "## ユーザーのリクエスト",
            user_request,
            "",
            "## 提案要件",
            "1. 特売商品を積極的に活用したレシピを提案",
            "2. ユーザーの苦手な食材は絶対に使用しない",
            "3. 利用可能な調理器具の範囲内で作れるもの",
            "4. 指定された調理時間内で完成するもの",
            "5. 健康目標に配慮した栄養バランス",
            "",
            "特売商品の価格も考慮して、コストパフォーマンスの良いレシピを提案してください。"
        ])
        
        return "\n".join(prompt_parts)
    
    def get_webfetch_instruction(self, url: str, target_date: str) -> Dict[str, str]:
        """WebFetchツール実行用の指示を生成"""
        return {
            "url": url,
            "prompt": self._build_fetch_prompt(target_date),
            "expected_info": "特売商品リスト、価格情報、日付範囲",
            "target_date": target_date
        }