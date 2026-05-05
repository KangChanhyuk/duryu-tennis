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

def team_name(t):
    return " & ".join(t) if isinstance(t, (list, tuple)) and len(t) > 1 else (t[0] if isinstance(t, (list, tuple)) else t)

def process_uploaded_file(df):
    df.columns = [str(c).strip() for c in df.columns]
    name_col = next((c for c in df.columns if any(kw in c.lower() for kw in ['이름', '성함', 'name'])), None)
    point_col = next((c for c in df.columns if any(kw in c.lower() for kw in ['현재', '포인트', '점수'])), None)
    if not name_col: return None
    new_df = pd.DataFrame()
    new_df['이름'] = df[name_col].astype(str)
    new_df['현재포인트'] = pd.to_numeric(df[point_col], errors='coerce').fillna(0).astype(int) if point_col else 0
    return new_df.sort_values("현재포인트", ascending=False).reset_index(drop=True)

def make_groups(players, sizes):
    rank_df = load_rank()
    if not rank_df.empty and '이름' in rank_df.columns:
        rank_order = rank_df.sort_values("현재포인트", ascending=False)["이름"].tolist()
        ordered = [p for p in rank_order if p in players] + [p for p in players if p not in rank_order]
    else: ordered = players
    groups = {}
    curr = 0
    for g, s in sizes.items():
        groups[g] = ordered[curr:curr+s]
        curr += s
    return groups

def make_pairs(players, mode):
    temp = players[:]
    if mode == "KDK": random.shuffle(temp)
    pairs = []
    if mode in ["고정페어", "KDK"]:
        for i in range(0, len(temp)-1, 2): pairs.append([temp[i], temp[i+1]])
        if len(temp) % 2 == 1: pairs.append([temp[-1]])
    else: pairs = [[p] for p in temp]
    return pairs

def make_schedule(teams, target_games):
    matches = [[teams[i], teams[j]] for i in range(len(teams)) for j in range(i+1, len(teams))]
    random.shuffle(matches)
    rounds = []
    while matches:
        curr_round = []
        used_players = set()
        for m in matches[:]:
            p1_set = set(m[0])
            p2_set = set(m[1])
            if not (p1_set & used_players) and not (p2_set & used_players):
                curr_round.append(m)
                used_players.update(p1_set); used_players.update(p2_set)
                matches.remove(m)
        if not curr_round: break
        rounds.append(curr_round)
    return rounds[:target_games]

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
    else: st.info("데이터가 없습니다. 관리자 센터에서 랭킹 데이터를 업로드해주세요.")

elif menu == "📅 대진표/입력":
    st.markdown("<div class='main-title'>MATCH SCHEDULE</div>", unsafe_allow_html=True)
    if not st.session_state.schedule:
        st.warning("대진이 없습니다. 관리자 페이지에서 대회를 생성하세요.")
    else:
        st.info(f"🏟 대회명: {st.session_state.tournament_name}")
        # 전체 랭킹 명단 가져오기
        all_rank_players = load_rank()['이름'].tolist() if not load_rank().empty else []
        full_selection_list = sorted(list(set(st.session_state.players + all_rank_players)))
        
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.markdown(f"<h4 style='text-align: center; background:#eee; padding:5px;'>Round {ri+1}</h4>", unsafe_allow_html=True)
                    for mi, (t1, t2) in enumerate(rd):
                        bg_class = "match-bg-1" if mi % 2 == 0 else "match-bg-2"
                        with st.container():
                            c1, c_vs, c2 = st.columns([4, 1, 4])
                            with c1:
                                st.markdown(f"<div class='team-card {bg_class}'><div class='team-name'>{team_name(t1)}</div></div>", unsafe_allow_html=True)
                                with st.expander("선수 교체"):
                                    for pi, p_name in enumerate(t1):
                                        # 교체 옵션: 전체 명단 + 직접 입력
                                        options = ["선택안함"] + full_selection_list + ["🆕 직접 입력"]
                                        sel = st.selectbox(f"교체 ({p_name})", options, key=f"sel_{g}_{ri}_{mi}_t1_{pi}")
                                        if sel == "🆕 직접 입력":
                                            new_name = st.text_input("이름 입력", key=f"txt_{g}_{ri}_{mi}_t1_{pi}")
                                            if st.button("확인", key=f"btn_ok_{g}_{ri}_{mi}_t1_{pi}") and new_name:
                                                st.session_state.schedule[g][ri][mi][0][pi] = new_name.strip()
                                                st.rerun()
                                        elif sel != "선택안함":
                                            st.session_state.schedule[g][ri][mi][0][pi] = sel
                                            st.rerun()
                                s1 = st.number_input("Score", 0, 10, key=f"s1_{g}_{ri}_{mi}", label_visibility="collapsed")
                            with c_vs: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                            with c2:
                                st.markdown(f"<div class='team-card {bg_class}'><div class='team-name'>{team_name(t2)}</div></div>", unsafe_allow_html=True)
                                with st.expander("선수 교체"):
                                    for pi, p_name in enumerate(t2):
                                        options = ["선택안함"] + full_selection_list + ["🆕 직접 입력"]
                                        sel = st.selectbox(f"교체 ({p_name})", options, key=f"sel_{g}_{ri}_{mi}_t2_{pi}")
                                        if sel == "🆕 직접 입력":
                                            new_name = st.text_input("이름 입력", key=f"txt_{g}_{ri}_{mi}_t2_{pi}")
                                            if st.button("확인", key=f"btn_ok_{g}_{ri}_{mi}_t2_{pi}") and new_name:
                                                st.session_state.schedule[g][ri][mi][1][pi] = new_name.strip()
                                                st.rerun()
                                        elif sel != "선택안함":
                                            st.session_state.schedule[g][ri][mi][1][pi] = sel
                                            st.rerun()
                                s2 = st.number_input("Score", 0, 10, key=f"s2_{g}_{ri}_{mi}", label_visibility="collapsed")
                            if st.button(f"결과 저장: {mi+1}번 경기", key=f"btn_{g}_{ri}_{mi}"):
                                st.session_state.scores[(tuple(t1), tuple(t2))] = (s1, s2)
                                st.success("저장되었습니다!")
                        st.markdown("<hr style='margin:10px 0;'>", unsafe_allow_html=True)

elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>MATCH RESULTS</div>", unsafe_allow_html=True)
    if not st.session_state.scores: st.info("입력된 결과가 없습니다.")
    else:
        for g in st.session_state.groups.keys():
            st.markdown(f"<h3 style='text-align: center;'>Group {g} 결과</h3>", unsafe_allow_html=True)
            stats = {}
            for (t1, t2), (s1, s2) in st.session_state.scores.items():
                if t1[0] not in st.session_state.groups[g]: continue
                for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                    names = [team_name(team)] if st.session_state.modes[g] == "고정페어" else list(team)
                    for n in names:
                        if n not in stats: stats[n] = {"승":0, "패":0, "득실":0}
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
        selected = st.selectbox("대회 기록 선택", history['선택정보'].unique()[::-1])
        st.table(history[history['선택정보'] == selected].drop(columns=['선택정보']))

elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    if st.text_input("비밀번호", type="password") == "0502":
        tab1, tab2, tab3 = st.tabs(["대회 생성", "랭킹/결과/부과점", "시스템 초기화"])
        
        with tab1:
            st.session_state.tournament_name = st.text_input("대회 이름 입력", st.session_state.tournament_name)
            raw_p = st.text_area("참가자 (쉼표 구분)")
            g_count = st.number_input("그룹 수", 1, 10, 2)
            g_sizes = {}
            for i in range(int(g_count)):
                gn = chr(65+i); c1, c2, c3 = st.columns(3)
                with c1: g_sizes[gn] = st.number_input(f"Group {gn} 인원", 2, 100, 4)
                with c2: st.session_state.modes[gn] = st.selectbox(f"방식 {gn}", ["KDK", "고정페어", "단식"])
                with c3: st.session_state.game_counts[gn] = st.selectbox(f"게임수 {gn}", [3, 4, 5, 6])
            
            if st.button("대회 생성!", type="primary"):
                st.session_state.players = [p.strip() for p in raw_p.split(",") if p.strip()]
                st.session_state.groups = make_groups(st.session_state.players, g_sizes)
                st.session_state.current_date = datetime.now().strftime("%Y-%m-%d %H:%M")
                st.session_state.scores = {}
                for g in st.session_state.groups.keys():
                    teams = make_pairs(st.session_state.groups[g], st.session_state.modes[g])
                    st.session_state.schedule[g] = make_schedule(teams, st.session_state.game_counts[g])
                st.success(f"'{st.session_state.tournament_name}' 대진표 생성 완료!")

        with tab2:
            st.subheader("📁 엑셀 및 부과 포인트")
            up_file = st.file_uploader("랭킹 엑셀 업로드", type=["csv", "xlsx"])
            if up_file:
                df_raw = pd.read_excel(up_file) if up_file.name.endswith('xlsx') else pd.read_csv(up_file)
                df_p = process_uploaded_file(df_raw)
                if df_p is not None:
                    st.dataframe(df_p.head(5))
                    if st.button("랭킹 저장"): save_rank(df_p); st.success("저장완료")

            st.divider()
            st.subheader("⚖️ 부과점 관리")
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                target_p = st.selectbox("부과점 부여 선수", load_rank()['이름'].tolist() if not load_rank().empty else [])
                extra_pt = st.number_input("부과 점수(보너스/벌점)", -100, 100, 0)
                if st.button("부과점 반영"):
                    r_df = load_rank()
                    r_df.loc[r_df['이름'] == target_p, '현재포인트'] += extra_pt
                    save_rank(r_df); st.success(f"{target_p}님에게 {extra_pt}점 부과 완료")

            st.divider()
            if st.button("현재 대회 결과 확정 (랭킹 반영)"):
                rank = load_rank(); history_data = []
                for g, g_players in st.session_state.groups.items():
                    stats = {}
                    for (t1, t2), (s1, s2) in st.session_state.scores.items():
                        # 현재 대진표에 표시된 실시간 이름 기준 반영
                        for team, my_s, op_s in [(t1, s1, s2), (t2, s2, s1)]:
                            for n in team:
                                if n not in stats: stats[n] = {"승":0, "득실":0}
                                if my_s > op_s: stats[n]["승"] += 1
                                stats[n]["득실"] += (my_s - op_s)
                    
                    sorted_p = sorted(stats.items(), key=lambda x: (x[1]['승'], x[1]['득실']), reverse=True)
                    for idx, (p_name, s_vals) in enumerate(sorted_p):
                        rank_pos = idx + 1
                        pts = 7 if rank_pos <= 2 else (5 if rank_pos <= 4 else 3)
                        if p_name in rank["이름"].values: rank.loc[rank["이름"] == p_name, "현재포인트"] += pts
                        else: # 새로운 선수인 경우 랭킹에 추가
                             new_row = pd.DataFrame({"이름": [p_name], "현재포인트": [pts]})
                             rank = pd.concat([rank, new_row], ignore_index=True)
                             
                        history_data.append({
                            "날짜": st.session_state.current_date, "대회명": st.session_state.tournament_name,
                            "그룹": g, "방식": st.session_state.modes[g], "이름": p_name, 
                            "순위": rank_pos, "승": s_vals["승"], "득실": s_vals["득실"]
                        })
                save_rank(rank)
                new_h = pd.concat([load_history(), pd.DataFrame(history_data)], ignore_index=True)
                new_h.to_csv(HISTORY_FILE, index=False)
                st.success("랭킹 및 대회 기록 저장 완료!")

        with tab3:
            if st.button("시스템 전체 초기화"):
                if os.path.exists(RANK_FILE): os.remove(RANK_FILE)
                if os.path.exists(HISTORY_FILE): os.remove(HISTORY_FILE)
                st.session_state.clear(); st.rerun()
