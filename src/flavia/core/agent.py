"""シンプルなFlavia AI料理エージェント"""

import json
import os
import random
import time
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

from .data_manager import data_manager

# 環境変数読み込み
load_dotenv()


class FlaviaAgent:
    """シンプルなAI料理エージェント"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("⚠️ ANTHROPIC_API_KEY が設定されていません")
    
    async def generate_recipe(self, user_request: str, debug_callback=None) -> Dict[str, Any]:
        """単発レシピ生成"""
        if debug_callback:
            debug_callback("🍳 レシピ生成開始...")
        
        try:
            # 個人データ読み込み
            personal_context = data_manager.create_context_for_ai()
            
            # プロンプト作成
            prompt = self._create_recipe_prompt(user_request, personal_context)
            
            # Claude API 呼び出し
            response = await self._call_claude_api(prompt, debug_callback)
            
            # JSON解析
            recipe_data = self._parse_json_response(response)
            
            if debug_callback:
                debug_callback("✅ レシピ生成完了！")
            
            return {
                "success": True,
                "recipe": recipe_data,
                "generation_time": datetime.now().isoformat(),
                "request": user_request
            }
        
        except Exception as e:
            if debug_callback:
                debug_callback(f"❌ エラー: {str(e)}")
            
            raise Exception(f"レシピ生成エラー: {str(e)}")
    
    async def generate_weekly_dinner_plan(
        self, 
        days: int = 7, 
        user_request: str = "", 
        debug_callback=None
    ) -> Dict[str, Any]:
        """週間夕食献立生成"""
        if debug_callback:
            debug_callback(f"📅 {days}日分の夕食献立生成開始...")
        
        try:
            # 個人データ読み込み
            personal_context = data_manager.create_context_for_ai()
            
            # プロンプト作成
            prompt = self._create_weekly_prompt(days, user_request, personal_context)
            
            # Claude API 呼び出し
            response = await self._call_claude_api(prompt, debug_callback)
            
            # JSON解析
            dinner_data = self._parse_json_response(response)
            
            # 買い物リスト（Claude AIから直接取得）
            shopping_list = dinner_data.get("shopping_list", {})
            
            if debug_callback:
                debug_callback("✅ 週間献立生成完了！")
            
            return {
                "success": True,
                "plan_days": days,
                "dinners": dinner_data.get("dinners", []),
                "shopping_list": shopping_list,
                "generation_time": datetime.now().isoformat(),
                "request": user_request
            }
        
        except Exception as e:
            if debug_callback:
                debug_callback(f"❌ エラー: {str(e)}")
            
            raise Exception(f"週間献立生成エラー: {str(e)}")
    
    def _create_recipe_prompt(self, user_request: str, personal_context: str) -> str:
        """レシピ生成用プロンプト"""
        return f"""
あなたは個人化AI料理パートナーFlaviaです。
栄養学と料理の専門知識を持ち、ユーザーの好みや制約に合わせた実用的なレシピを提案することが得意です。
以下の個人情報を考慮して、実用的なレシピを提案してください。

## ユーザーリクエスト
{user_request}

{personal_context}

## 出力形式（必須JSON）
以下の形式で出力してください：

{{
  "name": "料理名",
  "description": "料理の説明",
  "ingredients": ["材料1 分量", "材料2 分量"],
  "instructions": ["手順1", "手順2", "手順3"],
  "prep_time": 10,
  "cook_time": 20,
  "total_time": 30,
  "servings": 1,
  "estimated_cost": 800,
  "difficulty": "簡単",
  "notes": "ポイントや注意事項"
}}

**重要**: 絶対にJSON形式のみで回答してください。他のテキストは含めないでください。
"""
    
    def _create_weekly_prompt(self, days: int, user_request: str, personal_context: str) -> str:
        """週間献立用プロンプト"""
        # 多様性確保のためのランダム要素
        random.seed(int(time.time() * 1000) % 10000)
        chaos_hash = hashlib.md5(f"{time.time()}_{user_request}_{days}".encode()).hexdigest()[:8]
        
        # フォーマット例（抽象的）
        today = datetime.now()
        cost_range = f"{random.randint(500, 800)}-{random.randint(1200, 1800)}"
        
        examples_text = f'''    {{
      "day": 1,
      "date": "{today.strftime("%Y-%m-%d")}",
      "main_dish": "メイン料理名",
      "description": "料理の簡潔な説明",
      "ingredients": ["食材名 数量 単位", "食材名 数量 単位"],
      "detailed_recipe": {{
        "prep_time": 準備時間（分）,
        "cook_time": 調理時間（分）,
        "instructions": ["手順1", "手順2", "手順3"]
      }},
      "estimated_cost": 予想費用,
      "difficulty": "簡単/普通/難しい"
    }},
    ... ({days}日分すべて異なるジャンル・調理法で作成)'''
        
        return f"""
あなたは個人化AI料理パートナーFlaviaです。
【指定日数: {days}日分】の夕食献立を提案してください。

## 献立作成条件
- 作成期間: {days}日分の夕食メニュー
- 各日異なる料理ジャンル（和洋中、エスニック等）
- 実用的で現実的なレシピ

## 多様性確保ガイドライン - ID: {chaos_hash}
- 【必須】3日連続で同じ料理ジャンルにはしない（和食、中華、洋食、イタリアン、韓国料理、タイ料理など）
- 【必須】連続で同じ調理法にはしない（炒める、煮る、焼く、蒸す、揚げる）
- 【必須】主菜のバリエーション（肉料理、魚料理、野菜料理をバランス良く）
- 避けるべき：同じような味付け、同じような食材の組み合わせ
- 推奨：季節感、色彩豊かな組み合わせ、食感のバリエーション

## ユーザーリクエスト
{user_request or "栄養バランスの良い美味しい夕食"}

{personal_context}

## 材料記載の必須ルール
- **材料は必ず「食材名 数量 単位」の形式で記載**
- 例：「玉ねぎ 2個」「豚肉 300g」「醤油 大さじ2」
- 数量が不明な場合も「玉ねぎ 1個」「キャベツ 1/4個」のように推定値を記載
- 「適量」「お好みで」は避けて具体的な分量を記載

## 出力形式（必須JSON）
{{
  "dinners": [
{examples_text}
  ],
  "shopping_list": {{
    "vegetables": ["玉ねぎ 2個", "にんじん 1本", "キャベツ 1/4個"],
    "meat_fish": ["豚肉 300g", "鮭 2切れ"],
    "dairy": ["牛乳 200ml"],
    "canned_condiments": ["ホールトマト缶 1缶"],
    "other": ["スパゲッティ 200g"]
  }}
}}

**重要**: 
- 必ず{days}日分すべての献立を作成してください
- 材料は必ず「食材名 数量 単位」形式で記載してください
- 買い物リストは野菜→肉魚→乳製品→缶詰調味料→その他の順で整理してください
- 常備品（醤油、塩、胡椒、油等）は買い物リストに含めないでください
- 絶対にJSON形式のみで回答してください
- 日付は{today.strftime("%Y-%m-%d")}から開始してください
"""
    
    async def _call_claude_api(self, prompt: str, debug_callback=None) -> str:
        """Claude API呼び出し"""
        if not self.api_key:
            raise Exception("API Key が設定されていません")
        
        try:
            import anthropic
            
            if debug_callback:
                debug_callback("🤖 Claude AIに接続中...")
            
            client = anthropic.AsyncAnthropic(api_key=self.api_key)
            
            # 創造性重視の設定
            temperature = round(random.uniform(0.7, 0.9), 2)
            
            response = await client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=4000,
                temperature=temperature,
                system="あなたは日本の料理に詳しいAI料理パートナーFlaviaです。個人の嗜好と制約を理解して実用的なレシピを提案します。回答は必ず完全なJSON形式で出力してください。JSON以外のテキストは一切含めないでください。",
                messages=[{"role": "user", "content": prompt}]
            )
            
            if debug_callback:
                debug_callback(f"✅ AI応答受信 (temperature: {temperature})")
            
            return response.content[0].text
        
        except Exception as e:
            raise Exception(f"Claude API エラー: {str(e)}")
    
    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """JSON レスポンス解析"""
        try:
            # JSONブロックの抽出を試行
            response = response.strip()
            
            # ```json ブロックがある場合は抽出
            if "```json" in response:
                start = response.find("```json") + 7
                end = response.find("```", start)
                if end > start:
                    response = response[start:end].strip()
            
            # {} で囲まれた部分を抽出
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                response = response[start:end]
            
            return json.loads(response)
        
        except json.JSONDecodeError as e:
            print(f"JSON解析エラー: {e}")
            print(f"レスポンス内容: {response[:500]}...")
            raise Exception("AI応答のJSON解析に失敗しました")
    
    def _generate_shopping_list(self, dinners: List[Dict]) -> Dict[str, Any]:
        """買い物リスト生成（同じ食材をまとめて表示）"""
        pantry = data_manager.get_pantry_items()
        pantry_items = set()
        
        # 常備品をセットに追加
        for category in pantry.values():
            pantry_items.update(item.lower() for item in category)
        
        # 材料を収集
        all_ingredients = []
        for dinner in dinners:
            all_ingredients.extend(dinner.get("ingredients", []))
        
        # 常備品以外をフィルタリング
        shopping_ingredients = []
        for ingredient in all_ingredients:
            ingredient_clean = ingredient.split()[0].lower()
            if not any(pantry_item in ingredient_clean for pantry_item in pantry_items):
                shopping_ingredients.append(ingredient)
        
        # 同じ食材をまとめる
        grouped_items = self._group_same_ingredients(shopping_ingredients)
        
        return {
            "items": grouped_items,
            "total_items": len(grouped_items),
            "excluded_pantry_items": len(all_ingredients) - len(shopping_ingredients),
            "notes": "常備調味料は除外済み・同じ食材はまとめて表示"
        }
    
    def _group_same_ingredients(self, ingredients: List[str]) -> List[str]:
        """同じ食材をまとめる"""
        from collections import defaultdict
        import re
        
        # 食材ごとにグループ化
        ingredient_groups = defaultdict(list)
        
        for ingredient in ingredients:
            # 食材名を抽出（最初の単語）
            base_name = ingredient.split()[0]
            
            # 数字と単位を抽出
            quantity_match = re.search(r'(\d+(?:\.\d+)?)\s*([^0-9\s]*)', ingredient)
            if quantity_match:
                quantity = quantity_match.group(1)
                unit = quantity_match.group(2)
                ingredient_groups[base_name].append((float(quantity), unit, ingredient))
            else:
                # 数量が明確でない場合はそのまま
                ingredient_groups[base_name].append((0, "", ingredient))
        
        # まとめた結果を生成
        grouped_results = []
        for base_name, items in ingredient_groups.items():
            if len(items) == 1:
                # 1つだけの場合はそのまま
                grouped_results.append(items[0][2])
            else:
                # 複数ある場合はまとめる
                total_quantity = 0
                common_unit = ""
                original_items = []
                
                # 同じ単位のものを合計
                units = {}
                for quantity, unit, original in items:
                    if quantity > 0:
                        if unit in units:
                            units[unit] += quantity
                        else:
                            units[unit] = quantity
                    original_items.append(original)
                
                if units:
                    # 単位ごとに表示
                    unit_strings = []
                    for unit, total in units.items():
                        if total == int(total):
                            unit_strings.append(f"{int(total)}{unit}")
                        else:
                            unit_strings.append(f"{total}{unit}")
                    
                    if len(unit_strings) == 1:
                        grouped_results.append(f"{base_name} {unit_strings[0]}")
                    else:
                        grouped_results.append(f"{base_name} ({'+'.join(unit_strings)})")
                else:
                    # 数量不明の場合
                    grouped_results.append(f"{base_name} ({len(items)}回分)")
        
        return sorted(grouped_results)
    
    def send_shopping_list_to_discord(self, shopping_list: Dict[str, Any]) -> bool:
        """買い物リストをDiscordに送信"""
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        
        if not webhook_url:
            print("⚠️ DISCORD_WEBHOOK_URL が設定されていません")
            return False
        
        try:
            # メッセージをフォーマット
            message = self._format_shopping_list_for_discord(shopping_list)
            
            # Discord Webhook に送信
            data = {
                "content": message,
                "username": "Flavia AI 料理アシスタント",
                "avatar_url": "https://cdn-icons-png.flaticon.com/512/3135/3135715.png"
            }
            
            response = requests.post(webhook_url, json=data)
            return response.status_code == 204
            
        except Exception as e:
            print(f"Discord送信エラー: {e}")
            return False
    
    def _format_shopping_list_for_discord(self, shopping_list: Dict[str, Any]) -> str:
        """買い物リストをDiscord用にフォーマット"""
        total_items = shopping_list.get('total_items', 0)
        
        message = f"🛒 **買い物リスト** ({total_items}品目)\n"
        message += f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M')} 作成\n\n"
        
        # 食材リスト
        items = shopping_list.get('items', [])
        if items:
            # 3列に分けて表示
            for i, item in enumerate(items):
                if i % 3 == 0 and i > 0:
                    message += "\n"
                message += f"☐ {item}　"
            message += "\n"
        else:
            message += "購入する食材はありません。"
        
        # 備考
        notes = shopping_list.get('notes', '')
        if notes:
            message += f"\n💡 {notes}"
        
        message += "\n\n---\n🍳 Flavia AI 料理アシスタント"
        
        return message


# グローバルインスタンス
flavia_agent = FlaviaAgent()
