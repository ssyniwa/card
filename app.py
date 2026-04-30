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
    existing_data = conn.read(ttl=0)  # キャッシュを無効にして最新のデータを取得 
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
# --- 事前に session_state に追加すべき変数 ---
if 'defense_flag' not in st.session_state: st.session_state.defense_flag = False
if 'buff_multiplier' not in st.session_state: st.session_state.buff_multiplier = 1.0
if 'poison_turn' not in st.session_state: st.session_state.poison_turn = 0
if 'poison' not in st.session_state: st.session_state.poison = 0
if 'debuff_multiplier' not in st.session_state: st.session_state.debuff_multiplier = 1.0
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
        {"カード名": "火炎", "画像URL": "img/fireball.png", "最小ダメ": 10, "最大ダメ": 20, "type": "攻撃","chara_image": "img/char_fire.png"},
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

    selected_file = st.selectbox("プレイヤーデッキ選択", deck_files)
    selected_enfile= st.selectbox("CPUデッキ選択", deck_files)
    if st.button("バトル開始！"):
        my_deck = all_data_df[all_data_df["deck_name"] == selected_file]
        en_deck = all_data_df[all_data_df["deck_name"] == selected_enfile]
        en_deck_filtered = en_deck[en_deck["type"].isin(["攻撃","回復"])]  # CPUは攻撃カードのみ使用
        if len(my_deck) < 3:
            st.error("カードは3枚以上登録してください！")
        else:
            st.session_state.full_deck = my_deck.to_dict(orient="records")  # デッキ全体をセッションに保存
            st.session_state.player_hp = 300
            st.session_state.en_full_deck = en_deck_filtered.to_dict(orient="records")  # CPUのデッキ全体をセッションに保存
            st.session_state.cpu_hp = 300
            st.session_state.player_img = my_deck.iloc[0]["chara_image"]
            st.session_state.en_img = en_deck.iloc[0]["chara_image"]
            # 最初の3枚をドロー
            st.session_state.hand = random.sample(st.session_state.full_deck, 3)
            st.session_state.page = "BATTLE"
            st.rerun()

# 4. バトル画面
elif st.session_state.page == "BATTLE":
    st.title("⚔️ バトル！")
    
    # HP表示
    c1, c2 = st.columns(2)
    c1.image(st.session_state.player_img, width=300)
    c1.metric("PLAYER HP", st.session_state.player_hp)
    c1.progress(max(0,min(st.session_state.player_hp/300,1.0)))
    c2.image(st.session_state.en_img, width=300)
    c2.metric("ENEMY HP", st.session_state.cpu_hp)
    c2.progress(max(0,min(st.session_state.cpu_hp/300,1.0)))
    c2.write("---")
    if 'enemy_last_card' in st.session_state:
        encard = st.session_state.enemy_last_card
        c2.write("📢 **敵のターン！**")
        c2.image(encard["画像URL"], width=250, caption=f"使用カード: {encard['カード名']}")

        # ダメージや効果の簡易説明
        c2.caption(f"効果: {encard['type']} ({encard['最小ダメ']}～{encard['最大ダメ']})")
    st.divider()

    # 手札（ランダムに選ばれた3枚）を表示
    st.write("### あなたの手札（ランダムに選出）")
    cols = st.columns(3)
    for i, card in enumerate(st.session_state.hand):
        with cols[i]:
            st.image(card["画像URL"], use_container_width=True)
            st.write(f"**{card['カード名']}** - ダメージ: {card['最小ダメ']} ~ {card['最大ダメ']}")
            if st.button(f"使う", key=f"play_{i}", use_container_width=True):
                card_type = card.get("type", "攻撃")
                log = []
                
                defense=0
                # 1. プレイヤーの行動フェーズ
                if card_type == "攻撃":
                    base_dmg = random.randint(int(float(card["最小ダメ"])), int(float(card["最大ダメ"])))
                    total_dmg = int(base_dmg * st.session_state.buff_multiplier)
                    st.session_state.cpu_hp -= total_dmg
                    log.append(f"💥 {card['カード名']}！ 敵に {total_dmg} ダメージ！")
                    st.session_state.buff_multiplier = 1.0 # バフ消費
                    st.session_state.debuff_multiplier = 1.0 # デバフ消費

                elif card_type == "回復":
                    heal = random.randint(int(float(card["最小ダメ"])), int(float(card["最大ダメ"])))
                    st.session_state.player_hp += heal
                    log.append(f"💖 {card['カード名']}！ HPが {heal} 回復した！")

                elif card_type == "防御":
                    defense = random.randint(int(float(card["最小ダメ"])), int(float(card["最大ダメ"])))
                    st.session_state.defense_flag = True
                    log.append(f"🛡️ {card['カード名']}！ 次のダメージを半減する！")

                elif card_type == "バフ":
                    buff=random.randint(int(float(card["最小ダメ"])), int(float(card["最大ダメ"])))
                    st.session_state.buff_multiplier = buff
                    log.append(f"🔥 {card['カード名']}！ 次の攻撃力が{buff}倍になる！")

                elif card_type == "デバフ":
                    debuff=random.randint(int(float(card["最小ダメ"])), int(float(card["最大ダメ"])))
                    st.session_state.debuff_multiplier = debuff
                    log.append(f"❄️ {card['カード名']}！ 敵の攻撃力が{debuff}倍になる！")
                elif card_type == "状態異常":
                    st.session_state.poison_turn = 3 # 3ターンの毒
                    st.session_state.poison = random.randint(int(float(card["最小ダメ"])), int(float(card["最大ダメ"])))
                    log.append(f"🧪 {card['カード名']}！ 敵を毒状態にした！")
                # 2. 敵の行動フェーズ（プレイヤーが勝っていなければ）
                if st.session_state.cpu_hp > 0:
                    enemy_card = random.choice(st.session_state.en_full_deck)
                    st.session_state.enemy_last_card = enemy_card
                    e_type = enemy_card.get("type", "攻撃")
                    if e_type=="攻撃":
                        enemy_dmg = random.randint(int(float(enemy_card["最小ダメ"])), int(float(enemy_card["最大ダメ"])))
                        enemy_dmg = int(enemy_dmg * st.session_state.debuff_multiplier)
                        # 防御判定
                        if st.session_state.defense_flag:
                            enemy_dmg = enemy_dmg-defense
                            if enemy_dmg < 0: enemy_dmg = 0
                            st.session_state.defense_flag = False # 防御消費
                    
                        st.session_state.player_hp -= enemy_dmg
                        log.append(f"👾 敵の攻撃！ {enemy_dmg} ダメージを受けた！")

                    elif e_type=="回復":
                        e_heal = random.randint(int(float(enemy_card["最小ダメ"])), int(float(enemy_card["最大ダメ"])))
                        st.session_state.cpu_hp += e_heal
                        log.append(f"💖 敵の回復！ HPが {e_heal} 回復した！")

                # 3. 継続ダメージ処理（毒など）
                if st.session_state.poison_turn > 0:
                    st.session_state.cpu_hp -= st.session_state.poison
                    st.session_state.poison_turn -= 1
                    log.append(f"状態異常ダメージ！ 敵のHPが {st.session_state.poison} 減った（残り {st.session_state.poison_turn} ターン）")

                st.session_state.battle_log = " / ".join(log)
                # 次のターン用に新しい3枚をドロー
                st.session_state.hand = random.sample(st.session_state.full_deck, 3)
                
                if st.session_state.cpu_hp <= 0 or st.session_state.player_hp <= 0:
                    st.session_state.page = "RESULT"
                st.rerun()

# 5. 結果画面
elif st.session_state.page == "RESULT":
    if st.session_state.player_hp>0 and st.session_state.cpu_hp<=0:
        st.balloons(); st.success("WIN!")
    elif st.session_state.player_hp<=0:
        st.error("LOSE...")
    if st.button("HOME"):
        st.session_state.page = "HOME"; st.rerun()