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
    .sub-title { text-align: center; color: #555; margin-bottom: 40px; }
    .team-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 8px solid #4CAF50;
        margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .team-name { font-size: 1.2rem; font-weight: bold; color: #333; overflow: visible; white-space: normal; }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #E53935; text-align: center; line-height: 100px; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 데이터 파일 및 상태 관리
# =============================
RANK_FILE = "ranking_master.csv"
TOURNAMENT_FILE = "tournaments.csv"

if not os.path.exists(RANK_FILE):
    pd.DataFrame(columns=["이름", "현재포인트", "이전포인트"]).to_csv(RANK_FILE, index=False)

def init_state():
    defaults = {
        "players": [], "groups": {}, "pairs": {}, "modes": {}, 
        "schedule": {}, "scores": {}, "is_admin": False,
        "current_tournament": None, "game_count_target": 3
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
    ordered = [p for p in rank["이름"] if p in players] + [p for p in players if p not in rank["이름"].values]
    
    groups = {}
    curr = 0
    for g, s in sizes.items():
        groups[g] = ordered[curr:curr+s]
        curr += s
    return groups

def make_pairs(players, mode):
    temp = players[:]
    if mode == "KDK": random.shuffle(temp)
    
    if mode in ["고정페어", "KDK"]:
        pairs = []
        for i in range(0, len(temp)-1, 2): pairs.append((temp[i], temp[i+1]))
        if len(temp) % 2 == 1: pairs.append((temp[-1],))
        return pairs
    return [(p,) for p in temp]

def make_schedule(teams, target_games):
    # 단순 풀리그 기반에서 타겟 게임 수에 맞춰 조정 (기본 풀리그 후 셔플)
    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    
    rounds = []
    used_matches = []
    # 간단한 라운드 로빈 로직
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
    return rounds[:target_games+1] # 설정된 게임 수에 근접하게 절삭

# =============================
# UI 메뉴 섹션
# =============================
st.sidebar.title("🎾 두류 테니스")
menu = st.sidebar.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "⚙ 관리자 센터"])

# 1. 랭킹보드
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
        st.warning("생성된 대진이 없습니다. 관리자 페이지에서 대회를 먼저 생성하세요.")
    else:
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.subheader(f"Round {ri+1}")
                    for i, (t1, t2) in enumerate(rd):
                        c1, c_vs, c2 = st.columns([4, 1, 4])
                        with c1:
                            st.markdown(f"<div class='team-card'><div class='team-name'>{team_name(t1)}</div></div>", unsafe_allow_html=True)
                            s1 = st.number_input("Score", 0, 10, key=f"s1_{g}_{ri}_{i}", label_visibility="collapsed")
                        with c_vs:
                            st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"<div class='team-card'><div class='team-name'>{team_name(t2)}</div></div>", unsafe_allow_html=True)
                            s2 = st.number_input("Score", 0, 10, key=f"s2_{g}_{ri}_{i}", label_visibility="collapsed")
                        
                        if st.button(f"결과 저장 ({team_name(t1)} vs {team_name(t2)})", key=f"btn_{g}_{ri}_{i}"):
                            st.session_state.scores[(t1, t2)] = (s1, s2)
                            st.toast("경기 결과가 임시 저장되었습니다!")

# 3. 경기 결과 및 당일 순위
elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>TODAY'S RANKING</div>", unsafe_allow_html=True)
    if not st.session_state.scores:
        st.info("진행 중인 경기가 없습니다.")
    else:
        for g in st.session_state.groups.keys():
            st.markdown(f"### Group {g} 결과 ({st.session_state.modes[g]})")
            stats = {}
            for (t1, t2), (s1, s2) in st.session_state.scores.items():
                if t1[0] not in st.session_state.groups[g]: continue
                
                targets = [(t1, s1, s2), (t2, s2, s1)]
                for team, my_s, op_s in targets:
                    if st.session_state.modes[g] == "고정페어":
                        name = team_name(team)
                        if name not in stats: stats[name] = {"승":0, "패":0, "득점":0, "실점":0}
                        if my_s > op_s: stats[name]["승"] += 1
                        elif my_s < op_s: stats[name]["패"] += 1
                        stats[name]["득점"] += my_s
                        stats[name]["실점"] += op_s
                    else:
                        for p in team:
                            if p not in stats: stats[p] = {"승":0, "패":0, "득점":0, "실점":0}
                            if my_s > op_s: stats[p]["승"] += 1
                            elif my_s < op_s: stats[p]["패"] += 1
                            stats[p]["득점"] += my_s
                            stats[p]["실점"] += op_s
            
            res_df = pd.DataFrame.from_dict(stats, orient='index')
            res_df["득실차"] = res_df["득점"] - res_df["실점"]
            res_df = res_df.sort_values(["승", "득실차"], ascending=False)
            res_df.insert(0, "순위", range(1, len(res_df)+1))
            st.table(res_df)

# 4. 관리자 센터
elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    pw = st.text_input("관리자 비밀번호", type="password")
    
    if pw == "0502":
        tab1, tab2, tab3 = st.tabs(["대회 생성/관리", "멤버/랭킹 관리", "데이터 초기화"])
        
        with tab1:
            st.subheader("🏆 월간 대회 아카이브")
            t_name = st.text_input("대회 제목 (예: 2026년 5월 정기대회)")
            t_game_cnt = st.radio("1인당 기준 경기 수", [3, 4], index=0)
            
            col_a, col_b = st.columns(2)
            with col_a:
                raw_p = st.text_area("참가자 명단 (쉼표 구분)")
            with col_b:
                g_count = st.number_input("그룹 수", 1, 5, 2)
                g_sizes = {chr(65+i): st.number_input(f"Group {chr(65+i)} 인원", 2, 20, 4) for i in range(g_count)}

            if st.button("대회 생성 및 대진 확정"):
                st.session_state.players = [p.strip() for p in raw_p.split(",") if p.strip()]
                st.session_state.groups = make_groups(st.session_state.players, g_sizes)
                st.session_state.game_count_target = t_game_cnt
                st.success(f"'{t_name}' 대회가 생성되었습니다. 그룹별 방식을 설정하세요.")

            if st.session_state.groups:
                st.divider()
                for g in st.session_state.groups.keys():
                    st.session_state.modes[g] = st.selectbox(f"Group {g} 방식", ["KDK", "고정페어", "단식"], key=f"m_{g}")
                
                if st.button("최종 대진표 배포", type="primary"):
                    for g in st.session_state.groups.keys():
                        teams = make_pairs(st.session_state.groups[g], st.session_state.modes[g])
                        st.session_state.schedule[g] = make_schedule(teams, st.session_state.game_count_target)
                    st.success("대진표가 생성되었습니다! '대진표/입력' 메뉴를 확인하세요.")

        with tab2:
            st.subheader("📈 랭킹 포인트 반영")
            if st.button("당일 경기 결과 랭킹에 합산하기"):
                rank = load_rank()
                # 승리당 3점, 참가당 1점 로직 예시
                for (t1, t2), (s1, s2) in st.session_state.scores.items():
                    winner = t1 if s1 > s2 else (t2 if s2 > s1 else None)
                    if winner:
                        for p in winner:
                            if p in rank["이름"].values: rank.loc[rank["이름"] == p, "현재포인트"] += 3
                save_rank(rank)
                st.success("랭킹에 포인트가 정수로 반영되었습니다.")

        with tab3:
            if st.button("모든 대회 및 점수 데이터 초기화"):
                st.session_state.clear()
                init_state()
                st.rerun()
