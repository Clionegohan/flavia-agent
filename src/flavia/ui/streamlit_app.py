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

# モダンUI デザインシステム
st.markdown("""
<style>
    /* ===================
       GLOBAL STYLES
    =================== */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
    
    .main {
        padding-top: 1rem;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
    }
    
    /* カスタムプロパティ（CSS変数） */
    :root {
        --primary-color: #2563eb;
        --primary-hover: #1d4ed8;
        --secondary-color: #64748b;
        --success-color: #10b981;
        --warning-color: #f59e0b;
        --error-color: #ef4444;
        --background-primary: #ffffff;
        --background-secondary: #f8fafc;
        --background-tertiary: #f1f5f9;
        --text-primary: #1e293b;
        --text-secondary: #64748b;
        --text-muted: #94a3b8;
        --border-color: #e2e8f0;
        --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
        --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
        --shadow-xl: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
        --radius-sm: 6px;
        --radius-md: 8px;
        --radius-lg: 12px;
        --radius-xl: 16px;
    }
    
    /* ===================
       HEADER & NAVIGATION
    =================== */
    .main-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 50%, #6366f1 100%);
        padding: 2rem 0;
        margin-bottom: 2rem;
        border-radius: 0 0 var(--radius-xl) var(--radius-xl);
        box-shadow: var(--shadow-lg);
    }
    
    .header-content {
        text-align: center;
        color: white;
    }
    
    .app-title {
        font-size: 2.5rem;
        font-weight: 800;
        margin: 0;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
        letter-spacing: -0.025em;
    }
    
    .app-subtitle {
        font-size: 1.125rem;
        font-weight: 400;
        margin-top: 0.5rem;
        opacity: 0.9;
        letter-spacing: 0.025em;
    }
    
    /* ===================
       RECIPE CARDS
    =================== */
    .recipe-card {
        background: var(--background-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-xl);
        padding: 0;
        margin: 1.5rem 0;
        box-shadow: var(--shadow-md);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        overflow: hidden;
        position: relative;
    }
    
    .recipe-card:hover {
        transform: translateY(-4px);
        box-shadow: var(--shadow-xl);
        border-color: var(--primary-color);
    }
    
    .recipe-header {
        background: linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 100%);
        padding: 1.5rem;
        color: white;
        position: relative;
        overflow: hidden;
    }
    
    .recipe-header::before {
        content: '';
        position: absolute;
        top: 0;
        right: 0;
        width: 100px;
        height: 100px;
        background: rgba(255,255,255,0.1);
        border-radius: 50%;
        transform: translate(30px, -30px);
    }
    
    .recipe-day-badge {
        display: inline-block;
        background: rgba(255,255,255,0.2);
        padding: 0.375rem 0.75rem;
        border-radius: var(--radius-md);
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 0.5rem;
        backdrop-filter: blur(10px);
    }
    
    .recipe-title {
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
        line-height: 1.2;
    }
    
    .recipe-description {
        font-size: 0.95rem;
        margin-top: 0.5rem;
        opacity: 0.9;
        line-height: 1.4;
    }
    
    .recipe-body {
        padding: 1.5rem;
    }
    
    .recipe-meta-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    
    .meta-item {
        text-align: center;
        padding: 0.75rem;
        background: var(--background-secondary);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color);
        transition: all 0.2s ease;
    }
    
    .meta-item:hover {
        background: var(--background-tertiary);
        transform: translateY(-2px);
    }
    
    .meta-icon {
        font-size: 1.125rem;
        margin-bottom: 0.25rem;
        display: block;
    }
    
    .meta-value {
        font-weight: 600;
        color: var(--text-primary);
        font-size: 0.875rem;
        margin: 0;
    }
    
    .meta-label {
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin: 0;
    }
    
    /* ===================
       RECIPE CONTENT
    =================== */
    .recipe-content-grid {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        margin-top: 1.5rem;
    }
    
    @media (max-width: 768px) {
        .recipe-content-grid {
            grid-template-columns: 1fr;
            gap: 1.5rem;
        }
    }
    
    .ingredients-section, .instructions-section {
        background: var(--background-secondary);
        padding: 1.5rem;
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-color);
    }
    
    .section-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 1rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .ingredient-list, .instruction-list {
        list-style: none;
        padding: 0;
        margin: 0;
    }
    
    .ingredient-item, .instruction-item {
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        background: var(--background-primary);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color);
        font-size: 0.875rem;
        line-height: 1.4;
        transition: all 0.2s ease;
    }
    
    .ingredient-item:hover, .instruction-item:hover {
        background: var(--background-tertiary);
        transform: translateX(4px);
    }
    
    .instruction-item {
        position: relative;
        padding-left: 2.5rem;
    }
    
    .instruction-number {
        position: absolute;
        left: 0.75rem;
        top: 0.75rem;
        width: 1.5rem;
        height: 1.5rem;
        background: var(--primary-color);
        color: white;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.75rem;
        font-weight: 600;
    }
    
    /* ===================
       NUTRITION INFO
    =================== */
    .nutrition-section {
        margin-top: 1.5rem;
        padding: 1.5rem;
        background: linear-gradient(135deg, #ecfdf5 0%, #f0fdf4 100%);
        border: 1px solid #bbf7d0;
        border-radius: var(--radius-lg);
    }
    
    .nutrition-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: #065f46;
        margin: 0 0 0.75rem 0;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    
    .nutrition-content {
        font-size: 0.875rem;
        color: #047857;
        line-height: 1.6;
    }
    
    /* ===================
       RATING SYSTEM
    =================== */
    .rating-section {
        margin-top: 1.5rem;
        padding: 1.5rem;
        background: var(--background-secondary);
        border-radius: var(--radius-lg);
        border: 1px solid var(--border-color);
    }
    
    .rating-title {
        font-size: 1.125rem;
        font-weight: 600;
        color: var(--text-primary);
        margin: 0 0 1rem 0;
        text-align: center;
    }
    
    .rating-buttons {
        display: flex;
        justify-content: center;
        gap: 0.5rem;
        flex-wrap: wrap;
    }
    
    .stButton > button {
        background: linear-gradient(135deg, var(--primary-color) 0%, #3b82f6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: var(--radius-md) !important;
        padding: 0.75rem 1rem !important;
        font-weight: 600 !important;
        font-size: 0.875rem !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-shadow: var(--shadow-sm) !important;
        min-height: unset !important;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px) !important;
        box-shadow: var(--shadow-md) !important;
        background: linear-gradient(135deg, var(--primary-hover) 0%, var(--primary-color) 100%) !important;
    }
    
    /* ===================
       SHOPPING LIST
    =================== */
    .shopping-overview {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background: var(--background-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin: 0;
    }
    
    .metric-label {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin-top: 0.25rem;
    }
    
    .category-section {
        background: var(--background-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        margin-bottom: 1rem;
        overflow: hidden;
        box-shadow: var(--shadow-sm);
    }
    
    .category-header {
        background: var(--background-secondary);
        padding: 1rem 1.5rem;
        border-bottom: 1px solid var(--border-color);
        font-weight: 600;
        color: var(--text-primary);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .category-items {
        padding: 1.5rem;
    }
    
    .shopping-item {
        padding: 0.75rem;
        margin-bottom: 0.5rem;
        background: var(--background-secondary);
        border-radius: var(--radius-md);
        border: 1px solid var(--border-color);
        font-size: 0.875rem;
        transition: all 0.2s ease;
    }
    
    .shopping-item:hover {
        background: var(--background-tertiary);
        transform: translateX(4px);
    }
    
    /* ===================
       SIDEBAR IMPROVEMENTS
    =================== */
    .sidebar-metric {
        background: var(--background-primary);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        padding: 1.5rem;
        margin: 1rem 0;
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: var(--shadow-sm);
    }
    
    .sidebar-metric:hover {
        transform: translateY(-2px);
        box-shadow: var(--shadow-md);
    }
    
    .sidebar-metric h3 {
        font-size: 2rem;
        font-weight: 700;
        color: var(--primary-color);
        margin: 0;
    }
    
    .sidebar-metric p {
        font-size: 0.875rem;
        color: var(--text-secondary);
        margin: 0.5rem 0 0 0;
    }
    
    /* ===================
       ALERTS & MESSAGES
    =================== */
    .stAlert {
        border-radius: var(--radius-lg) !important;
        border: none !important;
        box-shadow: var(--shadow-sm) !important;
    }
    
    .stSuccess {
        background-color: #ecfdf5 !important;
        color: #065f46 !important;
        border-left: 4px solid var(--success-color) !important;
    }
    
    .stError {
        background-color: #fef2f2 !important;
        color: #991b1b !important;
        border-left: 4px solid var(--error-color) !important;
    }
    
    .stWarning {
        background-color: #fffbeb !important;
        color: #92400e !important;
        border-left: 4px solid var(--warning-color) !important;
    }
    
    .stInfo {
        background-color: #eff6ff !important;
        color: #1e40af !important;
        border-left: 4px solid var(--primary-color) !important;
    }
    
    /* ===================
       RESPONSIVE DESIGN
    =================== */
    @media (max-width: 768px) {
        .app-title {
            font-size: 2rem;
        }
        
        .recipe-content-grid {
            grid-template-columns: 1fr;
        }
        
        .shopping-overview {
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
        }
        
        .main-header {
            padding: 1.5rem 0;
        }
        
        .recipe-body {
            padding: 1rem;
        }
        
        .ingredients-section, .instructions-section {
            padding: 1rem;
        }
    }
    
    /* ===================
       ANIMATIONS
    =================== */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .recipe-card {
        animation: fadeInUp 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* ===================
       LOADING STATES
    =================== */
    .stSpinner {
        text-align: center;
    }
    
    /* ===================
       INPUT IMPROVEMENTS
    =================== */
    .stTextInput > div > div > input {
        border-radius: var(--radius-lg) !important;
        border: 2px solid var(--border-color) !important;
        padding: 0.75rem 1rem !important;
        transition: all 0.3s ease !important;
        font-size: 0.875rem !important;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color) !important;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1) !important;
        outline: none !important;
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
    """週間夕食プランをレンダリング（モダンUI版）"""
    
    # プラン概要をモダンデザインで表示
    st.markdown("""
    <div class="shopping-overview">
    """, unsafe_allow_html=True)
    
    total_cost = sum(dinner.get('estimated_cost', 0) for dinner in dinners)
    total_ingredients = shopping_list.get('total_unique_ingredients', 0)
    avg_time = sum(dinner.get('detailed_recipe', {}).get('prep_time', 15) + 
                   dinner.get('detailed_recipe', {}).get('cook_time', 30) for dinner in dinners) // len(dinners)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">¥{total_cost:.0f}</div>
            <div class="metric-label">総予算</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{total_ingredients}</div>
            <div class="metric-label">食材種類</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{avg_time}</div>
            <div class="metric-label">平均調理時間(分)</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{len(dinners)}</div>
            <div class="metric-label">メニュー数</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    # タブで整理
    tab1, tab2 = st.tabs(["🍽️ 夕食メニュー", "🛒 買い物リスト"])
    
    with tab1:
        for i, dinner in enumerate(dinners):
            # シンプルで見やすいレシピカード
            with st.container():
                st.markdown(f"## 🍳 Day {dinner['day']} ({dinner['date']})")
                st.markdown(f"### {dinner['main_dish']}")
                st.write(dinner.get('description', ''))
                
                # メタ情報をシンプルに表示
                meta_col1, meta_col2, meta_col3, meta_col4, meta_col5 = st.columns(5)
                
                with meta_col1:
                    st.metric("💰 コスト", f"¥{dinner.get('estimated_cost', 0):.0f}")
                
                with meta_col2:
                    prep_time = dinner.get('detailed_recipe', {}).get('prep_time', 15)
                    st.metric("⏱️ 準備", f"{prep_time}分")
                
                with meta_col3:
                    cook_time = dinner.get('detailed_recipe', {}).get('cook_time', 30)
                    st.metric("🔥 調理", f"{cook_time}分")
                
                with meta_col4:
                    servings = dinner.get('detailed_recipe', {}).get('servings', 2)
                    st.metric("👥 分量", f"{servings}人分")
                
                with meta_col5:
                    difficulty = dinner.get('cooking_difficulty', '普通')
                    difficulty_emoji = {"簡単": "🟢", "普通": "🟡", "難しい": "🔴"}.get(difficulty, "🟡")
                    st.metric(f"{difficulty_emoji} 難易度", difficulty)
            
            # シンプルで見やすい材料と作り方
            recipe_col1, recipe_col2 = st.columns(2)
            
            with recipe_col1:
                st.subheader("🥬 材料")
                ingredients = dinner.get('ingredients', [])
                for ingredient in ingredients:
                    st.write(f"• {ingredient}")
            
            with recipe_col2:
                st.subheader("📋 作り方")
                instructions = dinner.get('detailed_recipe', {}).get('instructions', [])
                for j, step in enumerate(instructions, 1):
                    st.write(f"{j}. {step}")
            
            st.divider()
            
            # 栄養情報をシンプルに表示
            nutrition = dinner.get('nutrition_info', '情報なし')
            if nutrition != '情報なし':
                st.subheader("🍎 栄養情報")
                st.info(nutrition)
            
            # 評価セクションをシンプルに表示
            st.subheader("⭐ このレシピを評価してください")
            rating_key = f"dinner_rating_{dinner['day']}_{i}"
            rating_cols = st.columns(5)
            for star in range(1, 6):
                with rating_cols[star-1]:
                    if st.button(f"{'⭐' * star}", key=f"{rating_key}_{star}", use_container_width=True):
                        rate_dinner_recipe(dinner, star)
                        st.rerun()
                
                st.markdown("---")  # レシピの区切り
    
    with tab2:
        # 買い物リスト概要
        st.markdown("""
        <div class="shopping-overview">
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{shopping_list.get('total_unique_ingredients', 0)}</div>
                <div class="metric-label">総食材数</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">¥{shopping_list.get('total_estimated_cost', 0):.0f}</div>
                <div class="metric-label">予算総額</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{shopping_list.get('estimated_shopping_time', '30-45分')}</div>
                <div class="metric-label">買い物時間</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # カテゴリ別買い物リスト
        categories = shopping_list.get('ingredients_by_category', {})
        for category, items in categories.items():
            if items:  # アイテムがある場合のみ表示
                st.markdown(f"""
                <div class="category-section">
                    <div class="category-header">
                        <span>{category}</span>
                        <span>{len(items)}品目</span>
                    </div>
                    <div class="category-items">
                """, unsafe_allow_html=True)
                
                for item in items:
                    st.markdown(f'<div class="shopping-item">{item}</div>', unsafe_allow_html=True)
                
                st.markdown("</div></div>", unsafe_allow_html=True)
        
        # 買い物のコツ
        notes = shopping_list.get('shopping_notes', [])
        if notes:
            st.markdown("""
            <div style="margin-top: 2rem;">
                <h3 style="color: var(--text-primary); margin-bottom: 1rem;">💡 買い物のコツ</h3>
            </div>
            """, unsafe_allow_html=True)
            
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
                        <span class="meta-item">💰 ¥{recipe.estimated_cost:.0f}</span>
                        <span class="meta-item">⏱️ {recipe.total_time}分</span>
                        <span class="meta-item">🌍 {recipe.cuisine_type}</span>
                        <span class="meta-item">👤 {recipe.servings}人分</span>
                    </div>
                    <div style="margin-top: 1rem;"><strong>材料:</strong> {', '.join(recipe.ingredients[:3])}{'...' if len(recipe.ingredients) > 3 else ''}</div>
                    <div class="learning-badge" style="margin-top: 1rem;">AI学習型レシピ</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("### ⭐ このレシピを評価")
                rating_key = f"rating_{recipe.name}_{i}"
                
                # 星評価ボタン
                rating_cols = st.columns(5)
                for star in range(1, 6):
                    with rating_cols[star-1]:
                        if st.button(f"{'⭐' * star}", key=f"{rating_key}_{star}", use_container_width=True):
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
        
        # 動的思考過程表示
        thinking_placeholder = st.empty()
        progress_placeholder = st.empty()
        
        debug_messages = []
        
        def debug_callback(message: str):
            """AIの思考過程を動的表示"""
            debug_messages.append(f"⏰ {datetime.now().strftime('%H:%M:%S')} - {message}")
            
            # 動的更新（現在の思考のみ表示）
            with thinking_placeholder.container():
                st.markdown("### 🧠 AI思考中...")
                # 最新のメッセージを大きく表示
                if debug_messages:
                    latest_msg = debug_messages[-1]
                    st.markdown(f"**{latest_msg}**")
                
                # 最新3件の履歴を小さく表示
                if len(debug_messages) > 1:
                    st.markdown("**直前の思考:**")
                    for msg in debug_messages[-4:-1]:  # 最新を除く3件
                        st.markdown(f"<small>✓ {msg}</small>", unsafe_allow_html=True)
            
            # プログレスバー更新
            with progress_placeholder.container():
                progress = min(len(debug_messages) * 5, 100)
                st.progress(progress / 100, text=f"思考進行中... ({len(debug_messages)}/20 ステップ)")
        
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
        
        # 週間夕食プラン生成（デバッグコールバック付き）
        result = await agent.generate_weekly_dinner_plan(
            days=days,
            user_request=user_message,
            include_sale_info=True,
            sale_url="cache",
            debug_callback=debug_callback
        )
        
        dinners = result.get("dinners", [])
        shopping_list = result.get("shopping_list", {})
        
        # 思考過程表示をクリア
        thinking_placeholder.empty()
        progress_placeholder.empty()
        
        # 完了メッセージを簡潔に表示
        st.success(f"✅ {days}日分の夕食プラン生成完了！")
        
        # AI思考プロセス詳細（折りたたまれた状態）
        with st.expander("🔍 AI思考プロセス詳細（クリックで展開）"):
            for msg in debug_messages:
                st.markdown(f"<small>{msg}</small>", unsafe_allow_html=True)
        
        # 生成されたレシピのデバッグ情報
        with st.expander("🧪 レシピデバッグ情報"):
            st.write("### 生成結果詳細")
            st.write(f"**Success**: {result.get('success')}")
            st.write(f"**Fallback Used**: {result.get('fallback', False)}")
            st.write(f"**Error Details**: {result.get('error_details', 'なし')}")
            st.write(f"**Total Cost**: ¥{result.get('total_estimated_cost', 0):.0f}")
            
            if dinners:
                st.write("### 生成されたレシピ")
                try:
                    for i, dinner in enumerate(dinners):
                        st.write(f"**Day {i+1}**: {dinner.get('main_dish', 'Unknown')}")
                        
                        # 説明の安全な表示
                        description = dinner.get('description', 'No description')
                        if description and len(description) > 100:
                            st.write(f"説明: {description[:100]}...")
                        else:
                            st.write(f"説明: {description}")
                        
                        # フォールバック判定（改良版）
                        try:
                            fallback_patterns = [
                                ('鶏の照り焼き丼', '美味しい鶏の照り焼き丼です'),
                                ('鮭のムニエル', '美味しい鮭のムニエルです'),  
                                ('豚の生姜焼き', '美味しい豚の生姜焼きです'),
                                ('オムライス', '美味しいオムライスです'),
                                ('カレーライス', '美味しいカレーライスです'),
                                ('ハンバーグ', '美味しいハンバーグです'),
                                ('麻婆豆腐', '美味しい麻婆豆腐です')
                            ]
                            
                            main_dish = dinner.get('main_dish', '')
                            
                            # 実際のフォールバック判定基準
                            is_fallback = False
                            
                            # 1. result.get('fallback') をチェック
                            if result.get('fallback', False):
                                is_fallback = True
                            
                            # 2. パターンマッチング（料理名 + 説明の組み合わせ）
                            elif main_dish:
                                for fallback_dish, fallback_desc in fallback_patterns:
                                    if (fallback_dish == main_dish and 
                                        fallback_desc in description):
                                        is_fallback = True
                                        break
                            
                            if is_fallback:
                                st.warning(f"⚠️ Day {i+1} はフォールバック応答です")
                            else:
                                st.success(f"✅ Day {i+1} は実際のClaude生成レシピです")
                                
                        except Exception as fallback_error:
                            st.error(f"Day {i+1} フォールバック判定エラー: {fallback_error}")
                            
                        # レシピ品質の詳細表示
                        ingredients_count = len(dinner.get('ingredients', []))
                        instructions_count = len(dinner.get('detailed_recipe', {}).get('instructions', []))
                        
                        if ingredients_count > 5 and instructions_count > 3:
                            st.info(f"📊 詳細レシピ: 材料{ingredients_count}種類、手順{instructions_count}ステップ")
                        else:
                            st.warning(f"📊 簡易レシピ: 材料{ingredients_count}種類、手順{instructions_count}ステップ")
                            
                except Exception as dinner_error:
                    st.error(f"レシピ表示エラー: {dinner_error}")
                    st.write("Raw dinner data:")
                    st.write(dinners)
            else:
                st.error("レシピが生成されませんでした")
        
        # Raw Data表示
        with st.expander("📋 Raw Data"):
            st.json(result)
        
        # レスポンス生成
        if dinners:
            response = f"🍽️ **{days}日分の夕食プラン**を作成しました！\n\n"
            response += f"💰 **総予算**: ¥{result.get('total_estimated_cost', 0):.0f}\n"
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
    
    # モダンヘッダー
    st.markdown("""
    <div class="main-header">
        <div class="header-content">
            <h1 class="app-title">🍽️ Flavia AI 料理パートナー</h1>
            <p class="app-subtitle">あなた専用の学習型AI料理アシスタント ✨</p>
        </div>
    </div>
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