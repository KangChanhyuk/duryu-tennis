import streamlit as st
import pandas as pd
import os
from streamlit_option_menu import option_menu

# --- 1. 경로 및 데이터 로드 ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path).fillna("") # None 표시 제거
    return pd.DataFrame()

SCORE_MAP = {"선택": 0, "우승": 7, "준우승": 5, "3위": 3, "참가": 1}

# --- 2. 페이지 설정 및 스타일 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.2rem; font-weight: bold; margin-bottom: 20px; }
    h1, h2, h3, p { text-align: center !important; }
    .stDataFrame { margin-left: auto; margin-right: auto; }
    .stButton>button { display: block; margin: 0 auto; width: 250px; background-color: #28a745; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 (대회 선택 및 로그인) ---
with st.sidebar:
    st.markdown("### 🎾 대회 관리")
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    
    st.markdown("---")
    pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (pw == "0502")

# --- 4. 메뉴 구성 (권한별 분리) ---
# 누구나 볼 수 있는 메뉴
main_menu = ["전체랭킹", "대진 및 경기현황", "경기 결과"]
main_icons = ['trophy', 'play-circle', 'clipboard-data']

# 관리자만 볼 수 있는 메뉴 추가
if is_admin:
    main_menu += ["관리자 점수반영", "관리자 설정"]
    main_icons += ['calculator', 'gear']

menu = option_menu(None, main_menu, icons=main_icons, 
                  menu_icon="cast", default_index=0, orientation="horizontal")

# 대회 경로 설정
EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 5. 메뉴별 기능 ---

# (1) 전체랭킹
if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 두류테니스클럽 전체 랭킹</div>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        if '4월(최종)랭킹포인트' in df.columns:
            df = df.sort_values(by='4월(최종)랭킹포인트', ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 랭킹 데이터가 없습니다.")

# (2) 대진 및 경기현황 / 경기 결과 (공용)
elif menu in ["대진 및 경기현황", "경기 결과"]:
    st.markdown(f"<div class='main-title'>🎾 {sel_ev} {menu}</div>", unsafe_allow_html=True)
    if not MATCH_FILE:
        st.warning("왼쪽 사이드바에서 대회를 먼저 선택해 주세요.")
    else:
        m_df = load_data(MATCH_FILE)
        if not m_df.empty:
            st.dataframe(m_df, use_container_width=True, hide_index=True)
        else:
            st.info("데이터가 준비되지 않았습니다.")

# (3) 관리자 점수반영 (기존 포인트에 합산)
elif menu == "관리자 점수반영":
    st.markdown("<div class='main-title'>⚙️ 점수 및 부과점 반영</div>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        with st.form("score_form"):
            new_rows = []
            for i, row in df.iterrows():
                c1, c2, c3 = st.columns([2, 2, 2])
                with c1: st.write(f"**{row['성명']}**")
                with c2: res = st.selectbox(f"결과", list(SCORE_MAP.keys()), key=f"r_{i}")
                with c3: extra = st.number_input(f"부과점", min_value=0, step=1, key=f"e_{i}")
                
                # 계산 로직
                curr_p = pd.to_numeric(row.get('4월(최종)랭킹포인트', 0), errors='coerce') or 0
                df.at[i, '획득합계'] = SCORE_MAP[res] + extra
            
            if st.form_submit_button("🚀 랭킹 포인트 업데이트"):
                for i in range(len(df)):
                    df.at[i, '4월(최종)랭킹포인트'] = pd.to_numeric(df.at[i, '4월(최종)랭킹포인트']) + df.at[i, '획득합계']
                
                df.drop(columns=['획득합계'], inplace=True)
                df.to_csv(MEMBERS_FILE, index=False, encoding='utf-8-sig')
                st.success("점수가 반영되었습니다!")
                st.rerun()

# (4) 관리자 설정 (파일 업로드 전용)
elif menu == "관리자 설정":
    st.markdown("<div class='main-title'>📂 데이터 파일 업로드</div>", unsafe_allow_html=True)
    up_file = st.file_uploader("엑셀 또는 CSV 파일을 선택하세요", type=['csv', 'xlsx'])
    if up_file:
        try:
            if up_file.name.endswith('.csv'): new_df = pd.read_csv(up_file).fillna("")
            else: new_df = pd.read_excel(up_file).fillna("")
            
            if st.button("🚀 전체 랭킹 명단 교체"):
                new_df.to_csv(MEMBERS_FILE, index=False, encoding='utf-8-sig')
                st.success("명단이 성공적으로 교체되었습니다.")
        except Exception as e:
            st.error(f"오류: {e}")
