"""パフォーマンステスト - システムの性能評価"""

import pytest
import time
import asyncio
import sys
from pathlib import Path

# プロジェクトルートをパスに追加  
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from flavia.core.agents.personal import PersonalAgent
from flavia.rag.smart_context_builder import SmartContextBuilder
from flavia.monitoring import get_performance_report, metrics


class TestPerformance:
    """パフォーマンステストクラス"""
    
    @pytest.fixture
    def personal_agent(self):
        """PersonalAgentインスタンス"""
        return PersonalAgent()
    
    @pytest.fixture
    def smart_context_builder(self):
        """SmartContextBuilderインスタンス"""
        return SmartContextBuilder()
    
    def test_context_building_speed(self, smart_context_builder):
        """コンテキスト構築速度テスト"""
        requests = [
            "今日の夕食レシピを教えて",
            "3日分の献立プランをお願いします",
            "健康的な料理を提案して",
            "15分で作れる簡単レシピ"
        ]
        
        total_time = 0
        for request in requests:
            start_time = time.time()
            
            result = smart_context_builder.build_smart_context(
                user_request=request,
                max_tokens=3000
            )
            
            elapsed = time.time() - start_time
            total_time += elapsed
            
            # 個別の処理時間チェック（1秒以内）
            assert elapsed < 1.0, f"Context building too slow: {elapsed:.2f}s for '{request}'"
            
            # 結果品質チェック
            assert result["total_estimated_tokens"] <= 3000
            assert len(result["selected_elements"]) > 0
        
        # 平均処理時間チェック（0.5秒以内）
        avg_time = total_time / len(requests)
        assert avg_time < 0.5, f"Average context building time too slow: {avg_time:.2f}s"
    
    @pytest.mark.asyncio
    async def test_weekly_dinner_plan_performance(self, personal_agent):
        """週間夕食プラン生成パフォーマンステスト"""
        test_cases = [
            {"days": 1, "request": "1日分の夕食"},
            {"days": 3, "request": "3日分の夕食プラン"},
            {"days": 7, "request": "1週間の夕食プラン"}
        ]
        
        for case in test_cases:
            start_time = time.time()
            
            result = await personal_agent.generate_weekly_dinner_plan(
                days=case["days"],
                user_request=case["request"],
                include_sale_info=False
            )
            
            elapsed = time.time() - start_time
            
            # 性能基準（日数に応じて調整）
            max_time = 2.0 + (case["days"] * 0.5)  # 基本2秒 + 日数×0.5秒
            assert elapsed < max_time, f"Dinner plan generation too slow: {elapsed:.2f}s for {case['days']} days"
            
            # 結果確認
            assert result is not None
            if not result.get("fallback"):
                assert result.get("success") is True
                assert len(result.get("dinners", [])) == case["days"]
    
    def test_memory_efficiency(self, smart_context_builder):
        """メモリ効率テスト"""
        import tracemalloc
        
        # メモリ追跡開始
        tracemalloc.start()
        
        # 繰り返し処理でメモリリークがないかチェック
        for i in range(50):
            result = smart_context_builder.build_smart_context(
                user_request=f"レシピ提案 {i}",
                max_tokens=2000
            )
            assert result is not None
        
        # メモリ使用量確認
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        # メモリ使用量が妥当な範囲内か確認（50MB以下）
        peak_mb = peak / 1024 / 1024
        assert peak_mb < 50, f"Memory usage too high: {peak_mb:.2f}MB"
    
    def test_concurrent_requests(self, smart_context_builder):
        """並行リクエスト処理テスト"""
        import threading
        import queue
        
        num_threads = 5
        requests_per_thread = 3
        results_queue = queue.Queue()
        
        def worker():
            for i in range(requests_per_thread):
                start_time = time.time()
                
                try:
                    result = smart_context_builder.build_smart_context(
                        user_request=f"並行テスト {threading.current_thread().name} - {i}",
                        max_tokens=1500
                    )
                    
                    elapsed = time.time() - start_time
                    results_queue.put({
                        'success': True,
                        'elapsed': elapsed,
                        'result': result
                    })
                    
                except Exception as e:
                    results_queue.put({
                        'success': False,
                        'error': str(e),
                        'elapsed': time.time() - start_time
                    })
        
        # スレッド作成・実行
        threads = []
        start_time = time.time()
        
        for i in range(num_threads):
            thread = threading.Thread(target=worker, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()
        
        # 全スレッド完了待ち
        for thread in threads:
            thread.join()
        
        total_time = time.time() - start_time
        
        # 結果収集・検証
        results = []
        while not results_queue.empty():
            results.append(results_queue.get())
        
        # 全リクエスト成功確認
        success_count = sum(1 for r in results if r['success'])
        total_requests = num_threads * requests_per_thread
        
        assert success_count == total_requests, f"Only {success_count}/{total_requests} requests succeeded"
        
        # 並行処理効率確認（全体時間が sequential time の 70% 以下）
        avg_sequential_time = sum(r['elapsed'] for r in results) / len(results)
        expected_sequential_time = avg_sequential_time * total_requests
        efficiency = total_time / expected_sequential_time
        
        assert efficiency < 0.7, f"Concurrent processing not efficient enough: {efficiency:.2%}"
    
    @pytest.mark.asyncio
    async def test_api_response_time_distribution(self, personal_agent):
        """API応答時間分布テスト"""
        response_times = []
        
        # 複数回のAPI呼び出しで応答時間を測定
        for i in range(10):
            start_time = time.time()
            
            # フォールバック応答を使用（実際のAPI呼び出しなし）
            original_api_key = personal_agent.api_key
            personal_agent.api_key = None
            
            try:
                result = await personal_agent.generate_weekly_dinner_plan(
                    days=1,
                    user_request=f"パフォーマンステスト {i}"
                )
                
                elapsed = time.time() - start_time
                response_times.append(elapsed)
                
                assert result is not None
                
            finally:
                personal_agent.api_key = original_api_key
        
        # 統計分析
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # 性能基準
        assert avg_time < 1.0, f"Average response time too slow: {avg_time:.2f}s"
        assert max_time < 2.0, f"Max response time too slow: {max_time:.2f}s"
        assert min_time < 0.5, f"Min response time should be faster: {min_time:.2f}s"
        
        # 応答時間の一貫性確認（標準偏差が平均の50%以下）
        import statistics
        std_dev = statistics.stdev(response_times)
        consistency_ratio = std_dev / avg_time
        
        assert consistency_ratio < 0.5, f"Response time inconsistent: std_dev={std_dev:.2f}, avg={avg_time:.2f}"
    
    def test_large_dataset_handling(self, smart_context_builder):
        """大量データ処理テスト"""
        # 長いユーザーリクエストでのテスト
        long_request = """
        今日の夕食について詳しく相談したいです。
        家族は4人で、子供が2人います。
        アレルギーは特にありませんが、辛い食べ物は苦手です。
        野菜をたくさん使った健康的な料理を作りたいと思っています。
        調理時間は30分程度で収めたいです。
        今冷蔵庫にある材料は、キャベツ、人参、豚肉、米です。
        栄養バランスも考慮してもらえると嬉しいです。
        コストは1食あたり500円以内に抑えたいです。
        """ * 5  # 5回繰り返し
        
        start_time = time.time()
        
        result = smart_context_builder.build_smart_context(
            user_request=long_request,
            max_tokens=4000
        )
        
        elapsed = time.time() - start_time
        
        # 大量データでも適切な時間で処理される
        assert elapsed < 2.0, f"Large dataset processing too slow: {elapsed:.2f}s"
        
        # 結果の品質確認
        assert result["total_estimated_tokens"] <= 4000
        assert result["optimization_summary"]["optimization_successful"]
    
    def test_monitoring_overhead(self):
        """監視機能のオーバーヘッドテスト"""
        # 監視なしの処理時間測定
        smart_context_builder = SmartContextBuilder()
        
        start_time = time.time()
        for _ in range(20):
            result = smart_context_builder.build_smart_context(
                user_request="監視オーバーヘッドテスト",
                max_tokens=2000
            )
        no_monitoring_time = time.time() - start_time
        
        # パフォーマンスレポート生成のオーバーヘッド測定
        start_time = time.time()
        for _ in range(10):
            report = get_performance_report()
            assert report is not None
        monitoring_time = time.time() - start_time
        
        # 監視オーバーヘッドが妥当な範囲内か確認（10%以下）
        overhead_ratio = monitoring_time / (no_monitoring_time / 2)  # 半分の回数なので調整
        assert overhead_ratio < 0.1, f"Monitoring overhead too high: {overhead_ratio:.1%}"
    
    def test_resource_usage_limits(self):
        """リソース使用量制限テスト"""
        from flavia.monitoring import ResourceMonitor
        
        # 初期リソース使用量
        initial_resources = ResourceMonitor.get_resource_summary()
        
        # 複数の処理を実行
        smart_context_builder = SmartContextBuilder()
        for i in range(100):
            result = smart_context_builder.build_smart_context(
                user_request=f"リソーステスト {i}",
                max_tokens=1000
            )
        
        # 処理後のリソース使用量
        final_resources = ResourceMonitor.get_resource_summary()
        
        # メモリ使用量の増加が適切な範囲内か確認
        if 'memory' in initial_resources and 'memory' in final_resources:
            initial_memory = initial_resources['memory'].get('rss_mb', 0)
            final_memory = final_resources['memory'].get('rss_mb', 0)
            memory_increase = final_memory - initial_memory
            
            # メモリ増加が100MB以下
            assert memory_increase < 100, f"Memory increase too high: {memory_increase:.2f}MB"


class TestScalability:
    """スケーラビリティテスト"""
    
    def test_increasing_load(self):
        """負荷増加テスト"""
        smart_context_builder = SmartContextBuilder()
        
        # 段階的に負荷を増加
        load_levels = [5, 10, 20, 30]
        performance_degradation = []
        
        for load in load_levels:
            start_time = time.time()
            
            for i in range(load):
                result = smart_context_builder.build_smart_context(
                    user_request=f"負荷テスト {i}",
                    max_tokens=1500
                )
                assert result is not None
            
            elapsed = time.time() - start_time
            avg_time_per_request = elapsed / load
            performance_degradation.append(avg_time_per_request)
        
        # 負荷増加に対する性能劣化が線形範囲内かチェック
        baseline = performance_degradation[0]
        for i, perf in enumerate(performance_degradation[1:], 1):
            # 性能劣化が負荷増加の2倍を超えないこと
            degradation_factor = perf / baseline
            load_factor = load_levels[i] / load_levels[0]
            
            assert degradation_factor < load_factor * 2, \
                f"Performance degradation too high at load {load_levels[i]}: {degradation_factor:.2f}x"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])