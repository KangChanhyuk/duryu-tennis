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
    "group_count": 2,
    "group_types": {},
    "schedule": {},
    "current_round": {},
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------
# 스타일 (중앙 정렬)
# ----------------------
st.markdown("""
<style>
h1,h2,h3 {text-align:center;}
.card {
    padding:12px;
    margin:6px;
    border-radius:12px;
    background:#eef1f5;
    text-align:center;
}
.now {background:#ffe066;}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 랭킹 로드
# ----------------------
def load_rank():
    if os.path.exists(RANK_FILE):
        return pd.read_csv(RANK_FILE)
    return pd.DataFrame(columns=["이름","현재포인트"])

# ----------------------
# 그룹 생성 (Snake)
# ----------------------
def make_groups(players, group_count):
    rank_df = load_rank()
    rank_map = {r["이름"]:r["현재포인트"] for _,r in rank_df.iterrows()}

    players_sorted = sorted(players, key=lambda x: rank_map.get(x,0), reverse=True)

    group_names = list(string.ascii_uppercase[:group_count])
    groups = {g:[] for g in group_names}

    idx = 0
    direction = 1

    for p in players_sorted:
        groups[group_names[idx]].append(p)

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
# 대진 생성
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
menu = st.sidebar.radio("메뉴", ["참가자 명단","대진"])

# ----------------------
# 1. 참가자 + 그룹
# ----------------------
if menu == "참가자 명단":

    st.title("👥 참가자 관리")

    raw = st.text_area("참가자 입력 (쉼표)")
    if st.button("등록"):
        st.session_state.players_all = [p.strip() for p in raw.split(",") if p.strip()]

    # 그룹 개수 설정
    st.session_state.group_count = st.number_input("그룹 개수", min_value=2, max_value=6, value=2)

    selected = []
    for p in st.session_state.players_all:
        if st.checkbox(p, value=True):
            selected.append(p)

    st.session_state.players_selected = selected

    # 그룹 생성 버튼
    if st.button("그룹 생성"):
        st.session_state.groups = make_groups(selected, st.session_state.group_count)

    # 그룹 탭 표시
    if st.session_state.groups:
        tabs = st.tabs(list(st.session_state.groups.keys()))

        for i, g in enumerate(st.session_state.groups.keys()):
            with tabs[i]:
                st.subheader(f"{g} 그룹")

                players = st.session_state.groups[g]

                for p in players:
                    st.markdown(f"<div class='card'>{p}</div>", unsafe_allow_html=True)

                # 그룹별 경기 방식 설정
                mode = st.selectbox(
                    f"{g} 그룹 경기 방식",
                    ["단식","고정페어","KDK"],
                    key=f"type_{g}"
                )
                st.session_state.group_types[g] = mode

# ----------------------
# 2. 대진
# ----------------------
elif menu == "대진":

    st.title("🎮 그룹별 대진")

    if st.button("대진 생성"):

        for g, players in st.session_state.groups.items():
            mode = st.session_state.group_types.get(g, "단식")

            if mode == "단식":
                st.session_state.schedule[g] = make_schedule(players)
            else:
                pairs = make_pairs(players, mode)
                flat = [p for pair in pairs for p in pair]
                st.session_state.schedule[g] = make_schedule(flat)

            st.session_state.current_round[g] = 0

    # 그룹별 탭
    if st.session_state.schedule:
        tabs = st.tabs(list(st.session_state.schedule.keys()))

        for i, g in enumerate(st.session_state.schedule.keys()):
            with tabs[i]:
                st.subheader(f"{g} 그룹 진행")

                rounds = st.session_state.schedule[g]

                for ri, rd in enumerate(rounds):
                    cols = st.columns(2)

                    for j, m in enumerate(rd):
                        with cols[j]:
                            cls = "card now" if ri == st.session_state.current_round[g] else "card"
                            st.markdown(
                                f"<div class='{cls}'>{m[0]} vs {m[1]}</div>",
                                unsafe_allow_html=True
                            )

                if st.button(f"{g} 다음 경기"):
                    st.session_state.current_round[g] += 1
