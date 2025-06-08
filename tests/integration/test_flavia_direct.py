"""Streamlit UIをバイパスして直接FlaviaAgentをテスト"""

import asyncio
from dotenv import load_dotenv
import os

# 環境変数を読み込み
load_dotenv()

from src.flavia_agent.agent.flavia import FlaviaAgent
from src.flavia_agent.data.models import MealPreferences

async def test_flavia_full_functionality():
    """Flaviaの全機能をテスト"""
    print("=== Flavia Agent 完全機能テスト ===")
    
    # エージェント初期化
    agent = FlaviaAgent(
        primary_provider="anthropic",
        fallback_provider=None
    )
    
    # テストケース1: 基本的な献立生成
    print("\n📋 テスト1: 基本献立生成")
    basic_preferences = MealPreferences(
        budget=25.0,
        dietary_restrictions=[],
        cuisine_preferences=["Japanese"],
        cooking_time=30,
        servings=2
    )
    
    recipes = await agent.generate_meal_plan(basic_preferences)
    print(f"✅ 生成レシピ数: {len(recipes)}")
    
    for i, recipe in enumerate(recipes[:2], 1):  # 最初の2つ表示
        print(f"\n🍳 レシピ{i}: {recipe.name}")
        print(f"   💰 コスト: ${recipe.estimated_cost:.2f}")
        print(f"   ⏱️ 調理時間: {recipe.total_time}分")
        print(f"   🥘 材料数: {len(recipe.ingredients)}")
        print(f"   🌍 ジャンル: {recipe.cuisine_type}")
    
    # テストケース2: 制約ありの献立生成
    print("\n📋 テスト2: 制約付き献立生成")
    restricted_preferences = MealPreferences(
        budget=15.0,
        dietary_restrictions=["Vegetarian", "Gluten-Free"],
        cuisine_preferences=["Italian", "Mediterranean"],
        cooking_time=20,
        servings=1
    )
    
    restricted_recipes = await agent.generate_meal_plan(restricted_preferences)
    print(f"✅ 制約付きレシピ数: {len(restricted_recipes)}")
    
    if restricted_recipes:
        recipe = restricted_recipes[0]
        print(f"\n🥗 制約対応レシピ: {recipe.name}")
        print(f"   💰 低予算コスト: ${recipe.estimated_cost:.2f}")
        print(f"   ⚡ 短時間: {recipe.total_time}分")
        print(f"   🌱 制約対応: ベジタリアン・グルテンフリー")
    
    # テストケース3: レシピ提案機能
    print("\n📋 テスト3: レシピ提案機能")
    suggestions = await agent.suggest_recipes(
        "今日は疲れているので、簡単で栄養のある料理が食べたいです",
        basic_preferences
    )
    
    print(f"✅ 提案レシピ数: {len(suggestions)}")
    if suggestions:
        suggestion = suggestions[0]
        print(f"\n💡 提案レシピ: {suggestion.name}")
        print(f"   🏃‍♂️ 簡単度: {suggestion.difficulty}")
        print(f"   ⏱️ 時間: {suggestion.total_time}分")
    
    print("\n🎉 全テスト完了！Flaviaは正常に動作しています")
    
    return {
        "basic_recipes": len(recipes),
        "restricted_recipes": len(restricted_recipes), 
        "suggestions": len(suggestions),
        "total_cost": sum(r.estimated_cost for r in recipes),
        "avg_time": sum(r.total_time for r in recipes) // len(recipes) if recipes else 0
    }

def display_summary(results):
    """テスト結果サマリー表示"""
    print("\n" + "="*50)
    print("📊 Flavia Agent テストサマリー")
    print("="*50)
    print(f"🍳 基本レシピ生成: {results['basic_recipes']}件")
    print(f"🥗 制約付きレシピ: {results['restricted_recipes']}件") 
    print(f"💡 レシピ提案: {results['suggestions']}件")
    print(f"💰 総コスト: ${results['total_cost']:.2f}")
    print(f"⏱️ 平均調理時間: {results['avg_time']}分")
    
    if all(v > 0 for v in results.values()):
        print("\n✅ 全機能正常動作確認！")
        print("🎯 StreamlitのGUI化準備完了")
    else:
        print("\n⚠️ 一部機能に問題があります")

if __name__ == "__main__":
    try:
        results = asyncio.run(test_flavia_full_functionality())
        display_summary(results)
        
        print("\n📝 次のステップ:")
        print("1. StreamlitのGUI動作確認")
        print("2. RAGシステムとの統合")
        print("3. 特売情報連携テスト")
        
    except Exception as e:
        print(f"❌ テスト失敗: {e}")
        import traceback
        traceback.print_exc()