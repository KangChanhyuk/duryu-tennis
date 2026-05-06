import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

st.set_page_config(layout="wide", page_title="🎾 두류 테니스", page_icon="🎾")

# =============================
# 🎨 모바일 앱 스타일 UI
# =============================
st.markdown("""
<style>
body { background:#eaf7ef; }

.main-title {
    font-size:2.5rem;
    text-align:center;
    font-weight:900;
    color:#1b5e3c;
}

.card {
    background:white;
    padding:15px;
    border-radius:12px;
    box-shadow:0 4px 12px rgba(0,0,0,0.08);
    margin-bottom:10px;
}

/* 중앙정렬 */
th, td { text-align:center !important; }

/* 자기 자신 셀 */
.self { background:#dcdcdc !important; }

/* VS 정렬 */
.vs-box {
    display:flex;
    justify-content:space-between;
    align-items:center;
    font-weight:700;
    font-size:1.1rem;
}

/* 버튼 */
.stButton button {
    border-radius:10px;
    background:#2e7d55;
    color:white;
}
</style>
""", unsafe_allow_html=True)

# =============================
# 📁 파일
# =============================
RANK_FILE = "rank.csv"
HISTORY_FILE = "history.csv"
TOUR_FILE = "tournament.csv"

# =============================
# 📊 데이터 함수
# =============================
def load_rank():
    if not os.path.exists(RANK_FILE):
        return pd.DataFrame(columns=["이름","포인트","승","패","득실"])
    return pd.read_csv(RANK_FILE)

def save_rank(df):
    df.to_csv(RANK_FILE,index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame()
    return pd.read_csv(HISTORY_FILE)

def save_history(df):
    df.to_csv(HISTORY_FILE,index=False)

# =============================
# 🎯 그룹 배정 (스네이크)
# =============================
def snake(players, sizes):
    groups = {chr(65+i):[] for i in range(len(sizes))}
    d = 1
    while players:
        order = range(len(sizes)) if d==1 else reversed(range(len(sizes)))
        for i in order:
            if len(groups[chr(65+i)])<sizes[i]:
                groups[chr(65+i)].append(players.pop(0))
        d*=-1
    return groups

# =============================
# 🎾 고정페어
# =============================
def fixed_pairs(players):
    pairs=[]
    while len(players)>=2:
        pairs.append([players[0],players[-1]])
        players=players[1:-1]
    return pairs

# =============================
# 📅 라운드 생성
# =============================
def round_robin(teams):
    matches=[]
    for i in range(len(teams)):
        for j in range(i+1,len(teams)):
            matches.append([teams[i],teams[j]])
    random.shuffle(matches)

    rounds=[]
    while matches:
        used=set()
        rd=[]
        rest=[]
        for m in matches:
            p=set(m[0]+m[1])
            if not p & used:
                rd.append(m)
                used|=p
            else:
                rest.append(m)
        rounds.append(rd)
        matches=rest
    return rounds

# =============================
# 🎯 순위 묶기
# =============================
def rank_label(r):
    if r<=2: return "🥇 우승"
    elif r<=4: return "🥈 준우승"
    elif r<=6: return "🥉 3위"
    else: return f"{r}위"

# =============================
# 📺 경기 호출 화면
# =============================
def call_screen(schedule):
    st.markdown("<div class='main-title'>📺 경기 호출</div>",unsafe_allow_html=True)

    for g in schedule:
        st.markdown(f"### Group {g}")
        for ri,rd in enumerate(schedule[g]):
            for t1,t2 in rd:
                st.markdown(f"""
                <div class='card vs-box'>
                    <div>{' & '.join(t1)}</div>
                    <div>VS</div>
                    <div>{' & '.join(t2)}</div>
                </div>
                """,unsafe_allow_html=True)

# =============================
# 📊 그래프
# =============================
def draw_graph():
    df=load_rank()
    if df.empty: return
    st.line_chart(df.set_index("이름")["포인트"])

# =============================
# 🧠 상태
# =============================
if "groups" not in st.session_state:
    st.session_state.groups={}
    st.session_state.schedule={}
    st.session_state.scores={}

# =============================
# 📌 메뉴
# =============================
menu=st.sidebar.radio("메뉴",["🏆 랭킹","📅 대진","📊 결과","📺 호출","⚙️ 관리자"])

# =============================
# 🏆 랭킹
# =============================
if menu=="🏆 랭킹":
    st.markdown("<div class='main-title'>🏆 랭킹</div>",unsafe_allow_html=True)
    df=load_rank()
    st.dataframe(df, use_container_width=True)
    draw_graph()

# =============================
# 📅 대진
# =============================
elif menu=="📅 대진":
    st.markdown("<div class='main-title'>📅 대진표</div>",unsafe_allow_html=True)

    for g in st.session_state.schedule:
        st.markdown(f"## Group {g}")
        for ri,rd in enumerate(st.session_state.schedule[g]):
            st.markdown(f"### Round {ri+1}")
            for t1,t2 in rd:
                c1,c2,c3=st.columns([4,1,4])
                with c1: st.write(" & ".join(t1))
                with c2: st.write("VS")
                with c3: st.write(" & ".join(t2))

# =============================
# 📊 결과
# =============================
elif menu=="📊 결과":
    st.markdown("<div class='main-title'>📊 결과</div>",unsafe_allow_html=True)

    players=[]
    for g in st.session_state.groups:
        players+=st.session_state.groups[g]

    random.shuffle(players)

    rows=[]
    for i,p in enumerate(players):
        rows.append({
            "순위":rank_label(i+1),
            "이름":p
        })
    st.dataframe(pd.DataFrame(rows))

# =============================
# 📺 호출
# =============================
elif menu=="📺 호출":
    call_screen(st.session_state.schedule)

# =============================
# ⚙️ 관리자
# =============================
elif menu=="⚙️ 관리자":
    pwd=st.text_input("비밀번호",type="password")

    if pwd=="0502":
        st.subheader("대회 생성")

        players=st.text_area("참가자 (쉼표)").split(",")
        players=[p.strip() for p in players if p.strip()]

        group_n=st.number_input("그룹 수",1,4,1)

        if st.button("생성"):
            df=load_rank()
            rank_map=dict(zip(df["이름"],df["포인트"]))

            players.sort(key=lambda x:rank_map.get(x,0),reverse=True)

            sizes=[len(players)//group_n]*group_n
            groups=snake(players,sizes)

            st.session_state.groups=groups
            st.session_state.schedule={}

            for g in groups:
                p=groups[g]
                pairs=fixed_pairs(p.copy())
                st.session_state.schedule[g]=round_robin(pairs)

            st.success("대진 생성 완료")

        st.subheader("데이터 초기화")
        if st.button("전체 삭제"):
            if os.path.exists(RANK_FILE): os.remove(RANK_FILE)
            if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
            st.success("삭제 완료")
