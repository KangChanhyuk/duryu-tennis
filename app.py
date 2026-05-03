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
        df = pd.read_csv(MEMBERS_FILE).fillna(0)
        # 필수 컬럼이 없을 경우 자동 생성하여 에러 방지
        for col in ['성명', '포인트', '나이', '랭킹']:
            if col not in df.columns: df[col] = 0
        return df
    # 파일이 아예 없을 경우 빈 데이터프레임 반환
    return pd.DataFrame(columns=['랭킹', '성명', '나이', '포인트', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 및 레이아웃 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    h1, h2, h3, p { text-align: center !important; }
    .match-card { border: 2px solid #eee; border-radius: 15px; padding: 20px; margin-bottom: 20px; background: white; }
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
    
    if not df_members.empty and len(df_members) > 0:
        try:
            # 포인트 내림차순, 포인트 같으면 나이 내림차순으로 정렬
            df_display = df_members.sort_values(by=['포인트', '나이'], ascending=[False, False])
            df_display['랭킹'] = range(1, len(df_display) + 1)
            
            # 보기 좋게 컬럼 순서 재배치
            cols = ['랭킹', '성명', '포인트', '나이', '비고']
            actual_cols = [c for c in cols if c in df_display.columns]
            st.dataframe(df_display[actual_cols], use_container_width=True, hide_index=True)
        except Exception as e:
            st.error(f"데이터 정렬 중 오류가 발생했습니다. 관리자 설정에서 파일을 다시 확인해주세요.")
    else:
        st.warning("등록된 회원 정보가 없습니다. [관리자 설정] 탭에서 엑셀 파일을 업로드하거나 회원을 등록해주세요.")

elif menu == "관리자 설정" and is_admin:
    st.markdown("<div class='main-title'>⚙️ 관리자 컨트롤 타워</div>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["📊 엑셀 업로드/랭킹", "⚔️ 대진 생성/교체", "📈 대회 결과 반영"])
    
    with tab1:
        st.subheader("📁 회원 명단 엑셀 업로드")
        st.info("엑셀 파일에 '성명', '포인트', '나이' 컬럼이 포함되어야 합니다.")
        up_file = st.file_uploader("CSV 또는 XLSX 파일 선택", type=['csv', 'xlsx'])
        if up_file:
            try:
                if up_file.name.endswith('.csv'): df_up = pd.read_csv(up_file)
                else: df_up = pd.read_excel(up_file)
                
                # 업로드된 데이터 검증
                if '성명' not in df_up.columns:
                    st.error("'성명' 컬럼이 엑셀에 없습니다. 확인 후 다시 올려주세요.")
                else:
                    if st.button("전체 랭킹에 데이터 저장"):
                        # 포인트나 나이가 없으면 0으로 채우기
                        if '포인트' not in df_up.columns: df_up['포인트'] = 0
                        if '나이' not in df_up.columns: df_up['나이'] = 0
                        save_data(df_up, MEMBERS_FILE)
                        st.success("회원 명단 업데이트 완료!")
                        st.rerun()
            except Exception as e:
                st.error(f"파일을 읽는 중 에러가 발생했습니다: {e}")

    # ... (대진 생성 및 결과 반영 탭은 이전 코드 유지) ...
