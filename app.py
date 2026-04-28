import streamlit as st
import random

# --- 設定と初期化 ---
st.set_page_config(page_title="Card Battle with Images", layout="centered")
st.title("🃏 画像付き！カードバトル")

# カードデータの定義（画像URLと効果）
CARD_DATA = {
    "攻撃": {
        "image": "https://raw.githubusercontent.com/google/fonts/main/ofl/notoemoji/img/2694.png", # 剣の画像
        "desc": "敵にダメージを与える",
        "color": "red"
    },
    "回復": {
        "image": "https://raw.githubusercontent.com/google/fonts/main/ofl/notoemoji/img/1f496.png", # ハートの画像
        "desc": "自分のHPを回復する",
        "color": "green"
    },
    "必殺": {
        "image": "https://raw.githubusercontent.com/google/fonts/main/ofl/notoemoji/img/1f525.png", # 炎の画像
        "desc": "大ダメージを与える",
        "color": "orange"
    }
}

if 'player_hp' not in st.session_state:
    st.session_state.player_hp = 50
    st.session_state.cpu_hp = 50
    st.session_state.log = "カードを選んでバトル開始！"

# --- ゲームロジック ---
def play_turn(action):
    if st.session_state.player_hp <= 0 or st.session_state.cpu_hp <= 0:
        return

    p_dmg = 0
    if action == "攻撃":
        p_dmg = random.randint(8, 12)
    elif action == "必殺":
        p_dmg = random.randint(15, 25)
    elif action == "回復":
        st.session_state.player_hp += 10
    
    st.session_state.cpu_hp -= p_dmg
    
    # CPUの簡易攻撃
    c_dmg = random.randint(5, 15)
    st.session_state.player_hp -= c_dmg
    
    st.session_state.log = f"あなたの行動: {action} ({p_dmg}ダメ) / 敵の攻撃: ({c_dmg}ダメ)"

# --- 画面表示 ---
# ステータス
st.progress(max(0, min(st.session_state.player_hp / 100, 1.0)), text=f"あなたのHP: {st.session_state.player_hp}")
st.progress(max(0, min(st.session_state.cpu_hp / 100, 1.0)), text=f"敵のHP: {st.session_state.cpu_hp}")

st.write("### あなたの手札")
cols = st.columns(3)

# カードをループで表示
for i, (name, info) in enumerate(CARD_DATA.items()):
    with cols[i]:
        # 画像を表示
        st.image(info["image"], use_container_width=True)
        st.write(f"**{name}**")
        st.caption(info["desc"])
        # 画像の下に選択ボタン
        if st.button(f"{name}を使う", key=f"btn_{name}", use_container_width=True):
            play_turn(name)
            st.rerun()

st.divider()
st.info(st.session_state.log)

# リセット
if st.button("ゲームリセット"):
    for key in st.session_state.keys():
        del st.session_state[key]
    st.rerun()