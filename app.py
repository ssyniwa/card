import streamlit as st
import random

# --- 設定と初期化 ---
st.set_page_config(page_title="Card Battle Game", layout="centered")

# カードデータの定義（画像URLと効果）
CARD_DATA = {
    "火炎": {
        "image": "images/kyle.png",
        "dmg": (15, 25),
        "desc": "大ダメージを与える"
    },
    "斬撃": {
        "image": "images/elena.png",
        "dmg": (8, 12),
        "desc": "安定した攻撃"
    },
    "祈り": {
        "image": "images/dragon.png",
        "dmg": (0, 0),
        "desc": "HPを大幅に回復"
    }
}

if 'player_hp' not in st.session_state:
    st.session_state.player_hp = 50
    st.session_state.cpu_hp = 50
    st.session_state.game_over = False
    st.session_state.result_msg = ""

# --- 勝敗判定の関数 ---
def check_winner():
    if st.session_state.cpu_hp <= 0:
        st.session_state.cpu_hp = 0
        st.session_state.game_over = True
        st.session_state.result_msg = "WIN"
    elif st.session_state.player_hp <= 0:
        st.session_state.player_hp = 0
        st.session_state.game_over = True
        st.session_state.result_msg = "LOSE"

# --- 画面表示 ---
st.title("⚔️ 画像付き・最終決戦バトル")

# ステータス表示（体力ゲージ）
st.write(f"### YOUR HP: {st.session_state.player_hp}")
st.progress(max(0, min(st.session_state.player_hp / 100, 1.0)))
st.write(f"### ENEMY HP: {st.session_state.cpu_hp}")
st.progress(max(0, min(st.session_state.cpu_hp / 100, 1.0)))

st.divider()

# --- 画面の分岐処理 ---
if not st.session_state.game_over:
    # 【プレイ中】画像付きカードを表示
    st.write("### 手札を選択してください")
    cols = st.columns(3)

    for i, (name, info) in enumerate(CARD_DATA.items()):
        with cols[i]:
            # カード画像を表示
            st.image(info["image"], use_container_width=True)
            st.write(f"**{name}**")
            st.caption(info["desc"])
            
            # 選択ボタン
            if st.button(f"{name}を使う", key=f"btn_{name}", use_container_width=True):
                # プレイヤーの行動
                p_dmg = random.randint(*info['dmg'])
                if name == "祈り": 
                    st.session_state.player_hp += 20
                st.session_state.cpu_hp -= p_dmg
                
                # 敵の反撃（プレイヤーが勝っていなければ）
                if st.session_state.cpu_hp > 0:
                    st.session_state.player_hp -= random.randint(10, 18)
                
                check_winner()
                st.rerun()

else:
    # 【ゲーム終了時】結果を表示
    if st.session_state.result_msg == "WIN":
        st.balloons() # 勝利の風船
        st.success("# 🎉 勝利！あなたは伝説の勇者となりました！")
    else:
        st.snow()     # 敗北の雪
        st.error("# 💀 GAME OVER... 敗北してしまった。")
    
    if st.button("もう一度最初から遊ぶ", type="primary", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()