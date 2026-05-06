import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime
import itertools

# =============================
# 페이지 설정 및 CSS
# =============================
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
    th, td { text-align: center !important; border: 1px solid #ddd !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 데이터 파일 및 상태 관리
# =============================
RANK_FILE = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"

# [image_e5bcba.jpg] 기반 한울방식 KDK 대진표 데이터
# A:10, B:11, C:12로 매핑
HANUL_KDK_DATA = {
    "3": { # 1인 3게임 기준
        4: ["14:23", "13:24", "12:34"],
        8: ["12:34", "56:78", "18:27", "36:45", "14:58", "23:67"],
        12: ["12:34", "56:78", "910:1112", "13:57", "24:68", "911:1012", "48:912", "67:1011", "1112:23"]
    },
    "4": { # 1인 4게임 기준
        5: ["12:34", "13:25", "14:35", "15:24", "23:45"],
        6: ["13:24", "15:46", "23:56", "14:35", "26:34", "16:25"],
        7: ["12:34", "56:17", "23:57", "14:67", "35:24", "16:25", "46:37"],
        8: ["12:34", "56:78", "13:57", "24:68", "15:26", "37:48", "16:38", "25:47"],
        9: ["12:34", "56:78", "19:57", "23:68", "49:38", "15:26", "36:45", "17:89", "24:79"],
        10: ["12:35", "67:810", "23:46", "78:19", "34:57", "89:210", "45:68", "13:910", "56:79", "110:24"],
        11: ["12:35", "67:810", "49:111", "23:68", "45:710", "911:26", "13:711", "48:59", "110:28", "47:611", "39:510"]
    }
}

def init_state():
    if "players" not in st.session_state: st.session_state.players = []
    if "groups" not in st.session_state: st.session_state.groups = {}
    if "modes" not in st.session_state: st.session_state.modes = {}
    if "game_counts" not in st.session_state: st.session_state.game_counts = {}
    if "schedule" not in st.session_state: st.session_state.schedule = {}
    if "scores" not in st.session_state: st.session_state.scores = {}
    if "current_date" not in st.session_state: st.session_state.current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
    if "tournament_name" not in st.session_state: st.session_state.tournament_name = "정기 대회"

init_state()

# =============================
# 유틸리티 함수
# =============================
def load_rank():
    if not os.path.exists(RANK_FILE): return pd.DataFrame(columns=["이름", "현재포인트"])
    df = pd.read_csv(RANK_FILE)
    df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors='coerce').fillna(0).astype(int)
    return df

def save_rank(df):
    df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
    df.to_csv(RANK_FILE, index=False)

def team_name(t, p_list=None):
    if isinstance(t, (list, tuple)):
        names = []
        for p in t:
            prefix = f"({p_list.index(p)+1})" if p_list and p in p_list else ""
            names.append(f"{prefix}{p}")
        return " & ".join(names)
    return str(t)

# =============================
# 대진 생성 로직 (한울방식 최적화)
# =============================
def make_kdk_hanul(players, target_games):
    n = len(players)
    key = str(target_games)
    if key in HANUL_KDK_DATA and n in HANUL_KDK_DATA[key]:
        shuffled_p = random.sample(players, n)
        match_strings = HANUL_KDK_DATA[key][n]
        rounds = []
        
        def parse_idx(s):
            res = []
            i = 0
            while i < len(s):
                if s[i:i+2] in ['10', '11', '12']:
                    res.append(int(s[i:i+2])-1); i += 2
                else:
                    res.append(int(s[i])-1); i += 1
            return res

        for ms in match_strings:
            t1_s, t2_s = ms.split(":")
            idx1, idx2 = parse_idx(t1_s), parse_idx(t2_s)
            match = [[shuffled_p[i] for i in idx1], [shuffled_p[i] for i in idx2]]
            rounds.append([match])
        return rounds
    return None

def make_round_robin(teams, target_games):
    matches = [[teams[i], teams[j]] for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    rounds = []
    while matches:
        curr_round = []; used = set()
        for m in matches[:]:
            p_in_m = set(m[0] + m[1])
            if not (p_in_m & used):
                curr_round.append(m); used.update(p_in_m); matches.remove(m)
        if not curr_round: break
        rounds.append(curr_round)
    return rounds

# =============================
# 매트릭스 UI 함수
# =============================
def draw_match_matrix(group_name):
    players = st.session_state.groups[group_name]
    mode = st.session_state.modes[group_name]
    group_scores = {k: v for k, v in st.session_state.scores.items() if k[0] == group_name}
    
    if mode == "고정페어":
        teams = []
        seen = set()
        for rd in st.session_state.schedule[group_name]:
            for m in rd:
                for t in [tuple(m[0]), tuple(m[1])]:
                    if t not in seen: teams.append(t); seen.add(t)
        entities = [" & ".join(t) for t in teams]
        entity_map = {t: " & ".join(t) for t in teams}
    else:
        entities = players
        entity_map = {tuple([p]): p for p in players}

    stats = {e: {"승":0, "패":0, "득실":0} for e in entities}
    matrix = {e: {other: "" for other in entities} for e in entities}

    for data in group_scores.values():
        t1, t2 = data["teams"]; s1, s2 = data["score"]
        e1 = entity_map.get(tuple(t1)) if mode=="고정페어" else t1[0]
        e2 = entity_map.get(tuple(t2)) if mode=="고정페어" else t2[0]

        for ent, op, my_s, op_s in [(e1, e2, s1, s2), (e2, e1, s2, s1)]:
            if ent in stats:
                if my_s > op_s: stats[ent]["승"] += 1
                elif my_s < op_s: stats[ent]["패"] += 1
                stats[ent]["득실"] += (my_s - op_s)
                matrix[ent][op] = f"{my_s}:{op_s}"

    st.subheader(f"📊 Group {group_name} 경기 현황 ({mode})")
    c1, c2 = st.columns([3, 2])
    with c1: st.dataframe(pd.DataFrame.from_dict(matrix, orient='index'))
    with c2: st.dataframe(pd.DataFrame.from_dict(stats, orient='index').sort_values(["승", "득실"], ascending=False))

# =============================
# 메인 메뉴
# =============================
st.sidebar.title("🎾 두류 테니스")
menu = st.sidebar.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "⚙ 관리자 센터"])

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
    if not st.session_state.schedule: st.warning("대진을 먼저 생성하세요.")
    else:
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                draw_match_matrix(g)
                st.divider()
                p_list = st.session_state.groups[g]
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.markdown(f"<div style='text-align:center; background:#eee; font-weight:bold;'>Round {ri+1}</div>", unsafe_allow_html=True)
                    for mi, (t1, t2) in enumerate(rd):
                        c1, cv, c2 = st.columns([4, 1, 4])
                        sk = (g, ri, mi)
                        score = st.session_state.scores.get(sk, {"score":(0,0)})["score"]
                        with c1:
                            st.markdown(f"<div class='team-card match-bg-1'>{team_name(t1, p_list)}</div>", unsafe_allow_html=True)
                            s1 = st.number_input("S1", 0, 10, score[0], key=f"s1_{g}_{ri}_{mi}", label_visibility="collapsed")
                        with cv: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"<div class='team-card match-bg-2'>{team_name(t2, p_list)}</div>", unsafe_allow_html=True)
                            s2 = st.number_input("S2", 0, 10, score[1], key=f"s2_{g}_{ri}_{mi}", label_visibility="collapsed")
                        if st.button(f"저장 {mi+1}", key=f"btn_{g}_{ri}_{mi}"):
                            st.session_state.scores[sk] = {"teams": (tuple(t1), tuple(t2)), "score": (s1, s2)}
                            st.rerun()

elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>MATCH RESULTS</div>", unsafe_allow_html=True)
    for g in st.session_state.groups.keys():
        st.markdown(f"### Group {g}")
        draw_match_matrix(g)

elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    if st.text_input("비밀번호", type="password") == "0502":
        st.session_state.tournament_name = st.text_input("대회명", st.session_state.tournament_name)
        raw_p = st.text_area("참가자 (쉼표 구분)")
        g_count = st.number_input("그룹 수", 1, 5, 1)
        configs = {}
        for i in range(g_count):
            gn = chr(65+i); col = st.columns(3)
            with col[0]: sz = st.number_input(f"{gn} 인원", 2, 20, 8)
            with col[1]: md = st.selectbox(f"{gn} 방식", ["KDK", "고정페어", "단식"], key=f"m_{gn}")
            with col[2]: gc = st.selectbox(f"{gn} 경기수", [3, 4], key=f"c_{gn}")
            configs[gn] = (sz, md, gc)
        
        if st.button("대진 생성", type="primary"):
            all_p = [p.strip() for p in raw_p.split(",") if p.strip()]
            if len(all_p) < sum(c[0] for c in configs.values()): st.error("인원 부족")
            else:
                curr = 0
                st.session_state.scores = {}
                for gn, (sz, md, gc) in configs.items():
                    gp = all_p[curr:curr+sz]
                    st.session_state.groups[gn] = gp
                    st.session_state.modes[gn] = md
                    if md == "KDK":
                        sched = make_kdk_hanul(gp, gc)
                        st.session_state.schedule[gn] = sched if sched else []
                    elif md == "고정페어":
                        teams = [gp[i:i+2] for i in range(0, len(gp), 2)]
                        st.session_state.schedule[gn] = make_round_robin(teams, gc)
                    else:
                        st.session_state.schedule[gn] = make_round_robin([[p] for p in gp], gc)
                    curr += sz
                st.success("생성 완료"); st.rerun()
