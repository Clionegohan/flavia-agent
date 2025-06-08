"""シンプルなStreamlitテスト"""

import streamlit as st

st.title("🍽️ Flavia Test App")
st.write("Hello from Streamlit!")

if st.button("Test Button"):
    st.success("Button clicked! Streamlit is working!")

st.sidebar.write("Sidebar working too!")