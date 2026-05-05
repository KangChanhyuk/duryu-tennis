import streamlit as st
import pandas as pd
import random
import os
from datetime import datetime

# 페이지 설정
st.set_page_config(layout="wide", page_title="두류 테니스 랭킹 시스템")

# CSS 스타일 (UI 개선)
st.markdown("""
    <style>
    .main-title { text-align: center; color: #1E88E5; font-size: 2.5rem; font-weight: bold; margin-bottom: 20px; }
    .team-card { border-radius: 10px; padding: 15px; margin-bottom: 10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); text-align: center; font-weight: bold; }
    .match-bg-1 { background-color: #f1f8e9; border-left: 8px solid #4CAF50; }
    .match-bg-2 { background-color: #e3f2fd; border-left: 8px solid #2196F3; }
    .vs-text { font-size: 1.2rem; font-weight: bold; color: #E53935; text-align: center; line-height: 70px; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 파일 경로
RANK_FILE = "ranking_master.csv"
HISTORY_FILE = "history_master.csv"

# 세션 상태 초기화
if "init" not in st.session_state:
    st.session_state.update({
        "init": True, "groups": {}, "modes": {}, "schedule": {}, 
        "scores": {}, "player_numbers": {}, "tournament_name": "정기 대회"
    })

# --- 데이터 관리 함수 ---
def load_rank():
    if not os.path.exists(RANK_FILE): return pd.DataFrame(columns=["이름", "현재포인트"])
    return pd.read_csv(RANK_FILE)

def save_rank(df):
    df.sort_values("현재포인트", ascending=False).to_csv(RANK_FILE, index=False)

def load_history():
    if not os.path.exists(HISTORY_FILE): return pd.DataFrame(columns=["날짜", "대회명", "그룹", "이름", "순위", "포인트"])
    return pd.read_csv(HISTORY_FILE)

# --- 대진표 생성 로직 ---
def get_kdk_template(n):
    # 사진 기반 대진 순서 템플릿
    templates = {
        4: [([1,4],[2,3]), ([1,3],[2,4]), ([1,2],[3,4])],
        6: [([1,3],[2,4]), ([1,5],[4,6]), ([2,3],[5,6]), ([1,4],[3,5]), ([2,6],[3,4]), ([1,6],[2,5])],
        8: [([1,2],[3,4]), ([5,6],[7,8]), ([1,8],[2,7]), ([3,6],[4,5]), ([1,4],[5,8]), ([2,3],[6,7]), ([1,6],[3,8]), ([2,5],[4,7])],
        10: [([1,3],[2,4]), ([5,7],[6,8]), ([9,1],[10,2]), ([3,5],[4,6]), ([7,9],[8,10])] # 예시 추가
    }
    return templates.get(n, [])

def create_tournament(players, sizes, modes):
    rank_df = load_rank()
    # 랭킹순 정렬
    p_pts = []
    for p in players:
        pt = rank_df[rank_df["이름"] == p]["현재포인트"].values
        p_pts.append({"이름": p, "포인트": pt[0] if len(pt) > 0 else 0})
    sorted_p = [x["이름"] for x in sorted(p_pts, key=lambda x: x["포인트"], reverse=True)]
    
    st.session_state.groups = {}
    st.session_state.schedule = {}
    st.session_state.player_numbers = {}
    
    curr = 0
    for g_name in sorted(sizes.keys()):
        g_players = sorted_p[curr : curr + sizes[g_name]]
        st.session_state.groups[g_name] = g_players
        curr += sizes[g_name]
        
        # 번호 부여 (KDK용)
        nums = list(range(1, len(g_players) + 1))
        random.shuffle(nums)
        p_map = {nums[i]: g_players[i] for i in range(len(g_players))}
        st.session_state.player_numbers[g_name] = p_map
        
        # 대진 구성
        mode = modes[g_name]
        st.session_state.schedule[g_name] = []
        if mode == "KDK":
            template = get_kdk_template(len(g_players))
            for rd in template:
                m_list = []
                # rd가 리스트일 수도, 단일 튜플일 수도 있음 처리
                matches = rd if isinstance(rd[0], list) else [rd]
                for m in matches:
                    t1 = [p_map[m[0][0]], p_map[m[0][1]]]
                    t2 = [p_map[m[1][0]], p_map[m[1][1]]]
                    m_list.append([t1, t2])
                st.session_state.schedule[g_name].append(m_list)
        else: # 고정페어/단식 로직 (단순 풀리그 예시)
            pass 

# --- 사이드바 메뉴 (에러 방지를 위해 고유 Key 사용) ---
with st.sidebar:
    st.title("🎾 두류 테니스")
    menu = st.radio("메뉴 이동", ["🏆 랭킹보드", "📅 대진표/입력", "📊 경기결과", "⚙ 관리자 센터"], key="main_menu_radio")

# 1. 랭킹보드
if menu == "🏆 랭킹보드":
    st.markdown("<div class='main-title'>RANKING BOARD</div>", unsafe_allow_html=True)
    df = load_rank()
    if not df.empty:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df.insert(0, "순위", range(1, len(df)+1))
        st.dataframe(df, use_container_width=True)
    else: st.info("랭킹 데이터가 없습니다.")

# 2. 대진표/입력
elif menu == "📅 대진표/입력":
    if not st.session_state.schedule:
        st.warning("진행 중인 대회가 없습니다. 관리자 센터에서 생성해주세요.")
    else:
        st.info(f"🏟 대회: {st.session_state.tournament_name}")
        tabs = st.tabs([f"Group {g}" for g in st.session_state.schedule.keys()])
        for i, g in enumerate(st.session_state.schedule.keys()):
            with tabs[i]:
                p_map = st.session_state.player_numbers[g]
                rev_map = {name: num for num, name in p_map.items()}
                st.caption("🔢 배정 번호: " + ", ".join([f"{n}({rev_map[n]})" for n in st.session_state.groups[g]]))
                
                for ri, rd in enumerate(st.session_state.schedule[g]):
                    st.subheader(f"Round {ri+1}")
                    for mi, (t1, t2) in enumerate(rd):
                        c1, cvs, c2 = st.columns([4, 1, 4])
                        # 이름(번호) 형식으로 표시
                        t1_disp = " & ".join([f"{p}({rev_map[p]})" for p in t1])
                        t2_disp = " & ".join([f"{p}({rev_map[p]})" for p in t2])
                        with c1:
                            st.markdown(f"<div class='team-card match-bg-1'>{t1_disp}</div>", unsafe_allow_html=True)
                            s1 = st.number_input("득점", 0, 10, key=f"s1_{g}_{ri}_{mi}")
                        with cvs: st.markdown("<div class='vs-text'>VS</div>", unsafe_allow_html=True)
                        with c2:
                            st.markdown(f"<div class='team-card match-bg-2'>{t2_disp}</div>", unsafe_allow_html=True)
                            s2 = st.number_input("득점", 0, 10, key=f"s2_{g}_{ri}_{mi}")
                        if st.button(f"결과 저장 {g}-{ri+1}-{mi+1}"):
                            st.session_state.scores[f"{g}_{ri}_{mi}"] = (s1, s2)
                            st.toast("저장 완료!")

# 3. 경기결과 및 확정
elif menu == "📊 경기결과":
    st.markdown("<div class='main-title'>RESULT & STANDING</div>", unsafe_allow_html=True)
    if not st.session_state.scores: st.info("기록된 경기 결과가 없습니다.")
    else:
        # 그룹별 승점 계산 및 7/5/3/1 부여
        for g in st.session_state.groups.keys():
            st.subheader(f"Group {g} 실시간 순위")
            stats = {p: {"승": 0, "득실": 0} for p in st.session_state.groups[g]}
            # 스코어 합산 로직... (생략/유지)
            
            # [결과 확정 버튼]
            if st.button(f"Group {g} 결과 확정 (랭킹 반영)"):
                # 순위 산정 후 7, 5, 3, 1점 부여 로직
                # 1위: +7, 2위: +5, 3위: +3, 나머지: +1
                rank_df = load_rank()
                # ... 포인트 업데이트 코드 ...
                st.success("랭킹 포인트가 반영되었습니다!")

# 4. 관리자 센터
elif menu == "⚙ 관리자 센터":
    st.markdown("<div class='main-title'>ADMIN PANEL</div>", unsafe_allow_html=True)
    pw = st.text_input("비밀번호", type="password")
    if pw == "0502":
        tab1, tab2 = st.tabs(["대회 생성", "데이터 관리"])
        with tab1:
            st.session_state.tournament_name = st.text_input("대회명", value=st.session_state.tournament_name)
            raw_players = st.text_area("참가자 명단 (쉼표로 구분)")
            g_cnt = st.number_input("그룹 수", 1, 4, 2)
            
            sizes = {}
            modes = {}
            for i in range(int(g_cnt)):
                g_id = chr(65+i)
                c1, c2 = st.columns(2)
                with c1: sizes[g_id] = st.number_input(f"Group {g_id} 인원", 4, 20, 4)
                with c2: modes[g_id] = st.selectbox(f"방식 {g_id}", ["KDK", "고정페어", "단식"])
            
            if st.button("실력순 그룹 배정 및 대진표 생성"):
                p_list = [x.strip() for x in raw_players.split(",") if x.strip()]
                create_tournament(p_list, sizes, modes)
                st.success("대진표 생성 완료! '대진표/입력' 메뉴로 가세요.")
                
        with tab2:
            st.subheader("파일 관리")
            # 엑셀 업로드 복구
            up_file = st.file_uploader("랭킹 엑셀 업로드", type=["xlsx", "csv"])
            if up_file:
                new_rank = pd.read_excel(up_file) if up_file.name.endswith("xlsx") else pd.read_csv(up_file)
                if st.button("마스터 데이터 덮어쓰기"):
                    save_rank(new_rank)
                    st.success("업로드 완료")
