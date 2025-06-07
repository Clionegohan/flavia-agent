import streamlit as st
import asyncio
from typing import List
from ..agent.flavia import FlaviaAgent
from ..data.models import MealPreferences, Recipe
from ..exceptions import (
    FlaviaException, AIProviderError, NetworkError, ParseError, 
    ConfigurationError, AuthenticationError, RateLimitError,
    QuotaExceededError
)


st.set_page_config(
    page_title="Flavia - AI Meal Planner",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Flavia - AI Meal Planning Assistant")
st.markdown("Generate personalized meal plans based on your budget and preferences!")


@st.cache_resource
def get_agent():
    """エージェントインスタンスを取得（キャッシュ付き）"""
    try:
        return FlaviaAgent(
            primary_provider="openai",
            fallback_provider="anthropic",
            timeout=45.0
        )
    except ConfigurationError as e:
        st.error(f"⚙️ Configuration Error: {e.message}")
        if e.config_key:
            st.info(f"Please set the environment variable: {e.config_key}")
        st.stop()


def display_recipe(recipe: Recipe):
    """レシピを表示する（強化版）"""
    with st.expander(f"🍳 {recipe.name} (${recipe.estimated_cost:.2f})"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**🥘 Ingredients:**")
            for ingredient in recipe.ingredients:
                st.markdown(f"• {ingredient}")
        
        with col2:
            st.markdown("**📊 Details:**")
            st.markdown(f"• **⏱️ Prep Time:** {recipe.prep_time} min")
            st.markdown(f"• **🔥 Cook Time:** {recipe.cook_time} min")
            st.markdown(f"• **👥 Servings:** {recipe.servings}")
            st.markdown(f"• **💰 Total Cost:** ${recipe.estimated_cost:.2f}")
            st.markdown(f"• **💵 Cost per Serving:** ${recipe.cost_per_serving:.2f}")
            st.markdown(f"• **🌍 Cuisine:** {recipe.cuisine_type}")
            st.markdown(f"• **📈 Difficulty:** {recipe.difficulty}")
            st.markdown(f"• **⏰ Total Time:** {recipe.total_time} min")
        
        st.markdown("**👩‍🍳 Instructions:**")
        for i, instruction in enumerate(recipe.instructions, 1):
            st.markdown(f"{i}. {instruction}")


def display_error_message(error: Exception) -> None:
    """エラーメッセージを適切に表示する"""
    
    if isinstance(error, ConfigurationError):
        st.error("⚙️ **Configuration Error**")
        st.markdown(f"**Issue:** {error.message}")
        if error.config_key:
            st.info(f"**Solution:** Please set the environment variable: `{error.config_key}`")
        st.markdown("**Help:** Check your .env file or environment settings.")
    
    elif isinstance(error, AuthenticationError):
        st.error("🔐 **Authentication Error**")
        st.markdown(f"**Issue:** {error.message}")
        st.markdown(f"**Provider:** {error.details.get('provider', 'Unknown')}")
        st.info("**Solution:** Please check your API key. It may be invalid or expired.")
    
    elif isinstance(error, RateLimitError):
        st.warning("⏱️ **Rate Limit Exceeded**")
        st.markdown(f"**Issue:** {error.message}")
        st.markdown(f"**Provider:** {error.details.get('provider', 'Unknown')}")
        retry_after = error.details.get('retry_after')
        if retry_after:
            st.info(f"**Solution:** Please wait {retry_after} seconds before trying again.")
        else:
            st.info("**Solution:** Please wait a few minutes before trying again.")
    
    elif isinstance(error, QuotaExceededError):
        st.error("💳 **Quota Exceeded**")
        st.markdown(f"**Issue:** {error.message}")
        st.markdown(f"**Provider:** {error.details.get('provider', 'Unknown')}")
        st.info("**Solution:** Please check your billing settings or upgrade your plan.")
    
    elif isinstance(error, NetworkError):
        st.error("🌐 **Network Error**")
        st.markdown(f"**Issue:** {error.message}")
        if error.details.get('url'):
            st.markdown(f"**URL:** {error.details['url']}")
        st.info("**Solution:** Please check your internet connection and try again.")
    
    elif isinstance(error, ParseError):
        st.error("📄 **Data Processing Error**")
        st.markdown("**Issue:** The AI response could not be processed properly.")
        st.markdown(f"**Details:** {error.message}")
        st.info("**Solution:** Please try again. If the problem persists, the AI service may be experiencing issues.")
        
        # デバッグ情報（展開可能）
        with st.expander("🔍 Debug Information"):
            st.markdown(f"**Parser Type:** {error.details.get('parser_type', 'Unknown')}")
            raw_data = error.details.get('raw_data')
            if raw_data:
                st.code(raw_data[:500] + "..." if len(raw_data) > 500 else raw_data)
    
    elif isinstance(error, AIProviderError):
        st.error("🤖 **AI Service Error**")
        st.markdown(f"**Issue:** {error.message}")
        st.markdown(f"**Provider:** {error.details.get('provider', 'Unknown')}")
        status_code = error.details.get('status_code')
        if status_code:
            st.markdown(f"**Status Code:** {status_code}")
        st.info("**Solution:** Please try again later. The AI service may be temporarily unavailable.")
    
    elif isinstance(error, FlaviaException):
        st.error("⚠️ **Application Error**")
        st.markdown(f"**Issue:** {error.message}")
        if error.details:
            with st.expander("🔍 Error Details"):
                st.json(error.details)
        st.info("**Solution:** Please try again or contact support if the problem persists.")
    
    else:
        # 未知のエラー
        st.error("❌ **Unexpected Error**")
        st.markdown(f"**Issue:** {str(error)}")
        st.markdown(f"**Type:** {type(error).__name__}")
        st.info("**Solution:** Please try again or contact support.")


async def generate_meal_plan_async(preferences: MealPreferences) -> List[Recipe]:
    """非同期で献立を生成"""
    agent = get_agent()
    return await agent.generate_meal_plan(preferences)


def main():
    """メインアプリケーション"""
    
    # サイドバー: 設定
    st.sidebar.header("🍽️ Meal Preferences")
    
    # 予算設定
    budget = st.sidebar.number_input(
        "💰 Budget ($)", 
        min_value=5.0, 
        max_value=200.0, 
        value=30.0, 
        step=5.0,
        help="Total budget for the meal plan"
    )
    
    # 調理時間
    cooking_time = st.sidebar.slider(
        "⏱️ Max Cooking Time (minutes)", 
        15, 120, 30,
        help="Maximum total cooking time per recipe"
    )
    
    # 人数
    servings = st.sidebar.number_input(
        "👥 Number of Servings", 
        min_value=1, 
        max_value=10, 
        value=4,
        help="Number of people to serve"
    )
    
    # 食事制限
    dietary_restrictions = st.sidebar.multiselect(
        "🥗 Dietary Restrictions",
        ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Low-Carb", "High-Protein"],
        help="Select any dietary restrictions"
    )
    
    # 料理の種類
    cuisine_preferences = st.sidebar.multiselect(
        "🌍 Cuisine Preferences",
        ["Italian", "Mexican", "Asian", "Mediterranean", "American", "Indian", "Thai", "French"],
        help="Select preferred cuisine types"
    )
    
    # 生成ボタン
    generate_button = st.sidebar.button(
        "🚀 Generate Meal Plan", 
        type="primary",
        help="Generate personalized recipes based on your preferences"
    )
    
    # メイン画面
    if generate_button:
        try:
            # 入力バリデーション
            preferences = MealPreferences(
                budget=budget,
                dietary_restrictions=dietary_restrictions,
                cuisine_preferences=cuisine_preferences,
                cooking_time=cooking_time,
                servings=servings
            )
            
            # 進捗表示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            with st.spinner("🤖 Generating your personalized meal plan..."):
                status_text.text("🔄 Connecting to AI service...")
                progress_bar.progress(25)
                
                status_text.text("🧠 Analyzing your preferences...")
                progress_bar.progress(50)
                
                status_text.text("🍳 Generating recipes...")
                progress_bar.progress(75)
                
                # 献立生成
                recipes = asyncio.run(generate_meal_plan_async(preferences))
                
                progress_bar.progress(100)
                status_text.text("✅ Generation complete!")
                
                # 結果表示
                if recipes:
                    # 成功メッセージ
                    st.success(f"🎉 Generated {len(recipes)} delicious recipes for you!")
                    
                    # 統計情報
                    total_cost = sum(recipe.estimated_cost for recipe in recipes)
                    avg_time = sum(recipe.total_time for recipe in recipes) // len(recipes)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("💰 Total Cost", f"${total_cost:.2f}")
                    with col2:
                        st.metric("⏱️ Avg Cooking Time", f"{avg_time} min")
                    with col3:
                        st.metric("🍽️ Recipes Generated", len(recipes))
                    
                    # レシピ表示
                    st.markdown("---")
                    for i, recipe in enumerate(recipes, 1):
                        st.markdown(f"### Recipe {i}")
                        display_recipe(recipe)
                else:
                    st.warning("🤔 No recipes were generated. Please try adjusting your preferences.")
                
                # プログレスバーをクリア
                progress_bar.empty()
                status_text.empty()
        
        except Exception as e:
            # エラー表示
            display_error_message(e)
    
    else:
        # 初期画面
        st.markdown("### 👋 Welcome to Flavia!")
        st.markdown("""
        **Flavia** is your AI-powered meal planning assistant. Here's how it works:
        
        1. **🍽️ Set Your Preferences:** Use the sidebar to configure your budget, dietary restrictions, and preferences
        2. **🚀 Generate:** Click the "Generate Meal Plan" button
        3. **🍳 Cook & Enjoy:** Get personalized recipes with detailed instructions
        
        **Features:**
        - 🤖 AI-powered recipe generation
        - 💰 Budget-conscious planning
        - 🥗 Dietary restriction support
        - ⏱️ Time-based filtering
        - 🌍 Multi-cuisine options
        """)
        
        # サンプル画像やデモ情報
        st.markdown("### 🌟 Example Output")
        st.markdown("Here's what you can expect:")
        
        example_col1, example_col2 = st.columns(2)
        with example_col1:
            st.info("""
            **🍝 Recipe Example:**
            - Name: Creamy Mushroom Pasta
            - Cost: $12.50 (4 servings)
            - Time: 25 minutes
            - Difficulty: Easy
            """)
        
        with example_col2:
            st.info("""
            **📊 Smart Analysis:**
            - Nutritional breakdown
            - Cost per serving
            - Cooking complexity
            - Time optimization
            """)
    
    # サイドバー: 設定情報
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Configuration")
    
    # API設定状況の表示
    import os
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    anthropic_configured = bool(os.getenv("ANTHROPIC_API_KEY"))
    
    st.sidebar.markdown("**AI Providers:**")
    st.sidebar.markdown(f"• OpenAI: {'✅' if openai_configured else '❌'}")
    st.sidebar.markdown(f"• Anthropic: {'✅' if anthropic_configured else '❌'}")
    
    if not (openai_configured or anthropic_configured):
        st.sidebar.error("⚠️ No AI providers configured!")
        st.sidebar.markdown("Set at least one API key in your .env file.")
    
    # ヘルプ情報
    with st.sidebar.expander("💡 Tips"):
        st.markdown("""
        **For better results:**
        - Be specific about dietary restrictions
        - Set realistic budgets
        - Choose 2-3 cuisine types max
        - Allow reasonable cooking time
        """)


if __name__ == "__main__":
    main()