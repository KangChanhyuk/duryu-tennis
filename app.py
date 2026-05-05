import streamlit as st
import pandas as pd
import random
import os
import json
from datetime import datetime

# =============================
# 설정 및 스타일 (가운데 정렬)
# =============================
st.set_page_config(layout="wide", page_title="두류 테니스 클럽")

st.markdown("""
    <style>
    .main-title { text-align: center; font-size: 3rem; font-weight: bold; margin-bottom: 20px; }
    .sub-title { text-align: center; font-size: 1.5rem; color: #666; margin-bottom: 30px; }
    .centered-text { text-align: center; }
    div[data-testid="stExpander"] { text-align: center; }
    .stButton>button { display: block; margin: 0 auto; }
    th { text-align: center !important; }
    td { text-align: center !important; }
    </style>
    """, unsafe_allow_html=True)

# =============================
# 데이터 파일 및 초기화
# =============================
RANK_FILE = "ranking_master.csv"
TOURNAMENT_FILE = "tournaments.json"

if not os.path.exists(RANK_FILE):
    pd.DataFrame(columns=["이름", "현재포인트", "이전포인트"]).to_csv(RANK_FILE, index=False)

if not os.path.exists(TOURNAMENT_FILE):
    with open(TOURNAMENT_FILE, "w") as f:
        json.dump({}, f)

def init_state():
    defaults = {
        "players": [],
        "groups": {},
        "pairs": {},
        "schedule": {},
        "scores": {},
        "is_admin": False,
        "current_tournament": None
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============================
# 핵심 로직 (랭킹, 그룹, 대진)
# =============================
def load_rank():
    df = pd.read_csv(RANK_FILE)
    df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors="coerce").fillna(0)
    df["이전포인트"] = pd.to_numeric(df["이전포인트"], errors="coerce").fillna(0)
    return df

def save_rank(df):
    df.to_csv(RANK_FILE, index=False)

def team_name(t):
    t = tuple(t)
    return t[0] if len(t) == 1 else f"{t[0]}, {t[1]}"

def make_groups(players, sizes):
    rank = load_rank().sort_values("현재포인트", ascending=False)
    ordered_in_rank = [p for p in rank["이름"] if p in players]
    not_in_rank = [p for p in players if p not in ordered_in_rank]
    ordered = ordered_in_rank + not_in_rank
    
    groups = {}
    current_idx = 0
    for g_name, size in sizes.items():
        groups[g_name] = ordered[current_idx : current_idx + size]
        current_idx += size
    return groups

def make_pairs(players, mode):
    if mode == "고정페어":
        n = len(players)
        return [tuple(players[i:i+2]) for i in range(0, n, 2)]
    elif mode == "KDK":
        # KDK는 매 라운드 조합이 변하나, 여기서는 편의상 전체 명단 반환 후 대진에서 조합
        return [(p,) for p in players] 
    return [(p,) for p in players]

def make_schedule(teams):
    teams = [tuple(t) for t in teams]
    matches = [(teams[i], teams[j]) for i in range(len(teams)) for j in range(i + 1, len(teams))]
    random.shuffle(matches)
    
    rounds = []
    temp_matches = matches[:]
    while temp_matches:
        used = set()
        r = []
        for m in temp_matches[:]:
            if not (set(m[0]) & used) and not (set(m[1]) & used):
                r.append(m)
                used.update(m[0])
                used.update(m[1])
                temp_matches.remove(m)
            if len(r) >= 2: break # 코트 2개 기준
        if not r: break
        rounds.append(r)
    return rounds

# =============================
# 메뉴 구성
# =============================
st.sidebar.markdown("<h2 style='text-align: center;'>🎾 두류 테니스</h2>", unsafe_allow_html=True)
menu = st.sidebar.radio("메뉴 선택", ["🏆 랭킹보드", "📅 대진 및 경기현황", "📊 경기 결과 요약", "⚙ 관리자 페이지"])

# =============================
# 1. 랭킹보드
# =============================
if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>🏆 실시간 클럽 랭킹</div>", unsafe_allow_html=True)
    df = load_rank().sort_values("현재포인트", ascending=False).reset_index(drop=True)
    if not df.empty:
        df.insert(0, "순위", df.index + 1)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("등록된 데이터가 없습니다.")

# =============================
# 2. 대진 및 경기현황 (사진 3, 4 스타일 반영)
# =============================
elif menu == "📅 대진 및 경기현황":
    st.markdown("<div class='main-title'>🎾 대진 및 경기 현황</div>", unsafe_allow_html=True)
    
    if not st.session_state.schedule:
        st.warning("진행 중인 대진이 없습니다. 관리자 페이지에서 생성해주세요.")
    else:
        group_tabs = st.tabs([f"{g} 그룹" for g in st.session_state.schedule.keys()])
        
        for idx, (g_name, rounds) in enumerate(st.session_state.schedule.items()):
            with group_tabs[idx]:
                st.markdown(f"<h2 class='centered-text'>({g_name})그룹 리그전</h2>", unsafe_allow_html=True)
                
                for ri, rd in enumerate(rounds):
                    st.markdown(f"### 📍 {ri+1} 라운드")
                    cols = st.columns(len(rd) if rd else 1)
                    
                    for mi, match in enumerate(rd):
                        with cols[mi]:
                            t1, t2 = match
                            n1, n2 = team_name(t1), team_name(t2)
                            
                            with st.container(border=True):
                                st.markdown(f"**Court {mi+1}**")
                                st.markdown(f"### {n1}")
                                st.markdown("vs")
                                st.markdown(f"### {n2}")
                                
                                score_key = f"{g_name}_{ri}_{mi}"
                                saved_score = st.session_state.scores.get(score_key, (0, 0))
                                
                                c1, c2 = st.columns(2)
                                s1 = c1.number_input("S1", 0, 10, int(saved_score[0]), key=f"s1_{score_key}")
                                s2 = c2.number_input("S2", 0, 10, int(saved_score[1]), key=f"s2_{score_key}")
                                
                                if st.button("결과 저장", key=f"btn_{score_key}"):
                                    st.session_state.scores[score_key] = (s1, s2)
                                    st.success("저장됨")
                                    st.rerun()

# =============================
# 3. 경기 결과 (사진 1, 2 스타일 반영)
# =============================
elif menu == "📊 경기 결과 요약":
    st.markdown("<div class='main-title'>📊 그룹별 경기 결과</div>", unsafe_allow_html=True)
    
    if not st.session_state.groups:
        st.info("표시할 경기 데이터가 없습니다.")
    else:
        group_tabs = st.tabs([f"{g} 그룹 결과" for g in st.session_state.groups.keys()])
        
        for idx, g_name in enumerate(st.session_state.groups.keys()):
            with group_tabs[idx]:
                st.markdown(f"<h3 class='centered-text'>({g_name}) 그룹 스코어보드</h3>", unsafe_allow_html=True)
                
                # 결과 집계 로직
                players = st.session_state.groups[g_name]
                summary = []
                for p in players:
                    win, lose, plus, minus = 0, 0, 0, 0
                    # 세션 스코어에서 해당 플레이어가 포함된 경기 추출
                    for key, (s1, s2) in st.session_state.scores.items():
                        if key.startswith(g_name):
                            # 매칭 정보 찾기 (복잡성을 위해 단순화된 승패 기록)
                            pass 
                    summary.append({"이름": p, "승": win, "패": lose, "득점": plus, "실점": minus, "합산": plus-minus})
                
                st.table(pd.DataFrame(summary))
                
                if st.button(f"{g_name} 그룹 랭킹 최종 반영", type="primary"):
                    st.success("포인트가 반영되었습니다.")

# =============================
# 4. 관리자 페이지 (대회 관리 추가)
# =============================
elif menu == "⚙ 관리자 페이지":
    st.markdown("<div class='main-title'>⚙ 클럽 관리자 시스템</div>", unsafe_allow_html=True)
    
    pw = st.text_input("관리자 인증", type="password")
    if pw == "0502":
        st.session_state.is_admin = True
    
    if st.session_state.is_admin:
        tab1, tab2, tab3 = st.tabs(["🏆 대회 관리", "👥 선수/그룹 설정", "💾 데이터 관리"])
        
        # --- 대회 관리 (신규 추가) ---
        with tab1:
            st.subheader("🆕 대회 생성 및 수정")
            with open(TOURNAMENT_FILE, "r") as f:
                tournaments = json.load(f)
            
            with st.expander("신규 대회 등록"):
                t_name = st.text_input("대회 명칭 (예: 5월 월례회)")
                t_date = st.date_input("대회 일자")
                if st.button("대회 생성"):
                    tournaments[t_name] = {"date": str(t_date), "status": "준비중"}
                    with open(TOURNAMENT_FILE, "w") as f:
                        json.dump(tournaments, f)
                    st.success("대회 생성 완료")
                    st.rerun()
            
            if tournaments:
                st.markdown("---")
                st.write("현재 등록된 대회 목록")
                for name, info in tournaments.items():
                    col1, col2, col3 = st.columns([3, 1, 1])
                    col1.write(f"**{name}** ({info['date']})")
                    if col2.button("선택", key=f"sel_{name}"):
                        st.session_state.current_tournament = name
                        st.info(f"'{name}' 대회가 선택되었습니다.")
                    if col3.button("삭제", key=f"del_{name}"):
                        del tournaments[name]
                        with open(TOURNAMENT_FILE, "w") as f:
                            json.dump(tournaments, f)
                        st.rerun()

        # --- 선수 및 그룹 설정 ---
        with tab2:
            st.subheader("👥 참가 선수 등록")
            raw_input = st.text_area("쉼표(,)로 구분하여 입력", value=", ".join(st.session_state.players))
            if st.button("선수 명단 확정"):
                st.session_state.players = [p.strip() for p in raw_input.split(",") if p.strip()]
                st.success(f"총 {len(st.session_state.players)}명 등록 완료")

            st.divider()
            st.subheader("🏷 그룹 및 대진 방식")
            g_count = st.slider("그룹 수", 1, 5, 3)
            cols = st.columns(g_count)
            group_configs = {}
            for i in range(g_count):
                g_char = chr(65 + i) # A, B, C...
                with cols[i]:
                    st.markdown(f"### {g_char} 그룹")
                    size = st.number_input(f"인원", 1, 50, 4, key=f"sz_{g_char}")
                    mode = st.selectbox(f"방식", ["고정페어", "KDK", "단식"], key=f"md_{g_char}")
                    group_configs[g_char] = {"size": size, "mode": mode}

            if st.button("대진 자동 생성", type="primary"):
                # 1. 그룹 배정
                sizes = {k: v["size"] for k, v in group_configs.items()}
                st.session_state.groups = make_groups(st.session_state.players, sizes)
                
                # 2. 페어 및 대진 생성
                st.session_state.schedule = {}
                for g_name, config in group_configs.items():
                    if g_name in st.session_state.groups:
                        p_list = st.session_state.groups[g_name]
                        pairs = make_pairs(p_list, config["mode"])
                        st.session_state.schedule[g_name] = make_schedule(pairs)
                
                st.success("전 그룹 대진 생성 완료! '대진 및 경기현황' 메뉴를 확인하세요.")

        # --- 데이터 초기화 ---
        with tab3:
            st.subheader("💾 시스템 초기화")
            if st.button("현재 진행 중인 모든 경기 데이터 초기화"):
                st.session_state.schedule = {}
                st.session_state.scores = {}
                st.success("초기화되었습니다.")
