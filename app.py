import streamlit as st
import pandas as pd
import os
import random
import itertools
from datetime import datetime

# --- 1. 데이터 저장소 및 초기화 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_members():
    """멤버 데이터를 불러오고 랭킹 및 변동을 정밀 계산합니다."""
    if os.path.exists(MEMBERS_FILE):
        try:
            df = pd.read_csv(MEMBERS_FILE).fillna("")
            # 필수 컬럼 강제 생성 및 타입 변환
            for c in ['4월 포인트', '3월 포인트', '부과점', '랭킹']:
                df[c] = pd.to_numeric(df.get(c, 0), errors='coerce').fillna(0).astype(int)
            
            # [기능 확인] 랭킹 변동 로직: 4월이 높으면 🔺 (찬혁님 지적 반영)
            df['변동치'] = df['4월 포인트'] - df['3월 포인트']
            df['상태'] = df['변동치'].apply(lambda x: "🔺" if x > 0 else ("🔻" if x < 0 else "—"))
            
            # [기능 확인] 총점 계산: 4월 포인트 + 부과점 (비고/부과점 상승 포인트 반영)
            df['총점'] = df['4월 포인트'] + df['부과점']
            return df
        except:
            pass
    return pd.DataFrame(columns=['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '총점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 시인성 강화 UI 설정 (글자색 문제 해결) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    /* 배경 흰색, 글자 검은색 강제 고정 */
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, h4, h5, h6, p, label, span, div, .stMarkdown { 
        color: #111111 !important; 
    }
    /* 테이블 가독성 */
    .stTable, .stDataFrame { background-color: #FFFFFF !important; color: #111111 !important; }
    /* 매치 카드 스타일 */
    .match-card {
        border: 2px solid #002366;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
        background-color: #F8F9FA;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.1);
    }
    .team-box { font-size: 1.2rem; font-weight: bold; color: #002366 !important; text-align: center; }
    .vs-tag { color: #E63946 !important; font-weight: 900; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 제어판 ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>🎾 두류테니스</h1>", unsafe_allow_html=True)
    
    # [기능 확인] 지나간 대회 수정 가능하도록 목록 로드
    all_events = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    selected_event = st.selectbox("📅 대회 선택 (과거 수정 가능)", ["선택 안함"] + all_events)
    
    # [기능 확인] 관리자 암호 및 메뉴 분리
    admin_pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (admin_pw == "0502")
    
    menu = st.radio("메뉴 이동", ["전체랭킹", "대진 및 경기현황", "경기 결과"] + (["관리자 설정"] if is_admin else []))

EV_PATH = os.path.join(DATA_DIR, selected_event) if selected_event != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 정밀 구현 ---

# [1] 전체 랭킹 (화살표 및 부과점 로직)
if menu == "전체랭킹":
    st.markdown("<h1 style='text-align:center;'>🥇 실시간 클럽 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    # 필요한 컬럼만 가독성 있게 배치
    display_cols = ['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '총점', '비고']
    st.table(df[display_cols])

# [2] 대진 및 경기현황 (지나간 대회 수정 + 점수 대칭 저장)
elif menu == "대진 및 경기현황":
    if not MATCH_FILE or not os.path.exists(MATCH_FILE):
        st.info("왼쪽 사이드바에서 대회를 선택하거나 관리자 설정에서 대진표를 생성해 주세요.")
    else:
        st.markdown(f"<h1 style='text-align:center;'>📅 {selected_event} 경기 현황</h1>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        
        for idx, row in df_m.iterrows():
            with st.container():
                st.markdown(f"""
                <div class='match-card'>
                    <div style='text-align:center; font-weight:bold; margin-bottom:10px;'>[{row['그룹']}] 제 {row['순서']} 경기</div>
                    <div style='display:flex; justify-content:space-around; align-items:center;'>
                        <div class='team-box'>{row['팀A']}</div>
                        <div class='vs-tag'>VS</div>
                        <div class='team-box'>{row['팀B']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2, c3 = st.columns([2, 1, 2])
                # [기능 확인] 개별 점수 입력 및 대칭 반영
                score_a = c1.number_input(f"{row['팀A']} 득점", 0, 10, int(row['A점수']), key=f"sa_{idx}")
                score_b = c3.number_input(f"{row['팀B']} 득점", 0, 10, int(row['B점수']), key=f"sb_{idx}")
                
                if st.button(f"{idx+1}번 경기 결과 확정", key=f"btn_{idx}"):
                    df_m.at[idx, 'A점수'], df_m.at[idx, 'B점수'], df_m.at[idx, '완료'] = score_a, score_b, 1
                    save_data(df_m, MATCH_FILE)
                    st.success(f"{idx+1}번 경기 기록 완료!")
                    st.rerun()

# [3] 경기 결과 (매트릭스 표)
elif menu == "경기 결과":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        st.markdown(f"<h1 style='text-align:center;'>📊 {selected_event} 스코어보드</h1>", unsafe_allow_html=True)
        df_res = pd.read_csv(MATCH_FILE)
        # 그룹별 데이터프레임 요약 노출
        for g in df_res['그룹'].unique():
            st.subheader(f"📍 {g} 상세 결과")
            st.dataframe(df_res[df_res['그룹'] == g], use_container_width=True, hide_index=True)

# [4] 관리자 설정 (모든 요구 기능 포함)
elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1 style='text-align:center;'>⚙️ 관리자 시스템</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📂 대회 및 회원 관리", "⚔️ 대진표 자동 생성", "📈 포인트 최종 반영"])
    
    with t1:
        st.subheader("1. 대회 관리 및 엑셀 업로드")
        col1, col2 = st.columns(2)
        with col1:
            new_ev = st.text_input("새 대회 이름 (예: 2026_05_정기대회)")
            if st.button("새 대회 생성"):
                os.makedirs(os.path.join(DATA_DIR, new_ev), exist_ok=True)
                st.success("대회 폴더가 생성되었습니다.")
        
        with col2:
            # [기능 확인] 엑셀 다중 확장자 지원 (xlsx, xls, csv)
            up_file = st.file_uploader("회원 명단 업로드", type=['xlsx', 'xls', 'csv'])
            if up_file:
                if up_file.name.endswith('csv'): df_up = pd.read_csv(up_file)
                else: df_up = pd.read_excel(up_file)
                if st.button("업로드 파일로 전체 멤버 교체"):
                    save_data(df_up, MEMBERS_FILE)
                    st.rerun()

        st.divider()
        st.subheader("2. 참가자 개별 수정 및 전체 선택")
        df_curr_mem = load_members()
        # [기능 확인] 개인별 수정 기능 (에디터)
        edited_mem = st.data_editor(df_curr_mem, use_container_width=True, num_rows="dynamic", key="mem_edit")
        if st.button("수정사항 저장"):
            save_data(edited_mem, MEMBERS_FILE)
            st.success("회원 정보가 저장되었습니다.")

    with t2:
        st.subheader("대진표 자동 생성 알고리즘")
        if not selected_event or selected_event == "선택 안함":
            st.error("왼쪽에서 대진표를 생성할 대회를 먼저 선택하세요.")
        else:
            # [기능 확인] 텍스트/체크박스 혼합 참가자 선택
            all_names = df_curr_mem['성명'].tolist()
            st.write("✅ 참가자 선택 (랭킹순 정렬됨)")
            
            c1, c2 = st.columns([1, 1])
            with c1:
                # [기능 확인] 전체 선택 기능
                select_all = st.checkbox("전체 인원 자동 선택")
                chosen_names = []
                for name in all_names:
                    if st.checkbox(name, value=select_all, key=f"chk_{name}"):
                        chosen_names.append(name)
            
            with c2:
                st.write("✍️ 이름 직접 입력 (쉼표 구분)")
                manual_input = st.text_area("명단 복사/붙여넣기")
                if manual_input:
                    manual_list = [n.strip() for n in manual_input.split(',') if n.strip()]
                    chosen_names = list(set(chosen_names + manual_list))
            
            st.write(f"**최종 참가 확정({len(chosen_names)}명):** {', '.join(chosen_names)}")
            
            gc1, gc2 = st.columns(2)
            g_num = gc1.number_input("조 개수", 1, 10, 1)
            g_type = gc2.selectbox("매칭 알고리즘", ["고정페어 (랭킹순 스네이크)", "KDK 랜덤"])
            
            if st.button("⚔️ 대진표 생성 및 저장"):
                # 랭킹 데이터 결합
                sel_df = df_curr_mem[df_curr_mem['성명'].isin(chosen_names)].sort_values('랭킹')
                p_list = sel_df['성명'].tolist()
                
                matches = []
                for g in range(g_num):
                    g_tag = f"{chr(65+g)}조"
                    g_mems = p_list[g::g_num] # 랭킹순 분배
                    
                    if g_type == "고정페어 (랭킹순 스네이크)":
                        # [기능 확인] 스네이크 방식: 1위+최하위 매칭
                        pairs = []
                        temp = g_mems[:]
                        while len(temp) >= 2:
                            pairs.append(f"{temp.pop(0)} / {temp.pop(-1)}")
                        for idx, combo in enumerate(itertools.combinations(pairs, 2)):
                            matches.append({"그룹": g_tag, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수":0, "B점수":0, "완료":0})
                    else:
                        # KDK 랜덤 매칭
                        random.shuffle(g_mems)
                        for idx, combo in enumerate(itertools.combinations(g_mems, 4)):
                            if idx >= len(g_mems) * 1.5: break
                            p = list(combo)
                            matches.append({"그룹": g_tag, "순서": idx+1, "팀A": f"{p[0]},{p[1]}", "팀B": f"{p[2]},{p[3]}", "A점수":0, "B점수":0, "완료":0})
                
                save_data(pd.DataFrame(matches), MATCH_FILE)
                st.success(f"{selected_event} 대진표 생성 완료!")

    with t3:
        st.subheader("대회 포인트 랭킹 반영")
        st.warning("이 기능은 대회의 점수를 현재 회원들의 '4월 포인트'에 합산합니다.")
        if st.button("현재 대회 결과 일괄 반영하기"):
            if MATCH_FILE and os.path.exists(MATCH_FILE):
                m_results = pd.read_csv(MATCH_FILE)
                m_results = m_results[m_results['완료'] == 1]
                
                df_rank = load_members()
                for _, r in m_results.iterrows():
                    # 승점 계산 (승리 10, 패배 5 예시)
                    for t, s_my, s_op in [(r['팀A'], r['A점수'], r['B점수']), (r['팀B'], r['B점수'], r['A점수'])]:
                        players = [p.strip() for p in t.replace('/', ',').split(',')]
                        for p in players:
                            if p in df_rank['성명'].values:
                                idx = df_rank[df_rank['성명'] == p].index[0]
                                df_rank.at[idx, '4월 포인트'] += (10 if s_my > s_op else 5)
                
                save_data(df_rank, MEMBERS_FILE)
                st.success("랭킹 포인트 업데이트가 완료되었습니다!")
