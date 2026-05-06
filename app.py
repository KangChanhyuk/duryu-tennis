import streamlit as st
import pandas as pd
import random
import itertools
import json
import os
from datetime import datetime

st.set_page_config(layout="wide", page_title="두류 테니스", page_icon="🎾")

# =========================================================
# 🎨 고급 UI 복구
# =========================================================
st.markdown("""
<style>
body {
    background: linear-gradient(135deg,#eef9ff,#f4fff9);
}
.title {
    text-align:center;
    font-size:3.2rem;
    font-weight:900;
    color:#156348;
}
.card {
    background:white;
    border-radius:16px;
    padding:16px;
    margin-bottom:10px;
    box-shadow:0 8px 20px rgba(0,0,0,0.08);
}
.match {
    display:flex;
    justify-content:space-between;
    align-items:center;
    padding:14px;
    border-radius:14px;
    background:white;
    margin-bottom:8px;
}
.vs {
    font-weight:900;
    color:#ff4d6d;
}
.rank1 {color:#f4b400;}
.rank2 {color:#9aa6b2;}
.rank3 {color:#c78b4f;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 저장 파일
# =========================================================
RANK_FILE = "rank.csv"
SAVE_FILE = "tournament.json"

# =========================================================
# 유틸
# =========================================================
def now():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def load_rank():
    if not os.path.exists(RANK_FILE):
        return pd.DataFrame(columns=["이름","포인트","승","패","득실"])
    return pd.read_csv(RANK_FILE)

def save_rank(df):
    df.to_csv(RANK_FILE, index=False)

def load_save():
    if not os.path.exists(SAVE_FILE):
        return {"tournaments":[]}
    return json.load(open(SAVE_FILE, encoding="utf-8"))

def save_all(data):
    json.dump(data, open(SAVE_FILE,"w",encoding="utf-8"), ensure_ascii=False, indent=2)

# =========================================================
# 세션
# =========================================================
if "groups" not in st.session_state:
    st.session_state.groups = {}
if "schedule" not in st.session_state:
    st.session_state.schedule = {}
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "mode" not in st.session_state:
    st.session_state.mode = "복식"

# =========================================================
# 🧠 진짜 KDK (중복 최소화 알고리즘)
# =========================================================
def make_kdk(players):
    pairs = list(itertools.combinations(players, 2))
    random.shuffle(pairs)

    used = set()
    rounds = []

    for _ in range(len(players)):
        round_matches = []
        used_players = set()

        for p1, p2 in pairs:
            if p1 in used_players or p2 in used_players:
                continue

            for p3, p4 in pairs:
                if len({p1,p2,p3,p4}) < 4:
                    continue
                if p3 in used_players or p4 in used_players:
                    continue

                team1 = tuple(sorted([p1,p2]))
                team2 = tuple(sorted([p3,p4]))

                if (team1,team2) not in used:
                    round_matches.append([list(team1), list(team2)])
                    used.add((team1,team2))
                    used_players.update([p1,p2,p3,p4])
                    break

        if round_matches:
            rounds.append(round_matches)

    return rounds

# =========================================================
# 단식
# =========================================================
def make_single(players):
    random.shuffle(players)
    matches = []
    for i in range(0,len(players),2):
        if i+1 < len(players):
            matches.append([[players[i]],[players[i+1]]])
    return [matches]

# =========================================================
# 그룹
# =========================================================
def make_groups(players, size):
    random.shuffle(players)
    return {f"G{i+1}":players[i:i+size] for i in range(0,len(players),size)}

# =========================================================
# 📊 매트릭스
# =========================================================
def matrix(group):
    players = st.session_state.groups[group]
    mat = pd.DataFrame("", index=players, columns=players)

    for (g,r,m), (s1,s2) in st.session_state.scores.items():
        if g != group: continue
        t1,t2 = st.session_state.schedule[g][r][m]

        for p1 in t1:
            for p2 in t2:
                mat.loc[p1,p2] = f"{s1}:{s2}"
                mat.loc[p2,p1] = f"{s2}:{s1}"

    st.dataframe(mat)

# =========================================================
# 메뉴
# =========================================================
menu = st.sidebar.radio("메뉴",[
    "🏆 랭킹",
    "📅 대진 생성",
    "📊 점수 입력",
    "📊 매트릭스",
    "💾 저장"
])

# =========================================================
# 랭킹
# =========================================================
if menu=="🏆 랭킹":
    st.markdown("<div class='title'>DU-RYU TENNIS</div>", unsafe_allow_html=True)
    df = load_rank()

    if df.empty:
        st.info("데이터 없음")
    else:
        df = df.sort_values("포인트", ascending=False)

        for i,row in df.iterrows():
            cls = f"rank{i+1}" if i<3 else ""
            st.markdown(f"<div class='card {cls}'>🏆 {i+1}위 {row['이름']} ({row['포인트']}점)</div>", unsafe_allow_html=True)

# =========================================================
# 대진
# =========================================================
elif menu=="📅 대진 생성":
    st.markdown("<div class='title'>MATCH</div>", unsafe_allow_html=True)

    names = st.text_area("선수 입력").split("\n")
    size = st.number_input("그룹 인원",4,12,4)
    mode = st.selectbox("경기 방식",["복식","단식"])
    st.session_state.mode = mode

    if st.button("생성"):
        players = [n.strip() for n in names if n.strip()]
        groups = make_groups(players,size)
        st.session_state.groups = groups

        schedule = {}
        for g,plist in groups.items():
            if mode=="복식":
                schedule[g] = make_kdk(plist)
            else:
                schedule[g] = make_single(plist)

        st.session_state.schedule = schedule

    for g, rounds in st.session_state.schedule.items():
        st.subheader(g)
        for r_idx, rd in enumerate(rounds):
            st.write(f"라운드 {r_idx+1}")
            for m in rd:
                st.markdown(f"<div class='match'>{m[0]} <span class='vs'>VS</span> {m[1]}</div>", unsafe_allow_html=True)

# =========================================================
# 점수 입력 + 우승 계산
# =========================================================
elif menu=="📊 점수 입력":
    results = {}

    for g, rounds in st.session_state.schedule.items():
        st.subheader(g)

        stats = {}

        for r_idx, rd in enumerate(rounds):
            for m_idx, m in enumerate(rd):
                t1,t2 = m
                c1,c2 = st.columns(2)

                with c1:
                    s1 = st.number_input(str(t1), key=f"{g}{r_idx}{m_idx}1")
                with c2:
                    s2 = st.number_input(str(t2), key=f"{g}{r_idx}{m_idx}2")

                st.session_state.scores[(g,r_idx,m_idx)] = (s1,s2)

                for team,score,opp in [(t1,s1,s2),(t2,s2,s1)]:
                    for p in team:
                        stats.setdefault(p,{"win":0,"diff":0})
                        if score>opp:
                            stats[p]["win"]+=1
                        stats[p]["diff"]+=(score-opp)

        ranking = sorted(stats.items(), key=lambda x:(x[1]["win"],x[1]["diff"]), reverse=True)

        if ranking:
            st.success(f"🏆 우승: {ranking[0][0]}")
        if len(ranking)>1:
            st.info(f"🥈 준우승: {ranking[1][0]}")

# =========================================================
# 매트릭스
# =========================================================
elif menu=="📊 매트릭스":
    for g in st.session_state.groups:
        st.subheader(g)
        matrix(g)

# =========================================================
# 저장
# =========================================================
elif menu=="💾 저장":
    name = st.text_input("대회명")

    if st.button("저장"):
        data = load_save()
        data["tournaments"].append({
            "name":name,
            "groups":st.session_state.groups,
            "schedule":st.session_state.schedule,
            "scores":st.session_state.scores,
            "date":now()
        })
        save_all(data)
        st.success("저장 완료")
