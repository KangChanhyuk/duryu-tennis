import streamlit as st
import pandas as pd
import os
import itertools
import random
import re
from streamlit_option_menu import option_menu

# --- 1. 기본 설정 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        return pd.read_csv(MEMBERS_FILE).fillna("")
    return pd.DataFrame(columns=['랭킹', '성명', '4월 포인트', '3월 포인트', '부과점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    h1, h2, h3 { text-align: center; color: #002366; }
    .match-card { border: 2px solid #eee; border-radius: 15px; padding: 20px; margin-bottom: 20px; background: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #ff4b4b; text-align: center; display: block; }
    .matrix-table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; font-size: 14px; }
    .matrix-table th, .matrix-table td { border: 1px solid #ccc; padding: 10px; text-align: center; height: 50px; }
    .diagonal-line { background: linear-gradient(to top right, transparent 48%, #999 48%, #999 52%, transparent 52%); background-color: #f9f9f9; }
    .court-label { background: #002366; color: white; padding: 2px 10px; border-radius: 5px; font-size: 0.8rem; }
    .admin-box { background: #f8f9fa; padding: 20px; border-radius: 10px; border: 1px solid #ddd; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 및 메뉴 ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>🎾 두류테니스</h1>", unsafe_allow_html=True)
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'layout-text-sidebar', 'clipboard-data', 'gear'], 
                  menu_icon="cast", default_index=1, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴 기능 ---

if menu == "전체랭킹":
    st.markdown("<h1>🥇 전체 회원 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"🏆 {g}그룹" for g in groups])
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = m_df[m_df['그룹'] == g]
                # (매트릭스 출력 로직 생략 - 이전과 동일)
                st.markdown("### 🎾 경기 순서 (2코트 최적화)")
                for idx, row in g_df.iterrows():
                    court_num = 1 if (idx % 2 == 0) else 2
                    st.markdown(f"<div class='match-card'>", unsafe_allow_html=True)
                    st.markdown(f"<span class='court-label'>{court_num}번 코트 예정</span> <span style='color:gray; float:right;'>M-{row['순서']}</span>", unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 3])
                    c1.markdown(f"<h3 style='text-align:right;'>{row['팀A']}</h3>", unsafe_allow_html=True)
                    s_a = c2.number_input("", 0, 10, int(row['A점수']), key=f"sA_{idx}_{g}", label_visibility="collapsed")
                    c3.markdown("<span class='vs-text'>VS</span>", unsafe_allow_html=True)
                    s_b = c4.number_input("", 0, 10, int(row['B점수']), key=f"sB_{idx}_{g}", label_visibility="collapsed")
                    c5.markdown(f"<h3 style='text-align:left;'>{row['팀B']}</h3>", unsafe_allow_html=True)
                    if st.button(f"결과 저장", key=f"btn_{idx}_{g}", use_container_width=True):
                        actual_idx = m_df.index[m_df['순서'] == row['순서']][0]
                        m_df.loc[actual_idx, ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                        save_data(m_df, MATCH_FILE); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 관리자 설정</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📁 대회 관리", "⚔️ 대진 생성", "👤 참가자 관리"])
    
    with t2:
        # (대진 생성 로직 - 이전과 동일)
        st.info("명단을 입력하고 그룹별 경기 방식을 설정하여 대진을 생성하세요.")
        raw_names = st.text_area("명단 붙여넣기")
        # ... (생성 버튼 등 기존 로직)

    with t3:
        st.subheader("👤 대회 참가자 실시간 관리")
        if not MATCH_FILE: st.warning("대회를 먼저 선택해주세요.")
        else:
            m_df = pd.read_csv(MATCH_FILE)
            all_ps = sorted(list(set(re.split(r'[/]', "/".join(m_df['팀A'].tolist() + m_df['팀B'].tolist())))))
            
            # 1. 개인 수정 및 체크박스
            st.markdown("<div class='admin-box'>", unsafe_allow_html=True)
            cols = st.columns([1, 2, 2, 1])
            cols[0].write("**상태**")
            cols[1].write("**현재 이름**")
            cols[2].write("**변경할 이름**")
            cols[3].write("**동작**")
            
            for p in all_ps:
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                is_present = c1.checkbox("", value=True, key=f"chk_{p}")
                c2.text(p)
                new_name = c3.text_input("수정", value=p, key=f"edit_{p}", label_visibility="collapsed")
                if c4.button("교체", key=f"repl_{p}"):
                    if p != new_name:
                        # 대진표 전체에서 이름 교체 로직
                        m_df['팀A'] = m_df['팀A'].str.replace(p, new_name)
                        m_df['팀B'] = m_df['팀B'].str.replace(p, new_name)
                        save_data(m_df, MATCH_FILE)
                        st.success(f"'{p}'님이 '{new_name}'님으로 교체되었습니다.")
                        st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

            if st.button("⚠️ 모든 수정사항 저장 및 대진표 동기화"):
                save_data(m_df, MATCH_FILE)
                st.success("대진표 데이터가 업데이트되었습니다.")
