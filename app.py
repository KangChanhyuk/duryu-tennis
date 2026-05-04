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
TOUR_FILE = "tournaments.csv"
MATCH_FILE = "match_history.csv"

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
        "is_admin": False,
        "current_tour": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================
# 스타일 (페어 카드 UI)
# =========================
st.markdown("""
<style>
h1,h2,h3 {text-align:center;}

.team-card {
    padding:18px;
    border-radius:20px;
    background: linear-gradient(135deg,#4CAF50,#2E7D32);
    color:white;
    font-weight:bold;
    text-align:center;
    margin:10px;
    font-size:18px;
}

.team-card2 {
    padding:18px;
    border-radius:20px;
    background: linear-gradient(135deg,#2196F3,#1565C0);
    color:white;
    font-weight:bold;
    text-align:center;
    margin:10px;
    font-size:18px;
}

.vs {
    font-size:20px;
    font-weight:bold;
    margin-top:25px;
}

.center td, .center th {
    text-align:center !important;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 공통 함수
# =========================
def clean(x):
    return str(x).strip().replace(" ","")

def team_name(t):
    return t[0] if len(t)==1 else f"{t[0]}&{t[1]}"

def safe_load(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        for c in cols:
            if c not in df.columns:
                df[c] = 0
        return df
    return pd.DataFrame(columns=cols)

def safe_save(df, file):
    df.to_csv(file, index=False)

# =========================
# 랭킹
# =========================
def load_rank():
    df = safe_load(RANK_FILE, ["이름","현재포인트","이전포인트"])
    df["이름"] = df["이름"].astype(str)
    df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors="coerce").fillna(0)
    df["이전포인트"] = pd.to_numeric(df["이전포인트"], errors="coerce").fillna(0)
    return df

def save_rank(df):
    safe_save(df, RANK_FILE)

# =========================
# 그룹 생성 (랭킹 기반)
# =========================
def make_groups(players, sizes):
    rank = load_rank().sort_values("현재포인트", ascending=False)
    players_sorted = [p for p in rank["이름"] if p in players]

    groups = {g: [] for g in sizes}
    idx = []
    for g, s in sizes.items():
        idx += [g]*s

    for i, p in enumerate(players_sorted):
        if i < len(idx):
            groups[idx[i]].append(p)

    return groups

# =========================
# 페어 생성
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
# 대진 생성 (2코트)
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
# 랭킹 화면
# =========================
if menu == "두류랭킹":

    st.title("🏆 두류랭킹")

    df = load_rank()

    if len(df) == 0:
        st.warning("⚠️ 관리자에서 엑셀 업로드 필요")
    else:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df.insert(0, "랭킹", df.index + 1)

        df["변동"] = df["현재포인트"] - df["이전포인트"]

        df["변동"] = df["변동"].apply(
            lambda x: f"⬆{int(x)}" if x > 0 else f"⬇{abs(int(x))}" if x < 0 else "-"
        )

        st.dataframe(df, use_container_width=True, hide_index=True)

# =========================
# 대진 (그룹 탭)
# =========================
elif menu == "대진 및 경기":

    st.title("🎾 대진 및 경기")

    if not st.session_state.schedule:
        st.warning("⚠️ 관리자에서 대진 생성 필요")
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
                            <div style="display:flex; justify-content:center;">
                                <div class="team-card">{n1}</div>
                                <div class="vs">VS</div>
                                <div class="team-card2">{n2}</div>
                            </div>
                            """, unsafe_allow_html=True)

                            key = f"{g}_{ri}_{i}"

                            s1 = st.number_input(n1, 0, 50, 0, key=key+"_1")
                            s2 = st.number_input(n2, 0, 50, 0, key=key+"_2")

                            if st.button(f"💾 저장 {key}"):

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
        st.success("✅ 랭킹 반영 완료")

# =========================
# 관리자
# =========================
elif menu == "관리자":

    st.title("⚙ 관리자")

    if st.text_input("비밀번호", type="password") == "0502":
        st.session_state.is_admin = True

    if st.session_state.is_admin:

        st.subheader("📂 랭킹 엑셀 업로드")

        file = st.file_uploader("CSV 또는 XLSX 업로드", type=["csv","xlsx"])

        if file:
            df = pd.read_csv(file) if file.name.endswith("csv") else pd.read_excel(file)

            df.columns = ["이름","현재포인트","이전포인트"]
            df["이름"] = df["이름"].apply(clean)

            save_rank(df)
            st.success("업로드 완료")

        st.subheader("👥 참가자")

        raw = st.text_area("쉼표로 입력")

        if st.button("등록"):
            st.session_state.players = [clean(p) for p in raw.split(",") if p.strip()]

        st.subheader("🏷 그룹 설정")

        count = st.number_input("그룹 수", 2, 6, 2)
        names = list("ABCDEF")[:count]

        sizes = {}
        for g in names:
            sizes[g] = st.number_input(f"{g} 인원", 1, 20, 4)

        if st.button("그룹 생성"):
            st.session_state.groups = make_groups(st.session_state.players, sizes)

        for g, players in st.session_state.groups.items():
            st.subheader(g)
            mode = st.selectbox(f"{g} 방식", ["단식","고정페어","KDK"], key=g)
            st.session_state.pairs[g] = make_pairs(players, mode)

        if st.button("🎾 대진 생성"):
            for g, teams in st.session_state.pairs.items():
                st.session_state.schedule[g] = make_schedule(teams)
