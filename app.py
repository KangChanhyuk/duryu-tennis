import streamlit as st
import pandas as pd
import random
import os

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"

# ----------------------
# 상태
# ----------------------
for key, default in {
    "is_admin": False,
    "players_all": [],
    "players_selected": [],
    "groups": [],
    "schedule": {},
    "scores": {},
    "current_round": 0
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------
# 스타일 (모바일 최적화 + 강조)
# ----------------------
st.markdown("""
<style>
button {height:55px;font-size:18px;border-radius:12px;}
.card {padding:15px;margin:8px;border-radius:12px;background:#f1f3f6;text-align:center;}
.now {background:#ffeb3b !important;font-weight:bold;}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 사이드바
# ----------------------
with st.sidebar:
    menu = st.radio("메뉴", ["랭킹","참가자","대진","결과","관리자"])

    if menu == "관리자":
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0502":
                st.session_state.is_admin = True
                st.success("관리자 모드")

# ----------------------
# 랭킹
# ----------------------
def load_rank():
    if os.path.exists(RANK_FILE):
        return pd.read_csv(RANK_FILE)
    return pd.DataFrame(columns=["이름","현재포인트","이전포인트"])

# ----------------------
# 1. 랭킹
# ----------------------
if menu == "랭킹":
    st.title("🏆 랭킹")

    df = load_rank()

    if len(df):
        df["변동값"] = df["현재포인트"] - df["이전포인트"]
        df["변동"] = df["변동값"].apply(lambda x: f"⬆ {x}" if x>0 else f"⬇ {abs(x)}" if x<0 else "-")
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df["순위"] = df.index+1
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("랭킹 없음")

# ----------------------
# 2. 참가자
# ----------------------
elif menu == "참가자":
    st.title("👥 참가자")

    if st.session_state.is_admin:
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
    st.write("선택 인원:", len(selected))

# ----------------------
# 그룹 (랭킹 기반 Snake)
# ----------------------
def make_groups(players):
    rank_df = load_rank()
    rank_map = {r["이름"]:r["현재포인트"] for _,r in rank_df.iterrows()}

    players_sorted = sorted(players, key=lambda x: rank_map.get(x,0), reverse=True)

    groups = [[],[]]

    for i,p in enumerate(players_sorted):
        if (i//2)%2==0:
            groups[i%2].append(p)
        else:
            groups[1-(i%2)].append(p)

    return groups

# ----------------------
# 페어 (완벽 랭킹 기반)
# ----------------------
def make_pairs(players):
    sorted_players = players.copy()
    n = len(sorted_players)
    pairs = []
    for i in range(n//2):
        pairs.append((sorted_players[i], sorted_players[n-1-i]))
    return pairs

# ----------------------
# 스케줄 (2코트 + 휴식 보장)
# ----------------------
def make_schedule(players):

    matches = [(players[i], players[j]) for i in range(len(players)) for j in range(i+1,len(players))]
    random.shuffle(matches)

    result=[]
    last_play={p:-10 for p in players}
    r=0

    while matches:
        round_match=[]
        used=set()

        for m in matches[:]:
            a,b=m
            if a in used or b in used:
                continue
            if r-last_play[a]<1 or r-last_play[b]<1:
                continue

            round_match.append(m)
            used.update([a,b])
            last_play[a]=r
            last_play[b]=r
            matches.remove(m)

            if len(round_match)==2:
                break

        if not round_match:
            break

        result.append(round_match)
        r+=1

    return result

# ----------------------
# 3. 대진
# ----------------------
elif menu == "대진":
    st.title("🎮 대진")

    if st.button("그룹 생성"):
        st.session_state.groups = make_groups(st.session_state.players_selected)

    for gi, group in enumerate(st.session_state.groups):
        st.subheader(f"그룹 {gi+1}")

        pairs = make_pairs(group)
        st.write("페어:", pairs)

        schedule = make_schedule(group)
        st.session_state.schedule[gi] = schedule

        for ri, rd in enumerate(schedule):
            st.write(f"라운드 {ri+1}")
            cols = st.columns(2)

            for i,m in enumerate(rd):
                with cols[i]:
                    cls = "card now" if ri == st.session_state.current_round else "card"
                    st.markdown(f"<div class='{cls}'>{m[0]} vs {m[1]}</div>", unsafe_allow_html=True)

    # 경기 진행 버튼
    if st.button("➡ 다음 경기"):
        st.session_state.current_round += 1

# ----------------------
# 4. 결과
# ----------------------
elif menu == "결과":
    st.title("📊 결과")

    for gi, schedule in st.session_state.schedule.items():
        st.subheader(f"그룹 {gi+1}")

        for ri, rd in enumerate(schedule):
            st.write(f"라운드 {ri+1}")
            cols = st.columns(2)

            for i,m in enumerate(rd):
                with cols[i]:
                    a,b=m
                    s1 = st.number_input(a, step=1, key=f"{a}{gi}{ri}")
                    s2 = st.number_input(b, step=1, key=f"{b}{gi}{ri}")
                    st.session_state.scores[(gi,ri,i)] = (s1,s2)

# ----------------------
# 관리자 반영
# ----------------------
if st.session_state.is_admin and st.button("포인트 반영"):

    rank_df = load_rank()
    rank_df["이전포인트"] = rank_df["현재포인트"]

    for name in st.session_state.players_selected:
        pt = random.choice([7,5,3,1])

        if name in rank_df["이름"].values:
            rank_df.loc[rank_df["이름"]==name, "현재포인트"] += pt
        else:
            rank_df = pd.concat([rank_df, pd.DataFrame([[name,pt,0]], columns=["이름","현재포인트","이전포인트"])])

    rank_df.to_csv(RANK_FILE, index=False)

    st.success("랭킹 반영 완료")
