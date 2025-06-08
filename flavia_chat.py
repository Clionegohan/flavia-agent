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

# Streamlit設定
st.set_page_config(
    page_title="🍽️ Flavia AI 料理パートナー",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        display: flex;
        align-items: flex-start;
    }
    
    .chat-message.user {
        background-color: #007bff;
        color: white;
        margin-left: 2rem;
        flex-direction: row-reverse;
    }
    
    .chat-message.assistant {
        background-color: #f1f3f4;
        color: #333;
        margin-right: 2rem;
    }
    
    .chat-avatar {
        width: 40px;
        height: 40px;
        border-radius: 50%;
        margin: 0 0.5rem;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.2rem;
    }
    
    .recipe-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background-color: #fff;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .recipe-title {
        font-size: 1.2rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 0.5rem;
    }
    
    .recipe-meta {
        display: flex;
        gap: 1rem;
        margin: 0.5rem 0;
        font-size: 0.9rem;
        color: #666;
    }
    
    .rating-stars {
        font-size: 1.5rem;
        color: #ffc107;
        margin: 0.5rem 0;
    }
    
    .learning-badge {
        background: linear-gradient(45deg, #ff6b6b, #4ecdc4);
        color: white;
        padding: 0.2rem 0.5rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    
    .sidebar-metric {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
    }
    
    .sidebar-metric h3 {
        margin: 0;
        font-size: 2rem;
        color: #007bff;
    }
    
    .sidebar-metric p {
        margin: 0;
        color: #666;
        font-size: 0.9rem;
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
        with st.spinner("🧠 Flaviaを起動中..."):
            try:
                from src.flavia_agent.agent.personal_flavia import PersonalFlaviaAgent
                st.session_state.flavia_agent = PersonalFlaviaAgent()
                st.session_state.agent_initialized = True
            except Exception as e:
                st.session_state.agent_initialized = False
                st.session_state.initialization_error = str(e)
    
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

def render_recipe_cards(recipes: List[Any]):
    """レシピカードをレンダリング"""
    for i, recipe in enumerate(recipes):
        with st.container():
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.markdown(f"""
                <div class="recipe-card">
                    <div class="recipe-title">🍳 {recipe.name}</div>
                    <div class="recipe-meta">
                        <span>💰 ${recipe.estimated_cost:.2f}</span>
                        <span>⏱️ {recipe.total_time}分</span>
                        <span>🌍 {recipe.cuisine_type}</span>
                        <span>👤 {recipe.servings}人分</span>
                    </div>
                    <div><strong>材料:</strong> {', '.join(recipe.ingredients[:3])}{'...' if len(recipe.ingredients) > 3 else ''}</div>
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

async def generate_recipe_response(user_message: str) -> Dict[str, Any]:
    """レシピ応答を生成"""
    try:
        agent = st.session_state.flavia_agent
        
        # ユーザーインタラクションを記録
        agent.record_interaction(
            interaction_type="chat_message",
            details={
                "action": "sent_message",
                "message": user_message,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # レシピ生成
        result = await agent.generate_personalized_meal_plan(
            user_request=user_message,
            include_sale_info=True,
            sale_url="cache"
        )
        
        recipes = result.get("recipes", [])
        st.session_state.current_recipes = recipes
        
        # レスポンス生成
        if recipes:
            recipe_count = len(recipes)
            response = f"素晴らしいリクエストですね！🎯\n\nあなたの嗜好を考慮して、**{recipe_count}つのレシピ**を提案します。\n\n"
            
            if result.get("sale_integration"):
                response += "💰 **特売情報も活用**してコストパフォーマンスを重視しました！\n\n"
            
            response += "各レシピの右側で⭐評価をお願いします。あなたの評価で私はもっと賢くなります！"
            
            return {
                "content": response,
                "recipes": recipes,
                "generation_info": result
            }
        else:
            return {
                "content": "申し訳ありませんが、条件に合うレシピを見つけられませんでした。別の条件で試してみませんか？"
            }
            
    except Exception as e:
        return {
            "content": f"申し訳ありません。エラーが発生しました: {e}\n\n別の方法で試してみてください。"
        }

def render_sidebar():
    """サイドバーをレンダリング"""
    with st.sidebar:
        st.title("🧠 学習ダッシュボード")
        
        if st.session_state.get("agent_initialized"):
            try:
                agent = st.session_state.flavia_agent
                dashboard = agent.get_learning_dashboard()
                
                # 学習状況
                st.subheader("📊 学習状況")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("総フィードバック", dashboard["学習状況"]["総フィードバック数"])
                with col2:
                    st.metric("学習項目", dashboard["学習状況"]["適応的嗜好項目数"])
                
                # 今週の傾向
                st.subheader("📈 今週の傾向")
                week_trends = dashboard["今週の傾向"]
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(
                        "平均評価", 
                        f"{week_trends['平均レシピ評価']:.1f}/5.0",
                        delta=None
                    )
                with col2:
                    st.metric(
                        "嗜好安定性",
                        f"{week_trends['嗜好安定性']:.0%}",
                        delta=None
                    )
                
                # 推奨アクション
                if dashboard["推奨アクション"]:
                    st.subheader("💡 推奨アクション")
                    for action in dashboard["推奨アクション"][:3]:
                        st.info(action)
                
                # クイックアクション
                st.subheader("⚡ クイックアクション")
                
                if st.button("🎯 今日のおすすめ", use_container_width=True):
                    handle_quick_action("今日のおすすめレシピを教えて")
                
                if st.button("🛒 特売活用レシピ", use_container_width=True):
                    handle_quick_action("今日の特売商品を使ったお得なレシピを教えて")
                
                if st.button("⚡ 時短料理", use_container_width=True):
                    handle_quick_action("15分以内で作れる簡単レシピを教えて")
                
                if st.button("🌱 ヘルシー料理", use_container_width=True):
                    handle_quick_action("健康的で栄養バランスの良い料理を教えて")
                
                # 詳細分析
                with st.expander("📊 詳細分析"):
                    if st.button("嗜好分析実行"):
                        analysis = agent.analyze_my_preferences(days=30)
                        st.json(analysis)
                
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

def main():
    """メインアプリケーション"""
    # セッション初期化
    initialize_session()
    
    # タイトル
    st.title("🍽️ Flavia AI 料理パートナー")
    st.markdown("**あなた専用の学習型AI料理アシスタント**")
    
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
                with st.spinner("🍳 レシピを考えています..."):
                    # 非同期処理の実行
                    response = asyncio.run(generate_recipe_response(prompt))
                    
                    # 応答を表示
                    st.write(response["content"])
                    
                    # レシピカードを表示
                    if "recipes" in response:
                        render_recipe_cards(response["recipes"])
                    
                    # メッセージ履歴に追加
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": response["content"],
                        "recipes": response.get("recipes", []),
                        "timestamp": datetime.now().isoformat()
                    })
    else:
        st.error("🚫 Flaviaエージェントが利用できません。アプリケーションを再起動してください。")
        if st.button("🔄 再初期化"):
            st.rerun()

if __name__ == "__main__":
    main()