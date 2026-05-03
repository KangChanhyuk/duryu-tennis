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

# --- 2. 스타일 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main-title { text-align: center; color: #002366; font-size: 2.5rem; font-weight: bold; margin-bottom: 10px; }
    .match-card { border: 2px solid #eee; border-radius: 15px; padding: 20px; margin-bottom: 20px; background: white; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .vs-area { text-align: center; font-size: 1.8rem; font-weight: bold; color: #ff4b4b; }
    th, td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 로직 함수: 1인당 게임 수 기반 대진 생성 ---
def generate_matches_by_game_count(players, target_games, mode, is_random):
    match_list = []
    if len(players) < 2: return []
    
    if mode == "단식":
        # 모든 가능한 조합 생성 후 각자 목표 경기 수에 도달할 때까지 추출
        all_combos = list(itertools.combinations(players, 2))
        if is_random: random.shuffle(all_combos)
        
        play_counts = {p: 0 for p in players}
        for p1, p2 in all_combos:
            if play_counts[p1] < target_games and play_counts[p2] < target_games:
                match_list.append((p1, p2))
                play_counts[p1] += 1
                play_counts[p2] += 1
                
    else: # KDK 또는 복식 (4인 기준)
        if len(players) < 4: return []
        # KDK 로직: 파트너 조합 생성
        all_matches = []
        combos = list(itertools.combinations(players, 4))
        for c in combos:
            p = list(c)
            all_matches.append((f"{p[0]}/{p[1]}", f"{p[2]}/{p[3]}"))
            all_matches.append((f"{p[0]}/{p[2]}", f"{p[1]}/{p[3]}"))
            all_matches.append((f"{p[0]}/{p[3]}", f"{p[1]}/{p[2]}"))
        
        if is_random: random.shuffle(all_matches)
        
        play_counts = {p: 0 for p in players}
        for m1, m2 in all_matches:
            current_players = re.split(r'[/]', m1) + re.split(r'[/]', m2)
            # 모든 참여자가 목표 경기 수 미만인 경우만 추가
            if all(play_counts[p] < target_games for p in current_players):
                match_list.append((m1, m2))
                for p in current_players: play_counts[p] += 1
                
    return match_list

def optimize_matches(match_list):
    if not match_list: return []
    ordered = [match_list.pop(0)]
    for _ in range(len(match_list) * 2): # 충분히 반복
        if not match_list: break
        last_players = set(re.split(r'[/]', ordered[-1][0]) + re.split(r'[/]', ordered[-1][1]))
        found = False
        for i, m in enumerate(match_list):
            curr_players = set(re.split(r'[/]', m[0]) + re.split(r'[/]', m[1]))
            if not (last_players & curr_players):
                ordered.append(match_list.pop(i))
                found = True; break
        if not found: ordered.append(match_list.pop(0))
    return ordered

# --- 4. 메뉴 구성 ---
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

# --- 5. 관리자 설정 (핵심 변경 부분) ---
if menu == "관리자 설정" and is_admin:
    st.markdown("<div class='main-title'>⚙️ 대회 관리 시스템</div>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["⚔️ 대진표 생성", "👤 참가자 체크/교체", "📝 회원 정보"])
    
    with t1:
        if 'raw_names' not in st.session_state: st.session_state.raw_names = ""
        st.session_state.raw_names = st.text_area("1. 참가자 명단 입력", value=st.session_state.raw_names)
        p_list = [n.strip() for n in re.split(r'[,\s\n]+', st.session_state.raw_names) if n.strip()]
        
        all_mems = load_members()
        p_ranked = all_mems[all_mems['성명'].isin(p_list)].sort_values('랭킹')
        sorted_p = p_ranked['성명'].tolist() + [n for n in p_list if n not in p_ranked['성명'].tolist()]
        
        st.info(f"참가자: {len(sorted_p)}명 (랭킹순 정렬됨)")
        
        g_cnt = st.number_input("2. 그룹 수 설정", 1, 5, 1)
        configs, cur = [], 0
        for i in range(g_cnt):
            gl = chr(65 + i)
            st.markdown(f"**[{gl} 그룹 설정]**")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 1])
            sz = c1.number_input(f"인원", 0, 50, key=f"sz_{gl}")
            md = c2.selectbox(f"방식", ["KDK 복식", "단식"], key=f"md_{gl}")
            target = c3.selectbox(f"1인당 경기수", [3, 4, 5], key=f"tg_{gl}")
            is_rnd = c4.checkbox("랜덤", value=True, key=f"rnd_{gl}")
            configs.append({'label': gl, 'members': sorted_p[cur:cur+sz], 'mode': md, 'target': target, 'random': is_rnd})
            cur += sz

        if st.button("⚔️ 1인당 경기수 맞춤형 대진 생성", use_container_width=True):
            final_rows = []
            for cfg in configs:
                m_list = generate_matches_by_game_count(cfg['members'], cfg['target'], cfg['mode'], cfg['random'])
                optimized = optimize_matches(m_list)
                for idx, m in enumerate(optimized):
                    final_rows.append({"그룹": cfg['label'], "순서": idx+1, "팀A": m[0], "팀B": m[1], "A점수": 0, "B점수": 0, "완료": 0})
            
            if final_rows:
                save_data(pd.DataFrame(final_rows), MATCH_FILE)
                st.success("대진표 생성 완료! (각 인원별 경기수 최적화)")
                st.rerun()

# --- (나머지 메뉴 '대진 및 경기현황', '경기 결과' 등은 이전 코드와 동일하게 유지) ---
elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        # (기존의 카드 형태 출력 로직 실행)
        for idx, row in m_df.iterrows():
             st.markdown(f"<div class='match-card'> ... </div>", unsafe_allow_html=True)
             # 중략...
