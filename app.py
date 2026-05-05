import streamlit as st
import pandas as pd
import random
import os

# 페이지 설정 및 CSS
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 3rem; font-weight: bold; margin-bottom: 20px; }
    .team-card {
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
        text-align: center;
    }
    .match-bg-1 { background-color: #f1f8e9; border-left: 8px solid #4CAF50; }
    .match-bg-2 { background-color: #e3f2fd; border-left: 8px solid #2196F3; }
    
    .team-name { font-size: 1.2rem; font-weight: bold; color: #333; text-align: center; }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #E53935; text-align: center; line-height: 80px; }
    
    input { text-align: center !important; }
    .stButton>button { width: 100%; border-radius: 5px; }
    
    /* 표와 모든 텍스트 중앙 정렬 */
    .stDataFrame, .stTable, [data-testid="stTable"] { 
        display: flex; justify-content: center; text-align: center !important; 
    }
    th, td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 데이터 파일 및 상태 관리
# =============================
RANK_FILE = "ranking_master.csv"

def init_state():
    defaults = {
        "players": [], "groups": {}, "modes": {}, "game_counts": {},
        "schedule": {}, "scores": {}, "is_admin": False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_state()

# =============================
# 핵심 로직 함수
# =============================
def load_rank():
    if not os.path.exists(RANK_FILE):
        return pd.DataFrame(columns=["이름", "현재포인트"])
    df = pd.read_csv(RANK_FILE)
    if "현재포인트" in df.columns:
        df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors='coerce').fillna(0).astype(int)
    return df

def save_rank(df):
    df.to_csv(RANK_FILE, index=False)

def team_name(t):
    return " & ".join(t) if len(t) > 1 else t[0]

def process_uploaded_file(df):
    df.columns = [str(c).strip() for c in df.columns]
    mapping = {}
    for c in df.columns:
        c_lower = c.lower()
        if any(kw in c_lower for kw in ['이름', '성함', 'name', '선수명']):
            mapping[c] = '이름'
        elif any(kw in c_lower for kw in ['현재', '포인트', '점수', 'point', '랭킹']):
            mapping[c] = '현재포인트'
            
    if '이름' not in mapping.values():
        return None
    
    df = df.rename(columns=mapping)
    if '현재포인트' not in df.columns:
        df['현재포인트'] = 0
    else:
        df['현재포인트'] = pd.to_numeric(df['현재포인트'], errors='coerce').fillna(0).astype(int)
    
    return df

def make_groups(players, sizes):
    rank_df = load_rank()
    if not rank_df.empty and '이름' in rank_df.columns:
        rank_order = rank_df.sort_values("현재포인트", ascending=False)["이름"].tolist()
        ordered = [p for p in rank_order if p in players] + [p for p in players if p not in rank_order]
    else:
        ordered = players
    groups = {}
    curr = 0
    for g, s in sizes.items():
        groups[g] = ordered[curr:curr+s]
        curr += s
    return groups

def make_pairs(players, mode):
    temp = players[:]
    if mode == "KDK": random.shuffle(temp)
    pairs = []
    if mode in ["고정페어", "KDK"]:
        for i in range(0, len(temp)-1, 2): pairs.append((temp[i], temp[i+1]))
        if len(temp) % 2 == 1: pairs.append((temp[-1],))
    else: pairs = [(p,) for p in temp]
    return pairs

def make_schedule(teams, target_games):
    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    rounds = []
    while matches:
        curr_round = []
        used_players = set()
        for m in matches[:]:
            if not (set(m[0]) & used_players) and not (set(m[1]) & used_players):
                curr_round.append(m)
                used_players.update(m[0]); used_players.update(m[1])
                matches.remove(m)
        if not curr_round: break
        rounds.append(curr_round)
    return rounds[:target_games]

# =============================
# UI 메뉴 섹션
# =============================
st.sidebar.title("🎾 두류 테니스")
menu = st.sidebar.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "⚙ 관리자 센터"])

if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS RANKING</div>", unsafe_allow_html=True)
    df = load_rank()
    if not df.empty:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df.insert(0, "순위", range(1, len(df)+1))
        st.table(df)
    else:
        st.info("데이터가 없습니다. 관리자 센터에서 엑셀을 업로드해주세요.")

elif menu == "📅 대진표/입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    if not st.session_state.schedule:
        st.warning("대진이 없습니다. 관리자 페이지에서 대회를 생성하세요.")
    else:
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.markdown(f"<h4 style='text-align: center;'>Round {ri+1}</h4>", unsafe_allow_html=True)
                    for i, (t1, t2) in enumerate(rd):
                        bg_class = "match-bg-1" if i % 2 == 0 else "match-bg-2"
                        with st.container():
                            c1, c_vs, c2 = st.columns([4, 1, 4])
                            with c1:
                                st.markdown(f"<div class='team-card {bg_class}'><div class='team-name'>{team_name(t1)}</div></div>", unsafe_allow_html=True)
                                s1 = st.number_input("Score", 0, 10, key=f"s1_{g}_{ri}_{i}", label_visibility="collapsed")
                            with c_vs:
                                st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<div class='team-card {bg_class}'><div class='team-name'>{team_name(t2)}</div></div>", unsafe_allow_html=True)
                                s2 = st.number_input("Score", 0, 10, key=f"s2_{g}_{ri}_{i}", label_visibility="collapsed")
                            
                            if st.button(f"결과 저장: {team_name(t1)} vs {team_name(t2)}", key=f"btn_{g}_{ri}_{i}"):
                                st.session_state.scores[(t1, t2)] = (s1, s2)
                                st.success("저장되었습니다!")
                        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>MATCH RESULTS</div>", unsafe_allow_html=True)
    if not st.session_state.scores:
        st.info("입력된 결과가 없습니다.")
    else:
        for g in st.session_state.groups.keys():
            st.markdown(f"<h3 style='text-align: center;'>Group {g} 결과</h3>", unsafe_allow_html=True)
            stats = {}
            for (t1, t2), (s1, s2) in st.session_state.scores.items():
                if t1[0] not in st.session_state.groups[g]: continue
                for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                    names = [team_name(team)] if st.session_state.modes[g] == "고정페어" else team
                    for n in names:
                        if n not in stats: stats[n] = {"승":0, "패":0, "득실":0}
                        if my_s > op_s: stats[n]["승"] += 1
                        elif my_s < op_s: stats[n]["패"] += 1
                        stats[n]["득실"] += (my_s - op_s)
            res_df = pd.DataFrame.from_dict(stats, orient='index').sort_values(["승", "득실"], ascending=False)
            res_df.insert(0, "순위", range(1, len(res_df)+1))
            st.table(res_df)

elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    pw = st.text_input("비밀번호", type="password")
    
    if pw == "0502":
        tab1, tab2, tab3 = st.tabs(["대회 생성", "랭킹 데이터 관리", "시스템 초기화"])
        
        with tab1:
            raw_p = st.text_area("참가자 (쉼표 구분)", help="홍길동, 김철수 형식으로 입력")
            g_count = st.number_input("그룹 수", 1, 10, 2)
            g_sizes = {}
            for i in range(int(g_count)):
                gn = chr(65+i)
                col1, col2, col3 = st.columns(3)
                with col1: g_sizes[gn] = st.number_input(f"Group {gn} 인원", 2, 100, 4)
                with col2: st.session_state.modes[gn] = st.selectbox(f"방식 {gn}", ["KDK", "고정페어", "단식"])
                with col3: st.session_state.game_counts[gn] = st.selectbox(f"게임수 {gn}", [3, 4, 5, 6])
            
            if st.button("대회 생성 및 대진표 확정", type="primary"):
                st.session_state.players = [p.strip() for p in raw_p.split(",") if p.strip()]
                st.session_state.groups = make_groups(st.session_state.players, g_sizes)
                for g in st.session_state.groups.keys():
                    teams = make_pairs(st.session_state.groups[g], st.session_state.modes[g])
                    st.session_state.schedule[g] = make_schedule(teams, st.session_state.game_counts[g])
                st.success("대진표 생성이 완료되었습니다.")

        with tab2:
            st.subheader("📁 엑셀 업로드 (랭킹 갱신)")
            up_file = st.file_uploader("파일 업로드", type=["csv", "xlsx"])
            if up_file:
                try:
                    df_raw = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
                    df_processed = process_uploaded_file(df_raw)
                    if df_processed is not None:
                        st.dataframe(df_processed.head(5))
                        if st.button("업로드 데이터로 랭킹 즉시 저장"):
                            save_rank(df_processed)
                            st.success("랭킹이 업데이트되었습니다! '🏆 랭킹보드'에서 확인하세요.")
                    else:
                        st.error("'이름' 컬럼을 찾을 수 없습니다.")
                except Exception as e:
                    st.error(f"파일 처리 중 오류 발생: {e}")

            st.divider()
            st.subheader("📝 오늘 경기 결과 승점 반영")
            st.info("고정페어: 1위(7점), 2위(5점), 3위(3점), 나머지(1점)\nKDK/단식: 1-2위(7점), 3-4위(5점), 5-6위(3점), 나머지(1점)")
            
            if st.button("경기 결과에 따른 승점 확정 및 저장"):
                rank = load_rank()
                update_count = 0
                
                for g in st.session_state.groups.keys():
                    stats = {}
                    # 특정 그룹에 속한 선수들만 필터링하여 순위 계산
                    for (t1, t2), (s1, s2) in st.session_state.scores.items():
                        if t1[0] not in st.session_state.groups[g]: continue
                        for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                            for n in team:
                                if n not in stats: stats[n] = {"승":0, "득실":0}
                                if my_s > op_s: stats[n]["승"] += 1
                                stats[n]["득실"] += (my_s - op_s)
                    
                    # 순위 정렬
                    sorted_players = sorted(stats.items(), key=lambda x: (x[1]['승'], x[1]['득실']), reverse=True)
                    
                    mode = st.session_state.modes[g]
                    for idx, (p_name, _) in enumerate(sorted_players):
                        rank_pos = idx + 1
                        points = 1 # 기본 1점
                        
                        if mode == "고정페어":
                            if rank_pos == 1: points = 7
                            elif rank_pos == 2: points = 5
                            elif rank_pos == 3: points = 3
                        else: # KDK, 단식
                            if rank_pos <= 2: points = 7
                            elif rank_pos <= 4: points = 5
                            elif rank_pos <= 6: points = 3
                        
                        if p_name in rank["이름"].values:
                            rank.loc[rank["이름"] == p_name, "현재포인트"] += points
                            update_count += 1
                            
                save_rank(rank)
                st.success(f"총 {update_count}명의 선수에게 승점이 반영되었습니다.")

        with tab3:
            if st.button("전체 데이터 초기화"):
                if os.path.exists(RANK_FILE): os.remove(RANK_FILE)
                st.session_state.clear()
                init_state()
                st.rerun()
