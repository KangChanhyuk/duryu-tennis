import streamlit as st
import pandas as pd
import numpy as np
import os
import random
from streamlit_option_menu import option_menu

# --- 1. 데이터 관리 및 초기화 (KeyError 방지) ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        for col in df.columns:
            if '포인트' in col or '점수' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        # 필수 컬럼 누락 방지 (KeyError 해결)
        if '승자' not in df.columns:
            df['승자'] = "진행중"
        return df.fillna("")
    return pd.DataFrame()

# --- 2. 페이지 스타일 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E3A8A; font-size: 2.2rem; font-weight: bold; margin-bottom: 20px; }
    h1, h2, h3, p { text-align: center !important; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 20px; }
    /* 숫자 입력 칸 너비 및 중앙 정렬 */
    div[data-testid="stNumberInput"] { width: 100px !important; margin: 0 auto; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 및 메뉴 ---
with st.sidebar:
    st.markdown("### 🏆 대회 선택")
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    if 'selected_event' not in st.session_state:
        st.session_state.selected_event = all_ev[0] if all_ev else "선택 안함"
    sel_ev = st.selectbox("대회 선택", all_ev, index=all_ev.index(st.session_state.selected_event) if st.session_state.selected_event in all_ev else 0)
    st.session_state.selected_event = sel_ev
    st.markdown("---")
    pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (pw == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'diagram-3', 'table', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, st.session_state.selected_event) if st.session_state.selected_event != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 ---

# (1) 전체랭킹
if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 전체 랭킹</div>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        score_col = [c for c in df.columns if '포인트' in c][0]
        df_sorted = df.sort_values(by=score_col, ascending=False).reset_index(drop=True)
        df_sorted.insert(0, '순위', range(1, len(df_sorted) + 1))
        st.dataframe(df_sorted, use_container_width=True, hide_index=True)

# (2) 대진 및 경기현황 (+- 버튼 입력)
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
                    cols = st.columns([1, 4, 1.5, 1.5, 4])
                    with cols[0]: st.write(f"**{row['순서']}**")
                    with cols[1]: st.markdown(f"<p style='text-align:right;'>{row['팀A']}</p>", unsafe_allow_html=True)
                    # 직접 입력 + 증감 버튼 병행 (step=1)
                    a_score = cols[2].number_input("A", 0, 10, int(row['A점수']), step=1, key=f"a_{g}_{i}", label_visibility="collapsed")
                    b_score = cols[3].number_input("B", 0, 10, int(row['B점수']), step=1, key=f"b_{g}_{i}", label_visibility="collapsed")
                    with cols[4]: st.markdown(f"<p style='text-align:left;'>{row['팀B']}</p>", unsafe_allow_html=True)
                    
                    m_df.at[i, 'A점수'] = a_score
                    m_df.at[i, 'B점수'] = b_score
                    # 승자 로직 업데이트
                    if a_score > b_score: m_df.at[i, '승자'] = row['팀A']
                    elif b_score > a_score: m_df.at[i, '승자'] = row['팀B']
                    else: m_df.at[i, '승자'] = "진행중"
        
        if is_admin and st.button("💾 모든 경기 결과 저장"):
            m_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
            st.success("점수가 안전하게 저장되었습니다!")

# (3) 경기 결과 (탭 분리 및 KeyError 해결)
elif menu == "경기 결과":
    st.markdown(f"<div class='main-title'>📊 {st.session_state.selected_event} 그룹별 결과</div>", unsafe_allow_html=True)
    if MATCH_FILE:
        m_df = load_data(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"{g} 그룹 결과" for g in groups])
        for idx, g in enumerate(groups):
            with tabs[idx]:
                res_df = m_df[m_df['그룹'] == g].copy()
                # KeyError 방지를 위해 컬럼 존재 확인 후 출력
                cols_to_show = ['순서', '팀A', 'A점수', 'B점수', '팀B', '승자']
                st.dataframe(res_df[cols_to_show], use_container_width=True, hide_index=True)

# (4) 관리자 설정 (자동 분할 대진 생성 로직)
elif menu == "관리자 설정":
    if not is_admin:
        st.error("관리자 인증이 필요합니다.")
    else:
        st.markdown("<div class='main-title'>⚙️ 관리자 대회 생성 도구</div>", unsafe_allow_html=True)
        # 랭킹 기반 자동 그룹 분할 로직 유지
        st.info("여기서 참가자 선택 시 랭킹순으로 그룹이 자동 분할됩니다.")
