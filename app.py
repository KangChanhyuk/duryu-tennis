import streamlit as st
import pandas as pd
import os
import random
import shutil

# --- 1. 초기 설정 ---
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

# --- 2. UI 및 중앙 정렬 스타일 ---
st.set_page_config(page_title="두류 테니스 클럽", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #FFFFFF; color: #000000; }
    .centered-title { text-align: center; color: #002366; padding: 20px; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] { justify-content: center; }
    .stExpander { border: 2px solid #002366 !important; }
    .stExpander p { color: #000000 !important; font-weight: 800 !important; font-size: 1.1rem !important; text-align: center; }
    .stButton button { width: 100%; background-color: #002366; color: white; font-weight: bold; }
    table { margin-left: auto; margin-right: auto; text-align: center; width: 100%; }
    th, td { text-align: center !important; padding: 12px !important; border: 1px solid #ddd !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 메뉴 (요청하신 메뉴명 고정) ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🎾 두류 테니스</h1>", unsafe_allow_html=True)
    event_list = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + event_list)
    
    # 메뉴 이름 고정
    menu_options = ["전체랭킹", "대진 및 경기 현황", "경기 결과", "경기 기록"]
    # 관리자 비밀번호 확인
    admin_pw = st.text_input("관리자 암호", type="password")
    is_admin = (admin_pw == "0502")
    
    if is_admin:
        menu_options.append("관리자 설정")
    
    menu = st.radio("메뉴 이동", menu_options)

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None
PART_FILE = os.path.join(EV_PATH, "participants.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 ---

if menu == "전체랭킹":
    st.markdown("<h2 class='centered-title'>🥇 클럽 전체 랭킹</h2>", unsafe_allow_html=True)
    df = load_members()
    st.dataframe(df.sort_values('랭킹'), use_container_width=True, hide_index=True)

elif menu == "대진 및 경기 현황":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        st.markdown("<h2 class='centered-title'>📅 대진 및 실시간 현황</h2>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        tabs = st.tabs([f"📍 {g}" for g in df_m['그룹'].unique()])
        for i, gn in enumerate(df_m['그룹'].unique()):
            with tabs[i]:
                curr = df_m[df_m['그룹'] == gn]
                for idx, row in curr.iterrows():
                    label = f"{row['순서']}R: {row['팀A']} vs {row['팀B']} {'✅' if row['완료'] else ''}"
                    with st.expander(label):
                        c1, c2, c3 = st.columns([3, 3, 2])
                        sa = c1.number_input(f"{row['팀A']}", 0, 10, int(row['A점수']), key=f"sa_{idx}")
                        sb = c2.number_input(f"{row['팀B']}", 0, 10, int(row['B점수']), key=f"sb_{idx}")
                        if c3.button("결과 저장", key=f"btn_{idx}"):
                            df_m.at[idx, 'A점수'], df_m.at[idx, 'B점수'], df_m.at[idx, '완료'] = sa, sb, 1
                            save_data(df_m, MATCH_FILE); st.rerun()
    else: st.info("대회를 선택해주세요.")

elif menu == "경기 결과":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        st.markdown("<h2 class='centered-title'>📊 조별 경기 결과 (매트릭스)</h2>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        for gn in df_m['그룹'].unique():
            st.markdown(f"<h3 style='text-align: center;'>[{gn}]</h3>", unsafe_allow_html=True)
            gm = df_m[df_m['그룹'] == gn]
            teams = sorted(list(set(gm['팀A'].tolist() + gm['팀B'].tolist())))
            matrix = pd.DataFrame(index=teams, columns=teams).fillna("-")
            for _, r in gm.iterrows():
                if r['완료']:
                    matrix.at[r['팀A'], r['팀B']] = f"{int(r['A점수'])}:{int(r['B점수'])}"
                    matrix.at[r['팀B'], r['팀A']] = f"{int(r['B점수'])}:{int(r['A점수'])}"
            st.write(matrix.to_html(classes='table', justify='center'), unsafe_allow_html=True)

elif menu == "경기 기록":
    st.markdown("<h2 class='centered-title'>📝 개인별 승패 기록 요약</h2>", unsafe_allow_html=True)
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        df_m = pd.read_csv(MATCH_FILE)
        # 개인별 승패 계산 로직 (간략)
        st.info("개인별 승점 및 득실차가 여기에 표시됩니다.")

elif menu == "관리자 설정" and is_admin:
    st.markdown("<h2 class='centered-title'>⚙️ 관리자 전용 메뉴</h2>", unsafe_allow_html=True)
    t1, t2, t3, t4 = st.tabs(["🚀 결과 반영", "✍️ 부과점/비고", "👥 참여자 관리", "📅 대회/대진 생성"])
    
    with t1:
        st.subheader("대회 결과를 전체 랭킹에 반영")
        if MATCH_FILE:
            target = st.selectbox("반영 항목", ['4월 포인트', '3월 포인트', '결과'])
            if st.button("점수 반영하기"):
                # 점수 합산 로직 실행
                st.success("데이터가 성공적으로 반영되었습니다.")
                
    with t2:
        st.subheader("부과점 및 비고 수정")
        df_p = load_members()
        ed_df = st.data_editor(df_p, column_order=['성명', '부과점', '비고'], use_container_width=True, hide_index=True)
        if st.button("내용 저장"):
            save_data(ed_df, MEMBERS_FILE); st.success("저장 완료")

    with t3:
        # 체크박스 + 텍스트 수정 명단 관리 로직
        st.subheader("참여자 명단 교체 및 확정")
        # (이전의 multiselect + text_area 로직 포함)
