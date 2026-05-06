import streamlit as st
import pandas as pd
import random
import os
import json
from datetime import datetime

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="두류 테니스 랭킹",
    page_icon="🎾"
)

# =========================================================
# 기본 스타일 (간소 + 안정화)
# =========================================================
st.markdown("""
<style>
body {background: #eef9ff;}
.main-title {
    font-size: 3rem;
    text-align: center;
    font-weight: 800;
    color: #156348;
}
.sub-title {
    text-align: center;
    color: #5d8f7f;
    margin-bottom: 20px;
}
.card {
    background: white;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 10px;
    box-shadow: 0 5px 15px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 파일
# =========================================================
RANK_FILE = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"

# =========================================================
# 기본 데이터
# =========================================================
def default_rank_df():
    return pd.DataFrame(columns=["이름", "포인트", "승", "패", "득실"])

def load_rank():
    if not os.path.exists(RANK_FILE):
        return default_rank_df()
    return pd.read_csv(RANK_FILE)

def save_rank(df):
    df.to_csv(RANK_FILE, index=False)

# =========================================================
# 세션
# =========================================================
if "players" not in st.session_state:
    st.session_state.players = []
if "matches" not in st.session_state:
    st.session_state.matches = []
if "scores" not in st.session_state:
    st.session_state.scores = {}

# =========================================================
# 메뉴
# =========================================================
menu = st.sidebar.radio(
    "메뉴",
    ["🏆 랭킹보드", "📅 대진표 생성", "📊 점수 입력", "⚙️ 관리자"]
)

# =========================================================
# 1. 랭킹보드
# =========================================================
if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>RANKING</div>", unsafe_allow_html=True)

    df = load_rank()

    if df.empty:
        st.info("선수가 없습니다.")
    else:
        df = df.sort_values("포인트", ascending=False)

        for i, row in df.iterrows():
            st.markdown(f"""
            <div class='card'>
                <b>{i+1}위</b> {row['이름']} | {row['포인트']}점
                <br>승:{row['승']} 패:{row['패']} 득실:{row['득실']}
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# 2. 대진표 생성
# =========================================================
elif menu == "📅 대진표 생성":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)

    names = st.text_area("선수 입력 (줄바꿈)").split("\n")

    if st.button("대진 생성"):
        players = [n.strip() for n in names if n.strip()]
        random.shuffle(players)

        matches = []
        for i in range(0, len(players), 2):
            if i+1 < len(players):
                matches.append((players[i], players[i+1]))

        st.session_state.players = players
        st.session_state.matches = matches

    for i, m in enumerate(st.session_state.matches):
        st.write(f"{i+1}경기: {m[0]} vs {m[1]}")

# =========================================================
# 3. 점수 입력
# =========================================================
elif menu == "📊 점수 입력":
    st.markdown("<div class='main-title'>SCORE INPUT</div>", unsafe_allow_html=True)

    for i, m in enumerate(st.session_state.matches):
        col1, col2 = st.columns(2)

        with col1:
            s1 = st.number_input(f"{m[0]}", key=f"s1_{i}")
        with col2:
            s2 = st.number_input(f"{m[1]}", key=f"s2_{i}")

        st.session_state.scores[i] = (s1, s2)

    if st.button("결과 저장"):
        df = load_rank()

        for i, (p1, p2) in enumerate(st.session_state.matches):
            s1, s2 = st.session_state.scores.get(i, (0, 0))

            for p in [p1, p2]:
                if p not in df["이름"].values:
                    df.loc[len(df)] = [p, 0, 0, 0, 0]

            idx1 = df[df["이름"] == p1].index[0]
            idx2 = df[df["이름"] == p2].index[0]

            if s1 > s2:
                df.at[idx1, "승"] += 1
                df.at[idx2, "패"] += 1
                df.at[idx1, "포인트"] += 10
            elif s2 > s1:
                df.at[idx2, "승"] += 1
                df.at[idx1, "패"] += 1
                df.at[idx2, "포인트"] += 10

            df.at[idx1, "득실"] += (s1 - s2)
            df.at[idx2, "득실"] += (s2 - s1)

        save_rank(df)
        st.success("저장 완료!")

# =========================================================
# 4. 관리자
# =========================================================
elif menu == "⚙️ 관리자":
    st.markdown("<div class='main-title'>ADMIN</div>", unsafe_allow_html=True)

    if st.button("데이터 초기화"):
        if os.path.exists(RANK_FILE):
            os.remove(RANK_FILE)
        st.success("초기화 완료")
