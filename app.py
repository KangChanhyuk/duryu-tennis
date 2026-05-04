import streamlit as st
import pandas as pd
import random
import os
import datetime

st.set_page_config(layout="wide")

# =========================
# 파일 경로
# =========================
RANK_FILE = "ranking_master.csv"

# =========================
# 초기 파일 생성 (안 터지게 핵심)
# =========================
if not os.path.exists(RANK_FILE):
    pd.DataFrame(columns=["이름","현재포인트","이전포인트"]).to_csv(RANK_FILE,index=False)

# =========================
# 상태 초기화
# =========================
def init_state():
    defaults = {
        "players": [],
        "groups": {},
        "pairs": {},
        "schedule": {},
        "scores": {},
        "is_admin": False
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================
# 스타일 (카드 UI)
# =========================
st.markdown("""
<style>
h1,h2,h3 {text-align:center;}

.team1 {
    background: linear-gradient(135deg,#4CAF50,#2E7D32);
    padding:18px;
    border-radius:20px;
    color:white;
    text-align:center;
    font-weight:bold;
}
.team2 {
    background: linear-gradient(135deg,#2196F3,#1565C0);
    padding:18px;
    border-radius:20px;
    color:white;
    text-align:center;
    font-weight:bold;
}
.vs {
    text-align:center;
    font-size:20px;
    font-weight:bold;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 엑셀 자동 인식 (핵심)
# =========================
def smart_read_excel(file):

    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
    except:
        st.error("파일 읽기 실패")
        return None

    df.columns = [str(c).strip().lower() for c in df.columns]

    name_col = None
    point_col = None
    prev_col = None

    for c in df.columns:
        if "이름" in c or "name" in c:
            name_col = c
        elif "포인트" in c or "point" in c:
            if point_col is None:
                point_col = c
            else:
                prev_col = c

    if name_col is None:
        st.error("이름 컬럼 없음")
        return None

    df["이름"] = df[name_col].astype(str).str.strip().str.replace(" ","")

    if point_col:
        df["현재포인트"] = pd.to_numeric(df[point_col], errors="coerce").fillna(0)
    else:
        df["현재포인트"] = 0

    if prev_col:
        df["이전포인트"] = pd.to_numeric(df[prev_col], errors="coerce").fillna(0)
    else:
        df["이전포인트"] = 0

    df = df[["이름","현재포인트","이전포인트"]]
    df = df.drop_duplicates(subset="이름")

    return df

# =========================
# 랭킹 로드
# =========================
def load_rank():
    df = pd.read_csv(RANK_FILE)

    df["이름"] = df["이름"].astype(str)
    df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors="coerce").fillna(0)
    df["이전포인트"] = pd.to_numeric(df["이전포인트"], errors="coerce").fillna(0)

    return df

def save_rank(df):
    df.to_csv(RANK_FILE,index=False)

# =========================
# 이름 처리
# =========================
def clean(x):
    return str(x).strip().replace(" ","")

def team_name(t):
    return t[0] if len(t)==1 else f"{t[0]}&{t[1]}"

# =========================
# 그룹 생성 (랭킹 기반)
# =========================
def make_groups(players, sizes):
    rank = load_rank().sort_values("현재포인트", ascending=False)

    sorted_players = [p for p in rank["이름"] if p in players]

    groups = {g: [] for g in sizes}

    idx = []
    for g, s in sizes.items():
        idx += [g]*s

    for i, p in enumerate(sorted_players):
        if i < len(idx):
            groups[idx[i]].append(p)

    return groups

# =========================
# 페어
# =========================
def make_pairs(players, mode):

    if mode == "고정페어":
        return [(players[i], players[-1-i]) for i in range(len(players)//2)]

    if mode == "KDK":
        temp = players[:]
        random.shuffle(temp)
        return [(temp[i], temp[i+1]) for i in range(0, len(temp), 2)]

    return [(p,) for p in players]

# =========================
# 대진 (2코트)
# =========================
def make_schedule(teams):

    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)

    rounds = []

    while matches:
        used = set()
        r = []

        for m in matches[:]:
            if m[0] in used or m[1] in used:
                continue

            r.append(m)
            used.add(m[0])
            used.add(m[1])
            matches.remove(m)

            if len(r) == 2:
                break

        if not r:
            break

        rounds.append(r)

    return rounds

# =========================
# 메뉴
# =========================
menu = st.sidebar.radio("메뉴",
["두류랭킹","대진 및 경기","경기 결과","관리자"])

# =========================
# 랭킹
# =========================
if menu == "두류랭킹":

    st.title("🏆 두류랭킹")

    df = load_rank()

    if len(df) == 0:
        st.warning("엑셀 업로드 필요")
    else:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)

        df.insert(0, "랭킹", df.index + 1)

        df["변동"] = df["현재포인트"] - df["이전포인트"]

        st.dataframe(df, use_container_width=True, hide_index=True)

# =========================
# 대진
# =========================
elif menu == "대진 및 경기":

    st.title("🎾 대진 및 경기")

    if not st.session_state.schedule:
        st.warning("대진 생성 필요")
    else:

        tabs = st.tabs(list(st.session_state.schedule.keys()))

        for idx, g in enumerate(st.session_state.schedule.keys()):

            with tabs[idx]:

                rounds = st.session_state.schedule[g]

                for ri, rd in enumerate(rounds):

                    st.markdown(f"### {ri+1} 라운드")

                    cols = st.columns(2)

                    for i, m in enumerate(rd):

                        t1, t2 = m

                        n1 = team_name(t1)
                        n2 = team_name(t2)

                        with cols[i]:

                            st.markdown(f"""
                            <div class="team1">{n1}</div>
                            <div class="vs">VS</div>
                            <div class="team2">{n2}</div>
                            """, unsafe_allow_html=True)

                            key = f"{g}_{ri}_{i}"

                            s1 = st.number_input(n1, 0, 50, 0, key=key+"_1")
                            s2 = st.number_input(n2, 0, 50, 0, key=key+"_2")

                            if st.button(f"저장 {key}"):

                                st.session_state.scores[(tuple(t1), tuple(t2))] = (s1, s2)

# =========================
# 결과
# =========================
elif menu == "경기 결과":

    st.title("📊 경기 결과")

    rank = load_rank()
    player_scores = {}

    for (t1, t2), (s1, s2) in st.session_state.scores.items():

        if s1 > s2:
            winners = t1
        elif s2 > s1:
            winners = t2
        else:
            continue

        for p in winners:
            player_scores[p] = player_scores.get(p, 0) + 3

    if st.button("🏆 랭킹 반영"):

        rank["이전포인트"] = rank["현재포인트"]

        for p, pt in player_scores.items():

            if p in rank["이름"].values:
                rank.loc[rank["이름"] == p, "현재포인트"] += pt
            else:
                rank = pd.concat([
                    rank,
                    pd.DataFrame([[p, pt, 0]],
                                 columns=["이름","현재포인트","이전포인트"])
                ])

        save_rank(rank)
        st.success("완료")
