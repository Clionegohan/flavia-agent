"""Claude API接続テスト"""

import os
from dotenv import load_dotenv

# .envファイルを明示的に読み込み
load_dotenv()

def test_claude_api():
    """Claude API接続をテスト"""
    print("=== Claude API接続テスト ===")
    
    # 環境変数確認
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not anthropic_key:
        print("❌ ANTHROPIC_API_KEYが見つかりません")
        return False
    
    if anthropic_key == "your-claude-api-key-here":
        print("❌ デフォルトのプレースホルダーのままです")
        return False
    
    print(f"✅ Anthropic APIキー設定済み (長さ: {len(anthropic_key)}文字)")
    
    # 実際にAPIテスト
    try:
        from src.flavia_agent.agent.flavia import FlaviaAgent
        
        print("\n=== FlaviaAgent初期化テスト ===")
        agent = FlaviaAgent(
            primary_provider="anthropic",
            fallback_provider=None  # フォールバックなしでテスト
        )
        
        print("✅ Agent初期化成功")
        
        # 実際の献立生成テスト
        print("\n=== 献立生成テスト ===")
        from src.flavia_agent.data.models import MealPreferences
        
        test_preferences = MealPreferences(
            budget=20.0,
            dietary_restrictions=[],
            cuisine_preferences=["Japanese"],
            cooking_time=30,
            servings=2
        )
        
        import asyncio
        recipes = asyncio.run(agent.generate_meal_plan(test_preferences))
        
        print(f"✅ 生成されたレシピ数: {len(recipes)}")
        if recipes:
            print(f"最初のレシピ: {recipes[0].name}")
            print(f"コスト: ${recipes[0].estimated_cost:.2f}")
        
        print("\n🎉 Claude API接続＆レシピ生成成功！")
        return True
        
    except Exception as e:
        print(f"❌ エラー: {e}")
        print(f"エラータイプ: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = test_claude_api()
    if success:
        print("\n=== 次のステップ ===")
        print("1. 既存Streamlitアプリでレシピ生成テスト")
        print("2. 新RAGシステムと統合")
        print("3. 特売情報連携テスト")
    else:
        print("\nAPIキーの設定を確認してください。")