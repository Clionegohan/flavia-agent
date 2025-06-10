"""Flavia AI料理プロンプトアシスタント"""

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
    """個人化AI料理プロンプトアシスタント"""
    
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            print("⚠️ ANTHROPIC_API_KEY が設定されていません")
    
    async def generate(
        self, 
        request_type: str, 
        user_request: str, 
        days: int = 1, 
        debug_callback=None
    ) -> Dict[str, Any]:
        """統一生成メソッド（単発レシピ・週間献立対応）"""
        type_label = "レシピ" if request_type == "recipe" else f"{days}日分の献立"
        
        if debug_callback:
            debug_callback(f"🍳 {type_label}生成開始...")
        
        try:
            # 個人データ読み込み
            personal_context = data_manager.create_context_for_ai()
            
            # 統一プロンプト作成
            prompt = self._create_prompt(request_type, user_request, personal_context, days)
            
            # Claude API 呼び出し
            response = await self._call_claude_api(prompt, debug_callback)
            
            # JSON解析
            parsed_data = self._parse_json_response(response)
            
            # 統一出力形式
            result = self._format_output(request_type, parsed_data, user_request, days)
            
            if debug_callback:
                debug_callback(f"✅ {type_label}生成完了！")
            
            return result
        
        except Exception as e:
            if debug_callback:
                debug_callback(f"❌ エラー: {str(e)}")
            
            raise Exception(f"{type_label}生成エラー: {str(e)}")
    
    async def generate_recipe(self, user_request: str, debug_callback=None) -> Dict[str, Any]:
        """単発レシピ生成（レガシー互換）"""
        return await self.generate("recipe", user_request, 1, debug_callback)
    
    async def generate_weekly_dinner_plan(
        self, 
        days: int = 7, 
        user_request: str = "", 
        debug_callback=None
    ) -> Dict[str, Any]:
        """週間夕食献立生成（レガシー互換）"""
        return await self.generate("weekly", user_request, days, debug_callback)
    
    def _create_prompt(self, request_type: str, user_request: str, personal_context: str, days: int = 1) -> str:
        """統一プロンプト生成メソッド"""
        if request_type == "recipe":
            # 単発レシピ用（days=1の週間献立として処理）
            return self._create_weekly_prompt_content(1, user_request, personal_context)
        elif request_type == "weekly":
            return self._create_weekly_prompt_content(days, user_request, personal_context)
        else:
            raise ValueError(f"未対応のリクエスト種別: {request_type}")
    
    def _create_weekly_prompt_content(self, days: int, user_request: str, personal_context: str) -> str:
        """週間献立用プロンプト内容"""
        # 多様性確保のためのランダム要素
        random.seed(int(time.time() * 1000) % 10000)
        chaos_hash = hashlib.md5(f"{time.time()}_{user_request}_{days}".encode()).hexdigest()[:8]
        
        # フォーマット例（抽象的）
        today = datetime.now()
        
        examples_text = f'''    {{
      "day": 1,
      "date": "{today.strftime("%Y-%m-%d")}",
      "main_dish": "メイン料理名",
      "description": "料理の魅力と特徴を2-3行で説明",
      "ingredients": [
        "玉ねぎ 1個（約200g・薄切り）",
        "豚こま切れ肉 300g（一口大）",
        "醤油 大さじ2",
        "みりん 大さじ1"
      ],
      "detailed_recipe": {{
        "prep_time": 準備時間（分）,
        "cook_time": 調理時間（分）,
        "instructions": [
          "★準備：玉ねぎは薄切り、豚肉は一口大に切る。調味料は事前に混ぜておく",
          "フライパンを中火で熱し、油大さじ1を入れる。豚肉を入れ、表面が白くなるまで2-3分炒める",
          "玉ねぎを加え、中火で5分炒める。玉ねぎが透明になり、しんなりしたらOK",
          "★ポイント：調味料を加え、弱火で2分煮絡める。焦げないよう混ぜながら調理",
          "味見をして調整。器に盛り、お好みで青ねぎを散らして完成"
        ]
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

## 材料・調理手順の詳細化ルール
- **材料は必ず「食材名 数量 単位（下ごしらえ）」の形式で記載**
- 例：「玉ねぎ 1個（約200g・薄切り）」「豚肉 300g（一口大）」
- **調理手順は具体的かつ詳細に記載**
- 火加減・時間・見た目の変化を必ず含める
- 例：「中火で5分炒め、玉ねぎが透明になったら」
- 重要なポイントには「★」をつけて強調
- 「適量」「お好みで」は避けて具体的な分量・手順を記載

## 出力形式（必須JSON）
{{
  "dinners": [
{examples_text}
  ],
  "shopping_list": [
    "玉ねぎ 2個", "にんじん 1本", "キャベツ 1/4個",
    "豚肉 300g", "鮭 2切れ", 
    "牛乳 200ml",
    "ホールトマト缶 1缶", "スパゲッティ 200g"
  ]
}}

## 買い物リスト作成の必須ルール
- **必ずカテゴリ順で並べる**: 野菜類 → 肉・魚類 → 乳製品 → 調味料・缶詰 → その他の順番
- 同じカテゴリ内ではアルファベット順に整理
- 例：「玉ねぎ 2個, にんじん 1本, キャベツ 1/4個, 豚肉 300g, 鮭 2切れ, 牛乳 200ml, ホールトマト缶 1缶」
- 常備品（醤油、塩、胡椒、油、だしの素等）は含めない

**重要**: 
- 必ず{days}日分すべての献立を作成してください
- 材料は必ず「食材名 数量 単位」形式で記載してください
- 買い物リストは必ずカテゴリ順（野菜→肉魚→乳製品→調味料→その他）で並べてください
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
    
    def _format_output(self, request_type: str, parsed_data: Dict[str, Any], user_request: str, days: int) -> Dict[str, Any]:
        """統一出力形式"""
        base_result = {
            "success": True,
            "generation_time": datetime.now().isoformat(),
            "request": user_request
        }
        
        if request_type == "recipe":
            # 単発レシピ形式
            base_result.update({
                "recipe": parsed_data
            })
        elif request_type == "weekly":
            # 週間献立形式
            base_result.update({
                "plan_days": days,
                "dinners": parsed_data.get("dinners", []),
                "shopping_list": parsed_data.get("shopping_list", {})
            })
        
        return base_result
    
    
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
