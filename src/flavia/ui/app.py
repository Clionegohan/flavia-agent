"""シンプルなFlavia AI料理アシスタント UI"""

import streamlit as st
import asyncio
import sys
from pathlib import Path

# パス設定
sys.path.append(str(Path(__file__).parent.parent.parent))

from flavia.assistant import flavia_agent
from flavia.data_manager import data_manager


def main():
    """メインアプリケーション"""
    st.set_page_config(
        page_title="Flavia AI 料理アシスタント",
        page_icon="🍳",
        layout="wide"
    )
    
    st.title("🍳 Flavia AI 料理アシスタント")
    st.markdown("あなた専用のAI料理パートナー")
    
    # サイドバー：個人データ管理
    with st.sidebar:
        st.header("👤 個人データ管理")
        
        # 個人データ更新フォーム
        with st.expander("🔄 嗜好・制約の更新"):
            st.markdown("最近の食の変化を教えてください：")
            
            preference_update = st.text_area(
                "例：最近パクチーが好きになった、魚料理をもっと食べたい、など",
                placeholder="最近辛い物が苦手になりました。代わりに優しい味の料理が好きです。"
            )
            
            if st.button("📝 嗜好を更新"):
                if preference_update:
                    success = data_manager.update_preferences_from_text(preference_update)
                    if success:
                        st.success("嗜好情報を記録しました！")
                        st.info("次回のレシピ提案から反映されます")
                    else:
                        st.error("更新の保存に失敗しました")
                else:
                    st.warning("更新内容を入力してください")
        
        # 最近の更新履歴
        with st.expander("📋 最近の更新履歴"):
            recent_updates = data_manager.get_recent_updates(days=7)
            if recent_updates:
                for update in recent_updates[-3:]:  # 最新3件
                    date = update["timestamp"][:10]
                    st.text(f"{date}: {update['update_text'][:50]}...")
            else:
                st.text("まだ更新履歴がありません")
        
        st.divider()
        
        # 使用例
        st.header("💡 使用例")
        st.markdown("""
        **レシピ相談：**
        - 今日の夕食何作ろう？
        - 鶏肉を使った簡単料理
        - 野菜たっぷりヘルシー料理
        - 30分で作れる和食
        
        **献立計画：**
        - 3日分の夕食献立
        - 週末の特別メニュー
        """)
    
    # メインエリア：チャット
    st.header("💬 料理相談チャット")
    
    # ユーザー入力
    user_input = st.text_input(
        "どんな料理を作りたいですか？",
        placeholder="例: 今日の夕食におすすめの料理を教えて",
        help="自由に料理の相談をしてください"
    )

    # 献立生成エリア
    st.markdown("---")  # 区切り線
    
    # 献立日数選択
    days = st.selectbox("📅 献立作成日数を選択", [1, 3, 5, 7], index=3, 
                       help="作成したい日数分の夕食献立を選択してください")
    
    # 献立作成ボタン
    if st.button(f"🍽️ {days}日分の献立を作成する", use_container_width=True, type="primary"):
        if user_input:
            generate_weekly_plan(user_input, days)
        else:
            generate_weekly_plan("栄養バランスの良い夕食", days)
    
    # 保存された献立があれば表示（新規生成時以外）
    elif "last_plan" in st.session_state:
        display_weekly_plan(st.session_state.last_plan)


def generate_weekly_plan(user_request: str, days: int):
    """週間献立生成"""
    with st.spinner(f"📅 {days}日分の献立を作成しています..."):
        
        # デバッグ表示用のプレースホルダー
        debug_placeholder = st.empty()
        debug_messages = []
        
        def debug_callback(message: str):
            debug_messages.append(message)
            debug_placeholder.text("\n".join(debug_messages))
        
        try:
            # 非同期関数の実行
            result = asyncio.run(
                flavia_agent.generate_weekly_dinner_plan(days, user_request, debug_callback)
            )
            
            # デバッグメッセージをクリア
            debug_placeholder.empty()
            
            # セッション状態に保存
            st.session_state.last_plan = result
            
            # 結果表示
            display_weekly_plan(result)
        
        except Exception as e:
            debug_placeholder.empty()
            st.error(f"週間献立生成エラー: {str(e)}")


def display_weekly_plan(plan: dict):
    """週間献立表示"""
    st.success(f"✅ {plan['plan_days']}日分の献立が完成しました！")
    
    # 献立一覧
    st.subheader("📅 週間献立")
    
    for dinner in plan.get('dinners', []):
        with st.expander(f"Day {dinner['day']} ({dinner.get('date', '')}) - {dinner.get('main_dish', '')}"):
            st.write(f"**説明:** {dinner.get('description', '')}")
            
            # 材料
            st.write("**材料:**")
            ingredients_text = ", ".join(dinner.get('ingredients', []))
            st.write(ingredients_text)
            
            # レシピ詳細
            recipe = dinner.get('detailed_recipe', {})
            if recipe:
                st.write(f"**調理時間:** 準備{recipe.get('prep_time', 0)}分 + 調理{recipe.get('cook_time', 0)}分")
                
                st.write("**作り方:**")
                for i, instruction in enumerate(recipe.get('instructions', []), 1):
                    st.write(f"{i}. {instruction}")
            
            # コスト
            if dinner.get('estimated_cost'):
                st.write(f"**推定コスト:** {dinner['estimated_cost']}円")
    
    # 買い物リスト
    shopping_list = plan.get('shopping_list', {})
    if shopping_list.get('items'):
        st.subheader("🛒 買い物リスト")
        
        st.info(f"購入予定: {shopping_list.get('total_items', 0)}品目")
        
        # 買い物リストを読みやすく表示
        shopping_text = " | ".join(shopping_list['items'])
        st.write(shopping_text)
        
        if shopping_list.get('notes'):
            st.caption(shopping_list['notes'])
        
        # Discord送信ボタン
        col1, col2 = st.columns([2, 1])
        with col2:
            # ユニークキー生成（generation_time + hash）
            import hashlib
            unique_key = hashlib.md5(str(plan.get('generation_time', '')).encode()).hexdigest()[:8]
            
            if st.button("📱 Discordに送信", use_container_width=True, key=f"discord_{unique_key}"):
                try:
                    success = flavia_agent.send_shopping_list_to_discord(shopping_list)
                    if success:
                        st.success("✅ Discordに送信しました！")
                    else:
                        st.error("❌ 送信に失敗しました\n（Webhook URLを確認してください）")
                except Exception as e:
                    st.error(f"❌ 送信エラー: {str(e)}")


if __name__ == "__main__":
    main()