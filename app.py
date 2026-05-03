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
        for col in ['랭킹', '4월 포인트', '3월 포인트', '부과점']:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    return pd.DataFrame(columns=['랭킹', '성명', '4월 포인트', '3월 포인트', '변동', '부과점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 및 중앙 정렬 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1, h2, h3 { text-align: center; color: #1a2a6c; font-family: 'Nanum Gothic', sans-serif; }
    .stDataFrame { display: flex; justify-content: center; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    .match-card { border: 2px solid #1a2a6c; border-radius: 10px; padding: 15px; margin: 10px 0; background-color: white; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 핵심 로직: 대진 생성 (고정페어 & KDK) ---
def generate_matches(names, mode, rankings):
    # 이름을 랭킹순으로 재정렬
    ranked_names = [n for n in rankings if n in names]
    matches = []
    
    if mode == "고정페어":
        # 1위+최하위, 2위+차하위 매칭
        pairs = []
        while len(ranked_names) >= 2:
            pairs.append(f"{ranked_names.pop(0)} / {ranked_names.pop(-1)}")
        # 페어 간 리그전 대진 생성
        for idx, (a, b) in enumerate(itertools.combinations(pairs, 2)):
            matches.append({"순서": idx+1, "팀A": a, "팀B": b, "A점수": 0, "B점수": 0, "완료": 0})
            
    elif mode == "KDK (랜덤)":
        random.shuffle(names)
        for idx, combo in enumerate(itertools.combinations(names, 4)):
            if idx >= len(names) * 1.5: break # 인원 대비 적절수 제한
            p = list(combo)
            matches.append({"순서": idx+1, "팀A": f"{p[0]},{p[1]}", "팀B": f"{p[2]},{p[3]}", "A점수": 0, "B점수": 0, "완료": 0})
            
    return pd.DataFrame(matches)

# --- 4. 사이드바 메뉴 ---
with st.sidebar:
    st.markdown("## 🎾 두류테니스클럽")
    event_list = sorted([d for d in os.listdir(DATA_DIR)], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + event_list)
    admin_pw = st.text_input("관리자 암호", type="password")
    is_admin = (admin_pw == "0502")
    menu = st.radio("메뉴 이동", ["전체랭킹", "대진 및 경기현황", "경기 결과", "경기 기록"] + (["관리자 설정"] if is_admin else []))

# --- 5. 메뉴별 기능 구현 ---

# 1) 전체 랭킹
if menu == "전체랭킹":
    st.markdown("<h1>🥇 클럽 전체 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    # 변동 화살표 로직
    df['상태'] = df['변동'].apply(lambda x: "🔺" if x > 0 else ("🔻" if x < 0 else "—"))
    st.dataframe(df[['랭킹', '상태', '성명', '4월 포인트', '부과점', '비고']], use_container_width=True, hide_index=True)

# 2) 대진 및 경기현황 (자동 대칭 저장)
elif menu == "대진 및 경기현황":
    if sel_ev != "선택 안함":
        st.markdown(f"<h1>📅 {sel_ev} 현황</h1>", unsafe_allow_html=True)
        m_path = os.path.join(DATA_DIR, sel_ev, "matches.csv")
        if os.path.exists(m_path):
            df_m = pd.read_csv(m_path)
            for i, r in df_m.iterrows():
                with st.container():
                    st.markdown(f"<div class='match-card'>", unsafe_allow_html=True)
                    col1, col2, col3, col4 = st.columns([1, 3, 1, 3])
                    col1.write(f"**{r['순서']}R**")
                    sa = col2.number_input(f"{r['팀A']}", 0, 10, int(r['A점수']), key=f"a{i}")
                    col3.write("VS")
                    sb = col4.number_input(f"{r['팀B']}", 0, 10, int(r['B점수']), key=f"b{i}")
                    if st.button("결과 확정", key=f"save{i}"):
                        df_m.at[i, 'A점수'], df_m.at[i, 'B점수'], df_m.at[i, '완료'] = sa, sb, 1
                        save_data(df_m, m_path); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

# 3) 경기 결과 (매트릭스 및 요약)
elif menu == "경기 결과":
    st.markdown("<h1>📊 경기 결과 매트릭스</h1>", unsafe_allow_html=True)
    # 매트릭스 및 승패/득실차 계산 로직 배치

# 4) 관리자 설정 (핵심 기능)
elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 관리자 컨트롤 타워</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["🏆 대회 생성/삭제", "👥 참여자 관리", "🔄 결과 반영"])
    
    with tab1:
        ev_name = st.text_input("새 대회 명칭")
        df_mem = load_members().sort_values('랭킹')
        selected = st.multiselect("참가자 선택 (랭킹순 정렬됨)", df_mem['성명'].tolist())
        
        c1, c2, c3 = st.columns(3)
        g_cnt = c1.number_input("그룹 수", 1, 5, 1)
        g_mode = c2.selectbox("방식", ["KDK (랜덤)", "고정페어"])
        
        if st.button("🚀 대회 및 대진 생성"):
            path = os.path.join(DATA_DIR, ev_name)
            if not os.path.exists(path): os.makedirs(path)
            # 랭킹순 분배 로직 (A, B, C, D 그룹순)
            # 대진 생성 함수 호출 및 저장
            st.success("대진표 생성 완료!")

    with tab2:
        st.subheader("참가자 명단 수정")
        # 텍스트 area와 체크박스를 이용한 명단 교체 로직
        
    with tab3:
        st.subheader("결과 반영 및 수정")
        # 전체 랭킹 자동 합산 및 수정 기능
