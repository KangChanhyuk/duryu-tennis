import streamlit as st
import pandas as pd
import random
import os
import string

st.set_page_config(layout="wide")

# ----------------------
# 상태 초기화
# ----------------------
defaults = {
    "players_all": [],
    "players_selected": [],
    "groups": {},
    "group_sizes": {},
    "group_types": {},
    "pairs": {},
    "schedule": {},
    "scores": {},
    "current_round": {},
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
    return [(p,) for p in players]  # 단식

# ----------------------
# 그룹 생성 (빠짐 방지)
# ----------------------
def make_groups(players, group_sizes):
    groups = {g:[] for g in group_sizes.keys()}

    idx_list = []
    for g, size in group_sizes.items():
        idx_list += [g]*size

    # 부족한 경우 자동 채움
    while len(idx_list) < len(players):
        idx_list.append(list(group_sizes.keys())[0])

    for i, p in enumerate(players):
        groups[idx_list[i]].append(p)

    return groups

# ----------------------
# 대진 생성 (페어 기준)
# ----------------------
def make_schedule(teams):
    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1,len(teams))]
    random.shuffle(matches)

    rounds=[]
    while matches:
        used=set()
        r=[]

        for m in matches[:]:
            t1, t2 = m

            if t1 in used or t2 in used:
                continue

            r.append(m)
            used.add(t1)
            used.add(t2)
            matches.remove(m)

            if len(r)==2:
                break

        if not r:
            break

        rounds.append(r)

    return rounds

# ----------------------
# 매트릭스 (페어)
# ----------------------
def draw_matrix(teams, scores):
    names = [" / ".join(t) for t in teams]

    table = "<table class='matrix'>"
    table += "<tr><td></td>" + "".join([f"<td>{n}</td>" for n in names]) + "</tr>"

    for i, t1 in enumerate(teams):
        table += f"<tr><td>{names[i]}</td>"

        for j, t2 in enumerate(teams):
            if i == j:
                table += "<td>❌</td>"
            else:
                key = (tuple(t1), tuple(t2))
                if key in scores:
                    s1,s2 = scores[key]
                    table += f"<td>{s1}:{s2}</td>"
                else:
                    table += "<td></td>"
        table += "</tr>"

    table += "</table>"
    st.markdown(table, unsafe_allow_html=True)

# ----------------------
# 메뉴
# ----------------------
menu = st.sidebar.radio("메뉴", ["대진 및 경기 현황","경기 결과","관리자 설정"])

# ----------------------
# 관리자
# ----------------------
if menu == "관리자 설정":

    st.title("⚙ 관리자")

    pw = st.text_input("비밀번호", type="password")
    if st.button("로그인"):
        if pw == "0502":
            st.session_state.is_admin = True

    if st.session_state.is_admin:

        raw = st.text_area("참가자 입력")
        if st.button("등록"):
            st.session_state.players_selected = [p.strip() for p in raw.split(",") if p.strip()]

        total = len(st.session_state.players_selected)
        st.info(f"총 참가자: {total}")

        # 그룹 설정
        count = st.number_input("그룹 수",2,6,2)
        names = list(string.ascii_uppercase[:count])

        group_sizes = {}
        total_set = 0

        for g in names:
            size = st.number_input(f"{g} 그룹 인원",1,20,4)
            group_sizes[g] = size
            total_set += size

        st.write(f"설정 인원 합: {total_set}")

        if total_set != total:
            st.warning("⚠ 인원 불일치 (자동 보정됨)")

        st.session_state.group_sizes = group_sizes

        # 그룹 생성
        if st.button("그룹 생성"):
            st.session_state.groups = make_groups(st.session_state.players_selected, group_sizes)

        # 경기 방식 + 페어
        for g, players in st.session_state.groups.items():
            st.subheader(f"{g} 그룹")

            mode = st.selectbox("경기 방식",["단식","고정페어","KDK"], key=g)
            pairs = make_pairs(players, mode)
            st.session_state.pairs[g] = pairs

            for p in pairs:
                st.markdown(f"<div class='card'>{' / '.join(p)}</div>", unsafe_allow_html=True)

        # 대진 생성
        if st.button("대진 생성"):
            for g, teams in st.session_state.pairs.items():
                st.session_state.schedule[g] = make_schedule(teams)
                st.session_state.current_round[g] = 0

# ----------------------
# 대진
# ----------------------
elif menu == "대진 및 경기 현황":

    st.title("🎮 대진 및 경기")

    for g, rounds in st.session_state.schedule.items():

        st.subheader(f"{g} 그룹")

        teams = st.session_state.pairs[g]

        draw_matrix(teams, st.session_state.scores)

        for ri, rd in enumerate(rounds):
            cols = st.columns(2)

            for i,m in enumerate(rd):
                t1,t2 = m
                with cols[i]:
                    name1 = " / ".join(t1)
                    name2 = " / ".join(t2)

                    st.markdown(f"<div class='card'>{name1} vs {name2}</div>", unsafe_allow_html=True)

                    s1 = st.number_input(name1,0,50,0,key=f"{name1}{ri}")
                    s2 = st.number_input(name2,0,50,0,key=f"{name2}{ri}")

                    if s1 or s2:
                        st.session_state.scores[(tuple(t1),tuple(t2))] = (s1,s2)
                        st.session_state.scores[(tuple(t2),tuple(t1))] = (s2,s1)

# ----------------------
# 결과
# ----------------------
elif menu == "경기 결과":

    st.title("📊 경기 결과")

    for g, teams in st.session_state.pairs.items():

        st.subheader(f"{g} 그룹")

        draw_matrix(teams, st.session_state.scores)

        result = {}

        for (t1,t2), (s1,s2) in st.session_state.scores.items():

            n1 = " / ".join(t1)
            n2 = " / ".join(t2)

            for t in [n1,n2]:
                if t not in result:
                    result[t] = {"승":0,"패":0,"득실":0}

            if s1 > s2:
                result[n1]["승"]+=1
                result[n2]["패"]+=1
            elif s2 > s1:
                result[n2]["승"]+=1
                result[n1]["패"]+=1

            result[n1]["득실"] += s1-s2
            result[n2]["득실"] += s2-s1

        df = pd.DataFrame(result).T.reset_index()
        df.columns = ["팀","승","패","득실"]
        df = df.sort_values(["승","득실"], ascending=False)
        df["순위"] = range(1,len(df)+1)

        st.dataframe(df)
