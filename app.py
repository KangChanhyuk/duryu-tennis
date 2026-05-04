import streamlit as st
import pandas as pd
import random
import os
import string

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"
ARCHIVE_FILE = "match_archive.csv"

# ----------------------
# 상태 초기화
# ----------------------
defaults = {
    "players_all": [],
    "players_selected": [],
    "groups": {},
    "group_types": {},
    "schedule": {},
    "current_round": {},
    "results": {},
    "group_count": 2,
    "is_admin": False
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------
# UI 스타일
# ----------------------
st.markdown("""
<style>
h1,h2,h3 {text-align:center;}
.card {padding:12px;margin:6px;border-radius:12px;background:#eef1f5;text-align:center;}
.now {background:#ffe066;}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 랭킹 로드/저장
# ----------------------
def load_rank():
    if os.path.exists(RANK_FILE):
        df = pd.read_csv(RANK_FILE)
        return df.fillna("")
    return pd.DataFrame(columns=["이름","현재포인트","이전포인트"])

def save_rank(df):
    df.to_csv(RANK_FILE, index=False)

# ----------------------
# 업로드
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

    df = df.fillna("")
    save_rank(df)

# ----------------------
# 그룹 생성 (Snake)
# ----------------------
def make_groups(players, group_count):
    rank_df = load_rank()
    rank_map = {r["이름"]:r["현재포인트"] for _,r in rank_df.iterrows()}

    players_sorted = sorted(players, key=lambda x: rank_map.get(x,0), reverse=True)

    names = list(string.ascii_uppercase[:group_count])
    groups = {n:[] for n in names}

    idx = 0
    direction = 1

    for p in players_sorted:
        groups[names[idx]].append(p)

        if direction == 1:
            if idx == group_count-1:
                direction = -1
                idx -= 1
            else:
                idx += 1
        else:
            if idx == 0:
                direction = 1
                idx += 1
            else:
                idx -= 1

    return groups

# ----------------------
# 페어
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
# 대진
# ----------------------
def make_schedule(players):
    matches = [(players[i], players[j]) for i in range(len(players)) for j in range(i+1,len(players))]
    random.shuffle(matches)

    rounds=[]
    while matches:
        used=set()
        r=[]

        for m in matches[:]:
            a,b=m
            if a in used or b in used:
                continue

            r.append(m)
            used.update([a,b])
            matches.remove(m)

            if len(r)==2:
                break

        if not r:
            break

        rounds.append(r)

    return rounds

# ----------------------
# 메뉴
# ----------------------
menu = st.sidebar.radio("메뉴", ["두류랭킹","대진 및 경기 현황","경기 결과","관리자 설정"])

# ----------------------
# 1. 랭킹
# ----------------------
if menu == "두류랭킹":

    st.title("🏆 두류 랭킹")

    file = st.file_uploader("랭킹 업로드")
    if file:
        upload_rank(file)
        st.success("업로드 완료")

    df = load_rank()

    if len(df):
        df["변동"] = df["현재포인트"] - df["이전포인트"]
        df["변동"] = df["변동"].apply(lambda x: f"⬆{x}" if x>0 else f"⬇{abs(x)}" if x<0 else "-")
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df["순위"] = df.index+1

        st.dataframe(df, use_container_width=True)

# ----------------------
# 2. 대진
# ----------------------
elif menu == "대진 및 경기 현황":

    st.title("🎮 대진 및 경기 현황")

    st.session_state.group_count = st.number_input("그룹 수",2,6,2)

    if st.button("그룹 생성"):
        st.session_state.groups = make_groups(st.session_state.players_selected, st.session_state.group_count)

    if st.session_state.groups:

        tabs = st.tabs(list(st.session_state.groups.keys()))

        for i,g in enumerate(st.session_state.groups.keys()):
            with tabs[i]:
                st.subheader(f"{g} 그룹")

                players = st.session_state.groups[g]

                for p in players:
                    st.markdown(f"<div class='card'>{p}</div>", unsafe_allow_html=True)

                mode = st.selectbox("경기 방식",["단식","고정페어","KDK"], key=g)
                st.session_state.group_types[g] = mode

        if st.button("대진 생성"):

            for g, players in st.session_state.groups.items():

                mode = st.session_state.group_types[g]

                if mode == "단식":
                    st.session_state.schedule[g] = make_schedule(players)
                else:
                    pairs = make_pairs(players, mode)
                    flat = [p for pair in pairs for p in pair]
                    st.session_state.schedule[g] = make_schedule(flat)

                st.session_state.current_round[g] = 0

    if st.session_state.schedule:

        tabs = st.tabs(list(st.session_state.schedule.keys()))

        for i,g in enumerate(st.session_state.schedule.keys()):
            with tabs[i]:
                st.subheader(f"{g} 진행")

                rounds = st.session_state.schedule[g]

                for ri, rd in enumerate(rounds):
                    cols = st.columns(2)
                    for j,m in enumerate(rd):
                        with cols[j]:
                            cls = "card now" if ri == st.session_state.current_round[g] else "card"
                            st.markdown(f"<div class='{cls}'>{m[0]} vs {m[1]}</div>", unsafe_allow_html=True)

                if st.button(f"{g} 다음 경기"):
                    st.session_state.current_round[g] += 1

# ----------------------
# 3. 결과
# ----------------------
elif menu == "경기 결과":

    st.title("📊 경기 결과")

    all_results = {}

    for g, rounds in st.session_state.schedule.items():

        st.subheader(f"{g} 그룹")

        group_res = {}

        for ri, rd in enumerate(rounds):
            cols = st.columns(2)

            for i,m in enumerate(rd):
                with cols[i]:
                    a,b = m
                    s1 = st.number_input(a,0,50,0,key=f"{a}{g}{ri}")
                    s2 = st.number_input(b,0,50,0,key=f"{b}{g}{ri}")

                    for p in [a,b]:
                        if p not in group_res:
                            group_res[p] = {"승":0,"득실":0}

                    if s1 > s2:
                        group_res[a]["승"] +=1
                    elif s2 > s1:
                        group_res[b]["승"] +=1

                    group_res[a]["득실"] += s1-s2
                    group_res[b]["득실"] += s2-s1

        df = pd.DataFrame(group_res).T.reset_index()
        df.columns = ["이름","승","득실"]
        df = df.sort_values(["승","득실"], ascending=False).reset_index(drop=True)
        df["순위"] = df.index+1

        st.dataframe(df)

        for _, row in df.iterrows():
            all_results[row["이름"]] = row["순위"]

    if st.button("전체 랭킹 반영"):

        rank_df = load_rank()
        rank_df["이전포인트"] = rank_df["현재포인트"]

        for name, r in all_results.items():

            pt = 7 if r==1 else 5 if r==2 else 3 if r==3 else 1

            if name in rank_df["이름"].values:
                rank_df.loc[rank_df["이름"]==name,"현재포인트"] += pt
            else:
                rank_df = pd.concat([
                    rank_df,
                    pd.DataFrame([[name,pt,0]], columns=["이름","현재포인트","이전포인트"])
                ])

        save_rank(rank_df)
        st.success("랭킹 반영 완료")

# ----------------------
# 4. 관리자
# ----------------------
elif menu == "관리자 설정":

    st.title("⚙ 관리자 설정")

    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if pw == "0502":
            st.session_state.is_admin = True
            st.success("관리자 로그인")

    if st.session_state.is_admin:
        raw = st.text_area("참가자 입력")

        if st.button("참가자 등록"):
            st.session_state.players_all = [p.strip() for p in raw.split(",") if p.strip()]

        selected = []
        for p in st.session_state.players_all:
            if st.checkbox(p, value=True):
                selected.append(p)

        if st.button("전체 선택"):
            selected = st.session_state.players_all.copy()

        st.session_state.players_selected = selected
        st.write("선택 인원:", len(selected))
