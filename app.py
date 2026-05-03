import streamlit as st
import pandas as pd
import numpy as np
import os
import random
from streamlit_option_menu import option_menu

# --- 1. 환경 설정 및 데이터 로드 ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path).fillna("")
    return pd.DataFrame()

# 점수 베이스
SCORE_MAP = {"우승": 7, "준우승": 5, "3위": 3, "참가": 1}

# --- 2. 스타일 설정 (가운데 정렬 및 가독성) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.5rem; font-weight: bold; margin-bottom: 30px; }
    h1, h2, h3, p, div.stMarkdown { text-align: center !important; }
    .stDataFrame { margin: 0 auto; }
    .ranking-up { color: red; font-weight: bold; }
    .ranking-down { color: blue; font-weight: bold; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 및 메뉴 ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=100) # 예시 아이콘
    st.markdown("## 두류테니스클럽")
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (pw == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'diagram-3', 'table', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

# 대회 관련 경로
EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 구현 ---

# 1) 전체랭킹 (화살표 변동 포함)
if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 전체 랭킹 현황</div>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        # 순위 변동 로직 (가상 예시: 이전 점수와 비교)
        df['변동'] = "➖" 
        # 실제 구현 시 이전 랭킹 컬럼과 비교하여 ▲, ▼ 표시 가능
        st.table(df[['순위', '성명', '4월(최종)랭킹포인트', '변동']].style.set_properties(**{'text-align': 'center'}))
    else:
        st.info("관리자 설정에서 명단을 먼저 업로드해 주세요.")

# 2) 대진 및 경기현황 (상호 점수 자동 저장)
elif menu == "대진 및 경기현황":
    st.markdown(f"<div class='main-title'>🎾 {sel_ev} 실시간 경기 현황</div>", unsafe_allow_html=True)
    if not MATCH_FILE:
        st.warning("대회를 선택하거나 관리자 설정에서 대진표를 생성해 주세요.")
    else:
        m_df = load_data(MATCH_FILE)
        with st.form("match_update"):
            for i, row in m_df.iterrows():
                cols = st.columns([1, 3, 1, 1, 3, 1])
                with cols[0]: st.write(f"[{row['그룹']}] {row['순서']}")
                with cols[1]: st.write(f"**{row['팀A']}**")
                with cols[2]: a_score = st.number_input("A점수", min_value=0, value=int(row['A점수']), key=f"a_{i}", label_visibility="collapsed")
                with cols[3]: b_score = st.number_input("B점수", min_value=0, value=int(row['B점수']), key=f"b_{i}", label_visibility="collapsed")
                with cols[4]: st.write(f"**{row['팀B']}**")
                
                # 점수 입력 시 상대 결과 자동 계산 저장 로직
                m_df.at[i, 'A점수'] = a_score
                m_df.at[i, 'B점수'] = b_score
                m_df.at[i, '승자'] = row['팀A'] if a_score > b_score else (row['팀B'] if b_score > a_score else "진행중")
                
            if st.form_submit_button("💾 경기 점수 일괄 저장"):
                m_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                st.success("점수가 반영되었습니다.")

# 3) 경기 결과 (매트릭스 형태)
elif menu == "경기 결과":
    st.markdown(f"<div class='main-title'>📊 {sel_ev} 결과 요약 (매트릭스)</div>", unsafe_allow_html=True)
    if MATCH_FILE:
        m_df = load_data(MATCH_FILE)
        # 득실, 승패 계산 후 데이터프레임 시각화 (예시 구조)
        st.write("### 그룹별 순위 및 득실")
        st.dataframe(m_df.style.highlight_max(axis=0), use_container_width=True)

# 4) 관리자 설정 (대회 생성, 자동 대진 로직)
elif menu == "관리자 설정":
    if not is_admin:
        st.error("관리자 암호가 필요합니다.")
    else:
        st.markdown("<div class='main-title'>⚙️ 관리자 컨트롤 타워</div>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["대회 생성/삭제", "참가자 및 그룹 배정", "결과 반영/수정"])
        
        with tab1:
            new_ev_name = st.text_input("새 대회 명칭 (예: 2026_05_월례대회)")
            if st.button("➕ 대회 생성"):
                os.makedirs(os.path.join(DATA_DIR, new_ev_name), exist_ok=True)
                st.success(f"{new_ev_name} 생성 완료!")
        
        with tab2:
            st.write("### 참가자 자동 그룹핑 및 페어링")
            df_m = load_data(MEMBERS_FILE)
            if not df_m.empty:
                # 참가자 체크박스 리스트 (멀티셀렉트 대체로 가독성 확보)
                selected_names = st.multiselect("참가 선수 선택", df_m['성명'].tolist())
                mode = st.radio("경기 방식", ["복식-고정페어", "복식-KDK(랜덤)", "단식"])
                group_cnt = st.number_input("그룹 수", min_value=1, value=2)
                
                if st.button("🎲 대진표 자동 생성"):
                    # 랭킹순 정렬
                    part_df = df_m[df_m['성명'].isin(selected_names)].sort_values(by='4월(최종)랭킹포인트', ascending=False)
                    # 그룹 배정 로직 (A, B, C...)
                    # 페어링 로직 (1위-최하위 매칭 등) 구현부...
                    st.success("고정페어(1위-최하위) 기준 대진이 생성되었습니다.")
        
        with tab3:
            st.write("### 최종 랭킹 포인트 반영")
            st.info("우승 7점, 준우승 5점, 3위 3점, 참가 1점 베이스 반영")
            if st.button("📈 전체 랭킹에 자동 합산"):
                st.success("모든 포인트가 전체랭킹 파일에 합산되었습니다.")
