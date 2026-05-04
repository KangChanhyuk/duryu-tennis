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
    "players_selected": [],
    "groups": {},
    "group_sizes": {},
    "group_types": {},
    "pairs": {},
    "schedule": {},
    "scores": {},
    "is_admin": False
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
.block-container {text-align:center;}
.card {
    padding:12px;
    margin:6px auto;
    border-radius:12px;
    background:#f4f6f8;
    width:80%;
}
.matrix {
    margin-left:auto;
    margin-right:auto;
}
.matrix td {
    text-align:center;
    padding:6px;
    border:1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 팀 이름 함수 (🔥 핵심)
# ----------------------
def team_name(team):
    return team[0] if len(team) == 1 else f"{team[0]}&{team[1]}"

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
def make_groups(players, group_sizes):
    groups = {g:[] for g in group_sizes.keys()}

    idx_list = []
    for g, size in group_sizes.items():
        idx_list += [g]*size

    while len(idx_list) < len(players):
        idx_list.append(list(group_sizes.keys())[0])

    for i,p in enumerate(players):
        groups[idx_list[i]].append(p)

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
    return [(p,) for p in players]

# ----------------------
# 대진 생성
# ----------------------
def make_schedule(teams):
    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1,len(teams))]
    random.shuffle(matches)

    rounds=[]
    while matches:
        used=set()
        r=[]
        for m in matches[:]:
            if m[0] in used or m[1] in used:
                continue
            r.append(m)
            used.add(m[0]); used.add(m[1])
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
def draw_matrix(teams):
    names = [team_name(t) for t in teams]

    table = "<table class='matrix'>"
    table += "<tr><td></td>" + "".join([f"<td>{n}</td>" for n in names]) + "</tr>"

    for i,t1 in enumerate(teams):
        table += f"<tr><td>{names[i]}</td>"
        for j,t2 in enumerate(teams):
            if i==j:
                table += "<td>❌</td>"
            else:
                key = (tuple(t1),tuple(t2))
                if key in st.session_state.scores:
                    s1,s2 = st.session_state.scores[key]
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
# 랭킹
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
# 대진
# ----------------------
elif menu == "대진 및 경기 현황":

    st.title("🎾 대진 및 경기")

    for g, rounds in st.session_state.schedule.items():

        st.subheader(f"{g} 그룹")
        teams = st.session_state.pairs[g]

        draw_matrix(teams)

        for ri, rd in enumerate(rounds):
            cols = st.columns(2)

            for i,m in enumerate(rd):
                t1,t2 = m
                name1 = team_name(t1)
                name2 = team_name(t2)

                with cols[i]:
                    st.markdown(f"<div class='card'>{name1} vs {name2}</div>", unsafe_allow_html=True)

                    key = f"{name1}_{name2}_{ri}"

                    s1 = st.number_input(name1,0,50,0,key=key+"_1")
                    s2 = st.number_input(name2,0,50,0,key=key+"_2")

                    if s1 or s2:
                        st.session_state.scores[(tuple(t1),tuple(t2))]=(s1,s2)
                        st.session_state.scores[(tuple(t2),tuple(t1))]=(s2,s1)

# ----------------------
# 결과 + 랭킹
# ----------------------
elif menu == "경기 결과":

    st.title("📊 경기 결과")

    total_scores = {}

    for g, teams in st.session_state.pairs.items():

        st.subheader(f"{g} 그룹")
        draw_matrix(teams)

        result = {}

        for (t1,t2),(s1,s2) in st.session_state.scores.items():

            n1 = team_name(t1)
            n2 = team_name(t2)

            for t in [n1,n2]:
                if t not in result:
                    result[t]={"승":0,"패":0,"득실":0}

            if s1>s2:
                result[n1]["승"]+=1
                result[n2]["패"]+=1
            elif s2>s1:
                result[n2]["승"]+=1
                result[n1]["패"]+=1

            result[n1]["득실"]+=s1-s2
            result[n2]["득실"]+=s2-s1

        df = pd.DataFrame(result).T.reset_index()
        df.columns=["팀","승","패","득실"]
        df = df.sort_values(["승","득실"], ascending=False)
        df["순위"]=range(1,len(df)+1)

        st.dataframe(df)

        # 개인 환산
        for _,row in df.iterrows():
            players = row["팀"].split("&")
            r = row["순위"]
            pt = 7 if r==1 else 5 if r==2 else 3 if r==3 else 1

            for p in players:
                total_scores[p] = total_scores.get(p,0)+pt

    if st.button("🏆 랭킹 반영"):
        df = load_rank()
        df["이전포인트"]=df["현재포인트"]

        for name,pt in total_scores.items():
            if name in df["이름"].values:
                df.loc[df["이름"]==name,"현재포인트"] += pt
            else:
                df = pd.concat([df, pd.DataFrame([[name,pt,0]],columns=["이름","현재포인트","이전포인트"])])

        save_rank(df)
        st.success("완료")

# ----------------------
# 관리자
# ----------------------
elif menu == "관리자 설정":

    st.title("⚙ 관리자")

    if st.text_input("비밀번호", type="password")=="0502":
        st.session_state.is_admin=True

    if st.session_state.is_admin:

        raw = st.text_area("참가자 입력")
        if st.button("등록"):
            st.session_state.players_selected=[p.strip() for p in raw.split(",") if p.strip()]

        count = st.number_input("그룹 수",2,6,2)
        names = list(string.ascii_uppercase[:count])

        sizes={}
        for g in names:
            sizes[g]=st.number_input(f"{g} 인원",1,20,4)

        if st.button("그룹 생성"):
            st.session_state.groups = make_groups(st.session_state.players_selected, sizes)

        for g, players in st.session_state.groups.items():
            st.subheader(g)
            mode = st.selectbox("방식",["단식","고정페어","KDK"],key=g)
            pairs = make_pairs(players, mode)
            st.session_state.pairs[g]=pairs

            for p in pairs:
                st.markdown(f"<div class='card'>{team_name(p)}</div>", unsafe_allow_html=True)

        if st.button("대진 생성"):
            for g, teams in st.session_state.pairs.items():
                st.session_state.schedule[g]=make_schedule(teams)
