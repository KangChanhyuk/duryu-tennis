import streamlit as st
import pandas as pd
import random
import os
import json
from datetime import datetime

# =========================================================
# 페이지 설정
# =========================================================
st.set_page_config(
    layout="wide",
    page_title="두류 테니스 랭킹",
    page_icon="🎾"
)

# =========================================================
# CSS - 밝고 시원한 테니스 무드
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;500;700;800&display=swap');

:root {
    --court-green: #1e7f5a;
    --court-green-deep: #156348;
    --court-mint: #52c7a3;
    --sky-blue: #dff6ff;
    --sky-blue-2: #b8ebff;
    --accent-yellow: #ffd54f;
    --accent-orange: #ffb703;
    --accent-red: #ff5d73;

    --bg-main: #eef9ff;
    --bg-grad-1: #f4fcff;
    --bg-grad-2: #dbf3ff;
    --bg-card: rgba(255,255,255,0.88);
    --bg-card-2: rgba(242,252,247,0.95);
    --bg-soft: #f7fffb;

    --text-main: #17332a;
    --text-strong: #0f241e;
    --text-mid: #3f6a5d;
    --text-soft: #6f9185;

    --line: #bfe8d7;
    --line-2: #d8edf2;
    --shadow: 0 10px 30px rgba(44, 100, 90, 0.10);
    --shadow-2: 0 8px 20px rgba(31, 127, 90, 0.12);
}

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
    background:
        radial-gradient(circle at top left, #ffffff 0%, #effbff 30%, #e5f8ff 60%, #f4fff9 100%) !important;
    color: var(--text-main) !important;
}

.stApp {
    background:
        linear-gradient(135deg, var(--bg-grad-1) 0%, var(--bg-grad-2) 45%, #f4fff9 100%) !important;
}

/* 사이드바 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #f5fffb 0%, #e2fbf0 100%) !important;
    border-right: 1px solid var(--line) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-main) !important;
}
[data-testid="stSidebar"] .stRadio label {
    padding: 10px 14px;
    border-radius: 12px;
    margin-bottom: 6px;
    border: 1px solid transparent;
    transition: all 0.18s;
}
[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255,255,255,0.9);
    border-color: var(--line);
    box-shadow: var(--shadow-2);
}

/* 메인 타이틀 */
.main-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 4rem;
    letter-spacing: 0.12em;
    color: var(--court-green-deep);
    text-align: center;
    padding: 8px 0 4px;
    line-height: 1.05;
    text-shadow: 0 2px 0 rgba(255,255,255,0.8);
}
.sub-title {
    text-align: center;
    color: var(--text-mid);
    font-size: 0.9rem;
    letter-spacing: 0.28em;
    text-transform: uppercase;
    margin-bottom: 28px;
    font-weight: 700;
}

/* 카드 */
.card {
    background: var(--bg-card);
    border: 1px solid var(--line-2);
    border-radius: 18px;
    padding: 18px 20px;
    margin-bottom: 12px;
    box-shadow: var(--shadow);
    backdrop-filter: blur(6px);
}
.card-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.55rem;
    letter-spacing: 0.08em;
    color: var(--court-green-deep);
    margin-bottom: 12px;
    border-bottom: 1px solid var(--line);
    padding-bottom: 8px;
}

/* 정보박스 */
.info-box {
    background: linear-gradient(135deg, rgba(255,255,255,0.92), rgba(240,255,249,0.95));
    border: 1px solid var(--line);
    border-left: 5px solid var(--court-green);
    border-radius: 14px;
    padding: 16px 18px;
    margin-bottom: 16px;
    box-shadow: var(--shadow);
}
.info-box p {
    color: var(--text-mid);
    margin: 4px 0;
    font-size: 0.92rem;
}
.info-box strong {
    color: var(--text-strong);
}

/* 랭킹 카드 */
.rank-row {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 13px 16px;
    border-radius: 14px;
    margin-bottom: 9px;
    background: rgba(255,255,255,0.88);
    border: 1px solid var(--line-2);
    box-shadow: var(--shadow);
    transition: all 0.15s;
}
.rank-row:hover {
    transform: translateY(-1px);
}
.rank-num {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.9rem;
    color: var(--text-soft);
    width: 54px;
    text-align: center;
}
.rank-num.top1 { color: #f4b400; font-size: 2.25rem; }
.rank-num.top2 { color: #9aa6b2; font-size: 2.05rem; }
.rank-num.top3 { color: #c78b4f; font-size: 1.95rem; }

.rank-name {
    flex: 1;
    font-size: 1.12rem;
    font-weight: 800;
    color: var(--text-strong);
    padding: 0 10px;
}
.rank-pts {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.55rem;
    color: var(--court-green-deep);
    letter-spacing: 0.05em;
}
.rank-pts-label {
    color: var(--text-soft);
    font-size: 0.72rem;
    text-align: right;
    font-weight: 700;
}

/* 배지 */
.stat-badge {
    display: inline-block;
    padding: 5px 12px;
    border-radius: 999px;
    font-size: 0.8rem;
    font-weight: 700;
    margin: 2px;
}
.badge-win {
    background: rgba(30,127,90,0.12);
    color: var(--court-green-deep);
    border: 1px solid rgba(30,127,90,0.25);
}
.badge-lose {
    background: rgba(255,93,115,0.12);
    color: #c63b50;
    border: 1px solid rgba(255,93,115,0.25);
}
.badge-diff {
    background: rgba(255,213,79,0.18);
    color: #8a6600;
    border: 1px solid rgba(255,179,3,0.28);
}
.badge-title {
    background: rgba(82,199,163,0.18);
    color: #136549;
    border: 1px solid rgba(82,199,163,0.35);
}

/* 대진 카드 */
.match-card {
    display: grid;
    grid-template-columns: 1fr 90px 1fr;
    gap: 12px;
    align-items: stretch;
    margin-bottom: 12px;
}
.team-box {
    min-height: 92px;
    display: flex;
    flex-direction: column;
    justify-content: center;
    text-align: center;
    padding: 14px 14px;
    background: linear-gradient(135deg, rgba(82,199,163,0.12), rgba(255,255,255,0.92));
    border: 1px solid rgba(82,199,163,0.28);
    border-radius: 16px;
    box-shadow: var(--shadow);
}
.team-box.team2 {
    background: linear-gradient(135deg, rgba(184,235,255,0.32), rgba(255,255,255,0.94));
    border-color: rgba(120, 200, 240, 0.35);
}
.team-label {
    font-size: 0.7rem;
    letter-spacing: 0.18em;
    color: var(--text-soft);
    text-transform: uppercase;
    margin-bottom: 5px;
    font-weight: 700;
}
.team-players {
    font-size: 1.02rem;
    font-weight: 800;
    color: var(--text-strong);
    line-height: 1.5;
    word-break: keep-all;
}
.vs-box {
    display: flex;
    align-items: center;
    justify-content: center;
}
.vs-badge {
    width: 70px;
    height: 70px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.8rem;
    color: white;
    background: linear-gradient(135deg, var(--accent-orange), var(--accent-red));
    box-shadow: 0 10px 20px rgba(255,93,115,0.18);
}

.round-header {
    background: linear-gradient(90deg, rgba(30,127,90,0.14), rgba(82,199,163,0.02));
    padding: 9px 16px;
    border-radius: 12px;
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.12rem;
    letter-spacing: 0.14em;
    color: var(--court-green-deep);
    margin: 18px 0 12px;
    border: 1px solid rgba(82,199,163,0.20);
}

/* 폼 */
.stTextInput input,
.stTextArea textarea,
.stNumberInput input,
.stSelectbox div[data-baseweb] {
    background: rgba(255,255,255,0.92) !important;
    border: 1px solid var(--line) !important;
    color: var(--text-main) !important;
    border-radius: 12px !important;
}

.stButton > button {
    background: linear-gradient(135deg, var(--court-green), var(--court-green-deep)) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 0.08em !important;
    font-size: 1rem !important;
    transition: all 0.18s !important;
    box-shadow: var(--shadow-2) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--court-green), var(--court-mint)) !important;
    color: #083324 !important;
}

/* 탭 */
div[data-testid="stTab"] button {
    color: var(--text-mid) !important;
    font-weight: 700 !important;
}
div[data-testid="stTab"] button[aria-selected="true"] {
    color: var(--court-green-deep) !important;
    border-bottom-color: var(--court-green-deep) !important;
}

/* HTML 테이블 */
.matrix-wrap, .result-wrap {
    background: rgba(255,255,255,0.82);
    border: 1px solid var(--line-2);
    border-radius: 16px;
    padding: 10px;
    box-shadow: var(--shadow);
    overflow-x: auto;
}
.matrix-table, .result-table {
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.92rem;
}
.matrix-table th, .matrix-table td,
.result-table th, .result-table td {
    padding: 10px 10px;
    text-align: center !important;
    vertical-align: middle !important;
    border-bottom: 1px solid #e4f0f3;
    color: var(--text-strong);
}
.matrix-table th, .result-table th {
    background: linear-gradient(180deg, #effcf6 0%, #e5f8ef 100%);
    color: var(--court-green-deep);
    font-weight: 800;
    position: sticky;
    top: 0;
}
.matrix-table .row-head,
.result-table .row-head {
    font-weight: 800;
    color: var(--text-strong);
    background: rgba(255,255,255,0.96);
}
.matrix-table .self-cell {
    background: #d8dde3 !important;
    color: #7f8a94 !important;
    font-weight: 700;
}
.matrix-table .empty-cell {
    color: #9ab0a8 !important;
}
.result-table .top-gold {
    background: rgba(255, 213, 79, 0.14);
}
.result-table .top-silver {
    background: rgba(173, 181, 189, 0.12);
}
.result-table .top-bronze {
    background: rgba(199, 139, 79, 0.12);
}

/* 데이터프레임 */
[data-testid="stDataFrame"] {
    border: 1px solid var(--line) !important;
    border-radius: 14px;
    overflow: hidden;
    background: white;
}
[data-testid="stDataFrame"] th {
    background: #effcf6 !important;
    color: var(--court-green-deep) !important;
}

/* 알림 */
.stSuccess, .stInfo, .stWarning, .stError {
    border-radius: 12px !important;
}

/* 스크롤바 */
::-webkit-scrollbar { width: 7px; height: 7px; }
::-webkit-scrollbar-track { background: #edf7f8; }
::-webkit-scrollbar-thumb { background: #b7dacf; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# =========================================================
# 파일 경로
# =========================================================
RANK_FILE = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"
TOURNAMENTS_FILE = "tournaments_store.json"

# =========================================================
# KDK 한울방식 대진표
# =========================================================
KDK_TABLE = {
    4: {
        3: [["12:34"], ["13:24"], ["14:23"]],
    },
    6: {
        3: [["13:24", "56:XX"], ["15:46", "23:XX"], ["26:34", "XX:XX"]],
        4: [["13:24"], ["15:46"], ["23:56"], ["14:35"], ["26:34"], ["16:25"]],
    },
    8: {
        3: [
            ["12:34", "56:78"],
            ["18:27", "36:45"],
            ["14:58", "23:67"],
        ],
        4: [
            ["12:34", "56:78"],
            ["13:57", "24:68"],
            ["15:26", "37:48"],
            ["16:38", "25:47"],
        ],
    },
    10: {
        4: [
            ["12:35", "67:810"],
            ["23:46", "78:19"],
            ["34:57", "89:210"],
            ["45:68", "910:13"],
            ["56:79", "110:24"],
        ],
    },
    12: {
        4: [
            ["12:34", "56:78", "910:1112"],
            ["13:57", "24:68", "911:1012"],
            ["48:912", "67:1011", "1112:23"],
            ["15:26", "37:48", "910:1112"],
            ["16:27", "38:49", "1011:1112"],
        ],
    },
}

POINT_TABLE = {1: 100, 2: 80, 3: 65, 4: 55, 5: 45, 6: 37, 7: 30, 8: 24}

# =========================================================
# 유틸
# =========================================================
def safe_int(v, default=0):
    try:
        return int(v)
    except:
        return default

def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M")

def default_rank_df():
    return pd.DataFrame(columns=["이름", "현재포인트", "총경기", "총승", "총득실"])

def default_history_df():
    return pd.DataFrame(columns=[
        "대회ID", "날짜", "대회명", "그룹", "방식",
        "이름", "페어명",
        "순위", "최종구분",
        "승", "패", "득실", "총득점",
        "획득포인트"
    ])

def load_json(path, default_value):
    if not os.path.exists(path):
        return default_value
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default_value

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# =========================================================
# 랭킹 / 기록 / 대회 저장소
# =========================================================
def load_rank():
    if not os.path.exists(RANK_FILE):
        return default_rank_df()
    df = pd.read_csv(RANK_FILE)
    for col in ["이름", "현재포인트", "총경기", "총승", "총득실"]:
        if col not in df.columns:
            df[col] = 0 if col != "이름" else ""
    for col in ["현재포인트", "총경기", "총승", "총득실"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    return df[["이름", "현재포인트", "총경기", "총승", "총득실"]]

def save_rank(df):
    if df.empty:
        default_rank_df().to_csv(RANK_FILE, index=False)
        return
    df = df.copy()
    for col in ["현재포인트", "총경기", "총승", "총득실"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
    df = df.sort_values(["현재포인트", "총승", "총득실"], ascending=[False, False, False]).reset_index(drop=True)
    df.to_csv(RANK_FILE, index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return default_history_df()
    df = pd.read_csv(HISTORY_FILE)
    base = default_history_df()
    for col in base.columns:
        if col not in df.columns:
            df[col] = "" if col in ["대회ID", "날짜", "대회명", "그룹", "방식", "이름", "페어명", "최종구분"] else 0
    for col in ["순위", "승", "패", "득실", "총득점", "획득포인트"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df[base.columns]

def save_history(df):
    if df.empty:
        default_history_df().to_csv(HISTORY_FILE, index=False)
        return
    df.to_csv(HISTORY_FILE, index=False)

def load_tournaments():
    data = load_json(TOURNAMENTS_FILE, {"tournaments": []})
    if "tournaments" not in data:
        data = {"tournaments": []}
    return data

def save_tournaments(data):
    save_json(TOURNAMENTS_FILE, data)

def rebuild_rank_from_history():
    hist = load_history()
    if hist.empty:
        save_rank(default_rank_df())
        return

    hist["승"] = pd.to_numeric(hist["승"], errors="coerce").fillna(0)
    hist["패"] = pd.to_numeric(hist["패"], errors="coerce").fillna(0)
    hist["득실"] = pd.to_numeric(hist["득실"], errors="coerce").fillna(0)
    hist["획득포인트"] = pd.to_numeric(hist["획득포인트"], errors="coerce").fillna(0)

    rank_df = (
        hist.groupby("이름", as_index=False)
        .agg({
            "획득포인트": "sum",
            "승": "sum",
            "패": "sum",
            "득실": "sum"
        })
        .rename(columns={
            "획득포인트": "현재포인트",
            "승": "총승",
            "득실": "총득실"
        })
    )
    rank_df["총경기"] = rank_df["총승"] + rank_df["패"]
    rank_df = rank_df[["이름", "현재포인트", "총경기", "총승", "총득실"]]
    rank_df["현재포인트"] = rank_df["현재포인트"].astype(int)
    rank_df["총경기"] = rank_df["총경기"].astype(int)
    rank_df["총승"] = rank_df["총승"].astype(int)
    rank_df["총득실"] = rank_df["총득실"].astype(int)
    save_rank(rank_df)

# =========================================================
# 세션 상태
# =========================================================
def init_state():
    defaults = {
        "players": [],
        "groups": {},
        "modes": {},
        "group_configs": {},
        "group_display_order": {},
        "shuffled_players": {},
        "schedule": {},
        "scores": {},
        "current_date": now_text(),
        "tournament_name": "정기 대회",
        "tournament_id": "",
        "loaded_tournament_id": "",
        "settled": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================================================
# 번호 / 이름 표시
# =========================================================
def get_player_no(group_name, player_name):
    order = st.session_state.group_display_order.get(group_name, [])
    try:
        return order.index(player_name) + 1
    except:
        return None

def player_label(group_name, player_name):
    no = get_player_no(group_name, player_name)
    if no is None:
        return player_name
    return f"{no}. {player_name}"

def team_label(group_name, team):
    return " / ".join([player_label(group_name, p) for p in team])

# =========================================================
# KDK 파싱
# =========================================================
def smart_split(s, n):
    res = []
    i = 0
    while i < len(s):
        two = s[i:i+2]
        if len(two) == 2 and two.isdigit() and 10 <= int(two) <= n:
            res.append(int(two))
            i += 2
        else:
            if s[i].isdigit():
                res.append(int(s[i]))
            i += 1
    return res

def parse_kdk_round(match_str, shuffled_players):
    n = len(shuffled_players)
    if ":" not in match_str:
        return None
    left, right = match_str.split(":")
    left_idx = smart_split(left, n)
    right_idx = smart_split(right, n)

    team1 = [shuffled_players[i-1] for i in left_idx if 1 <= i <= n]
    team2 = [shuffled_players[i-1] for i in right_idx if 1 <= i <= n]
    if not team1 or not team2:
        return None
    return [team1, team2]

def make_kdk_schedule(players, target_games):
    n = len(players)
    shuffled = random.sample(players, n)

    if n in KDK_TABLE and target_games in KDK_TABLE[n]:
        rounds_raw = KDK_TABLE[n][target_games]
        schedule = []
        for round_strs in rounds_raw:
            round_matches = []
            for ms in round_strs:
                m = parse_kdk_round(ms, shuffled)
                if m:
                    round_matches.append(m)
            if round_matches:
                schedule.append(round_matches)
        return schedule, shuffled

    schedule = []
    used_pairs = set()

    all_combos = []
    for i in range(n):
        for j in range(i+1, n):
            for k in range(n):
                for l in range(k+1, n):
                    s1 = {i, j}
                    s2 = {k, l}
                    if not (s1 & s2):
                        all_combos.append((i, j, k, l))
    random.shuffle(all_combos)

    num_courts = max(1, n // 4)

    for _ in range(target_games):
        round_matches = []
        used_in_round = set()

        for combo in all_combos:
            i, j, k, l = combo
            if any(x in used_in_round for x in [i, j, k, l]):
                continue

            pair1 = tuple(sorted([i, j]))
            pair2 = tuple(sorted([k, l]))
            if pair1 in used_pairs or pair2 in used_pairs:
                continue

            round_matches.append([[shuffled[i], shuffled[j]], [shuffled[k], shuffled[l]]])
            used_in_round.update([i, j, k, l])
            used_pairs.add(pair1)
            used_pairs.add(pair2)

            if len(round_matches) >= num_courts:
                break

        if round_matches:
            schedule.append(round_matches)

    return schedule, shuffled

# =========================================================
# 라운드로빈
# =========================================================
def make_round_robin(teams, target_games=None):
    teams = [list(t) for t in teams]
    if not teams:
        return []

    dummy = ["BYE"]
    arr = teams[:]
    if len(arr) % 2 == 1:
        arr.append(dummy)

    n = len(arr)
    total_rounds = n - 1
    rounds = []

    for _ in range(total_rounds):
        rd = []
        for i in range(n // 2):
            t1 = arr[i]
            t2 = arr[n - 1 - i]
            if t1 != dummy and t2 != dummy:
                rd.append([t1, t2])
        rounds.append(rd)
        arr = [arr[0]] + [arr[-1]] + arr[1:-1]

    if target_games is not None:
        target_games = min(target_games, len(rounds))
        rounds = rounds[:target_games]

    return rounds

# =========================================================
# 그룹 배분 / 페어링
# =========================================================
def distribute_players_snake(players_sorted, group_sizes):
    group_names = list(group_sizes.keys())
    groups = {g: [] for g in group_names}
    remain = group_sizes.copy()

    idx = 0
    direction = 1
    order = group_names[:]

    while idx < len(players_sorted) and sum(remain.values()) > 0:
        seq = order if direction == 1 else order[::-1]
        for g in seq:
            if idx >= len(players_sorted):
                break
            if remain[g] > 0:
                groups[g].append(players_sorted[idx])
                remain[g] -= 1
                idx += 1
        direction *= -1

    return groups

def make_fixed_pairs_by_rank(group_players, rank_map):
    ordered = sorted(group_players, key=lambda x: rank_map.get(x, 0), reverse=True)
    pairs = []
    left = 0
    right = len(ordered) - 1
    while left < right:
        pairs.append([ordered[left], ordered[right]])
        left += 1
        right -= 1
    if left == right:
        pairs.append([ordered[left]])
    return pairs

# =========================================================
# 통계 계산
# =========================================================
def calc_individual_stats(group_name):
    players = st.session_state.groups.get(group_name, [])
    stats = {p: {"승": 0, "패": 0, "득실": 0, "총득점": 0} for p in players}

    for key, data in st.session_state.scores.items():
        if key[0] != group_name:
            continue
        t1, t2 = data["teams"]
        s1, s2 = data["score"]

        if s1 == 0 and s2 == 0:
            continue

        for team, my_s, op_s in [(list(t1), s1, s2), (list(t2), s2, s1)]:
            for p in team:
                if p in stats:
                    if my_s > op_s:
                        stats[p]["승"] += 1
                    elif my_s < op_s:
                        stats[p]["패"] += 1
                    stats[p]["득실"] += (my_s - op_s)
                    stats[p]["총득점"] += my_s

    sorted_players = sorted(
        stats.items(),
        key=lambda x: (x[1]["승"], x[1]["득실"], x[1]["총득점"]),
        reverse=True
    )
    return sorted_players

def calc_pair_stats(group_name):
    pair_stats = {}
    team_order = []

    for rd in st.session_state.schedule.get(group_name, []):
        for t1, t2 in rd:
            for team in [t1, t2]:
                key = tuple(team)
                if key not in pair_stats:
                    pair_stats[key] = {"승": 0, "패": 0, "득실": 0, "총득점": 0}
                    team_order.append(key)

    for key, data in st.session_state.scores.items():
        if key[0] != group_name:
            continue
        t1, t2 = tuple(data["teams"][0]), tuple(data["teams"][1])
        s1, s2 = data["score"]

        if s1 == 0 and s2 == 0:
            continue

        if t1 in pair_stats:
            if s1 > s2:
                pair_stats[t1]["승"] += 1
            elif s1 < s2:
                pair_stats[t1]["패"] += 1
            pair_stats[t1]["득실"] += (s1 - s2)
            pair_stats[t1]["총득점"] += s1

        if t2 in pair_stats:
            if s2 > s1:
                pair_stats[t2]["승"] += 1
            elif s2 < s1:
                pair_stats[t2]["패"] += 1
            pair_stats[t2]["득실"] += (s2 - s1)
            pair_stats[t2]["총득점"] += s2

    sorted_pairs = sorted(
        pair_stats.items(),
        key=lambda x: (x[1]["승"], x[1]["득실"], x[1]["총득점"]),
        reverse=True
    )
    return sorted_pairs

def placement_label(mode, rank):
    if mode in ["KDK", "단식"]:
        if rank in [1, 2]:
            return "우승"
        elif rank in [3, 4]:
            return "준우승"
        elif rank in [5, 6]:
            return "3위"
        return f"{rank}위"
    else:
        return f"{rank}위"

def points_by_rank(rank):
    return POINT_TABLE.get(rank, max(10, 25 - rank * 2))

# =========================================================
# 대회 저장 / 불러오기 / 삭제
# =========================================================
def serialize_scores(scores):
    rows = []
    for (g, ri, mi), data in scores.items():
        rows.append({
            "group": g,
            "round": ri,
            "match": mi,
            "team1": list(data["teams"][0]),
            "team2": list(data["teams"][1]),
            "score1": data["score"][0],
            "score2": data["score"][1],
        })
    return rows

def deserialize_scores(score_rows):
    scores = {}
    for item in score_rows:
        key = (item["group"], int(item["round"]), int(item["match"]))
        scores[key] = {
            "teams": (tuple(item["team1"]), tuple(item["team2"])),
            "score": (safe_int(item["score1"]), safe_int(item["score2"]))
        }
    return scores

def build_tournament_payload():
    return {
        "tournament_id": st.session_state.tournament_id,
        "tournament_name": st.session_state.tournament_name,
        "current_date": st.session_state.current_date,
        "groups": st.session_state.groups,
        "modes": st.session_state.modes,
        "group_configs": st.session_state.group_configs,
        "group_display_order": st.session_state.group_display_order,
        "shuffled_players": st.session_state.shuffled_players,
        "schedule": st.session_state.schedule,
        "scores": serialize_scores(st.session_state.scores),
        "settled": st.session_state.settled,
        "updated_at": now_text()
    }

def save_current_tournament():
    data = load_tournaments()

    if not st.session_state.tournament_id:
        st.session_state.tournament_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"

    payload = build_tournament_payload()
    found = False

    for i, t in enumerate(data["tournaments"]):
        if t.get("tournament_id") == st.session_state.tournament_id:
            created_at = t.get("created_at", now_text())
            payload["created_at"] = created_at
            data["tournaments"][i] = payload
            found = True
            break

    if not found:
        payload["created_at"] = now_text()
        data["tournaments"].append(payload)

    save_tournaments(data)

def load_tournament_to_session(tid):
    data = load_tournaments()
    target = None
    for t in data["tournaments"]:
        if t.get("tournament_id") == tid:
            target = t
            break
    if not target:
        return False

    st.session_state.tournament_id = target.get("tournament_id", "")
    st.session_state.loaded_tournament_id = target.get("tournament_id", "")
    st.session_state.tournament_name = target.get("tournament_name", "정기 대회")
    st.session_state.current_date = target.get("current_date", now_text())
    st.session_state.groups = target.get("groups", {})
    st.session_state.modes = target.get("modes", {})
    st.session_state.group_configs = target.get("group_configs", {})
    st.session_state.group_display_order = target.get("group_display_order", {})
    st.session_state.shuffled_players = target.get("shuffled_players", {})
    st.session_state.schedule = target.get("schedule", {})
    st.session_state.scores = deserialize_scores(target.get("scores", []))
    st.session_state.settled = target.get("settled", False)
    return True

def delete_tournament(tid):
    data = load_tournaments()
    data["tournaments"] = [t for t in data["tournaments"] if t.get("tournament_id") != tid]
    save_tournaments(data)

    hist = load_history()
    if not hist.empty and "대회ID" in hist.columns:
        hist = hist[hist["대회ID"] != tid]
        save_history(hist)
        rebuild_rank_from_history()

# =========================================================
# 결과 정산
# =========================================================
def settle_current_tournament():
    if not st.session_state.tournament_id:
        st.session_state.tournament_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"

    hist = load_history()
    hist = hist[hist["대회ID"] != st.session_state.tournament_id].copy()

    new_rows = []

    for g in st.session_state.schedule.keys():
        mode = st.session_state.modes.get(g, "KDK")

        if mode == "고정페어":
            sorted_pairs = calc_pair_stats(g)
            for rank, (pair, s) in enumerate(sorted_pairs, start=1):
                pts = points_by_rank(rank)
                pair_name = " / ".join([player_label(g, p) for p in pair])
                place = placement_label(mode, rank)

                for member in pair:
                    new_rows.append({
                        "대회ID": st.session_state.tournament_id,
                        "날짜": st.session_state.current_date,
                        "대회명": st.session_state.tournament_name,
                        "그룹": g,
                        "방식": mode,
                        "이름": member,
                        "페어명": pair_name,
                        "순위": rank,
                        "최종구분": place,
                        "승": s["승"],
                        "패": s["패"],
                        "득실": s["득실"],
                        "총득점": s["총득점"],
                        "획득포인트": pts
                    })
        else:
            sorted_players = calc_individual_stats(g)
            for rank, (name, s) in enumerate(sorted_players, start=1):
                pts = points_by_rank(rank)
                place = placement_label(mode, rank)
                new_rows.append({
                    "대회ID": st.session_state.tournament_id,
                    "날짜": st.session_state.current_date,
                    "대회명": st.session_state.tournament_name,
                    "그룹": g,
                    "방식": mode,
                    "이름": name,
                    "페어명": "",
                    "순위": rank,
                    "최종구분": place,
                    "승": s["승"],
                    "패": s["패"],
                    "득실": s["득실"],
                    "총득점": s["총득점"],
                    "획득포인트": pts
                })

    hist = pd.concat([hist, pd.DataFrame(new_rows)], ignore_index=True)
    save_history(hist)
    rebuild_rank_from_history()

    st.session_state.settled = True
    save_current_tournament()

# =========================================================
# HTML 렌더
# =========================================================
def render_matrix_html(headers, row_labels, data_2d, self_mask=None):
    html = ["<div class='matrix-wrap'><table class='matrix-table'>"]
    html.append("<thead><tr><th>선수</th>")
    for h in headers:
        html.append(f"<th>{h}</th>")
    html.append("</tr></thead><tbody>")

    for i, row_name in enumerate(row_labels):
        html.append(f"<tr><td class='row-head'>{row_name}</td>")
        for j, cell in enumerate(data_2d[i]):
            classes = []
            if self_mask and self_mask(i, j):
                classes.append("self-cell")
            elif str(cell).strip() in ["", "-", "·"]:
                classes.append("empty-cell")
            class_attr = f" class='{' '.join(classes)}'" if classes else ""
            html.append(f"<td{class_attr}>{cell}</td>")
        html.append("</tr>")

    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)

def render_result_table(rows):
    html = ["<div class='result-wrap'><table class='result-table'>"]
    html.append("""
    <thead>
        <tr>
            <th>순위</th>
            <th>최종구분</th>
            <th>이름/페어</th>
            <th>승</th>
            <th>패</th>
            <th>득실</th>
            <th>총득점</th>
            <th>포인트</th>
        </tr>
    </thead>
    <tbody>
    """)

    for idx, r in enumerate(rows):
        cls = ""
        if idx == 0:
            cls = "top-gold"
        elif idx == 1:
            cls = "top-silver"
        elif idx == 2:
            cls = "top-bronze"

        html.append(f"""
        <tr class="{cls}">
            <td>{r['순위']}</td>
            <td>{r['최종구분']}</td>
            <td class='row-head'>{r['이름']}</td>
            <td>{r['승']}</td>
            <td>{r['패']}</td>
            <td>{r['득실']}</td>
            <td>{r['총득점']}</td>
            <td>{r['획득포인트']}</td>
        </tr>
        """)

    html.append("</tbody></table></div>")
    st.markdown("".join(html), unsafe_allow_html=True)

# =========================================================
# 매트릭스
# =========================================================
def build_individual_matrix(group_name):
    players = st.session_state.groups[group_name]
    labels = [player_label(group_name, p) for p in players]
    matrix = [["-" for _ in players] for _ in players]

    for i in range(len(players)):
        matrix[i][i] = "—"

    # 상대 전적 누적 표기
    record = {p: {op: {"승": 0, "패": 0, "득점": 0, "실점": 0} for op in players if op != p} for p in players}

    for key, data in st.session_state.scores.items():
        if key[0] != group_name:
            continue
        t1, t2 = list(data["teams"][0]), list(data["teams"][1])
        s1, s2 = data["score"]

        if s1 == 0 and s2 == 0:
            continue

        for p1 in t1:
            for p2 in t2:
                if p1 in record and p2 in record[p1]:
                    record[p1][p2]["득점"] += s1
                    record[p1][p2]["실점"] += s2
                    if s1 > s2:
                        record[p1][p2]["승"] += 1
                    elif s1 < s2:
                        record[p1][p2]["패"] += 1

                if p2 in record and p1 in record[p2]:
                    record[p2][p1]["득점"] += s2
                    record[p2][p1]["실점"] += s1
                    if s2 > s1:
                        record[p2][p1]["승"] += 1
                    elif s2 < s1:
                        record[p2][p1]["패"] += 1

    idx_map = {p: i for i, p in enumerate(players)}
    for p in players:
        for op in players:
            if p == op:
                continue
            d = record[p].get(op)
            if d and (d["승"] or d["패"] or d["득점"] or d["실점"]):
                txt = f"{d['승']}W {d['패']}L<br>{d['득점']}:{d['실점']}"
                matrix[idx_map[p]][idx_map[op]] = txt
            else:
                matrix[idx_map[p]][idx_map[op]] = "·"

    render_matrix_html(
        headers=labels,
        row_labels=labels,
        data_2d=matrix,
        self_mask=lambda i, j: i == j
    )

def build_pair_matrix(group_name):
    seen = []
    seen_set = set()
    for rd in st.session_state.schedule[group_name]:
        for t1, t2 in rd:
            for t in [tuple(t1), tuple(t2)]:
                if t not in seen_set:
                    seen_set.add(t)
                    seen.append(t)

    team_labels = [" / ".join([player_label(group_name, p) for p in t]) for t in seen]
    idx_map = {tuple(seen[i]): i for i in range(len(seen))}
    matrix = [["-" for _ in seen] for _ in seen]

    for i in range(len(seen)):
        matrix[i][i] = "—"

    record = {tuple(t): {} for t in seen}

    for key, data in st.session_state.scores.items():
        if key[0] != group_name:
            continue
        t1 = tuple(data["teams"][0])
        t2 = tuple(data["teams"][1])
        s1, s2 = data["score"]
        if s1 == 0 and s2 == 0:
            continue

        record.setdefault(t1, {})
        record.setdefault(t2, {})
        record[t1][t2] = f"{s1}:{s2}"
        record[t2][t1] = f"{s2}:{s1}"

    for a in seen:
        for b in seen:
            if a == b:
                continue
            i = idx_map[a]
            j = idx_map[b]
            matrix[i][j] = record.get(a, {}).get(b, "·")

    render_matrix_html(
        headers=team_labels,
        row_labels=team_labels,
        data_2d=matrix,
        self_mask=lambda i, j: i == j
    )

def draw_match_matrix(group_name):
    mode = st.session_state.modes[group_name]

    st.markdown(f"""
    <div class='card'>
        <div class='card-title'>📊 GROUP {group_name} · 경기 현황</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3.4, 2])

    with col1:
        st.markdown("**상대별 전적 매트릭스**")
        if mode == "고정페어":
            build_pair_matrix(group_name)
        else:
            build_individual_matrix(group_name)

    with col2:
        st.markdown("**현재 순위**")

        if mode == "고정페어":
            sorted_pairs = calc_pair_stats(group_name)
            rows = []
            for rank, (pair, s) in enumerate(sorted_pairs, 1):
                rows.append({
                    "순위": rank,
                    "최종구분": placement_label(mode, rank),
                    "이름": " / ".join([player_label(group_name, p) for p in pair]),
                    "승": s["승"],
                    "패": s["패"],
                    "득실": f"{s['득실']:+d}",
                    "총득점": s["총득점"],
                    "획득포인트": points_by_rank(rank)
                })
            if rows:
                render_result_table(rows)
        else:
            sorted_stats = calc_individual_stats(group_name)
            rows = []
            for rank, (name, s) in enumerate(sorted_stats, 1):
                rows.append({
                    "순위": rank,
                    "최종구분": placement_label(mode, rank),
                    "이름": player_label(group_name, name),
                    "승": s["승"],
                    "패": s["패"],
                    "득실": f"{s['득실']:+d}",
                    "총득점": s["총득점"],
                    "획득포인트": points_by_rank(rank)
                })
            if rows:
                render_result_table(rows)

# =========================================================
# 사이드바
# =========================================================
st.sidebar.markdown("""
<div style='text-align:center; padding: 16px 0 8px;'>
    <div style='font-family: Bebas Neue, sans-serif; font-size:1.95rem; 
         color:#156348; letter-spacing:0.12em;'>DU-RYU TENNIS</div>
    <div style='color:#5d8f7f; font-size:0.72rem; letter-spacing:0.28em;'>RANKING SYSTEM</div>
</div>
<hr style='border-color:#bfe8d7; margin:12px 0;'>
""", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "메뉴",
    ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과 & 정산", "📜 대회 기록", "⚙️ 관리자 센터"],
    label_visibility="collapsed"
)

# =========================================================
# 1. 랭킹보드
# =========================================================
if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>PLAYER RANKING BOARD</div>", unsafe_allow_html=True)

    df = load_rank()

    if df.empty:
        st.markdown("""
        <div class='info-box'>
            <p>🎾 아직 등록된 선수가 없습니다.</p>
            <p>관리자 센터에서 대회를 생성하고 결과를 정산하면 자동으로 랭킹이 반영됩니다.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = df.sort_values(["현재포인트", "총승", "총득실"], ascending=[False, False, False]).reset_index(drop=True)

        top_n = min(3, len(df))
        cols = st.columns(top_n)
        labels = ["🥇 1위", "🥈 2위", "🥉 3위"]

        for i in range(top_n):
            row = df.iloc[i]
            with cols[i]:
                st.markdown(f"""
                <div class='card' style='text-align:center; padding:24px 16px;'>
                    <div style='font-size:2rem;'>{labels[i]}</div>
                    <div style='font-family:Bebas Neue,sans-serif; font-size:1.9rem; color:#156348; margin:8px 0;'>
                        {row['이름']}
                    </div>
                    <div style='font-size:2rem; font-weight:800; color:#ffb703;'>{int(row['현재포인트'])}</div>
                    <div style='color:#5d8f7f; font-size:0.75rem; font-weight:700;'>POINTS</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        for i, row in df.iterrows():
            rank = i + 1
            rank_class = {1: "top1", 2: "top2", 3: "top3"}.get(rank, "")
            st.markdown(f"""
            <div class='rank-row'>
                <div class='rank-num {rank_class}'>{rank}</div>
                <div class='rank-name'>{row['이름']}</div>
                <div>
                    <div class='rank-pts'>{int(row['현재포인트'])}</div>
                    <div class='rank-pts-label'>pts</div>
                </div>
                <div style='margin-left:14px;'>
                    <span class='stat-badge badge-win'>승 {int(row['총승'])}</span>
                    <span class='stat-badge badge-diff'>득실 {int(row['총득실']):+d}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =========================================================
# 2. 대진표/입력
# =========================================================
elif menu == "📅 대진표/입력":
    st.markdown("<div class='main-title'>MATCH S
