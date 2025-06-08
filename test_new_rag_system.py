#!/usr/bin/env python3
"""新RAGシステムのテストスクリプト"""

import asyncio
import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from flavia.rag.smart_context_builder import SmartContextBuilder
from flavia.rag.learning_system import LearningSystem
from flavia.rag.preference_parser import PreferenceParser


async def test_smart_context_builder():
    """スマートコンテキストビルダーのテスト"""
    print("=== スマートコンテキストビルダーテスト ===")
    
    try:
        builder = SmartContextBuilder()
        
        # 各種リクエストタイプのテスト
        test_requests = [
            ("今日の夕食のレシピを教えて", "recipe_suggestion"),
            ("3日分の献立を考えて", "meal_planning"),
            ("今日の買い物リストを作って", "shopping_list"),
            ("卵の代用品を教えて", "ingredient_substitution"),
            ("健康的な料理を提案して", "dietary_advice")
        ]
        
        for request, expected_type in test_requests:
            print(f"\n--- テスト: {request} ---")
            
            result = builder.build_smart_context(
                user_request=request,
                max_tokens=3000
            )
            
            print(f"リクエスト分析: {result['request_analysis']['type']}")
            print(f"選択された要素: {result['selected_elements']}")
            print(f"推定トークン数: {result['total_estimated_tokens']}")
            print(f"最適化成功: {result['optimization_summary']['optimization_successful']}")
            
            # コンテキストの一部を表示
            context_preview = result['context'][:200] + "..." if len(result['context']) > 200 else result['context']
            print(f"コンテキスト(抜粋): {context_preview}")
            
            print("✅ テスト成功")
        
        return True
        
    except Exception as e:
        print(f"❌ スマートコンテキストビルダーテスト失敗: {e}")
        return False


async def test_learning_system_integration():
    """学習システム統合テスト"""
    print("\n=== 学習システム統合テスト ===")
    
    try:
        learning_system = LearningSystem()
        
        # テスト用フィードバックの記録
        print("テスト用フィードバックを記録中...")
        
        feedback_id = learning_system.record_recipe_feedback(
            recipe_name="鶏の照り焼き",
            rating=4,
            comments="美味しかった！",
            recipe_context={
                "ingredients": ["鶏肉", "醤油", "みりん", "砂糖"],
                "cuisine_type": "和食"
            }
        )
        print(f"フィードバックID: {feedback_id}")
        
        # 食材嗜好の変更テスト
        preference_id = learning_system.record_ingredient_preference_change(
            ingredient="ブロッコリー",
            new_preference="like",
            reason="栄養価が高いから"
        )
        print(f"嗜好変更ID: {preference_id}")
        
        # 学習結果を反映した嗜好データの取得
        print("学習結果を反映した嗜好データを取得中...")
        updated_preferences = learning_system.get_updated_preferences()
        
        print(f"更新された好きな食材数: {len(updated_preferences.liked_foods)}")
        print(f"更新された嫌いな食材数: {len(updated_preferences.disliked_foods)}")
        print(f"料理嗜好数: {len(updated_preferences.cuisine_preferences)}")
        
        # トレンド分析
        print("嗜好トレンド分析中...")
        trends = learning_system.analyze_preference_trends(days=30)
        print(f"分析期間のフィードバック数: {trends['total_feedback_count']}")
        print(f"推奨事項: {trends['recommendations']}")
        
        # 学習サマリー
        summary = learning_system.get_learning_summary()
        print(f"学習サマリー: {summary}")
        
        print("✅ 学習システム統合テスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 学習システム統合テスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_preference_parser():
    """嗜好パーサーテスト"""
    print("\n=== 嗜好パーサーテスト ===")
    
    try:
        parser = PreferenceParser()
        
        # 全嗜好データの解析
        print("全嗜好データを解析中...")
        preferences = parser.parse_all_preferences()
        
        print(f"基本プロフィール: {preferences.profile.age}歳{preferences.profile.gender}性")
        print(f"居住地: {preferences.profile.location}")
        print(f"家族構成: {preferences.profile.family_structure}")
        print(f"嫌いな食材: {preferences.disliked_foods}")
        print(f"料理嗜好数: {len(preferences.cuisine_preferences)}")
        print(f"健康目標: {preferences.health_goals}")
        print(f"最近のトレンド: {preferences.recent_trends}")
        
        # 利用可能調理器具
        available_equipment = preferences.cooking_equipment.get('available', [])
        unavailable_equipment = preferences.cooking_equipment.get('not_available', [])
        print(f"利用可能器具: {available_equipment}")
        print(f"使用不可器具: {unavailable_equipment}")
        
        print("✅ 嗜好パーサーテスト成功")
        return True
        
    except Exception as e:
        print(f"❌ 嗜好パーサーテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_integrated_rag_workflow():
    """統合RAGワークフローテスト"""
    print("\n=== 統合RAGワークフローテスト ===")
    
    try:
        # 1. スマートコンテキストビルダーでコンテキスト構築
        builder = SmartContextBuilder()
        
        user_request = "今晩の夕食で、健康的で簡単に作れるレシピを提案して"
        
        smart_context = builder.build_smart_context(
            user_request=user_request,
            context_type="recipe_suggestion",
            max_tokens=4000
        )
        
        print(f"ユーザーリクエスト: {user_request}")
        print(f"リクエスト分析: {smart_context['request_analysis']}")
        print(f"選択されたコンテキスト要素: {smart_context['selected_elements']}")
        print(f"コンテキストトークン数: {smart_context['total_estimated_tokens']}")
        
        # 2. コンテキストの品質確認
        context = smart_context['context']
        
        # 重要な制約が含まれているかチェック
        constraints_included = "絶対制約" in context
        preferences_included = "料理嗜好" in context
        capabilities_included = "調理環境" in context
        
        print(f"制約情報含まれている: {constraints_included}")
        print(f"嗜好情報含まれている: {preferences_included}")
        print(f"調理能力情報含まれている: {capabilities_included}")
        
        # 3. 学習データが反映されているかチェック
        learning_included = "学習済み嗜好情報" in context
        print(f"学習データ含まれている: {learning_included}")
        
        # 4. コンテキストサイズの適切性
        context_size = len(context)
        size_appropriate = 1000 <= context_size <= 10000  # 適切な範囲
        print(f"コンテキストサイズ: {context_size}文字")
        print(f"サイズ適切: {size_appropriate}")
        
        # 5. 最適化効果の確認
        optimization = smart_context['optimization_summary']
        selection_ratio = optimization['selection_ratio']
        print(f"選択率: {selection_ratio:.2%}")
        print(f"除外された要素: {optimization['excluded_by_priority']}")
        
        if constraints_included and preferences_included and size_appropriate:
            print("✅ 統合RAGワークフローテスト成功")
            return True
        else:
            print("❌ 統合RAGワークフローテスト失敗 - 品質要件未達")
            return False
        
    except Exception as e:
        print(f"❌ 統合RAGワークフローテスト失敗: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """全テストを実行"""
    print("🚀 新RAGシステム総合テスト開始")
    print("=" * 50)
    
    test_results = []
    
    # 各テストを実行
    test_results.append(await test_preference_parser())
    test_results.append(await test_learning_system_integration())
    test_results.append(await test_smart_context_builder())
    test_results.append(await test_integrated_rag_workflow())
    
    # 結果集計
    passed = sum(test_results)
    total = len(test_results)
    
    print("\n" + "=" * 50)
    print(f"📊 テスト結果: {passed}/{total} 成功")
    
    if passed == total:
        print("🎉 全テスト成功！新RAGシステムは正常に動作しています。")
        print("\n✨ 主な改善点:")
        print("- スマートコンテキスト選択によるトークン効率化")
        print("- 実際の学習データ統合")
        print("- リクエストタイプ別最適化")
        print("- 品質重視のコンテキスト構築")
        return True
    else:
        print("⚠️ 一部テスト失敗。修正が必要です。")
        return False


if __name__ == "__main__":
    result = asyncio.run(run_all_tests())
    sys.exit(0 if result else 1)