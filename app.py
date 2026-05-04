import streamlit as st
import pandas as pd
import random
import os
import string

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"

# ----------------------
# 상태 초기화
# ----------------------
defaults = {
    "players_all": [],
    "players_selected": [],
    "groups": {},
    "group_types": {},
    "schedule": {},
    "pairs": {},
    "scores": {},
    "current_round": {},
    "group_count": 2,
    "is_admin": False,
    "user_name": ""
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------
# 스타일
# ----------------------
st.markdown("""
<style>
h1,h2,h3 {text-align:center;}
.card {
    padding:14px;
    margin:6px;
    border-radius:14px;
    background:#f4f6f8;
    text-align:center;
    font-weight:600;
}
.now {background:#ffe066;}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 랭킹
# ----------------------
def load_rank():
    if os.path.exists(RANK_FILE):
        df = pd.read_csv(RANK_FILE)
        df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors="coerce").fillna(0)
        df["이전포인트"] = pd.to_numeric(df["이전포인트"], errors="coerce").fillna(0)
        return df
    return pd.DataFrame(columns=["이름","현재포인트","이전포인트"])

def save_rank(df):
    df.to_csv(RANK_FILE, index=False)

# ----------------------
# 그룹 생성
# ----------------------
def make_groups(players, group_count):
    rank_df = load_rank()
    rank_map = {r["이름"]:r["현재포인트"] for _,r in rank_df.iterrows()}

    players_sorted = sorted(players, key=lambda x: rank_map.get(x,0), reverse=True)

    names = list(string.ascii_uppercase[:group_count])
    groups = {n:[] for n in names}

    idx, direction = 0, 1

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

    df = load_rank()

    if len(df):
        df["변동"] = df["현재포인트"] - df["이전포인트"]
        df["변동"] = df["변동"].apply(lambda x: f"⬆{int(x)}" if x>0 else f"⬇{abs(int(x))}" if x<0 else "-")
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df["순위"] = df.index+1
        st.dataframe(df, use_container_width=True)

# ----------------------
# 2. 대진 (보기 전용)
# ----------------------
elif menu == "대진 및 경기 현황":
    st.title("🎮 경기 현황")

    if not st.session_state.schedule:
        st.warning("관리자가 대진 생성 필요")
    else:
        tabs = st.tabs(list(st.session_state.schedule.keys()))

        for i,g in enumerate(st.session_state.schedule.keys()):
            with tabs[i]:
                rounds = st.session_state.schedule[g]

                for ri, rd in enumerate(rounds):
                    cols = st.columns(2)

                    for j,m in enumerate(rd):
                        with cols[j]:
                            cls = "card now" if ri == st.session_state.current_round[g] else "card"
                            st.markdown(f"<div class='{cls}'>{m[0]} vs {m[1]}</div>", unsafe_allow_html=True)

# ----------------------
# 3. 경기 결과 (본인만 입력)
# ----------------------
elif menu == "경기 결과":
    st.title("📊 경기 결과 입력")

    if not st.session_state.schedule:
        st.warning("대진 없음")
    else:
        name = st.selectbox("본인 선택", st.session_state.players_selected)
        st.session_state.user_name = name

        for g, rounds in st.session_state.schedule.items():

            st.subheader(f"{g} 그룹")

            for ri, rd in enumerate(rounds):
                for m in rd:
                    a,b = m

                    if name in m:
                        st.markdown(f"### {a} vs {b}")

                        key1 = f"{a}_{b}_{g}_{ri}_1"
                        key2 = f"{a}_{b}_{g}_{ri}_2"

                        s1 = st.number_input(a,0,50,0,key=key1)
                        s2 = st.number_input(b,0,50,0,key=key2)

                        st.session_state.scores[(a,b)] = (s1,s2)

# ----------------------
# 4. 관리자
# ----------------------
elif menu == "관리자 설정":
    st.title("⚙ 관리자")

    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if pw == "0502":
            st.session_state.is_admin = True
            st.success("관리자 로그인")

    if st.session_state.is_admin:

        # 참가자 입력
        raw = st.text_area("참가자 입력")

        if st.button("등록"):
            st.session_state.players_all = [p.strip() for p in raw.split(",") if p.strip()]

        selected = []
        for p in st.session_state.players_all:
            if st.checkbox(p, value=True):
                selected.append(p)

        if st.button("전체 선택"):
            selected = st.session_state.players_all.copy()

        st.session_state.players_selected = selected

        # 그룹 설정
        st.session_state.group_count = st.number_input("그룹 수",2,6,2)

        if st.button("그룹 생성"):
            st.session_state.groups = make_groups(selected, st.session_state.group_count)

        # 경기 방식 + 페어
        for g, players in st.session_state.groups.items():
            st.subheader(f"{g} 그룹")

            mode = st.selectbox("경기 방식",["단식","고정페어","KDK"], key=f"type_{g}")
            st.session_state.group_types[g] = mode

            if mode != "단식":
                pairs = make_pairs(players, mode)
                st.session_state.pairs[g] = pairs

                for p in pairs:
                    st.markdown(f"<div class='card'>{p[0]} / {p[1]}</div>", unsafe_allow_html=True)

        # 대진 생성
        if st.button("대진 생성"):
            for g, players in st.session_state.groups.items():
                base = players
                st.session_state.schedule[g] = make_schedule(base)
                st.session_state.current_round[g] = 0

        st.success("설정 완료")
