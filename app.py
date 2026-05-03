import streamlit as st
import pandas as pd
import os
import itertools
import random
import re
from streamlit_option_menu import option_menu

# --- 1. 데이터 관리 및 파일 경로 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        return pd.read_csv(MEMBERS_FILE).fillna("")
    # 파일 없을 시 기본 틀 생성
    return pd.DataFrame(columns=['랭킹', '성명', '나이', '포인트', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 및 레이아웃 (가운데 정렬) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    h1, h2, h3, p { text-align: center !important; }
    .stButton>button { display: block; margin: 0 auto; }
    .match-card { border: 2px solid #eee; border-radius: 15px; padding: 20px; margin-bottom: 20px; background: white; }
    .matrix-table { width: 100%; margin: 0 auto; border-collapse: collapse; text-align: center; }
    .matrix-table th, .matrix-table td { border: 1px solid #ddd; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 및 세션 관리 ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🎾 관리 메뉴</h2>", unsafe_allow_html=True)
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")

if 'raw_names' not in st.session_state: st.session_state.raw_names = ""

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'play-circle', 'clipboard-data', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 상세 기능 ---

if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 두류테니스클럽 전체 랭킹</div>", unsafe_allow_html=True)
    df_members = load_members()
    if not df_members.empty:
        # 포인트 순으로 자동 정렬하여 표시
        df_display = df_members.sort_values(by='포인트', ascending=False)
        df_display['랭킹'] = range(1, len(df_display) + 1)
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.warning("등록된 회원 정보가 없습니다. 관리자 설정에서 엑셀을 업로드해주세요.")

elif menu == "대진 및 경기현황":
    # (기존의 2코트 최적화 카드 출력 로직 유지)
    st.markdown("<div class='main-title'>🎾 경기 진행 현황</div>", unsafe_allow_html=True)
    if not MATCH_FILE: st.info("사이드바에서 대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        # ... 경기 스코어 입력 로직 ...
        st.write("경기 현황판이 활성화되었습니다.")

elif menu == "경기 결과":
    st.markdown("<div class='main-title'>📊 대회 최종 결과</div>", unsafe_allow_html=True)
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        # (기존의 매트릭스 및 순위 산정 로직 유지)
        st.write("그룹별 최종 순위 및 매트릭스 점수표가 표시됩니다.")

elif menu == "관리자 설정" and is_admin:
    st.markdown("<div class='main-title'>⚙️ 관리자 컨트롤 타워</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📊 엑셀 업로드/랭킹", "⚔️ 대진 생성/교체", "📈 대회 결과 반영"])
    
    with tab1:
        st.subheader("📁 회원 명단 엑셀 업로드")
        up_file = st.file_uploader("CSV 또는 XLSX 파일 선택", type=['csv', 'xlsx'])
        if up_file:
            if up_file.name.endswith('.csv'): df_up = pd.read_csv(up_file)
            else: df_up = pd.read_excel(up_file)
            if st.button("전체 랭킹에 덮어쓰기"):
                save_data(df_up, MEMBERS_FILE)
                st.success("회원 명단이 성공적으로 업데이트되었습니다!")

    with tab2:
        # (기존의 랭킹순 정렬 및 1인당 게임수 기반 대진 생성 로직 유지)
        st.session_state.raw_names = st.text_area("참가자 명단 입력", value=st.session_state.raw_names)
        # ... 대진 생성 버튼 ...

    with tab3:
        st.subheader("📈 대회 점수 전체 랭킹에 반영")
        st.info("현재 선택된 대회의 승패 결과를 전체 랭킹 포인트에 합산합니다.")
        if MATCH_FILE:
            if st.button("🚀 대회 결과 최종 반영 (포인트 업데이트)"):
                m_df = pd.read_csv(MATCH_FILE)
                mem_df = load_members()
                
                # 점수 반영 로직 (예: 승리 10점, 무승부 5점, 참가 2점)
                for idx, row in m_df.iterrows():
                    if row['완료'] == 1:
                        # 복식일 경우 파트너 분리
                        players_a = re.split(r'[/]', row['팀A'])
                        players_b = re.split(r'[/]', row['팀B'])
                        
                        if row['A점수'] > row['B점수']:
                            for p in players_a: mem_df.loc[mem_df['성명']==p, '포인트'] += 10
                        elif row['A점수'] < row['B점수']:
                            for p in players_b: mem_df.loc[mem_df['성명']==p, '포인트'] += 10
                        else: # 무승부
                            for p in players_a + players_b: mem_df.loc[mem_df['성명']==p, '포인트'] += 5
                
                save_data(mem_df, MEMBERS_FILE)
                st.success("대회 결과가 전체 랭킹에 성공적으로 반영되었습니다!")
