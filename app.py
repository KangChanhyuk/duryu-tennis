import streamlit as st
import pandas as pd
import random
import os
import datetime

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"
SEASON_FILE = "season_ranking.csv"
HISTORY_FILE = "match_history.csv"

# ----------------------
# 상태 초기화
# ----------------------
defaults = {
    "players_selected": [],
    "groups": {},
    "pairs": {},
    "schedule": {},
    "scores": {},
    "is_admin": False
}
for k,v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ----------------------
# 유틸
# ----------------------
def team_name(team):
    return team[0] if len(team)==1 else f"{team[0]}&{team[1]}"

# ----------------------
# 랭킹 로드
# ----------------------
def load_csv(file, cols):
    if os.path.exists(file):
        df = pd.read_csv(file)
        for c in cols:
            if c not in df.columns:
                df[c]=0
        return df
    return pd.DataFrame(columns=cols)

def save_csv(df, file):
    df.to_csv(file,index=False)

# ----------------------
# 그룹
# ----------------------
def make_groups(players, sizes):
    groups={g:[] for g in sizes}
    idx=[]
    for g,s in sizes.items():
        idx += [g]*s
    while len(idx)<len(players):
        idx.append(list(sizes.keys())[0])
    for i,p in enumerate(players):
        groups[idx[i]].append(p)
    return groups

# ----------------------
# 페어
# ----------------------
def make_pairs(players, mode):
    if mode=="고정페어":
        return [(players[i],players[-1-i]) for i in range(len(players)//2)]
    if mode=="KDK":
        temp=players[:]
        random.shuffle(temp)
        return [(temp[i],temp[i+1]) for i in range(0,len(temp),2)]
    return [(p,) for p in players]

# ----------------------
# 대진
# ----------------------
def make_schedule(teams):
    matches=[(teams[i],teams[j]) for i in range(len(teams)) for j in range(i+1,len(teams))]
    random.shuffle(matches)
    rounds=[]
    while matches:
        used=set(); r=[]
        for m in matches[:]:
            if m[0] in used or m[1] in used: continue
            r.append(m)
            used.add(m[0]); used.add(m[1])
            matches.remove(m)
            if len(r)==2: break
        if not r: break
        rounds.append(r)
    return rounds

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
                table+="<td>❌</td>"
            else:
                key=(tuple(t1),tuple(t2))
                if key in st.session_state.scores:
                    s1,s2=st.session_state.scores[key]
                    table+=f"<td>{s1}:{s2}</td>"
                else:
                    table+="<td></td>"
        table+="</tr>"
    table+="</table>"
    st.markdown(table,unsafe_allow_html=True)

# ----------------------
# 메뉴
# ----------------------
menu = st.sidebar.radio("메뉴",
["두류랭킹","대진 및 경기","경기 결과","시즌 랭킹","관리자"])

# ----------------------
# 1 랭킹
# ----------------------
if menu=="두류랭킹":
    st.title("🏆 랭킹")
    df=load_csv(RANK_FILE,["이름","현재포인트","이전포인트"])
    if len(df):
        df["변동"]=df["현재포인트"]-df["이전포인트"]
        df["변동"]=df["변동"].apply(lambda x:f"⬆{int(x)}" if x>0 else f"⬇{abs(int(x))}" if x<0 else "-")
        df=df.sort_values("현재포인트",ascending=False).reset_index(drop=True)
        df["순위"]=df.index+1
        st.dataframe(df,use_container_width=True)

# ----------------------
# 2 대진
# ----------------------
elif menu=="대진 및 경기":
    st.title("🎾 대진")

    for g,rounds in st.session_state.schedule.items():
        st.subheader(g)
        teams=st.session_state.pairs[g]
        draw_matrix(teams)

        for ri,rd in enumerate(rounds):
            cols=st.columns(2)
            for i,m in enumerate(rd):
                t1,t2=m
                n1=team_name(t1); n2=team_name(t2)
                with cols[i]:
                    st.markdown(f"**{n1} vs {n2}**")
                    key=f"{n1}_{n2}_{ri}"
                    s1=st.number_input(n1,0,50,0,key=key+"_1")
                    s2=st.number_input(n2,0,50,0,key=key+"_2")

                    if s1 or s2:
                        st.session_state.scores[(tuple(t1),tuple(t2))]=(s1,s2)
                        st.session_state.scores[(tuple(t2),tuple(t1))]=(s2,s1)

# ----------------------
# 3 결과 + 저장 + 랭킹
# ----------------------
elif menu=="경기 결과":
    st.title("📊 결과")

    rank=load_csv(RANK_FILE,["이름","현재포인트","이전포인트"])
    season=load_csv(SEASON_FILE,["이름","포인트"])

    history_rows=[]
    player_scores={}

    for g,teams in st.session_state.pairs.items():
        st.subheader(g)
        draw_matrix(teams)

        result={}
        for (t1,t2),(s1,s2) in st.session_state.scores.items():

            n1=team_name(t1); n2=team_name(t2)

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

            # 기록 저장용
            history_rows.append({
                "날짜":datetime.date.today(),
                "그룹":g,
                "팀1":n1,
                "팀2":n2,
                "점수":f"{s1}:{s2}"
            })

        df=pd.DataFrame(result).T.reset_index()
        df.columns=["팀","승","패","득실"]
        df=df.sort_values(["승","득실"],ascending=False)
        df["순위"]=range(1,len(df)+1)
        st.dataframe(df)

        # 개인 점수
        for _,row in df.iterrows():
            players=row["팀"].split("&")
            r=row["순위"]
            pt=7 if r==1 else 5 if r==2 else 3 if r==3 else 1
            for p in players:
                player_scores[p]=player_scores.get(p,0)+pt

    # 버튼
    if st.button("🏆 반영"):

        rank["이전포인트"]=rank["현재포인트"]

        for p,pt in player_scores.items():
            if p in rank["이름"].values:
                rank.loc[rank["이름"]==p,"현재포인트"]+=pt
            else:
                rank=pd.concat([rank,pd.DataFrame([[p,pt,0]],columns=["이름","현재포인트","이전포인트"])])

        # 시즌 누적
        for p,pt in player_scores.items():
            if p in season["이름"].values:
                season.loc[season["이름"]==p,"포인트"]+=pt
            else:
                season=pd.concat([season,pd.DataFrame([[p,pt]],columns=["이름","포인트"])])

        save_csv(rank,RANK_FILE)
        save_csv(season,SEASON_FILE)

        # 기록 저장
        hist=load_csv(HISTORY_FILE,["날짜","그룹","팀1","팀2","점수"])
        hist=pd.concat([hist,pd.DataFrame(history_rows)])
        save_csv(hist,HISTORY_FILE)

        st.success("완료!")

# ----------------------
# 시즌 랭킹
# ----------------------
elif menu=="시즌 랭킹":
    st.title("📈 시즌 랭킹")
    df=load_csv(SEASON_FILE,["이름","포인트"])
    df=df.sort_values("포인트",ascending=False)
    df["순위"]=range(1,len(df)+1)
    st.dataframe(df)

# ----------------------
# 관리자
# ----------------------
elif menu=="관리자":
    st.title("⚙ 관리자")

    if st.text_input("비밀번호",type="password")=="0502":
        st.session_state.is_admin=True

    if st.session_state.is_admin:

        file=st.file_uploader("엑셀 업로드",type=["csv","xlsx"])

        if file:
            if file.name.endswith("csv"):
                df=pd.read_csv(file)
            else:
                df=pd.read_excel(file)

            df.columns=["이름","현재포인트","이전포인트"]
            save_csv(df,RANK_FILE)
            st.success("랭킹 업로드 완료")

        raw=st.text_area("참가자")
        if st.button("등록"):
            st.session_state.players_selected=[p.strip() for p in raw.split(",") if p.strip()]

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

        if st.button("대진 생성"):
            for g,teams in st.session_state.pairs.items():
                st.session_state.schedule[g]=make_schedule(teams)
