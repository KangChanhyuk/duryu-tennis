import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime
import itertools

# =============================
# 페이지 설정 및 CSS
# =============================
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 3rem; font-weight: bold; margin-bottom: 20px; }
    .team-card { border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; }
    .match-bg-1 { background-color: #f1f8e9; border-left: 8px solid #4CAF50; }
    .match-bg-2 { background-color: #e3f2fd; border-left: 8px solid #2196F3; }
    .pair-matrix { background-color: #ffffff; border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin-bottom: 20px; }
    .team-name { font-size: 1.2rem; font-weight: bold; color: #333; text-align: center; }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #E53935; text-align: center; line-height: 80px; }
    input { text-align: center !important; }
    .stButton>button { width: 100%; border-radius: 5px; }
    .stDataFrame, .stTable, [data-testid="stTable"] { display: flex; justify-content: center; text-align: center !important; }
    th, td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 데이터 파일 및 상태 관리
# =============================
RANK_FILE = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"

def init_state():
    defaults = {
        "players": [], "groups": {}, "modes": {}, "game_counts": {},
        "schedule": {}, "scores": {}, "current_date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tournament_name": "정기 대회",
        "group_pairs": {} # 페어 정보 저장용
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_state()

# =============================
# 핵심 로직 함수
# =============================
def load_rank():
    if not os.path.exists(RANK_FILE):
        return pd.DataFrame(columns=["이름", "현재포인트"])
    df = pd.read_csv(RANK_FILE)
    if "현재포인트" in df.columns:
        df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors='coerce').fillna(0).astype(int)
    return df

def save_rank(df):
    if "현재포인트" in df.columns:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
    df.to_csv(RANK_FILE, index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return pd.DataFrame(columns=["날짜", "대회명", "그룹", "방식", "이름", "순위", "승", "득실"])
    return pd.read_csv(HISTORY_FILE)

def team_name(t, p_list=None):
    if isinstance(t, (list, tuple)):
        names = []
        for p in t:
            prefix = f"({p_list.index(p)+1})" if p_list and p in p_list else ""
            names.append(f"{prefix}{p}")
        return " & ".join(names)
    return str(t)

def process_uploaded_file(df):
    df.columns = [str(c).strip() for c in df.columns]
    name_col = next((c for c in df.columns if any(kw in c.lower() for kw in ['이름', '성함', 'name'])), None)
    point_col = next((c for c in df.columns if any(kw in c.lower() for kw in ['현재', '포인트', '점수'])), None)
    if not name_col: return None
    new_df = pd.DataFrame()
    new_df['이름'] = df[name_col].astype(str)
    new_df['현재포인트'] = pd.to_numeric(df[point_col], errors='coerce').fillna(0).astype(int) if point_col else 0
    return new_df.sort_values("현재포인트", ascending=False).reset_index(drop=True)

# =============================
# 그룹 편성 및 대진 로직 (스네이크 매칭 적용)
# =============================
def make_groups_by_rank(players, sizes):
    rank_df = load_rank()
    rank_dict = dict(zip(rank_df['이름'], rank_df['현재포인트'])) if not rank_df.empty else {}
    ordered = sorted(players, key=lambda x: rank_dict.get(x, 0), reverse=True)
    groups = {}
    curr = 0
    for g, s in sizes.items():
        groups[g] = ordered[curr:curr+s]
        curr += s
    return groups

def make_balanced_pairs(group_players):
    """ 고정페어 스네이크 매칭 (1위-8위, 2위-7위...)"""
    pairs = []
    n = len(group_players)
    for i in range(n // 2):
        pairs.append([group_players[i], group_players[n - 1 - i]])
    if n % 2 == 1:
        pairs.append([group_players[n // 2]])
    return pairs

def make_kdk_schedule_v2(players, target_games_per_person):
    """백트래킹 방식의 균등 경기 수 로직"""
    max_attempts = 50
    for _ in range(max_attempts):
        player_counts = {p: 0 for p in players}
        partner_counts = {tuple(sorted(pair)): 0 for pair in itertools.combinations(players, 2)}
        all_rounds = []
        
        # 1인당 정확한 경기 수를 위해 충분히 시도
        for _ in range(target_games_per_person * 3):
            round_matches = []
            used_in_round = set()
            candidates = [p for p in players if player_counts[p] < target_games_per_person]
            random.shuffle(candidates)
            
            while len(candidates) >= 4:
                p1 = candidates.pop(0)
                # 파트너 선택
                rem = sorted(candidates, key=lambda x: partner_counts.get(tuple(sorted((p1, x))), 0))
                p2 = rem[0]; candidates.remove(p2)
                # 상대팀 선택
                p3 = candidates.pop(0)
                rem2 = sorted(candidates, key=lambda x: partner_counts.get(tuple(sorted((p3, x))), 0))
                p4 = rem2[0]; candidates.remove(p4)
                
                round_matches.append([[p1, p2], [p3, p4]])
                player_counts[p1]+=1; player_counts[p2]+=1; player_counts[p3]+=1; player_counts[p4]+=1
                partner_counts[tuple(sorted((p1, p2)))] += 1
                partner_counts[tuple(sorted((p3, p4)))] += 1
                
            if round_matches: all_rounds.append(round_matches)
            if all(c >= target_games_per_person for c in player_counts.values()):
                return all_rounds
    return []

def make_round_robin(teams, target_games):
    """리그전 형식 대진표"""
    matches = [[teams[i], teams[j]] for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    team_counts = {tuple(t): 0 for t in teams}
    final_matches = []
    for m in matches:
        t1, t2 = tuple(m[0]), tuple(m[1])
        if team_counts[t1] < target_games and team_counts[t2] < target_games:
            final_matches.append(m)
            team_counts[t1] += 1; team_counts[t2] += 1
            
    rounds = []
    while final_matches:
        curr_round = []; used = set()
        for m in final_matches[:]:
            p_set = set(m[0]) | set(m[1])
            if not (p_set & used):
                curr_round.append(m); used.update(p_set); final_matches.remove(m)
        if not curr_round: break
        rounds.append(curr_round)
    return rounds

# =============================
# UI 메뉴 섹션
# =============================
st.sidebar.title("🎾 두류 테니스")
menu = st.sidebar.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "📜 지난 대회 기록", "⚙ 관리자 센터"])

if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS RANKING</div>", unsafe_allow_html=True)
    df = load_rank()
    if not df.empty:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df.insert(0, "순위", range(1, len(df)+1))
        st.table(df[["순위", "이름", "현재포인트"]])
    else: st.info("관리자 센터에서 랭킹 데이터를 등록해주세요.")

elif menu == "📅 대진표/입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    if not st.session_state.schedule:
        st.warning("대진이 없습니다. 관리자 페이지에서 대회를 생성하세요.")
    else:
        st.info(f"🏟 대회명: {st.session_state.tournament_name} | 기준일: {st.session_state.current_date}")
        all_rank_players = load_rank()['이름'].tolist() if not load_rank().empty else []
        full_selection_list = sorted(list(set(st.session_state.players + all_rank_players)))
        
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                # [페어 정보 매트릭스 표시]
                if g in st.session_state.group_pairs and st.session_state.modes[g] == "고정페어":
                    st.markdown("##### 🤝 그룹 페어 구성 (스네이크 매칭)")
                    pairs_data = []
                    for i, p in enumerate(st.session_state.group_pairs[g]):
                        pairs_data.append({"No": i+1, "페어 명단": " & ".join(p)})
                    st.table(pd.DataFrame(pairs_data))

                p_list = st.session_state.groups[g]
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.markdown(f"<h4 style='text-align: center; background:#eee; padding:5px;'>Round {ri+1}</h4>", unsafe_allow_html=True)
                    # rd가 비어있거나 형식이 맞지 않는 경우 방지
                    if not rd or not isinstance(rd, list): continue
                    
                    for mi, match in enumerate(rd):
                        if len(match) != 2: continue # 안전장치
                        t1, t2 = match
                        bg_class = "match-bg-1" if mi % 2 == 0 else "match-bg-2"
                        with st.container():
                            c1, c_vs, c2 = st.columns([4, 1, 4])
                            with c1:
                                st.markdown(f"<div class='team-card {bg_class}'><div class='team-name'>{team_name(t1, p_list)}</div></div>", unsafe_allow_html=True)
                                with st.expander("교체"):
                                    for pi, p_name in enumerate(t1):
                                        sel = st.selectbox(f"({p_name})", ["선택안함"]+full_selection_list+["🆕 직접"], key=f"s_{g}_{ri}_{mi}_t1_{pi}")
                                        if sel == "🆕 직접":
                                            n = st.text_input("이름", key=f"x_{g}_{ri}_{mi}_t1_{pi}")
                                            if st.button("적용", key=f"b_{g}_{ri}_{mi}_t1_{pi}"):
                                                st.session_state.schedule[g][ri][mi][0][pi] = n.strip(); st.rerun()
                                        elif sel != "선택안함":
                                            st.session_state.schedule[g][ri][mi][0][pi] = sel; st.rerun()
                                s1 = st.number_input("Score", 0, 10, key=f"s1_{g}_{ri}_{mi}", label_visibility="collapsed")
                            with c_vs: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<div class='team-card {bg_class}'><div class='team-name'>{team_name(t2, p_list)}</div></div>", unsafe_allow_html=True)
                                with st.expander("교체"):
                                    for pi, p_name in enumerate(t2):
                                        sel = st.selectbox(f"({p_name})", ["선택안함"]+full_selection_list+["🆕 직접"], key=f"s_{g}_{ri}_{mi}_t2_{pi}")
                                        if sel == "🆕 직접":
                                            n = st.text_input("이름", key=f"x_{g}_{ri}_{mi}_t2_{pi}")
                                            if st.button("적용", key=f"b_{g}_{ri}_{mi}_t2_{pi}"):
                                                st.session_state.schedule[g][ri][mi][1][pi] = n.strip(); st.rerun()
                                        elif sel != "선택안함":
                                            st.session_state.schedule[g][ri][mi][1][pi] = sel; st.rerun()
                                s2 = st.number_input("Score", 0, 10, key=f"s2_{g}_{ri}_{mi}", label_visibility="collapsed")
                            if st.button(f"저장 ({mi+1}번 경기)", key=f"btn_{g}_{ri}_{mi}"):
                                st.session_state.scores[(g, ri, mi)] = {"teams": (tuple(t1), tuple(t2)), "score": (s1, s2)}
                                st.success("저장 완료")
                        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>MATCH RESULTS</div>", unsafe_allow_html=True)
    if not st.session_state.scores: st.info("입력된 결과가 없습니다.")
    else:
        for g in st.session_state.groups.keys():
            st.markdown(f"<h3 style='text-align: center;'>Group {g} 순위</h3>", unsafe_allow_html=True)
            stats = {}
            group_scores = {k: v for k, v in st.session_state.scores.items() if k[0] == g}
            for key, data in group_scores.items():
                t1, t2 = data["teams"]; s1, s2 = data["score"]
                for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                    for n in team:
                        if n not in stats: stats[n] = {"승":0, "패":0, "득실":0, "경기":0}
                        stats[n]["경기"] += 1
                        if my_s > op_s: stats[n]["승"] += 1
                        elif my_s < op_s: stats[n]["패"] += 1
                        stats[n]["득실"] += (my_s - op_s)
            if stats:
                res_df = pd.DataFrame.from_dict(stats, orient='index').sort_values(["승", "득실"], ascending=False)
                res_df.insert(0, "순위", range(1, len(res_df)+1))
                st.table(res_df)

elif menu == "📜 지난 대회 기록":
    st.markdown("<div class='main-title'>PAST RECORDS</div>", unsafe_allow_html=True)
    history = load_history()
    if history.empty: st.info("기록이 없습니다.")
    else:
        history['선택정보'] = history['날짜'] + " [" + history['대회명'] + "]"
        unique_tours = history['선택정보'].unique()[::-1]
        selected = st.selectbox("기록 선택", unique_tours)
        st.table(history[history['선택정보'] == selected].drop(columns=['선택정보']))

elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    if st.text_input("비밀번호", type="password") == "0502":
        tab1, tab2, tab3, tab4 = st.tabs(["대회 생성", "랭킹 관리", "기록 삭제", "초기화"])
        with tab1:
            st.session_state.tournament_name = st.text_input("대회명", st.session_state.tournament_name)
            raw_p = st.text_area("명단 (쉼표 구분)")
            g_count = st.number_input("그룹수", 1, 10, 2)
            g_sizes = {}
            for i in range(int(g_count)):
                gn = chr(65+i); c1, c2, c3 = st.columns(3)
                with c1: g_sizes[gn] = st.number_input(f"G {gn} 인원", 2, 100, 8)
                with c2: st.session_state.modes[gn] = st.selectbox(f"방식 {gn}", ["고정페어", "KDK", "단식"], key=f"m_{gn}")
                with c3: st.session_state.game_counts[gn] = st.selectbox(f"경기수 {gn}", [3,4,5,6], index=1, key=f"gc_{gn}")
            
            if st.button("대회 생성 (랭킹순 배정)", type="primary"):
                p_list = [p.strip() for p in raw_p.split(",") if p.strip()]
                if len(p_list) >= sum(g_sizes.values()):
                    st.session_state.players = p_list
                    st.session_state.groups = make_groups_by_rank(p_list, g_sizes)
                    st.session_state.current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.scores = {}; st.session_state.schedule = {}
                    st.session_state.group_pairs = {}
                    
                    for g in st.session_state.groups.keys():
                        gp = st.session_state.groups[g]; mode = st.session_state.modes[g]; tg = st.session_state.game_counts[g]
                        if mode == "KDK": st.session_state.schedule[g] = make_kdk_schedule_v2(gp, tg)
                        elif mode == "고정페어":
                            pairs = make_balanced_pairs(gp)
                            st.session_state.group_pairs[g] = pairs # 페어 정보 저장
                            st.session_state.schedule[g] = make_round_robin(pairs, tg)
                        else: st.session_state.schedule[g] = make_round_robin([[p] for p in gp], tg)
                    st.success("대회 생성 완료!"); st.rerun()
        
        with tab2:
            st.subheader("📁 랭킹 업로드")
            up_file = st.file_uploader("CSV/XLSX", type=["csv", "xlsx"])
            if up_file:
                df_raw = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
                df_p = process_uploaded_file(df_raw)
                if df_p is not None:
                    st.table(df_p.head(5))
                    if st.button("랭킹 저장"): save_rank(df_p); st.success("저장 완료")
            
            st.divider()
            if st.button("결과 최종 확정 (랭킹 반영)", type="primary"):
                rank = load_rank(); history_data = []
                for g, g_players in st.session_state.groups.items():
                    stats = {}
                    g_res = {k: v for k, v in st.session_state.scores.items() if k[0] == g}
                    for k, d in g_res.items():
                        t1, t2 = d["teams"]; s1, s2 = d["score"]
                        for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                            for n in team:
                                if n not in stats: stats[n] = {"승":0, "득실":0}
                                if my_s > op_s: stats[n]["승"] += 1
                                stats[n]["득실"] += (my_s - op_s)
                    
                    sort_p = sorted(stats.items(), key=lambda x: (x[1]['승'], x[1]['득실']), reverse=True)
                    for idx, (p_name, s_vals) in enumerate(sort_p):
                        rank_pos = idx + 1
                        pts = 7 if rank_pos <= 2 else (5 if rank_pos <= 4 else (3 if rank_pos <= 6 else 1))
                        if p_name in rank["이름"].values: rank.loc[rank["이름"] == p_name, "현재포인트"] += pts
                        else: rank = pd.concat([rank, pd.DataFrame({"이름":[p_name],"현재포인트":[pts]})], ignore_index=True)
                        history_data.append({"날짜": st.session_state.current_date, "대회명": st.session_state.tournament_name, "그룹": g, "방식": st.session_state.modes[g], "이름": p_name, "순위": f"{rank_pos}위", "승": s_vals["승"], "득실": s_vals["득실"]})
                save_rank(rank)
                pd.concat([load_history(), pd.DataFrame(history_data)], ignore_index=True).to_csv(HISTORY_FILE, index=False)
                st.success("랭킹 반영 완료!")

        with tab3:
            h = load_history()
            if not h.empty:
                h['선택'] = h['날짜'] + " [" + h['대회명'] + "]"
                target = st.selectbox("삭제 대회", h['선택'].unique()[::-1])
                if st.button("기록 삭제"):
                    h[h['선택'] != target].drop(columns=['선택']).to_csv(HISTORY_FILE, index=False)
                    st.rerun()

        with tab4:
            if st.button("시스템 전체 초기화"):
                for f in [RANK_FILE, HISTORY_FILE]:
                    if os.path.exists(f): os.remove(f)
                st.session_state.clear(); st.rerun()
