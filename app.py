import streamlit as st
import pandas as pd
import random
import os
import json
from datetime import datetime

# ============================================================
# 페이지 설정
# ============================================================
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹", page_icon="🎾")

# ============================================================
# CSS - 밝고 시원한 테니스 테마
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;500;700;900&display=swap');

:root {
    --sky: #e8f4fd;
    --court-blue: #1565c0;
    --court-blue-light: #1e88e5;
    --court-teal: #00838f;
    --court-green: #2e7d32;
    --accent-yellow: #f9a825;
    --accent-orange: #e65100;
    --white: #ffffff;
    --bg-main: #f0f7ff;
    --bg-card: #ffffff;
    --bg-card2: #f5faff;
    --text-dark: #0d2137;
    --text-mid: #37474f;
    --text-light: #78909c;
    --border: #b0d4f1;
    --border-light: #daeaf8;
    --green-team: #e8f5e9;
    --green-border: #66bb6a;
    --red-team: #fce4ec;
    --red-border: #ef9a9a;
    --shadow: 0 2px 12px rgba(21,101,192,0.10);
    --shadow-hover: 0 6px 24px rgba(21,101,192,0.18);
}

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: var(--bg-main) !important;
    color: var(--text-dark) !important;
}
.stApp {
    background: linear-gradient(160deg, #e8f4fd 0%, #f0f7ff 50%, #e8f5e9 100%) !important;
    min-height: 100vh;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d47a1 0%, #1565c0 40%, #0277bd 100%) !important;
    border-right: none !important;
    box-shadow: 4px 0 20px rgba(21,101,192,0.25) !important;
}
[data-testid="stSidebar"] * { color: #ffffff !important; }
[data-testid="stSidebar"] .stRadio > div { gap: 4px !important; }
[data-testid="stSidebar"] .stRadio label {
    padding: 10px 16px; border-radius: 10px; cursor: pointer;
    transition: all 0.2s; margin-bottom: 3px; display: block;
    border: 1px solid rgba(255,255,255,0.15);
    color: rgba(255,255,255,0.9) !important;
    font-size: 0.9rem;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.18) !important;
    border-color: rgba(255,255,255,0.4) !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb] {
    background: rgba(255,255,255,0.22) !important;
}

/* ── 타이틀 ── */
.main-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.6rem;
    letter-spacing: 0.14em;
    color: var(--court-blue);
    text-align: center;
    padding: 8px 0 2px;
    text-shadow: 0 2px 8px rgba(21,101,192,0.15);
    line-height: 1.1;
}
.sub-title {
    text-align: center;
    color: var(--text-light);
    font-size: 0.82rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    margin-bottom: 28px;
}

/* ── 공통 카드 ── */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 16px;
    padding: 20px 24px;
    margin-bottom: 14px;
    box-shadow: var(--shadow);
}
.card-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.3rem;
    letter-spacing: 0.1em;
    color: var(--court-blue);
    margin-bottom: 14px;
    border-bottom: 2px solid var(--border-light);
    padding-bottom: 8px;
}

/* ── 랭킹 ── */
.rank-row {
    display: flex; align-items: center; padding: 13px 18px;
    border-radius: 12px; margin-bottom: 8px;
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    box-shadow: var(--shadow);
    transition: all 0.18s;
}
.rank-row:hover { transform: translateX(5px); box-shadow: var(--shadow-hover); }
.rank-num {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.7rem;
    color: var(--text-light); width: 48px; text-align: center;
}
.rank-num.top1 { color: #f9a825; font-size: 2.1rem; }
.rank-num.top2 { color: #90a4ae; font-size: 2rem; }
.rank-num.top3 { color: #a1887f; font-size: 1.9rem; }
.rank-name { flex: 1; font-size: 1.05rem; font-weight: 700; padding: 0 16px; color: var(--text-dark); }
.rank-pts { font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem; color: var(--court-blue); }
.rank-pts-label { color: var(--text-light); font-size: 0.68rem; text-align: right; }

/* ── 대진표 매치 카드 ── */
.match-wrapper {
    background: var(--bg-card);
    border: 1px solid var(--border-light);
    border-radius: 14px;
    padding: 0;
    margin-bottom: 10px;
    box-shadow: var(--shadow);
    overflow: hidden;
}
.match-inner {
    display: grid;
    grid-template-columns: 1fr 70px 1fr;
    align-items: stretch;
}
.team-box {
    padding: 14px 16px;
    text-align: center;
    display: flex; flex-direction: column; justify-content: center;
    min-height: 80px;
}
.team-box-a { background: var(--green-team); border-right: 1px solid var(--border-light); }
.team-box-b { background: var(--red-team);   border-left:  1px solid var(--border-light); }
.team-label {
    font-size: 0.62rem; letter-spacing: 0.22em;
    color: var(--text-light); text-transform: uppercase; margin-bottom: 5px;
}
.team-players {
    font-size: 1.05rem; font-weight: 800;
    color: var(--text-dark);
    line-height: 1.35;
    word-break: keep-all;
}
.team-num {
    font-size: 0.75rem; font-weight: 400;
    color: var(--text-light); margin-top: 2px;
}
.vs-center {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    background: linear-gradient(180deg, #e3f2fd, #f8fbff);
}
.vs-text {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.5rem; color: var(--accent-orange);
    line-height: 1;
}
.score-saved {
    font-size: 0.75rem; font-weight: 700;
    color: var(--court-blue); margin-top: 3px;
}

/* ── 라운드 헤더 ── */
.round-header {
    background: linear-gradient(90deg, var(--court-blue), var(--court-blue-light), transparent);
    padding: 8px 18px; border-radius: 8px;
    font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem;
    letter-spacing: 0.15em; color: #ffffff;
    margin: 20px 0 10px;
}

/* ── 배지 ── */
.stat-badge {
    display: inline-block; padding: 3px 11px;
    border-radius: 20px; font-size: 0.78rem; font-weight: 600; margin: 2px;
}
.badge-win   { background: #e8f5e9; color: #2e7d32; border: 1px solid #a5d6a7; }
.badge-lose  { background: #fce4ec; color: #c62828; border: 1px solid #ef9a9a; }
.badge-diff  { background: #e3f2fd; color: #1565c0; border: 1px solid #90caf9; }
.badge-pts   { background: #fff8e1; color: #f57f17; border: 1px solid #ffe082; }
.badge-gold  { background: #fff8e1; color: #f57f17; border: 2px solid #f9a825; font-weight: 800; }
.badge-silver{ background: #eceff1; color: #546e7a; border: 2px solid #90a4ae; font-weight: 800; }
.badge-bronze{ background: #fbe9e7; color: #bf360c; border: 2px solid #ffab91; font-weight: 800; }

/* ── 결과표 그룹 배지 ── */
.result-champion { background: linear-gradient(90deg,#fff8e1,#fffde7); border-left: 5px solid #f9a825; }
.result-runner   { background: linear-gradient(90deg,#eceff1,#f5f5f5); border-left: 5px solid #90a4ae; }
.result-third    { background: linear-gradient(90deg,#fbe9e7,#fff3e0); border-left: 5px solid #ffab91; }

/* ── 매트릭스 셀 ── */
.matrix-table { width:100%; border-collapse: collapse; font-size:0.85rem; text-align:center; }
.matrix-table th {
    background: var(--court-blue); color: white;
    padding: 7px 10px; font-weight: 600;
    border: 1px solid var(--border);
}
.matrix-table td {
    padding: 7px 10px; border: 1px solid var(--border-light);
    text-align: center; vertical-align: middle;
}
.matrix-table td.self     { background: #e0e0e0; color: #9e9e9e; }
.matrix-table td.win      { background: #e8f5e9; color: #2e7d32; font-weight: 700; }
.matrix-table td.lose     { background: #fce4ec; color: #c62828; font-weight: 700; }
.matrix-table td.draw     { background: #fff8e1; color: #f57f17; font-weight: 700; }
.matrix-table td.empty    { background: #f5f5f5; color: #bdbdbd; }
.matrix-table tr.header-row th:first-child { min-width: 100px; }

/* ── 순위표 ── */
.rank-table { width:100%; border-collapse: collapse; font-size:0.88rem; }
.rank-table th {
    background: var(--court-blue); color: white;
    padding: 8px 12px; font-weight: 600; text-align: center;
    border: 1px solid var(--border);
}
.rank-table td {
    padding: 8px 12px; border: 1px solid var(--border-light);
    text-align: center; vertical-align: middle;
}
.rank-table tr:nth-child(even) td { background: #f5faff; }
.rank-table tr:hover td { background: #e3f2fd; }
.rank-table td.rank-medal { font-size: 1.1rem; font-weight: 700; }

/* ── 정보 박스 ── */
.info-box {
    background: linear-gradient(135deg, #e3f2fd, #e8f5e9);
    border: 1px solid var(--border);
    border-left: 4px solid var(--court-blue-light);
    border-radius: 10px; padding: 14px 18px; margin-bottom: 14px;
}
.info-box p { color: var(--text-mid); margin: 3px 0; font-size: 0.88rem; }
.info-box strong { color: var(--text-dark); }

/* ── 버튼 ── */
.stButton > button {
    background: linear-gradient(135deg, var(--court-blue-light), var(--court-blue)) !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 10px !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    font-weight: 600 !important;
    font-size: 0.9rem !important;
    transition: all 0.2s !important;
    box-shadow: 0 3px 10px rgba(21,101,192,0.25) !important;
    padding: 8px 16px !important;
}
.stButton > button:hover {
    background: linear-gradient(135deg, var(--court-blue), #0d47a1) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 18px rgba(21,101,192,0.35) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--accent-orange), #bf360c) !important;
    box-shadow: 0 4px 14px rgba(230,81,0,0.35) !important;
}

/* ── 폼 ── */
.stTextInput input, .stTextArea textarea, .stNumberInput input {
    background: var(--bg-card) !important;
    border: 1.5px solid var(--border) !important;
    color: var(--text-dark) !important;
    border-radius: 8px !important;
}
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: var(--court-blue-light) !important;
    box-shadow: 0 0 0 2px rgba(30,136,229,0.15) !important;
}
div[data-baseweb="select"] > div {
    background: var(--bg-card) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-dark) !important;
}

/* ── 탭 ── */
div[data-testid="stTab"] button { color: var(--text-mid) !important; font-weight: 600 !important; }
div[data-testid="stTab"] button[aria-selected="true"] {
    color: var(--court-blue) !important;
    border-bottom-color: var(--court-blue) !important;
}

/* ── 알림 ── */
.stSuccess > div { background: #e8f5e9 !important; color: #2e7d32 !important; border-radius: 10px !important; border: 1px solid #a5d6a7 !important; }
.stWarning > div { background: #fff8e1 !important; color: #f57f17 !important; border-radius: 10px !important; border: 1px solid #ffe082 !important; }
.stError   > div { background: #fce4ec !important; color: #c62828 !important; border-radius: 10px !important; border: 1px solid #ef9a9a !important; }
.stInfo    > div { background: #e3f2fd !important; color: #1565c0 !important; border-radius: 10px !important; border: 1px solid #90caf9 !important; }

/* ── 구분선 ── */
hr { border-color: var(--border-light) !important; }

/* ── 스크롤바 ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-main); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 상수 및 파일 경로
# ============================================================
RANK_FILE    = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"
MATCHES_DIR  = "matches"          

POINT_TABLE = {1: 100, 2: 80, 3: 65, 4: 55, 5: 45, 6: 37, 7: 30, 8: 24,
               9: 20, 10: 16, 11: 13, 12: 10}

KDK_TABLE = {
    4: { 3: [["12:34"], ["13:24"], ["14:23"]], },
    6: { 4: [["13:24"], ["15:46"], ["23:56"], ["14:35"], ["26:34"], ["16:25"]], },
    8: {
        3: [["12:34","56:78"], ["18:27","36:45"], ["14:58","23:67"]],
        4: [["12:34","56:78"], ["13:57","24:68"], ["15:26","37:48"], ["16:38","25:47"]],
    },
    10: {
        4: [ ["12:35","67:810"], ["23:46","78:910"], ["34:57","89:110"], ["45:68","910:12"], ["56:79","110:23"] ],
    },
    12: {
        4: [ ["12:34","56:78","910:1112"], ["13:57","24:68","911:1012"], ["48:912","67:1011","1112:23"], ["15:26","37:48","910:1112"], ["16:27","38:49","1011:1112"] ],
    },
}

# ============================================================
# 세션 상태 초기화
# ============================================================
def init_state():
    defaults = {
        "groups": {}, "modes": {}, "game_counts": {},
        "shuffled_players": {}, "schedule": {}, "scores": {},
        "tournament_name": "정기 대회",
        "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "admin_authed": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# ============================================================
# 대진표 관련 함수
# ============================================================
def smart_split(s, n):
    res = []
    i = 0
    while i < len(s):
        two = s[i:i+2]
        if len(two) == 2 and two.isdigit() and 10 <= int(two) <= n:
            res.append(int(two)); i += 2
        elif s[i].isdigit():
            res.append(int(s[i])); i += 1
        else:
            i += 1
    return res

def parse_match_str(ms, shuffled):
    n = len(shuffled)
    if ':' not in ms: return None
    l, r = ms.split(':')
    li = smart_split(l, n)
    ri = smart_split(r, n)
    t1 = [shuffled[i-1] for i in li if 1 <= i <= n]
    t2 = [shuffled[i-1] for i in ri if 1 <= i <= n]
    return [t1, t2] if t1 and t2 else None

def distribute_groups(p_list, g_configs):
    groups = {}
    g_names = list(g_configs.keys())
    g_sizes = [g_configs[gn][0] for gn in g_names]
    total = sum(g_sizes)
    players = p_list[:total]
    filled = {gn: [] for gn in g_names}
    player_ptr = 0
    max_sz = max(g_sizes)
    for r in range(max_sz):
        order = g_names if r % 2 == 0 else list(reversed(g_names))
        for gn in order:
            if len(filled[gn]) < g_configs[gn][0] and player_ptr < len(players):
                filled[gn].append(players[player_ptr])
                player_ptr += 1
    for gn in g_names:
        gp = filled[gn]
        md = g_configs[gn][1]
        if md == "고정페어":
            paired = []
            lo, hi = 0, len(gp) - 1
            while lo < hi:
                paired.extend([gp[lo], gp[hi]])
                lo += 1; hi -= 1
            if lo == hi: paired.append(gp[lo])
            groups[gn] = paired
        else:
            shuffled = gp[:]
            random.shuffle(shuffled)
            groups[gn] = shuffled
    return groups

def make_kdk_schedule(players, target_games):
    n = len(players)
    shuffled = players[:]
    if n in KDK_TABLE and target_games in KDK_TABLE[n]:
        rounds_raw = KDK_TABLE[n][target_games]
        schedule = []
        for round_strs in rounds_raw:
            rnd = []
            for ms in round_strs:
                m = parse_match_str(ms, shuffled)
                if m: rnd.append(m)
            if rnd: schedule.append(rnd)
        return schedule, shuffled
    used_pairs = set()
    all_combos = []
    for i in range(n):
        for j in range(i+1, n):
            for k in range(n):
                for l in range(k+1, n):
                    if not {i,j} & {k,l}: all_combos.append((i,j,k,l))
    random.shuffle(all_combos)
    schedule = []
    num_courts = max(1, n // 4)
    for _ in range(target_games):
        rnd = []
        used_in_round = set()
        for combo in all_combos:
            i,j,k,l = combo
            if any(x in used_in_round for x in [i,j,k,l]): continue
            p1 = tuple(sorted([i,j])); p2 = tuple(sorted([k,l]))
            if p1 in used_pairs or p2 in used_pairs: continue
            rnd.append([[shuffled[i],shuffled[j]],[shuffled[k],shuffled[l]]])
            used_in_round.update([i,j,k,l])
            used_pairs.add(p1); used_pairs.add(p2)
            if len(rnd) >= num_courts: break
        if rnd: schedule.append(rnd)
    return schedule, shuffled

def make_round_robin(teams):
    matches = [[teams[i], teams[j]] for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    rounds = []
    while matches:
        rnd, used, remaining = [], set(), []
        for m in matches:
            ps = set(str(p) for p in m[0]+m[1])
            if not ps & used: rnd.append(m); used |= ps
            else: remaining.append(m)
        if rnd: rounds.append(rnd)
        if not rnd: break
        matches = remaining
    return rounds

# ============================================================
# 저장 및 관리
# ============================================================
def ensure_dir():
    if not os.path.exists(MATCHES_DIR): os.makedirs(MATCHES_DIR)

def tournament_path(name):
    safe = name.replace("/","_").replace("\\","_").replace(" ","_")
    return os.path.join(MATCHES_DIR, f"{safe}.json")

def save_tournament(name):
    ensure_dir()
    data = {
        "name": name, "date": st.session_state.current_date,
        "groups": st.session_state.groups, "modes": st.session_state.modes,
        "game_counts": st.session_state.game_counts,
        "shuffled_players": st.session_state.shuffled_players,
        "schedule_raw": {}, "scores_raw": []
    }
    for g, rds in st.session_state.schedule.items():
        data["schedule_raw"][g] = []
        for rd in rds:
            data["schedule_raw"][g].append([{"t1": t1, "t2": t2} for t1, t2 in rd])
    for k, v in st.session_state.scores.items():
        data["scores_raw"].append({ "key": list(k), "teams": [list(v["teams"][0]), list(v["teams"][1])], "score": list(v["score"]) })
    with open(tournament_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_tournament(name):
    path = tournament_path(name)
    if not os.path.exists(path): return False
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    st.session_state.tournament_name = data["name"]
    st.session_state.current_date = data.get("date","")
    st.session_state.groups = data["groups"]
    st.session_state.modes = data["modes"]
    st.session_state.game_counts = data.get("game_counts", {})
    st.session_state.shuffled_players = data.get("shuffled_players", {})
    sched = {}
    for g, rds in data.get("schedule_raw",{}).items():
        sched[g] = [[(m["t1"], m["t2"]) for m in rd] for rd in rds]
    st.session_state.schedule = sched
    scores = {}
    for item in data.get("scores_raw",[]):
        k = tuple(item["key"])
        scores[k] = { "teams": (tuple(item["teams"][0]), tuple(item["teams"][1])), "score": tuple(item["score"]) }
    st.session_state.scores = scores
    return True

def list_tournaments():
    ensure_dir()
    files = [f for f in os.listdir(MATCHES_DIR) if f.endswith(".json")]
    names = []
    for f in files:
        try:
            with open(os.path.join(MATCHES_DIR,f),"r",encoding="utf-8") as fp:
                names.append(json.load(fp).get("name","?"))
        except: pass
    return names

def delete_tournament(name):
    path = tournament_path(name)
    if os.path.exists(path): os.remove(path)

# ============================================================
# 데이터 로드
# ============================================================
def load_rank():
    if not os.path.exists(RANK_FILE): return pd.DataFrame(columns=["이름","현재포인트","총경기","총승","총득실"])
    df = pd.read_csv(RANK_FILE)
    for col in ["현재포인트","총경기","총승","총득실"]:
        if col not in df.columns: df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df

def save_rank(df):
    df.sort_values("현재포인트", ascending=False).reset_index(drop=True).to_csv(RANK_FILE, index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE): return pd.DataFrame(columns=["날짜","대회명","그룹","방식","이름","등급","승","득실","획득포인트"])
    return pd.read_csv(HISTORY_FILE)

def save_history(df): df.to_csv(HISTORY_FILE, index=False)

def calc_stats(group_name):
    players = st.session_state.groups[group_name]
    stats = {p: {"승":0,"패":0,"득실":0,"총득점":0} for p in players}
    for key, data in st.session_state.scores.items():
        if key[0] != group_name: continue
        t1, t2, s1, s2 = list(data["teams"][0]), list(data["teams"][1]), data["score"][0], data["score"][1]
        if s1 == 0 and s2 == 0: continue
        for team, ms, os_ in [(t1,s1,s2),(t2,s2,s1)]:
            for p in team:
                if p in stats:
                    if ms > os_: stats[p]["승"] += 1
                    elif ms < os_: stats[p]["패"] += 1
                    stats[p]["득실"] += (ms - os_)
                    stats[p]["총득점"] += ms
    return sorted(stats.items(), key=lambda x:(x[1]["승"],x[1]["득실"],x[1]["총득점"]), reverse=True)

def get_result_grade(rank, mode):
    if mode == "고정페어":
        if rank == 1: return "🥇 우승"
        if rank == 2: return "🥈 준우승"
        if rank == 3: return "🥉 3위"
        return f"{rank}위"
    if rank <= 2: return "🥇 우승"
    if rank <= 4: return "🥈 준우승"
    if rank <= 6: return "🥉 3위"
    return f"{rank}위"

def grade_sort_key(grade):
    if "🥇" in grade: return 1
    if "🥈" in grade: return 2
    if "🥉" in grade: return 3
    try: return int(grade.replace("위","")) + 3
    except: return 99

# ============================================================
# 렌더링 함수
# ============================================================
def render_matrix(group_name):
    players = st.session_state.groups[group_name]
    mode = st.session_state.modes[group_name]
    shuffled = st.session_state.shuffled_players.get(group_name, players)
    
    st.markdown(f"""
    <div style='background:linear-gradient(90deg,#1565c0,#1e88e5,#00838f);
         border-radius:12px; padding:12px 20px; margin-bottom:16px;
         display:flex; align-items:center; gap:14px;'>
      <span style='font-family:Bebas Neue,sans-serif;font-size:1.6rem;color:#fff;letter-spacing:0.12em;'>
        GROUP {group_name}
      </span>
      <span style='background:rgba(255,255,255,0.25);color:#fff;padding:3px 12px;
           border-radius:20px;font-size:0.8rem;font-weight:600;'>{mode}</span>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([5, 3])
    with col1:
        st.markdown("**📋 상대별 전적 매트릭스**")
        if mode == "고정페어":
            teams_list, seen = [], set()
            for rd in st.session_state.schedule[group_name]:
                for t1, t2 in rd:
                    for t in [tuple(t1), tuple(t2)]:
                        if t not in seen: teams_list.append(t); seen.add(t)
            team_labels = {t: " & ".join(t) for t in teams_list}
            labels_list = [team_labels[t] for t in teams_list]
            score_map = {}
            for key, data in st.session_state.scores.items():
                if key[0] != group_name: continue
                t1k, t2k, s1, s2 = tuple(data["teams"][0]), tuple(data["teams"][1]), data["score"][0], data["score"][1]
                if s1==0 and s2==0: continue
                k1, k2 = team_labels.get(t1k), team_labels.get(t2k)
                if k1 and k2: score_map[(k1,k2)], score_map[(k2,k1)] = (s1,s2), (s2,s1)
            html = "<table class='matrix-table'><tr class='header-row'><th>팀</th>" + "".join(f"<th>{lb}</th>" for lb in labels_list) + "</tr>"
            for lb_r in labels_list:
                html += f"<tr><th style='text-align:left;padding-left:10px;'>{lb_r}</th>"
                for lb_c in labels_list:
                    if lb_r == lb_c: html += "<td class='self'>■</td>"
                    elif (lb_r, lb_c) in score_map:
                        s1, s2 = score_map[(lb_r,lb_c)]
                        css = "win" if s1>s2 else ("lose" if s1<s2 else "draw")
                        html += f"<td class='{css}'>{s1}:{s2}</td>"
                    else: html += "<td class='empty'>-</td>"
                html += "</tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
        else:
            score_map = {}
            for key, data in st.session_state.scores.items():
                if key[0] != group_name: continue
                t1, t2, s1, s2 = list(data["teams"][0]), list(data["teams"][1]), data["score"][0], data["score"][1]
                if s1==0 and s2==0: continue
                for p1 in t1:
                    for p2 in t2: score_map[(p1,p2)], score_map[(p2,p1)] = (s1,s2), (s2,s1)
            html = "<table class='matrix-table'><tr class='header-row'><th>선수</th>" + "".join(f"<th>({shuffled.index(p)+1}){p}</th>" for p in players) + "</tr>"
            for pr in players:
                html += f"<tr><th style='text-align:left;padding-left:10px;'>({shuffled.index(pr)+1}){pr}</th>"
                for pc in players:
                    if pr == pc: html += "<td class='self'>■</td>"
                    elif (pr, pc) in score_map:
                        s1, s2 = score_map[(pr,pc)]
                        css = "win" if s1>s2 else ("lose" if s1<s2 else "draw")
                        html += f"<td class='{css}'>{s1}:{s2}</td>"
                    else: html += "<td class='empty'>-</td>"
                html += "</tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

    with col2:
        st.markdown("**🏅 현재 순위**")
        if mode == "고정페어":
            teams_u, seen2 = [], set()
            for rd in st.session_state.schedule[group_name]:
                for t1, t2 in rd:
                    for t in [tuple(t1), tuple(t2)]:
                        if t not in seen2: teams_u.append(t); seen2.add(t)
            t_stats = {t: {"승":0,"패":0,"득실":0,"총득점":0} for t in teams_u}
            for key, data in st.session_state.scores.items():
                if key[0] != group_name: continue
                t1k, t2k, s1, s2 = tuple(data["teams"][0]), tuple(data["teams"][1]), data["score"][0], data["score"][1]
                if s1==0 and s2==0: continue
                for tk, ms, os_ in [(t1k,s1,s2),(t2k,s2,s1)]:
                    if tk in t_stats:
                        if ms>os_: t_stats[tk]["승"]+=1
                        elif ms<os_: t_stats[tk]["패"]+=1
                        t_stats[tk]["득실"]+=(ms-os_); t_stats[tk]["총득점"]+=ms
            sorted_t = sorted(t_stats.items(), key=lambda x:(x[1]["승"],x[1]["득실"],x[1]["총득점"]), reverse=True)
            html = "<table class='rank-table'><tr><th>순위</th><th>팀</th><th>승</th><th>패</th><th>득실</th></tr>"
            for rank,(t,s) in enumerate(sorted_t,1):
                medal = ["🥇","🥈","🥉"][rank-1] if rank<=3 else f"{rank}"
                html += f"<tr><td class='rank-medal'>{medal}</td><td>{' & '.join(t)}</td><td>{s['승']}</td><td>{s['패']}</td><td>{s['득실']:+d}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)
        else:
            sorted_p = calc_stats(group_name)
            html = "<table class='rank-table'><tr><th>순위</th><th>번호</th><th>선수</th><th>승</th><th>패</th><th>득실</th></tr>"
            for rank,(name,s) in enumerate(sorted_p,1):
                medal = ["🥇","🥈","🥉"][rank-1] if rank<=3 else f"{rank}"
                html += f"<tr><td class='rank-medal'>{medal}</td><td>No.{shuffled.index(name)+1}</td><td>{name}</td><td>{s['승']}</td><td>{s['패']}</td><td>{s['득실']:+d}</td></tr>"
            st.markdown(html + "</table>", unsafe_allow_html=True)

def render_schedule(group_name):
    shuffled = st.session_state.shuffled_players.get(group_name, st.session_state.groups[group_name])
    for ri, rd in enumerate(st.session_state.schedule[group_name]):
        st.markdown(f"<div class='round-header'>◆ ROUND {ri+1}</div>", unsafe_allow_html=True)
        for mi, (t1, t2) in enumerate(rd):
            t1, t2 = list(t1), list(t2)
            score_key = (group_name, ri, mi)
            existing = st.session_state.scores.get(score_key, {"score":(0,0)})["score"]
            saved_str = f"{existing[0]}:{existing[1]}" if sum(existing)>0 else ""
            st.markdown(f"""
            <div class='match-wrapper'><div class='match-inner'>
                <div class='team-box team-box-a'><div class='team-label'>Team A</div><div class='team-players'>{' & '.join(t1)}</div><div class='team-num'>{" ".join([f"No.{shuffled.index(p)+1}" for p in t1])}</div></div>
                <div class='vs-center'><div class='vs-text'>VS</div>{f"<div class='score-saved'>{saved_str}</div>" if saved_str else ""}</div>
                <div class='team-box team-box-b'><div class='team-label'>Team B</div><div class='team-players'>{' & '.join(t2)}</div><div class='team-num'>{" ".join([f"No.{shuffled.index(p)+1}" for p in t2])}</div></div>
            </div></div>
            """, unsafe_allow_html=True)
            ci1, ci2, _, ci4, ci5 = st.columns([2,1,0.4,1,1.2])
            s1 = ci1.number_input(f"A", 0, 10, existing[0], key=f"s1_{group_name}_{ri}_{mi}", label_visibility="collapsed")
            ci2.markdown("<div style='text-align:center;padding-top:8px;color:#90a4ae;font-weight:700;'>:</div>", unsafe_allow_html=True)
            s2 = ci4.number_input(f"B", 0, 10, existing[1], key=f"s2_{group_name}_{ri}_{mi}", label_visibility="collapsed")
            if ci5.button(f"💾 저장", key=f"save_{group_name}_{ri}_{mi}"):
                st.session_state.scores[score_key] = {"teams": (tuple(t1), tuple(t2)), "score": (s1, s2)}
                st.success("저장됨"); st.rerun()

# ============================================================
# 메인 로직
# ============================================================
st.sidebar.markdown("<div style='text-align:center;padding:20px 0 12px;'><div style='font-family:Bebas Neue,sans-serif;font-size:2.2rem;color:#fff;letter-spacing:0.12em;line-height:1;'>두류 테니스</div></div>", unsafe_allow_html=True)
menu = st.sidebar.radio("메뉴", ["🏆 랭킹보드", "📅 대진표 / 점수입력", "📊 경기결과 & 정산", "📜 대회 기록", "⚙️ 관리자 센터"], label_visibility="collapsed")

if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS</div><div class='sub-title'>PLAYER RANKING BOARD</div>", unsafe_allow_html=True)
    df = load_rank()
    if df.empty: st.info("선수가 없습니다.")
    else:
        top_n = min(3, len(df))
        cols = st.columns(top_n)
        for i in range(top_n):
            row = df.iloc[i]
            cols[i].markdown(f"<div style='background:#fff8e1;border:2px solid #f9a825;border-radius:16px;padding:22px 16px;text-align:center;'><h3>{['🥇','🥈','🥉'][i]} {row['이름']}</h3><h2>{row['현재포인트']}</h2></div>", unsafe_allow_html=True)
        for i, row in df.iterrows():
            st.markdown(f"<div class='rank-row'><div class='rank-num'>{i+1}</div><div class='rank-name'>{row['이름']}</div><div class='rank-pts'>{row['현재포인트']} pts</div></div>", unsafe_allow_html=True)

elif menu == "📅 대진표 / 점수입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    if not st.session_state.schedule: st.warning("대진표가 없습니다.")
    else:
        tabs = st.tabs([f" Group {g} " for g in st.session_state.schedule.keys()])
        for i, g in enumerate(st.session_state.schedule.keys()):
            with tabs[i]: render_matrix(g); st.divider(); render_schedule(g)
        if st.button("💾 전체 저장", type="primary"): save_tournament(st.session_state.tournament_name); st.success("저장 완료")

elif menu == "📊 경기결과 & 정산":
    st.markdown("<div class='main-title'>RESULTS & POINTS</div>", unsafe_allow_html=True)
    if not st.session_state.schedule: st.warning("데이터가 없습니다.")
    else:
        for g in st.session_state.schedule.keys():
            st.subheader(f"Group {g}")
            stats = calc_stats(g)
            for rank, (name, s) in enumerate(stats, 1):
                st.write(f"{rank}위: {name} ({s['승']}승 {s['패']}패, 득실 {s['득실']}) +{POINT_TABLE.get(rank, 5)}pt")
        if st.button("✅ 랭킹 반영", type="primary"): st.success("정산 완료(예시)"); st.balloons()

elif menu == "📜 대회 기록":
    st.markdown("<div class='main-title'>HISTORY</div>", unsafe_allow_html=True)
    st.write(load_history())

elif menu == "⚙️ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN</div>", unsafe_allow_html=True)
    if not st.session_state.admin_authed:
        if st.text_input("PW", type="password") == "0502": st.session_state.admin_authed = True; st.rerun()
    else:
        if st.button("로그아웃"): st.session_state.admin_authed = False; st.rerun()
        t_name = st.text_input("대회명", st.session_state.tournament_name)
        raw_p = st.text_area("참가자(쉼표 구분)")
        if st.button("대진표 생성"):
            p_list = [p.strip() for p in raw_p.split(",") if p.strip()]
            if p_list:
                st.session_state.tournament_name = t_name
                st.session_state.groups = {"A": p_list}
                st.session_state.modes = {"A": "KDK"}
                st.session_state.schedule["A"], st.session_state.shuffled_players["A"] = make_kdk_schedule(p_list, 3)
                st.success("생성 완료"); st.rerun()
