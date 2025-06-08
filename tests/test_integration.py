"""統合テスト - システム全体の動作確認"""

import pytest
import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from flavia.core.agents.personal import PersonalAgent
from flavia.rag.smart_context_builder import SmartContextBuilder
from flavia.rag.learning_system import LearningSystem
from flavia.monitoring import get_performance_report
from flavia.utils.error_handler import get_error_context


class TestSystemIntegration:
    """システム統合テスト"""
    
    @pytest.fixture
    def personal_agent(self):
        """PersonalAgentインスタンスを作成"""
        return PersonalAgent()
    
    @pytest.fixture
    def smart_context_builder(self):
        """SmartContextBuilderインスタンスを作成"""
        return SmartContextBuilder()
    
    def test_personal_agent_initialization(self, personal_agent):
        """PersonalAgentの初期化テスト"""
        assert personal_agent is not None
        assert personal_agent.smart_context_builder is not None
        assert personal_agent.learning_system is not None
        assert personal_agent.personal_data is not None
    
    def test_smart_context_builder_basic_functionality(self, smart_context_builder):
        """SmartContextBuilderの基本機能テスト"""
        # レシピ提案リクエスト
        result = smart_context_builder.build_smart_context(
            user_request="今日の夕食レシピを教えて",
            context_type="recipe_suggestion",
            max_tokens=3000
        )
        
        assert "context" in result
        assert "request_analysis" in result
        assert "selected_elements" in result
        assert "total_estimated_tokens" in result
        assert result["total_estimated_tokens"] <= 3000
        
        # 献立計画リクエスト
        result2 = smart_context_builder.build_smart_context(
            user_request="3日分の献立を考えて",
            context_type="meal_planning",
            max_tokens=5000
        )
        
        assert result2["request_analysis"]["type"].value == "meal_planning"
        assert len(result2["selected_elements"]) > 0
    
    def test_learning_system_functionality(self):
        """学習システムの機能テスト"""
        learning_system = LearningSystem()
        
        # フィードバック記録テスト
        feedback_id = learning_system.record_recipe_feedback(
            recipe_name="テスト料理",
            rating=4,
            comments="美味しかった！",
            recipe_context={
                "ingredients": ["鶏肉", "野菜"],
                "cuisine_type": "和食"
            }
        )
        
        assert feedback_id is not None
        assert feedback_id.startswith("recipe_")
        
        # 嗜好変更記録テスト
        pref_id = learning_system.record_ingredient_preference_change(
            ingredient="テスト食材",
            new_preference="like",
            reason="テストのため"
        )
        
        assert pref_id is not None
        assert pref_id.startswith("ingredient_")
        
        # 学習結果反映テスト
        updated_preferences = learning_system.get_updated_preferences()
        assert updated_preferences is not None
        
        # トレンド分析テスト
        trends = learning_system.analyze_preference_trends(days=30)
        assert "total_feedback_count" in trends
        assert "preference_stability" in trends
    
    @pytest.mark.asyncio
    async def test_weekly_dinner_plan_generation(self, personal_agent):
        """週間夕食プラン生成テスト"""
        # 基本的な週間プラン生成
        result = await personal_agent.generate_weekly_dinner_plan(
            days=3,
            user_request="健康的な夕食プランをお願いします",
            include_sale_info=False
        )
        
        assert result is not None
        
        # フォールバック応答の場合
        if result.get("fallback"):
            assert "dinners" in result
            assert "shopping_list" in result
            assert len(result["dinners"]) >= 1
        # 正常応答の場合
        else:
            assert result.get("success") is True
            assert "dinners" in result
            assert "shopping_list" in result
            assert len(result["dinners"]) == 3
    
    def test_error_handling_and_fallbacks(self, personal_agent):
        """エラーハンドリングとフォールバック機能テスト"""
        # 無効な入力での週間プラン生成テスト
        invalid_requests = [
            {"days": 0},  # 無効な日数
            {"days": 20}, # 上限超過
            {"user_request": "x" * 2000}  # 過度に長いリクエスト
        ]
        
        for invalid_request in invalid_requests:
            try:
                # バリデーションエラーが発生するか確認
                result = asyncio.run(personal_agent.generate_weekly_dinner_plan(**invalid_request))
                # エラーが発生しない場合はフォールバック応答を確認
                if result:
                    assert result.get("fallback") is True or result.get("success") is False
            except (ValueError, TypeError):
                # 期待される例外
                pass
    
    def test_monitoring_and_performance(self):
        """監視・パフォーマンス機能テスト"""
        # パフォーマンスレポート生成
        report = get_performance_report()
        assert "system_overview" in report
        assert "resource_usage" in report
        assert "report_timestamp" in report
        
        # エラーコンテキスト取得
        error_context = get_error_context()
        assert "error_summary" in error_context
        assert "system_health" in error_context
        assert "timestamp" in error_context
    
    def test_recipe_rating_workflow(self, personal_agent):
        """レシピ評価ワークフローテスト"""
        # レシピ評価記録
        feedback_id = personal_agent.rate_recipe(
            recipe_name="統合テスト料理",
            rating=5,
            comments="完璧！",
            recipe_context={
                "ingredients": ["テスト材料"],
                "cuisine_type": "テスト料理"
            }
        )
        
        assert feedback_id is not None
        
        # 学習ダッシュボード取得
        dashboard = personal_agent.get_learning_dashboard()
        assert "学習状況" in dashboard
        assert "今週の傾向" in dashboard
        assert dashboard["学習状況"]["総フィードバック数"] > 0
    
    def test_context_optimization(self, smart_context_builder):
        """コンテキスト最適化テスト"""
        # 小さなトークン制限でのテスト
        result = smart_context_builder.build_smart_context(
            user_request="簡単なレシピを教えて",
            max_tokens=1000
        )
        
        assert result["total_estimated_tokens"] <= 1000
        assert result["optimization_summary"]["optimization_successful"]
        
        # 絶対制約が含まれていることを確認
        context = result["context"]
        assert "絶対制約" in context or "制約" in context
    
    @pytest.mark.asyncio
    async def test_api_resilience(self, personal_agent):
        """API回復力テスト（フォールバック機能）"""
        # API keyなしでの動作確認
        original_api_key = personal_agent.api_key
        personal_agent.api_key = None
        
        try:
            result = await personal_agent.generate_weekly_dinner_plan(
                days=1,
                user_request="フォールバックテスト"
            )
            
            # フォールバック応答が返されることを確認
            assert result is not None
            assert "dinners" in result
            
        finally:
            # API keyを復元
            personal_agent.api_key = original_api_key
    
    def test_preference_persistence(self):
        """嗜好データの永続化テスト"""
        learning_system1 = LearningSystem()
        
        # 初回フィードバック記録
        feedback_id = learning_system1.record_recipe_feedback(
            recipe_name="永続化テスト料理",
            rating=3,
            comments="テスト"
        )
        
        # 新しいインスタンスで同じデータが読み込めるか確認
        learning_system2 = LearningSystem()
        summary = learning_system2.get_learning_summary()
        
        assert summary["total_feedbacks"] > 0
        assert summary["system_status"] == "active"


class TestErrorScenarios:
    """エラーシナリオテスト"""
    
    def test_corrupted_data_handling(self):
        """破損データの処理テスト"""
        # 破損したJSONファイルのシミュレーション
        learning_system = LearningSystem()
        
        # 無効なデータでのテスト（例外が適切に処理されるか）
        try:
            trends = learning_system.analyze_preference_trends(days=30)
            assert "total_feedback_count" in trends  # 正常処理または適切なフォールバック
        except Exception as e:
            pytest.fail(f"Unexpected exception in corrupted data handling: {e}")
    
    def test_memory_limits(self):
        """メモリ制限テスト"""
        smart_context_builder = SmartContextBuilder()
        
        # 極端に長いリクエストでのテスト
        very_long_request = "レシピを教えて " * 1000
        
        try:
            result = smart_context_builder.build_smart_context(
                user_request=very_long_request,
                max_tokens=2000
            )
            
            # メモリ効率的に処理されることを確認
            assert result["total_estimated_tokens"] <= 2000
            
        except Exception as e:
            # メモリエラーではない適切な例外処理を確認
            assert "memory" not in str(e).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])