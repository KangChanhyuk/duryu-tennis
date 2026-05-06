import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# =============================
# 페이지 설정 및 스타일
# =============================
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    .team-card { border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; }
    .match-bg-1 { background-color: #f1f8e9; border-left: 8px solid #4CAF50; }
    .match-bg-2 { background-color: #e3f2fd; border-left: 8px solid #2196F3; }
    .vs-text { font-size: 1.2rem; font-weight: bold; color: #E53935; text-align: center; line-height: 60px; }
    th, td { text-align: center !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 한울방식 KDK 대진표 데이터 (이미지 학습 결과)
# =============================
# A:10, B:11, C:12로 매핑됨
HANUL_DATA = {
    "3": { # 1인 3게임 기준
        4: ["14:23", "13:24", "12:34"],
        8: ["12:34", "56:78", "18:27", "36:45", "14:58", "23:67"],
        12: ["12:34", "56:78", "910:1112", "13:57", "24:68", "911:1012", "48:912", "67:1011", "1112:23"]
    },
    "4": { # 1인 4게임 기준
        5: ["12:34", "13:25", "14:35", "15:24", "23:45"],
        6: ["13:24", "15:46", "23:56", "14:35", "26:34", "16:25"],
        7: ["12:34", "56:17", "23:57", "14:67", "35:24", "16:25", "46:37"],
        8: ["12:34", "56:78", "13:57", "24:68", "15:26", "37:48", "16:38", "25:47"],
        9: ["12:34", "56:78", "19:57", "23:68", "49:38", "15:26", "36:45", "17:89", "24:79"],
        10: ["12:35", "67:810", "23:46", "78:19", "34:57", "89:210", "45:68", "13:910", "56:79", "110:24"],
        11: ["12:35", "67:810", "49:111", "23:68", "45:710", "911:26", "13:711", "48:59", "110:28", "47:611", "39:510"]
    }
}

# =============================
# 상태 관리 및 유틸리티
# =============================
if "schedule" not in st.session_state: st.session_state.schedule = {}
if "scores" not in st.session_state: st.session_state.scores = {}
if "groups" not in st.session_state: st.session_state.groups = {}
if "modes" not in st.session_state: st.session_state.modes = {}

def get_team_display(team_list):
    return " & ".join(team_list)

def parse_hanul_string(s):
    """한울 데이터 문자열을 인덱스 리스트로 변환 (10, 11, 12 처리)"""
    res = []
    i = 0
    while i < len(s):
        if s[i:i+2] in ["10", "11", "12"]:
            res.append(int(s[i:i+2]) - 1)
            i += 2
        else:
            res.append(int(s[i]) - 1)
            i += 1
    return res

# =============================
# 메인 로직: 대진 생성
# =============================
def generate_schedule(group_name, players, mode, games_per_person):
    if mode == "KDK":
        key = str(games_per_person)
        n = len(players)
        if key in HANUL_DATA and n in HANUL_DATA[key]:
            shuffled_players = random.sample(players, n)
            rounds = []
            for match_str in HANUL_DATA[key][n]:
                t1_idx_s, t2_idx_s = match_str.split(":")
                t1 = [shuffled_players[i] for i in parse_hanul_string(t1_idx_s)]
                t2 = [shuffled_players[i] for i in parse_hanul_string(t2_idx_s)]
                rounds.append([[t1, t2]])
            return rounds
    # 고정페어 및 기타 로직 (단순 라운드로빈 예시)
    elif mode == "고정페어":
        pairs = [players[i:i+2] for i in range(0, len(players), 2)]
        matches = []
        for i in range(len(pairs)):
            for j in range(i+1, len(pairs)):
                matches.append([pairs[i], pairs[j]])
        random.shuffle(matches)
        return [[m] for m in matches]
    return []

# =============================
# 화면 구성
# =============================
st.sidebar.title("🎾 메뉴")
menu = st.sidebar.radio("이동", ["📅 대진표 및 입력", "⚙️ 관리자 설정"])

if menu == "📅 대진표 및 입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    if not st.session_state.schedule:
        st.info("관리자 설정에서 대진표를 먼저 생성해주세요.")
    else:
        for gn, rounds in st.session_state.schedule.items():
            st.subheader(f"📍 Group {gn} ({st.session_state.modes[gn]})")
            
            # 매트릭스 표시 (고정페어 시 페어 이름 표시)
            mode = st.session_state.modes[gn]
            if mode == "고정페어":
                entities = [get_team_display(st.session_state.groups[gn][i:i+2]) 
                            for i in range(0, len(st.session_state.groups[gn]), 2)]
            else:
                entities = st.session_state.groups[gn]
            
            st.write("**[상대 전적 매트릭스]**")
            df_matrix = pd.DataFrame("", index=entities, columns=entities)
            st.dataframe(df_matrix, use_container_width=True)

            # 경기 입력
            for ri, rd in enumerate(rounds):
                for mi, match in enumerate(rd):
                    c1, cv, c2 = st.columns([4, 1, 4])
                    with c1: st.markdown(f"<div class='team-card match-bg-1'>{get_team_display(match[0])}</div>", unsafe_allow_html=True)
                    with cv: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                    with c2: st.markdown(f"<div class='team-card match-bg-2'>{get_team_display(match[1])}</div>", unsafe_allow_html=True)

elif menu == "⚙️ 관리자 설정":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    with st.expander("신규 대회 생성", expanded=True):
        raw_names = st.text_area("참가자 명단 (쉼표 구분)", "강호동, 유재석, 이수근, 은지원, 김종민, 하하, 노홍철, 정준하")
        col1, col2 = st.columns(2)
        with col1:
            mode = st.selectbox("경기 방식", ["KDK", "고정페어", "단식"])
        with col2:
            games = st.selectbox("1인당 경기 수", [3, 4])
            
        if st.button("대진표 생성 및 초기화", type="primary"):
            players = [p.strip() for p in raw_names.split(",") if p.strip()]
            st.session_state.groups["A"] = players
            st.session_state.modes["A"] = mode
            st.session_state.schedule["A"] = generate_schedule("A", players, mode, games)
            st.success("대진표가 생성되었습니다!")
            st.rerun()
