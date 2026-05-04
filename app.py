import streamlit as st
import pandas as pd
import random
import os
import datetime

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"

# ----------------------
# 상태 초기화
# ----------------------
if "players_selected" not in st.session_state:
    st.session_state.players_selected = []

if "groups" not in st.session_state:
    st.session_state.groups = {}

if "pairs" not in st.session_state:
    st.session_state.pairs = {}

if "schedule" not in st.session_state:
    st.session_state.schedule = {}

if "scores" not in st.session_state:
    st.session_state.scores = {}

if "current_round" not in st.session_state:
    st.session_state.current_round = {}

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

# ----------------------
# 스타일
# ----------------------
st.markdown("""
<style>
h1,h2,h3 {text-align:center;}

.match {
    display:flex;
    justify-content:center;
    align-items:center;
    gap:20px;
    margin:20px 0;
}

.team {
    padding:16px 24px;
    border-radius:25px;
    background:#4CAF50;
    color:white;
    font-weight:bold;
    min-width:140px;
    text-align:center;
}

.team2 { background:#2196F3; }

.now {
    background:#FFD54F !important;
    color:black !important;
}

.badge {
    background:red;
    color:white;
    padding:3px 10px;
    border-radius:12px;
    font-size:12px;
}

.center-table td, .center-table th {
    text-align:center !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 유틸
# ----------------------
def clean_name(name):
    return str(name).strip().replace(" ","")

def team_name(team):
    return team[0] if len(team)==1 else f"{team[0]}&{team[1]}"

def load_rank():
    if os.path.exists(RANK_FILE):
        df = pd.read_csv(RANK_FILE)
        df["이름"] = df["이름"].apply(clean_name)
        return df
    return pd.DataFrame(columns=["이름","현재포인트","이전포인트"])

def save_rank(df):
    df.to_csv(RANK_FILE, index=False)

# ----------------------
# 🔥 랭킹 기반 그룹 배정
# ----------------------
def make_groups_by_rank(players, sizes):
    rank = load_rank()

    # 랭킹 정렬
    players_df = rank[rank["이름"].isin(players)]
    players_df = players_df.sort_values("현재포인트", ascending=False)

    sorted_players = players_df["이름"].tolist()

    groups = {g: [] for g in sizes}

    idx = []
    for g, s in sizes.items():
        idx += [g]*s

    for i, p in enumerate(sorted_players):
        if i < len(idx):
            groups[idx[i]].append(p)

    return groups

# ----------------------
# 페어
# ----------------------
def make_pairs(players, mode):
    if mode=="고정페어":
        return [(players[i],players[-1-i]) for i in range(len(players)//2)]
    if mode=="KDK":
        temp=players[:]
        random.shuffle(temp)
        return [(temp[i],temp[i+1]) for i in range(0,len(temp),2)]
    return [(p,) for p in players]

# ----------------------
# 매트릭스 (대각선)
# ----------------------
def draw_matrix(teams):
    names=[team_name(t) for t in teams]

    table="<table class='center-table' border=1 style='margin:auto'>"
    table+="<tr><td></td>"+"".join([f"<td>{n}</td>" for n in names])+"</tr>"

    for i,t1 in enumerate(teams):
        table+=f"<tr><td>{names[i]}</td>"
        for j,t2 in enumerate(teams):
            if i==j:
                table+="<td>\\</td>"  # 👉 대각선 표시
            else:
                key=(tuple(t1),tuple(t2))
                if key in st.session_state.scores:
                    s1,s2=st.session_state.scores[key]
                    table+=f"<td>{s1}:{s2}</td>"
                else:
                    table+="<td></td>"
        table+="</tr>"
    table+="</table>"

    st.markdown(table, unsafe_allow_html=True)

# ----------------------
# 메뉴
# ----------------------
menu = st.sidebar.radio("메뉴",
["두류랭킹","대진 및 경기","관리자"])

# ----------------------
# 랭킹
# ----------------------
if menu=="두류랭킹":
    st.title("🏆 두류랭킹")

    df = load_rank()

    if len(df):
        df["변동"]=df["현재포인트"]-df["이전포인트"]
        df=df.sort_values("현재포인트",ascending=False).reset_index(drop=True)
        df["순위"]=df.index+1

        df = df[["순위","이름","현재포인트","변동"]]

        st.dataframe(df, use_container_width=True, hide_index=True)

# ----------------------
# 대진
# ----------------------
elif menu=="대진 및 경기":
    st.title("🎾 대진")

    for g,teams in st.session_state.pairs.items():

        st.subheader(f"{g} 그룹")

        tab1, tab2 = st.tabs(["📊 매트릭스","🎮 경기"])

        with tab1:
            draw_matrix(teams)

# ----------------------
# 관리자
# ----------------------
elif menu=="관리자":

    if st.text_input("비밀번호", type="password")=="0502":
        st.session_state.is_admin=True

    if st.session_state.is_admin:

        raw = st.text_area("참가자 입력")

        if st.button("등록"):
            st.session_state.players_selected=[clean_name(p) for p in raw.split(",") if p.strip()]

        count = st.number_input("그룹 수",2,6,2)
        names=list("ABCDEF")[:count]

        sizes={}
        for g in names:
            sizes[g]=st.number_input(f"{g} 인원",1,20,4)

        if st.button("🔥 랭킹 기반 그룹 생성"):
            st.session_state.groups = make_groups_by_rank(st.session_state.players_selected, sizes)

        for g,players in st.session_state.groups.items():
            st.subheader(g)
            mode=st.selectbox("경기 방식",["단식","고정페어","KDK"],key=g)
            st.session_state.pairs[g]=make_pairs(players,mode)
