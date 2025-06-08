"""
🍽️ Flavia AI 料理パートナー - チャットUI

あなた専用のAI料理アシスタント
学習機能付きパーソナライズドレシピ提案システム
"""

import streamlit as st
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

# パフォーマンス監視のインポート
try:
    from flavia.monitoring import get_performance_report, performance_alert_check
    from flavia.utils.error_handler import get_error_context
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False

# Streamlit設定
st.set_page_config(
    page_title="🍽️ Flavia AI 料理パートナー",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 最適化された洗練UI CSS
st.markdown("""
<style>
    /* メイン レイアウト */
    .main { padding-top: 0.5rem; }
    
    /* ヘッダーアニメーション */
    .header-animation {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        animation: shimmer 3s ease-in-out infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.8; }
    }
    
    /* チャットメッセージ */
    .chat-message {
        padding: 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s ease;
    }
    
    .chat-message:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* レシピカード */
    .recipe-card {
        background: linear-gradient(145deg, #ffffff 0%, #f8f9fa 100%);
        border: none;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
        position: relative;
        overflow: hidden;
    }
    
    .recipe-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
        background: linear-gradient(90deg, #FF6B6B, #4ECDC4, #45B7D1, #96CEB4);
        border-radius: 16px 16px 0 0;
    }
    
    .recipe-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 30px rgba(0,0,0,0.15);
    }
    
    .recipe-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: #2c3e50;
        margin-bottom: 0.5rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .recipe-meta {
        display: flex;
        flex-wrap: wrap;
        gap: 0.8rem;
        margin: 0.8rem 0;
        font-size: 0.9rem;
        color: #555;
    }
    
    .meta-item {
        background: rgba(116, 75, 162, 0.1);
        padding: 0.3rem 0.6rem;
        border-radius: 20px;
        font-weight: 500;
    }
    
    /* 学習バッジ */
    .learning-badge {
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        box-shadow: 0 2px 10px rgba(255, 107, 107, 0.3);
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    /* サイドバーメトリクス */
    .sidebar-metric {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 1.2rem;
        border-radius: 12px;
        margin: 0.8rem 0;
        text-align: center;
        border: 1px solid rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    
    .sidebar-metric:hover {
        background: linear-gradient(135deg, #e9ecef 0%, #dee2e6 100%);
        transform: scale(1.02);
    }
    
    .sidebar-metric h3 {
        margin: 0;
        font-size: 2.2rem;
        background: linear-gradient(45deg, #007bff, #0056b3);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 700;
    }
    
    .sidebar-metric p {
        margin: 0.5rem 0 0 0;
        color: #6c757d;
        font-size: 0.9rem;
        font-weight: 500;
    }
    
    /* ボタンスタイル */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 0.6rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
    }
    
    /* 評価星 */
    .rating-button {
        background: linear-gradient(45deg, #ffc107, #ff8c00);
        border: none;
        border-radius: 50%;
        width: 40px;
        height: 40px;
        margin: 0.2rem;
        transition: all 0.2s ease;
        box-shadow: 0 2px 8px rgba(255, 193, 7, 0.3);
    }
    
    .rating-button:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 15px rgba(255, 193, 7, 0.5);
    }
    
    /* アラート改善 */
    .stAlert {
        border-radius: 12px;
        border: none;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    
    /* スピナー改善 */
    .stSpinner {
        text-align: center;
    }
    
    /* 入力フィールド */
    .stTextInput > div > div > input {
        border-radius: 25px;
        border: 2px solid #e9ecef;
        padding: 0.8rem 1.2rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# セッション状態の初期化
def initialize_session():
    """セッション状態を初期化"""
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "こんにちは！🍽️ Flavia AI料理パートナーです。\n\nあなた専用の料理アシスタントとして、学習機能を使ってどんどん賢くなっていきます！\n\n今日はどんな料理について相談しましょうか？",
                "timestamp": datetime.now().isoformat()
            }
        ]
    
    if "flavia_agent" not in st.session_state:
        st.session_state.flavia_agent = None
        st.session_state.agent_initialized = False
        st.session_state.initialization_error = None
    
    if "recipe_ratings" not in st.session_state:
        st.session_state.recipe_ratings = {}
    
    if "current_recipes" not in st.session_state:
        st.session_state.current_recipes = []

def render_chat_message(message: Dict[str, Any]):
    """チャットメッセージをレンダリング"""
    role = message["role"]
    content = message["content"]
    
    if role == "user":
        with st.chat_message("user", avatar="👤"):
            st.write(content)
    else:
        with st.chat_message("assistant", avatar="🍽️"):
            st.write(content)
            
            # レシピが含まれている場合の特別表示
            if "recipes" in message:
                render_recipe_cards(message["recipes"])
            
            # 週間夕食プランが含まれている場合の特別表示
            elif "dinners" in message and "shopping_list" in message:
                render_weekly_dinner_plan(message["dinners"], message["shopping_list"])

def render_weekly_dinner_plan(dinners: List[Dict], shopping_list: Dict[str, Any]):
    """週間夕食プランをレンダリング"""
    
    # タブで整理
    tab1, tab2 = st.tabs(["📅 夕食メニュー", "🛒 買い物リスト"])
    
    with tab1:
        st.subheader("🍽️ 夕食メニュー詳細")
        
        for i, dinner in enumerate(dinners):
            with st.expander(f"**Day {dinner['day']} ({dinner['date']})** - {dinner['main_dish']}", expanded=(i==0)):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"""
                    <div class="recipe-card">
                        <div class="recipe-title">🍳 {dinner['main_dish']}</div>
                        <p><strong>説明:</strong> {dinner.get('description', '')}</p>
                        
                        <div class="recipe-meta">
                            <span class="meta-item">💰 ${dinner.get('estimated_cost', 0):.2f}</span>
                            <span class="meta-item">⏱️ 準備{dinner.get('detailed_recipe', {}).get('prep_time', 15)}分</span>
                            <span class="meta-item">🔥 調理{dinner.get('detailed_recipe', {}).get('cook_time', 30)}分</span>
                            <span class="meta-item">👤 {dinner.get('detailed_recipe', {}).get('servings', 2)}人分</span>
                            <span class="meta-item">📊 {dinner.get('cooking_difficulty', '普通')}</span>
                        </div>
                        
                        <div style="margin-top: 1rem;">
                            <strong>🥬 材料:</strong><br>
                            {'<br>'.join(f"• {ing}" for ing in dinner.get('ingredients', []))}
                        </div>
                        
                        <div style="margin-top: 1rem;">
                            <strong>📋 作り方:</strong><br>
                            {'<br>'.join(f"{idx+1}. {step}" for idx, step in enumerate(dinner.get('detailed_recipe', {}).get('instructions', [])))}
                        </div>
                        
                        <div style="margin-top: 1rem;">
                            <strong>🍎 栄養情報:</strong> {dinner.get('nutrition_info', '情報なし')}
                        </div>
                        
                        <div class="learning-badge" style="margin-top: 1rem;">AI学習型レシピ</div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown("**このレシピを評価:**")
                    rating_key = f"dinner_rating_{dinner['day']}_{i}"
                    
                    # 星評価ボタン
                    cols = st.columns(5)
                    for star in range(1, 6):
                        if cols[star-1].button(f"{'⭐' * star}", key=f"{rating_key}_{star}"):
                            # 夕食レシピの評価を記録
                            rate_dinner_recipe(dinner, star)
                            st.rerun()
    
    with tab2:
        st.subheader("🛒 統合買い物リスト")
        
        # サマリー情報
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("総食材数", shopping_list.get('total_unique_ingredients', 0))
        with col2:
            st.metric("予算総額", f"${shopping_list.get('total_estimated_cost', 0):.2f}")
        with col3:
            st.metric("買い物時間", shopping_list.get('estimated_shopping_time', '30-45分'))
        
        # カテゴリ別買い物リスト
        st.markdown("### 📝 カテゴリ別買い物リスト")
        
        categories = shopping_list.get('ingredients_by_category', {})
        for category, items in categories.items():
            if items:  # アイテムがある場合のみ表示
                with st.expander(f"**{category}** ({len(items)}品目)"):
                    for item in items:
                        st.markdown(f"• {item}")
        
        # 買い物のコツ
        st.markdown("### 💡 買い物のコツ")
        notes = shopping_list.get('shopping_notes', [])
        for note in notes:
            st.info(note)

def render_recipe_cards(recipes: List[Any]):
    """レシピカードをレンダリング（従来版）"""
    for i, recipe in enumerate(recipes):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="recipe-card">
                    <div class="recipe-title">🍳 {recipe.name}</div>
                    <div class="recipe-meta">
                        <span class="meta-item">💰 ${recipe.estimated_cost:.2f}</span>
                        <span class="meta-item">⏱️ {recipe.total_time}分</span>
                        <span class="meta-item">🌍 {recipe.cuisine_type}</span>
                        <span class="meta-item">👤 {recipe.servings}人分</span>
                    </div>
                    <div style="margin-top: 1rem;"><strong>材料:</strong> {', '.join(recipe.ingredients[:3])}{'...' if len(recipe.ingredients) > 3 else ''}</div>
                    <div class="learning-badge" style="margin-top: 1rem;">AI学習型レシピ</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("**このレシピを評価:**")
                rating_key = f"rating_{recipe.name}_{i}"
                
                # 星評価ボタン
                cols = st.columns(5)
                for star in range(1, 6):
                    if cols[star-1].button(f"{'⭐' * star}", key=f"{rating_key}_{star}"):
                        rate_recipe(recipe, star)
                        st.rerun()

def rate_recipe(recipe: Any, rating: int):
    """レシピを評価"""
    try:
        agent = st.session_state.flavia_agent
        
        # レシピコンテキストの準備
        recipe_context = {
            "ingredients": recipe.ingredients,
            "cuisine_type": recipe.cuisine_type,
            "cost": recipe.estimated_cost,
            "time": recipe.total_time
        }
        
        # フィードバック記録
        feedback_id = agent.rate_recipe(
            recipe_name=recipe.name,
            rating=rating,
            comments=f"チャットUIから{rating}つ星評価",
            recipe_context=recipe_context
        )
        
        # セッション状態に記録
        st.session_state.recipe_ratings[recipe.name] = rating
        
        # 成功メッセージ
        st.success(f"⭐ {recipe.name} を {rating}つ星で評価しました！学習に反映されます。")
        
        # インタラクション記録
        agent.record_interaction(
            interaction_type="recipe_rating",
            details={
                "action": f"rated_recipe_{rating}_stars",
                "recipe_name": recipe.name,
                "rating": rating,
                "feedback_id": feedback_id
            }
        )
        
    except Exception as e:
        st.error(f"評価の記録に失敗しました: {e}")

def rate_dinner_recipe(dinner: Dict, rating: int):
    """夕食レシピを評価"""
    try:
        agent = st.session_state.flavia_agent
        
        # 夕食レシピコンテキストの準備
        recipe_context = {
            "ingredients": dinner.get('ingredients', []),
            "main_dish": dinner.get('main_dish', ''),
            "cost": dinner.get('estimated_cost', 0),
            "cooking_difficulty": dinner.get('cooking_difficulty', '普通'),
            "day": dinner.get('day', 1),
            "date": dinner.get('date', '')
        }
        
        # フィードバック記録
        feedback_id = agent.rate_recipe(
            recipe_name=dinner.get('main_dish', '料理'),
            rating=rating,
            comments=f"夕食プランDay{dinner.get('day', 1)}から{rating}つ星評価",
            recipe_context=recipe_context
        )
        
        # セッション状態に記録
        if "dinner_ratings" not in st.session_state:
            st.session_state.dinner_ratings = {}
        st.session_state.dinner_ratings[f"day_{dinner.get('day', 1)}"] = rating
        
        # 成功メッセージ
        st.success(f"⭐ {dinner.get('main_dish', '料理')} を {rating}つ星で評価しました！学習に反映されます。")
        
        # インタラクション記録
        agent.record_interaction(
            interaction_type="dinner_recipe_rating",
            details={
                "action": f"rated_dinner_{rating}_stars",
                "recipe_name": dinner.get('main_dish', ''),
                "rating": rating,
                "day": dinner.get('day', 1),
                "feedback_id": feedback_id
            }
        )
        
    except Exception as e:
        st.error(f"評価の記録に失敗しました: {e}")

async def generate_weekly_dinner_response(days: int = 7, user_message: str = "") -> Dict[str, Any]:
    """週間夕食プラン応答を生成"""
    try:
        agent = st.session_state.flavia_agent
        
        # ユーザーインタラクションを記録
        agent.record_interaction(
            interaction_type="weekly_dinner_request",
            details={
                "action": "requested_weekly_plan",
                "days": days,
                "message": user_message,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # 週間夕食プラン生成
        result = await agent.generate_weekly_dinner_plan(
            days=days,
            user_request=user_message,
            include_sale_info=True,
            sale_url="cache"
        )
        
        dinners = result.get("dinners", [])
        shopping_list = result.get("shopping_list", {})
        
        # レスポンス生成
        if dinners:
            response = f"🍽️ **{days}日分の夕食プラン**を作成しました！\n\n"
            response += f"💰 **総予算**: ${result.get('total_estimated_cost', 0):.2f}\n"
            response += f"🛒 **買い物リスト**: {shopping_list.get('total_unique_ingredients', 0)}種類の食材\n\n"
            
            if result.get("sale_integration"):
                response += "💡 **特売情報も活用**してコストを最適化しました！\n\n"
            
            response += "下記の詳細プランをご確認ください。気に入ったレシピは⭐評価をお願いします！"
            
            return {
                "content": response,
                "dinners": dinners,
                "shopping_list": shopping_list,
                "generation_info": result,
                "plan_type": "weekly_dinner"
            }
        else:
            return {
                "content": "申し訳ありませんが、献立プランの生成に失敗しました。別の条件で試してみませんか？"
            }
            
    except Exception as e:
        return {
            "content": f"申し訳ありません。エラーが発生しました: {e}\n\n別の方法で試してみてください。"
        }

def initialize_agent():
    """エージェントを初期化"""
    if st.session_state.flavia_agent is None:
        try:
            from flavia.core.agents.personal import PersonalAgent
            st.session_state.flavia_agent = PersonalAgent()
            st.session_state.agent_initialized = True
            return True
        except Exception as e:
            st.session_state.agent_initialized = False
            st.session_state.initialization_error = str(e)
            return False
    return st.session_state.agent_initialized

def render_sidebar():
    """サイドバーをレンダリング"""
    with st.sidebar:
        st.title("🧠 学習ダッシュボード")
        
        # エージェント初期化ボタン
        if not st.session_state.get("agent_initialized", False):
            if st.button("🚀 Flavia起動", use_container_width=True):
                with st.spinner("🧠 Flaviaを起動中..."):
                    initialize_agent()
                st.rerun()
            
            if st.session_state.get("initialization_error"):
                st.error(f"初期化エラー: {st.session_state.initialization_error}")
            return
        
        if st.session_state.get("agent_initialized"):
            try:
                agent = st.session_state.flavia_agent
                dashboard = agent.get_learning_dashboard()
                
                # 学習状況
                st.subheader("📊 学習状況")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="sidebar-metric">
                        <h3>{dashboard["学習状況"]["総フィードバック数"]}</h3>
                        <p>総フィードバック</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="sidebar-metric">
                        <h3>{dashboard["学習状況"]["適応的嗜好項目数"]}</h3>
                        <p>学習項目</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 今週の傾向
                st.subheader("📈 今週の傾向")
                week_trends = dashboard["今週の傾向"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="sidebar-metric">
                        <h3>{week_trends['平均レシピ評価']:.1f}/5.0</h3>
                        <p>平均評価</p>
                    </div>
                    """, unsafe_allow_html=True)
                with col2:
                    st.markdown(f"""
                    <div class="sidebar-metric">
                        <h3>{week_trends['嗜好安定性']:.0%}</h3>
                        <p>嗜好安定性</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                # 推奨アクション
                if dashboard["推奨アクション"]:
                    st.subheader("💡 推奨アクション")
                    for action in dashboard["推奨アクション"][:3]:
                        st.info(action)
                
                # クイックアクション
                st.subheader("⚡ クイックアクション")
                
                # 週間夕食プラン生成
                st.markdown("**📅 週間夕食プラン**")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("📋 7日間プラン", use_container_width=True):
                        handle_weekly_dinner_action(7)
                with col2:
                    if st.button("📋 3日間プラン", use_container_width=True):
                        handle_weekly_dinner_action(3)
                
                st.markdown("**🍳 単発レシピ**")
                if st.button("🎯 今日のおすすめ", use_container_width=True):
                    handle_quick_action("今日のおすすめレシピを教えて")
                
                if st.button("🛒 特売活用レシピ", use_container_width=True):
                    handle_quick_action("今日の特売商品を使ったお得なレシピを教えて")
                
                if st.button("⚡ 時短料理", use_container_width=True):
                    handle_quick_action("15分以内で作れる簡単レシピを教えて")
                
                if st.button("🌱 ヘルシー料理", use_container_width=True):
                    handle_quick_action("健康的で栄養バランスの良い料理を教えて")
                
                # 詳細分析とシステム監視
                with st.expander("📊 詳細分析"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        if st.button("嗜好分析実行"):
                            analysis = agent.analyze_my_preferences(days=30)
                            st.json(analysis)
                    
                    with col2:
                        if MONITORING_AVAILABLE and st.button("システム監視"):
                            # パフォーマンスレポート表示
                            report = get_performance_report()
                            st.subheader("🔧 パフォーマンス")
                            st.json(report)
                            
                            # アラートチェック
                            alerts = performance_alert_check()
                            if alerts:
                                st.subheader("⚠️ アラート")
                                for alert in alerts:
                                    st.warning(alert['message'])
                            else:
                                st.success("✅ システム正常")
                
                # エラー情報表示
                if MONITORING_AVAILABLE:
                    with st.expander("🚨 エラー監視"):
                        error_context = get_error_context()
                        if error_context['error_summary']['total_errors'] > 0:
                            st.error(f"総エラー数: {error_context['error_summary']['total_errors']}")
                            st.json(error_context['error_summary'])
                        else:
                            st.success("✅ エラーなし")
                
            except Exception as e:
                st.error(f"ダッシュボード読み込みエラー: {e}")
        else:
            st.error("🚫 Flaviaエージェントの初期化に失敗しました")
            if st.session_state.get("initialization_error"):
                st.error(st.session_state.initialization_error)

def handle_quick_action(message: str):
    """クイックアクションを処理"""
    # メッセージを追加
    st.session_state.messages.append({
        "role": "user",
        "content": message,
        "timestamp": datetime.now().isoformat()
    })
    
    # 再実行して応答を生成
    st.rerun()

def handle_weekly_dinner_action(days: int):
    """週間夕食プランアクションを処理"""
    # 特別なメッセージタイプとして追加
    st.session_state.messages.append({
        "role": "user",
        "content": f"{days}日間の夕食プランを作成してください",
        "timestamp": datetime.now().isoformat(),
        "action_type": "weekly_dinner_plan",
        "days": days
    })
    
    # 再実行して応答を生成
    st.rerun()

def main():
    """メインアプリケーション"""
    # セッション初期化
    initialize_session()
    
    # 洗練されたタイトル
    st.markdown("""
    <h1 class="header-animation" style="font-size: 3rem; margin-bottom: 0;">
        🍽️ Flavia AI 料理パートナー
    </h1>
    <p style="font-size: 1.2rem; color: #6c757d; margin-top: 0; font-weight: 500;">
        あなた専用の学習型AI料理アシスタント ✨
    </p>
    """, unsafe_allow_html=True)
    
    # サイドバー
    render_sidebar()
    
    # メインチャット領域
    chat_container = st.container()
    
    with chat_container:
        # チャット履歴表示
        for message in st.session_state.messages:
            render_chat_message(message)
    
    # チャット入力
    if st.session_state.get("agent_initialized", False):
        if prompt := st.chat_input("料理について何でも聞いてください..."):
            # ユーザーメッセージを追加
            st.session_state.messages.append({
                "role": "user",
                "content": prompt,
                "timestamp": datetime.now().isoformat()
            })
            
            # ユーザーメッセージを表示
            with st.chat_message("user", avatar="👤"):
                st.write(prompt)
            
            # アシスタント応答を生成・表示
            with st.chat_message("assistant", avatar="🍽️"):
                # 週間プランリクエストかチェック
                last_message = st.session_state.messages[-1]
                is_weekly_plan = last_message.get("action_type") == "weekly_dinner_plan"
                
                if is_weekly_plan:
                    days = last_message.get("days", 7)
                    with st.spinner(f"🍽️ {days}日間の夕食プランを作成中..."):
                        # 週間プラン生成
                        response = asyncio.run(generate_weekly_dinner_response(days, prompt))
                        
                        # 応答を表示
                        st.write(response["content"])
                        
                        # 週間プランを表示
                        if "dinners" in response and "shopping_list" in response:
                            render_weekly_dinner_plan(response["dinners"], response["shopping_list"])
                        
                        # メッセージ履歴に追加
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response["content"],
                            "dinners": response.get("dinners", []),
                            "shopping_list": response.get("shopping_list", {}),
                            "plan_type": "weekly_dinner",
                            "timestamp": datetime.now().isoformat()
                        })
                else:
                    with st.spinner("🍳 夕食プランを考えています..."):
                        # デフォルトで7日間プラン生成
                        response = asyncio.run(generate_weekly_dinner_response(7, prompt))
                        
                        # 応答を表示
                        st.write(response["content"])
                        
                        # 週間プランを表示
                        if "dinners" in response and "shopping_list" in response:
                            render_weekly_dinner_plan(response["dinners"], response["shopping_list"])
                        
                        # メッセージ履歴に追加
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": response["content"],
                            "dinners": response.get("dinners", []),
                            "shopping_list": response.get("shopping_list", {}),
                            "plan_type": "weekly_dinner",
                            "timestamp": datetime.now().isoformat()
                        })
    else:
        st.info("👈 サイドバーの「🚀 Flavia起動」ボタンを押してエージェントを開始してください。")

if __name__ == "__main__":
    main()