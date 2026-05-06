import streamlit as st
import pandas as pd
import random
import os
import json
from datetime import datetime

# =============================
# 설정
# =============================
st.set_page_config(layout="wide", page_title="두류 테니스", page_icon="🎾")

RANK_FILE = "rank.csv"
TOUR_FILE = "tournament.json"

# =============================
# 🎨 CSS (밝은 테니스 스타일)
# =============================
st.markdown("""
<style>
body { background:#e8f5e9; }
.rank-name { color:#000; font-weight:700; }
.center { text-align:center !important; }
.self { background:#e0e0e0 !important; }
.team { width:40%; text-align:center; background:#81c784; padding:10px; border-radius:8px; font-weight:700;}
.vs { font-size:22px; font-weight:900; text-align:center; }
.match { display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;}
</style>
""", unsafe_allow_html=True)

# =============================
# 데이터
# =============================
def load_rank():
    if not os.path.exists(RANK_FILE):
        return pd.DataFrame(columns=["이름","포인트"])
    return pd.read_csv(RANK_FILE)

def save_rank(df):
    df.to_csv(RANK_FILE,index=False)

def load_tour():
    if not os.path.exists(TOUR_FILE):
        return {}
    return json.load(open(TOUR_FILE))

def save_tour(data):
    json.dump(data, open(TOUR_FILE,"w"))

# =============================
# 그룹 분배 (스네이크)
# =============================
def snake(players, groups):
    res = {g:[] for g in groups}
    g_list = list(groups)
    idx = 0
    dir = 1

    for p in players:
        res[g_list[idx]].append(p)
        if dir == 1:
            idx +=1
            if idx>=len(g_list):
                idx-=1; dir=-1
        else:
            idx-=1
            if idx<0:
                idx=0; dir=1
    return res

# =============================
# 페어 (1위-꼴찌)
# =============================
def pair(players):
    res=[]
    n=len(players)
    for i in range(n//2):
        res.append([players[i], players[n-1-i]])
    return res

# =============================
# 대진 생성
# =============================
def round_robin(teams):
    matches=[]
    for i in range(len(teams)):
        for j in range(i+1,len(teams)):
            matches.append([teams[i],teams[j]])
    random.shuffle(matches)

    rounds=[]
    while matches:
        r=[]; used=set(); rest=[]
        for m in matches:
            s=set(m[0]+m[1])
            if not s&used:
                r.append(m); used|=s
            else:
                rest.append(m)
        rounds.append(r)
        matches=rest
    return rounds

# =============================
# 순위 묶기
# =============================
def medal(rank):
    if rank<=2: return "🏆우승"
    elif rank<=4: return "🥈준우승"
    elif rank<=6: return "🥉3위"
    return f"{rank}위"

# =============================
# 세션
# =============================
if "groups" not in st.session_state:
    st.session_state.groups={}
    st.session_state.schedule={}
    st.session_state.scores={}
    st.session_state.mode={}
    st.session_state.num={}

# =============================
# 메뉴
# =============================
menu = st.sidebar.radio("메뉴",["랭킹","대진","결과","관리자"])

# =============================
# 랭킹
# =============================
if menu=="랭킹":
    st.title("🏆 랭킹")
    df=load_rank()
    if df.empty:
        st.info("없음")
    else:
        df=df.sort_values("포인트",ascending=False)
        for i,row in df.iterrows():
            st.markdown(f"{i+1}. {row['이름']} - {row['포인트']}")

# =============================
# 관리자
# =============================
elif menu=="관리자":
    pwd=st.text_input("비번",type="password")
    if pwd=="0502":

        name=st.text_input("대회명","대회")
        players=st.text_area("참가자","A,B,C,D,E,F,G,H")
        gnum=st.number_input("그룹수",1,3,1)

        if st.button("대진 생성"):
            plist=[p.strip() for p in players.split(",") if p.strip()]
            rank=load_rank()
            rmap=dict(zip(rank["이름"],rank["포인트"]))

            plist.sort(key=lambda x:rmap.get(x,0),reverse=True)

            gnames=[chr(65+i) for i in range(gnum)]
            groups=snake(plist,gnames)

            st.session_state.groups={}
            st.session_state.schedule={}
            st.session_state.mode={}
            st.session_state.num={}

            for g in gnames:
                p=groups[g]
                st.session_state.groups[g]=p
                st.session_state.mode[g]="고정페어"

                num={x:i+1 for i,x in enumerate(p)}
                st.session_state.num[g]=num

                pairs=pair(p)
                st.session_state.schedule[g]=round_robin(pairs)

            st.success("완료")

        # 저장
        if st.button("대회 저장"):
            data=load_tour()
            data[name]=dict(groups=st.session_state.groups)
            save_tour(data)
            st.success("저장됨")

        # 삭제
        if st.button("대회 삭제"):
            data=load_tour()
            if name in data:
                del data[name]
                save_tour(data)
                st.success("삭제됨")

# =============================
# 대진
# =============================
elif menu=="대진":
    st.title("📅 대진")

    for g in st.session_state.schedule:
        st.subheader(f"Group {g}")

        for ri,rd in enumerate(st.session_state.schedule[g]):
            st.markdown(f"### ROUND {ri+1}")

            for mi,(t1,t2) in enumerate(rd):
                nmap=st.session_state.num[g]

                t1n=" & ".join([f"{nmap[x]}.{x}" for x in t1])
                t2n=" & ".join([f"{nmap[x]}.{x}" for x in t2])

                c1,c2,c3=st.columns([4,1,4])
                with c1:
                    st.markdown(f"<div class='team'>{t1n}</div>",unsafe_allow_html=True)
                with c2:
                    st.markdown("<div class='vs'>VS</div>",unsafe_allow_html=True)
                with c3:
                    st.markdown(f"<div class='team'>{t2n}</div>",unsafe_allow_html=True)

                s1=st.number_input("",0,10,key=f"s1{g}{ri}{mi}")
                s2=st.number_input("",0,10,key=f"s2{g}{ri}{mi}")

                if st.button("저장",key=f"b{g}{ri}{mi}"):
                    st.session_state.scores[(g,ri,mi)]=(t1,t2,s1,s2)
                    st.success("저장")

# =============================
# 결과
# =============================
elif menu=="결과":
    st.title("📊 결과")

    for g in st.session_state.groups:
        stats={p:0 for p in st.session_state.groups[g]}

        for (gg,ri,mi),(t1,t2,s1,s2) in st.session_state.scores.items():
            if gg!=g: continue
            if s1>s2:
                for p in t1: stats[p]+=1
            elif s2>s1:
                for p in t2: stats[p]+=1

        sorted_p=sorted(stats.items(),key=lambda x:x[1],reverse=True)

        rows=[]
        for i,(p,v) in enumerate(sorted_p):
            rows.append([medal(i+1),p,v])

        df=pd.DataFrame(rows,columns=["순위","이름","승"])
        st.dataframe(df,use_container_width=True)

        if st.button(f"랭킹 반영 {g}"):
            rank=load_rank()

            for i,(p,v) in enumerate(sorted_p):
                pts=100-(i*10)

                if p in rank["이름"].values:
                    rank.loc[rank["이름"]==p,"포인트"]+=pts
                else:
                    rank=pd.concat([rank,pd.DataFrame([[p,pts]],columns=["이름","포인트"])])

            save_rank(rank)
            st.success("반영 완료")
