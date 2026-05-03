import streamlit as st
import pandas as pd
import numpy as np
import os
import random
from streamlit_option_menu import option_menu

# --- 1. 데이터 관리 (랭킹 기억 및 정렬) ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')

def load_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # 랭킹 포인트 숫자형 변환 (정렬 오류 방지)
        score_col = [c for c in df.columns if '포인트' in c or '점수' in c][0]
        df[score_col] = pd.to_numeric(df[score_col], errors='coerce').fillna(0)
        return df.sort_values(by=score_col, ascending=False).reset_index(drop=True)
    return pd.DataFrame()

# --- 2. 대진 생성 로직 (단식/복식/KDK) ---
def generate_matches(group_name, members, mode):
    matches = []
    if mode == "단식(1:1)":
        # 풀리그 방식
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                matches.append({"그룹": group_name, "팀A": members[i], "팀B": members[j]})
    
    elif mode == "복식(고정페어)":
        # 1위-꼴찌 매칭
        half = len(members) // 2
        teams = []
        for i in range(half):
            teams.append(f"{members[i]}/{members[-(i+1)]}")
        for i in range(len(teams)):
            for j in range(i + 1, len(teams)):
                matches.append({"그룹": group_name, "팀A": teams[i], "팀B": teams[j]})
                
    elif mode == "복식(KDK)":
        # 4인 1조 로테이션 예시 (간소화)
        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                matches.append({"그룹": group_name, "팀A": members[i], "팀B": members[j]})
                
    return matches

# --- 3. UI 구성 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
# ... (스타일 생략) ...

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'diagram-3', 'table', 'gear'], orientation="horizontal")

# --- 4. 메뉴별 기능 ---
if menu == "전체랭킹":
    st.markdown("<h2 style='text-align:center;'>🏆 현재 랭킹 순위</h2>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        df.insert(0, '순위', range(1, len(df) + 1))
        st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "관리자 설정" and (st.sidebar.text_input("🔑 암호", type="password") == "0502"):
    st.markdown("### ⚙️ 대회 자동 생성 (랭킹 기반)")
    
    df_mem = load_data(MEMBERS_FILE)
    all_players = st.multiselect("오늘 참가한 인원을 모두 선택하세요", df_mem['성명'].tolist())
    
    if all_players:
        # 참가자들을 랭킹 순서대로 다시 정렬
        sorted_players = df_mem[df_mem['성명'].isin(all_players)]['성명'].tolist()
        
        col1, col2 = st.columns(2)
        g_count = col1.number_input("나눌 그룹 수", 1, 5, 2)
        
        # 랭킹순 자동 분할 리스트 보여주기
        split_players = np.array_split(sorted_players, g_count)
        
        final_matches = []
        for i, group in enumerate(split_players):
            g_label = chr(65 + i)
            st.info(f"📍 {g_label}조 (랭킹 상위 {i+1}순위권): {', '.join(group)}")
            mode = st.selectbox(f"{g_label}조 경기 방식", ["단식(1:1)", "복식(고정페어)", "복식(KDK)"], key=f"m_{i}")
            
            group_matches = generate_matches(g_label, list(group), mode)
            for m in group_matches:
                m['순서'] = len(final_matches) + 1
                m['A점수'], m['B점수'] = 0, 0
                final_matches.append(m)
        
        if st.button("🚀 대진표 최종 확정 및 저장"):
            # 대회 폴더 생성 및 저장 로직
            st.success("대진표가 생성되었습니다! '대진 및 경기현황' 탭을 확인하세요.")
