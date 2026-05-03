import streamlit as st
import pandas as pd
import os
from streamlit_option_menu import option_menu

# --- 1. 파일 저장 경로 설정 ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

# --- 2. 데이터 로드 함수 (단순화) ---
def load_members():
    if os.path.exists(MEMBERS_FILE):
        # 엑셀 내용을 그대로 읽어옴
        return pd.read_csv(MEMBERS_FILE).fillna("")
    return pd.DataFrame()

# --- 3. 기본 UI 스타일 (가운데 정렬) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    h1, h2, h3, p { text-align: center !important; }
    .stDataFrame { margin-left: auto; margin-right: auto; }
    .stButton>button { display: block; margin: 0 auto; width: 200px; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 메뉴 구성 ---
menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'play-circle', 'clipboard-data', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

# 관리자 인증 (사이드바)
with st.sidebar:
    st.markdown("<h3 style='text-align:center;'>🔑 관리자 로그인</h3>", unsafe_allow_html=True)
    pw = st.text_input("비밀번호 입력", type="password")
    is_admin = (pw == "0502")

# --- 5. 메뉴별 화면 ---

if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 두류테니스클럽 전체 랭킹</div>", unsafe_allow_html=True)
    df = load_members()
    
    if not df.empty:
        # 엑셀 순서 그대로 1번부터 번호 부여
        df_display = df.copy()
        df_display.insert(0, '순위', range(1, len(df_display) + 1))
        
        # 화면 출력
        st.dataframe(df_display, use_container_width=True, hide_index=True)
    else:
        st.info("표시할 데이터가 없습니다. 관리자 설정에서 엑셀 파일을 업로드해 주세요.")

elif menu == "관리자 설정":
    if is_admin:
        st.markdown("<div class='main-title'>⚙️ 관리자 설정</div>", unsafe_allow_html=True)
        
        st.subheader("📁 엑셀 명단 업로드")
        st.write("작성하신 엑셀(CSV/XLSX) 파일을 올리면 순서 그대로 랭킹에 반영됩니다.")
        
        up_file = st.file_uploader("파일 선택", type=['csv', 'xlsx'])
        
        if up_file:
            try:
                if up_file.name.endswith('.csv'):
                    new_df = pd.read_csv(up_file)
                else:
                    new_df = pd.read_excel(up_file)
                
                st.write("### 업로드 데이터 미리보기")
                st.dataframe(new_df.head(10), use_container_width=True)
                
                if st.button("🚀 이 순서대로 랭킹 업데이트"):
                    new_df.to_csv(MEMBERS_FILE, index=False, encoding='utf-8-sig')
                    st.success("업데이트가 완료되었습니다! '전체랭킹' 탭에서 확인하세요.")
                    st.balloons()
            except Exception as e:
                st.error(f"파일 처리 중 에러 발생: {e}")
    else:
        st.warning("관리자 비밀번호를 입력해 주세요.")

# 나머지 메뉴는 선택 시 메시지만 표시 (코드 간결화)
else:
    st.markdown(f"<div class='main-title'>{menu}</div>", unsafe_allow_html=True)
    st.write("현재 랭킹 데이터 연동을 최우선으로 수정 중입니다.")
