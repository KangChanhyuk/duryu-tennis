import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# 페이지 설정 및 CSS
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 3rem; font-weight: bold; margin-bottom: 20px; }
    .team-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 8px solid #4CAF50;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .team-name { font-size: 1.2rem; font-weight: bold; color: #333; }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #E53935; text-align: center; line-height: 100px; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 데이터 파일 및 상태 관리
# =============================
RANK_FILE = "ranking_master.csv"

if not os.path.exists(RANK_FILE):
    pd.DataFrame(columns=["이름", "현재포인트", "이전포인트"]).to_csv(RANK_FILE, index=False)

def init_state():
    defaults = {
        "players": [], "groups": {}, "modes": {}, "game_counts": {},
        "schedule": {}, "scores": {}, "is_admin": False
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_state()

# =============================
# 핵심 로직 함수
# =============================
def load_rank():
    df = pd.read_csv(RANK_FILE)
    df["현재포인트"] = pd.to_numeric(df["현재포인트"]).fillna(0).astype(int)
    df["이전포인트"] = pd.to_numeric(df["이전포인트"]).fillna(0).astype(int)
    return df

def save_rank(df):
    df["현재포인트"] = df["현재포인트"].astype(int)
    df["이전포인트"] = df["이전포인트"].astype(int)
    df.to_csv(RANK_FILE, index=False)

def team_name(t):
    return " & ".join(t) if len(t) > 1 else t[0]

def make_groups(players, sizes):
    rank = load_rank().sort_values("현재포인트", ascending=False)
    # 랭킹 데이터 기반 정렬 (없는 사람은 뒤로)
    ordered = [p for p in rank["이름"] if p in players] + [p for p in players if p not in rank["이름"].values]
    
    groups = {}
    curr = 0
    for g, s in sizes.items():
        groups[g] = ordered[curr:curr+s]
        curr += s
    return groups

def make_pairs(players, mode):
    temp = players[:]
    if mode == "KDK": random.shuffle(temp) # 랜덤 조 배정
    
    pairs = []
    if mode in ["고정페어", "KDK"]:
        for i in range(0, len(temp)-1, 2): pairs.append((temp[i], temp[i+1]))
        if len(temp) % 2 == 1: pairs.append((temp[-1],))
    else: # 단식
        pairs = [(p,) for p in temp]
    return pairs

def make_schedule(teams, target_games):
    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    
    rounds = []
    while matches:
        curr_round = []
        used_players = set()
        for m in matches[:]:
            if not (set(m[0]) & used_players) and not (set(m[1]) & used_players):
                curr_round.append(m)
                used_players.update(m[0]); used_players.update(m[1])
                matches.remove(m)
        if not curr_round: break
        rounds.append(curr_round)
    return rounds[:target_games] # 그룹별 지정된 게임 수만큼만 생성

# =============================
# UI 메뉴 섹션
# =============================
st.sidebar.title("🎾 두류 테니스")
menu = st.sidebar.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "⚙ 관리자 센터"])

# 1. 랭킹보드 (메인 화면)
if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS RANKING</div>", unsafe_allow_html=True)
    df = load_rank().sort_values("현재포인트", ascending=False).reset_index(drop=True)
    if not df.empty:
        df.insert(0, "순위", df.index + 1)
        st.table(df)
    else:
        st.info("데이터가 없습니다. 관리자 페이지에서 멤버를 등록해주세요.")

# 2. 대진표 및 스코어 입력
elif menu == "📅 대진표/입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    if not st.session_state.schedule:
        st.warning("대진이 없습니다. 관리자 페이지에서 대회를 생성하세요.")
    else:
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                st.info(f"방식: {st.session_state.modes[g]} | 목표: 인당 {st.session_state.game_counts[g]}게임")
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.subheader(f"Round {ri+1}")
                    for i, (t1, t2) in enumerate(rd):
                        c1, c_vs, c2 = st.columns([4, 1, 4])
                        with c1:
                            st.markdown(f"<div class='team-card'><div class='team-name'>{team_name(t1)}</div></div>", unsafe_allow_html=True)
                            s1 = st.number_input("Score", 0, 10, key=f"s1_{g}_{ri}_{i}", label_visibility="collapsed")
                        with c_vs: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"<div class='team-card'><div class='team-name'>{team_name(t2)}</div></div>", unsafe_allow_html=True)
                            s2 = st.number_input("Score", 0, 10, key=f"s2_{g}_{ri}_{i}", label_visibility="collapsed")
                        
                        if st.button(f"저장: {team_name(t1)} vs {team_name(t2)}", key=f"btn_{g}_{ri}_{i}"):
                            st.session_state.scores[(t1, t2)] = (s1, s2)
                            st.toast("결과가 임시 저장되었습니다.")

# 3. 경기 결과 (순위 산출)
elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>MATCH RESULTS</div>", unsafe_allow_html=True)
    if not st.session_state.scores:
        st.info("입력된 결과가 없습니다.")
    else:
        for g in st.session_state.groups.keys():
            st.markdown(f"### Group {g} ({st.session_state.modes[g]})")
            stats = {}
            for (t1, t2), (s1, s2) in st.session_state.scores.items():
                if t1[0] not in st.session_state.groups[g]: continue
                
                for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                    names = [team_name(team)] if st.session_state.modes[g] == "고정페어" else team
                    for n in names:
                        if n not in stats: stats[n] = {"승":0, "패":0, "득점":0, "실점":0}
                        if my_s > op_s: stats[n]["승"] += 1
                        elif my_s < op_s: stats[n]["패"] += 1
                        stats[n]["득점"] += my_s
                        stats[n]["실점"] += op_s
            
            res_df = pd.DataFrame.from_dict(stats, orient='index')
            if not res_df.empty:
                res_df["득실차"] = res_df["득점"] - res_df["실점"]
                res_df = res_df.sort_values(["승", "득실차"], ascending=False)
                res_df.insert(0, "순위", range(1, len(res_df)+1))
                st.table(res_df)

# 4. 관리자 센터
elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    pw = st.text_input("관리자 비밀번호", type="password")
    
    if pw == "0502":
        tab1, tab2, tab3 = st.tabs(["대회 설정/대진생성", "랭킹 데이터 관리", "초기화"])
        
        with tab1:
            st.subheader("🏆 대회 및 그룹 설정")
            raw_p = st.text_area("참가자 명단 (쉼표 구분)", placeholder="홍길동, 김철수, 이영희...")
            g_count = st.number_input("그룹 수", 1, 5, 2)
            
            g_sizes = {}
            for i in range(g_count):
                gn = chr(65+i)
                col1, col2, col3 = st.columns(3)
                with col1: g_sizes[gn] = st.number_input(f"Group {gn} 인원", 2, 40, 4)
                with col2: st.session_state.modes[gn] = st.selectbox(f"Group {gn} 방식", ["KDK", "고정페어", "단식"])
                with col3: st.session_state.game_counts[gn] = st.selectbox(f"Group {gn} 게임수", [3, 4], key=f"gc_{gn}")

            if st.button("대회 생성 및 대진표 배포", type="primary"):
                st.session_state.players = [p.strip() for p in raw_p.split(",") if p.strip()]
                if len(st.session_state.players) < sum(g_sizes.values()):
                    st.error("참가자 수가 그룹 인원 합계보다 적습니다.")
                else:
                    st.session_state.groups = make_groups(st.session_state.players, g_sizes)
                    st.session_state.schedule = {}
                    for g in st.session_state.groups.keys():
                        teams = make_pairs(st.session_state.groups[g], st.session_state.modes[g])
                        st.session_state.schedule[g] = make_schedule(teams, st.session_state.game_counts[g])
                    st.success("그룹별 맞춤 대진 생성이 완료되었습니다!")

        with tab2:
            st.subheader("📁 랭킹 엑셀 업로드")
            up_file = st.file_uploader("랭킹 마스터 파일 업로드 (CSV/XLSX)", type=["csv", "xlsx"])
            if up_file and st.button("파일 적용"):
                df = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
                save_rank(df)
                st.success("랭킹 데이터가 업데이트되었습니다.")
            
            st.divider()
            st.subheader("📈 당일 포인트 반영")
            if st.button("현재 경기 결과 랭킹포인트 반영"):
                rank = load_rank()
                for (t1, t2), (s1, s2) in st.session_state.scores.items():
                    winner = t1 if s1 > s2 else (t2 if s2 > s1 else None)
                    if winner:
                        for p in winner:
                            if p in rank["이름"].values: rank.loc[rank["이름"] == p, "현재포인트"] += 3
                save_rank(rank)
                st.success("포인트가 성공적으로 합산되었습니다.")

        with tab3:
            if st.button("모든 데이터 초기화"):
                st.session_state.clear()
                init_state()
                st.rerun()
