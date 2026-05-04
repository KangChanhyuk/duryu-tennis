import streamlit as st
import pandas as pd
import random
import os

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"

# ----------------------
# 상태 초기화
# ----------------------
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "players_all" not in st.session_state:
    st.session_state.players_all = []
if "players_selected" not in st.session_state:
    st.session_state.players_selected = []
if "groups" not in st.session_state:
    st.session_state.groups = []
if "schedule" not in st.session_state:
    st.session_state.schedule = {}
if "scores" not in st.session_state:
    st.session_state.scores = {}
if "result_df" not in st.session_state:
    st.session_state.result_df = None
if "match_type" not in st.session_state:
    st.session_state.match_type = "단식"

# ----------------------
# UI 스타일
# ----------------------
st.markdown("""
<style>
button {height:50px;font-size:16px;border-radius:10px;}
.card {padding:12px;margin:6px;background:#f5f5f5;border-radius:10px;text-align:center;}
</style>
""", unsafe_allow_html=True)

# ----------------------
# 사이드바
# ----------------------
with st.sidebar:
    st.title("🎾 두류테니스")

    menu = st.radio("메뉴 선택", [
        "랭킹",
        "참가자",
        "대진",
        "결과",
        "관리자"
    ])

    if menu == "관리자":
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0502":
                st.session_state.is_admin = True
                st.success("관리자 로그인 완료")
            else:
                st.error("비밀번호 오류")

# ----------------------
# 랭킹 로드
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

    if len(df) > 0:
        df["변동"] = df["현재포인트"] - df["이전포인트"]

        def arrow(x):
            if x > 0: return f"⬆ {x}"
            elif x < 0: return f"⬇ {abs(x)}"
            else: return "-"

        df["변동"] = df["변동"].apply(arrow)

        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df["순위"] = df.index + 1

        st.dataframe(df, use_container_width=True)
    else:
        st.warning("랭킹 데이터 없음")

# ----------------------
# 2. 참가자
# ----------------------
elif menu == "참가자":

    st.title("👥 참가자")

    if st.session_state.is_admin:
        raw = st.text_area("참가자 입력 (쉼표)")
        if st.button("등록"):
            st.session_state.players_all = [p.strip() for p in raw.split(",") if p.strip()]

    selected = []
    cols = st.columns(4)

    for i, p in enumerate(st.session_state.players_all):
        with cols[i % 4]:
            if st.checkbox(p, value=True):
                selected.append(p)

    if st.button("전체 선택"):
        selected = st.session_state.players_all.copy()

    st.session_state.players_selected = selected
    st.write("선택 인원:", len(selected))

# ----------------------
# 그룹 생성
# ----------------------
def make_groups(players):
    rank_df = load_rank()
    rank_map = {row["이름"]: row["현재포인트"] for _, row in rank_df.iterrows()}

    players_sorted = sorted(players, key=lambda x: rank_map.get(x,0), reverse=True)

    groups = [[],[]]

    for i, p in enumerate(players_sorted):
        groups[i % 2].append(p)

    return groups

# ----------------------
# 페어 생성
# ----------------------
def make_pairs(players, mode):
    pairs = []

    if mode == "고정페어":
        n = len(players)
        for i in range(n//2):
            pairs.append((players[i], players[n-1-i]))

    elif mode == "KDK":
        temp = players.copy()
        random.shuffle(temp)
        for i in range(0, len(temp), 2):
            if i+1 < len(temp):
                pairs.append((temp[i], temp[i+1]))

    return pairs

# ----------------------
# 스케줄 생성
# ----------------------
def make_schedule(players, mode):

    if mode == "단식":
        matches = [(players[i], players[j]) for i in range(len(players)) for j in range(i+1, len(players))]
    else:
        pairs = make_pairs(players, mode)
        matches = [(pairs[i], pairs[j]) for i in range(len(pairs)) for j in range(i+1, len(pairs))]

    random.shuffle(matches)

    result = []

    while matches:
        round_match=[]
        used=set()

        for m in matches[:]:
            people = m if mode=="단식" else m[0]+m[1]

            if any(p in used for p in people):
                continue

            round_match.append(m)
            used.update(people)
            matches.remove(m)

            if len(round_match)==2:
                break

        if not round_match:
            break

        result.append(round_match)

    return result

# ----------------------
# 3. 대진
# ----------------------
elif menu == "대진":

    st.title("🎮 대진")

    st.session_state.match_type = st.radio("경기 방식", ["단식","고정페어","KDK"])

    if st.button("그룹 생성"):
        st.session_state.groups = make_groups(st.session_state.players_selected)

    for gi, group in enumerate(st.session_state.groups):
        st.subheader(f"그룹 {gi+1}")

        schedule = make_schedule(group, st.session_state.match_type)
        st.session_state.schedule[gi] = schedule

        for ri, rd in enumerate(schedule):
            st.write(f"라운드 {ri+1}")
            cols = st.columns(2)

            for i, m in enumerate(rd):
                with cols[i]:
                    if st.session_state.match_type == "단식":
                        txt = f"{m[0]} vs {m[1]}"
                    else:
                        txt = f"{m[0][0]}/{m[0][1]} vs {m[1][0]}/{m[1][1]}"
                    st.markdown(f"<div class='card'>{txt}</div>", unsafe_allow_html=True)

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

            for i, m in enumerate(rd):
                with cols[i]:
                    if st.session_state.match_type == "단식":
                        a,b = m
                        s1 = st.number_input(a, step=1, key=f"{a}{gi}{ri}")
                        s2 = st.number_input(b, step=1, key=f"{b}{gi}{ri}")
                    else:
                        t1 = f"{m[0][0]}/{m[0][1]}"
                        t2 = f"{m[1][0]}/{m[1][1]}"
                        s1 = st.number_input(t1, step=1, key=f"{t1}{gi}{ri}")
                        s2 = st.number_input(t2, step=1, key=f"{t2}{gi}{ri}")

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
            new = pd.DataFrame([[name, pt, 0]], columns=["이름","현재포인트","이전포인트"])
            rank_df = pd.concat([rank_df,new], ignore_index=True)

    rank_df.to_csv(RANK_FILE, index=False)

    st.success("랭킹 반영 완료")
