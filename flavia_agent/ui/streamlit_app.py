import streamlit as st
import asyncio
from typing import List
from ..agent.flavia import FlaviaAgent
from ..agent.base import MealPreferences, Recipe


st.set_page_config(
    page_title="Flavia - AI Meal Planner",
    page_icon="🍽️",
    layout="wide"
)

st.title("🍽️ Flavia - AI Meal Planning Assistant")
st.markdown("Generate personalized meal plans based on your budget and preferences!")


@st.cache_resource
def get_agent():
    return FlaviaAgent(provider="openai")


def display_recipe(recipe: Recipe):
    with st.expander(f"🍳 {recipe.name}"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Ingredients:**")
            for ingredient in recipe.ingredients:
                st.markdown(f"• {ingredient}")
        
        with col2:
            st.markdown("**Details:**")
            st.markdown(f"• **Prep Time:** {recipe.prep_time} min")
            st.markdown(f"• **Cook Time:** {recipe.cook_time} min")
            st.markdown(f"• **Servings:** {recipe.servings}")
            st.markdown(f"• **Estimated Cost:** ${recipe.estimated_cost:.2f}")
            st.markdown(f"• **Cuisine:** {recipe.cuisine_type}")
            st.markdown(f"• **Difficulty:** {recipe.difficulty}")
        
        st.markdown("**Instructions:**")
        for i, instruction in enumerate(recipe.instructions, 1):
            st.markdown(f"{i}. {instruction}")


async def generate_meal_plan_async(preferences: MealPreferences) -> List[Recipe]:
    agent = get_agent()
    return await agent.generate_meal_plan(preferences)


def main():
    st.sidebar.header("Meal Preferences")
    
    budget = st.sidebar.number_input("Budget ($)", min_value=5.0, max_value=200.0, value=30.0, step=5.0)
    
    cooking_time = st.sidebar.slider("Max Cooking Time (minutes)", 15, 120, 30)
    
    servings = st.sidebar.number_input("Number of Servings", min_value=1, max_value=10, value=4)
    
    dietary_restrictions = st.sidebar.multiselect(
        "Dietary Restrictions",
        ["Vegetarian", "Vegan", "Gluten-Free", "Dairy-Free", "Keto", "Low-Carb", "High-Protein"]
    )
    
    cuisine_preferences = st.sidebar.multiselect(
        "Cuisine Preferences",
        ["Italian", "Mexican", "Asian", "Mediterranean", "American", "Indian", "Thai", "French"]
    )
    
    if st.sidebar.button("Generate Meal Plan", type="primary"):
        preferences = MealPreferences(
            budget=budget,
            dietary_restrictions=dietary_restrictions,
            cuisine_preferences=cuisine_preferences,
            cooking_time=cooking_time,
            servings=servings
        )
        
        with st.spinner("🤖 Generating your personalized meal plan..."):
            try:
                recipes = asyncio.run(generate_meal_plan_async(preferences))
                
                if recipes:
                    st.success(f"Generated {len(recipes)} recipes for you!")
                    for recipe in recipes:
                        display_recipe(recipe)
                else:
                    st.error("Sorry, couldn't generate recipes. Please check your API configuration.")
            except Exception as e:
                st.error(f"Error generating meal plan: {str(e)}")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Configuration")
    st.sidebar.info("Make sure to set your OPENAI_API_KEY or ANTHROPIC_API_KEY environment variable.")


if __name__ == "__main__":
    main()