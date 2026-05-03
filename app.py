import streamlit as st
import pandas as pd
import os
from streamlit_option_menu import option_menu

# --- 파일 경로 ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        return pd.read_csv(MEMBERS_FILE).fillna("")
    return pd.DataFrame()

# --- 화면 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    h1, h2, h3, p { text-align: center !important; }
    .stDataFrame { margin-left: auto; margin-right: auto; }
    .stButton>button { display: block; margin: 0 auto; width: 200px; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 메뉴 ---
menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'play-circle', 'clipboard-data', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

with st.sidebar:
    pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (pw == "0502")

# --- 로직 ---
if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 두류테니스클럽 전체 랭킹</div>", unsafe_allow_html=True)
    df = load_members()
    if not df.empty:
        # 엑셀에 이미 '랭킹' 컬럼이 있으므로 그대로 출력
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("관리자 설정에서 엑셀 파일을 업로드해 주세요.")

elif menu == "관리자 설정" and is_admin:
    st.markdown("<div class='main-title'>⚙️ 관리자 설정</div>", unsafe_allow_html=True)
    
    up_file = st.file_uploader("📂 엑셀 또는 CSV 파일 선택", type=['csv', 'xlsx'])
    
    if up_file:
        try:
            if up_file.name.endswith('.csv'):
                new_df = pd.read_csv(up_file)
            else:
                # xlsx 읽기 시도 (openpyxl 필요)
                new_df = pd.read_excel(up_file)
            
            st.write("### 데이터 확인")
            st.dataframe(new_df.head(10), use_container_width=True)
            
            if st.button("🚀 랭킹 업데이트"):
                new_df.to_csv(MEMBERS_FILE, index=False, encoding='utf-8-sig')
                st.success("업데이트 완료! 전체랭킹 탭을 확인하세요.")
                st.rerun()
        except ImportError:
            st.error("⚠️ 서버 설정이 필요합니다. 'requirements.txt'에 'openpyxl'을 추가하시거나, 파일을 CSV 형식으로 저장해서 올려주세요.")
        except Exception as e:
            st.error(f"오류 발생: {e}")
