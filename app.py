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
    "group_sizes": {},
    "group_types": {},
    "schedule": {},
    "scores": {},
    "current_round": {},
    "group_count": 2,
    "is_admin": False
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
    padding:12px;
    margin:5px;
    border-radius:10px;
    background:#f4f6f8;
    text-align:center;
}
.now {background:#ffe066;}
.matrix td {
    text-align:center;
    padding:6px;
    border:1px solid #ddd;
}
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

# ----------------------
# 그룹 생성 (정원 기반)
# ----------------------
def make_groups(players, group_sizes):
    rank_df = load_rank()
    rank_map = {r["이름"]:r["현재포인트"] for _,r in rank_df.iterrows()}

    players_sorted = sorted(players, key=lambda x: rank_map.get(x,0), reverse=True)

    groups = {g:[] for g in group_sizes.keys()}

    idx_list = []
    for g, size in group_sizes.items():
        idx_list += [g]*size

    for i, p in enumerate(players_sorted):
        if i < len(idx_list):
            groups[idx_list[i]].append(p)

    return groups

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
# 매트릭스
# ----------------------
def draw_matrix(players, scores):
    table = "<table class='matrix'>"
    table += "<tr><td></td>" + "".join([f"<td>{p}</td>" for p in players]) + "</tr>"

    for p1 in players:
        table += f"<tr><td>{p1}</td>"
        for p2 in players:
            if p1 == p2:
                table += "<td>❌</td>"
            elif (p1,p2) in scores:
                s1,s2 = scores[(p1,p2)]
                table += f"<td>{s1}:{s2}</td>"
            else:
                table += "<td></td>"
        table += "</tr>"

    table += "</table>"
    st.markdown(table, unsafe_allow_html=True)

# ----------------------
# 메뉴
# ----------------------
menu = st.sidebar.radio("메뉴", ["두류랭킹","대진 및 경기 현황","경기 결과","관리자 설정"])

# ----------------------
# 대진 및 경기 현황
# ----------------------
if menu == "대진 및 경기 현황":

    st.title("🎮 대진 및 경기")

    if not st.session_state.schedule:
        st.warning("관리자 설정 필요")
    else:
        tabs = st.tabs(list(st.session_state.schedule.keys()))

        for i,g in enumerate(st.session_state.schedule.keys()):
            with tabs[i]:

                players = st.session_state.groups[g]
                rounds = st.session_state.schedule[g]

                st.subheader(f"{g} 그룹")

                # 매트릭스
                draw_matrix(players, st.session_state.scores)

                # 경기 순서
                st.markdown("### 경기 순서")

                for ri, rd in enumerate(rounds):
                    cols = st.columns(2)

                    for j,m in enumerate(rd):
                        a,b = m

                        with cols[j]:
                            key = (a,b)

                            cls = "card now" if ri == st.session_state.current_round[g] else "card"

                            st.markdown(f"<div class='{cls}'>{a} vs {b}</div>", unsafe_allow_html=True)

                            s1 = st.number_input(a,0,50,0,key=f"{a}{b}{ri}")
                            s2 = st.number_input(b,0,50,0,key=f"{b}{a}{ri}")

                            if s1 or s2:
                                st.session_state.scores[(a,b)] = (s1,s2)
                                st.session_state.scores[(b,a)] = (s2,s1)

                if st.button(f"{g} 다음 경기"):
                    st.session_state.current_round[g] += 1

# ----------------------
# 경기 결과
# ----------------------
elif menu == "경기 결과":

    st.title("📊 경기 결과")

    for g, players in st.session_state.groups.items():

        st.subheader(f"{g} 그룹")

        draw_matrix(players, st.session_state.scores)

        result = {}

        for (a,b), (s1,s2) in st.session_state.scores.items():

            for p in [a,b]:
                if p not in result:
                    result[p] = {"승":0,"패":0,"득실":0}

            if s1 > s2:
                result[a]["승"] +=1
                result[b]["패"] +=1
            elif s2 > s1:
                result[b]["승"] +=1
                result[a]["패"] +=1

            result[a]["득실"] += s1-s2
            result[b]["득실"] += s2-s1

        df = pd.DataFrame(result).T.reset_index()
        df.columns = ["이름","승","패","득실"]
        df = df.sort_values(["승","득실"], ascending=False).reset_index(drop=True)
        df["순위"] = df.index+1

        st.dataframe(df)

# ----------------------
# 관리자
# ----------------------
elif menu == "관리자 설정":

    st.title("⚙ 관리자")

    pw = st.text_input("비밀번호", type="password")

    if st.button("로그인"):
        if pw == "0502":
            st.session_state.is_admin = True

    if st.session_state.is_admin:

        raw = st.text_area("참가자 입력")

        if st.button("등록"):
            st.session_state.players_all = [p.strip() for p in raw.split(",") if p.strip()]

        selected = []
        for p in st.session_state.players_all:
            if st.checkbox(p, value=True):
                selected.append(p)

        st.session_state.players_selected = selected

        # 그룹 수
        count = st.number_input("그룹 수",2,6,2)

        group_sizes = {}
        names = list(string.ascii_uppercase[:count])

        for g in names:
            group_sizes[g] = st.number_input(f"{g} 인원",1,20,4)

        st.session_state.group_sizes = group_sizes

        if st.button("그룹 생성"):
            st.session_state.groups = make_groups(selected, group_sizes)

        if st.button("대진 생성"):
            for g, players in st.session_state.groups.items():
                st.session_state.schedule[g] = make_schedule(players)
                st.session_state.current_round[g] = 0
