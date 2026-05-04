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
# 기본 초기화
# =========================
def init_state():
    defaults = {
        "players": [],
        "groups": {},
        "pairs": {},
        "schedule": {},
        "scores": {},
        "current_round": {},
        "is_admin": False,
        "current_tour": None
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =========================
# 안전한 파일 로드
# =========================
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
# 랭킹 처리
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
# 대회 처리
# =========================
def load_tours():
    return safe_load(TOUR_FILE, ["대회ID","대회명","날짜"])

def save_tours(df):
    safe_save(df, TOUR_FILE)

# =========================
# 이름 처리
# =========================
def clean(x):
    return str(x).strip().replace(" ","")

def team_name(team):
    return team[0] if len(team)==1 else f"{team[0]}&{team[1]}"

# =========================
# 그룹 (랭킹 기반)
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
# 2코트 대진 생성
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
        st.warning("랭킹 데이터 없음")
    else:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)

        df.insert(0, "랭킹", df.index + 1)

        df["변동"] = df["현재포인트"] - df["이전포인트"]

        df["변동"] = df["변동"].apply(
            lambda x: f"⬆{int(x)}" if x > 0 else f"⬇{abs(int(x))}" if x < 0 else "-"
        )

        st.dataframe(df, use_container_width=True, hide_index=True)

# =========================
# 대진 화면
# =========================
elif menu == "대진 및 경기":

    st.title("🎾 대진 및 경기")

    if not st.session_state.schedule:
        st.warning("대진 생성 필요")
    else:

        for g, rounds in st.session_state.schedule.items():

            st.subheader(f"{g} 그룹")

            for ri, rd in enumerate(rounds):

                st.markdown(f"### {ri+1} 라운드")

                cols = st.columns(2)

                for i, m in enumerate(rd):

                    t1, t2 = m

                    n1 = team_name(t1)
                    n2 = team_name(t2)

                    with cols[i]:

                        st.markdown(f"**{n1} vs {n2}**")

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
                    pd.DataFrame([[p, pt, 0]], columns=["이름","현재포인트","이전포인트"])
                ])

        save_rank(rank)

        st.success("랭킹 반영 완료")

# =========================
# 관리자
# =========================
elif menu == "관리자":

    st.title("⚙ 관리자")

    if st.text_input("비밀번호", type="password") == "0502":
        st.session_state.is_admin = True

    if st.session_state.is_admin:

        st.subheader("대회 관리")

        tours = load_tours()

        name = st.text_input("대회명")

        if st.button("대회 생성"):
            tid = str(datetime.datetime.now().timestamp())
            tours = pd.concat([
                tours,
                pd.DataFrame([[tid, name, datetime.date.today()]],
                             columns=["대회ID","대회명","날짜"])
            ])
            save_tours(tours)
            st.success("대회 생성 완료")

        if len(tours):
            selected = st.selectbox("대회 선택", tours["대회명"])
            st.session_state.current_tour = selected

        raw = st.text_area("참가자 입력 (쉼표 구분)")

        if st.button("참가자 등록"):
            st.session_state.players = [clean(p) for p in raw.split(",") if p.strip()]

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

        if st.button("대진 생성"):
            for g, teams in st.session_state.pairs.items():
                st.session_state.schedule[g] = make_schedule(teams)
