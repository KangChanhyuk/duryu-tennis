import streamlit as st
import pandas as pd
import random
import os

# 페이지 설정
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

# CSS 스타일 적용 (이름 짤림 방지 및 카드 디자인)
st.markdown("""
    <style>
    .team-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #4CAF50;
        margin-bottom: 10px;
    }
    .team-name {
        font-size: 1.1rem;
        font-weight: bold;
        color: #333;
        white-space: nowrap;
    }
    .vs-text {
        font-size: 1.2rem;
        font-weight: bold;
        color: #ff4b4b;
        text-align: center;
        margin: auto 0;
    }
    .rank-table {
        font-size: 1rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 파일 및 경로 설정
# =============================
RANK_FILE = "ranking_master.csv"

if not os.path.exists(RANK_FILE):
    pd.DataFrame(columns=["이름", "현재포인트", "이전포인트"]).to_csv(RANK_FILE, index=False)

# =============================
# 세션 상태 초기화
# =============================
def init_state():
    defaults = {
        "players": [],
        "groups": {},
        "pairs": {},
        "modes": {}, # 그룹별 방식 저장
        "schedule": {},
        "scores": {},
        "is_admin": False
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============================
# 데이터 로드/저장/처리 함수
# =============================
def load_rank():
    df = pd.read_csv(RANK_FILE)
    df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors="coerce").fillna(0).astype(int)
    df["이전포인트"] = pd.to_numeric(df["이전포인트"], errors="coerce").fillna(0).astype(int)
    return df

def save_rank(df):
    df["현재포인트"] = df["현재포인트"].astype(int)
    df["이전포인트"] = df["이전포인트"].astype(int)
    df.to_csv(RANK_FILE, index=False)

def team_name(t):
    t = tuple(t)
    return " & ".join(t) if len(t) > 1 else t[0]

def make_groups(players, sizes):
    rank = load_rank().sort_values("현재포인트", ascending=False)
    ordered_in_rank = [p for p in rank["이름"] if p in players]
    not_in_rank = [p for p in players if p not in ordered_in_rank]
    ordered = ordered_in_rank + not_in_rank

    groups = {}
    current_idx = 0
    for g, s in sizes.items():
        groups[g] = ordered[current_idx : current_idx + s]
        current_idx += s
    return groups

def make_pairs(players, mode):
    temp = players[:]
    if mode == "KDK":
        random.shuffle(temp) # 랜덤 조 배정
    
    if mode in ["고정페어", "KDK"]:
        pairs = []
        for i in range(0, len(temp) - 1, 2):
            pairs.append((temp[i], temp[i+1]))
        if len(temp) % 2 == 1:
            pairs.append((temp[-1],))
        return pairs
    else: # 단식
        return [(p,) for p in temp]

def make_schedule(teams):
    teams = [tuple(t) for t in teams]
    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i + 1, len(teams))]
    random.shuffle(matches)

    rounds = []
    while matches:
        used = set()
        current_round = []
        for m in matches[:]:
            if not (set(m[0]) & used) and not (set(m[1]) & used):
                current_round.append(m)
                used.update(m[0])
                used.update(m[1])
                matches.remove(m)
            if len(current_round) == 2: break
        if not current_round: break
        rounds.append(current_round)
    return rounds

# =============================
# 메인 메뉴
# =============================
menu = st.sidebar.radio("메뉴", ["두류랭킹", "대진 및 경기", "경기 결과", "관리자"])

# -----------------------------
# 1. 두류랭킹
# -----------------------------
if menu == "두류랭킹":
    st.title("🏆 두류 클럽 랭킹")
    df = load_rank().sort_values("현재포인트", ascending=False).reset_index(drop=True)
    if not df.empty:
        df.insert(0, "랭킹", df.index + 1)
        st.table(df) # 이름이 잘리지 않도록 table 사용
    else:
        st.info("관리자 페이지에서 멤버를 업로드하거나 등록해주세요.")

# -----------------------------
# 2. 대진 및 경기
# -----------------------------
elif menu == "대진 및 경기":
    st.title("🎾 대진표 및 스코어 입력")
    if not st.session_state.schedule:
        st.warning("관리자 메뉴에서 대진을 먼저 생성해주세요.")
    else:
        tabs = st.tabs(list(st.session_state.schedule.keys()))
        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                rounds = st.session_state.schedule[g]
                for ri, rd in enumerate(rounds):
                    st.markdown(f"#### 📅 {ri + 1} 라운드")
                    for i, m in enumerate(rd):
                        t1, t2 = m
                        n1, n2 = team_name(t1), team_name(t2)
                        
                        # 경기 카드 UI
                        with st.container():
                            col1, col_vs, col2, col_btn = st.columns([4, 1, 4, 2])
                            with col1:
                                st.markdown(f"<div class='team-card'><span class='team-name'>{n1}</span></div>", unsafe_allow_html=True)
                                s1 = st.number_input(f"점수", 0, 50, key=f"s1_{g}_{ri}_{i}", label_visibility="collapsed")
                            with col_vs:
                                st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                            with col2:
                                st.markdown(f"<div class='team-card'><span class='team-name'>{n2}</span></div>", unsafe_allow_html=True)
                                s2 = st.number_input(f"점수", 0, 50, key=f"s2_{g}_{ri}_{i}", label_visibility="collapsed")
                            with col_btn:
                                if st.button("결과저장", key=f"btn_{g}_{ri}_{i}"):
                                    st.session_state.scores[(t1, t2)] = (s1, s2)
                                    st.toast(f"{n1} vs {n2} 저장완료!")

# -----------------------------
# 3. 경기 결과 (순위 포함)
# -----------------------------
elif menu == "경기 결과":
    st.title("📊 경기 결과 및 당일 순위")
    if not st.session_state.scores:
        st.info("입력된 경기 결과가 없습니다.")
    else:
        group_list = list(st.session_state.groups.keys())
        tabs = st.tabs(group_list)
        
        for idx, g in enumerate(group_list):
            with tabs[idx]:
                mode = st.session_state.modes.get(g, "단식")
                st.subheader(f"Group {g} ({mode} 방식) 결과")
                
                # 데이터 집계
                personal_stats = {} # {이름: {승:0, 패:0, 점수:0}}
                team_stats = {}     # {페어: {승:0, 패:0, 점수:0}}
                
                for (t1, t2), (s1, s2) in st.session_state.scores.items():
                    # 해당 그룹 선수들이 포함된 경기인지 확인
                    if t1[0] not in st.session_state.groups[g]: continue
                    
                    # 개인별 집계
                    for p in list(t1) + list(t2):
                        if p not in personal_stats: personal_stats[p] = {'승':0, '패':0, '득점':0}
                    
                    # 팀별 집계
                    n1, n2 = team_name(t1), team_name(t2)
                    if n1 not in team_stats: team_stats[n1] = {'승':0, '패':0, '득점':0}
                    if n2 not in team_stats: team_stats[n2] = {'승':0, '패':0, '득점':0}

                    # 승무패 로직
                    if s1 > s2:
                        for p in t1: personal_stats[p]['승'] += 1
                        for p in t2: personal_stats[p]['패'] += 1
                        team_stats[n1]['승'] += 1
                        team_stats[n2]['패'] += 1
                    elif s2 > s1:
                        for p in t2: personal_stats[p]['승'] += 1
                        for p in t1: personal_stats[p]['패'] += 1
                        team_stats[n2]['승'] += 1
                        team_stats[n1]['패'] += 1
                    
                    for p in t1: personal_stats[p]['득점'] += s1
                    for p in t2: personal_stats[p]['득점'] += s2
                    team_stats[n1]['득점'] += s1
                    team_stats[n2]['득점'] += s2

                # 순위 표시 방식 결정
                if mode == "고정페어":
                    res_df = pd.DataFrame.from_dict(team_stats, orient='index').sort_values(['승', '득점'], ascending=False)
                    res_df.index.name = "페어(팀)"
                else: # KDK, 단식
                    res_df = pd.DataFrame.from_dict(personal_stats, orient='index').sort_values(['승', '득점'], ascending=False)
                    res_df.index.name = "이름"
                
                res_df.insert(0, "당일순위", range(1, len(res_df) + 1))
                st.table(res_df)

# -----------------------------
# 4. 관리자
# -----------------------------
elif menu == "관리자":
    st.title("⚙ 관리자 설정")
    pw = st.text_input("비밀번호", type="password")
    if pw == "0502":
        st.session_state.is_admin = True
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("1. 멤버 관리")
            file = st.file_uploader("랭킹 엑셀 업로드", type=["xlsx", "csv"])
            if file and st.button("파일 적용"):
                df = pd.read_excel(file) if file.name.endswith('xlsx') else pd.read_csv(file)
                # ... (중복 제거 및 형식 맞춤 로직)
                save_rank(df)
                st.success("랭킹 파일이 업데이트 되었습니다.")
            
            raw_players = st.text_area("당일 참가자 명단 (쉼표 구분)", value=", ".join(st.session_state.players))
            if st.button("참가자 명단 확정"):
                st.session_state.players = [p.strip() for p in raw_players.split(",") if p.strip()]
                st.success(f"{len(st.session_state.players)}명 등록 완료")

        with col2:
            st.subheader("2. 그룹 및 대진 생성")
            g_count = st.number_input("그룹 수", 1, 10, 2)
            g_sizes = {}
            for i in range(int(g_count)):
                char = chr(65 + i)
                g_sizes[char] = st.number_input(f"그룹 {char} 인원", 1, 100, 4)
            
            if st.button("그룹 분할 및 대진 생성"):
                st.session_state.groups = make_groups(st.session_state.players, g_sizes)
                st.session_state.schedule = {}
                st.session_state.scores = {}
                st.success("그룹 분할 완료. 아래에서 방식을 선택하세요.")

        if st.session_state.groups:
            st.divider()
            st.subheader("3. 그룹별 경기 방식")
            for g in st.session_state.groups.keys():
                col_g1, col_g2 = st.columns([2, 3])
                with col_g1:
                    mode = st.selectbox(f"그룹 {g} 방식", ["단식", "고정페어", "KDK"], key=f"mode_sel_{g}")
                    st.session_state.modes[g] = mode
                with col_g2:
                    st.write(f"멤버: {', '.join(st.session_state.groups[g])}")
            
            if st.button("최종 대진표 생성 (랜덤 포함)", type="primary"):
                for g in st.session_state.groups.keys():
                    teams = make_pairs(st.session_state.groups[g], st.session_state.modes[g])
                    st.session_state.pairs[g] = teams
                    st.session_state.schedule[g] = make_schedule(teams)
                st.success("대진표 생성 완료! '대진 및 경기' 메뉴로 가세요.")

        st.divider()
        st.subheader("4. 경기 결과 반영 (랭킹 업데이트)")
        if st.button("현재 모든 경기 결과를 전체 랭킹에 반영"):
            rank = load_rank()
            # 오늘 승점 계산 (승리당 3점 예시)
            today_points = {}
            for (t1, t2), (s1, s2) in st.session_state.scores.items():
                if s1 > s2:
                    for p in t1: today_points[p] = today_points.get(p, 0) + 3
                elif s2 > s1:
                    for p in t2: today_points[p] = today_points.get(p, 0) + 3
            
            rank["이전포인트"] = rank["현재포인트"]
            for p, pt in today_points.items():
                if p in rank["이름"].values:
                    rank.loc[rank["이름"] == p, "현재포인트"] += pt
                else:
                    new_p = pd.DataFrame([{"이름": p, "현재포인트": pt, "이전포인트": 0}])
                    rank = pd.concat([rank, new_p], ignore_index=True)
            
            save_rank(rank)
            st.success("랭킹 포인트 반영 및 정수화 완료!")

        if st.button("시스템 전체 초기화 (주의)", type="secondary"):
            st.session_state.clear()
            init_state()
            st.rerun()
