import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# =============================
# 페이지 설정 및 CSS
# =============================
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹", page_icon="🎾")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

:root {
    --court-green: #1a4731;
    --court-light: #2d7a52;
    --accent-gold: #f0c040;
    --accent-red: #e63946;
    --bg-dark: #0d1b14;
    --bg-card: #132a1e;
    --bg-card2: #1a3526;
    --text-bright: #f0f4f0;
    --text-muted: #8aab96;
    --border: #2d5c3f;
}

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif;
    background-color: var(--bg-dark) !important;
    color: var(--text-bright) !important;
}

.stApp { background-color: var(--bg-dark) !important; }

/* 사이드바 */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1b14 0%, #1a3526 100%) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * { color: var(--text-bright) !important; }
[data-testid="stSidebar"] .stRadio label { 
    padding: 10px 14px; border-radius: 8px; cursor: pointer;
    transition: all 0.2s; margin-bottom: 4px; display: block;
    border: 1px solid transparent;
}
[data-testid="stSidebar"] .stRadio label:hover { 
    background: var(--bg-card2); border-color: var(--border);
}

/* 메인 타이틀 */
.main-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 3.8rem;
    letter-spacing: 0.12em;
    color: var(--accent-gold);
    text-align: center;
    padding: 10px 0 4px;
    text-shadow: 0 0 40px rgba(240,192,64,0.3);
    line-height: 1.1;
}
.sub-title {
    text-align: center;
    color: var(--text-muted);
    font-size: 0.85rem;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    margin-bottom: 30px;
}

/* 카드 */
.card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 12px;
}
.card-title {
    font-family: 'Bebas Neue', sans-serif;
    font-size: 1.4rem;
    letter-spacing: 0.08em;
    color: var(--accent-gold);
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 8px;
}

/* 랭킹 카드 */
.rank-row {
    display: flex; align-items: center; padding: 12px 16px;
    border-radius: 10px; margin-bottom: 8px;
    background: var(--bg-card2); border: 1px solid var(--border);
    transition: transform 0.15s;
}
.rank-row:hover { transform: translateX(4px); }
.rank-num { 
    font-family: 'Bebas Neue', sans-serif; font-size: 1.8rem;
    color: var(--text-muted); width: 50px; text-align: center;
}
.rank-num.top1 { color: var(--accent-gold); font-size: 2.2rem; }
.rank-num.top2 { color: #c0c0c0; font-size: 2rem; }
.rank-num.top3 { color: #cd7f32; font-size: 1.9rem; }
.rank-name { flex: 1; font-size: 1.1rem; font-weight: 600; padding: 0 16px; }
.rank-pts { 
    font-family: 'Bebas Neue', sans-serif; font-size: 1.5rem;
    color: var(--accent-gold); letter-spacing: 0.05em;
}
.rank-pts-label { color: var(--text-muted); font-size: 0.7rem; text-align: right; }

/* 경기 카드 */
.match-card {
    background: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 10px;
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    gap: 12px;
    align-items: center;
}
.team-box {
    text-align: center; padding: 10px;
    background: rgba(45,122,82,0.15);
    border-radius: 8px; border: 1px solid rgba(45,122,82,0.3);
}
.team-box.team2 {
    background: rgba(230,57,70,0.1);
    border-color: rgba(230,57,70,0.25);
}
.team-label {
    font-size: 0.65rem; letter-spacing: 0.2em;
    color: var(--text-muted); text-transform: uppercase; margin-bottom: 4px;
}
.team-players { font-size: 1rem; font-weight: 700; color: var(--text-bright); }
.vs-badge {
    font-family: 'Bebas Neue', sans-serif; font-size: 1.6rem;
    color: var(--accent-red); text-align: center; line-height: 1;
}
.round-header {
    background: linear-gradient(90deg, var(--court-green), transparent);
    padding: 8px 16px; border-radius: 6px;
    font-family: 'Bebas Neue', sans-serif; font-size: 1.1rem;
    letter-spacing: 0.15em; color: var(--accent-gold);
    margin: 18px 0 10px;
}

/* 통계 배지 */
.stat-badge {
    display: inline-block; padding: 4px 12px;
    border-radius: 20px; font-size: 0.8rem; font-weight: 600;
    margin: 2px;
}
.badge-win { background: rgba(45,122,82,0.3); color: #6dd99b; border: 1px solid #2d7a52; }
.badge-lose { background: rgba(230,57,70,0.2); color: #f08080; border: 1px solid rgba(230,57,70,0.4); }
.badge-diff { background: rgba(240,192,64,0.2); color: var(--accent-gold); border: 1px solid rgba(240,192,64,0.4); }

/* 폼 요소 */
.stTextInput input, .stTextArea textarea, .stNumberInput input, .stSelectbox div[data-baseweb] {
    background: var(--bg-card2) !important;
    border: 1px solid var(--border) !important;
    color: var(--text-bright) !important;
    border-radius: 8px !important;
}
.stButton > button {
    background: var(--court-green) !important;
    color: var(--accent-gold) !important;
    border: 1px solid var(--court-light) !important;
    border-radius: 8px !important;
    font-family: 'Bebas Neue', sans-serif !important;
    letter-spacing: 0.1em !important;
    font-size: 1rem !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: var(--court-light) !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 15px rgba(45,122,82,0.4) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, var(--court-light), var(--court-green)) !important;
    box-shadow: 0 4px 20px rgba(45,122,82,0.5) !important;
}
div[data-testid="stTab"] button {
    color: var(--text-muted) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
}
div[data-testid="stTab"] button[aria-selected="true"] {
    color: var(--accent-gold) !important;
    border-bottom-color: var(--accent-gold) !important;
}

/* 데이터프레임 */
[data-testid="stDataFrame"] { border: 1px solid var(--border) !important; border-radius: 10px; overflow: hidden; }
[data-testid="stDataFrame"] th { background: var(--court-green) !important; color: var(--accent-gold) !important; }

/* 구분선 */
hr { border-color: var(--border) !important; }

/* 알림 */
.stSuccess, .stInfo, .stWarning, .stError { border-radius: 10px !important; }

/* 점수 입력 특화 */
.score-row {
    display: flex; align-items: center; gap: 10px;
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 10px; padding: 12px 16px; margin-bottom: 8px;
}

/* KDK 설명 박스 */
.info-box {
    background: linear-gradient(135deg, rgba(26,71,49,0.5), rgba(13,27,20,0.8));
    border: 1px solid var(--court-light);
    border-left: 4px solid var(--accent-gold);
    border-radius: 10px; padding: 16px 20px; margin-bottom: 16px;
}
.info-box p { color: var(--text-muted); margin: 4px 0; font-size: 0.9rem; }
.info-box strong { color: var(--text-bright); }

/* 순위표 행 색상 */
.rank-1st { background: rgba(240,192,64,0.1) !important; }
.rank-2nd { background: rgba(192,192,192,0.07) !important; }
.rank-3rd { background: rgba(205,127,50,0.07) !important; }

/* 스크롤바 */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: var(--bg-dark); }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)

# =============================
# 데이터 파일 경로
# =============================
RANK_FILE = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"

# =============================
# KDK 한울방식 대진표 데이터
# 형식: "팀A:팀B" (숫자 = 참가자 번호, 두 자리는 붙여쓰기)
# 예) "12:34" → 1&2번 vs 3&4번
# =============================
KDK_TABLE = {
    # 인원수: {목표경기수: [라운드별 매치 문자열 목록]}
    4: {
        3: [["12:34"], ["13:24"], ["14:23"]],
    },
    6: {
        3: [["13:24", "56:XX"], ["15:46", "23:XX"], ["26:34", "XX:XX"]],
        # 6명 4게임
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
            ["45:68", "910:13"],  # 910 = 9&10번
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

# =============================
# 대진표 파싱 함수
# =============================
def smart_split(s, n):
    """번호 문자열을 파싱. 10 이상 숫자는 두 자리로 인식."""
    res = []
    i = 0
    while i < len(s):
        two = s[i:i+2]
        if len(two) == 2 and two.isdigit() and int(two) <= n and int(two) >= 10:
            res.append(int(two)); i += 2
        else:
            if s[i].isdigit():
                res.append(int(s[i])); i += 1
            else:
                i += 1  # 'X' 등 패딩 문자 무시
    return res

def parse_kdk_round(match_str, shuffled_players):
    """'12:34' 형태 문자열 → [[플레이어,플레이어],[플레이어,플레이어]]"""
    n = len(shuffled_players)
    if ':' not in match_str:
        return None
    left, right = match_str.split(':')
    left_idx = smart_split(left, n)
    right_idx = smart_split(right, n)
    # 'X' 패딩(바이 인원)은 인덱스 범위 초과로 필터
    team1 = [shuffled_players[i-1] for i in left_idx if 1 <= i <= n]
    team2 = [shuffled_players[i-1] for i in right_idx if 1 <= i <= n]
    if not team1 or not team2:
        return None
    return [team1, team2]

def make_kdk_schedule(players, target_games):
    """KDK 대진표 생성. 한울방식 → 없으면 자동생성."""
    n = len(players)
    shuffled = random.sample(players, n)

    # 한울방식 테이블 우선 적용
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

    # 자동생성: KDK 규칙 준수 대진 생성
    # 원칙: 각 플레이어는 매 라운드 다른 파트너, 다른 상대와 만남
    schedule = []
    used_pairs = set()  # 이미 파트너였던 쌍
    used_opponents = set()  # 이미 상대였던 쌍

    all_combos = []
    for i in range(n):
        for j in range(i+1, n):
            for k in range(n):
                for l in range(k+1, n):
                    s = {i, j}
                    t = {k, l}
                    if not s & t:
                        all_combos.append((i, j, k, l))

    random.shuffle(all_combos)

    total_rounds = target_games  # 최소한 1인당 target_games 경기 보장 시도
    num_courts = n // 4

    for r in range(total_rounds):
        round_matches = []
        used_in_round = set()
        for combo in all_combos:
            i, j, k, l = combo
            if any(x in used_in_round for x in [i,j,k,l]):
                continue
            pair1 = tuple(sorted([i,j]))
            pair2 = tuple(sorted([k,l]))
            opp1 = tuple(sorted([i,k])); opp2 = tuple(sorted([i,l]))
            opp3 = tuple(sorted([j,k])); opp4 = tuple(sorted([j,l]))
            if (pair1 in used_pairs or pair2 in used_pairs):
                continue
            round_matches.append([[shuffled[i], shuffled[j]], [shuffled[k], shuffled[l]]])
            used_in_round.update([i,j,k,l])
            used_pairs.add(pair1); used_pairs.add(pair2)
            used_opponents.update([opp1,opp2,opp3,opp4])
            if len(round_matches) >= num_courts:
                break
        if round_matches:
            schedule.append(round_matches)

    return schedule, shuffled

# =============================
# 고정페어 / 단식 리그전
# =============================
def make_round_robin(teams, target_games=None):
    """리그전 대진표 (팀 단위 입력)"""
    matches = []
    for i in range(len(teams)):
        for j in range(i+1, len(teams)):
            matches.append([teams[i], teams[j]])
    random.shuffle(matches)

    rounds = []
    while matches:
        curr_round = []
        used = set()
        remaining = []
        for m in matches:
            p_set = set()
            for p in m[0]: p_set.add(p)
            for p in m[1]: p_set.add(p)
            if not (p_set & used):
                curr_round.append(m)
                used.update(p_set)
            else:
                remaining.append(m)
        if curr_round:
            rounds.append(curr_round)
        matches = remaining
        if not curr_round:
            break  # 무한루프 방지

    return rounds

# =============================
# 데이터 로드/저장
# =============================
def load_rank():
    if not os.path.exists(RANK_FILE):
        return pd.DataFrame(columns=["이름", "현재포인트", "총경기", "총승", "총득실"])
    df = pd.read_csv(RANK_FILE)
    for col in ["현재포인트", "총경기", "총승", "총득실"]:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    return df

def save_rank(df):
    df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
    df.to_csv(RANK_FILE, index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["날짜", "대회명", "그룹", "방식", "이름", "순위", "승", "득실", "획득포인트"])
    return pd.read_csv(HISTORY_FILE)

def save_history(df):
    df.to_csv(HISTORY_FILE, index=False)

# =============================
# 포인트 계산 (KDK 순위 반영)
# =============================
POINT_TABLE = {1: 100, 2: 80, 3: 65, 4: 55, 5: 45, 6: 37, 7: 30, 8: 24}

def calc_kdk_stats(group_name):
    """KDK 방식: 개인별 승수/득실차 집계 → 순위 결정"""
    players = st.session_state.groups[group_name]
    mode = st.session_state.modes[group_name]
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

    # 순위: 1순위-승수, 2순위-득실차, 3순위-총득점
    sorted_players = sorted(
        stats.items(),
        key=lambda x: (x[1]["승"], x[1]["득실"], x[1]["총득점"]),
        reverse=True
    )
    return sorted_players  # [(이름, {stats}), ...]

# =============================
# 세션 상태 초기화
# =============================
def init_state():
    defaults = {
        "players": [], "groups": {}, "modes": {}, "shuffled_players": {},
        "schedule": {}, "scores": {},
        "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tournament_name": "정기 대회"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============================
# 경기 현황 매트릭스
# =============================
def draw_match_matrix(group_name):
    players = st.session_state.groups[group_name]
    mode = st.session_state.modes[group_name]
    sorted_stats = calc_kdk_stats(group_name)

    st.markdown(f"""
    <div class='card'>
        <div class='card-title'>📊 GROUP {group_name} · 경기 현황</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown("**상대별 전적**")
        if mode in ["KDK", "단식"]:
            matrix = {p: {op: "-" for op in players} for p in players}
            for p in players:
                matrix[p][p] = "✕"

            for key, data in st.session_state.scores.items():
                if key[0] != group_name:
                    continue
                t1, t2 = list(data["teams"][0]), list(data["teams"][1])
                s1, s2 = data["score"]
                if s1 == 0 and s2 == 0:
                    continue
                for p1 in t1:
                    for p2 in t2:
                        if p1 in matrix and p2 in matrix[p1]:
                            matrix[p1][p2] = f"{s1}:{s2}"
                        if p2 in matrix and p1 in matrix[p2]:
                            matrix[p2][p1] = f"{s2}:{s1}"

            df_m = pd.DataFrame(matrix).T
            st.dataframe(df_m, use_container_width=True)
        else:
            # 고정페어 매트릭스
            teams_list = []
            seen = set()
            for rd in st.session_state.schedule[group_name]:
                for t1, t2 in rd:
                    for t in [tuple(t1), tuple(t2)]:
                        if t not in seen:
                            teams_list.append(t); seen.add(t)
            labels = {t: " & ".join(t) for t in teams_list}
            matrix = {labels[t]: {labels[op]: "-" for op in teams_list} for t in teams_list}
            for t in teams_list:
                matrix[labels[t]][labels[t]] = "✕"

            for key, data in st.session_state.scores.items():
                if key[0] != group_name:
                    continue
                t1k = tuple(data["teams"][0]); t2k = tuple(data["teams"][1])
                s1, s2 = data["score"]
                if s1 == 0 and s2 == 0: continue
                if t1k in labels and t2k in labels:
                    matrix[labels[t1k]][labels[t2k]] = f"{s1}:{s2}"
                    matrix[labels[t2k]][labels[t1k]] = f"{s2}:{s1}"
            st.dataframe(pd.DataFrame(matrix).T, use_container_width=True)

    with col2:
        st.markdown("**현재 순위**")
        rows = []
        for rank, (name, s) in enumerate(sorted_stats, 1):
            medal = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else f"{rank}위"
            rows.append({
                "순위": medal,
                "이름": name,
                "승": s["승"],
                "패": s["패"],
                "득실": f"{'+' if s['득실']>=0 else ''}{s['득실']}",
            })
        if rows:
            st.dataframe(pd.DataFrame(rows).set_index("순위"), use_container_width=True)

# =============================
# UI 사이드바
# =============================
st.sidebar.markdown("""
<div style='text-align:center; padding: 16px 0 8px;'>
    <div style='font-family: Bebas Neue, sans-serif; font-size:1.8rem; 
         color: #f0c040; letter-spacing:0.1em;'>두류 테니스</div>
    <div style='color: #8aab96; font-size:0.7rem; letter-spacing:0.3em;'>RANKING SYSTEM</div>
</div>
<hr style='border-color:#2d5c3f; margin:12px 0;'>
""", unsafe_allow_html=True)

menu = st.sidebar.radio(
    "메뉴",
    ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과 & 정산", "📜 대회 기록", "⚙️ 관리자 센터"],
    label_visibility="collapsed"
)

# =============================
# 🏆 랭킹보드
# =============================
if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>PLAYER RANKING BOARD</div>", unsafe_allow_html=True)

    df = load_rank()
    if df.empty:
        st.markdown("""
        <div class='info-box'>
            <p>🎾 아직 등록된 선수가 없습니다.</p>
            <p>관리자 센터에서 대회를 생성하고 결과를 입력하면 자동으로 랭킹이 집계됩니다.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)

        # TOP 3 하이라이트
        top_cols = st.columns(min(3, len(df)))
        podium_order = [0, 1, 2] if len(df) >= 3 else list(range(len(df)))
        labels = ["🥇 1위", "🥈 2위", "🥉 3위"]
        for col, idx in zip(top_cols, podium_order[:3]):
            row = df.iloc[idx]
            with col:
                st.markdown(f"""
                <div class='card' style='text-align:center; padding:24px 16px;'>
                    <div style='font-size:2.2rem;'>{labels[idx]}</div>
                    <div style='font-family:Bebas Neue,sans-serif; font-size:1.8rem; 
                         color:#f0c040; margin:8px 0;'>{row['이름']}</div>
                    <div style='font-size:2rem; font-weight:700; color:#f0c040;'>{int(row['현재포인트'])}</div>
                    <div style='color:#8aab96; font-size:0.75rem;'>POINTS</div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # 전체 순위표
        for i, row in df.iterrows():
            rank = i + 1
            rank_class = {1: "top1", 2: "top2", 3: "top3"}.get(rank, "")
            st.markdown(f"""
            <div class='rank-row'>
                <div class='rank-num {rank_class}'>{rank}</div>
                <div class='rank-name'>{row['이름']}</div>
                <div>
                    <div class='rank-pts'>{int(row.get('현재포인트', 0))}</div>
                    <div class='rank-pts-label'>pts</div>
                </div>
                <div style='margin-left:20px;'>
                    <span class='stat-badge badge-win'>승 {int(row.get('총승', 0))}</span>
                    <span class='stat-badge badge-diff'>득실 {int(row.get('총득실', 0)):+d}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)

# =============================
# 📅 대진표/입력
# =============================
elif menu == "📅 대진표/입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>경기 대진표 및 점수 입력</div>", unsafe_allow_html=True)

    if not st.session_state.schedule:
        st.markdown("""
        <div class='info-box'>
            <p>⚠️ 아직 대진표가 생성되지 않았습니다.</p>
            <p>관리자 센터 → 대회 생성 에서 대진표를 만들어주세요.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        tabs = st.tabs([f"  Group {g}  " for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                draw_match_matrix(g)
                st.divider()

                mode = st.session_state.modes[g]
                p_list = st.session_state.groups[g]

                # KDK 방식 안내
                if mode == "KDK":
                    st.markdown(f"""
                    <div class='info-box'>
                        <strong>KDK 방식</strong>
                        <p>• 매 경기 파트너가 바뀝니다 · 개인 승수/득실로 순위 결정</p>
                        <p>• 1순위: 승수 | 2순위: 득실차 | 3순위: 총득점</p>
                    </div>
                    """, unsafe_allow_html=True)

                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.markdown(f"<div class='round-header'>◆ ROUND {ri+1}</div>", unsafe_allow_html=True)

                    for mi, (t1, t2) in enumerate(rd):
                        score_key = (g, ri, mi)
                        existing = st.session_state.scores.get(score_key, {"score": (0, 0)})["score"]

                        t1_name = " & ".join(t1) if isinstance(t1[0], str) else t1[0]
                        t2_name = " & ".join(t2) if isinstance(t2[0], str) else t2[0]

                        # 번호 표시
                        if mode == "KDK":
                            def num_label(players_in_team, shuffled):
                                labels = []
                                for p in players_in_team:
                                    try: labels.append(f"({shuffled.index(p)+1}){p}")
                                    except: labels.append(p)
                                return " & ".join(labels)
                            shuffled = st.session_state.shuffled_players.get(g, p_list)
                            t1_disp = num_label(t1, shuffled)
                            t2_disp = num_label(t2, shuffled)
                        else:
                            t1_disp = t1_name
                            t2_disp = t2_name

                        c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 1])
                        with c1:
                            st.markdown(f"""
                            <div class='team-box'>
                                <div class='team-label'>Team A</div>
                                <div class='team-players'>{t1_disp}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            s1 = st.number_input("", 0, 10, existing[0],
                                                 key=f"s1_{g}_{ri}_{mi}", label_visibility="collapsed")
                        with c2:
                            st.markdown("<div class='vs-badge' style='margin-top:28px;'>VS</div>", unsafe_allow_html=True)
                        with c3:
                            pass
                        with c4:
                            st.markdown(f"""
                            <div class='team-box team2'>
                                <div class='team-label'>Team B</div>
                                <div class='team-players'>{t2_disp}</div>
                            </div>
                            """, unsafe_allow_html=True)
                            s2 = st.number_input("", 0, 10, existing[1],
                                                 key=f"s2_{g}_{ri}_{mi}", label_visibility="collapsed")
                        with c5:
                            st.markdown("<br>", unsafe_allow_html=True)
                            if st.button(f"💾 저장", key=f"btn_{g}_{ri}_{mi}"):
                                st.session_state.scores[score_key] = {
                                    "teams": (tuple(t1), tuple(t2)),
                                    "score": (s1, s2)
                                }
                                st.success(f"R{ri+1}-{mi+1} 저장!")
                                st.rerun()

# =============================
# 📊 경기결과 & 정산
# =============================
elif menu == "📊 경기결과 & 정산":
    st.markdown("<div class='main-title'>RESULTS & POINTS</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>최종 순위 및 포인트 정산</div>", unsafe_allow_html=True)

    if not st.session_state.schedule:
        st.warning("대진표가 없습니다.")
    else:
        for g in st.session_state.schedule.keys():
            st.markdown(f"<div class='card-title'>GROUP {g}</div>", unsafe_allow_html=True)
            sorted_stats = calc_kdk_stats(g)

            rows = []
            for rank, (name, s) in enumerate(sorted_stats, 1):
                pts = POINT_TABLE.get(rank, max(10, 25 - rank * 2))
                medal = ["🥇", "🥈", "🥉"][rank-1] if rank <= 3 else f"{rank}위"
                rows.append({
                    "순위": medal, "이름": name,
                    "승": s["승"], "패": s["패"],
                    "득실": f"{s['득실']:+d}",
                    "총득점": s["총득점"],
                    "획득포인트": pts
                })

            if rows:
                df = pd.DataFrame(rows).set_index("순위")
                st.dataframe(df, use_container_width=True)

            st.divider()

        # 정산 버튼
        if st.button("✅ 포인트 정산 및 랭킹 반영", type="primary"):
            rank_df = load_rank()
            hist_df = load_history()
            new_hist = []

            all_finalized = True
            for g in st.session_state.schedule.keys():
                sorted_stats = calc_kdk_stats(g)
                for rank, (name, s) in enumerate(sorted_stats, 1):
                    pts = POINT_TABLE.get(rank, max(10, 25 - rank * 2))

                    # 랭킹 업데이트
                    if name in rank_df["이름"].values:
                        rank_df.loc[rank_df["이름"] == name, "현재포인트"] += pts
                        rank_df.loc[rank_df["이름"] == name, "총경기"] += (s["승"] + s["패"])
                        rank_df.loc[rank_df["이름"] == name, "총승"] += s["승"]
                        rank_df.loc[rank_df["이름"] == name, "총득실"] += s["득실"]
                    else:
                        new_row = pd.DataFrame([{
                            "이름": name, "현재포인트": pts,
                            "총경기": s["승"]+s["패"],
                            "총승": s["승"], "총득실": s["득실"]
                        }])
                        rank_df = pd.concat([rank_df, new_row], ignore_index=True)

                    # 기록 추가
                    new_hist.append({
                        "날짜": st.session_state.current_date,
                        "대회명": st.session_state.tournament_name,
                        "그룹": g,
                        "방식": st.session_state.modes[g],
                        "이름": name, "순위": rank,
                        "승": s["승"], "득실": s["득실"],
                        "획득포인트": pts
                    })

            save_rank(rank_df)
            hist_df = pd.concat([hist_df, pd.DataFrame(new_hist)], ignore_index=True)
            save_history(hist_df)
            st.success("🎉 랭킹 반영 완료!")
            st.balloons()

# =============================
# 📜 대회 기록
# =============================
elif menu == "📜 대회 기록":
    st.markdown("<div class='main-title'>TOURNAMENT HISTORY</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>역대 대회 기록</div>", unsafe_allow_html=True)

    df = load_history()
    if df.empty:
        st.info("아직 대회 기록이 없습니다.")
    else:
        tournaments = df["대회명"].unique().tolist()
        selected = st.selectbox("대회 선택", ["전체"] + tournaments)
        if selected != "전체":
            df = df[df["대회명"] == selected]

        # 선수 검색
        search = st.text_input("선수명 검색", placeholder="이름 입력...")
        if search:
            df = df[df["이름"].str.contains(search)]

        st.dataframe(df.sort_values("날짜", ascending=False), use_container_width=True)

# =============================
# ⚙️ 관리자 센터
# =============================
elif menu == "⚙️ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN CENTER</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-title'>관리자 전용 패널</div>", unsafe_allow_html=True)

    pwd = st.text_input("🔒 관리자 비밀번호", type="password", placeholder="비밀번호를 입력하세요")
    if pwd == "0502":
        tab1, tab2 = st.tabs(["🎾 대회 생성", "🗑️ 데이터 관리"])

        with tab1:
            st.markdown("<div class='card-title'>새 대회 설정</div>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                st.session_state.tournament_name = st.text_input("대회명", st.session_state.tournament_name)
            with col_b:
                st.session_state.current_date = st.text_input("날짜", st.session_state.current_date)

            st.markdown("**참가자 입력** (쉼표로 구분)")
            raw_p = st.text_area("참가자 목록", placeholder="예: 홍길동, 김철수, 이영희, 박민준...")

            g_count = st.number_input("그룹 수", 1, 5, 1)

            g_configs = {}
            st.markdown("**그룹별 설정**")
            for i in range(int(g_count)):
                gn = chr(65+i)
                with st.expander(f"Group {gn} 설정", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        sz = st.number_input(f"인원수", 2, 20, 8, key=f"sz_{gn}")
                    with c2:
                        md = st.selectbox(f"진행방식", ["KDK", "고정페어", "단식"], key=f"md_{gn}",
                                         help="KDK: 파트너 변경 복식 | 고정페어: 팀 유지 복식 | 단식: 1:1")
                    with c3:
                        gc = st.selectbox(f"1인당 경기수", [3, 4, 5, 6], index=1, key=f"gc_{gn}")

                    if md == "KDK":
                        st.markdown(f"""
                        <div class='info-box'>
                            <strong>KDK 방식 ({sz}명, {gc}게임)</strong>
                            <p>• 매 라운드 파트너 교체 · 1인당 약 {gc}경기</p>
                            <p>• {'✅ 한울방식 대진표 적용 가능' if sz in KDK_TABLE and gc in KDK_TABLE.get(sz, {}) else '⚡ 자동 대진 생성 (참가자 수 맞춤)'}</p>
                        </div>
                        """, unsafe_allow_html=True)
                    g_configs[gn] = (int(sz), md, int(gc))

            if st.button("🎾 대진표 생성", type="primary"):
                p_list = [p.strip() for p in raw_p.split(",") if p.strip()]
                total_needed = sum(c[0] for c in g_configs.values())

                if len(p_list) < total_needed:
                    st.error(f"참가자가 부족합니다. 필요: {total_needed}명, 입력: {len(p_list)}명")
                else:
                    # 랭킹순 정렬 → 스네이크 드래프트로 그룹 배분
                    rank_df = load_rank()
                    rank_map = dict(zip(rank_df["이름"], rank_df["현재포인트"]))
                    p_list.sort(key=lambda x: rank_map.get(x, 0), reverse=True)

                    st.session_state.groups = {}
                    st.session_state.modes = {}
                    st.session_state.schedule = {}
                    st.session_state.scores = {}
                    st.session_state.shuffled_players = {}

                    curr = 0
                    for gn, (sz, md, gc) in g_configs.items():
                        group_p = p_list[curr:curr+sz]
                        st.session_state.groups[gn] = group_p
                        st.session_state.modes[gn] = md

                        if md == "KDK":
                            schedule, shuffled = make_kdk_schedule(group_p, gc)
                            st.session_state.schedule[gn] = schedule
                            st.session_state.shuffled_players[gn] = shuffled
                        elif md == "고정페어":
                            pairs = [group_p[i:i+2] for i in range(0, len(group_p), 2)]
                            st.session_state.schedule[gn] = make_round_robin(pairs)
                        else:  # 단식
                            singles = [[p] for p in group_p]
                            st.session_state.schedule[gn] = make_round_robin(singles)

                        curr += sz

                    st.success(f"✅ 대진표 생성 완료! 총 {sum(len(rd) for g in st.session_state.schedule.values() for rd in g)}경기")
                    # 대진 미리보기
                    for gn in st.session_state.schedule.keys():
                        total_matches = sum(len(rd) for rd in st.session_state.schedule[gn])
                        st.info(f"Group {gn} ({st.session_state.modes[gn]}): {len(st.session_state.schedule[gn])}라운드, {total_matches}경기")
                    st.rerun()

        with tab2:
            st.markdown("<div class='card-title'>데이터 관리</div>", unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**선수 추가**")
                new_player = st.text_input("이름", key="new_player_input")
                if st.button("선수 추가") and new_player:
                    rank_df = load_rank()
                    if new_player not in rank_df["이름"].values:
                        new_row = pd.DataFrame([{"이름": new_player, "현재포인트": 0, "총경기": 0, "총승": 0, "총득실": 0}])
                        rank_df = pd.concat([rank_df, new_row], ignore_index=True)
                        save_rank(rank_df)
                        st.success(f"{new_player} 추가됨")
                    else:
                        st.warning("이미 등록된 선수입니다.")

            with col2:
                st.markdown("**현재 랭킹 데이터**")
                rank_df = load_rank()
                if not rank_df.empty:
                    st.dataframe(rank_df.sort_values("현재포인트", ascending=False), use_container_width=True)

            st.divider()
            st.markdown("**⚠️ 위험 구역**")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🗑️ 현재 대진 초기화"):
                    st.session_state.schedule = {}
                    st.session_state.scores = {}
                    st.session_state.groups = {}
                    st.session_state.modes = {}
                    st.success("대진 초기화 완료")
            with c2:
                if st.button("⚠️ 전체 랭킹 초기화", type="primary"):
                    if os.path.exists(RANK_FILE): os.remove(RANK_FILE)
                    if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                    st.success("전체 데이터 초기화 완료")
    elif pwd:
        st.error("❌ 비밀번호가 틀렸습니다.")
