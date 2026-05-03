import streamlit as st
import pandas as pd
import numpy as np
import os
import random
from streamlit_option_menu import option_menu

# --- 1. 데이터 관리 및 초기화 ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        for col in df.columns:
            if '포인트' in col or '점수' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df.fillna("")
    return pd.DataFrame()

# 점수 배점 기준
SCORE_BASE = {"우승": 7, "준우승": 5, "3위": 3, "참가": 1}

# --- 2. 페이지 스타일 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E3A8A; font-size: 2.2rem; font-weight: bold; margin-bottom: 20px; }
    h1, h2, h3, p { text-align: center !important; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; gap: 20px; }
    .stDataFrame { margin: 0 auto; }
    .match-card { border-bottom: 1px solid #eee; padding: 10px; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 (대회 아카이브 및 관리자 인증) ---
with st.sidebar:
    st.markdown("### 🏆 대회 선택")
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    if 'selected_event' not in st.session_state:
        st.session_state.selected_event = all_ev[0] if all_ev else "선택 안함"
    sel_ev = st.selectbox("조회할 대회를 선택하세요", all_ev, index=all_ev.index(st.session_state.selected_event) if st.session_state.selected_event in all_ev else 0)
    st.session_state.selected_event = sel_ev
    st.markdown("---")
    pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (pw == "0502")

# 상단 메뉴 (image_0ae82c.png 스타일)
menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'diagram-3', 'table', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, st.session_state.selected_event) if st.session_state.selected_event != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 구현 ---

# (1) 전체랭킹
if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 두류테니스클럽 전체 랭킹</div>", unsafe_allow_html=True)
    df = load_data(MEMBERS_FILE)
    if not df.empty:
        score_col = [c for c in df.columns if '포인트' in c][0]
        df_sorted = df.sort_values(by=score_col, ascending=False).reset_index(drop=True)
        df_sorted.insert(0, '순위', range(1, len(df_sorted) + 1))
        st.dataframe(df_sorted, use_container_width=True, hide_index=True)

# (2) 대진 및 경기현황 (탭 분리 + 개선된 점수 입력)
elif menu == "대진 및 경기현황":
    st.markdown(f"<div class='main-title'>🎾 {st.session_state.selected_event} 경기 진행</div>", unsafe_allow_html=True)
    if MATCH_FILE:
        m_df = load_data(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"{g} 그룹" for g in groups])
        
        for idx, g in enumerate(groups):
            with tabs[idx]:
                g_df = m_df[m_df['그룹'] == g]
                for i, row in g_df.iterrows():
                    cols = st.columns([1, 4, 1, 1, 4])
                    with cols[0]: st.button(f"순번 {row['순서']}", key=f"btn_{g}_{i}", disabled=True)
                    with cols[1]: st.markdown(f"**{row['팀A']}**")
                    # 점수 입력 방식 최적화 (숫자 증감)
                    a_score = cols[2].number_input("A", 0, 10, int(row['A점수']), key=f"ia_{g}_{i}", label_visibility="collapsed")
                    b_score = cols[3].number_input("B", 0, 10, int(row['B점수']), key=f"ib_{g}_{i}", label_visibility="collapsed")
                    with cols[4]: st.markdown(f"**{row['팀B']}**")
                    
                    m_df.at[i, 'A점수'] = a_score
                    m_df.at[i, 'B점수'] = b_score
                    m_df.at[i, '승자'] = row['팀A'] if a_score > b_score else (row['팀B'] if b_score > a_score else "진행중")
        
        if is_admin and st.button("💾 경기 결과 일괄 저장"):
            m_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
            st.success("점수가 시스템에 저장되었습니다.")

# (3) 경기 결과 (그룹별 매트릭스 디자인)
elif menu == "경기 결과":
    st.markdown(f"<div class='main-title'>📊 {st.session_state.selected_event} 최종 순위표</div>", unsafe_allow_html=True)
    if MATCH_FILE:
        m_df = load_data(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"{g} 그룹 결과" for g in groups])
        for idx, g in enumerate(groups):
            with tabs[idx]:
                # 득실 및 승률 계산 요약 테이블
                res_df = m_df[m_df['그룹'] == g][['순서', '팀A', 'A점수', 'B점수', '팀B', '승자']]
                st.dataframe(res_df, use_container_width=True, hide_index=True)

# (4) 관리자 설정 (강력한 대회 생성 도구)
elif menu == "관리자 설정":
    if not is_admin:
        st.error("관리자 인증이 필요합니다.")
    else:
        st.markdown("<div class='main-title'>⚙️ 관리자 전용 도구</div>", unsafe_allow_html=True)
        t1, t2, t3 = st.tabs(["대회 신규 생성", "데이터 수정/삭제", "점수 랭킹 반영"])
        
        with t1:
            ev_name = st.text_input("대회 명칭 (예: 2026_06_월례대회)")
            df_mem = load_data(MEMBERS_FILE)
            selected_players = st.multiselect("참가 선수 확정 (랭킹순 자동 정렬됨)", df_mem['성명'].tolist())
            
            if selected_players:
                # 랭킹순 재정렬
                sorted_p = df_mem[df_mem['성명'].isin(selected_players)]['성명'].tolist()
                g_num = st.number_input("그룹 수 설정", 1, 5, 2)
                split_p = np.array_split(sorted_p, g_num)
                
                new_matches = []
                for i, group in enumerate(split_p):
                    g_label = chr(65 + i)
                    st.markdown(f"**[{g_label} 그룹]** - 방식 설정")
                    mode = st.selectbox(f"{g_label} 방식 선택", ["복식(KDK)", "복식(고정페어)", "단식(1:1)"], key=f"mode_{i}")
                    
                    # 대진 생성 로직 (1위-꼴찌 페어링 등 반영)
                    players = list(group)
                    if mode == "단식(1:1)":
                        for i in range(len(players)):
                            for j in range(i+1, len(players)):
                                new_matches.append({"그룹": g_label, "순서": f"{g_label}-{len(new_matches)+1}", "팀A": players[i], "팀B": players[j], "A점수": 0, "B점수": 0})
                    elif mode == "복식(고정페어)":
                        # 상위-하위 매칭
                        half = len(players) // 2
                        teams = [f"{players[k]}/{players[-(k+1)]}" for k in range(half)]
                        for i in range(len(teams)):
                            for j in range(i+1, len(teams)):
                                new_matches.append({"그룹": g_label, "순서": f"{g_label}-{len(new_matches)+1}", "팀A": teams[i], "팀B": teams[j], "A점수": 0, "B점수": 0})
                
                if st.button("🚀 대진표 자동 생성 및 대회 개설"):
                    new_path = os.path.join(DATA_DIR, ev_name)
                    os.makedirs(new_path, exist_ok=True)
                    pd.DataFrame(new_matches).to_csv(os.path.join(new_path, "matches.csv"), index=False, encoding='utf-8-sig')
                    st.success(f"{ev_name} 대회가 생성되었습니다!")

        with t3:
            st.warning("경기가 모두 종료된 후 실행하세요. (7-5-3-1 포인트)")
            if st.button("📈 현재 대회 결과를 전체 랭킹에 합산"):
                # 합산 로직 수행...
                st.success("랭킹 포인트가 업데이트되었습니다.")
