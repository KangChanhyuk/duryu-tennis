import streamlit as st
import pandas as pd
import os
import itertools
import random
import re
from streamlit_option_menu import option_menu

# --- 1. 초기 설정 및 데이터 로드 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        if '나이' not in df.columns: df['나이'] = 0
        return df
    return pd.DataFrame(columns=['랭킹', '성명', '나이', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 설정 (가운데 정렬 및 카드 디자인) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    .sub-title { text-align: center; color: #002366; margin-bottom: 30px; }
    .match-card { border: 2px solid #eee; border-radius: 15px; padding: 20px; margin-bottom: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .court-tag { background: #e1e8f5; color: #002366; padding: 3px 10px; border-radius: 5px; font-weight: bold; font-size: 0.8rem; }
    .vs-area { text-align: center; font-size: 1.8rem; font-weight: bold; color: #ff4b4b; }
    div[data-testid="stExpander"] div[role="button"] p { font-size: 1.2rem; font-weight: bold; text-align: center; width: 100%; }
    .matrix-table { width: 100%; border-collapse: collapse; text-align: center; }
    .matrix-table th, .matrix-table td { border: 1px solid #ddd; padding: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 메뉴 및 세션 관리 ---
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🎾 관리 메뉴</h2>", unsafe_allow_html=True)
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'play-circle', 'clipboard-data', 'gear'], 
                  menu_icon="cast", default_index=1, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# 세션 상태 초기화 (참가자 명단 보존용)
if 'raw_names' not in st.session_state: st.session_state.raw_names = ""

# --- 4. 핵심 로직: 2코트 최적화 배정 ---
def optimize_matches(match_list):
    if not match_list: return []
    ordered = [match_list.pop(0)]
    while match_list:
        last_players = set(re.split(r'[/]', ordered[-1][0]) + re.split(r'[/]', ordered[-1][1]))
        found = False
        for i, m in enumerate(match_list):
            curr_players = set(re.split(r'[/]', m[0]) + re.split(r'[/]', m[1]))
            if not (last_players & curr_players): # 중복 인원 없음
                ordered.append(match_list.pop(i))
                found = True; break
        if not found: ordered.append(match_list.pop(0))
    return ordered

# --- 5. 메뉴별 화면 구현 ---

if menu == "전체랭킹":
    st.markdown("<div class='main-title'>🥇 두류테니스클럽 랭킹</div>", unsafe_allow_html=True)
    st.dataframe(load_members().sort_values('랭킹'), use_container_width=True, hide_index=True)

elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"🏆 {g}그룹 대진표" for g in groups])
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = m_df[m_df['그룹'] == g]
                for idx, row in g_df.iterrows():
                    st.markdown(f"<div class='match-card'>", unsafe_allow_html=True)
                    c_info = "1번 코트" if idx % 2 == 0 else "2번 코트"
                    st.markdown(f"<span class='court-tag'>{c_info}</span> <span style='float:right; color:#888;'>Match {row['순서']}</span>", unsafe_allow_html=True)
                    col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 3])
                    col1.markdown(f"<h3 style='text-align:right;'>{row['팀A']}</h3>", unsafe_allow_html=True)
                    sA = col2.number_input("", 0, 10, int(row['A점수']), key=f"sA_{idx}_{g}", label_visibility="collapsed")
                    col3.markdown("<div class='vs-area'>VS</div>", unsafe_allow_html=True)
                    sB = col4.number_input("", 0, 10, int(row['B점수']), key=f"sB_{idx}_{g}", label_visibility="collapsed")
                    col5.markdown(f"<h3 style='text-align:left;'>{row['팀B']}</h3>", unsafe_allow_html=True)
                    if st.button(f"결과 저장 (M-{row['순서']})", key=f"save_{idx}_{g}", use_container_width=True):
                        m_df.loc[m_df['순서'] == row['순서'], ['A점수', 'B점수', '완료']] = [sA, sB, 1]
                        save_data(m_df, MATCH_FILE); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "경기 결과":
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        mem_df = load_members()
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"📊 {g}그룹 결과" for g in groups])
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = m_df[m_df['그룹'] == g]
                players = sorted(list(set(re.split(r'[/]', "/".join(g_df['팀A'].tolist() + g_df['팀B'].tolist())))))
                # (순위 계산 및 매트릭스 로직 - 이전과 동일하되 가운데 정렬 보강)
                st.markdown("<h2 style='text-align:center;'>🏆 최종 순위</h2>", unsafe_allow_html=True)
                # ... (순위 산정 코드)

elif menu == "관리자 설정" and is_admin:
    st.markdown("<div class='main-title'>⚙️ 대회 관리 시스템</div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["⚔️ 대진표 생성", "👤 참가자 체크/교체", "📝 회원 정보"])
    
    with t1:
        st.session_state.raw_names = st.text_area("1. 참가자 명단 입력 (쉼표 또는 줄바꿈)", value=st.session_state.raw_names)
        p_list = [n.strip() for n in re.split(r'[,\s\n]+', st.session_state.raw_names) if n.strip()]
        
        # 랭킹 데이터 불러와서 정렬
        all_mems = load_members()
        p_ranked = all_mems[all_mems['성명'].isin(p_list)].sort_values('랭킹')
        sorted_p = p_ranked['성명'].tolist() + [n for n in p_list if n not in p_ranked['성명'].tolist()]
        
        st.success(f"현재 인식된 참가자: {len(sorted_p)}명 (랭킹순 자동 정렬됨)")
        
        g_cnt = st.number_input("2. 그룹 수 설정", 1, 5, 1)
        configs, cur = [], 0
        for i in range(g_cnt):
            gl = chr(65 + i)
            st.markdown(f"**[{gl} 그룹 설정]**")
            c1, c2, c3 = st.columns([1, 1, 1])
            sz = c1.number_input(f"인원", 0, 50, key=f"sz_{gl}")
            md = c2.selectbox(f"방식", ["KDK 복식", "고정페어 복식", "단식"], key=f"md_{gl}")
            is_rnd = c3.checkbox("랜덤 셔플", value=True, key=f"rnd_{gl}")
            configs.append({'label': gl, 'members': sorted_p[cur:cur+sz], 'mode': md, 'random': is_rnd})
            cur += sz

        if st.button("⚔️ 2코트 최적화 대진표 생성", use_container_width=True):
            final_matches = []
            for cfg in configs:
                m_raw = []
                if cfg['mode'] == "KDK 복식":
                    combos = list(itertools.combinations(cfg['members'], 4))
                    if cfg['random']: random.shuffle(combos)
                    for c in combos:
                        p = list(c); random.shuffle(p)
                        m_raw.append((f"{p[0]}/{p[1]}", f"{p[2]}/{p[3]}"))
                elif cfg['mode'] == "고정페어 복식":
                    pairs = []
                    tmp = cfg['members'].copy()
                    while len(tmp) >= 2: pairs.append(f"{tmp.pop(0)}/{tmp.pop(-1)}")
                    m_raw = list(itertools.combinations(pairs, 2))
                else:
                    m_raw = list(itertools.combinations(cfg['members'], 2))
                
                if cfg['random']: random.shuffle(m_raw)
                # 2코트 동시 진행 최적화 적용
                optimized = optimize_matches(m_raw)
                for idx, m in enumerate(optimized):
                    final_matches.append({"그룹": cfg['label'], "순서": idx+1, "팀A": m[0], "팀B": m[1], "A점수": 0, "B점수": 0, "완료": 0})
            
            save_data(pd.DataFrame(final_matches), MATCH_FILE)
            st.balloons(); st.success("대진표가 생성되었습니다!")

    with t2:
        if MATCH_FILE:
            st.markdown("<h3 style='text-align:center;'>실시간 참가자 교체 및 확인</h3>", unsafe_allow_html=True)
            m_df = pd.read_csv(MATCH_FILE)
            all_ps = sorted(list(set(re.split(r'[/]', "/".join(m_df['팀A'].tolist() + m_df['팀B'].tolist())))))
            
            if st.checkbox("전체 선택/해제", value=True): pass
            
            for p in all_ps:
                c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
                c1.checkbox("", value=True, key=f"chk_m_{p}")
                c2.info(p)
                new_n = c3.text_input("변경 성명", value=p, key=f"edit_m_{p}", label_visibility="collapsed")
                if c4.button("교체", key=f"btn_m_{p}"):
                    m_df['팀A'] = m_df['팀A'].str.replace(p, new_n)
                    m_df['팀B'] = m_df['팀B'].str.replace(p, new_n)
                    save_data(m_df, MATCH_FILE); st.rerun()
