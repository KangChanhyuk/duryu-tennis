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
MATCHES_DIR  = "matches"          # 대회별 대진/점수 JSON 저장 폴더

POINT_TABLE = {1: 100, 2: 80, 3: 65, 4: 55, 5: 45, 6: 37, 7: 30, 8: 24,
               9: 20, 10: 16, 11: 13, 12: 10}

# KDK 한울방식 대진표 (번호:번호 형식)
KDK_TABLE = {
    4: {
        3: [["12:34"], ["13:24"], ["14:23"]],
    },
    6: {
        4: [["13:24"], ["15:46"], ["23:56"], ["14:35"], ["26:34"], ["16:25"]],
    },
    8: {
        3: [["12:34","56:78"], ["18:27","36:45"], ["14:58","23:67"]],
        4: [["12:34","56:78"], ["13:57","24:68"], ["15:26","37:48"], ["16:38","25:47"]],
    },
    10: {
        4: [
            ["12:35","67:810"],
            ["23:46","78:910"],
            ["34:57","89:110"],
            ["45:68","910:12"],
            ["56:79","110:23"],
        ],
    },
    12: {
        4: [
            ["12:34","56:78","910:1112"],
            ["13:57","24:68","911:1012"],
            ["48:912","67:1011","1112:23"],
            ["15:26","37:48","910:1112"],
            ["16:27","38:49","1011:1112"],
        ],
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
# 대진표 파싱 함수
# ============================================================
def smart_split(s, n):
    """'12', '34', '910', '1112' 형태 파싱 → 정수 리스트 반환"""
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
    """'12:34' → [[이름,이름],[이름,이름]]"""
    n = len(shuffled)
    if ':' not in ms:
        return None
    l, r = ms.split(':')
    li = smart_split(l, n)
    ri = smart_split(r, n)
    t1 = [shuffled[i-1] for i in li if 1 <= i <= n]
    t2 = [shuffled[i-1] for i in ri if 1 <= i <= n]
    return [t1, t2] if t1 and t2 else None

# ============================================================
# 그룹 배분: 스네이크 드래프트 (랭킹순 → 1위↔최하위 페어링)
# ============================================================
def distribute_groups(p_list, g_configs):
    """
    랭킹순 정렬 후 스네이크 드래프트로 그룹 배분.
    각 그룹 내부는 1위&최하위, 2위&차하위 순으로 매핑.
    KDK/단식은 그룹 내 랜덤 셔플.
    """
    groups = {}
    g_names = list(g_configs.keys())
    g_sizes = [g_configs[gn][0] for gn in g_names]
    total = sum(g_sizes)
    players = p_list[:total]

    # 스네이크 드래프트: 라운드마다 방향 교대
    slot_groups = []   # 각 슬롯이 어느 그룹에 속하는지
    direction = 1
    idx = 0
    for sz in g_sizes:
        for _ in range(sz):
            slot_groups.append(idx)
        idx += 1

    # 실제 스네이크: 라운드별 그룹 순서
    round_assignments = []
    g_idx = list(range(len(g_names)))
    r_idx = 0
    remaining = list(zip(g_names, g_sizes))
    filled = {gn: [] for gn in g_names}
    player_ptr = 0

    # 라운드마다 순방향/역방향 번갈아 그룹에 1명씩 배분
    max_sz = max(g_sizes)
    for r in range(max_sz):
        order = g_names if r % 2 == 0 else list(reversed(g_names))
        for gn in order:
            if len(filled[gn]) < g_configs[gn][0] and player_ptr < len(players):
                filled[gn].append(players[player_ptr])
                player_ptr += 1

    # 그룹 내 배열:
    # - 고정페어: 1위&최하위, 2위&차하위 ... 순으로 페어 구성
    # - KDK/단식: 랜덤 셔플
    for gn in g_names:
        gp = filled[gn]
        md = g_configs[gn][1]
        if md == "고정페어":
            # 최강-최약 페어링
            paired = []
            lo, hi = 0, len(gp) - 1
            while lo < hi:
                paired.extend([gp[lo], gp[hi]])
                lo += 1; hi -= 1
            if lo == hi:
                paired.append(gp[lo])
            groups[gn] = paired
        else:
            # KDK/단식: 랜덤
            shuffled = gp[:]
            random.shuffle(shuffled)
            groups[gn] = shuffled

    return groups

# ============================================================
# KDK 대진 생성
# ============================================================
def make_kdk_schedule(players, target_games):
    n = len(players)
    shuffled = players[:]   # distribute_groups에서 이미 랜덤

    if n in KDK_TABLE and target_games in KDK_TABLE[n]:
        rounds_raw = KDK_TABLE[n][target_games]
        schedule = []
        for round_strs in rounds_raw:
            rnd = []
            for ms in round_strs:
                m = parse_match_str(ms, shuffled)
                if m:
                    rnd.append(m)
            if rnd:
                schedule.append(rnd)
        return schedule, shuffled

    # 자동 생성: 파트너 중복 최소화
    used_pairs = set()
    all_combos = []
    for i in range(n):
        for j in range(i+1, n):
            for k in range(n):
                for l in range(k+1, n):
                    if not {i,j} & {k,l}:
                        all_combos.append((i,j,k,l))
    random.shuffle(all_combos)

    schedule = []
    num_courts = max(1, n // 4)
    for _ in range(target_games):
        rnd = []
        used_in_round = set()
        for combo in all_combos:
            i,j,k,l = combo
            if any(x in used_in_round for x in [i,j,k,l]):
                continue
            p1 = tuple(sorted([i,j])); p2 = tuple(sorted([k,l]))
            if p1 in used_pairs or p2 in used_pairs:
                continue
            rnd.append([[shuffled[i],shuffled[j]],[shuffled[k],shuffled[l]]])
            used_in_round.update([i,j,k,l])
            used_pairs.add(p1); used_pairs.add(p2)
            if len(rnd) >= num_courts:
                break
        if rnd:
            schedule.append(rnd)
    return schedule, shuffled

# ============================================================
# 리그전(고정페어/단식) 대진 생성
# ============================================================
def make_round_robin(teams):
    matches = [[teams[i], teams[j]] for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    rounds = []
    while matches:
        rnd, used, remaining = [], set(), []
        for m in matches:
            ps = set(str(p) for p in m[0]+m[1])
            if not ps & used:
                rnd.append(m); used |= ps
            else:
                remaining.append(m)
        if rnd:
            rounds.append(rnd)
        if not rnd:
            break
        matches = remaining
    return rounds

# ============================================================
# 대회 저장/로드 (JSON)
# ============================================================
def ensure_dir():
    if not os.path.exists(MATCHES_DIR):
        os.makedirs(MATCHES_DIR)

def tournament_path(name):
    safe = name.replace("/","_").replace("\\","_").replace(" ","_")
    return os.path.join(MATCHES_DIR, f"{safe}.json")

def save_tournament(name):
    ensure_dir()
    data = {
        "name": name,
        "date": st.session_state.current_date,
        "groups": st.session_state.groups,
        "modes": st.session_state.modes,
        "game_counts": st.session_state.game_counts,
        "shuffled_players": st.session_state.shuffled_players,
        "schedule": {g: [[list(t1)+["|||"]+list(t2) for t1,t2 in rd] for rd in rds]
                     for g, rds in st.session_state.schedule.items()},
        "scores": {str(k): v for k, v in st.session_state.scores.items()},
    }
    # schedule을 JSON 직렬화 가능한 구조로 저장
    data["schedule_raw"] = {}
    for g, rds in st.session_state.schedule.items():
        data["schedule_raw"][g] = []
        for rd in rds:
            rd_list = []
            for t1, t2 in rd:
                rd_list.append({"t1": t1, "t2": t2})
            data["schedule_raw"][g].append(rd_list)

    data["scores_raw"] = []
    for k, v in st.session_state.scores.items():
        data["scores_raw"].append({
            "key": list(k),
            "teams": [list(v["teams"][0]), list(v["teams"][1])],
            "score": list(v["score"])
        })

    with open(tournament_path(name), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_tournament(name):
    path = tournament_path(name)
    if not os.path.exists(path):
        return False
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    st.session_state.tournament_name = data["name"]
    st.session_state.current_date    = data.get("date","")
    st.session_state.groups          = data["groups"]
    st.session_state.modes           = data["modes"]
    st.session_state.game_counts     = data.get("game_counts", {})
    st.session_state.shuffled_players= data.get("shuffled_players", {})

    # schedule 복원
    sched = {}
    for g, rds in data.get("schedule_raw",{}).items():
        sched[g] = []
        for rd in rds:
            sched[g].append([(m["t1"], m["t2"]) for m in rd])
    st.session_state.schedule = sched

    # scores 복원
    scores = {}
    for item in data.get("scores_raw",[]):
        k = tuple(item["key"])
        scores[k] = {
            "teams": (tuple(item["teams"][0]), tuple(item["teams"][1])),
            "score": tuple(item["score"])
        }
    st.session_state.scores = scores
    return True

def list_tournaments():
    ensure_dir()
    files = [f for f in os.listdir(MATCHES_DIR) if f.endswith(".json")]
    names = []
    for f in files:
        with open(os.path.join(MATCHES_DIR,f),"r",encoding="utf-8") as fp:
            try:
                d = json.load(fp)
                names.append(d.get("name","?"))
            except:
                pass
    return names

def delete_tournament(name):
    path = tournament_path(name)
    if os.path.exists(path):
        os.remove(path)

# ============================================================
# 랭킹 로드/저장
# ============================================================
def load_rank():
    if not os.path.exists(RANK_FILE):
        return pd.DataFrame(columns=["이름","현재포인트","총경기","총승","총득실"])
    df = pd.read_csv(RANK_FILE)
    for col in ["현재포인트","총경기","총승","총득실"]:
        if col not in df.columns: df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df

def save_rank(df):
    df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
    df.to_csv(RANK_FILE, index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["날짜","대회명","그룹","방식","이름","등급","승","득실","획득포인트"])
    return pd.read_csv(HISTORY_FILE)

def save_history(df):
    df.to_csv(HISTORY_FILE, index=False)

# ============================================================
# KDK/단식/고정페어 통합 개인 통계 계산
# ============================================================
def calc_stats(group_name):
    """개인별 승/패/득실/총득점 집계 → 순위 정렬된 리스트 반환"""
    players = st.session_state.groups[group_name]
    stats = {p: {"승":0,"패":0,"득실":0,"총득점":0} for p in players}

    for key, data in st.session_state.scores.items():
        if key[0] != group_name: continue
        t1, t2 = list(data["teams"][0]), list(data["teams"][1])
        s1, s2 = data["score"]
        if s1 == 0 and s2 == 0: continue
        for team, ms, os_ in [(t1,s1,s2),(t2,s2,s1)]:
            for p in team:
                if p in stats:
                    if ms > os_: stats[p]["승"] += 1
                    elif ms < os_: stats[p]["패"] += 1
                    stats[p]["득실"] += (ms - os_)
                    stats[p]["총득점"] += ms

    return sorted(stats.items(), key=lambda x:(x[1]["승"],x[1]["득실"],x[1]["총득점"]), reverse=True)

# ============================================================
# 결과 등급 산정
# ============================================================
def get_result_grade(rank, mode):
    """등급 문자열 반환"""
    if mode == "고정페어":
        # 페어 단위 순위 그대로
        if rank == 1: return "🥇 우승"
        if rank == 2: return "🥈 준우승"
        if rank == 3: return "🥉 3위"
        return f"{rank}위"
    else:
        # KDK/단식: 1-2위=우승, 3-4위=준우승, 5-6위=3위
        if rank <= 2: return "🥇 우승"
        if rank <= 4: return "🥈 준우승"
        if rank <= 6: return "🥉 3위"
        return f"{rank}위"

def grade_sort_key(grade):
    if "우승" in grade and "🥇" in grade: return 1
    if "준우승" in grade: return 2
    if "3위" in grade: return 3
    try: return int(grade.replace("위","")) + 3
    except: return 99

# ============================================================
# 매트릭스 + 순위표 렌더링
# ============================================================
def render_matrix(group_name):
    players = st.session_state.groups[group_name]
    mode    = st.session_state.modes[group_name]
    shuffled = st.session_state.shuffled_players.get(group_name, players)
    sorted_stats = calc_stats(group_name)

    # 번호 라벨 함수
    def num_tag(p):
        try: return f"({shuffled.index(p)+1})"
        except: return ""

    # ── 헤더 ──
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

    # ── 매트릭스 ──
    with col1:
        st.markdown("**📋 상대별 전적 매트릭스**")

        if mode == "고정페어":
            # 팀(페어) 단위 매트릭스
            teams_list = []
            seen = set()
            for rd in st.session_state.schedule[group_name]:
                for t1, t2 in rd:
                    for t in [tuple(t1), tuple(t2)]:
                        if t not in seen:
                            teams_list.append(t); seen.add(t)
            team_labels = {t: " & ".join(t) for t in teams_list}
            labels_list = [team_labels[t] for t in teams_list]

            score_map = {}
            for key, data in st.session_state.scores.items():
                if key[0] != group_name: continue
                t1k = tuple(data["teams"][0]); t2k = tuple(data["teams"][1])
                s1, s2 = data["score"]
                if s1==0 and s2==0: continue
                k1 = team_labels.get(t1k); k2 = team_labels.get(t2k)
                if k1 and k2:
                    score_map[(k1,k2)] = (s1,s2)
                    score_map[(k2,k1)] = (s2,s1)

            html = "<table class='matrix-table'><tr class='header-row'><th>팀</th>"
            for lb in labels_list:
                html += f"<th>{lb}</th>"
            html += "</tr>"
            for lb_r in labels_list:
                html += f"<tr><th style='text-align:left;padding-left:10px;'>{lb_r}</th>"
                for lb_c in labels_list:
                    if lb_r == lb_c:
                        html += "<td class='self'>■</td>"
                    elif (lb_r, lb_c) in score_map:
                        s1, s2 = score_map[(lb_r,lb_c)]
                        css = "win" if s1>s2 else ("lose" if s1<s2 else "draw")
                        html += f"<td class='{css}'>{s1}:{s2}</td>"
                    else:
                        html += "<td class='empty'>-</td>"
                html += "</tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

        else:
            # 개인 단위 매트릭스
            score_map = {}
            for key, data in st.session_state.scores.items():
                if key[0] != group_name: continue
                t1, t2 = list(data["teams"][0]), list(data["teams"][1])
                s1, s2 = data["score"]
                if s1==0 and s2==0: continue
                for p1 in t1:
                    for p2 in t2:
                        score_map[(p1,p2)] = (s1,s2)
                        score_map[(p2,p1)] = (s2,s1)

            html = "<table class='matrix-table'><tr class='header-row'><th>선수</th>"
            for p in players:
                nt = num_tag(p)
                html += f"<th>{nt}{p}</th>"
            html += "</tr>"
            for pr in players:
                nt_r = num_tag(pr)
                html += f"<tr><th style='text-align:left;padding-left:10px;'>{nt_r}{pr}</th>"
                for pc in players:
                    if pr == pc:
                        html += "<td class='self'>■</td>"
                    elif (pr, pc) in score_map:
                        s1, s2 = score_map[(pr,pc)]
                        css = "win" if s1>s2 else ("lose" if s1<s2 else "draw")
                        html += f"<td class='{css}'>{s1}:{s2}</td>"
                    else:
                        html += "<td class='empty'>-</td>"
                html += "</tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

    # ── 순위표 ──
    with col2:
        st.markdown("**🏅 현재 순위**")
        if mode == "고정페어":
            # 고정페어: 팀 단위 집계
            team_stats = {}
            teams_list_u = []
            seen2 = set()
            for rd in st.session_state.schedule[group_name]:
                for t1, t2 in rd:
                    for t in [tuple(t1), tuple(t2)]:
                        if t not in seen2:
                            teams_list_u.append(t); seen2.add(t)
            for t in teams_list_u:
                team_stats[t] = {"승":0,"패":0,"득실":0,"총득점":0}
            for key, data in st.session_state.scores.items():
                if key[0] != group_name: continue
                t1k = tuple(data["teams"][0]); t2k = tuple(data["teams"][1])
                s1, s2 = data["score"]
                if s1==0 and s2==0: continue
                for tk, ms, os_ in [(t1k,s1,s2),(t2k,s2,s1)]:
                    if tk in team_stats:
                        if ms>os_: team_stats[tk]["승"]+=1
                        elif ms<os_: team_stats[tk]["패"]+=1
                        team_stats[tk]["득실"]+=(ms-os_)
                        team_stats[tk]["총득점"]+=ms
            sorted_teams = sorted(team_stats.items(), key=lambda x:(x[1]["승"],x[1]["득실"],x[1]["총득점"]), reverse=True)

            html = "<table class='rank-table'><tr><th>순위</th><th>팀</th><th>승</th><th>패</th><th>득실</th></tr>"
            for rank,(t,s) in enumerate(sorted_teams,1):
                medal = ["🥇","🥈","🥉"][rank-1] if rank<=3 else f"{rank}"
                team_str = " & ".join(t)
                diff = f"+{s['득실']}" if s['득실']>=0 else str(s['득실'])
                html += f"<tr><td class='rank-medal'>{medal}</td><td>{team_str}</td><td>{s['승']}</td><td>{s['패']}</td><td>{diff}</td></tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)
        else:
            html = "<table class='rank-table'><tr><th>순위</th><th>번호</th><th>선수</th><th>승</th><th>패</th><th>득실</th></tr>"
            for rank,(name,s) in enumerate(sorted_stats,1):
                medal = ["🥇","🥈","🥉"][rank-1] if rank<=3 else f"{rank}"
                diff = f"+{s['득실']}" if s['득실']>=0 else str(s['득실'])
                nt = num_tag(name)
                html += f"<tr><td class='rank-medal'>{medal}</td><td>{nt}</td><td>{name}</td><td>{s['승']}</td><td>{s['패']}</td><td>{diff}</td></tr>"
            html += "</table>"
            st.markdown(html, unsafe_allow_html=True)

# ============================================================
# 대진표 점수 입력 UI
# ============================================================
def render_schedule(group_name):
    mode    = st.session_state.modes[group_name]
    p_list  = st.session_state.groups[group_name]
    shuffled= st.session_state.shuffled_players.get(group_name, p_list)

    def num_label(p):
        try: n = shuffled.index(p)+1; return f"<span class='team-num'>No.{n}</span>"
        except: return ""

    def team_display(team):
        return " & ".join(team)

    if mode == "KDK":
        st.markdown("""
        <div class='info-box'>
          <strong>🔄 KDK 방식</strong>
          <p>• 매 라운드 파트너 교체 · 개인 승수/득실로 최종 순위 결정</p>
          <p>• 1순위: 승수 &nbsp;|&nbsp; 2순위: 득실차 &nbsp;|&nbsp; 3순위: 총득점</p>
        </div>
        """, unsafe_allow_html=True)

    for ri, rd in enumerate(st.session_state.schedule[group_name]):
        st.markdown(f"<div class='round-header'>◆ ROUND {ri+1}</div>", unsafe_allow_html=True)

        for mi, (t1, t2) in enumerate(rd):
            t1, t2 = list(t1), list(t2)
            score_key = (group_name, ri, mi)
            existing  = st.session_state.scores.get(score_key, {"score":(0,0)})["score"]
            saved_str = f"{existing[0]}:{existing[1]}" if (existing[0]+existing[1])>0 else ""

            t1_disp = team_display(t1)
            t2_disp = team_display(t2)
            t1_nums = " ".join([f"No.{shuffled.index(p)+1}" for p in t1 if p in shuffled])
            t2_nums = " ".join([f"No.{shuffled.index(p)+1}" for p in t2 if p in shuffled])

            # 매치 카드 HTML
            st.markdown(f"""
            <div class='match-wrapper'>
              <div class='match-inner'>
                <div class='team-box team-box-a'>
                  <div class='team-label'>Team A</div>
                  <div class='team-players'>{t1_disp}</div>
                  <div class='team-num'>{t1_nums}</div>
                </div>
                <div class='vs-center'>
                  <div class='vs-text'>VS</div>
                  {f"<div class='score-saved'>{saved_str}</div>" if saved_str else ""}
                </div>
                <div class='team-box team-box-b'>
                  <div class='team-label'>Team B</div>
                  <div class='team-players'>{t2_disp}</div>
                  <div class='team-num'>{t2_nums}</div>
                </div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # 점수 입력 행
            ci1, ci2, ci3, ci4, ci5 = st.columns([2,1,0.4,1,1.2])
            with ci1:
                s1 = st.number_input(f"{t1_disp} 점수", 0, 10, existing[0],
                                     key=f"s1_{group_name}_{ri}_{mi}", label_visibility="collapsed")
            with ci2:
                st.markdown("<div style='text-align:center;padding-top:8px;color:#90a4ae;font-weight:700;'>:</div>", unsafe_allow_html=True)
            with ci3:
                pass
            with ci4:
                s2 = st.number_input(f"{t2_disp} 점수", 0, 10, existing[1],
                                     key=f"s2_{group_name}_{ri}_{mi}", label_visibility="collapsed")
            with ci5:
                if st.button(f"💾 저장", key=f"save_{group_name}_{ri}_{mi}"):
                    st.session_state.scores[score_key] = {
                        "teams": (tuple(t1), tuple(t2)),
                        "score": (s1, s2)
                    }
                    st.success(f"R{ri+1}-{mi+1} 저장 완료!")
                    st.rerun()

# ============================================================
# 사이드바
# ============================================================
st.sidebar.markdown("""
<div style='text-align:center;padding:20px 0 12px;'>
  <div style='font-family:Bebas Neue,sans-serif;font-size:2.2rem;
       color:#fff;letter-spacing:0.12em;line-height:1;'>두류 테니스</div>
  <div style='color:rgba(255,255,255,0.65);font-size:0.7rem;letter-spacing:0.35em;margin-top:4px;'>
    RANKING SYSTEM
  </div>
</div>
<hr style='border-color:rgba(255,255,255,0.2);margin:10px 0 16px;'>
""", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "메뉴",
    ["🏆 랭킹보드", "📅 대진표 / 점수입력", "📊 경기결과 & 정산", "📜 대회 기록", "⚙️ 관리자 센터"],
    label_visibility="collapsed"
)

# 현재 대회명 표시
if st.session_state.schedule:
    st.sidebar.markdown(f"""
    <div style='background:rgba(255,255,255,0.15);border-radius:8px;padding:8px 12px;margin-top:16px;'>
      <div style='font-size:0.7rem;color:rgba(255,255,255,0.6);'>현재 대회</div>
      <div style='font-size:0.9rem;font-weight:700;color:#fff;'>{st.session_state.tournament_name}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================================
# 🏆 랭킹보드
# ============================================================
if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>PLAYER RANKING BOARD</div>", unsafe_allow_html=True)

    df = load_rank()
    if df.empty:
        st.markdown("""
        <div class='info-box'>
          <p>🎾 아직 등록된 선수가 없습니다.</p>
          <p>관리자 센터에서 대회를 생성하고 결과를 정산하면 자동으로 랭킹이 집계됩니다.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)

        # TOP 3 포디엄
        n_top = min(3, len(df))
        top_cols = st.columns(n_top)
        podium_icons  = ["🥇","🥈","🥉"]
        podium_colors = ["#fff8e1","#eceff1","#fbe9e7"]
        podium_border = ["#f9a825","#90a4ae","#ffab91"]
        for ci, idx in enumerate(range(n_top)):
            row = df.iloc[idx]
            with top_cols[ci]:
                st.markdown(f"""
                <div style='background:{podium_colors[ci]};border:2px solid {podium_border[ci]};
                     border-radius:16px;padding:22px 16px;text-align:center;
                     box-shadow:0 4px 16px rgba(0,0,0,0.08);'>
                  <div style='font-size:2.5rem;margin-bottom:6px;'>{podium_icons[idx]}</div>
                  <div style='font-family:Bebas Neue,sans-serif;font-size:1.7rem;
                       color:#1565c0;letter-spacing:0.05em;'>{row['이름']}</div>
                  <div style='font-size:2.2rem;font-weight:900;color:#1565c0;margin:4px 0;'>
                    {int(row['현재포인트'])}
                  </div>
                  <div style='color:#78909c;font-size:0.72rem;letter-spacing:0.2em;'>POINTS</div>
                  <div style='margin-top:10px;'>
                    <span class='stat-badge badge-win'>승 {int(row.get('총승',0))}</span>
                    <span class='stat-badge badge-diff'>득실 {int(row.get('총득실',0)):+d}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 전체 순위 목록
        for i, row in df.iterrows():
            rank = i + 1
            rank_class = {1:"top1",2:"top2",3:"top3"}.get(rank,"")
            st.markdown(f"""
            <div class='rank-row'>
              <div class='rank-num {rank_class}'>{rank}</div>
              <div class='rank-name'>{row['이름']}</div>
              <div style='text-align:right;'>
                <div class='rank-pts'>{int(row.get('현재포인트',0))}</div>
                <div class='rank-pts-label'>pts</div>
              </div>
              <div style='margin-left:18px;'>
                <span class='stat-badge badge-win'>승 {int(row.get('총승',0))}</span>
                <span class='stat-badge badge-diff'>득실 {int(row.get('총득실',0)):+d}</span>
                <span class='stat-badge badge-pts'>경기 {int(row.get('총경기',0))}</span>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ============================================================
# 📅 대진표 / 점수 입력
# ============================================================
elif menu == "📅 대진표 / 점수입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>대진표 확인 및 점수 입력</div>", unsafe_allow_html=True)

    if not st.session_state.schedule:
        st.markdown("""
        <div class='info-box'>
          <p>⚠️ 대진표가 없습니다. 관리자 센터 → 대회 생성에서 만들어주세요.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        tabs = st.tabs([f" Group {g} " for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                render_matrix(g)
                st.divider()
                render_schedule(g)

        # 저장 버튼
        st.divider()
        if st.button("💾 현재 대회 점수 저장", type="primary"):
            save_tournament(st.session_state.tournament_name)
            st.success("저장 완료!")

# ============================================================
# 📊 경기결과 & 정산
# ============================================================
elif menu == "📊 경기결과 & 정산":
    st.markdown("<div class='main-title'>RESULTS & POINTS</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>최종 순위 및 포인트 정산</div>", unsafe_allow_html=True)

    if not st.session_state.schedule:
        st.warning("대진표가 없습니다.")
    else:
        for g in st.session_state.schedule.keys():
            mode = st.session_state.modes[g]
            sorted_stats = calc_stats(g)
            shuffled = st.session_state.shuffled_players.get(g, st.session_state.groups[g])

            st.markdown(f"""
            <div style='background:linear-gradient(90deg,#1565c0,#1e88e5);
                 border-radius:10px;padding:10px 20px;margin-bottom:12px;'>
              <span style='font-family:Bebas Neue,sans-serif;font-size:1.4rem;
                   color:#fff;letter-spacing:0.12em;'>GROUP {g} · {mode}</span>
            </div>
            """, unsafe_allow_html=True)

            if mode == "고정페어":
                # 팀 단위 집계
                teams_list_u, seen2 = [], set()
                for rd in st.session_state.schedule[g]:
                    for t1, t2 in rd:
                        for t in [tuple(t1),tuple(t2)]:
                            if t not in seen2:
                                teams_list_u.append(t); seen2.add(t)
                team_stats = {t:{"승":0,"패":0,"득실":0,"총득점":0} for t in teams_list_u}
                for key,data in st.session_state.scores.items():
                    if key[0]!=g: continue
                    t1k=tuple(data["teams"][0]); t2k=tuple(data["teams"][1])
                    s1,s2=data["score"]
                    if s1==0 and s2==0: continue
                    for tk,ms,os_ in [(t1k,s1,s2),(t2k,s2,s1)]:
                        if tk in team_stats:
                            if ms>os_: team_stats[tk]["승"]+=1
                            elif ms<os_: team_stats[tk]["패"]+=1
                            team_stats[tk]["득실"]+=(ms-os_)
                            team_stats[tk]["총득점"]+=ms
                sorted_teams = sorted(team_stats.items(),key=lambda x:(x[1]["승"],x[1]["득실"],x[1]["총득점"]),reverse=True)

                rows = []
                for rank,(t,s) in enumerate(sorted_teams,1):
                    grade = get_result_grade(rank,"고정페어")
                    pts = POINT_TABLE.get(rank, max(5,15-rank*2))
                    rows.append({
                        "등급":grade,"팀":" & ".join(t),
                        "승":s["승"],"패":s["패"],
                        "득실":f"{s['득실']:+d}","총득점":s["총득점"],
                        "획득포인트":pts
                    })

                # 등급별 그룹으로 표시
                grades_order = sorted(set(r["등급"] for r in rows), key=grade_sort_key)
                for grade_label in grades_order:
                    grade_rows = [r for r in rows if r["등급"]==grade_label]
                    css_class = "result-champion" if "🥇" in grade_label else ("result-runner" if "🥈" in grade_label else ("result-third" if "🥉" in grade_label else ""))
                    st.markdown(f"<div class='card {css_class}' style='padding:10px 18px;margin-bottom:8px;'>", unsafe_allow_html=True)
                    st.markdown(f"**{grade_label}**")
                    for r in grade_rows:
                        st.markdown(f"""
                        <div style='display:flex;align-items:center;gap:10px;padding:4px 0;'>
                          <span style='font-weight:700;font-size:1rem;color:#0d2137;min-width:120px;'>{r['팀']}</span>
                          <span class='stat-badge badge-win'>승 {r['승']}</span>
                          <span class='stat-badge badge-lose'>패 {r['패']}</span>
                          <span class='stat-badge badge-diff'>득실 {r['득실']}</span>
                          <span class='stat-badge badge-pts'>+{r['획득포인트']}pt</span>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            else:
                # KDK/단식: 1-2위=우승, 3-4위=준우승, 5-6위=3위
                rows = []
                for rank,(name,s) in enumerate(sorted_stats,1):
                    grade = get_result_grade(rank, mode)
                    pts = POINT_TABLE.get(rank, max(5,15-rank*2))
                    try: num = f"No.{shuffled.index(name)+1}"
                    except: num = ""
                    rows.append({
                        "등급":grade,"번호":num,"이름":name,
                        "승":s["승"],"패":s["패"],
                        "득실":f"{s['득실']:+d}","총득점":s["총득점"],
                        "획득포인트":pts
                    })

                grades_order = sorted(set(r["등급"] for r in rows), key=grade_sort_key)
                for grade_label in grades_order:
                    grade_rows = [r for r in rows if r["등급"]==grade_label]
                    css_class = "result-champion" if "🥇" in grade_label else ("result-runner" if "🥈" in grade_label else ("result-third" if "🥉" in grade_label else ""))
                    st.markdown(f"<div class='card {css_class}' style='padding:10px 18px;margin-bottom:8px;'>", unsafe_allow_html=True)
                    st.markdown(f"**{grade_label}**")
                    for r in grade_rows:
                        st.markdown(f"""
                        <div style='display:flex;align-items:center;gap:10px;padding:4px 0;'>
                          <span style='color:#78909c;font-size:0.85rem;min-width:50px;'>{r['번호']}</span>
                          <span style='font-weight:700;font-size:1rem;color:#0d2137;min-width:80px;'>{r['이름']}</span>
                          <span class='stat-badge badge-win'>승 {r['승']}</span>
                          <span class='stat-badge badge-lose'>패 {r['패']}</span>
                          <span class='stat-badge badge-diff'>득실 {r['득실']}</span>
                          <span class='stat-badge badge-pts'>+{r['획득포인트']}pt</span>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)

            st.divider()

        # 정산 버튼
        if st.button("✅ 포인트 정산 및 랭킹 반영", type="primary"):
            rank_df   = load_rank()
            hist_df   = load_history()
            new_hist  = []

            for g in st.session_state.schedule.keys():
                mode = st.session_state.modes[g]
                sorted_stats = calc_stats(g)
                shuffled = st.session_state.shuffled_players.get(g, st.session_state.groups[g])

                if mode == "고정페어":
                    teams_list_u2, seen3 = [], set()
                    for rd in st.session_state.schedule[g]:
                        for t1,t2 in rd:
                            for t in [tuple(t1),tuple(t2)]:
                                if t not in seen3:
                                    teams_list_u2.append(t); seen3.add(t)
                    team_stats2 = {t:{"승":0,"패":0,"득실":0,"총득점":0} for t in teams_list_u2}
                    for key,data in st.session_state.scores.items():
                        if key[0]!=g: continue
                        t1k=tuple(data["teams"][0]); t2k=tuple(data["teams"][1])
                        s1,s2=data["score"]
                        if s1==0 and s2==0: continue
                        for tk,ms,os_ in [(t1k,s1,s2),(t2k,s2,s1)]:
                            if tk in team_stats2:
                                if ms>os_: team_stats2[tk]["승"]+=1
                                elif ms<os_: team_stats2[tk]["패"]+=1
                                team_stats2[tk]["득실"]+=(ms-os_)
                                team_stats2[tk]["총득점"]+=ms
                    sorted_teams2 = sorted(team_stats2.items(),key=lambda x:(x[1]["승"],x[1]["득실"],x[1]["총득점"]),reverse=True)

                    for rank,(t,s) in enumerate(sorted_teams2,1):
                        pts = POINT_TABLE.get(rank,max(5,15-rank*2))
                        grade = get_result_grade(rank,"고정페어")
                        for name in t:
                            if name in rank_df["이름"].values:
                                rank_df.loc[rank_df["이름"]==name,"현재포인트"] += pts
                                rank_df.loc[rank_df["이름"]==name,"총경기"]    += (s["승"]+s["패"])
                                rank_df.loc[rank_df["이름"]==name,"총승"]      += s["승"]
                                rank_df.loc[rank_df["이름"]==name,"총득실"]    += s["득실"]
                            else:
                                rank_df = pd.concat([rank_df, pd.DataFrame([{
                                    "이름":name,"현재포인트":pts,
                                    "총경기":s["승"]+s["패"],
                                    "총승":s["승"],"총득실":s["득실"]
                                }])],ignore_index=True)
                            new_hist.append({
                                "날짜":st.session_state.current_date,
                                "대회명":st.session_state.tournament_name,
                                "그룹":g,"방식":mode,"이름":name,
                                "등급":grade,"승":s["승"],"득실":s["득실"],"획득포인트":pts
                            })
                else:
                    for rank,(name,s) in enumerate(sorted_stats,1):
                        pts = POINT_TABLE.get(rank,max(5,15-rank*2))
                        grade = get_result_grade(rank,mode)
                        if name in rank_df["이름"].values:
                            rank_df.loc[rank_df["이름"]==name,"현재포인트"] += pts
                            rank_df.loc[rank_df["이름"]==name,"총경기"]    += (s["승"]+s["패"])
                            rank_df.loc[rank_df["이름"]==name,"총승"]      += s["승"]
                            rank_df.loc[rank_df["이름"]==name,"총득실"]    += s["득실"]
                        else:
                            rank_df = pd.concat([rank_df, pd.DataFrame([{
                                "이름":name,"현재포인트":pts,
                                "총경기":s["승"]+s["패"],
                                "총승":s["승"],"총득실":s["득실"]
                            }])],ignore_index=True)
                        new_hist.append({
                            "날짜":st.session_state.current_date,
                            "대회명":st.session_state.tournament_name,
                            "그룹":g,"방식":mode,"이름":name,
                            "등급":grade,"승":s["승"],"득실":s["득실"],"획득포인트":pts
                        })

            save_rank(rank_df)
            hist_df = pd.concat([hist_df,pd.DataFrame(new_hist)],ignore_index=True)
            save_history(hist_df)
            save_tournament(st.session_state.tournament_name)
            st.success("🎉 포인트 정산 및 랭킹 반영 완료!")
            st.balloons()

# ============================================================
# 📜 대회 기록
# ============================================================
elif menu == "📜 대회 기록":
    st.markdown("<div class='main-title'>TOURNAMENT HISTORY</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>역대 대회 기록 조회</div>", unsafe_allow_html=True)

    df = load_history()
    if df.empty:
        st.info("아직 대회 기록이 없습니다.")
    else:
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            tournaments = df["대회명"].unique().tolist()
            selected_t = st.selectbox("대회 선택", ["전체"]+tournaments)
        with col_f2:
            search = st.text_input("선수명 검색", placeholder="이름 입력...")

        dff = df.copy()
        if selected_t != "전체":
            dff = dff[dff["대회명"]==selected_t]
        if search:
            dff = dff[dff["이름"].str.contains(search, na=False)]

        dff = dff.sort_values("날짜", ascending=False)

        # HTML 테이블로 가운데 정렬
        html = "<table class='rank-table' style='width:100%;'>"
        html += "<tr>" + "".join(f"<th>{c}</th>" for c in dff.columns) + "</tr>"
        for _,row in dff.iterrows():
            html += "<tr>" + "".join(f"<td>{v}</td>" for v in row.values) + "</tr>"
        html += "</table>"
        st.markdown(html, unsafe_allow_html=True)

# ============================================================
# ⚙️ 관리자 센터
# ============================================================
elif menu == "⚙️ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN CENTER</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>관리자 전용 패널</div>", unsafe_allow_html=True)

    if not st.session_state.admin_authed:
        pwd = st.text_input("🔒 관리자 비밀번호", type="password", placeholder="비밀번호를 입력하세요")
        if pwd == "0502":
            st.session_state.admin_authed = True
            st.rerun()
        elif pwd:
            st.error("❌ 비밀번호가 틀렸습니다.")
    else:
        # 로그아웃
        if st.button("🔓 로그아웃"):
            st.session_state.admin_authed = False
            st.rerun()

        tab1, tab2, tab3 = st.tabs(["🎾 대회 생성", "📂 대회 관리 (수정/삭제)", "🗑️ 데이터 관리"])

        # ── 대회 생성 ──
        with tab1:
            st.markdown("<div class='card-title'>새 대회 설정</div>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.session_state.tournament_name = st.text_input("대회명", st.session_state.tournament_name)
            with col_b:
                st.session_state.current_date = st.text_input("날짜", st.session_state.current_date)

            st.markdown("**참가자 입력** (쉼표로 구분, 순서 상관없이 랭킹순 자동 배분)")
            raw_p = st.text_area("참가자 목록", height=100,
                                 placeholder="예: 홍길동, 김철수, 이영희, 박민준, 최강자, 이신입...")

            st.divider()
            g_count = st.number_input("그룹 수", 1, 5, 1)

            g_configs = {}
            st.markdown("**그룹별 설정**")
            for i in range(int(g_count)):
                gn = chr(65+i)
                with st.expander(f"Group {gn} 설정", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        # 기본값: 8명
                        sz = st.number_input("인원수", 2, 20, 8, key=f"sz_{gn}")
                    with c2:
                        # 기본값: 고정페어
                        md_idx = 1  # 고정페어가 index 1
                        md = st.selectbox("진행방식", ["KDK","고정페어","단식"],
                                          index=md_idx, key=f"md_{gn}",
                                          help="KDK: 파트너 변경 복식 | 고정페어: 팀 유지 복식 | 단식: 1:1")
                    with c3:
                        # 기본값: 3게임
                        gc = st.selectbox("1인당 경기수", [3,4,5,6],
                                          index=0, key=f"gc_{gn}")

                    # 안내
                    if md == "KDK":
                        has_table = sz in KDK_TABLE and gc in KDK_TABLE.get(sz,{})
                        st.markdown(f"""
                        <div class='info-box'>
                          <strong>KDK 방식 ({sz}명, {gc}게임)</strong>
                          <p>• 매 라운드 파트너 교체 · 개인 승수/득실로 순위 결정</p>
                          <p>• {'✅ 한울방식 대진표 적용' if has_table else '⚡ 자동 대진 생성'}</p>
                          <p>• 그룹 내 <strong>랜덤 번호 배정</strong></p>
                        </div>
                        """, unsafe_allow_html=True)
                    elif md == "고정페어":
                        st.markdown(f"""
                        <div class='info-box'>
                          <strong>고정페어 방식 ({sz}명, {gc}게임)</strong>
                          <p>• 랭킹 1위 &amp; 최하위, 2위 &amp; 차하위 ... 순으로 페어 구성</p>
                          <p>• 팀 단위 리그전 · 팀 순위로 결과 산정</p>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.markdown(f"""
                        <div class='info-box'>
                          <strong>단식 방식 ({sz}명, {gc}게임)</strong>
                          <p>• 1:1 리그전 · 개인 승수/득실로 순위 결정</p>
                          <p>• 그룹 내 <strong>랜덤 순서</strong></p>
                        </div>
                        """, unsafe_allow_html=True)

                    g_configs[gn] = (int(sz), md, int(gc))

            if st.button("🎾 대진표 생성", type="primary"):
                p_list = [p.strip() for p in raw_p.split(",") if p.strip()]
                total_needed = sum(c[0] for c in g_configs.values())

                if len(p_list) < total_needed:
                    st.error(f"참가자 부족 — 필요: {total_needed}명, 입력: {len(p_list)}명")
                else:
                    # 랭킹순 정렬
                    rank_df_tmp = load_rank()
                    rank_map = dict(zip(rank_df_tmp["이름"], rank_df_tmp["현재포인트"]))
                    p_list.sort(key=lambda x: rank_map.get(x, 0), reverse=True)

                    # 그룹 배분 (스네이크 드래프트)
                    groups = distribute_groups(p_list, g_configs)

                    st.session_state.groups  = groups
                    st.session_state.modes   = {gn: v[1] for gn,v in g_configs.items()}
                    st.session_state.game_counts = {gn: v[2] for gn,v in g_configs.items()}
                    st.session_state.schedule = {}
                    st.session_state.scores   = {}
                    st.session_state.shuffled_players = {}

                    for gn, (sz, md, gc) in g_configs.items():
                        gp = groups[gn]
                        if md == "KDK":
                            sched, shuffled = make_kdk_schedule(gp, gc)
                            st.session_state.schedule[gn] = sched
                            st.session_state.shuffled_players[gn] = shuffled
                        elif md == "고정페어":
                            pairs = [gp[i:i+2] for i in range(0, len(gp), 2)]
                            st.session_state.schedule[gn] = make_round_robin(pairs)
                            st.session_state.shuffled_players[gn] = gp
                        else:
                            singles = [[p] for p in gp]
                            st.session_state.schedule[gn] = make_round_robin(singles)
                            st.session_state.shuffled_players[gn] = gp

                    save_tournament(st.session_state.tournament_name)

                    st.success(f"✅ 대진표 생성 완료!")
                    for gn in st.session_state.schedule.keys():
                        total_m = sum(len(rd) for rd in st.session_state.schedule[gn])
                        md = st.session_state.modes[gn]
                        gp = st.session_state.groups[gn]
                        members = " / ".join(gp)
                        st.info(f"Group {gn} ({md}): {len(gp)}명 · {total_m}경기 → {members}")
                    st.rerun()

        # ── 대회 관리 (수정/삭제) ──
        with tab2:
            st.markdown("<div class='card-title'>저장된 대회 목록</div>", unsafe_allow_html=True)
            t_list = list_tournaments()
            if not t_list:
                st.info("저장된 대회가 없습니다.")
            else:
                for tname in t_list:
                    col_l, col_e, col_d = st.columns([4, 1.5, 1.5])
                    with col_l:
                        st.markdown(f"""
                        <div style='padding:10px 14px;background:var(--bg-card2);
                             border:1px solid var(--border-light);border-radius:8px;'>
                          <span style='font-weight:700;color:var(--text-dark);'>{tname}</span>
                        </div>
                        """, unsafe_allow_html=True)
                    with col_e:
                        if st.button(f"📂 불러오기", key=f"load_{tname}"):
                            if load_tournament(tname):
                                st.success(f"'{tname}' 불러오기 완료!")
                                st.rerun()
                            else:
                                st.error("불러오기 실패")
                    with col_d:
                        if st.button(f"🗑️ 삭제", key=f"del_{tname}"):
                            delete_tournament(tname)
                            st.success(f"'{tname}' 삭제됨")
                            st.rerun()

            if st.session_state.schedule:
                st.divider()
                st.markdown("**현재 불러온 대회를 수정 후 저장**")
                if st.button("💾 현재 대회 덮어쓰기 저장"):
                    save_tournament(st.session_state.tournament_name)
                    st.success("저장 완료!")

        # ── 데이터 관리 ──
        with tab3:
            st.markdown("<div class='card-title'>선수 및 랭킹 데이터</div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**신규 선수 추가**")
                np1 = st.text_input("선수명", key="np_input")
                np2 = st.number_input("초기 포인트", 0, 9999, 0, key="np_pts")
                if st.button("➕ 선수 추가"):
                    if np1:
                        rdf = load_rank()
                        if np1 not in rdf["이름"].values:
                            rdf = pd.concat([rdf, pd.DataFrame([{
                                "이름":np1,"현재포인트":int(np2),
                                "총경기":0,"총승":0,"총득실":0
                            }])],ignore_index=True)
                            save_rank(rdf)
                            st.success(f"'{np1}' 추가됨")
                        else:
                            st.warning("이미 등록된 선수입니다.")

            with col2:
                st.markdown("**랭킹 수정**")
                rdf2 = load_rank()
                if not rdf2.empty:
                    edit_name = st.selectbox("선수 선택", rdf2["이름"].tolist(), key="edit_sel")
                    edit_pts  = st.number_input("포인트 직접 설정", 0, 99999,
                        int(rdf2.loc[rdf2["이름"]==edit_name,"현재포인트"].values[0]), key="edit_pts")
                    if st.button("수정 저장"):
                        rdf2.loc[rdf2["이름"]==edit_name,"현재포인트"] = edit_pts
                        save_rank(rdf2)
                        st.success("수정됨!")

            st.divider()
            rdf3 = load_rank()
            if not rdf3.empty:
                st.markdown("**현재 랭킹 데이터**")
                html = "<table class='rank-table' style='width:100%;'>"
                html += "<tr><th>이름</th><th>현재포인트</th><th>총경기</th><th>총승</th><th>총득실</th></tr>"
                for _,row in rdf3.sort_values("현재포인트",ascending=False).iterrows():
                    html += f"<tr><td>{row['이름']}</td><td>{int(row['현재포인트'])}</td><td>{int(row['총경기'])}</td><td>{int(row['총승'])}</td><td>{int(row['총득실'])}</td></tr>"
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)

            st.divider()
            st.markdown("**⚠️ 위험 구역**")
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button("🗑️ 현재 대진 초기화"):
                    st.session_state.schedule = {}
                    st.session_state.scores   = {}
                    st.session_state.groups   = {}
                    st.session_state.modes    = {}
                    st.session_state.shuffled_players = {}
                    st.success("대진 초기화 완료")
            with c2:
                if st.button("⚠️ 랭킹 데이터 초기화"):
                    if os.path.exists(RANK_FILE): os.remove(RANK_FILE)
                    st.success("랭킹 초기화 완료")
            with c3:
                if st.button("🔥 전체 초기화"):
                    if os.path.exists(RANK_FILE):    os.remove(RANK_FILE)
                    if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                    st.session_state.schedule = {}
                    st.session_state.scores   = {}
                    st.session_state.groups   = {}
                    st.session_state.modes    = {}
                    st.success("전체 초기화 완료")
