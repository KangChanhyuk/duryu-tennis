import streamlit as st
import pandas as pd
import os
import random
import itertools
import io

# --- 1. 데이터 저장 및 로드 설정 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        try:
            df = pd.read_csv(MEMBERS_FILE).fillna("")
            # 필수 컬럼 보장 및 타입 변환
            cols = ['랭킹', '성명', '4월 포인트', '3월 포인트', '부과점', '비고']
            for c in cols:
                if c not in df.columns:
                    df[c] = 0 if '포인트' in c or c in ['랭킹', '부과점'] else ""
            df['랭킹'] = pd.to_numeric(df['랭킹'], errors='coerce').fillna(999).astype(int)
            df['4월 포인트'] = pd.to_numeric(df['4월 포인트'], errors='coerce').fillna(0).astype(int)
            df['3월 포인트'] = pd.to_numeric(df['3월 포인트'], errors='coerce').fillna(0).astype(int)
            df['변동'] = df['3월 포인트'] - df['4월 포인트']
            return df
        except:
            pass
    return pd.DataFrame(columns=['랭킹', '성명', '4월 포인트', '3월 포인트', '변동', '부과점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. UI/UX 디자인 (글자색 시인성 확보) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    /* 배경과 글자색 강제 지정 (가시성 해결) */
    .stApp { background-color: #FFFFFF !important; }
    h1, h2, h3, p, span, label, .stMarkdown { color: #111111 !important; text-align: center; }
    
    /* 데이터프레임 및 테이블 스타일 */
    .stDataFrame, .stTable { background-color: #FFFFFF !important; border: 1px solid #DDDDDD; }
    
    /* 매치 카드 디자인 */
    .match-card {
        border: 2px solid #002366;
        border-radius: 12px;
        padding: 20px;
        margin: 15px auto;
        background-color: #F8F9FA;
        max-width: 800px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .team-name { font-size: 1.3rem; font-weight: bold; color: #002366 !important; }
    .vs-text { font-size: 1.5rem; font-weight: 900; color: #E63946 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 제어 ---
with st.sidebar:
    st.markdown("# 🎾 두류테니스")
    events = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    selected_event = st.selectbox("📅 대회 선택", ["선택 안함"] + events)
    
    pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (pw == "0502")
    
    menu = st.radio("메뉴", ["전체랭킹", "대진 및 경기현황", "경기 결과", "경기 기록"] + (["관리자 설정"] if is_admin else []))

EV_PATH = os.path.join(DATA_DIR, selected_event) if selected_event != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 상세 구현 ---

# [1] 전체 랭킹
if menu == "전체랭킹":
    st.markdown("<h1>🥇 클럽 전체 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    df['상태'] = df['변동'].apply(lambda x: "🔺" if x > 0 else ("🔻" if x < 0 else "—"))
    st.table(df[['랭킹', '상태', '성명', '4월 포인트', '부과점', '비고']])

# [2] 대진 및 경기현황
elif menu == "대진 및 경기현황":
    if not MATCH_FILE or not os.path.exists(MATCH_FILE):
        st.info("대회를 선택하거나 대진표를 생성해 주세요.")
    else:
        st.markdown(f"<h1>📅 {selected_event} 현황</h1>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        for i, row in df_m.iterrows():
            with st.container():
                st.markdown(f"""
                <div class='match-card'>
                    <p style='margin-bottom:10px;'><b>GROUP {row['그룹']} - MATCH {row['순서']}</b></p>
                    <div style='display:flex; align-items:center; justify-content:space-between;'>
                        <div style='flex:1;' class='team-name'>{row['팀A']}</div>
                        <div style='flex:0.5;' class='vs-text'>VS</div>
                        <div style='flex:1;' class='team-name'>{row['팀B']}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                c1, c2, c3 = st.columns([2, 1, 2])
                sc_a = c1.number_input(f"{row['팀A']} 점수", 0, 10, int(row['A점수']), key=f"a_{i}")
                sc_b = c3.number_input(f"{row['팀B']} 점수", 0, 10, int(row['B점수']), key=f"b_{i}")
                if st.button(f"{i+1}번 경기 결과 저장", key=f"btn_{i}"):
                    df_m.at[i, 'A점수'], df_m.at[i, 'B점수'], df_m.at[i, '완료'] = sc_a, sc_b, 1
                    save_data(df_m, MATCH_FILE)
                    st.rerun()

# [3] 경기 결과
elif menu == "경기 결과":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        st.markdown("<h1>📊 대회 스코어보드</h1>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        for g in df_m['그룹'].unique():
            st.subheader(f"📍 {g} 결과")
            st.dataframe(df_m[df_m['그룹'] == g], use_container_width=True)

# [4] 관리자 설정 (요청 기능 집중 구현)
elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 관리자 시스템</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📂 대회/참가자 관리", "⚔️ 대진표 자동생성", "📈 데이터 업데이트"])
    
    with t1:
        st.subheader("1. 대회 생성 및 엑셀 업로드")
        col_c, col_u = st.columns(2)
        with col_c:
            new_name = st.text_input("새 대회명")
            if st.button("대회 생성"):
                os.makedirs(os.path.join(DATA_DIR, new_name), exist_ok=True)
                st.success("대회 생성 완료")
        with col_u:
            up_file = st.file_uploader("엑셀/CSV 업로드 (전체 멤버 교체)", type=['xlsx', 'xls', 'csv'])
            if up_file:
                df_up = pd.read_csv(up_file) if up_file.name.endswith('csv') else pd.read_excel(up_file)
                if st.button("DB 전체 교체 실행"):
                    save_data(df_up, MEMBERS_FILE); st.rerun()

        st.divider()
        st.subheader("2. 참가자 개별 수정 및 선택")
        df_edit = load_members()
        # 전체 선택 기능 및 개별 수정 가능 에디터
        st.info("아래 표에서 직접 수정하거나 행을 선택하여 삭제할 수 있습니다.")
        edited_df = st.data_editor(df_edit, use_container_width=True, num_rows="dynamic", key="mem_editor")
        if st.button("참가자 명단 수정사항 저장"):
            save_data(edited_df, MEMBERS_FILE); st.success("저장 완료")

    with t2:
        if not EV_PATH: st.error("왼쪽 메뉴에서 대회를 먼저 선택하세요.")
        else:
            st.subheader(f"[{selected_event}] 대진표 구성")
            all_mems = load_members().sort_values('랭킹')
            
            # 참가자 선택 (텍스트로 입력 OR 체크박스 선택)
            c1, c2 = st.columns(2)
            with c1:
                st.write("✅ 체크박스로 선택")
                sel_names = []
                # 전체 선택 체크박스
                all_select = st.checkbox("전체 선택")
                for _, r in all_mems.iterrows():
                    if st.checkbox(f"{r['성명']} (Rank {r['랭킹']})", value=all_select):
                        sel_names.append(r['성명'])
            with c2:
                st.write("✍️ 텍스트로 대량 입력 (쉼표 구분)")
                text_input = st.text_area("이름을 직접 입력하세요")
                if text_input:
                    sel_names = list(set(sel_names + [n.strip() for n in text_input.split(',') if n.strip()]))
            
            st.write(f"**현재 선택된 인원({len(sel_names)}명):** {', '.join(sel_names)}")
            
            cc1, cc2, cc3 = st.columns(3)
            g_count = cc1.number_input("그룹 수", 1, 5, 1)
            mode = cc2.selectbox("방식", ["고정페어 (1위+최하위)", "KDK (랜덤)"])
            
            if st.button("⚔️ 대진표 생성 및 대회 시작"):
                # 랭킹순 정렬
                sel_df = all_mems[all_mems['성명'].isin(sel_names)].sort_values('랭킹')
                p_list = sel_df['성명'].tolist()
                
                final_matches = []
                for g in range(g_count):
                    gn = chr(65+g)
                    g_mems = p_list[g::g_count] # 랭킹순 그룹 분배
                    
                    if mode == "고정페어 (1위+최하위)":
                        pairs = []
                        temp = g_mems[:]
                        while len(temp) >= 2:
                            pairs.append(f"{temp.pop(0)} / {temp.pop(-1)}")
                        for idx, c in enumerate(itertools.combinations(pairs, 2)):
                            final_matches.append({"그룹":gn, "순서":idx+1, "팀A":c[0], "팀B":c[1], "A점수":0, "B점수":0, "완료":0})
                    else: # KDK 랜덤
                        random.shuffle(g_mems)
                        for idx, c in enumerate(itertools.combinations(g_mems, 4)):
                            if idx > len(g_mems)*1.5: break
                            final_matches.append({"그룹":gn, "순서":idx+1, "팀A":f"{c[0]},{c[1]}", "팀B":f"{c[2]},{c[3]}", "A점수":0, "B점수":0, "완료":0})
                
                save_data(pd.DataFrame(final_matches), MATCH_FILE)
                st.success("대진표가 성공적으로 생성되었습니다!")

    with t3:
        st.subheader("결과 랭킹 자동 반영")
        if MATCH_FILE and os.path.exists(MATCH_FILE):
            if st.button("이 대회의 모든 결과를 전체 랭킹에 합산"):
                df_rank = load_members()
                df_curr = pd.read_csv(MATCH_FILE)
                # 단순 합산 로직 (승리 10, 패배 5)
                for _, r in df_curr[df_curr['완료']==1].iterrows():
                    for t, s_my, s_op in [(r['팀A'], r['A점수'], r['B점수']), (r['팀B'], r['B점수'], r['A점수'])]:
                        players = [p.strip() for p in t.replace('/', ',').split(',')]
                        for p in players:
                            if p in df_rank['성명'].values:
                                idx = df_rank[df_rank['성명']==p].index[0]
                                df_rank.at[idx, '4월 포인트'] += (10 if s_my > s_op else 5)
                save_data(df_rank, MEMBERS_FILE); st.success("랭킹 포인트 업데이트 완료")
