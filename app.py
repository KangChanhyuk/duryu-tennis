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
        return pd.read_csv(MEMBERS_FILE).fillna("")
    return pd.DataFrame(columns=['랭킹', '성명', '4월 포인트', '3월 포인트', '부과점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 설정 (긴 사선 배경 추가) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    h1, h2, h3 { text-align: center; color: #002366; }
    .match-card { border: 1px solid #ddd; border-radius: 12px; padding: 15px; margin-bottom: 15px; background: #ffffff; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .vs-text { font-size: 1.2rem; font-weight: bold; color: #ff4b4b; text-align: center; display: block; padding-top: 10px; }
    
    /* 매트릭스 테이블 스타일 */
    .matrix-table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; }
    .matrix-table th, .matrix-table td { border: 1px solid #ddd; padding: 12px; text-align: center; }
    .matrix-table th { background-color: #f8f9fa; font-weight: bold; }
    .matrix-header { background-color: #f8f9fa; font-weight: bold; width: 150px; }
    
    /* 칸 전체를 채우는 긴 사선 스타일 */
    .diagonal-line {
        background: linear-gradient(to top right, #fff 49.5%, #ccc 49.5%, #ccc 50.5%, #fff 50.5%);
    }
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
                players = sorted(list(set(g_df['팀A'].tolist() + g_df['팀B'].tolist())))
                
                # HTML 매트릭스 생성 (사선 스타일 포함)
                st.markdown("### 📊 조별 대진표 (매트릭스)")
                html = "<table class='matrix-table'><tr><th></th>"
                for p in players: html += f"<th>{p}</th>"
                html += "</tr>"
                
                for p1 in players:
                    html += f"<tr><td class='matrix-header'>{p1}</td>"
                    for p2 in players:
                        if p1 == p2:
                            html += "<td class='diagonal-line'></td>" # 긴 사선 적용
                        else:
                            # 경기 결과 찾기
                            match = g_df[((g_df['팀A']==p1) & (g_df['팀B']==p2)) | ((g_df['팀A']==p2) & (g_df['팀B']==p1))]
                            if not match.empty:
                                row = match.iloc[0]
                                if row['완료'] == 1:
                                    if row['팀A'] == p1: score = f"{int(row['A점수'])}:{int(row['B점수'])}"
                                    else: score = f"{int(row['B점수'])}:{int(row['A점수'])}"
                                    html += f"<td>{score}</td>"
                                else: html += "<td>•</td>"
                            else: html += "<td>-</td>"
                    html += "</tr>"
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)
                
                st.divider()
                st.markdown("### 🎾 경기 순서 (2코트 최적화)")
                for idx, row in g_df.iterrows():
                    st.markdown("<div class='match-card'>", unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 3])
                    c1.markdown(f"<h3 style='text-align:right;'>{row['팀A']}</h3>", unsafe_allow_html=True)
                    s_a = c2.number_input("", 0, 10, int(row['A점수']), key=f"sA_{idx}_{g}", label_visibility="collapsed")
                    c3.markdown("<span class='vs-text'>VS</span>", unsafe_allow_html=True)
                    s_b = c4.number_input("", 0, 10, int(row['B점수']), key=f"sB_{idx}_{g}", label_visibility="collapsed")
                    c5.markdown(f"<h3 style='text-align:left;'>{row['팀B']}</h3>", unsafe_allow_html=True)
                    if st.button(f"결과 저장 (M-{row['순서']})", key=f"btn_{idx}_{g}", use_container_width=True):
                        # 정확한 행 인덱스로 업데이트
                        actual_idx = g_df.index[g_df['순서'] == row['순서']][0]
                        m_df.loc[actual_idx, ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                        save_data(m_df, MATCH_FILE); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "관리자 설정" and is_admin:
    # ... (관리자 설정 로직은 이전과 동일하게 유지)
    st.markdown("<h1>⚙️ 관리자 설정</h1>", unsafe_allow_html=True)
    # (중략 - 이전 코드의 관리자 탭 내용 사용)
