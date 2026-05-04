import streamlit as st
import pandas as pd
import random
import os

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"

# ----------------------
# 상태
# ----------------------
for k,v in {
    "players_selected": [],
    "groups": {},
    "pairs": {},
    "schedule": {},
    "scores": {},
    "is_admin": False
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------
# 이름 정리
# ----------------------
def clean(x):
    return str(x).strip().replace(" ","")

def team_name(t):
    return t[0] if len(t)==1 else f"{t[0]}&{t[1]}"

# ----------------------
# CSS (대각선 포함)
# ----------------------
st.markdown("""
<style>
thead th, tbody td {text-align:center !important;}

.diagonal {
    background:
    linear-gradient(to bottom right, transparent 49%, black 50%, transparent 51%);
}

.match {display:flex; justify-content:center; gap:20px; margin:20px;}
.team {padding:14px 22px; border-radius:20px; color:white; background:#4CAF50;}
.team2 {background:#2196F3;}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 파일
# ----------------------
def load_rank():
    if os.path.exists(RANK_FILE):
        df = pd.read_csv(RANK_FILE)
        df["이름"] = df["이름"].apply(clean)
        return df
    return pd.DataFrame(columns=["이름","현재포인트","이전포인트"])

def save_rank(df):
    df.to_csv(RANK_FILE,index=False)

# ----------------------
# 그룹 (랭킹 기준)
# ----------------------
def make_groups(players, sizes):
    rank = load_rank().sort_values("현재포인트",ascending=False)
    players = [p for p in rank["이름"] if p in players]

    groups = {g:[] for g in sizes}
    idx=[]
    for g,s in sizes.items():
        idx += [g]*s

    for i,p in enumerate(players):
        if i<len(idx):
            groups[idx[i]].append(p)

    return groups

# ----------------------
# KDK 한울 방식
# ----------------------
def kdk_pairs(players):
    players = players[:]
    random.shuffle(players)
    return [(players[i],players[i+1]) for i in range(0,len(players),2)]

# ----------------------
# 페어
# ----------------------
def make_pairs(players, mode):
    if mode=="고정페어":
        return [(players[i],players[-1-i]) for i in range(len(players)//2)]
    if mode=="KDK":
        return kdk_pairs(players)
    return [(p,) for p in players]

# ----------------------
# 경기 수 결정
# ----------------------
def games_per_player(n):
    return 3 if n<=6 else 4

# ----------------------
# 대진 생성
# ----------------------
def make_schedule(players, mode):

    gpp = games_per_player(len(players))

    schedule = []
    played = {p:0 for p in players}

    while min(played.values()) < gpp:

        if mode=="KDK":
            pairs = kdk_pairs(players)
        else:
            pairs = make_pairs(players, mode)

        matches=[]
        for i in range(0,len(pairs),2):
            if i+1 < len(pairs):
                matches.append((pairs[i],pairs[i+1]))

        schedule.append(matches)

        for m in matches:
            for t in m:
                for p in t:
                    played[p]+=1

    return schedule

# ----------------------
# 매트릭스
# ----------------------
def draw_matrix(teams):

    names=[team_name(t) for t in teams]

    table="<table border=1 style='margin:auto'>"
    table+="<tr><td></td>"+"".join([f"<td>{n}</td>" for n in names])+"</tr>"

    for i,t1 in enumerate(teams):
        table+=f"<tr><td>{names[i]}</td>"
        for j,t2 in enumerate(teams):
            if i==j:
                table+="<td class='diagonal'></td>"
            else:
                key=(tuple(t1),tuple(t2))
                if key in st.session_state.scores:
                    s1,s2=st.session_state.scores[key]
                    table+=f"<td>{s1}:{s2}</td>"
                else:
                    table+="<td></td>"
        table+="</tr>"

    table+="</table>"
    st.markdown(table, unsafe_allow_html=True)

# ----------------------
# 메뉴
# ----------------------
menu = st.sidebar.radio("메뉴",
["두류랭킹","대진 및 경기","경기 결과","관리자"])

# ----------------------
# 랭킹
# ----------------------
if menu=="두류랭킹":

    st.title("🏆 두류랭킹")

    df = load_rank()

    if len(df):
        df=df.sort_values("현재포인트",ascending=False).reset_index(drop=True)
        df.insert(0,"랭킹",df.index+1)

        st.dataframe(df, use_container_width=True, hide_index=True)

# ----------------------
# 대진
# ----------------------
elif menu=="대진 및 경기":

    st.title("🎾 대진")

    for g, rounds in st.session_state.schedule.items():

        st.subheader(g)

        for ri,rd in enumerate(rounds):

            st.markdown(f"### {ri+1}라운드")

            cols = st.columns(2)

            for i,m in enumerate(rd):
                t1,t2=m
                n1=team_name(t1)
                n2=team_name(t2)

                with cols[i]:

                    st.markdown(f"""
                    <div class="match">
                        <div class="team">{n1}</div>
                        <div>VS</div>
                        <div class="team team2">{n2}</div>
                    </div>
                    """, unsafe_allow_html=True)

                    key=f"{g}_{ri}_{i}"

                    s1=st.number_input(n1,0,50,0,key=key+"_1")
                    s2=st.number_input(n2,0,50,0,key=key+"_2")

                    if st.button(f"저장 {key}"):

                        st.session_state.scores[(tuple(t1),tuple(t2))]=(s1,s2)
                        st.session_state.scores[(tuple(t2),tuple(t1))]=(s2,s1)

# ----------------------
# 결과
# ----------------------
elif menu=="경기 결과":

    st.title("📊 경기 결과")

    rank = load_rank()
    player_scores={}

    for g,teams in st.session_state.pairs.items():

        st.subheader(g)

        result={}

        for (t1,t2),(s1,s2) in st.session_state.scores.items():

            n1=team_name(t1)
            n2=team_name(t2)

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

        df=pd.DataFrame(result).T.reset_index()
        df.columns=["팀","승","패","득실"]
        df=df.sort_values(["승","득실"],ascending=False)
        df.insert(0,"순위",range(1,len(df)+1))

        st.dataframe(df, use_container_width=True, hide_index=True)

        for _,row in df.iterrows():
            players=row["팀"].split("&")
            pt = 7 if row["순위"]==1 else 5 if row["순위"]==2 else 3 if row["순위"]==3 else 1

            for p in players:
                player_scores[p]=player_scores.get(p,0)+pt

    if st.button("🏆 랭킹 반영"):
        rank["이전포인트"]=rank["현재포인트"]

        for p,pt in player_scores.items():
            if p in rank["이름"].values:
                rank.loc[rank["이름"]==p,"현재포인트"]+=pt
            else:
                rank=pd.concat([rank,pd.DataFrame([[p,pt,0]],columns=["이름","현재포인트","이전포인트"])])

        save_rank(rank)
        st.success("완료")

# ----------------------
# 관리자
# ----------------------
elif menu=="관리자":

    if st.text_input("비밀번호",type="password")=="0502":
        st.session_state.is_admin=True

    if st.session_state.is_admin:

        raw=st.text_area("참가자 입력")

        if st.button("등록"):
            st.session_state.players_selected=[clean(p) for p in raw.split(",") if p.strip()]

        count=st.number_input("그룹 수",2,6,2)
        names=list("ABCDEF")[:count]

        sizes={}
        for g in names:
            sizes[g]=st.number_input(f"{g} 인원",1,20,4)

        if st.button("그룹 생성"):
            st.session_state.groups=make_groups(st.session_state.players_selected,sizes)

        for g,players in st.session_state.groups.items():
            st.subheader(g)
            mode=st.selectbox("방식",["단식","고정페어","KDK"],key=g)

            st.session_state.pairs[g]=make_pairs(players,mode)
            st.session_state.schedule[g]=make_schedule(players,mode)
