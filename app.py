import streamlit as st
import pandas as pd
import os
import itertools
import random
import re
from streamlit_option_menu import option_menu

# --- 1. 데이터 관리 함수 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        # 나이 정보가 없을 경우를 대비해 기본값 0 세팅
        if '나이' not in df.columns: df['나이'] = 0
        return df
    return pd.DataFrame(columns=['랭킹', '성명', '나이', '4월 포인트', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 및 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    h1, h2, h3 { text-align: center; color: #002366; }
    .match-card { border: 2px solid #eee; border-radius: 12px; padding: 15px; margin-bottom: 15px; background: white; }
    .matrix-table { width: 100%; border-collapse: collapse; font-size: 13px; }
    .matrix-table th, .matrix-table td { border: 1px solid #ccc; padding: 8px; text-align: center; }
    .diagonal-line { background: linear-gradient(to top right, transparent 48%, #ddd 48%, #ddd 52%, transparent 52%); background-color: #f5f5f5; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 및 메인 메뉴 ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🎾 두류테니스</h2>", unsafe_allow_html=True)
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'play-circle', 'clipboard-data', 'gear'], 
                  menu_icon="cast", default_index=1, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 로직 ---

if menu == "전체랭킹":
    st.markdown("<h1>🥇 전체 회원 랭킹</h1>", unsafe_allow_html=True)
    st.dataframe(load_members().sort_values('랭킹'), use_container_width=True, hide_index=True)

elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"🏆 {g}그룹" for g in groups])
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = m_df[m_df['그룹'] == g]
                for idx, row in g_df.iterrows():
                    st.markdown(f"<div class='match-card'>", unsafe_allow_html=True)
                    st.write(f"**순서: M-{row['순서']}**")
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 3])
                    c1.markdown(f"<h3 style='text-align:right;'>{row['팀A']}</h3>", unsafe_allow_html=True)
                    s_a = c2.number_input("", 0, 15, int(row['A점수']), key=f"sA_{idx}_{g}", label_visibility="collapsed")
                    c3.markdown("<h3 style='text-align:center;'>:</h3>", unsafe_allow_html=True)
                    s_b = c4.number_input("", 0, 15, int(row['B점수']), key=f"sB_{idx}_{g}", label_visibility="collapsed")
                    c5.markdown(f"<h3 style='text-align:left;'>{row['팀B']}</h3>", unsafe_allow_html=True)
                    if st.button("결과 저장", key=f"btn_{idx}_{g}", use_container_width=True):
                        m_df.loc[m_df.index[m_df['순서'] == row['순서']][0], ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                        save_data(m_df, MATCH_FILE); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "경기 결과":
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        mem_df = load_members()
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"📊 {g}그룹 결과" for g in groups])
        
        for i, g in enumerate(tabs):
            with tabs[i]:
                g_df = m_df[m_df['그룹'] == groups[i]]
                teams = sorted(list(set(g_df['팀A'].tolist() + g_df['팀B'].tolist())))
                
                # 1. 매트릭스 출력
                html = "<table class='matrix-table'><tr><th></th>"
                for t in teams: html += f"<th>{t}</th>"
                html += "</tr>"
                for t1 in teams:
                    html += f"<tr><td style='font-weight:bold;'>{t1}</td>"
                    for t2 in teams:
                        if t1 == t2: html += "<td class='diagonal-line'></td>"
                        else:
                            m = g_df[((g_df['팀A']==t1) & (g_df['팀B']==t2)) | ((g_df['팀A']==t2) & (g_df['팀B']==t1))]
                            if not m.empty and m.iloc[0]['완료'] == 1:
                                row = m.iloc[0]
                                s = f"{int(row['A점수'])}:{int(row['B점수'])}" if row['팀A']==t1 else f"{int(row['B점수'])}:{int(row['A점수'])}"
                                html += f"<td>{s}</td>"
                            else: html += "<td>-</td>"
                    html += "</tr>"
                st.markdown(html + "</table>", unsafe_allow_html=True)

                # 2. 순위 계산 로직 (득실차, 나이 반영)
                st.markdown("### 🏆 최종 순위")
                result_data = []
                for t in teams:
                    # 해당 팀의 모든 경기 데이터
                    t_matches = g_df[((g_df['팀A'] == t) | (g_df['팀B'] == t)) & (g_df['완료'] == 1)]
                    wins, pts_for, pts_against = 0, 0, 0
                    for _, rm in t_matches.iterrows():
                        is_team_a = (rm['팀A'] == t)
                        my_score = rm['A점수'] if is_team_a else rm['B점수']
                        opp_score = rm['B점수'] if is_team_a else rm['A점수']
                        pts_for += my_score
                        pts_against += opp_score
                        if my_score > opp_score: wins += 1
                    
                    # 나이 합계 계산 (복식일 경우 두 명의 나이 합산)
                    names = re.split(r'[/]', t)
                    age_sum = sum([int(mem_df[mem_df['성명']==n]['나이'].values[0]) if n in mem_df['성명'].values else 0 for n in names])
                    
                    result_data.append({'팀': t, '승': wins, '득점': pts_for, '실점': pts_against, '득실차': pts_for - pts_against, '나이합': age_sum})
                
                res_df = pd.DataFrame(result_data).sort_values(by=['승', '득실차', '나이합'], ascending=[False, False, False])
                res_df.insert(0, '순위', range(1, len(res_df)+1))
                st.table(res_df)

elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 관리자 설정</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["대회/명단 관리", "대진표 작성", "나이/정보 수정"])
    
    with tab1:
        new_ev = st.text_input("새 대회 명칭")
        if st.button("대회 생성"): os.makedirs(os.path.join(DATA_DIR, new_ev), exist_ok=True); st.rerun()

    with tab2:
        raw_names = st.text_area("참가자 명단 (이름들 입력)")
        p_list = [n.strip() for n in re.split(r'[,\s\n]+', raw_names) if n.strip()]
        g_cnt = st.number_input("그룹 수", 1, 10, 1)
        configs, cur = [], 0
        for i in range(g_cnt):
            gl = chr(65 + i)
            c1, c2 = st.columns(2)
            sz = c1.number_input(f"{gl}그룹 인원", 0, 100, key=f"sz_{gl}")
            md = c2.selectbox(f"{gl} 방식", ["고정페어 복식", "KDK 복식", "단식"], key=f"md_{gl}")
            configs.append({'label': gl, 'members': p_list[cur:cur+sz], 'mode': md})
            cur += sz

        if st.button("⚔️ 대진표 생성"):
            all_m = []
            for cfg in configs:
                m_list = []
                if cfg['mode'] == "고정페어 복식":
                    # 실력순(랭킹순)으로 1위-꼴찌 매칭 로직 등 활용 가능
                    tmp = cfg['members'].copy()
                    pairs = []
                    while len(tmp) >= 2: pairs.append(f"{tmp.pop(0)}/{tmp.pop(-1)}")
                    m_list = list(itertools.combinations(pairs, 2))
                elif cfg['mode'] == "KDK 복식":
                    # 4명씩 랜덤 복식 매칭
                    combos = list(itertools.combinations(cfg['members'], 4))
                    random.shuffle(combos)
                    for c in combos:
                        p = list(c); random.shuffle(p)
                        m_list.append((f"{p[0]}/{p[1]}", f"{p[2]}/{p[3]}"))
                else: m_list = list(itertools.combinations(cfg['members'], 2))
                
                # 순서 최적화 (단순 랜덤 셔플 후 중복 최소화 배치)
                random.shuffle(m_list)
                for idx, c in enumerate(m_list):
                    all_m.append({"그룹": cfg['label'], "순서": idx+1, "팀A": c[0], "팀B": c[1], "A점수": 0, "B점수": 0, "완료": 0})
            save_data(pd.DataFrame(all_m), MATCH_FILE); st.success("대진 생성 완료!")

    with tab3:
        st.subheader("👤 참가자 나이 및 정보 수정")
        mdf = load_members()
        edited_df = st.data_editor(mdf, use_container_width=True, hide_index=True)
        if st.button("회원 정보 저장"):
            save_data(edited_df, MEMBERS_FILE); st.success("정보가 업데이트되었습니다.")
