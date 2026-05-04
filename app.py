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

    for i, p in enumerate(players):
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
    names = [" & ".join(t) for t in teams]

    table = "<table class='matrix'>"
    table += "<tr><td></td>" + "".join([f"<td>{n}</td>" for n in names]) + "</tr>"

    for i, t1 in enumerate(teams):
        table += f"<tr><td>{names[i]}</td>"
        for j, t2 in enumerate(teams):
            if i == j:
                table += "<td>❌</td>"
            else:
                key = (tuple(t1), tuple(t2))
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
# 2. 대진
# ----------------------
elif menu == "대진 및 경기 현황":

    st.title("🎮 대진 및 경기")

    for g, rounds in st.session_state.schedule.items():

        st.subheader(f"{g} 그룹")

        teams = st.session_state.pairs[g]

        draw_matrix(teams)

        for ri, rd in enumerate(rounds):
            cols = st.columns(2)

            for i,m in enumerate(rd):
                t1,t2 = m

                with cols[i]:
                    name1 = " & ".join(t1)
                    name2 = " & ".join(t2)

                    st.markdown(f"<div class='card'>{name1} vs {name2}</div>", unsafe_allow_html=True)

                    key = f"{name1}_{name2}_{ri}"

                    s1 = st.number_input(f"{name1}",0,50,0,key=key+"_1")
                    s2 = st.number_input(f"{name2}",0,50,0,key=key+"_2")

                    if s1 or s2:
                        st.session_state.scores[(tuple(t1),tuple(t2))] = (s1,s2)
                        st.session_state.scores[(tuple(t2),tuple(t1))] = (s2,s1)

# ----------------------
# 3. 결과 + 랭킹 반영
# ----------------------
elif menu == "경기 결과":

    st.title("📊 경기 결과")

    all_player_scores = {}

    for g, teams in st.session_state.pairs.items():

        st.subheader(f"{g} 그룹")

        draw_matrix(teams)

        result = {}

        for (t1,t2), (s1,s2) in st.session_state.scores.items():

            n1 = " & ".join(t1)
            n2 = " & ".join(t2)

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

        # 개인 점수 환산
        for _, row in df.iterrows():
            players = row["팀"].split(" & ")
            r = row["순위"]

            pt = 7 if r==1 else 5 if r==2 else 3 if r==3 else 1

            for p in players:
                all_player_scores[p] = all_player_scores.get(p,0) + pt

    # ----------------------
    # 랭킹 반영 버튼
    # ----------------------
    if st.button("🏆 랭킹 반영"):

        rank_df = load_rank()
        rank_df["이전포인트"] = rank_df["현재포인트"]

        for name, pt in all_player_scores.items():
            if name in rank_df["이름"].values:
                rank_df.loc[rank_df["이름"]==name,"현재포인트"] += pt
            else:
                rank_df = pd.concat([
                    rank_df,
                    pd.DataFrame([[name,pt,0]], columns=["이름","현재포인트","이전포인트"])
                ])

        save_rank(rank_df)

        st.success("랭킹 반영 완료!")

# ----------------------
# 4. 관리자
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
            st.session_state.players_selected = [p.strip() for p in raw.split(",") if p.strip()]

        total = len(st.session_state.players_selected)
        st.info(f"총 참가자: {total}")

        count = st.number_input("그룹 수",2,6,2)
        names = list(string.ascii_uppercase[:count])

        group_sizes = {}
        total_set = 0

        for g in names:
            size = st.number_input(f"{g} 인원",1,20,4)
            group_sizes[g] = size
            total_set += size

        st.write(f"설정 인원 합: {total_set}")

        st.session_state.group_sizes = group_sizes

        if st.button("그룹 생성"):
            st.session_state.groups = make_groups(st.session_state.players_selected, group_sizes)

        for g, players in st.session_state.groups.items():
            st.subheader(f"{g} 그룹")
            mode = st.selectbox("경기 방식",["단식","고정페어","KDK"], key=g)
            pairs = make_pairs(players, mode)
            st.session_state.pairs[g] = pairs

            for p in pairs:
                st.markdown(f"<div class='card'>{' & '.join(p)}</div>", unsafe_allow_html=True)

        if st.button("대진 생성"):
            for g, teams in st.session_state.pairs.items():
                st.session_state.schedule[g] = make_schedule(teams)
                st.session_state.current_round[g] = 0
