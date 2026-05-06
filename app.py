import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# =============================
# 1. 페이지 설정 및 스타일
# =============================
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    .team-card { border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; font-weight: bold; }
    .match-bg-1 { background-color: #f1f8e9; border-left: 8px solid #4CAF50; }
    .match-bg-2 { background-color: #e3f2fd; border-left: 8px solid #2196F3; }
    .vs-text { font-size: 1.2rem; font-weight: bold; color: #E53935; text-align: center; line-height: 60px; }
    th, td { text-align: center !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 2. 한울방식 KDK 데이터 (image_e5bcba.jpg 기반)
# =============================
# A=10, B=11, C=12로 자동 변환 처리
HANUL_KDK_CONFIG = {
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
# 3. 데이터 및 유틸리티 함수
# =============================
if "schedule" not in st.session_state: st.session_state.schedule = {}
if "scores" not in st.session_state: st.session_state.scores = {}
if "groups" not in st.session_state: st.session_state.groups = {}
if "modes" not in st.session_state: st.session_state.modes = {}

def get_display_name(team):
    """팀 리스트를 '이름 & 이름' 형식으로 반환"""
    return " & ".join(team)

def parse_indices(s):
    """한울 데이터의 숫자 문자열을 실제 인덱스로 변환"""
    res = []
    i = 0
    while i < len(s):
        if s[i:i+2] in ["10", "11", "12"]:
            res.append(int(s[i:i+2]) - 1); i += 2
        else:
            res.append(int(s[i]) - 1); i += 1
    return res

# =============================
# 4. 대진표 생성 알고리즘
# =============================
def create_kdk_hanul(players, games):
    n = len(players)
    key = str(games)
    if key in HANUL_KDK_CONFIG and n in HANUL_KDK_CONFIG[key]:
        shuffled = random.sample(players, n)
        match_list = HANUL_KDK_CONFIG[key][n]
        rounds = []
        for ms in match_list:
            t1_s, t2_s = ms.split(":")
            t1 = [shuffled[i] for i in parse_indices(t1_s)]
            t2 = [shuffled[i] for i in parse_indices(t2_s)]
            rounds.append([[t1, t2]])
        return rounds
    return None

# =============================
# 5. 메인 UI 및 로직
# =============================
st.sidebar.title("🎾 시스템 메뉴")
page = st.sidebar.radio("이동", ["📅 경기 대진표", "⚙️ 대회 관리 설정"])

if page == "📅 경기 대진표":
    st.markdown("<div class='main-title'>DU-RYU TENNIS MATCHES</div>", unsafe_allow_html=True)
    
    if not st.session_state.schedule:
        st.warning("먼저 '대회 관리 설정'에서 대진표를 생성해 주세요.")
    else:
        for gn, rounds in st.session_state.schedule.items():
            mode = st.session_state.modes[gn]
            st.divider()
            st.subheader(f"🏆 Group {gn} 전적표 ({mode})")
            
            # 고정페어인 경우 상단에 페어로 이름 표시
            if mode == "고정페어":
                entities = [get_display_name(st.session_state.groups[gn][i:i+2]) 
                            for i in range(0, len(st.session_state.groups[gn]), 2)]
            else:
                entities = st.session_state.groups[gn]
            
            # 매트릭스 생성
            matrix = pd.DataFrame("", index=entities, columns=entities)
            st.dataframe(matrix, use_container_width=True)

            # 경기 입력 섹션
            st.write(f"**[{gn}조 경기 순서]**")
            for ri, rd in enumerate(rounds):
                for mi, match in enumerate(rd):
                    c1, cv, c2 = st.columns([4, 1, 4])
                    with c1: st.markdown(f"<div class='team-card match-bg-1'>{get_display_name(match[0])}</div>", unsafe_allow_html=True)
                    with cv: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                    with c2: st.markdown(f"<div class='team-card match-bg-2'>{get_display_name(match[1])}</div>", unsafe_allow_html=True)

elif page == "⚙️ 대회 관리 설정":
    st.markdown("<div class='main-title'>ADMIN CONTROL</div>", unsafe_allow_html=True)
    
    with st.form("create_tournament"):
        names = st.text_area("참가자 명단 (쉼표로 구분)", "홍길동, 임꺽정, 장길산, 이순신, 강감찬, 을지문덕")
        mode = st.selectbox("경기 방식", ["KDK", "고정페어"])
        game_cnt = st.selectbox("1인당 경기수 (KDK 한울방식 전용)", [3, 4])
        submit = st.form_submit_button("대진표 생성하기")
        
        if submit:
            p_list = [p.strip() for p in names.split(",") if p.strip()]
            st.session_state.groups["A"] = p_list
            st.session_state.modes["A"] = mode
            
            if mode == "KDK":
                result = create_kdk_hanul(p_list, game_cnt)
                if result: 
                    st.session_state.schedule["A"] = result
                    st.success("한울방식 KDK 대진표가 생성되었습니다!")
                else: 
                    st.error("해당 인원/경기수의 한울방식 데이터가 없습니다.")
            else:
                # 고정페어 단순 생성 로직
                pairs = [p_list[i:i+2] for i in range(0, len(p_list), 2)]
                st.session_state.schedule["A"] = [[[pairs[0], pairs[1]]]] # 예시용
                st.success("고정페어 대진이 생성되었습니다.")
            st.rerun()
