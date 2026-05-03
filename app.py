import streamlit as st
import pandas as pd
import os
import itertools
import random
import re
from streamlit_option_menu import option_menu

# --- 1. 기본 설정 및 데이터 관리 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        for c in ['4월 포인트', '3월 포인트', '부과점', '랭킹']:
            df[c] = pd.to_numeric(df.get(c, 0), errors='coerce').fillna(0).astype(int)
        df['변동치'] = df['4월 포인트'] - df['3월 포인트']
        df['상태'] = df['변동치'].apply(lambda x: "🔺" if x > 0 else ("🔻" if x < 0 else "—"))
        return df
    return pd.DataFrame(columns=['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    h1, h2, h3 { text-align: center; color: #002366; }
    .match-card { border: 1px solid #ddd; border-radius: 12px; padding: 15px; margin-bottom: 15px; background: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .vs-text { font-size: 1.2rem; font-weight: bold; color: #ff4b4b; text-align: center; display: block; padding-top: 10px; }
    .matrix-table { margin-bottom: 30px; }
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
                  menu_icon="cast", default_index=0, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 ---

if menu == "전체랭킹":
    st.markdown("<h1>🥇 전체 회원 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    st.dataframe(df[['랭킹', '상태', '성명', '4월 포인트', '부과점', '비고']], use_container_width=True, hide_index=True)

elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"🏆 {g}그룹" for g in groups])
        
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = m_df[m_df['그룹'] == g]
                
                # [추가] 상단 매트릭스 대진표
                st.markdown("### 📊 조별 대진표 (매트릭스)")
                players = sorted(list(set(g_df['팀A'].tolist() + g_df['팀B'].tolist())))
                matrix = pd.DataFrame("-", index=players, columns=players)
                for _, row in g_df.iterrows():
                    if row['완료'] == 1:
                        score = f"{int(row['A점수'])}:{int(row['B점수'])}"
                        matrix.at[row['팀A'], row['팀B']] = score
                        matrix.at[row['팀B'], row['팀A']] = f"{int(row['B점수'])}:{int(row['A점수'])}"
                st.table(matrix)
                
                st.divider()
                st.markdown("### 🎾 경기 순서 (2코트 동시 진행)")
                
                # 경기 카드 출력
                for idx, row in g_df.iterrows():
                    st.markdown("<div class='match-card'>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center; color:gray; font-weight:bold;'>MATCH {row['순서']}</p>", unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 3])
                    c1.markdown(f"<h3 style='text-align:right;'>{row['팀A']}</h3>", unsafe_allow_html=True)
                    s_a = c2.number_input("", 0, 10, int(row['A점수']), key=f"sA_{idx}", label_visibility="collapsed")
                    c3.markdown("<span class='vs-text'>VS</span>", unsafe_allow_html=True)
                    s_b = c4.number_input("", 0, 10, int(row['B점수']), key=f"sB_{idx}", label_visibility="collapsed")
                    c5.markdown(f"<h3 style='text-align:left;'>{row['팀B']}</h3>", unsafe_allow_html=True)
                    if st.button(f"결과 저장 (M-{row['순서']})", key=f"btn_{idx}", use_container_width=True):
                        m_df.loc[idx, ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                        save_data(m_df, MATCH_FILE); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "관리자 설정" and is_admin:
    # (앞선 로직 유지하며 대진 생성 알고리즘만 강화)
    st.markdown("<h1>⚙️ 관리자 설정</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📁 대회 관리", "⚔️ 참가자 및 대진 생성", "📈 결과 반영"])
    
    with t2:
        # ... (명단 및 그룹 설정 UI 생략 - 이전과 동일)
        if st.button("⚔️ 대진표 생성 (연속 경기 방지 로직 적용)"):
            # [핵심] 연속 경기 방지 알고리즘 적용 부분
            def optimize_order(matches):
                if not matches: return []
                ordered = [matches.pop(0)]
                while matches:
                    last_match = ordered[-1]
                    last_players = set(last_match['팀A'].split('/') + last_match['팀B'].split('/'))
                    
                    # 이전 경기와 겹치지 않는 경기 찾기
                    found = False
                    for i, m in enumerate(matches):
                        current_players = set(m['팀A'].split('/') + m['팀B'].split('/'))
                        if not (last_players & current_players):
                            ordered.append(matches.pop(i))
                            found = True
                            break
                    if not found: # 억지로라도 하나 넣기
                        ordered.append(matches.pop(0))
                return ordered

            # 위 함수를 사용하여 그룹별 matches 생성 후 저장...
