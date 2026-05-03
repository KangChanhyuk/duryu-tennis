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

# --- 2. 스타일 설정 (매트릭스 사선 및 카드 디자인) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    h1, h2, h3 { text-align: center; color: #002366; }
    .match-card { border: 2px solid #eee; border-radius: 15px; padding: 20px; margin-bottom: 20px; background: #ffffff; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #ff4b4b; text-align: center; display: block; }
    .matrix-table { width: 100%; border-collapse: collapse; margin: 20px 0; background: white; font-size: 14px; }
    .matrix-table th, .matrix-table td { border: 1px solid #ccc; padding: 10px; text-align: center; height: 50px; }
    .matrix-table th { background-color: #f1f3f5; }
    .diagonal-line {
        background: linear-gradient(to top right, transparent 48%, #999 48%, #999 52%, transparent 52%);
        background-color: #f9f9f9;
    }
    .court-label { background: #002366; color: white; padding: 2px 10px; border-radius: 5px; font-size: 0.8rem; }
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
                
                # 매트릭스 출력
                st.markdown("### 📊 조별 대진표 (매트릭스)")
                html = "<table class='matrix-table'><tr><th></th>"
                for p in players: html += f"<th>{p}</th>"
                html += "</tr>"
                for p1 in players:
                    html += f"<tr><td style='font-weight:bold; background:#f8f9fa;'>{p1}</td>"
                    for p2 in players:
                        if p1 == p2: html += "<td class='diagonal-line'></td>"
                        else:
                            match = g_df[((g_df['팀A']==p1) & (g_df['팀B']==p2)) | ((g_df['팀A']==p2) & (g_df['팀B']==p1))]
                            if not match.empty:
                                row = match.iloc[0]
                                if row['완료'] == 1:
                                    s = f"{int(row['A점수'])}:{int(row['B점수'])}" if row['팀A'] == p1 else f"{int(row['B점수'])}:{int(row['A점수'])}"
                                    html += f"<td style='background:#e7f3ff; font-weight:bold;'>{s}</td>"
                                else: html += "<td>•</td>"
                            else: html += "<td>-</td>"
                    html += "</tr>"
                st.markdown(html + "</table>", unsafe_allow_html=True)
                
                st.divider()
                st.markdown("### 🎾 경기 순서 (2코트 동시 진행 최적화)")
                # 경기 카드 출력
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
                        m_df.loc[m_df.index[m_df['순서'] == row['순서']], ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                        save_data(m_df, MATCH_FILE); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 관리자 설정</h1>", unsafe_allow_html=True)
    t1, t2 = st.tabs(["📁 대회 관리", "⚔️ 대진 생성"])
    
    with t2:
        raw_names = st.text_area("명단 붙여넣기 (쉼표/공백/엔터)")
        p_list = [n.strip() for n in re.split(r'[,\s\n]+', raw_names) if n.strip()]
        all_mems = load_members()
        p_ranked = all_mems[all_mems['성명'].isin(p_list)].sort_values('랭킹')
        final_p = p_ranked['성명'].tolist() + [n for n in p_list if n not in p_ranked['성명'].tolist()]
        
        g_cnt = st.number_input("그룹 수", 1, 10, 1)
        configs = []
        cur = 0
        for i in range(g_cnt):
            g_label = chr(65 + i)
            col1, col2 = st.columns(2)
            sz = col1.number_input(f"{g_label}그룹 인원", 0, len(final_p), key=f"sz_{g_label}")
            md = col2.selectbox(f"{g_label} 방식", ["고정페어 복식", "단식", "KDK 복식"], key=f"md_{g_label}")
            configs.append({'label': g_label, 'members': final_p[cur:cur+sz], 'mode': md})
            cur += sz

        if st.button("⚔️ 2코트 최적화 대진 생성"):
            if not MATCH_FILE: st.error("대회를 먼저 선택하세요."); st.stop()
            all_m = []
            for cfg in configs:
                # 1. 원시 대진 생성
                if cfg['mode'] == "고정페어 복식":
                    pairs, tmp = [], cfg['members'].copy()
                    while len(tmp) >= 2: pairs.append(f"{tmp.pop(0)}/{tmp.pop(-1)}")
                    raw = list(itertools.combinations(pairs, 2))
                else: raw = list(itertools.combinations(cfg['members'], 2))
                
                # 2. 2코트 동시 경기 최적화 알고리즘
                random.shuffle(raw)
                ordered = []
                while raw:
                    m1 = raw.pop(0)
                    ordered.append(m1)
                    if not raw: break
                    
                    # m1에 참여한 모든 인원 추출
                    m1_players = set(re.split(r'[/]', m1[0]) + re.split(r'[/]', m1[1]))
                    
                    # m1 인원과 겹치지 않는 경기 찾기 (2번 코트용)
                    found_idx = -1
                    for i, m2 in enumerate(raw):
                        m2_players = set(re.split(r'[/]', m2[0]) + re.split(r'[/]', m2[1]))
                        if not (m1_players & m2_players):
                            found_idx = i
                            break
                    
                    if found_idx != -1: ordered.append(raw.pop(found_idx))
                    else: ordered.append(raw.pop(0)) # 어쩔 수 없이 겹치는 경우
                
                for idx, c in enumerate(ordered):
                    all_m.append({"그룹": cfg['label'], "순서": idx+1, "팀A": c[0], "팀B": c[1], "A점수": 0, "B점수": 0, "완료": 0})
            
            save_data(pd.DataFrame(all_m), MATCH_FILE); st.success("2코트 최 최적화 대진 생성 완료!"); st.balloons()
