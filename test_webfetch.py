"""WebFetch機能のテストスクリプト"""

import asyncio
from datetime import datetime
from src.flavia_agent.rag.web_sale_fetcher import WebSaleFetcher
from src.flavia_agent.services.recipe_service import RecipeService


def test_webfetch_instruction():
    """WebFetch指示の生成テスト"""
    print("=== WebFetch指示生成テスト ===")
    
    fetcher = WebSaleFetcher()
    url = "https://www.universe.co.jp/store/detail/102021030.html?recordno=99"
    target_date = "2025-06-07"
    
    instruction = fetcher.get_webfetch_instruction(url, target_date)
    
    print(f"URL: {instruction['url']}")
    print(f"対象日: {instruction['target_date']}")
    print(f"期待する情報: {instruction['expected_info']}")
    print("\n=== 生成されたプロンプト ===")
    print(instruction['prompt'])
    print("=" * 50)


def test_recipe_service_without_sales():
    """特売情報なしでのレシピ提案テスト"""
    print("\n=== 特売情報なしレシピ提案テスト ===")
    
    service = RecipeService()
    
    try:
        result = service.suggest_recipe_without_sales("今日の夕食におすすめの和食を教えて")
        
        print(f"成功: {result['success']}")
        if result['success']:
            print(f"レシピ提案: {result['recipe'][:200]}...")
            print(f"ユーザー制約: {result['user_considerations']}")
            print(f"注意事項: {result.get('note', '')}")
        
    except Exception as e:
        print(f"エラー: {e}")
    
    print("=" * 50)


def test_sale_content_analysis():
    """特売コンテンツ解析のテスト"""
    print("\n=== 特売コンテンツ解析テスト ===")
    
    # サンプルの特売情報コンテンツ
    sample_content = """
    本日6月7日の特売情報
    
    肉類
    鶏もも肉 398円
    豚バラ肉 298円
    牛こま切れ 580円
    
    野菜
    キャベツ 198円
    大根 158円
    じゃがいも 248円
    
    魚介類
    サーモン 398円
    さば 298円
    """
    
    fetcher = WebSaleFetcher()
    url = "https://www.universe.co.jp/store/detail/102021030.html?recordno=99"
    target_date = "2025-06-07"
    
    try:
        sale_info, status = fetcher.analyze_web_content(
            sample_content, url, "ユニバース", target_date
        )
        
        print(f"解析結果: {status}")
        if sale_info:
            print(f"店舗名: {sale_info.store_name}")
            print(f"日付: {sale_info.date}")
            print(f"商品数: {len(sale_info.items)}")
            print("\n商品リスト:")
            for item in sale_info.items:
                print(f"- {item.name}: {item.price} ({item.category})")
        
    except Exception as e:
        print(f"エラー: {e}")
    
    print("=" * 50)


def test_context_building():
    """コンテキスト構築のテスト"""
    print("\n=== コンテキスト構築テスト ===")
    
    from src.flavia_agent.rag import ContextBuilder
    
    builder = ContextBuilder()
    
    # レシピ用コンテキスト
    recipe_context = builder.build_recipe_context()
    print("=== レシピ用コンテキスト ===")
    print(recipe_context[:400] + "...")
    
    # 買い物用コンテキスト
    shopping_context = builder.build_shopping_context()
    print("\n=== 買い物用コンテキスト ===")
    print(shopping_context[:400] + "...")
    
    print("=" * 50)


def test_integrated_prompt():
    """統合プロンプト生成のテスト"""
    print("\n=== 統合プロンプト生成テスト ===")
    
    from src.flavia_agent.rag.sale_info_fetcher import SaleInfo, SaleItem
    from src.flavia_agent.rag import ContextBuilder
    
    # サンプル特売情報
    sample_items = [
        SaleItem(name="鶏もも肉", price="398円", category="肉類"),
        SaleItem(name="キャベツ", price="198円", category="野菜"),
        SaleItem(name="大根", price="158円", category="野菜"),
        SaleItem(name="じゃがいも", price="248円", category="野菜"),
    ]
    
    sale_info = SaleInfo(
        store_name="ユニバース",
        date="2025-06-07",
        items=sample_items,
        url="test_url",
        fetched_at=datetime.now()
    )
    
    fetcher = WebSaleFetcher()
    builder = ContextBuilder()
    
    user_context = builder.build_recipe_context()
    user_request = "今日の夕食に野菜たっぷりの和食を作りたい"
    
    integrated_prompt = fetcher.create_recipe_prompt_with_sales(
        sale_info, user_request, user_context
    )
    
    print("=== 統合プロンプト ===")
    print(integrated_prompt[:600] + "...")
    print("=" * 50)


if __name__ == "__main__":
    print("Flavia Agent WebFetch機能テスト開始\n")
    
    # 各テストを実行
    test_webfetch_instruction()
    test_context_building() 
    test_sale_content_analysis()
    test_integrated_prompt()
    test_recipe_service_without_sales()
    
    print("\nテスト完了！")
    
    print("\n=== 次のステップ ===")
    print("1. 実際のWebFetchツールでチラシサイトをテスト")
    print("2. WebFetch結果でRecipeServiceの完全テスト") 
    print("3. FlaviaAgentの個人化統合")