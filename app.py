import streamlit as st
import pandas as pd
import os
import random
import itertools

# --- 1. 기본 설정 및 데이터 로드 ---
DATA_DIR = "data"
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)
MEMBERS_FILE = 'tennis_members.csv'

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        # 랭킹을 숫자로 변환 (미등록자 999등 처리)
        df['랭킹'] = pd.to_numeric(df['랭킹'], errors='coerce').fillna(999).astype(int)
        return df
    return pd.DataFrame(columns=['랭킹', '성명', '4월 포인트', '3월 포인트', '결과', '부과점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. KDK 생성 엔진 (랜덤 기능 포함) ---
def generate_kdk_random(names):
    random.shuffle(names) # 섞어서 랜덤성 부여
    n = len(names)
    matches = []
    
    # 4명씩 짝지어 경기 생성 (KDK 로직 예시)
    # 실제로는 참가 인원수(4~8명)에 따른 KDK 테이블을 참조하게 됨
    if n >= 4:
        # 간단한 로테이션 예시 (실제 복식 매칭)
        combs = list(itertools.combinations(names, 2))
        random.shuffle(combs)
        for i in range(0, len(combs)-1, 2):
            matches.append({
                "순서": f"매치 {i//2 + 1}",
                "팀A": combs[i][0] + "," + combs[i][1],
                "팀B": combs[i+1][0] + "," + combs[i+1][1],
                "A점수": 0, "B점수": 0, "완료": 0
            })
    return pd.DataFrame(matches)

# --- 3. UI 및 메뉴 ---
st.set_page_config(page_title="두류 테니스 클럽", layout="wide")

with st.sidebar:
    st.title("🎾 두류 테니스")
    event_list = sorted([d for d in os.listdir(DATA_DIR)], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + event_list)
    
    admin_pw = st.text_input("관리자 암호", type="password")
    is_admin = (admin_pw == "0502")
    
    menu = st.radio("메뉴 이동", ["전체랭킹", "대진 및 경기 현황", "경기 결과", "경기 기록"] + (["관리자 설정"] if is_admin else []))

# --- 4. 관리자 설정 (대진 생성 핵심) ---
if menu == "관리자 설정" and is_admin:
    st.header("⚙️ 관리자 설정")
    t1, t2 = st.tabs(["📅 대회 및 대진 생성", "✍️ 멤버 관리"])
    
    with t1:
        st.subheader("1. 새로운 대회 만들기")
        new_ev_name = st.text_input("대회 명칭 (예: 2026-05-03 일요모임)")
        
        df_mem = load_members()
        # 랭킹순으로 정렬하여 표시
        sorted_mem = df_mem.sort_values('랭킹')
        selected_names = st.multiselect("참여자 선택 (랭킹순 정렬됨)", sorted_mem['성명'].tolist())
        
        col1, col2 = st.columns(2)
        group_type = col1.selectbox("대진 방식", ["KDK (랜덤)", "리그전"])
        group_count = col2.number_input("그룹 수", 1, 4, 1)
        
        if st.button("대진표 생성 및 저장"):
            if new_ev_name and selected_names:
                path = os.path.join(DATA_DIR, new_ev_name)
                if not os.path.exists(path): os.makedirs(path)
                
                # 선택된 인원을 다시 랭킹순으로 정렬
                final_names = sorted_mem[sorted_mem['성명'].isin(selected_names)]['성명'].tolist()
                
                # 그룹 나누기 (랭킹순으로 분배)
                all_matches = []
                for i in range(group_count):
                    # 랭킹순으로 슬라이싱 (예: 1~8위 1그룹, 9~16위 2그룹)
                    group_members = final_names[i::group_count] 
                    group_df = generate_kdk_random(group_members)
                    group_df['그룹'] = f"{i+1}그룹"
                    all_matches.append(group_df)
                
                final_match_df = pd.concat(all_matches)
                save_data(final_match_df, os.path.join(path, "matches.csv"))
                st.success(f"'{new_ev_name}' 대진표가 생성되었습니다!")
                st.rerun()

    with t2:
        st.subheader("2. 전체 멤버 및 부과점 수정")
        edited_df = st.data_editor(df_mem, use_container_width=True, hide_index=True)
        if st.button("멤버 정보 업데이트"):
            save_data(edited_df, MEMBERS_FILE)
            st.success("저장되었습니다.")

# --- 5. 일반 메뉴 (생략 - 이전 코드와 동일) ---
elif menu == "전체랭킹":
    st.table(load_members().sort_values('랭킹'))
