import streamlit as st
import random
import json
import os
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# スプレッドシートへの接続設定
conn = st.connection("gsheets", type=GSheetsConnection)

# デッキを保存する関数
def save_deck_to_gsheet(deck_name, df):
    # すべてのデータを一度読み込み、新しいデータを追加して書き戻す
    existing_data = conn.read()
    df["deck_name"] = deck_name # どのデッキのカードか判別する列を追加
    updated_df = pd.concat([existing_data, df], ignore_index=True)
    conn.update( data=updated_df)

# --- 設定と初期化 ---
st.set_page_config(page_title="Card Deck Builder", layout="centered")

if not os.path.exists("decks"):
    os.makedirs("decks")

if 'page' not in st.session_state:
    st.session_state.page = "HOME"
if 'player_hp' not in st.session_state:
    st.session_state.player_hp = 300
    st.session_state.cpu_hp = 300
    st.session_state.hand = [] # 現在の手札

# --- 画面描画 ---

# 1. ホーム画面
if st.session_state.page == "HOME":
    st.title("🃏 無限デッキバトラー")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎴 カードを好きなだけ登録する", use_container_width=True):
            st.session_state.page = "REGISTER"
            st.rerun()
    with col2:
        if st.button("⚔️ ゲームを開始する", use_container_width=True):
            st.session_state.page = "SELECT_DECK"
            st.rerun()

# 2. カード登録画面（データエディタ使用）
elif st.session_state.page == "REGISTER":
    st.title("📝 デッキ編集")
    deck_name = st.text_input("デッキ名", "MyCustomDeck")
    
    st.write("表にカード情報を入力してください（行を追加できます）")
    
    # 初期データ
    default_data = [
        {"カード名": "火炎", "画像URL": "img/fireball.png", "最小ダメ": 10, "最大ダメ": 20},
    ]
    
    # データエディタを表示（行の追加・削除を許可）
    edited_df = st.data_editor(
        pd.DataFrame(default_data), 
        num_rows="dynamic", 
        use_container_width=True,
        key="deck_editor"
    )

    if st.button("このデッキを保存して戻る", type="primary"):
        # 1. 編集されたデータをDataFrame（表形式）として取得
        edited_frame_df=pd.DataFrame(edited_df)
        # 2. スプレッドシートへ保存 (ここが呼び出し位置！)
        save_deck_to_gsheet(deck_name, edited_frame_df)
        st.cache_data.clear()
        
        st.success("スプレッドシートに保存しました！")
        st.session_state.page = "HOME"
        st.rerun()
    
    if st.button("戻る"):
        st.session_state.page = "HOME"
        st.rerun()

# 3. デッキ選択画面
elif st.session_state.page == "SELECT_DECK":
    st.title("🎮 デッキ選択")
    all_data_df=conn.read()
    # 【デバッグ用】読み込んだデータの中身を画面に表示して確認
    st.write("デバッグ: スプレッドシートの中身", all_data_df)
    st.write("デバッグ: 存在する列名", all_data_df.columns.tolist())
    deck_files = all_data_df["deck_name"].unique() if "deck_name" in all_data_df.columns else [] # スプレッドシートからデッキ名を取得

    selected_file = st.selectbox("デッキ選択", deck_files)
    if st.button("バトル開始！"):
        my_deck = all_data_df[all_data_df["deck_name"] == selected_file]  # 選択したデッキのカードデータを読み込む
        if len(my_deck) < 3:
            st.error("カードは3枚以上登録してください！")
        else:
            st.session_state.full_deck = my_deck.to_dict(orient="records")  # デッキ全体をセッションに保存
            st.session_state.player_hp = 300
            st.session_state.cpu_hp = 300
            # 最初の3枚をドロー
            st.session_state.hand = random.sample(st.session_state.full_deck, 3)
            st.session_state.page = "BATTLE"
            st.rerun()

# 4. バトル画面
elif st.session_state.page == "BATTLE":
    st.title("⚔️ バトル！")
    
    # HP表示
    c1, c2 = st.columns(2)
    c1.metric("PLAYER HP", st.session_state.player_hp)
    c2.metric("ENEMY HP", st.session_state.cpu_hp)
    
    st.divider()
    
    # 手札（ランダムに選ばれた3枚）を表示
    st.write("### あなたの手札（ランダムに選出）")
    cols = st.columns(3)
    for i, card in enumerate(st.session_state.hand):
        with cols[i]:
            st.image(card["画像URL"], use_container_width=True)
            st.write(f"**")
            if st.button(f"使う", key=f"play_{i}", use_container_width=True):
                # ダメージ処理
                min_val = int(float(card["最小ダメ"]))
                max_val = int(float(card["最大ダメ"]))
                dmg = random.randint(min_val, max_val)
                st.session_state.cpu_hp -= dmg
                st.session_state.player_hp -= random.randint(10, 15) # 敵の反撃
                
                # 次のターン用に新しい3枚をドロー
                st.session_state.hand = random.sample(st.session_state.full_deck, 3)
                
                if st.session_state.cpu_hp <= 0 or st.session_state.player_hp <= 0:
                    st.session_state.page = "RESULT"
                st.rerun()

# 5. 結果画面
elif st.session_state.page == "RESULT":
    if st.session_state.player_hp > st.session_state.cpu_hp:
        st.balloons(); st.success("WIN!")
    else:
        st.error("LOSE...")
    if st.button("HOME"):
        st.session_state.page = "HOME"; st.rerun()