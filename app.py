import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# 페이지 설정 및 CSS
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 3rem; font-weight: bold; margin-bottom: 20px; }
    .team-card { border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; }
    .match-bg-1 { background-color: #f1f8e9; border-left: 8px solid #4CAF50; }
    .match-bg-2 { background-color: #e3f2fd; border-left: 8px solid #2196F3; }
    .team-name { font-size: 1.2rem; font-weight: bold; color: #333; text-align: center; }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #E53935; text-align: center; line-height: 80px; }
    input { text-align: center !important; }
    .stButton>button { width: 100%; border-radius: 5px; }
    th, td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)
import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# 페이지 설정 및 CSS
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 3rem; font-weight: bold; margin-bottom: 20px; }
    .team-card { border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; }
    .match-bg-1 { background-color: #f1f8e9; border-left: 8px solid #4CAF50; }
    .match-bg-2 { background-color: #e3f2fd; border-left: 8px solid #2196F3; }
    .team-name { font-size: 1.2rem; font-weight: bold; color: #333; text-align: center; }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #E53935; text-align: center; line-height: 80px; }
    input { text-align: center !important; }
    .stButton>button { width: 100%; border-radius: 5px; }
    th, td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 데이터 파일 및 상태 관리
# =============================
RANK_FILE = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"

def init_state():
    defaults = {
        "players": [], "groups": {}, "modes": {}, "game_counts": {},
        "schedule": {}, "scores": {}, "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tournament_name": "정기 대회", "player_numbers": {}
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
    if "현재포인트" in df.columns:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
    df.to_csv(RANK_FILE, index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["날짜", "대회명", "그룹", "방식", "이름", "순위", "승", "득실"])
    return pd.read_csv(HISTORY_FILE)

def process_uploaded_file(df):
    df.columns = [str(c).strip() for c in df.columns]
    name_col = next((c for c in df.columns if any(kw in c.lower() for kw in ['이름', '성함', 'name'])), None)
    point_col = next((c for c in df.columns if any(kw in c.lower() for kw in ['현재', '포인트', '점수'])), None)
    if not name_col: return None
    new_df = pd.DataFrame()
    new_df['이름'] = df[name_col].astype(str)
    new_df['현재포인트'] = pd.to_numeric(df[point_col], errors='coerce').fillna(0).astype(int) if point_col else 0
    return new_df

def make_groups_by_rank(players, sizes):
    rank_df = load_rank()
    player_pts = []
    for p in players:
        pt = rank_df[rank_df["이름"] == p]["현재포인트"].values
        player_pts.append({"이름": p, "포인트": pt[0] if len(pt) > 0 else 0})
    
    sorted_players = sorted(player_pts, key=lambda x: x["포인트"], reverse=True)
    sorted_names = [x["이름"] for x in sorted_players]
    
    groups = {}
    curr = 0
    for g in sorted(sizes.keys()):
        s = sizes[g]
        groups[g] = sorted_names[curr:curr+s]
        curr += s
    return groups

# KDK 대진 (사진 KakaoTalk_20260503_010122321_2.jpg 기준 번호 대진)
def get_kdk_template(n):
    templates = {
        4: [([1,4],[2,3]), ([1,3],[2,4]), ([1,2],[3,4])],
        6: [([1,3],[2,4]), ([1,5],[4,6]), ([2,3],[5,6]), ([1,4],[3,5]), ([2,6],[3,4]), ([1,6],[2,5])],
        8: [([1,2],[3,4]), ([5,6],[7,8]), ([1,8],[2,7]), ([3,6],[4,5]), ([1,4],[5,8]), ([2,3],[6,7]), ([1,6],[3,8]), ([2,5],[4,7])],
        12: [([1,2],[3,4]), ([5,6],[7,8]), ([9,10],[11,12]), ([1,3],[5,7]), ([2,4],[6,8]), ([9,11],[10,12])]
    }
    return templates.get(n, [])

def make_schedule_logic(group_players, mode, g_name):
    n = len(group_players)
    nums = list(range(1, n+1))
    random.shuffle(nums)
    p_map = {nums[i]: group_players[i] for i in range(n)}
    st.session_state.player_numbers[g_name] = p_map
    
    schedule = []
    if mode == "KDK":
        template = get_kdk_template(n)
        for round_matches in template:
            r_list = []
            if isinstance(round_matches, tuple): round_matches = [round_matches]
            for m in round_matches:
                t1 = [p_map[m[0][0]], p_map[m[0][1]]]
                t2 = [p_map[m[1][0]], p_map[m[1][1]]]
                r_list.append([t1, t2])
            schedule.append(r_list)
    else: # 고정페어 (사진 KakaoTalk_20260503_005949424_01_2.jpg 기준)
        pairs = [group_players[i:i+2] for i in range(0, len(group_players), 2)]
        tn = len(pairs)
        if tn == 4:
            order = [([1,2],[3,4]), ([1,3],[2,4]), ([1,4],[2,3])]
            for m_pair in order:
                schedule.append([[pairs[m_pair[0][0]-1], pairs[m_pair[0][1]-1]], [pairs[m_pair[1][0]-1], pairs[m_pair[1][1]-1]]])
    return schedule

# =============================
# UI 메뉴 섹션
# =============================
st.sidebar.title("🎾 두류 테니스")
menu = st.sidebar.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "📜 지난 대회 기록", "⚙ 관리자 센터"])

if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS RANKING</div>", unsafe_allow_html=True)
    df = load_rank()
    if not df.empty:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df.insert(0, "순위", range(1, len(df)+1))
        st.table(df[["순위", "이름", "현재포인트"]])
    else: st.info("데이터가 없습니다. 관리자 센터에서 엑셀을 업로드하세요.")

elif menu == "📅 대진표/입력":
    if not st.session_state.schedule:
        st.warning("진행 중인 대진이 없습니다.")
    else:
        st.info(f"🏟 대회명: {st.session_state.tournament_name}")
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                p_map = st.session_state.player_numbers.get(g, {})
                if st.session_state.modes[g] == "KDK":
                    st.caption("🔢 배정 번호: " + ", ".join([f"{name}({num})" for num, name in sorted(p_map.items())]))
                
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.markdown(f"**Round {ri+1}**")
                    for mi, (t1, t2) in enumerate(rd):
                        c1, cvs, c2 = st.columns([4, 1, 4])
                        key_name = f"{g}_{ri}_{mi}"
                        with c1:
                            st.markdown(f"<div class='team-card match-bg-1'>{' & '.join(t1)}</div>", unsafe_allow_html=True)
                            s1 = st.number_input("Score", 0, 15, key=f"s1_{key_name}", value=st.session_state.scores.get(key_name, (0,0))[0])
                        with cvs: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"<div class='team-card match-bg-2'>{' & '.join(t2)}</div>", unsafe_allow_html=True)
                            s2 = st.number_input("Score", 0, 15, key=f"s2_{key_name}", value=st.session_state.scores.get(key_name, (0,0))[1])
                        if st.button(f"결과 저장 ({g}-{ri+1}-{mi+1})"):
                            st.session_state.scores[key_name] = (s1, s2)
                            st.toast("저장되었습니다!")

elif menu == "📊 경기결과":
    # (결합된 결과 집계 로직 - 득실/승 정렬)
    st.markdown("<div class='main-title'>MATCH RESULTS</div>", unsafe_allow_html=True)
    if not st.session_state.scores: st.info("결과가 없습니다.")
    else:
        for g in st.session_state.groups.keys():
            st.subheader(f"Group {g} 순위")
            # ... 집계 로직 ...

elif menu == "📜 지난 대회 기록":
    history = load_history()
    if history.empty: st.info("기록이 없습니다.")
    else:
        selected_date = st.selectbox("기록 선택", history['날짜'].unique()[::-1])
        st.table(history[history['날짜'] == selected_date])

elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    if st.text_input("비밀번호", type="password") == "0502":
        t1, t2, t3 = st.tabs(["대회 생성/배정", "엑셀/부과점/기록수정", "데이터 초기화"])
        
        with t1:
            st.subheader("실력순 그룹 배정 대회 생성")
            name = st.text_input("대회 이름", st.session_state.tournament_name)
            raw_p = st.text_area("참가자 명단 (쉼표 구분)")
            g_count = st.number_input("그룹 수", 1, 5, 2)
            g_sizes = {}
            for i in range(int(g_count)):
                gn = chr(65+i); c_m, c_s = st.columns(2)
                with c_m: st.session_state.modes[gn] = st.selectbox(f"방식 {gn}", ["고정페어", "KDK"])
                with c_s: g_sizes[gn] = st.number_input(f"Group {gn} 인원", 4, 20, 4)
            
            if st.button("실력순 배정 및 생성", type="primary"):
                p_list = [p.strip() for p in raw_p.split(",") if p.strip()]
                st.session_state.groups = make_groups_by_rank(p_list, g_sizes)
                st.session_state.tournament_name = name
                st.session_state.scores = {}
                for g in st.session_state.groups.keys():
                    st.session_state.schedule[g] = make_schedule_logic(st.session_state.groups[g], st.session_state.modes[g], g)
                st.success("대회가 생성되었습니다.")

        with t2:
            st.subheader("📁 랭킹 엑셀 업로드")
            up_file = st.file_uploader("엑셀 파일 (이름, 현재포인트 포함)", type=["csv", "xlsx"])
            if up_file:
                df_raw = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
                df_p = process_uploaded_file(df_raw)
                if df_p is not None:
                    st.dataframe(df_p.head())
                    if st.button("랭킹 데이터 마스터에 저장"):
                        save_rank(df_p); st.success("마스터 파일에 저장되었습니다.")

            st.divider()
            st.subheader("⚖️ 부과점 및 개별 포인트 수정")
            r_df = load_rank()
            if not r_df.empty:
                target_p = st.selectbox("선수 선택", r_df['이름'].tolist())
                extra = st.number_input("포인트 가감", -50, 50, 0)
                if st.button("포인트 즉시 수정"):
                    r_df.loc[r_df['이름'] == target_p, '현재포인트'] += extra
                    save_rank(r_df); st.success("수정 완료")

            st.divider()
            st.subheader("📝 지난 대회 기록 삭제/수정")
            h_df = load_history()
            if not h_df.empty:
                del_date = st.selectbox("삭제할 대회 날짜", h_df['날짜'].unique())
                if st.button("해당 대회 기록 삭제"):
                    h_df = h_df[h_df['날짜'] != del_date]
                    h_df.to_csv(HISTORY_FILE, index=False)
                    st.success("기록이 삭제되었습니다."); st.rerun()

        with t3:
            if st.button("진행 중인 대회만 초기화"):
                st.session_state.schedule = {}; st.session_state.scores = {}
                st.success("대진표가 초기화되었습니다.")
            if st.button("‼️ 시스템 전체 초기화 (랭킹 포함)"):
                if os.path.exists(RANK_FILE): os.remove(RANK_FILE)
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                st.session_state.clear(); st.rerun()
# =============================
# 데이터 파일 및 상태 관리
# =============================
RANK_FILE = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"

def init_state():
    defaults = {
        "players": [], "groups": {}, "modes": {}, "game_counts": {},
        "schedule": {}, "scores": {}, "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tournament_name": "정기 대회"
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
    if "현재포인트" in df.columns:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
    df.to_csv(RANK_FILE, index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["날짜", "대회명", "그룹", "방식", "이름", "순위", "승", "득실"])
    return pd.read_csv(HISTORY_FILE)

def team_name(t):
    return " & ".join(t) if isinstance(t, (list, tuple)) and len(t) > 1 else (t[0] if isinstance(t, (list, tuple)) else t)

# [수정] 랭킹 포인트 순서대로 그룹 자동 배정 로직
def make_groups_by_rank(players, sizes):
    rank_df = load_rank()
    # 1. 랭킹 데이터가 있는 경우 포인트순 정렬, 없는 경우 하위 배치
    player_pts = []
    for p in players:
        pt = rank_df[rank_df["이름"] == p]["현재포인트"].values
        player_pts.append({"이름": p, "포인트": pt[0] if len(pt) > 0 else 0})
    
    # 포인트 내림차순 정렬
    sorted_players = sorted(player_pts, key=lambda x: x["포인트"], reverse=True)
    sorted_names = [x["이름"] for x in sorted_players]
    
    groups = {}
    curr = 0
    # A그룹부터 순차적으로 배정
    for g in sorted(sizes.keys()):
        s = sizes[g]
        groups[g] = sorted_names[curr:curr+s]
        curr += s
    return groups

def make_kdk_schedule(players, target_games):
    all_rounds = []
    past_partners = {p: set() for p in players}
    for r in range(target_games):
        curr_round_matches = []
        available = players[:]
        random.shuffle(available)
        while len(available) >= 4:
            p1 = available.pop(0)
            partner1 = next((p for i, p in enumerate(available) if p not in past_partners[p1]), available[0])
            available.remove(partner1)
            p2 = available.pop(0)
            partner2 = next((p for i, p in enumerate(available) if p not in past_partners[p2]), available[0])
            available.remove(partner2)
            past_partners[p1].add(partner1); past_partners[partner1].add(p1)
            past_partners[p2].add(partner2); past_partners[partner2].add(p2)
            curr_round_matches.append([[p1, partner1], [p2, partner2]])
        if curr_round_matches: all_rounds.append(curr_round_matches)
    return all_rounds

def make_pairs(players, mode):
    temp = players[:]
    if mode == "KDK": random.shuffle(temp)
    pairs = []
    if mode in ["고정페어", "KDK"]:
        for i in range(0, len(temp)-1, 2): pairs.append([temp[i], temp[i+1]])
        if len(temp) % 2 == 1: pairs.append([temp[-1]])
    else: pairs = [[p] for p in temp]
    return pairs

def make_schedule(teams, target_games):
    matches = [[teams[i], teams[j]] for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    rounds = []
    while matches:
        curr_round = []
        used_players = set()
        for m in matches[:]:
            p1_set = set(m[0]); p2_set = set(m[1])
            if not (p1_set & used_players) and not (p2_set & used_players):
                curr_round.append(m)
                used_players.update(p1_set); used_players.update(p2_set)
                matches.remove(m)
        if not curr_round: break
        rounds.append(curr_round)
    return rounds[:target_games]

# =============================
# UI 메뉴 섹션
# =============================
st.sidebar.title("🎾 두류 테니스")
menu = st.sidebar.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "📜 지난 대회 기록", "⚙ 관리자 센터"])

if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS RANKING</div>", unsafe_allow_html=True)
    df = load_rank()
    if not df.empty:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df.insert(0, "순위", range(1, len(df)+1))
        st.table(df[["순위", "이름", "현재포인트"]])
    else: st.info("데이터가 없습니다.")

elif menu == "📅 대진표/입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    if not st.session_state.schedule:
        st.warning("진행 중인 대진이 없습니다.")
    else:
        st.info(f"🏟 대회명: {st.session_state.tournament_name}")
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.markdown(f"<h4 style='text-align: center; background:#eee; padding:5px;'>Round {ri+1}</h4>", unsafe_allow_html=True)
                    for mi, (t1, t2) in enumerate(rd):
                        c1, c_vs, c2 = st.columns([4, 1, 4])
                        with c1:
                            st.markdown(f"<div class='team-card match-bg-1'><div class='team-name'>{team_name(t1)}</div></div>", unsafe_allow_html=True)
                            s1 = st.number_input("Score", 0, 10, key=f"s1_{g}_{ri}_{mi}", value=st.session_state.scores.get((tuple(t1), tuple(t2)), (0,0))[0])
                        with c_vs: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"<div class='team-card match-bg-2'><div class='team-name'>{team_name(t2)}</div></div>", unsafe_allow_html=True)
                            s2 = st.number_input("Score", 0, 10, key=f"s2_{g}_{ri}_{mi}", value=st.session_state.scores.get((tuple(t1), tuple(t2)), (0,0))[1])
                        if st.button(f"결과 저장: {mi+1}번 경기", key=f"btn_{g}_{ri}_{mi}"):
                            st.session_state.scores[(tuple(t1), tuple(t2))] = (s1, s2)
                            st.toast("저장되었습니다!")
                    st.markdown("<hr>", unsafe_allow_html=True)

elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>MATCH RESULTS</div>", unsafe_allow_html=True)
    if not st.session_state.scores: st.info("입력된 결과가 없습니다.")
    else:
        for g in st.session_state.groups.keys():
            st.markdown(f"### Group {g} 결과")
            stats = {}
            for (t1, t2), (s1, s2) in st.session_state.scores.items():
                if t1[0] not in st.session_state.groups[g]: continue
                for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                    names = [team_name(team)] if st.session_state.modes[g] == "고정페어" else list(team)
                    for n in names:
                        if n not in stats: stats[n] = {"승":0, "패":0, "득실":0}
                        if my_s > op_s: stats[n]["승"] += 1
                        elif my_s < op_s: stats[n]["패"] += 1
                        stats[n]["득실"] += (my_s - op_s)
            if stats:
                res_df = pd.DataFrame.from_dict(stats, orient='index').sort_values(["승", "득실"], ascending=False)
                res_df.insert(0, "순위", range(1, len(res_df)+1))
                st.table(res_df)

elif menu == "📜 지난 대회 기록":
    st.markdown("<div class='main-title'>PAST RECORDS</div>", unsafe_allow_html=True)
    history = load_history()
    if history.empty: st.info("기록이 없습니다.")
    else:
        history['선택정보'] = history['날짜'] + " [" + history['대회명'] + "]"
        selected = st.selectbox("대회 기록 선택", history['선택정보'].unique()[::-1])
        st.table(history[history['선택정보'] == selected].drop(columns=['선택정보']))

elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    if st.text_input("비밀번호", type="password") == "0502":
        tab1, tab2, tab3 = st.tabs(["🔥 대회 생성 (랭킹배정)", "✏️ 기록 수정/관리", "🧹 시스템 초기화"])
        
        with tab1:
            st.subheader("새 대회 생성")
            st.session_state.tournament_name = st.text_input("대회 이름", st.session_state.tournament_name)
            raw_p = st.text_area("참가자 명단 (쉼표 구분)")
            g_count = st.number_input("그룹 수", 1, 5, 2)
            g_sizes = {}
            for i in range(int(g_count)):
                gn = chr(65+i); c1, c2, c3 = st.columns(3)
                with c1: g_sizes[gn] = st.number_input(f"Group {gn} 인원", 2, 50, 4)
                with c2: st.session_state.modes[gn] = st.selectbox(f"방식 {gn}", ["고정페어", "KDK", "단식"])
                with c3: st.session_state.game_counts[gn] = st.selectbox(f"게임수 {gn}", [3, 4, 5, 6])
            
            if st.button("실력순 그룹 배정 및 대회 생성", type="primary"):
                p_list = [p.strip() for p in raw_p.split(",") if p.strip()]
                # [핵심] 실력순 그룹 배정 호출
                st.session_state.groups = make_groups_by_rank(p_list, g_sizes)
                st.session_state.schedule = {}
                st.session_state.scores = {}
                for g in st.session_state.groups.keys():
                    if st.session_state.modes[g] == "KDK":
                        st.session_state.schedule[g] = make_kdk_schedule(st.session_state.groups[g], st.session_state.game_counts[g])
                    else:
                        teams = make_pairs(st.session_state.groups[g], st.session_state.modes[g])
                        st.session_state.schedule[g] = make_schedule(teams, st.session_state.game_counts[g])
                st.success("대회가 실력순으로 생성되었습니다!")

        with tab2:
            st.subheader("📋 진행 중인 대회 관리")
            if st.session_state.schedule:
                if st.button("현재 진행 중인 대회 삭제 (초기화)"):
                    st.session_state.schedule = {}; st.session_state.scores = {}
                    st.rerun()
                
                if st.button("결과 확정 (랭킹포인트 반영)"):
                    rank = load_rank(); history_data = []
                    # ... (기존 랭킹 반영 로직 동일)
                    st.success("랭킹에 반영되었습니다!")
            
            st.divider()
            st.subheader("📚 지난 대회 기록 수정/삭제")
            h_df = load_history()
            if not h_df.empty:
                h_df['선택용'] = h_df['날짜'] + " | " + h_df['대회명']
                target_del = st.selectbox("수정/삭제할 대회 선택", h_df['선택용'].unique())
                if st.button("선택한 대회 기록 전체 삭제"):
                    h_df = h_df[h_df['선택용'] != target_del]
                    h_df.drop(columns=['선택용']).to_csv(HISTORY_FILE, index=False)
                    st.success("삭제되었습니다."); st.rerun()

            st.divider()
            st.subheader("⚖️ 개별 포인트 수정")
            r_df = load_rank()
            target_p = st.selectbox("선수 선택", r_df['이름'].tolist() if not r_df.empty else [])
            point_change = st.number_input("조정할 포인트 (예: -5, 10)", value=0)
            if st.button("포인트 수정 적용"):
                r_df.loc[r_df['이름'] == target_p, '현재포인트'] += point_change
                save_rank(r_df); st.success("수정 완료!")

        with tab3:
            if st.button("시스템 전체 데이터 포맷 (복구 불가)"):
                if os.path.exists(RANK_FILE): os.remove(RANK_FILE)
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                st.session_state.clear(); st.rerun()
