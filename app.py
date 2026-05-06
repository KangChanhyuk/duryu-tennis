import streamlit as st
import pandas as pd
import random
import itertools
import json
import os
from datetime import datetime

# =========================================================
# 기본 설정
# =========================================================
st.set_page_config(layout="wide", page_title="두류 테니스", page_icon="🎾")

# =========================================================
# UI (문법 오류 없는 안정 버전)
# =========================================================
st.markdown("""
<style>
body {background: linear-gradient(135deg,#eef9ff,#f4fff9);}
.title {text-align:center;font-size:3rem;font-weight:900;color:#156348;}
.card {background:white;padding:14px;border-radius:14px;margin-bottom:10px;
box-shadow:0 6px 18px rgba(0,0,0,0.08);}
.match {display:flex;justify-content:space-between;align-items:center;
background:white;padding:10px;border-radius:10px;margin-bottom:6px;}
.vs {font-weight:900;color:#ff4d6d;}
</style>
""", unsafe_allow_html=True)

# =========================================================
# 파일
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
    with open(SAVE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_all(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================================================
# 세션
# =========================================================
if "groups" not in st.session_state:
    st.session_state.groups = {}
if "schedule" not in st.session_state:
    st.session_state.schedule = {}
if "scores" not in st.session_state:
    st.session_state.scores = {}

# =========================================================
# KDK
# =========================================================
def make_kdk(players):
    pairs = list(itertools.combinations(players, 2))
    random.shuffle(pairs)

    rounds = []
    used_pairs = set()

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

                if (team1,team2) not in used_pairs:
                    round_matches.append([list(team1), list(team2)])
                    used_pairs.add((team1,team2))
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
    groups = {}
    g = 1
    for i in range(0,len(players),size):
        groups[f"G{g}"] = players[i:i+size]
        g += 1
    return groups

# =========================================================
# 매트릭스
# =========================================================
def show_matrix(group):
    players = st.session_state.groups[group]
    mat = pd.DataFrame("", index=players, columns=players)

    for (g,r,m), (s1,s2) in st.session_state.scores.items():
        if g != group:
            continue

        t1,t2 = st.session_state.schedule[g][r][m]

        for p1 in t1:
            for p2 in t2:
                mat.loc[p1,p2] = f"{s1}:{s2}"
                mat.loc[p2,p1] = f"{s2}:{s1}"

    st.dataframe(mat, use_container_width=True)

# =========================================================
# 메뉴
# =========================================================
menu = st.sidebar.radio("메뉴",[
    "🏆 랭킹",
    "📅 대진 생성",
    "📊 점수 입력",
    "📊 매트릭스",
    "💾 저장/불러오기"
])

# =========================================================
# 랭킹
# =========================================================
if menu == "🏆 랭킹":
    st.markdown("<div class='title'>DU-RYU TENNIS</div>", unsafe_allow_html=True)

    df = load_rank()

    if df.empty:
        st.info("데이터 없음")
    else:
        df = df.sort_values("포인트", ascending=False)

        for i,row in df.iterrows():
            st.markdown(f"""
            <div class='card'>
            🏆 {i+1}위 <b>{row['이름']}</b><br>
            {row['포인트']}점 | 승:{row['승']} 패:{row['패']} | 득실:{row['득실']}
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# 대진 생성
# =========================================================
elif menu == "📅 대진 생성":
    st.markdown("<div class='title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)

    names = st.text_area("선수 입력 (줄바꿈)").split("\n")
    size = st.number_input("그룹 인원",4,12,4)
    mode = st.selectbox("경기 방식",["복식","단식"])

    if st.button("대진 생성"):
        players = [n.strip() for n in names if n.strip()]

        groups = make_groups(players,size)
        st.session_state.groups = groups

        schedule = {}
        for g,plist in groups.items():
            if mode == "복식":
                schedule[g] = make_kdk(plist)
            else:
                schedule[g] = make_single(plist)

        st.session_state.schedule = schedule

    # 출력
    for g, rounds in st.session_state.schedule.items():
        st.subheader(g)
        for r_idx, rd in enumerate(rounds):
            st.write(f"라운드 {r_idx+1}")
            for m in rd:
                st.markdown(
                    f"<div class='match'>{m[0]} <span class='vs'>VS</span> {m[1]}</div>",
                    unsafe_allow_html=True
                )

# =========================================================
# 점수 입력 + 우승 표시
# =========================================================
elif menu == "📊 점수 입력":
    for g, rounds in st.session_state.schedule.items():
        st.subheader(g)

        stats = {}

        for r_idx, rd in enumerate(rounds):
            for m_idx, m in enumerate(rd):
                t1,t2 = m

                c1,c2 = st.columns(2)
                with c1:
                    s1 = st.number_input(f"{t1}", key=f"{g}{r_idx}{m_idx}1")
                with c2:
                    s2 = st.number_input(f"{t2}", key=f"{g}{r_idx}{m_idx}2")

                st.session_state.scores[(g,r_idx,m_idx)] = (s1,s2)

                for team,score,opp in [(t1,s1,s2),(t2,s2,s1)]:
                    for p in team:
                        stats.setdefault(p,{"win":0,"diff":0})
                        if score > opp:
                            stats[p]["win"] += 1
                        stats[p]["diff"] += (score - opp)

        ranking = sorted(stats.items(), key=lambda x:(x[1]["win"],x[1]["diff"]), reverse=True)

        if ranking:
            st.success(f"🏆 우승: {ranking[0][0]}")
        if len(ranking) > 1:
            st.info(f"🥈 준우승: {ranking[1][0]}")

# =========================================================
# 매트릭스
# =========================================================
elif menu == "📊 매트릭스":
    for g in st.session_state.groups:
        st.subheader(g)
        show_matrix(g)

# =========================================================
# 저장/불러오기
# =========================================================
elif menu == "💾 저장/불러오기":
    name = st.text_input("대회명")

    if st.button("저장"):
        data = load_save()
        data["tournaments"].append({
            "name": name,
            "groups": st.session_state.groups,
            "schedule": st.session_state.schedule,
            "scores": st.session_state.scores,
            "date": now()
        })
        save_all(data)
        st.success("저장 완료")

    data = load_save()
    for i,t in enumerate(data["tournaments"]):
        col1,col2 = st.columns([3,1])
        col1.write(f"{t['name']} ({t['date']})")
        if col2.button("불러오기", key=f"load_{i}"):
            st.session_state.groups = t["groups"]
            st.session_state.schedule = t["schedule"]
            st.session_state.scores = t["scores"]
            st.success("불러오기 완료")
