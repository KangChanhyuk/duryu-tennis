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
        "tournament_name": "정기 대회"
    }
    for k, v in defaults.items():
        if k not in st.session_state: st.session_state[k] = v

init_state()

# =============================
# 핵심 로직 함수 (데이터 핸들링)
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
            # p_list 내의 인덱스를 기반으로 번호 부여
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
# 그룹 편성 및 대진 로직 (강화된 알고리즘)
# =============================

def make_groups_by_rank(players, sizes):
    """참가자를 랭킹순으로 정렬한 뒤 그룹별로 순차 배정"""
    rank_df = load_rank()
    rank_dict = dict(zip(rank_df['이름'], rank_df['현재포인트'])) if not rank_df.empty else {}
    
    # 랭킹 점수 기준 정렬 (랭킹에 없으면 0점)
    ordered = sorted(players, key=lambda x: rank_dict.get(x, 0), reverse=True)
    
    groups = {}
    curr = 0
    for g, s in sizes.items():
        groups[g] = ordered[curr:curr+s]
        curr += s
    return groups

def make_balanced_pairs(group_players):
    """고정페어: 1위-8위, 2위-7위... 형태로 실력 균형을 맞춰 페어 구성"""
    # group_players는 이미 랭킹순으로 정렬되어 있음
    pairs = []
    n = len(group_players)
    for i in range(n // 2):
        pairs.append([group_players[i], group_players[n - 1 - i]])
    
    # 인원이 홀수인 경우 중간 사람 한 명 남음
    if n % 2 == 1:
        pairs.append([group_players[n // 2]])
    return pairs

def make_kdk_schedule_v2(players, target_games_per_person):
    """
    KDK 로직: 모든 인원이 target_games_per_person만큼 정확히 경기를 뛰도록 보장.
    백트래킹 스타일의 최적화 시도.
    """
    max_attempts = 100
    for attempt in range(max_attempts):
        schedule = []
        player_counts = {p: 0 for p in players}
        # 파트너십 기록 (중복 방지용)
        partner_counts = {tuple(sorted(pair)): 0 for pair in itertools.combinations(players, 2)}
        
        rounds = []
        success = True
        
        # 1인당 경기 수 달성을 위한 반복
        for r in range(target_games_per_person * 2): # 안전을 위해 충분한 라운드 생성 시도
            round_matches = []
            used_in_round = set()
            
            # 이 라운드에서 뛸 수 있는 사람 (아직 목표 미달성 + 라운드 미사용)
            candidates = [p for p in players if player_counts[p] < target_games_per_person]
            random.shuffle(candidates)
            
            while len(candidates) >= 4:
                p1 = candidates.pop(0)
                # 파트너 선택 (가장 적게 파트너를 했던 사람 중 선택)
                remaining_candidates = [c for c in candidates]
                remaining_candidates.sort(key=lambda x: partner_counts.get(tuple(sorted((p1, x))), 0))
                
                p2 = remaining_candidates.pop(0)
                candidates.remove(p2)
                
                # 상대팀
                p3 = candidates.pop(0)
                remaining_candidates2 = [c for c in candidates]
                remaining_candidates2.sort(key=lambda x: partner_counts.get(tuple(sorted((p3, x))), 0))
                
                p4 = remaining_candidates2.pop(0)
                candidates.remove(p4)
                
                # 매치 추가
                match = [[p1, p2], [p3, p4]]
                round_matches.append(match)
                
                player_counts[p1] += 1; player_counts[p2] += 1
                player_counts[p3] += 1; player_counts[p4] += 1
                partner_counts[tuple(sorted((p1, p2)))] += 1
                partner_counts[tuple(sorted((p3, p4)))] += 1
                
            if round_matches:
                rounds.append(round_matches)
            
            if all(c >= target_games_per_person for c in player_counts.values()):
                return rounds
                
    return [["로직 구성 실패 - 인원/경기수 조정 필요"]]

def make_round_robin(teams, target_games):
    """리그전 형식의 대진표 생성 (고정페어/단식용)"""
    matches = [[teams[i], teams[j]] for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    
    # 1인당 경기 수 제한 로직 (단순 리그전에서 발췌)
    team_counts = {tuple(t): 0 for t in teams}
    final_matches = []
    
    for m in matches:
        t1, t2 = tuple(m[0]), tuple(m[1])
        if team_counts[t1] < target_games and team_counts[t2] < target_games:
            final_matches.append(m)
            team_counts[t1] += 1
            team_counts[t2] += 1
            
    # 라운드 배분
    rounds = []
    while final_matches:
        curr_round = []
        used_in_round = set()
        for m in final_matches[:]:
            p_in_match = set()
            for p in m[0]: p_in_match.add(p)
            for p in m[1]: p_in_match.add(p)
            
            if not (p_in_match & used_in_round):
                curr_round.append(m)
                used_in_round.update(p_in_match)
                final_matches.remove(m)
        if not curr_round: break
        rounds.append(curr_round)
        
    return rounds

# =============================
# UI 메뉴 섹션
# =============================
st.sidebar.title("🎾 두류 테니스")
menu = st.sidebar.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "📜 지난 대회 기록", "⚙ 관리자 센터"])

# [1] 랭킹보드
if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>DU-RYU TENNIS RANKING</div>", unsafe_allow_html=True)
    df = load_rank()
    if not df.empty:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df.insert(0, "순위", range(1, len(df)+1))
        st.table(df[["순위", "이름", "현재포인트"]])
    else: st.info("데이터가 없습니다. 관리자 센터에서 랭킹 데이터를 업로드해주세요.")

# [2] 대진표 및 점수 입력
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
                p_list = st.session_state.groups[g] # 번호 표시용 원본 리스트
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.markdown(f"<h4 style='text-align: center; background:#eee; padding:5px;'>Round {ri+1}</h4>", unsafe_allow_html=True)
                    for mi, (t1, t2) in enumerate(rd):
                        bg_class = "match-bg-1" if mi % 2 == 0 else "match-bg-2"
                        with st.container():
                            c1, c_vs, c2 = st.columns([4, 1, 4])
                            with c1:
                                st.markdown(f"<div class='team-card {bg_class}'><div class='team-name'>{team_name(t1, p_list)}</div></div>", unsafe_allow_html=True)
                                with st.expander("선수 교체"):
                                    for pi, p_name in enumerate(t1):
                                        options = ["선택안함"] + full_selection_list + ["🆕 직접 입력"]
                                        sel = st.selectbox(f"교체 ({p_name})", options, key=f"sel_{g}_{ri}_{mi}_t1_{pi}")
                                        if sel == "🆕 직접 입력":
                                            new_name = st.text_input("이름 입력", key=f"txt_{g}_{ri}_{mi}_t1_{pi}")
                                            if st.button("확인", key=f"btn_ok_{g}_{ri}_{mi}_t1_{pi}") and new_name:
                                                st.session_state.schedule[g][ri][mi][0][pi] = new_name.strip(); st.rerun()
                                        elif sel != "선택안함":
                                            st.session_state.schedule[g][ri][mi][0][pi] = sel; st.rerun()
                                s1 = st.number_input("Score", 0, 10, key=f"s1_{g}_{ri}_{mi}", label_visibility="collapsed")
                            with c_vs: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<div class='team-card {bg_class}'><div class='team-name'>{team_name(t2, p_list)}</div></div>", unsafe_allow_html=True)
                                with st.expander("선수 교체"):
                                    for pi, p_name in enumerate(t2):
                                        options = ["선택안함"] + full_selection_list + ["🆕 직접 입력"]
                                        sel = st.selectbox(f"교체 ({p_name})", options, key=f"sel_{g}_{ri}_{mi}_t2_{pi}")
                                        if sel == "🆕 직접 입력":
                                            new_name = st.text_input("이름 입력", key=f"txt_{g}_{ri}_{mi}_t2_{pi}")
                                            if st.button("확인", key=f"btn_ok_{g}_{ri}_{mi}_t2_{pi}") and new_name:
                                                st.session_state.schedule[g][ri][mi][1][pi] = new_name.strip(); st.rerun()
                                        elif sel != "선택안함":
                                            st.session_state.schedule[g][ri][mi][1][pi] = sel; st.rerun()
                                s2 = st.number_input("Score", 0, 10, key=f"s2_{g}_{ri}_{mi}", label_visibility="collapsed")
                            if st.button(f"결과 저장: {mi+1}번 경기", key=f"btn_{g}_{ri}_{mi}"):
                                st.session_state.scores[(g, ri, mi)] = {"teams": (tuple(t1), tuple(t2)), "score": (s1, s2)}
                                st.success("저장되었습니다!")
                        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

# [3] 경기결과 집계
elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>MATCH RESULTS</div>", unsafe_allow_html=True)
    if not st.session_state.scores: st.info("입력된 결과가 없습니다.")
    else:
        for g in st.session_state.groups.keys():
            st.markdown(f"<h3 style='text-align: center;'>Group {g} 실시간 순위</h3>", unsafe_allow_html=True)
            stats = {}
            # 해당 그룹의 점수만 필터링
            group_scores = {k: v for k, v in st.session_state.scores.items() if k[0] == g}
            
            for key, data in group_scores.items():
                t1, t2 = data["teams"]
                s1, s2 = data["score"]
                for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                    # KDK나 단식은 개인별 집계, 고정페어는 팀별 집계도 가능하나 여기서는 개인별 합산
                    for n in team:
                        if n not in stats: stats[n] = {"승":0, "패":0, "득실":0, "경기수":0}
                        stats[n]["경기수"] += 1
                        if my_s > op_s: stats[n]["승"] += 1
                        elif my_s < op_s: stats[n]["패"] += 1
                        stats[n]["득실"] += (my_s - op_s)
            if stats:
                res_df = pd.DataFrame.from_dict(stats, orient='index').sort_values(["승", "득실"], ascending=False)
                res_df.insert(0, "순위", range(1, len(res_df)+1))
                st.table(res_df)

# [4] 지난 기록
elif menu == "📜 지난 대회 기록":
    st.markdown("<div class='main-title'>PAST RECORDS</div>", unsafe_allow_html=True)
    history = load_history()
    if history.empty: st.info("기록이 없습니다.")
    else:
        history['선택정보'] = history['날짜'] + " [" + history['대회명'] + "]"
        unique_tours = history['선택정보'].unique()[::-1]
        selected = st.selectbox("대회 기록 선택", unique_tours)
        filtered_history = history[history['선택정보'] == selected].drop(columns=['선택정보'])
        st.table(filtered_history)

# [5] 관리자 센터
elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    if st.text_input("비밀번호", type="password") == "0502":
        tab1, tab2, tab3, tab4 = st.tabs(["대회 생성", "랭킹/결과 관리", "기록 삭제/수정", "시스템 초기화"])
        
        with tab1:
            st.session_state.tournament_name = st.text_input("대회 이름 입력", st.session_state.tournament_name)
            raw_p = st.text_area("참가자 명단 (쉼표로 구분 예: 홍길동, 김철수, ...)")
            g_count = st.number_input("그룹 수", 1, 10, 2)
            g_sizes = {}
            for i in range(int(g_count)):
                gn = chr(65+i); c1, c2, c3 = st.columns(3)
                with c1: g_sizes[gn] = st.number_input(f"Group {gn} 인원", 2, 100, 8)
                with c2: st.session_state.modes[gn] = st.selectbox(f"방식 {gn}", ["고정페어", "KDK", "단식"], key=f"mode_select_{gn}")
                with c3: st.session_state.game_counts[gn] = st.selectbox(f"1인당 경기수 {gn}", [3, 4, 5, 6], index=1, key=f"game_select_{gn}")
            
            if st.button("대회 생성 및 랭킹순 자동 배정", type="primary"):
                player_list = [p.strip() for p in raw_p.split(",") if p.strip()]
                if len(player_list) < sum(g_sizes.values()):
                    st.error(f"입력된 인원({len(player_list)}명)이 설정된 총원({sum(g_sizes.values())}명)보다 적습니다.")
                else:
                    st.session_state.players = player_list
                    # 1. 랭킹순 그룹 배정
                    st.session_state.groups = make_groups_by_rank(player_list, g_sizes)
                    st.session_state.current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.session_state.scores = {}
                    st.session_state.schedule = {}
                    
                    for g in st.session_state.groups.keys():
                        group_p = st.session_state.groups[g]
                        mode = st.session_state.modes[g]
                        target = st.session_state.game_counts[g]
                        
                        if mode == "KDK":
                            # KDK 균등 경기수 로직
                            st.session_state.schedule[g] = make_kdk_schedule_v2(group_p, target)
                        elif mode == "고정페어":
                            # 밸런싱 페어 구성 (1위-8위 등)
                            balanced_teams = make_balanced_pairs(group_p)
                            st.session_state.schedule[g] = make_round_robin(balanced_teams, target)
                        else: # 단식
                            single_teams = [[p] for p in group_p]
                            st.session_state.schedule[g] = make_round_robin(single_teams, target)
                            
                    st.success(f"'{st.session_state.tournament_name}' 대회가 생성되었습니다!")
                    st.balloons()

        with tab2:
            st.subheader("📁 랭킹 데이터 관리")
            up_file = st.file_uploader("랭킹 엑셀/CSV 업로드 (이름, 현재포인트 컬럼 필요)", type=["csv", "xlsx"])
            if up_file:
                df_raw = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
                df_p = process_uploaded_file(df_raw)
                if df_p is not None:
                    st.dataframe(df_p.head(10))
                    if st.button("데이터베이스에 저장"):
                        save_rank(df_p)
                        st.success("랭킹 정보가 업데이트되었습니다.")

            st.divider()
            st.subheader("⚖️ 수동 점수(부과점) 관리")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                target_p = st.selectbox("대상 선수", load_rank()['이름'].tolist() if not load_rank().empty else [])
                extra_pt = st.number_input("조정 점수 (+/-)", -100, 100, 0)
                if st.button("점수 반영"):
                    r_df = load_rank()
                    r_df.loc[r_df['이름'] == target_p, '현재포인트'] += extra_pt
                    save_rank(r_df); st.success("반영 완료")

            st.divider()
            if st.button("현재 대회 결과 최종 확정 (랭킹 포인트 반영)", type="primary"):
                rank = load_rank()
                history_data = []
                
                for g, g_players in st.session_state.groups.items():
                    stats = {}
                    group_scores = {k: v for k, v in st.session_state.scores.items() if k[0] == g}
                    
                    for key, data in group_scores.items():
                        t1, t2 = data["teams"]
                        s1, s2 = data["score"]
                        for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                            for n in team:
                                if n not in stats: stats[n] = {"승":0, "득실":0}
                                if my_s > op_s: stats[n]["승"] += 1
                                stats[n]["득실"] += (my_s - op_s)
                    
                    # 그룹 내 순위 산정
                    sorted_p = sorted(stats.items(), key=lambda x: (x[1]['승'], x[1]['득실']), reverse=True)
                    mode = st.session_state.modes[g]
                    
                    for idx, (p_name, s_vals) in enumerate(sorted_p):
                        rank_pos = idx + 1
                        # 포인트 부여 로직
                        if mode == "고정페어":
                            if rank_pos == 1: pts = 7
                            elif rank_pos == 2: pts = 5
                            elif rank_pos == 3: pts = 3
                            else: pts = 1
                        else: # KDK, 단식 (공동 순위 성격 고려 상위권 혜택)
                            if rank_pos <= 2: pts = 7
                            elif rank_pos <= 4: pts = 5
                            elif rank_pos <= 6: pts = 3
                            else: pts = 1
                        
                        # 랭킹 반영
                        if p_name in rank["이름"].values:
                            rank.loc[rank["이름"] == p_name, "현재포인트"] += pts
                        else:
                            new_row = pd.DataFrame({"이름": [p_name], "현재포인트": [pts]})
                            rank = pd.concat([rank, new_row], ignore_index=True)
                            
                        history_data.append({
                            "날짜": st.session_state.current_date, "대회명": st.session_state.tournament_name,
                            "그룹": g, "방식": mode, "이름": p_name, 
                            "순위": f"{rank_pos}위" if pts > 1 else "참가", "승": s_vals["승"], "득실": s_vals["득실"]
                        })
                
                save_rank(rank)
                new_h = pd.concat([load_history(), pd.DataFrame(history_data)], ignore_index=True)
                new_h.to_csv(HISTORY_FILE, index=False)
                st.success("모든 결과가 랭킹에 반영되었으며 기록으로 저장되었습니다!")

        with tab3:
            st.subheader("🗑 대회 기록 삭제")
            history = load_history()
            if history.empty: st.info("삭제할 기록이 없습니다.")
            else:
                history['선택정보'] = history['날짜'] + " [" + history['대회명'] + "]"
                del_target = st.selectbox("삭제할 대회 선택", history['선택정보'].unique()[::-1], key="del_select")
                if st.button("선택한 대회 기록 영구 삭제", type="primary"):
                    new_history = history[history['선택정보'] != del_target].drop(columns=['선택정보'])
                    new_history.to_csv(HISTORY_FILE, index=False)
                    st.success(f"{del_target} 기록이 삭제되었습니다.")
                    st.rerun()

        with tab4:
            st.warning("⚠️ 주의: 전체 초기화 시 랭킹과 모든 대회 기록이 사라집니다.")
            if st.button("시스템 전체 데이터 초기화"):
                if os.path.exists(RANK_FILE): os.remove(RANK_FILE)
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                st.session_state.clear()
                st.rerun()
