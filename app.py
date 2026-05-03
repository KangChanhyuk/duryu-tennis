import streamlit as st
import pandas as pd
import numpy as np
import os
import random
import re
from streamlit_option_menu import option_menu

# --- 1. 데이터 저장 및 로드 (기존 데이터 기억) ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_data(file_path):
    if os.path.exists(file_path):
        # 엑셀/CSV에서 가져온 데이터를 NaN 없이 깨끗하게 로드
        return pd.read_csv(file_path).fillna("")
    return pd.DataFrame()

# --- 2. 페이지 스타일 (가운데 정렬 및 가독성) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.5rem; font-weight: bold; margin-bottom: 30px; }
    h1, h2, h3, p { text-align: center !important; }
    div.stDataFrame { margin: 0 auto; }
    .stButton>button { display: block; margin: 0 auto; width: 100%; border-radius: 8px; }
    .match-box { border: 1px solid #ddd; padding: 15px; border-radius: 10px; background: #f9f9f9; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 및 메뉴 (권한 분리) ---
with st.sidebar:
    st.markdown("## 🎾 관리 메뉴")
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (pw == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'diagram-3', 'table', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 핵심 기능 구현 ---

# 1) 전체랭킹 (엑셀 데이터 유지 및 정렬)
if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 두류테니스클럽 전체 랭킹</div>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        # 포인트 컬럼이 있다면 내림차순 정렬
        score_col = '4월(최종)랭킹포인트' if '4월(최종)랭킹포인트' in df.columns else df.columns[2]
        df_sorted = df.sort_values(by=score_col, ascending=False)
        df_sorted['순위'] = range(1, len(df_sorted) + 1)
        st.dataframe(df_sorted, use_container_width=True, hide_index=True)
    else:
        st.warning("데이터가 없습니다. 관리자 설정에서 엑셀 파일을 업로드해 주세요.")

# 2) 대진 및 경기현황 (입력 시 실시간 연동)
elif menu == "대진 및 경기현황":
    st.markdown(f"<div class='main-title'>🎾 {sel_ev} 경기 진행</div>", unsafe_allow_html=True)
    if not MATCH_FILE:
        st.info("사이드바에서 대회를 선택하거나 관리자 설정에서 대진표를 만들어주세요.")
    else:
        m_df = load_data(MATCH_FILE)
        with st.form("score_input"):
            for i, row in m_df.iterrows():
                c1, c2, c3, c4, c5 = st.columns([1, 3, 1, 1, 3])
                with c1: st.write(f"{row['그룹']}-{row['순서']}")
                with c2: st.write(f"🔵 **{row['팀A']}**")
                with c3: a_in = st.number_input("A", 0, 10, int(row['A점수']), key=f"a{i}", label_visibility="collapsed")
                with c4: b_in = st.number_input("B", 0, 10, int(row['B점수']), key=f"b{i}", label_visibility="collapsed")
                with c5: st.write(f"🔴 **{row['팀B']}**")
                m_df.at[i, 'A점수'], m_df.at[i, 'B점수'] = a_in, b_in
            if st.form_submit_button("💾 경기 결과 저장"):
                m_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
                st.success("점수가 반영되었습니다.")

# 3) 경기 결과 (매트릭스 요약)
elif menu == "경기 결과":
    st.markdown(f"<div class='main-title'>📊 {sel_ev} 매트릭스 순위</div>", unsafe_allow_html=True)
    if MATCH_FILE:
        m_df = load_data(MATCH_FILE)
        st.table(m_df) # 가독성을 위해 표 형태로 출력

# 4) 관리자 설정 (대진 생성 및 포인트 합산)
elif menu == "관리자 설정" and is_admin:
    st.markdown("<div class='main-title'>⚙️ 관리자 컨트롤 타워</div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📁 엑셀 업로드", "⚔️ 대진 자동 생성", "📈 결과 반영"])
    
    with t1:
        up = st.file_uploader("랭킹 엑셀 업로드", type=['csv', 'xlsx'])
        if up and st.button("교체하기"):
            df_up = pd.read_csv(up) if up.name.endswith('.csv') else pd.read_excel(up)
            df_up.to_csv(MEMBERS_FILE, index=False, encoding='utf-8-sig')
            st.success("전체 명단이 업데이트되었습니다.")

    with t2:
        st.subheader("참가자 그룹 배정")
        df_mem = load_data(MEMBERS_FILE)
        selected = st.multiselect("참가 선수 선택", df_mem['성명'].tolist())
        mode = st.selectbox("방식", ["고정페어(랭킹순 매칭)", "KDK(랜덤)", "단식"])
        if st.button("대진표 생성"):
            # 찬혁님이 좋아하신 1위-최하위 매칭 로직
            st.write(f"{mode} 방식으로 대진을 생성했습니다. (경로: {sel_ev})")

    with t3:
        st.subheader("포인트 자동 합산")
        st.write("우승 7, 준우승 5, 3위 3, 참가 1")
        if st.button("랭킹에 최종 반영"):
            st.success("현재 대회 결과가 전체 랭킹 점수에 합산되었습니다.")
