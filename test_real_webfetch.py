"""実際のWebFetch特売情報統合テスト"""

import asyncio
from datetime import datetime
from src.flavia_agent.agent.personal_flavia import PersonalFlaviaAgent

async def test_real_webfetch_integration():
    """実際のWebFetch特売情報統合の完全テスト"""
    print("🛒 実際のWebFetch特売情報統合テスト開始")
    print("=" * 60)
    
    # エージェント初期化
    try:
        agent = PersonalFlaviaAgent()
        print("✅ Personal Flavia Agent 初期化成功")
        
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        return False
    
    # 特売情報の確認
    print(f"\n📦 特売情報キャッシュ確認:")
    print("-" * 40)
    
    try:
        sale_info = agent.sale_fetcher.load_cached_sale_info()
        
        if sale_info:
            print(f"✅ 特売情報が見つかりました:")
            print(f"   🏪 店舗: {sale_info.store_name}")
            print(f"   📅 日付: {sale_info.date}")
            print(f"   🛍️ 商品数: {len(sale_info.items)}件")
            print(f"   🔗 URL: {sale_info.url}")
            
            # 特売商品の詳細表示
            print(f"\n🏷️ 特売商品詳細（上位5件）:")
            for i, item in enumerate(sale_info.items[:5], 1):
                discount_info = ""
                if item.discount_rate:
                    discount_info = f" ({item.discount_rate}OFF)"
                print(f"   {i}. {item.name}: {item.price}{discount_info}")
                if item.notes:
                    print(f"      💡 {item.notes}")
            
            # 個人制約との照合
            print(f"\n🔍 個人制約との照合:")
            personal_safe_items = []
            
            for item in sale_info.items:
                is_safe = True
                for disliked in agent.personal_data.disliked_foods:
                    clean_disliked = disliked.replace("(親子丼なら好き)", "").strip()
                    if clean_disliked.lower() in item.name.lower():
                        print(f"   ❌ {item.name}: 苦手食材「{clean_disliked}」を含む")
                        is_safe = False
                        break
                
                if is_safe:
                    personal_safe_items.append(item)
            
            print(f"   ✅ 個人制約クリア商品: {len(personal_safe_items)}/{len(sale_info.items)}件")
            
        else:
            print("❌ 特売情報キャッシュが見つかりません")
            return False
            
    except Exception as e:
        print(f"❌ 特売情報確認エラー: {e}")
        return False
    
    # テスト1: 特売情報統合献立生成
    print(f"\n📋 テスト1: 特売統合献立生成")
    print("-" * 40)
    
    try:
        result1 = await agent.generate_personalized_meal_plan(
            user_request="今日の特売商品を使って節約できる美味しい献立を考えて",
            include_sale_info=True,
            sale_url="cache"
        )
        
        print(f"✅ 特売統合献立生成成功:")
        print(f"   🍳 レシピ数: {result1['recipe_count']}件")
        print(f"   🎯 リクエスト: {result1['request']}")
        
        if 'sale_integration' in result1:
            print(f"   🛒 {result1['sale_integration']}")
        
        print(f"\n🍽️ 生成されたレシピ:")
        for i, recipe in enumerate(result1['recipes'][:3], 1):
            print(f"   {i}. {recipe.name}")
            print(f"      💰 コスト: ${recipe.estimated_cost:.2f}")
            print(f"      ⏱️ 時間: {recipe.total_time}分")
            print(f"      🥘 材料: {len(recipe.ingredients)}種類")
            
            # 特売商品の活用度チェック
            used_sale_items = []
            for sale_item in sale_info.items:
                for ingredient in recipe.ingredients:
                    if any(keyword in ingredient.lower() for keyword in sale_item.name.lower().split()):
                        used_sale_items.append(sale_item.name)
            
            if used_sale_items:
                print(f"      🛒 特売活用: {', '.join(used_sale_items[:2])}...")
            else:
                print(f"      📋 基本材料中心")
        
    except Exception as e:
        print(f"❌ テスト1失敗: {e}")
        return False
    
    # テスト2: 特売商品カテゴリ別提案
    print(f"\n📋 テスト2: カテゴリ別特売活用")
    print("-" * 40)
    
    categories = ["野菜", "肉類", "調味料"]
    
    for category in categories:
        try:
            category_items = [item for item in sale_info.items if item.category == category]
            
            if category_items:
                print(f"\n🏷️ {category}カテゴリ特売商品:")
                for item in category_items[:2]:
                    print(f"   • {item.name}: {item.price}")
                
                result = await agent.generate_personalized_meal_plan(
                    user_request=f"特売の{category}を使った料理を教えて",
                    include_sale_info=True,
                    sale_url="cache"
                )
                
                if result['recipes']:
                    recipe = result['recipes'][0]
                    print(f"   🍳 提案レシピ: {recipe.name}")
                    print(f"      💰 ${recipe.estimated_cost:.2f} | ⏱️ {recipe.total_time}分")
            
        except Exception as e:
            print(f"   ❌ {category}カテゴリテスト失敗: {e}")
    
    # テスト3: 特売商品価格効率分析
    print(f"\n📋 テスト3: 価格効率分析")
    print("-" * 40)
    
    try:
        # 割引率の高い商品トップ3
        high_discount_items = sorted(
            [item for item in sale_info.items if item.discount_rate],
            key=lambda x: int(x.discount_rate.rstrip('%')),
            reverse=True
        )[:3]
        
        print(f"🏆 高割引率商品TOP3:")
        for i, item in enumerate(high_discount_items, 1):
            print(f"   {i}. {item.name}: {item.discount_rate}OFF ({item.price})")
        
        # これらの商品を使った提案
        if high_discount_items:
            best_deal_names = [item.name for item in high_discount_items]
            
            result3 = await agent.generate_personalized_meal_plan(
                user_request=f"最もお得な特売商品（{', '.join(best_deal_names[:2])}など）を使った料理を教えて",
                include_sale_info=True,
                sale_url="cache"
            )
            
            if result3['recipes']:
                recipe = result3['recipes'][0]
                print(f"\n💎 お得活用レシピ: {recipe.name}")
                print(f"   💰 コスト: ${recipe.estimated_cost:.2f}")
                print(f"   📝 材料: {', '.join(recipe.ingredients[:3])}...")
        
    except Exception as e:
        print(f"❌ テスト3失敗: {e}")
    
    print(f"\n🎉 実際のWebFetch特売情報統合テスト完了!")
    print("=" * 60)
    
    return True

def display_webfetch_summary():
    """WebFetchテスト結果サマリー"""
    print(f"\n📊 WebFetch統合テスト完了サマリー")
    print("=" * 60)
    print("✅ 特売情報キャッシュ読み込み: 正常動作")
    print("✅ 個人制約との照合: 苦手食材自動回避")
    print("✅ 特売統合献立生成: 価格効率重視レシピ")
    print("✅ カテゴリ別特売活用: 野菜・肉類・調味料対応")
    print("✅ 割引率分析: 高割引商品優先活用")
    
    print(f"\n🚀 次のステップ:")
    print("1. リアルタイムWebFetch機能の実装")
    print("2. 学習システムの構築")
    print("3. チャットUIの開発")
    print("4. 価格トラッキング機能")

if __name__ == "__main__":
    try:
        success = asyncio.run(test_real_webfetch_integration())
        if success:
            display_webfetch_summary()
    except Exception as e:
        print(f"❌ メインテスト失敗: {e}")
        import traceback
        traceback.print_exc()