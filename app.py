import streamlit as st
import pandas as pd
import os
import itertools
import random
import re

# --- 1. 기본 설정 및 데이터 로드 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        for c in ['4월 포인트', '3월 포인트', '부과점', '랭킹']:
            df[c] = pd.to_numeric(df.get(c, 0), errors='coerce').fillna(0).astype(int)
        # 순위 변동 계산 로직
        df['변동치'] = df['3월 포인트'] - df['4월 포인트'] # 예시: 포인트가 높을수록 순위 상승
        df['상태'] = df['변동치'].apply(lambda x: "🔺" if x > 0 else ("🔻" if x < 0 else "—"))
        return df
    return pd.DataFrame(columns=['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '총점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 배경 및 스타일 설정 (가운데 정렬 및 가독성) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #fcfcfc; }
    h1, h2, h3 { text-align: center; color: #002366; font-family: 'Pretendard', sans-serif; }
    .stTable, .stDataFrame { margin-left: auto; margin-right: auto; }
    .match-card { 
        border: 2px solid #e0e0e0; border-radius: 15px; padding: 20px; 
        margin: 10px 0; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .center-text { text-align: center; }
    .vs-badge { background: #ff4b4b; color: white; padding: 5px 15px; border-radius: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 메뉴 ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>🎾 두류테니스</h1>", unsafe_allow_html=True)
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")
    menu = st.option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
        icons=['trophy', 'layout-text-sidebar', 'clipboard-data', 'gear'], menu_icon="cast", default_index=0)

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 구현 ---

# [메뉴 1] 전체랭킹
if menu == "전체랭킹":
    st.markdown("<h1>🥇 실시간 클럽 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    # 많은 정보가 보이도록 테이블 구성
    st.table(df[['랭킹', '상태', '성명', '4월 포인트', '부과점', '비고']].style.set_properties(**{'text-align': 'center'}))

# [메뉴 2] 대진 및 경기현황
elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택하세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"Group {g}" for g in groups])
        
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = m_df[m_df['그룹'] == g]
                for idx, row in g_df.iterrows():
                    st.markdown(f"<div class='match-card'>", unsafe_allow_html=True)
                    st.markdown(f"<p class='center-text'><b>Match {row['순서']}</b></p>", unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                    with c1: st.markdown(f"<h3 class='center-text'>{row['팀A']}</h3>", unsafe_allow_html=True)
                    with c2: s_a = st.number_input("", 0, 10, int(row['A점수']), key=f"sA_{idx}")
                    with c3: st.markdown("<div class='vs-badge'>VS</div>", unsafe_allow_html=True)
                    with c4: s_b = st.number_input("", 0, 10, int(row['B점수']), key=f"sB_{idx}")
                    with c5: st.markdown(f"<h3 class='center-text'>{row['팀B']}</h3>", unsafe_allow_html=True)
                    
                    if st.button(f"결과 저장 (M-{row['순서']})", key=f"btn_{idx}"):
                        m_df.loc[idx, ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                        save_data(m_df, MATCH_FILE)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

# [메뉴 3] 경기 결과 (매트릭스 랭킹)
elif menu == "경기 결과":
    if not MATCH_FILE: st.info("대회를 선택하세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        st.markdown("<h1>📊 대회 성적 집계</h1>", unsafe_allow_html=True)
        # 성적 계산 로직 (승패, 득실 등 계산 후 매트릭스 형태로 시각화)
        # (생략: 각 팀별 승률 및 득실점 계산 후 DataFrame 출력)

# [메뉴 4] 관리자 설정
elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 관리자 컨트롤 타워</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📁 대회 관리", "🤝 참가자 및 대진 생성", "🏆 결과 반영"])
    
    with t1: # 대회 생성 및 삭제
        new_ev = st.text_input("새 대회 명칭 (예: 2026_05_정기전)")
        if st.button("대회 생성"): os.makedirs(os.path.join(DATA_DIR, new_ev), exist_ok=True); st.rerun()
        del_ev = st.selectbox("삭제할 대회", all_ev)
        if st.button("대회 삭제"): # 폴더 삭제 로직
            pass

    with t2: # 랭킹 기반 그룹 및 페어 구성
        all_mems = load_members().sort_values('랭킹')
        st.subheader("참가자 선택")
        raw_names = st.text_area("명단 붙여넣기 (자유 형식)")
        names = re.split(r'[,\s\n]+', raw_names)
        # ... (이름 필터링 로직)
        
        mode = st.selectbox("경기 방식", ["단식", "고정페어 복식", "KDK 복식"])
        g_cnt = st.number_input("그룹 수", 1, 5, 2)
        
        if st.button("대진 생성"):
            # 랭킹순 A->B->C 그룹 분배 로직
            # 고정페어: 1위+최하위 / 2위+차하위 밸런싱 로직 적용
            # KDK: 랜덤 파트너십 생성
            pass

    with t3: # 결과 반영 및 랭킹 업데이트
        st.subheader("대회 결과 포인트 부여")
        # 대회 종료 후 포인트를 전체랭킹(tennis_members.csv)에 합산 저장하는 기능
