import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime, date
import itertools

# =============================
# 페이지 설정
# =============================
st.set_page_config(
    layout="wide",
    page_title="두류 테니스 랭킹 시스템",
    page_icon="🎾",
    initial_sidebar_state="collapsed"
)

# =============================
# 전역 CSS (모바일 최적화 포함)
# =============================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;900&display=swap');

/* 전체 폰트 */
html, body, [class*="css"], .stMarkdown, .stText, button, input, select, textarea {
    font-family: 'Noto Sans KR', sans-serif !important;
}

/* 모바일 대응: 기본 패딩 줄이기 */
.block-container { padding: 0.5rem 0.6rem 2rem 0.6rem !important; max-width: 100% !important; }

/* 탭 버튼 크게 */
button[data-baseweb="tab"] {
    font-size: 1.05rem !important;
    font-weight: 700 !important;
    padding: 10px 18px !important;
    border-radius: 10px 10px 0 0 !important;
    white-space: nowrap !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, #1565c0, #1e88e5) !important;
    color: white !important;
}

/* 버튼 전체 */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 0.95rem !important;
    padding: 8px 14px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(0,0,0,0.15) !important; }

/* 입력창 가운데 정렬 */
input[type="number"] { text-align: center !important; font-size: 1.2rem !important; font-weight: 700 !important; }

/* 테이블 가운데 정렬 */
th, td { text-align: center !important; vertical-align: middle !important; }
.dataframe th, .dataframe td { text-align: center !important; }

/* 커스텀 카드류 */
.main-title {
    text-align: center;
    font-size: clamp(1.4rem, 5vw, 2.5rem);
    font-weight: 900;
    background: linear-gradient(135deg, #1565c0, #42a5f5);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0.3rem 0 1rem 0;
    letter-spacing: -0.5px;
}

/* 섹션 헤더 */
.sec-title {
    font-size: clamp(1rem, 3.5vw, 1.25rem);
    font-weight: 900;
    color: #1565c0;
    border-left: 5px solid #42a5f5;
    padding-left: 12px;
    margin: 14px 0 10px 0;
}

/* 팀 도형 카드 */
.team-shape-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 10px 4px;
}
.team-shape {
    border-radius: 16px;
    padding: 10px 14px;
    text-align: center;
    font-weight: 800;
    font-size: clamp(0.78rem, 2.5vw, 1rem);
    box-shadow: 0 4px 14px rgba(0,0,0,0.13);
    min-width: 90px;
    line-height: 1.4;
    word-break: keep-all;
}
.shape-green  { background: linear-gradient(135deg, #43a047, #1b5e20); color: #fff; }
.shape-blue   { background: linear-gradient(135deg, #1e88e5, #0d47a1); color: #fff; }
.shape-orange { background: linear-gradient(135deg, #fb8c00, #e65100); color: #fff; }
.shape-purple { background: linear-gradient(135deg, #8e24aa, #4a148c); color: #fff; }
.shape-red    { background: linear-gradient(135deg, #e53935, #b71c1c); color: #fff; }
.shape-teal   { background: linear-gradient(135deg, #00897b, #004d40); color: #fff; }

.vs-badge {
    background: linear-gradient(135deg, #e53935, #b71c1c);
    color: white;
    border-radius: 50%;
    width: 36px; height: 36px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 900; font-size: 0.85rem;
    margin: 4px auto;
    box-shadow: 0 3px 10px rgba(229,57,53,0.4);
}

/* 라운드 헤더 */
.round-header {
    background: linear-gradient(90deg, #1565c0, #42a5f5);
    color: white;
    border-radius: 10px;
    padding: 7px 16px;
    font-size: clamp(0.85rem, 3vw, 1rem);
    font-weight: 800;
    margin: 14px 0 8px 0;
    text-align: center;
    box-shadow: 0 3px 10px rgba(21,101,192,0.3);
}

/* 매치 컨테이너 */
.match-wrap {
    background: #fff;
    border-radius: 14px;
    padding: 10px 8px 12px 8px;
    margin: 6px 0;
    box-shadow: 0 3px 12px rgba(0,0,0,0.09);
    border: 1.5px solid #e3eaf5;
}

/* 랭킹 배지 */
.rank-gold   { color: #f9a825; font-size: 1.3rem; font-weight:900; }
.rank-silver { color: #78909c; font-size: 1.2rem; font-weight:900; }
.rank-bronze { color: #a1887f; font-size: 1.15rem; font-weight:900; }

/* 체크박스 크게 */
.stCheckbox > label { font-size: 1rem !important; font-weight: 600 !important; }

/* 참가 확인 카드 */
.attend-card {
    background: #f0f7ff;
    border: 1.5px solid #90caf9;
    border-radius: 12px;
    padding: 10px 14px;
    margin: 4px 0;
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: clamp(0.88rem, 3vw, 1rem);
    font-weight: 600;
}
.attend-ok   { border-color: #66bb6a; background: #f1f8e9; }
.attend-none { border-color: #ef9a9a; background: #fff3f3; }

/* 매트릭스 테이블 */
.matrix-wrap { overflow-x: auto; -webkit-overflow-scrolling: touch; }

/* 그룹 탭 색상 */
.group-badge {
    display: inline-block;
    border-radius: 8px;
    padding: 3px 12px;
    font-weight: 800;
    font-size: 0.9rem;
    margin-bottom: 6px;
}

/* 반응형: 좁은 화면 */
@media (max-width: 640px) {
    .block-container { padding: 0.3rem 0.3rem 2rem 0.3rem !important; }
    .team-shape { min-width: 70px; padding: 7px 8px; }
    .round-header { padding: 6px 10px; }
}

/* 점수 입력란 크게 */
div[data-testid="stNumberInput"] input {
    font-size: 1.4rem !important;
    font-weight: 900 !important;
    text-align: center !important;
    padding: 8px 4px !important;
}
</style>
""", unsafe_allow_html=True)

# =============================
# 파일 상수
# =============================
RANK_FILE       = "ranking_master.csv"
HISTORY_FILE    = "history_master.csv"
TOURNAMENT_FILE = "tournaments.csv"
ATTEND_FILE     = "attendance.csv"

for f, cols in [
    (RANK_FILE,       ["이름","현재포인트","이전포인트"]),
    (HISTORY_FILE,    ["날짜","대회명","그룹","이름","순위","승","패","득실","획득포인트"]),
    (TOURNAMENT_FILE, ["대회명","날짜","장소","방식","상태"]),
    (ATTEND_FILE,     ["대회명","이름","참가확인"]),
]:
    if not os.path.exists(f):
        pd.DataFrame(columns=cols).to_csv(f, index=False)

# =============================
# 한울방식 KDK 대진 데이터
# =============================
HANUL_KDK = {
    3: {
        4:  ["14:23","13:24","12:34"],
        8:  ["12:34","56:78","18:27","36:45","14:58","23:67"],
        12: ["12:34","56:78","9A:BC","13:57","24:68","9B:AC","48:9C","67:AB","BC:23"],
    },
    4: {
        5:  ["12:34","13:25","14:35","15:24","23:45"],
        6:  ["13:24","15:46","23:56","14:35","26:34","16:25"],
        7:  ["12:34","56:17","23:57","14:67","35:24","16:25","46:37"],
        8:  ["12:34","56:78","13:57","24:68","15:26","37:48","16:38","25:47"],
        9:  ["12:34","56:78","19:57","23:68","49:38","15:26","36:45","17:89","24:79"],
        10: ["12:35","67:8A","23:46","78:19","34:57","89:2A","45:68","13:9A","56:79","1A:24"],
        11: ["12:35","67:8A","49:1B","23:68","45:7A","9B:26","13:7B","48:59","1A:28","47:6B","39:5A"],
    },
}

def smart_split_indices(s, n):
    """'12:34' 같은 문자열에서 1-based 인덱스 파싱 (n명 기준, A=10, B=11, C=12)"""
    res = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == 'A': res.append(9); i += 1
        elif ch == 'B': res.append(10); i += 1
        elif ch == 'C': res.append(11); i += 1
        elif i+1 < len(s) and s[i:i+2].isdigit() and int(s[i:i+2]) <= n and int(s[i:i+2]) >= 10:
            res.append(int(s[i:i+2])-1); i += 2
        else:
            res.append(int(ch)-1); i += 1
    return res

def make_kdk_hanul(players, target_games):
    n = len(players)
    data = HANUL_KDK.get(target_games, {}).get(n)
    if not data:
        return None
    shuffled = random.sample(players, n)
    rounds = []
    for ms in data:
        left, right = ms.split(":")
        t1 = [shuffled[i] for i in smart_split_indices(left, n)]
        t2 = [shuffled[i] for i in smart_split_indices(right, n)]
        rounds.append([(t1, t2)])
    return rounds

def make_round_robin(teams):
    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    rounds = []
    while matches:
        used, r = set(), []
        for m in matches[:]:
            flat = tuple(m[0]) + tuple(m[1])
            if not (set(flat) & used):
                r.append(m); used.update(flat); matches.remove(m)
        if not r: break
        rounds.append(r)
    return rounds

# =============================
# 상태 초기화
# =============================
def init_state():
    defaults = {
        "players": [], "groups": {}, "modes": {}, "game_counts": {},
        "schedule": {}, "scores": {}, "is_admin": False,
        "tournament_name": "정기 대회",
        "tournament_date": str(date.today()),
        "tournament_place": "",
        "attendance": {},  # {이름: True/False}
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============================
# 데이터 함수
# =============================
def load_rank():
    df = pd.read_csv(RANK_FILE)
    df["현재포인트"] = pd.to_numeric(df.get("현재포인트", 0), errors="coerce").fillna(0).astype(int)
    df["이전포인트"] = pd.to_numeric(df.get("이전포인트", 0), errors="coerce").fillna(0).astype(int)
    return df

def save_rank(df):
    df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
    df.to_csv(RANK_FILE, index=False)

def load_history():
    return pd.read_csv(HISTORY_FILE)

def save_history(df):
    df.to_csv(HISTORY_FILE, index=False)

def load_tournaments():
    return pd.read_csv(TOURNAMENT_FILE)

def save_tournaments(df):
    df.to_csv(TOURNAMENT_FILE, index=False)

def load_attendance():
    return pd.read_csv(ATTEND_FILE)

def save_attendance(df):
    df.to_csv(ATTEND_FILE, index=False)

# =============================
# 포인트 계산 (1위:7, 2위:5, 3위:3, 참가:1)
# =============================
POINT_TABLE = {1: 7, 2: 5, 3: 3}
ATTEND_POINT = 1

def calc_points(rank: int) -> int:
    return POINT_TABLE.get(rank, ATTEND_POINT)

# =============================
# 유틸
# =============================
def clean(x): return str(x).strip().replace(" ", "")

def team_name(t):
    t = list(t)
    return " & ".join(t) if len(t) > 1 else t[0]

GROUP_COLORS = ["shape-green","shape-blue","shape-orange","shape-purple","shape-red","shape-teal"]
GROUP_LABELS = ["🟢","🔵","🟠","🟣","🔴","🩵"]
GROUP_HEX    = ["#43a047","#1e88e5","#fb8c00","#8e24aa","#e53935","#00897b"]

def group_color(idx):
    return GROUP_COLORS[idx % len(GROUP_COLORS)]

def group_hex(idx):
    return GROUP_HEX[idx % len(GROUP_HEX)]

# =============================
# 팀 도형 카드 렌더링
# =============================
def render_team_shape(players_list, color_cls):
    names_html = "<br>".join(players_list)
    return f'<div class="team-shape {color_cls}">{names_html}</div>'

# =============================
# 매트릭스 생성
# =============================
def draw_match_matrix(group_name):
    players = st.session_state.groups.get(group_name, [])
    mode    = st.session_state.modes.get(group_name, "단식")
    sched   = st.session_state.schedule.get(group_name, [])

    # 팀 목록 수집
    teams_list = []
    seen = set()
    for rd in sched:
        for (t1, t2) in rd:
            for t in [tuple(t1), tuple(t2)]:
                if t not in seen:
                    teams_list.append(t); seen.add(t)

    def tname(t): return team_name(list(t))

    # stats: 팀 단위
    stats = {t: {"승": 0, "패": 0, "득실": 0} for t in teams_list}
    matrix = {t: {o: "-" for o in teams_list if o != t} for t in teams_list}

    for score_data in st.session_state.scores.values():
        g = score_data.get("group")
        if g != group_name: continue
        t1 = tuple(score_data["t1"]); t2 = tuple(score_data["t2"])
        s1, s2 = score_data["s1"], score_data["s2"]
        if s1 == s2: continue

        for my_t, op_t, ms, os_ in [(t1,t2,s1,s2),(t2,t1,s2,s1)]:
            if my_t in stats:
                if ms > os_: stats[my_t]["승"] += 1
                else: stats[my_t]["패"] += 1
                stats[my_t]["득실"] += (ms - os_)
            if my_t in matrix and op_t in matrix[my_t]:
                matrix[my_t][op_t] = f"{ms}:{os_}"

    # 순위 정렬
    ranked = sorted(teams_list, key=lambda t: (-stats[t]["승"], -stats[t]["득실"]))

    # 매트릭스 DataFrame
    labels = [tname(t) for t in ranked]
    data = {}
    for t in ranked:
        row = {}
        for o in ranked:
            if o == t: row[tname(o)] = "●"
            else: row[tname(o)] = matrix[t].get(o, "-")
        data[tname(t)] = row
    mdf = pd.DataFrame(data).T
    mdf.index.name = "팀"

    # 순위 DataFrame
    rank_rows = []
    for ri, t in enumerate(ranked):
        rank_rows.append({
            "순위": ri+1,
            "팀명": tname(t),
            "승": stats[t]["승"],
            "패": stats[t]["패"],
            "득실": stats[t]["득실"],
        })
    rank_df = pd.DataFrame(rank_rows)

    gidx = list(st.session_state.schedule.keys()).index(group_name) if group_name in st.session_state.schedule else 0
    hex_c = group_hex(gidx)
    st.markdown(f"""
    <div style='background:linear-gradient(90deg,{hex_c}22,{hex_c}08);
        border-left:5px solid {hex_c}; border-radius:10px;
        padding:8px 14px; margin-bottom:10px;'>
        <span style='font-size:1.1rem;font-weight:900;color:{hex_c}'>
        {GROUP_LABELS[gidx % len(GROUP_LABELS)]} 그룹 {group_name} — 전적 현황
        </span>
    </div>""", unsafe_allow_html=True)

    col_m, col_r = st.columns([3, 2])
    with col_m:
        st.markdown("**📋 상대별 전적 매트릭스**")
        st.markdown('<div class="matrix-wrap">', unsafe_allow_html=True)
        st.dataframe(mdf, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    with col_r:
        st.markdown("**🏅 그룹 순위**")
        def rank_icon(r):
            return ["🥇","🥈","🥉"][r-1] if r <= 3 else str(r)
        rank_df["순위"] = rank_df["순위"].apply(rank_icon)
        st.dataframe(rank_df, use_container_width=True, hide_index=True)

# =============================
# 메뉴 (하단 네비 스타일)
# =============================
MENU_ITEMS = {
    "🏆 랭킹": "ranking",
    "📅 대진표": "schedule",
    "📊 결과": "result",
    "✅ 참가확인": "attend",
    "⚙️ 관리자": "admin",
}

if "menu" not in st.session_state:
    st.session_state["menu"] = "ranking"

cols_nav = st.columns(len(MENU_ITEMS))
for ci, (label, key) in enumerate(MENU_ITEMS.items()):
    with cols_nav[ci]:
        is_active = st.session_state["menu"] == key
        btn_style = "primary" if is_active else "secondary"
        if st.button(label, key=f"nav_{key}", use_container_width=True, type=btn_style):
            st.session_state["menu"] = key
            st.rerun()

st.divider()
menu = st.session_state["menu"]

# =============================
# 🏆 랭킹
# =============================
if menu == "ranking":
    st.markdown("<div class='main-title'>🎾 두류 테니스 랭킹</div>", unsafe_allow_html=True)
    df = load_rank()
    if df.empty:
        st.info("관리자에서 랭킹 데이터를 업로드하세요.")
    else:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        def rank_icon(i):
            icons = ["🥇","🥈","🥉"]
            return icons[i] if i < 3 else str(i+1)
        df.insert(0, "순위", [rank_icon(i) for i in df.index])
        df["변동"] = (df["현재포인트"] - df["이전포인트"]).apply(
            lambda x: f"▲{int(x)}" if x > 0 else (f"▼{int(abs(x))}" if x < 0 else "—")
        )
        # 포인트 구간별 배지
        def point_bar(p):
            p = int(p)
            filled = min(int(p // 10), 10)
            return "■" * filled + "□" * (10 - filled)
        df["포인트그래프"] = df["현재포인트"].apply(point_bar)

        st.dataframe(
            df[["순위","이름","현재포인트","변동","포인트그래프"]],
            use_container_width=True, hide_index=True
        )

# =============================
# 📅 대진표/입력
# =============================
elif menu == "schedule":
    st.markdown("<div class='main-title'>📅 대진표</div>", unsafe_allow_html=True)

    if not st.session_state.schedule:
        st.warning("⚠️ 관리자 센터에서 대진을 생성하세요.")
    else:
        group_names = list(st.session_state.schedule.keys())
        tab_labels  = [f"{GROUP_LABELS[i % len(GROUP_LABELS)]} 그룹 {g}" for i, g in enumerate(group_names)]
        tabs = st.tabs(tab_labels)

        for tidx, g in enumerate(group_names):
            with tabs[tidx]:
                # 매트릭스 먼저
                draw_match_matrix(g)
                st.divider()

                gidx = tidx
                c_cls = group_color(gidx)
                sched = st.session_state.schedule[g]

                for ri, rd in enumerate(sched):
                    st.markdown(f'<div class="round-header">🏸 Round {ri+1}</div>', unsafe_allow_html=True)

                    # 최대 2코트씩 나란히
                    court_cols = st.columns(min(len(rd), 2))
                    for mi, (t1, t2) in enumerate(rd):
                        t1 = list(t1); t2 = list(t2)
                        with court_cols[mi % 2]:
                            key = f"{g}_{ri}_{mi}"
                            existing = st.session_state.scores.get(key, {})
                            es1 = existing.get("s1", 0)
                            es2 = existing.get("s2", 0)

                            # 팀 도형 + VS
                            shape1 = render_team_shape(t1, c_cls)
                            shape2 = render_team_shape(t2, c_cls)

                            st.markdown(f"""
                            <div class="match-wrap">
                              <div class="team-shape-wrap">
                                {shape1}
                                <div class="vs-badge">VS</div>
                                {shape2}
                              </div>
                            </div>""", unsafe_allow_html=True)

                            # 점수 입력 (일반 사용자는 읽기 전용 표시)
                            if es1 > 0 or es2 > 0:
                                st.markdown(
                                    f"<div style='text-align:center;font-size:1.3rem;font-weight:900;"
                                    f"color:#1565c0;padding:4px 0'>"
                                    f"{team_name(t1)} <span style='color:#e53935'>{es1} : {es2}</span> {team_name(t2)}"
                                    f"</div>", unsafe_allow_html=True
                                )

# =============================
# 📊 경기 결과
# =============================
elif menu == "result":
    st.markdown("<div class='main-title'>📊 경기 결과</div>", unsafe_allow_html=True)

    if not st.session_state.scores:
        st.info("아직 입력된 점수가 없습니다.")
    else:
        group_names = list(st.session_state.schedule.keys()) if st.session_state.schedule else []
        tab_labels  = [f"{GROUP_LABELS[i % len(GROUP_LABELS)]} 그룹 {g}" for i, g in enumerate(group_names)]

        if group_names:
            tabs = st.tabs(tab_labels)
            for tidx, g in enumerate(group_names):
                with tabs[tidx]:
                    gidx = tidx
                    hex_c = group_hex(gidx)

                    sched  = st.session_state.schedule.get(g, [])
                    teams_list, seen = [], set()
                    for rd in sched:
                        for (t1,t2) in rd:
                            for t in [tuple(t1),tuple(t2)]:
                                if t not in seen:
                                    teams_list.append(t); seen.add(t)

                    stats = {t: {"승":0,"패":0,"득실":0} for t in teams_list}
                    match_rows = []

                    for key, sd in st.session_state.scores.items():
                        if sd.get("group") != g: continue
                        t1 = tuple(sd["t1"]); t2 = tuple(sd["t2"])
                        s1, s2 = sd["s1"], sd["s2"]
                        n1 = team_name(list(t1)); n2 = team_name(list(t2))

                        if s1 > s2:
                            result = f"🏆 {n1} 승"
                            if t1 in stats: stats[t1]["승"] += 1
                            if t2 in stats: stats[t2]["패"] += 1
                        elif s2 > s1:
                            result = f"🏆 {n2} 승"
                            if t2 in stats: stats[t2]["승"] += 1
                            if t1 in stats: stats[t1]["패"] += 1
                        else:
                            result = "🤝 무승부"

                        if t1 in stats: stats[t1]["득실"] += (s1-s2)
                        if t2 in stats: stats[t2]["득실"] += (s2-s1)

                        match_rows.append({"팀1": n1,"점수1": s1,"점수2": s2,"팀2": n2,"결과": result})

                    if match_rows:
                        st.markdown("**📋 전체 경기 결과**")
                        st.dataframe(pd.DataFrame(match_rows), use_container_width=True, hide_index=True)

                    # 순위 집계
                    ranked = sorted(teams_list, key=lambda t: (-stats[t]["승"], -stats[t]["득실"]))
                    rank_rows = []
                    for ri2, t in enumerate(ranked):
                        rank = ri2 + 1
                        icon = ["🥇","🥈","🥉"][ri2] if ri2 < 3 else str(rank)
                        rank_rows.append({
                            "순위": icon,
                            "팀명": team_name(list(t)),
                            "승": stats[t]["승"],
                            "패": stats[t]["패"],
                            "득실": f"{stats[t]['득실']:+d}",
                            "획득포인트": calc_points(rank),
                        })
                    if rank_rows:
                        st.markdown("**🏅 그룹 순위 (승 → 득실 순)**")
                        st.dataframe(pd.DataFrame(rank_rows), use_container_width=True, hide_index=True)

# =============================
# ✅ 참가 확인
# =============================
elif menu == "attend":
    st.markdown("<div class='main-title'>✅ 참가 확인</div>", unsafe_allow_html=True)

    t_name = st.session_state.tournament_name
    t_date = st.session_state.tournament_date
    t_place = st.session_state.tournament_place

    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#e3f2fd,#bbdefb);
        border:2px solid #42a5f5; border-radius:14px; padding:14px 18px; margin-bottom:14px;'>
        <div style='font-size:1.25rem;font-weight:900;color:#1565c0'>🏆 {t_name}</div>
        <div style='color:#555;margin-top:4px'>📅 {t_date} &nbsp;|&nbsp; 📍 {t_place if t_place else "장소 미정"}</div>
    </div>""", unsafe_allow_html=True)

    # 참가자 목록
    all_players = st.session_state.players
    if not all_players:
        st.info("관리자에서 참가자를 먼저 등록하세요.")
    else:
        st.markdown('<div class="sec-title">참가자 명단 및 참가 확인</div>', unsafe_allow_html=True)
        st.caption("✏️ 본인 이름 옆 체크박스를 눌러 참가를 확인하세요.")

        # 참가확인 상태
        attend = st.session_state.attendance

        # 체크박스 + 카드 UI
        confirmed = 0
        for pi, pname in enumerate(all_players):
            is_checked = attend.get(pname, False)
            col_name, col_check = st.columns([4, 1])
            with col_name:
                card_cls = "attend-ok" if is_checked else "attend-none"
                icon = "✅" if is_checked else "⬜"
                num = pi + 1
                st.markdown(
                    f'<div class="attend-card {card_cls}">'
                    f'<span style="font-size:1.1rem">{icon}</span>'
                    f'<span style="color:#888;font-size:0.85rem">No.{num}</span>'
                    f'<span style="font-size:1rem;font-weight:700">{pname}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_check:
                new_val = st.checkbox(
                    "참가", value=is_checked,
                    key=f"attend_{pname}",
                    label_visibility="collapsed"
                )
                if new_val != is_checked:
                    st.session_state.attendance[pname] = new_val
                    st.rerun()
            if is_checked:
                confirmed += 1

        st.divider()
        st.markdown(
            f"<div style='text-align:center;font-size:1.1rem;font-weight:700;"
            f"color:#1565c0;padding:8px;background:#e3f2fd;border-radius:10px'>"
            f"✅ 참가 확인: {confirmed}명 &nbsp;|&nbsp; 전체: {len(all_players)}명</div>",
            unsafe_allow_html=True
        )

        # CSV 저장
        if st.button("💾 참가 현황 저장", use_container_width=True):
            rows = [{"대회명": t_name, "이름": p, "참가확인": attend.get(p, False)} for p in all_players]
            adf = pd.DataFrame(rows)
            save_attendance(adf)
            st.success("✅ 참가 현황이 저장되었습니다.")

# =============================
# ⚙️ 관리자 센터
# =============================
elif menu == "admin":
    st.markdown("<div class='main-title'>⚙️ 관리자 센터</div>", unsafe_allow_html=True)

    pw = st.text_input("🔒 비밀번호", type="password", placeholder="비밀번호 입력")
    if pw == "0502":
        st.session_state.is_admin = True
    if not st.session_state.is_admin:
        st.stop()

    st.success("✅ 관리자 모드")

    adm_tabs = st.tabs(["🏆 대회 생성", "📂 랭킹 관리", "🎯 대진 생성", "📊 점수 입력", "💾 결과 반영"])

    # ─────────────────────────
    # 탭1: 대회 생성
    # ─────────────────────────
    with adm_tabs[0]:
        st.markdown('<div class="sec-title">새 대회 만들기</div>', unsafe_allow_html=True)

        with st.form("form_tournament"):
            t_name  = st.text_input("대회명", value=st.session_state.tournament_name, placeholder="예: 5월 정기 대회")
            t_date  = st.date_input("날짜", value=date.today())
            t_place = st.text_input("장소", value=st.session_state.tournament_place, placeholder="예: 두류테니스장 A코트")
            t_mode  = st.selectbox("대회 방식", ["리그전(풀리그)", "KDK", "고정페어", "혼합"])
            if st.form_submit_button("✅ 대회 생성", use_container_width=True, type="primary"):
                if not t_name.strip():
                    st.error("대회명을 입력하세요")
                else:
                    st.session_state.tournament_name  = t_name.strip()
                    st.session_state.tournament_date  = str(t_date)
                    st.session_state.tournament_place = t_place.strip()
                    # 기존 데이터 리셋
                    st.session_state.players  = []
                    st.session_state.groups   = {}
                    st.session_state.modes    = {}
                    st.session_state.schedule = {}
                    st.session_state.scores   = {}
                    st.session_state.attendance = {}
                    # 파일 저장
                    t_df = load_tournaments()
                    new_row = pd.DataFrame([[t_name.strip(), str(t_date), t_place.strip(), t_mode, "진행중"]],
                                           columns=["대회명","날짜","장소","방식","상태"])
                    t_df = pd.concat([t_df, new_row], ignore_index=True)
                    save_tournaments(t_df)
                    st.success(f"🎉 '{t_name}' 대회가 생성되었습니다!")
                    st.rerun()

        st.markdown('<div class="sec-title">대회 목록</div>', unsafe_allow_html=True)
        t_df = load_tournaments()
        if not t_df.empty:
            for i, row in t_df.iterrows():
                sc = {"진행중": "#fb8c00", "완료": "#43a047", "예정": "#1e88e5"}.get(row["상태"], "#888")
                st.markdown(f"""
                <div style='background:#f8f9fa;border:1.5px solid #e0e0e0;border-radius:12px;
                    padding:10px 14px;margin:6px 0;'>
                    <span style='font-weight:900;font-size:1rem'>{row['대회명']}</span>
                    <span style='margin-left:10px;font-size:0.85rem;color:#555'>
                    📅{row['날짜']} | 📍{row['장소']} | {row['방식']}
                    </span>
                    <span style='margin-left:8px;color:{sc};font-weight:800'>[{row['상태']}]</span>
                </div>""", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("완료 처리", key=f"done_{i}", use_container_width=True):
                        t_df.loc[i,"상태"] = "완료"
                        save_tournaments(t_df)
                        st.rerun()
                with c2:
                    if st.button("🗑 삭제", key=f"del_{i}", use_container_width=True):
                        t_df = t_df.drop(index=i).reset_index(drop=True)
                        save_tournaments(t_df)
                        st.rerun()
        else:
            st.info("생성된 대회가 없습니다.")

    # ─────────────────────────
    # 탭2: 랭킹 관리
    # ─────────────────────────
    with adm_tabs[1]:
        st.markdown('<div class="sec-title">랭킹 파일 업로드</div>', unsafe_allow_html=True)
        st.caption("컬럼명에 '이름/name/선수/회원', '포인트/point/pts/점수' 등이 포함되면 자동 인식합니다.")

        NAME_KW  = ["이름","name","선수","player","성명","회원","member","참가자","닉네임","nick"]
        POINT_KW = ["포인트","point","pts","점수","score","랭킹","ranking","현재","current"]
        PREV_KW  = ["이전","prev","before","old","기존","previous","지난"]

        def find_col(cols, kws):
            for kw in kws:
                for c in cols:
                    if kw in c: return c
            return None

        def smart_read(file):
            try:
                df = pd.read_csv(file, encoding_errors="replace") if file.name.endswith(".csv") else pd.read_excel(file)
            except Exception as e:
                st.error(f"파일 읽기 실패: {e}"); return None

            orig = list(df.columns)
            df.columns = [str(c).lower().strip().replace(" ","") for c in df.columns]
            norm = list(df.columns)

            name_col = find_col(norm, NAME_KW)
            point_col, prev_col = None, None
            for c in norm:
                is_prev = any(kw in c for kw in PREV_KW)
                is_pt   = any(kw in c for kw in POINT_KW)
                if is_pt:
                    if is_prev: prev_col = c
                    elif point_col is None: point_col = c
                    elif prev_col is None: prev_col = point_col; point_col = c

            with st.expander("📋 컬럼 인식 결과"):
                st.write(f"원본 컬럼: {orig}")
                st.write(f"이름→[{name_col}] | 현재포인트→[{point_col}] | 이전포인트→[{prev_col}]")

            if name_col is None:
                st.error(f"❌ 이름 컬럼 없음. 컬럼: {orig}")
                st.info("컬럼에 '이름','name','선수','회원' 중 하나를 포함하세요.")
                return None

            df["이름"]     = df[name_col].astype(str).str.strip().str.replace(" ","")
            df["현재포인트"] = pd.to_numeric(df[point_col], errors="coerce").fillna(0).astype(int) if point_col else 0
            df["이전포인트"] = pd.to_numeric(df[prev_col],  errors="coerce").fillna(0).astype(int) if prev_col  else 0
            df = df[["이름","현재포인트","이전포인트"]]
            df = df[df["이름"].str.len() > 0]
            df = df[df["이름"] != "nan"]
            df = df.drop_duplicates(subset="이름")
            return df

        file = st.file_uploader("엑셀/CSV 파일 선택", type=["csv","xlsx"])
        if file:
            df_up = smart_read(file)
            if df_up is not None:
                st.dataframe(df_up.head(15), use_container_width=True, hide_index=True)
                if st.button("💾 랭킹 저장", use_container_width=True, type="primary"):
                    save_rank(df_up)
                    st.success("✅ 랭킹 저장 완료!")

        st.markdown('<div class="sec-title">현재 랭킹</div>', unsafe_allow_html=True)
        cur = load_rank()
        if not cur.empty:
            cur = cur.sort_values("현재포인트", ascending=False).reset_index(drop=True)
            cur.insert(0, "순위", cur.index+1)
            st.dataframe(cur, use_container_width=True, hide_index=True)
        else:
            st.info("랭킹 데이터 없음")

    # ─────────────────────────
    # 탭3: 대진 생성
    # ─────────────────────────
    with adm_tabs[2]:
        st.markdown('<div class="sec-title">참가자 등록</div>', unsafe_allow_html=True)
        raw_p = st.text_area("참가자 (쉼표로 구분)", value=", ".join(st.session_state.players), height=80)
        if st.button("📝 참가자 등록", use_container_width=True):
            st.session_state.players = [clean(p) for p in raw_p.split(",") if p.strip()]
            st.session_state.attendance = {p: st.session_state.attendance.get(p, False) for p in st.session_state.players}
            st.success(f"✅ {len(st.session_state.players)}명 등록")

        if st.session_state.players:
            st.markdown(f"**등록 인원: {len(st.session_state.players)}명** — {', '.join(st.session_state.players)}")

        st.divider()
        st.markdown('<div class="sec-title">그룹 및 방식 설정</div>', unsafe_allow_html=True)

        g_count = st.number_input("그룹 수", 1, 6, 1)
        g_names = list("ABCDEF")[:g_count]

        g_configs = {}
        for gi, gn in enumerate(g_names):
            hex_c = group_hex(gi)
            st.markdown(
                f"<div style='background:{hex_c}18;border-left:5px solid {hex_c};"
                f"border-radius:8px;padding:7px 14px;margin:8px 0;"
                f"font-weight:800;color:{hex_c};font-size:1rem'>"
                f"{GROUP_LABELS[gi % len(GROUP_LABELS)]} 그룹 {gn}</div>",
                unsafe_allow_html=True
            )
            cc = st.columns(3)
            with cc[0]:
                default_sz = max(2, len(st.session_state.players) // g_count) if st.session_state.players else 4
                sz = st.number_input(f"인원", 2, 30, default_sz, key=f"sz_{gn}")
            with cc[1]:
                md = st.selectbox(f"방식", ["KDK","고정페어","단식"], key=f"md_{gn}")
            with cc[2]:
                gc_opts = [3,4,5,6]
                gc = st.selectbox(f"1인 게임수", gc_opts, index=1, key=f"gc_{gn}")
            g_configs[gn] = (sz, md, gc)

        total_sz = sum(c[0] for c in g_configs.values())
        if st.session_state.players:
            diff = len(st.session_state.players) - total_sz
            if diff == 0: st.success(f"✅ 참가자 {len(st.session_state.players)}명 = 배정 {total_sz}명")
            else: st.warning(f"⚠️ 참가자 {len(st.session_state.players)}명 / 배정 {total_sz}명 (차이 {diff:+d}명)")

        if st.button("🎲 대진 생성", use_container_width=True, type="primary"):
            p_list = st.session_state.players[:]
            if len(p_list) < total_sz:
                st.error(f"인원 부족: 참가자 {len(p_list)}명 < 배정 {total_sz}명")
            else:
                # 랭킹 기반 정렬
                rank_df = load_rank()
                rank_map = dict(zip(rank_df["이름"], rank_df["현재포인트"]))
                p_list.sort(key=lambda x: rank_map.get(x, 0), reverse=True)

                st.session_state.groups   = {}
                st.session_state.modes    = {}
                st.session_state.game_counts = {}
                st.session_state.schedule = {}
                st.session_state.scores   = {}

                curr = 0
                for gn, (sz, md, gc) in g_configs.items():
                    gp = p_list[curr:curr+sz]
                    st.session_state.groups[gn]      = gp
                    st.session_state.modes[gn]       = md
                    st.session_state.game_counts[gn] = gc

                    if md == "KDK":
                        hanul = make_kdk_hanul(gp, gc)
                        if hanul:
                            st.session_state.schedule[gn] = hanul
                            st.info(f"그룹 {gn}: 한울 KDK 대진 적용 ({len(gp)}명 × {gc}게임)")
                        else:
                            # KDK 페어 랜덤: 2명씩 묶어 리그
                            shuffled = random.sample(gp, len(gp))
                            pairs = [shuffled[i:i+2] for i in range(0, len(shuffled)-1, 2)]
                            if len(shuffled) % 2 == 1: pairs.append([shuffled[-1]])
                            st.session_state.schedule[gn] = make_round_robin(pairs)
                            st.warning(f"그룹 {gn}: 한울 데이터 없음 → 랜덤 페어 리그 적용")
                    elif md == "고정페어":
                        n = len(gp)
                        pairs = [[gp[i], gp[n-1-i]] for i in range(n//2)]
                        if n % 2 == 1: pairs.append([gp[n//2]])
                        st.session_state.schedule[gn] = make_round_robin(pairs)
                    else:  # 단식
                        singles = [[p] for p in gp]
                        st.session_state.schedule[gn] = make_round_robin(singles)

                    curr += sz

                st.success("✅ 대진이 생성되었습니다! '대진표' 메뉴에서 확인하세요.")
                st.rerun()

    # ─────────────────────────
    # 탭4: 점수 입력 (관리자 전용)
    # ─────────────────────────
    with adm_tabs[3]:
        st.markdown('<div class="sec-title">점수 입력</div>', unsafe_allow_html=True)

        if not st.session_state.schedule:
            st.warning("대진을 먼저 생성하세요.")
        else:
            group_names = list(st.session_state.schedule.keys())
            tab_labels  = [f"{GROUP_LABELS[i % len(GROUP_LABELS)]} 그룹 {g}" for i, g in enumerate(group_names)]
            score_tabs  = st.tabs(tab_labels)

            for tidx, g in enumerate(group_names):
                with score_tabs[tidx]:
                    gidx  = tidx
                    c_cls = group_color(gidx)
                    sched = st.session_state.schedule[g]

                    for ri, rd in enumerate(sched):
                        st.markdown(f'<div class="round-header">🏸 Round {ri+1}</div>', unsafe_allow_html=True)
                        court_cols = st.columns(min(len(rd), 2))

                        for mi, (t1, t2) in enumerate(rd):
                            t1 = list(t1); t2 = list(t2)
                            with court_cols[mi % 2]:
                                key = f"{g}_{ri}_{mi}"
                                existing = st.session_state.scores.get(key, {})
                                es1 = existing.get("s1", 0)
                                es2 = existing.get("s2", 0)
                                n1  = team_name(t1)
                                n2  = team_name(t2)

                                shape1 = render_team_shape(t1, c_cls)
                                shape2 = render_team_shape(t2, c_cls)

                                st.markdown(f"""
                                <div class="match-wrap">
                                  <div class="team-shape-wrap">
                                    {shape1}
                                    <div class="vs-badge">VS</div>
                                    {shape2}
                                  </div>
                                </div>""", unsafe_allow_html=True)

                                sc1, sc2 = st.columns(2)
                                with sc1:
                                    s1 = st.number_input(n1, 0, 50, es1, key=f"{key}_s1")
                                with sc2:
                                    s2 = st.number_input(n2, 0, 50, es2, key=f"{key}_s2")

                                if st.button(f"💾 저장", key=f"{key}_btn", use_container_width=True):
                                    st.session_state.scores[key] = {
                                        "group": g, "ri": ri, "mi": mi,
                                        "t1": t1, "t2": t2,
                                        "s1": s1, "s2": s2
                                    }
                                    if s1 > s2: result_txt = f"🏆 {n1} 승"
                                    elif s2 > s1: result_txt = f"🏆 {n2} 승"
                                    else: result_txt = "🤝 무승부"
                                    st.success(f"{n1} {s1} : {s2} {n2} — {result_txt}")
                                    st.rerun()

    # ─────────────────────────
    # 탭5: 결과 반영
    # ─────────────────────────
    with adm_tabs[4]:
        st.markdown('<div class="sec-title">경기 결과 랭킹 반영</div>', unsafe_allow_html=True)
        st.caption("승패 순위 기준: 1위 +7점 / 2위 +5점 / 3위 +3점 / 참가 +1점")

        if not st.session_state.scores:
            st.warning("입력된 점수가 없습니다.")
        else:
            # 최종 포인트 미리보기
            rank_df = load_rank()
            earn_map = {}  # {이름: 획득포인트}

            # 참가자 전원에게 참가 포인트 +1
            for pname in st.session_state.players:
                earn_map[pname] = ATTEND_POINT

            # 그룹별 순위 계산
            preview_rows = []
            for g, sched in st.session_state.schedule.items():
                teams_list, seen = [], set()
                for rd in sched:
                    for (t1,t2) in rd:
                        for t in [tuple(t1),tuple(t2)]:
                            if t not in seen:
                                teams_list.append(t); seen.add(t)

                stats = {t: {"승":0,"득실":0} for t in teams_list}
                for key, sd in st.session_state.scores.items():
                    if sd.get("group") != g: continue
                    t1=tuple(sd["t1"]); t2=tuple(sd["t2"])
                    s1,s2=sd["s1"],sd["s2"]
                    if s1>s2:
                        if t1 in stats: stats[t1]["승"]+=1
                        if t1 in stats: stats[t1]["득실"]+=(s1-s2)
                        if t2 in stats: stats[t2]["득실"]+=(s2-s1)
                    elif s2>s1:
                        if t2 in stats: stats[t2]["승"]+=1
                        if t2 in stats: stats[t2]["득실"]+=(s2-s1)
                        if t1 in stats: stats[t1]["득실"]+=(s1-s2)

                ranked = sorted(teams_list, key=lambda t: (-stats[t]["승"],-stats[t]["득실"]))
                for ri2, t in enumerate(ranked):
                    rank = ri2+1
                    bonus = calc_points(rank) - ATTEND_POINT  # 참가점 제외한 순위 보너스
                    for pname in list(t):
                        earn_map[pname] = earn_map.get(pname, ATTEND_POINT) + bonus
                        preview_rows.append({
                            "그룹": g,
                            "팀": team_name(list(t)),
                            "그룹순위": ["🥇","🥈","🥉"][ri2] if ri2<3 else str(rank),
                            "이름": pname,
                            "획득포인트": earn_map[pname],
                        })

            if preview_rows:
                st.markdown("**📋 포인트 획득 미리보기**")
                st.dataframe(pd.DataFrame(preview_rows), use_container_width=True, hide_index=True)

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🏆 랭킹에 반영하기", use_container_width=True, type="primary"):
                    rank_df["이전포인트"] = rank_df["현재포인트"]
                    for pname, pts in earn_map.items():
                        if pname in rank_df["이름"].values:
                            rank_df.loc[rank_df["이름"]==pname,"현재포인트"] += pts
                        else:
                            nr = pd.DataFrame([[pname,pts,0]],columns=["이름","현재포인트","이전포인트"])
                            rank_df = pd.concat([rank_df,nr],ignore_index=True)
                    save_rank(rank_df)

                    # 히스토리 저장
                    hist_df = load_history()
                    today   = str(date.today())
                    tname   = st.session_state.tournament_name
                    new_hist = []
                    for row in preview_rows:
                        new_hist.append({
                            "날짜": today, "대회명": tname,
                            "그룹": row["그룹"], "이름": row["이름"],
                            "순위": row["그룹순위"], "승": 0, "패": 0,
                            "득실": 0, "획득포인트": row["획득포인트"]
                        })
                    hist_df = pd.concat([hist_df, pd.DataFrame(new_hist)], ignore_index=True)
                    save_history(hist_df)

                    # 대회 완료 처리
                    t_df = load_tournaments()
                    t_df.loc[t_df["대회명"]==tname,"상태"] = "완료"
                    save_tournaments(t_df)

                    st.success("✅ 랭킹 반영 및 히스토리 저장 완료!")
                    st.rerun()

            with col2:
                if st.button("🗑 모든 점수 초기화", use_container_width=True):
                    st.session_state.scores = {}
                    st.success("✅ 점수 초기화 완료")
                    st.rerun()

            st.divider()
            st.markdown('<div class="sec-title">📜 지난 대회 히스토리</div>', unsafe_allow_html=True)
            hist = load_history()
            if not hist.empty:
                st.dataframe(hist.sort_values("날짜", ascending=False).reset_index(drop=True),
                             use_container_width=True, hide_index=True)
            else:
                st.info("히스토리 없음")
