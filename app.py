import streamlit as st
import pandas as pd
import random
import os
import itertools

# =============================
# 설정 및 스타일
# =============================
st.set_page_config(layout="wide", page_title="두류 테니스 클럽")

st.markdown("""
    <style>
    .main-title { text-align: center; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    .sub-title { text-align: center; font-size: 1.5rem; margin-bottom: 10px; }
    .centered-text { text-align: center; }
    .stButton button { display: block; margin: 0 auto; }
    th { background-color: #f0f2f6 !important; text-align: center !important; }
    td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 파일 및 상태 관리
# =============================
RANK_FILE = "ranking_master.csv"
TOUR_FILE = "tournament_list.csv"

for f in [RANK_FILE, TOUR_FILE]:
    if not os.path.exists(f):
        if f == RANK_FILE:
            pd.DataFrame(columns=["이름", "현재포인트", "이전포인트"]).to_csv(f, index=False)
        else:
            pd.DataFrame(columns=["대회명", "날짜", "상태"]).to_csv(f, index=False)

def init_state():
    defaults = {
        "players": [], "groups": {}, "pairs": {}, "schedule": {},
        "scores": {}, "is_admin": False, "selected_tour": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============================
# 로직 함수
# =============================
def load_data(file):
    return pd.read_csv(file)

def save_data(df, file):
    df.to_csv(file, index=False)

def team_name(t):
    return f"{t[0]} & {t[1]}" if len(t) > 1 else t[0]

def make_groups(players, sizes):
    rank = load_data(RANK_FILE).sort_values("현재포인트", ascending=False)
    ordered = [p for p in rank["이름"] if p in players] + [p for p in players if p not in rank["이름"].values]
    groups = {}
    curr = 0
    for g_name, size in sizes.items():
        groups[g_name] = ordered[curr:curr+size]
        curr += size
    return groups

def make_pairs(players, mode):
    if mode == "고정페어":
        return [tuple(players[i:i+2]) for i in range(0, len(players), 2)]
    elif mode == "KDK":
        # KDK 복식 조합: 인원을 섞어서 2명씩 짝지음
        temp = players[:]
        random.shuffle(temp)
        return [tuple(temp[i:i+2]) for i in range(0, len(temp)-1, 2)]
    return [(p,) for p in players]

def make_schedule(teams):
    teams = [tuple(t) for t in teams]
    matches = list(itertools.combinations(teams, 2))
    random.shuffle(matches)
    rounds = []
    while matches:
        used, r = set(), []
        for m in matches[:]:
            if not (set(m[0]) & used) and not (set(m[1]) & used):
                r.append(m); used.update(m[0]); used.update(m[1])
                matches.remove(m)
            if len(r) == 2: break # 2코트 기준
        if not r: break
        rounds.append(r)
    return rounds

# =============================
# 사이드바 메뉴
# =============================
st.sidebar.markdown("<h2 class='centered-text'>🎾 두류 메뉴</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("이동", ["두류랭킹", "대진 및 경기", "경기 결과", "관리자"])

# =============================
# 1. 두류랭킹
# =============================
if menu == "두류랭킹":
    st.markdown("<div class='main-title'>🏆 두류 클럽 통합 랭킹</div>", unsafe_allow_html=True)
    df = load_data(RANK_FILE).sort_values("현재포인트", ascending=False).reset_index(drop=True)
    if not df.empty:
        df.insert(0, "순위", df.index + 1)
        st.table(df)
    else:
        st.warning("데이터가 없습니다.")

# =============================
# 2. 대진 및 경기 (Matrix + Match)
# =============================
elif menu == "대진 및 경기":
    st.markdown("<div class='main-title'>🎾 대진 및 현황</div>", unsafe_allow_html=True)
    if not st.session_state.schedule:
        st.info("관리자 메뉴에서 대진을 생성해주세요.")
    else:
        tabs = st.tabs([f"그룹 {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                # 1. 상단 페어 매트릭스 (사진 1, 2 스타일)
                st.markdown(f"<h3 class='sub-title'>({g}) 그룹 리그전 대진표</h3>", unsafe_allow_html=True)
                teams = st.session_state.pairs[g]
                t_names = [team_name(t) for t in teams]
                matrix_df = pd.DataFrame(":", index=t_names, columns=t_names)
                for (t1, t2), (s1, s2) in st.session_state.scores.items():
                    n1, n2 = team_name(t1), team_name(t2)
                    if n1 in matrix_df.index and n2 in matrix_df.columns:
                        matrix_df.at[n1, n2] = f"{s1}:{s2}"
                        matrix_df.at[n2, n1] = f"{s2}:{s1}"
                st.dataframe(matrix_df, use_container_width=True)

                # 2. 하단 경기 입력 (사진 3 스타일)
                rounds = st.session_state.schedule[g]
                for ri, rd in enumerate(rounds):
                    st.markdown(f"#### 📍 {ri+1} 라운드")
                    cols = st.columns(2)
                    for i, m in enumerate(rd):
                        t1, t2 = m
                        with cols[i]:
                            with st.container(border=True):
                                st.markdown(f"<p class='centered-text'><b>{team_name(t1)}</b> vs <b>{team_name(t2)}</b></p>", unsafe_allow_html=True)
                                s_key = (t1, t2)
                                saved = st.session_state.scores.get(s_key, (0, 0))
                                c1, c2 = st.columns(2)
                                s1 = c1.number_input(f"{t1[0][:2]}.. 점수", 0, 50, int(saved[0]), key=f"s1_{g}_{ri}_{i}")
                                s2 = c2.number_input(f"{t2[0][:2]}.. 점수", 0, 50, int(saved[1]), key=f"s2_{g}_{ri}_{i}")
                                if st.button("결과 저장", key=f"btn_{g}_{ri}_{i}"):
                                    st.session_state.scores[s_key] = (s1, s2)
                                    st.rerun()

# =============================
# 3. 경기 결과
# =============================
elif menu == "경기 결과":
    st.markdown("<div class='main-title'>📊 최종 경기 결과</div>", unsafe_allow_html=True)
    if not st.session_state.scores:
        st.info("기록된 경기 결과가 없습니다.")
    else:
        tabs = st.tabs([f"그룹 {g}" for g in st.session_state.groups.keys()])
        for idx, g in enumerate(st.session_state.groups.keys()):
            with tabs[idx]:
                st.markdown(f"<h3 class='sub-title'>({g}) 그룹 성적 기록</h3>", unsafe_allow_html=True)
                stats = {p: {"승": 0, "패": 0, "득": 0, "실": 0} for p in st.session_state.groups[g]}
                
                for (t1, t2), (s1, s2) in st.session_state.scores.items():
                    # 현재 그룹의 선수들만 필터링
                    if not any(p in st.session_state.groups[g] for p in (list(t1)+list(t2))): continue
                    for p in t1: 
                        stats[p]["득"] += s1; stats[p]["실"] += s2
                        if s1 > s2: stats[p]["승"] += 1
                        elif s1 < s2: stats[p]["패"] += 1
                    for p in t2:
                        stats[p]["득"] += s2; stats[p]["실"] += s1
                        if s2 > s1: stats[p]["승"] += 1
                        elif s2 < s1: stats[p]["패"] += 1
                
                res_df = pd.DataFrame.from_dict(stats, orient='index').reset_index()
                res_df.columns = ["이름", "승", "패", "득점", "실점"]
                res_df["득실차"] = res_df["득점"] - res_df["실점"]
                res_df = res_df.sort_values(by=["승", "득실차"], ascending=False)
                st.table(res_df)

# =============================
# 4. 관리자 (대회 CRUD 포함)
# =============================
elif menu == "관리자":
    st.markdown("<div class='main-title'>⚙ 관리자 컨트롤 타워</div>", unsafe_allow_html=True)
    pw = st.text_input("비밀번호", type="password")
    if pw == "0502":
        st.session_state.is_admin = True
        
        tab_admin = st.tabs(["🏆 대회 관리", "👥 선수 및 그룹 설정", "💾 데이터 초기화"])
        
        with tab_admin[0]:
            st.subheader("대회 생성/수정/삭제")
            t_df = load_data(TOUR_FILE)
            with st.form("new_tour"):
                col1, col2 = st.columns(2)
                new_name = col1.text_input("새 대회 명칭")
                new_date = col2.date_input("대회 날짜")
                if st.form_submit_button("대회 생성"):
                    new_row = pd.DataFrame([{"대회명": new_name, "날짜": str(new_date), "상태": "준비중"}])
                    save_data(pd.concat([t_df, new_row]), TOUR_FILE)
                    st.rerun()
            
            st.write("현재 대회 목록")
            for i, row in t_df.iterrows():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                c1.write(f"**{row['대회명']}**")
                c2.write(row['날짜'])
                if c3.button("선택", key=f"sel_{i}"):
                    st.session_state.selected_tour = row['대회명']
                    st.success(f"{row['대회명']} 선택됨")
                if c4.button("삭제", key=f"del_{i}"):
                    save_data(t_df.drop(i), TOUR_FILE)
                    st.rerun()

        with tab_admin[1]:
            st.subheader("참가자 및 대진 설정")
            raw_p = st.text_area("참가자 명단 (쉼표 구분)", value=", ".join(st.session_state.players))
            if st.button("참가자 저장"):
                st.session_state.players = [p.strip() for p in raw_p.split(",") if p.strip()]
            
            g_cnt = st.number_input("그룹 수", 1, 5, 3)
            g_sizes = {}
            cols = st.columns(g_cnt)
            for i in range(g_cnt):
                g_n = chr(65 + i)
                g_sizes[g_n] = cols[i].number_input(f"그룹 {g_n} 인원", 1, 40, 4)
            
            if st.button("그룹 및 대진 생성", type="primary"):
                st.session_state.groups = make_groups(st.session_state.players, g_sizes)
                st.session_state.pairs = {}
                st.session_state.schedule = {}
                st.session_state.scores = {}
                for g in st.session_state.groups:
                    # 모든 그룹의 방식을 선택하게 하거나 기본 고정페어로 설정
                    st.session_state.pairs[g] = make_pairs(st.session_state.groups[g], "KDK")
                    st.session_state.schedule[g] = make_schedule(st.session_state.pairs[g])
                st.success("대진 생성 완료!")

        with tab_admin[2]:
            if st.button("모든 진행 데이터 리셋"):
                for k in ["players", "groups", "pairs", "schedule", "scores"]:
                    st.session_state[k] = [] if k == "players" else {}
                st.rerun()
