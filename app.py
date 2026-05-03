import streamlit as st
import pandas as pd
import numpy as np
import os
from streamlit_option_menu import option_menu

# --- 1. 데이터 로드 및 오류 방지 ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # 랭킹 정렬 오류(TypeError) 방지: 포인트 컬럼을 숫자로 강제 변환
        for col in df.columns:
            if '포인트' in col or '점수' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df.fillna("")
    return pd.DataFrame()

# --- 2. 페이지 레이아웃 및 스타일 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E3A8A; font-size: 2.2rem; font-weight: bold; margin-bottom: 20px; }
    h1, h2, h3, p { text-align: center !important; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    div.stDataFrame { margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바: 대회 선택 (모든 메뉴에서 공유) ---
with st.sidebar:
    st.markdown("### 🏆 대회 아카이브")
    # 폴더 목록을 읽어 최신순으로 정렬
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    
    # 세션 상태를 이용해 선택한 대회를 고정
    if 'selected_event' not in st.session_state:
        st.session_state.selected_event = all_ev[0] if all_ev else "선택 안함"
    
    sel_ev = st.selectbox("조회할 대회를 선택하세요", all_ev, index=all_ev.index(st.session_state.selected_event) if st.session_state.selected_event in all_ev else 0)
    st.session_state.selected_event = sel_ev
    
    st.markdown("---")
    pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (pw == "0502")

# 상단 메뉴 (image_0ae82c.png 디자인 반영)
menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'diagram-3', 'table', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

# 대회 관련 경로 설정
EV_PATH = os.path.join(DATA_DIR, st.session_state.selected_event) if st.session_state.selected_event != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 구현 ---

# (1) 전체랭킹
if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🏆 두류테니스클럽 전체 랭킹</div>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        # 포인트 기준 내림차순 정렬
        score_col = [c for c in df.columns if '포인트' in c][0]
        df_sorted = df.sort_values(by=score_col, ascending=False).reset_index(drop=True)
        df_sorted.insert(0, '순위', range(1, len(df_sorted) + 1))
        st.dataframe(df_sorted, use_container_width=True, hide_index=True)

# (2) 대진 및 경기현황 (그룹별 탭 분리)
elif menu == "대진 및 경기현황":
    st.markdown(f"<div class='main-title'>🎾 {st.session_state.selected_event} 경기 진행</div>", unsafe_allow_html=True)
    if MATCH_FILE:
        m_df = load_data(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"{g} 그룹" for g in groups])
        
        for idx, g in enumerate(groups):
            with tabs[idx]:
                g_df = m_df[m_df['그룹'] == g]
                for i, row in g_df.iterrows():
                    c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 1, 3])
                    with c1: st.info(f"순번 {row['순서']}")
                    with c2: st.markdown(f"**{row['팀A']}**")
                    # 관리자만 점수 수정 가능하도록 설정 가능
                    a_val = st.number_input("A", 0, 10, int(row['A점수']), key=f"a_{g}_{i}", label_visibility="collapsed", disabled=not is_admin)
                    with c4: b_val = st.number_input("B", 0, 10, int(row['B점수']), key=f"b_{g}_{i}", label_visibility="collapsed", disabled=not is_admin)
                    with c5: st.markdown(f"**{row['팀B']}**")
                    m_df.at[i, 'A점수'], m_df.at[i, 'B점수'] = a_val, b_val
        
        if is_admin and st.button("💾 경기 결과 저장"):
            m_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
            st.success("점수가 기록되었습니다.")

# (3) 경기 결과 (매트릭스 및 그룹 요약)
elif menu == "경기 결과":
    st.markdown(f"<div class='main-title'>📊 {st.session_state.selected_event} 최종 결과</div>", unsafe_allow_html=True)
    if MATCH_FILE:
        m_df = load_data(MATCH_FILE)
        # 그룹별 승패/득실 요약 로직 추가 가능
        st.table(m_df[['그룹', '순서', '팀A', 'A점수', 'B점수', '팀B']])

# (4) 관리자 설정 (대회 생성 및 포인트 합산)
elif menu == "관리자 설정":
    if not is_admin:
        st.error("관리자 암호를 입력해주세요.")
    else:
        st.markdown("<div class='main-title'>⚙️ 관리자 운영 도구</div>", unsafe_allow_html=True)
        # 대회 생성, 랭킹 기반 자동 분할 대진 생성 로직 (이전 코드 반영)
        st.info("여기서 새로운 대회를 생성하고 그룹을 자동 분할할 수 있습니다.")
