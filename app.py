import streamlit as st
import pandas as pd
import random
import os

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"
ARCHIVE_FILE = "match_archive.csv"

# ----------------------
# 공통 UI 스타일 (중앙 정렬 포함)
# ----------------------
st.markdown("""
<style>
h1, h2, h3 {text-align:center;}
.center {text-align:center;}
.card {
    padding:15px;
    margin:8px;
    border-radius:12px;
    background:#f1f3f6;
    text-align:center;
    font-size:18px;
}
.now {background:#ffe066 !important; font-weight:bold;}
button {height:50px;font-size:16px;border-radius:10px;}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 상태 초기화
# ----------------------
defaults = {
    "is_admin": False,
    "players_all": [],
    "players_selected": [],
    "groups": [],
    "schedule": None,
    "scores": {},
    "result_df": None,
    "current_round": 0,
    "tournament_name": "",
    "match_type": "단식"
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------
# 파일 로드
# ----------------------
def load_rank():
    if os.path.exists(RANK_FILE):
        return pd.read_csv(RANK_FILE)
    return pd.DataFrame(columns=["이름","현재포인트","이전포인트"])

# ----------------------
# 랭킹 파일 업로드 (csv/xlsx)
# ----------------------
def upload_rank(file):
    if file.name.endswith("xlsx"):
        df = pd.read_excel(file)
    else:
        df = pd.read_csv(file)

    df = df.rename(columns={
        "성명":"이름",
        "랭킹포인트":"현재포인트"
    })

    if "이전포인트" not in df.columns:
        df["이전포인트"] = df["현재포인트"]

    df.to_csv(RANK_FILE, index=False)
    return df

# ----------------------
# 그룹 생성 (랭킹 기반)
# ----------------------
def make_groups(players):
    rank_df = load_rank()
    rank_map = {r["이름"]:r["현재포인트"] for _,r in rank_df.iterrows()}

    players_sorted = sorted(players, key=lambda x: rank_map.get(x,0), reverse=True)

    g1, g2 = [], []
    for i, p in enumerate(players_sorted):
        (g1 if i % 2 == 0 else g2).append(p)

    return [g1, g2]

# ----------------------
# 페어 생성
# ----------------------
def make_pairs(players, mode):
    if mode == "고정페어":
        n = len(players)
        return [(players[i], players[n-1-i]) for i in range(n//2)]
    elif mode == "KDK":
        temp = players.copy()
        random.shuffle(temp)
        return [(temp[i], temp[i+1]) for i in range(0,len(temp),2)]
    return []

# ----------------------
# 대진 생성 (2코트)
# ----------------------
def make_schedule(players):
    matches = [(players[i], players[j]) for i in range(len(players)) for j in range(i+1,len(players))]
    random.shuffle(matches)

    rounds = []
    while matches:
        round_match = []
        used = set()

        for m in matches[:]:
            a,b = m
            if a in used or b in used:
                continue

            round_match.append(m)
            used.update([a,b])
            matches.remove(m)

            if len(round_match) == 2:
                break

        if not round_match:
            break

        rounds.append(round_match)

    return rounds

# ----------------------
# 메뉴
# ----------------------
menu = st.sidebar.radio("메뉴", ["두류랭킹","참가자","대진 및 진행","경기 결과","관리자"])

# ----------------------
# 1. 랭킹
# ----------------------
if menu == "두류랭킹":
    st.title("🎾 두류랭킹 시스템")

    file = st.file_uploader("랭킹 업로드 (csv/xlsx)")
    if file:
        df = upload_rank(file)
        st.success("업로드 완료")

    df = load_rank()

    if len(df):
        df["변동"] = df["현재포인트"] - df["이전포인트"]
        df["변동"] = df["변동"].apply(lambda x: f"⬆{x}" if x>0 else f"⬇{abs(x)}" if x<0 else "-")
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df["순위"] = df.index + 1

        st.dataframe(df, use_container_width=True)

# ----------------------
# 2. 참가자
# ----------------------
elif menu == "참가자":
    st.title("👥 참가자 명단")

    if st.session_state.is_admin:
        raw = st.text_area("참가자 입력 (쉼표)")
        if st.button("등록"):
            st.session_state.players_all = [p.strip() for p in raw.split(",") if p.strip()]

    selected = []
    cols = st.columns(4)

    for i, p in enumerate(st.session_state.players_all):
        with cols[i%4]:
            if st.checkbox(p, value=True):
                selected.append(p)

    if st.button("전체 선택"):
        selected = st.session_state.players_all.copy()

    st.session_state.players_selected = selected

    st.markdown(f"<div class='center'>총 인원: {len(selected)}</div>", unsafe_allow_html=True)

# ----------------------
# 3. 대진
# ----------------------
elif menu == "대진 및 진행":
    st.title("🎮 대진 및 진행")

    st.session_state.match_type = st.selectbox("경기 방식", ["단식","고정페어","KDK"])

    if st.button("대진 생성"):
        groups = make_groups(st.session_state.players_selected)

        schedule = {}
        for i,g in enumerate(groups):
            schedule[i] = make_schedule(g)

        st.session_state.groups = groups
        st.session_state.schedule = schedule
        st.session_state.current_round = 0

    if st.session_state.schedule:
        for gi, rounds in st.session_state.schedule.items():
            st.subheader(f"그룹 {gi+1}")

            for ri, rd in enumerate(rounds):
                cols = st.columns(2)
                for i,m in enumerate(rd):
                    with cols[i]:
                        cls = "card now" if ri == st.session_state.current_round else "card"
                        st.markdown(f"<div class='{cls}'>{m[0]} vs {m[1]}</div>", unsafe_allow_html=True)

        if st.button("다음 경기"):
            st.session_state.current_round += 1

# ----------------------
# 4. 결과
# ----------------------
elif menu == "경기 결과":
    st.title("📊 경기 결과")

    if not st.session_state.schedule:
        st.warning("대진 먼저 생성")
    else:
        result = {}

        for gi, rounds in st.session_state.schedule.items():
            st.subheader(f"그룹 {gi+1}")

            for ri, rd in enumerate(rounds):
                cols = st.columns(2)

                for i,m in enumerate(rd):
                    with cols[i]:
                        a,b = m
                        s1 = st.number_input(a, step=1, key=f"{a}{gi}{ri}")
                        s2 = st.number_input(b, step=1, key=f"{b}{gi}{ri}")

                        for p in [a,b]:
                            if p not in result:
                                result[p] = {"승":0,"득실":0}

                        if s1 > s2:
                            result[a]["승"] +=1
                        elif s2 > s1:
                            result[b]["승"] +=1

                        result[a]["득실"] += s1-s2
                        result[b]["득실"] += s2-s1

        if st.button("순위 계산"):
            df = pd.DataFrame(result).T.reset_index()
            df.columns = ["이름","승","득실"]
            df = df.sort_values(["승","득실"], ascending=False).reset_index(drop=True)
            df["순위"] = df.index+1

            st.session_state.result_df = df
            st.dataframe(df)

# ----------------------
# 5. 관리자
# ----------------------
elif menu == "관리자":
    st.title("⚙ 관리자")

    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if pw == "0502":
            st.session_state.is_admin = True
            st.success("관리자 로그인")

    if st.session_state.is_admin and st.session_state.result_df is not None:
        if st.button("랭킹 반영"):
            rank_df = load_rank()
            rank_df["이전포인트"] = rank_df["현재포인트"]

            for _, row in st.session_state.result_df.iterrows():
                pt = 7 if row["순위"]==1 else 5 if row["순위"]==2 else 3 if row["순위"]==3 else 1

                name = row["이름"]
                if name in rank_df["이름"].values:
                    rank_df.loc[rank_df["이름"]==name,"현재포인트"] += pt
                else:
                    rank_df = pd.concat([
                        rank_df,
                        pd.DataFrame([[name,pt,0]], columns=["이름","현재포인트","이전포인트"])
                    ])

            rank_df.to_csv(RANK_FILE, index=False)
            st.success("랭킹 반영 완료")
