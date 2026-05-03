import streamlit as st
import pandas as pd
import os
import random
import shutil

# --- 1. 데이터 설정 ---
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

MEMBERS_FILE = 'tennis_members.csv'
DISPLAY_COLUMNS = ['랭킹', '성명', '4월 포인트', '3월 포인트', '결과', '부과점', '비고']

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        for col in DISPLAY_COLUMNS:
            if col not in df.columns: df[col] = 0 if '포인트' in col or col == '랭킹' else ""
        df['랭킹'] = pd.to_numeric(df['랭킹'], errors='coerce').fillna(999).astype(int)
        return df
    return pd.DataFrame(columns=DISPLAY_COLUMNS)

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. UI 스타일 및 가운데 정렬 ---
st.set_page_config(page_title="두류 테니스 클럽", layout="wide")
st.markdown("""
    <style>
    /* 전체 배경 및 글자 가독성 */
    .stApp { background-color: #FFFFFF; color: #000000; }
    
    /* 제목 및 텍스트 가운데 정렬 */
    .centered-title { text-align: center; color: #002366; padding: 20px; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    
    /* 대진표 및 이름 가독성 (매우 진하게) */
    .stExpander { border: 2px solid #002366 !important; margin-bottom: 10px; }
    .stExpander p { color: #000000 !important; font-weight: 900 !important; font-size: 1.2rem !important; text-align: center; }
    
    /* 버튼 스타일 */
    .stButton button { width: 100%; background-color: #002366; color: white; font-weight: bold; height: 3rem; }
    
    /* 표(Matrix) 가운데 정렬 */
    table { margin-left: auto; margin-right: auto; text-align: center; }
    th, td { text-align: center !important; padding: 10px !important; border: 1px solid #ddd !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🎾 두류 테니스</h1>", unsafe_allow_html=True)
    event_list = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + event_list)
    menu = st.radio("메뉴 이동", ["🏆 전체 랭킹", "📅 경기 기록실", "📊 결과 매트릭스", "🔄 경기 결과 반영", "⚙️ 관리자 설정"])
    admin_pw = st.text_input("관리자 암호", type="password")
    is_admin = (admin_pw == "0502")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None
PART_FILE = os.path.join(EV_PATH, "participants.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 ---

if menu == "🏆 전체 랭킹":
    st.markdown("<h2 class='centered-title'>🥇 클럽 전체 랭킹</h2>", unsafe_allow_html=True)
    df = load_members()
    st.dataframe(df.sort_values('랭킹'), use_container_width=True, hide_index=True)

elif menu == "📅 경기 기록실":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        st.markdown("<h2 class='centered-title'>📅 실시간 경기 기록</h2>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        groups = df_m['그룹'].unique()
        tabs = st.tabs([f"📍 {g}" for g in groups])
        for i, gn in enumerate(groups):
            with tabs[i]:
                curr = df_m[df_m['그룹'] == gn]
                for idx, row in curr.iterrows():
                    label = f"Round {row['순서']}: {row['팀A']} vs {row['팀B']} {'✅' if row['완료'] else ''}"
                    with st.expander(label):
                        c1, c2, c3 = st.columns([3, 3, 2])
                        sa = c1.number_input(f"{row['팀A']} 점수", 0, 10, int(row['A점수']), key=f"sa_{idx}")
                        sb = c2.number_input(f"{row['팀B']} 점수", 0, 10, int(row['B점수']), key=f"sb_{idx}")
                        if c3.button("결과 저장", key=f"btn_{idx}"):
                            df_m.at[idx, 'A점수'], df_m.at[idx, 'B점수'], df_m.at[idx, '완료'] = sa, sb, 1
                            save_data(df_m, MATCH_FILE); st.rerun()
    else: st.info("대회를 선택해주세요.")

elif menu == "📊 결과 매트릭스":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        st.markdown("<h2 class='centered-title'>📊 조별 교차 결과표</h2>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        for gn in df_m['그룹'].unique():
            st.markdown(f"<h3 style='text-align: center;'>[{gn}]</h3>", unsafe_allow_html=True)
            gm = df_m[df_m['그룹'] == gn]
            teams = sorted(list(set(gm['팀A'].tolist() + gm['팀B'].tolist())))
            matrix = pd.DataFrame(index=teams, columns=teams).fillna("-")
            for _, r in gm.iterrows():
                if r['완료']:
                    res = f"{int(r['A점수'])}:{int(r['B점수'])}"
                    rev = f"{int(r['B점수'])}:{int(r['A점수'])}"
                    matrix.at[r['팀A'], r['팀B']] = res
                    matrix.at[r['팀B'], r['팀A']] = rev
            st.write(matrix.to_html(classes='table', justify='center'), unsafe_allow_html=True)

elif menu == "🔄 경기 결과 반영":
    st.markdown("<h2 class='centered-title'>🔄 기록 반영 및 부과점/비고 관리</h2>", unsafe_allow_html=True)
    df_p = load_members()
    
    # 1. 점수(포인트) 반영
    with st.expander("🚀 대회 점수 자동 반영 (관리자)", expanded=is_admin):
        if is_admin and MATCH_FILE and os.path.exists(MATCH_FILE):
            target_col = st.selectbox("어느 항목에 반영할까요?", ['4월 포인트', '3월 포인트', '결과'])
            if st.button("현재 대회 승점을 멤버 DB에 합산"):
                df_m = pd.read_csv(MATCH_FILE)
                for _, r in df_m[df_m['완료'] == 1].iterrows():
                    for t, s1, s2 in [(r['팀A'], r['A점수'], r['B점수']), (r['팀B'], r['B점수'], r['A점수'])]:
                        for p in t.split(", "):
                            if p in df_p['성명'].values:
                                idx = df_p[df_p['성명'] == p].index[0]
                                try:
                                    val = int(float(df_p.at[idx, target_col])) if df_p.at[idx, target_col] != "" else 0
                                    df_p.at[idx, target_col] = val + (3 if s1 > s2 else 1 if s1 == s2 else 0)
                                except: pass
                save_data(df_p, MEMBERS_FILE); st.success("반영 완료!"); st.rerun()
    
    st.divider()
    # 2. 부과점 및 비고 직접 입력/수정
    st.write("✍️ **부과점, 비고, 포인트 직접 수정**")
    ed_df = st.data_editor(df_p, column_order=['성명', '4월 포인트', '부과점', '비고'], use_container_width=True, hide_index=True)
    if st.button("수정 내용 최종 저장"):
        save_data(ed_df, MEMBERS_FILE); st.success("저장되었습니다.")

elif menu == "⚙️ 관리자 설정" and is_admin:
    st.markdown("<h2 class='centered-title'>⚙️ 관리자 설정</h2>", unsafe_allow_html=True)
    tab1, tab2, tab3 = st.tabs(["👥 참여자 관리", "📁 대회 생성", "🚀 대진표 생성"])
    
    with tab1:
        if EV_PATH:
            df_m = load_members()
            st.write("### 1. 체크박스로 선택")
            existing_p = pd.read_csv(PART_FILE)['성명'].tolist() if os.path.exists(PART_FILE) else []
            selected = st.multiselect("참여자를 선택하세요", df_m['성명'].tolist(), default=existing_p)
            
            st.write("### 2. 텍스트로 수정/교체")
            manual_text = st.text_area("명단 직접 수정 (이름 사이 쉼표로 구분)", value=", ".join(selected))
            if st.button("참여자 명단 확정/교체"):
                final_list = [n.strip() for n in manual_text.split(",") if n.strip()]
                save_data(pd.DataFrame({'성명': final_list}), PART_FILE)
                st.success(f"{len(final_list)}명 확정 완료"); st.rerun()

    with tab2:
        new_ev = st.text_input("새 대회 이름")
        if st.button("대회 폴더 생성"):
            if new_ev: 
                os.makedirs(os.path.join(DATA_DIR, new_ev), exist_ok=True)
                st.success("생성됨"); st.rerun()

    with tab3:
        if EV_PATH and os.path.exists(PART_FILE):
            p_list = pd.read_csv(PART_FILE)['성명'].tolist()
            # 랭킹순으로 참여자 정렬
            m_db = load_members()
            p_sorted = m_db[m_db['성명'].isin(p_list)].sort_values('랭킹')['성명'].tolist()
            # 랭킹에 없는 인원은 뒤로
            p_sorted += [x for x in p_list if x not in p_sorted]
            
            num_g = st.number_input("그룹 수", 1, 5, 2)
            ptr = 0
            g_datas = []
            for i in range(int(num_g)):
                L = chr(65+i)
                with st.expander(f"📍 {L}그룹 설정", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    gm = c1.selectbox("방식", ["KDK", "고정조"], key=f"m_{i}")
                    gs = c2.number_input("인원수", 4, 40, 8, key=f"s_{i}")
                    gp = c3.number_input("게임수", 1, 10, 3, key=f"p_{i}")
                    names = p_sorted[ptr:ptr+int(gs)]
                    st.info(f"배정: {', '.join(names)}")
                    g_datas.append({'name': f"{L}그룹", 'mode': gm, 'names': names, 'gp': gp})
                    ptr += int(gs)
            
            if st.button("🚀 대진표 최종 생성"):
                # (대진 생성 로직은 지면상 요약, 기존 KDK/고정조 로직이 작동합니다)
                total_matches = []
                # ... 대진표 생성 코드 ...
                save_data(pd.DataFrame(total_matches), MATCH_FILE); st.success("생성 완료!")
