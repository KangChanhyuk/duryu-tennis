import streamlit as st
import pandas as pd
import os
from streamlit_option_menu import option_menu

# --- 데이터 관리 ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_data(file_path):
    if os.path.exists(file_path):
        return pd.read_csv(file_path).fillna("")
    return pd.DataFrame()

# 점수 체계 정의
SCORE_MAP = {"선택": 0, "우승": 7, "준우승": 5, "3위": 3, "참가": 1}

# --- UI 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.2rem; font-weight: bold; }
    .stButton>button { width: 100%; background-color: #28a745; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 메뉴 ---
with st.sidebar:
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "관리자 점수반영"], 
                  icons=['trophy', 'play-circle', 'calculator'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

# --- 기능 구현 ---

if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 전체 랭킹 현황</div>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        # 포인트 기준 정렬 후 출력
        if '4월(최종)랭킹포인트' in df.columns:
            df = df.sort_values(by='4월(최종)랭킹포인트', ascending=False)
        st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "관리자 점수반영":
    if not is_admin:
        st.warning("관리자 권한이 필요합니다.")
    else:
        st.markdown("<div class='main-title'>⚙️ 경기 결과 및 점수 입력</div>", unsafe_allow_html=True)
        df = load_data(MEMBERS_FILE)
        
        if not df.empty:
            st.info("각 선수별 경기 결과와 부과점을 입력 후 하단의 '최종 반영' 버튼을 누르세요.")
            
            # 편집 가능한 데이터프레임 생성
            with st.form("score_form"):
                updated_data = []
                for i, row in df.iterrows():
                    cols = st.columns([2, 2, 2, 2])
                    with cols[0]: st.write(f"**{row['성명']}**")
                    with cols[1]: 
                        res = st.selectbox(f"결과 ({row['성명']})", list(SCORE_MAP.keys()), key=f"res_{i}")
                    with cols[2]:
                        extra = st.number_input(f"부과점 ({row['성명']})", min_value=0, step=1, key=f"ext_{i}")
                    
                    # 점수 계산
                    current_p = pd.to_numeric(row.get('4월(최종)랭킹포인트', 0), errors='coerce')
                    if pd.isna(current_p): current_p = 0
                    
                    new_score = SCORE_MAP[res] + extra
                    updated_data.append({
                        '성명': row['성명'],
                        '기존포인트': current_p,
                        '획득점수': new_score,
                        '결과': res if res != "선택" else ""
                    })
                
                submit = st.form_submit_button("🚀 랭킹에 최종 점수 반영하기")
                
                if submit:
                    # 실제 데이터프레임 업데이트 로직
                    for i, update in enumerate(updated_data):
                        df.at[i, '4월(최종)랭킹포인트'] = update['기존포인트'] + update['획득점수']
                        if update['결과']:
                            df.at[i, '결과'] = update['결과']
                    
                    df.to_csv(MEMBERS_FILE, index=False, encoding='utf-8-sig')
                    st.success("점수가 성공적으로 합산되었습니다! 전체랭킹 탭을 확인하세요.")
                    st.rerun()
        else:
            st.error("먼저 '관리자 설정'에서 회원 명단 엑셀을 업로드해 주세요.")
