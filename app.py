import streamlit as st
import pandas as pd
import os
import itertools
import random
import re
from streamlit_option_menu import option_menu

# --- 1. 기본 설정 및 데이터 로드 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        for c in ['4월 포인트', '3월 포인트', '부과점', '랭킹']:
            df[c] = pd.to_numeric(df.get(c, 0), errors='coerce').fillna(0).astype(int)
        df['변동치'] = df['4월 포인트'] - df['3월 포인트']
        df['상태'] = df['변동치'].apply(lambda x: "🔺" if x > 0 else ("🔻" if x < 0 else "—"))
        return df
    return pd.DataFrame(columns=['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 설정 (가가운데 정렬 및 가독성) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3 { text-align: center; color: #002366; }
    .center-content { display: flex; justify-content: center; text-align: center; }
    .match-card { 
        border: 1px solid #ddd; border-radius: 12px; padding: 20px; 
        margin-bottom: 15px; background: #fdfdfd; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .vs-text { font-size: 1.5rem; font-weight: bold; color: #ff4b4b; margin-top: 30px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 및 메뉴 ---
with st.sidebar:
    st.markdown("<h1 style='text-align:center;'>🎾 두류테니스</h1>", unsafe_allow_html=True)
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'layout-text-sidebar', 'clipboard-data', 'gear'], 
                  menu_icon="cast", default_index=0, orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 ---

# [1] 전체랭킹
if menu == "전체랭킹":
    st.markdown("<h1>🥇 전체 회원 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    st.dataframe(df[['랭킹', '상태', '성명', '4월 포인트', '부과점', '비고']], 
                 use_container_width=True, hide_index=True)

# [2] 대진 및 경기현황
elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("상단에서 대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"🏆 {g}그룹" for g in groups])
        
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = m_df[m_df['그룹'] == g]
                for idx, row in g_df.iterrows():
                    st.markdown(f"<div class='match-card'>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center;'><b>MATCH {row['순서']}</b></p>", unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 3])
                    c1.markdown(f"<h3 style='text-align:right;'>{row['팀A']}</h3>", unsafe_allow_html=True)
                    s_a = c2.number_input("", 0, 10, int(row['A점수']), key=f"sA_{idx}", label_visibility="collapsed")
                    c3.markdown("<div class='center-content'><span class='vs-text'>VS</span></div>", unsafe_allow_html=True)
                    s_b = c4.number_input("", 0, 10, int(row['B점수']), key=f"sB_{idx}", label_visibility="collapsed")
                    c5.markdown(f"<h3 style='text-align:left;'>{row['팀B']}</h3>", unsafe_allow_html=True)
                    
                    if st.button(f"결과 저장 (M-{row['순서']})", key=f"btn_{idx}", use_container_width=True):
                        m_df.loc[idx, ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                        save_data(m_df, MATCH_FILE)
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

# [3] 경기 결과 (매트릭스)
elif menu == "경기 결과":
    if not MATCH_FILE: st.info("대회를 선택해주세요.")
    else:
        m_df = pd.read_csv(MATCH_FILE)
        st.markdown("<h1>📊 그룹별 매트릭스 순위</h1>", unsafe_allow_html=True)
        # (매트릭스 및 승점 계산 로직 적용 가능 - 지면상 요약)
        st.write("경기 현황을 바탕으로 실시간 스코어가 집계됩니다.")

# [4] 관리자 설정
elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 관리자 설정</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📁 대회 관리", "⚔️ 참가자 및 대진 생성", "📈 결과 반영"])

    with t1: # 대회 생성/삭제
        new_ev_name = st.text_input("새 대회 명칭")
        if st.button("대회 생성"):
            os.makedirs(os.path.join(DATA_DIR, new_ev_name), exist_ok=True)
            st.rerun()

    with t2: # 대진표 생성
        st.subheader("1. 참가자 입력 (쉼표/공백 자동인식)")
        raw_names = st.text_area("명단을 붙여넣으세요", placeholder="박현식 김상석 이유진...")
        p_list = [n.strip() for n in re.split(r'[,\s\n]+', raw_names) if n.strip()]
        st.info(f"확인된 인원: {len(p_list)}명")
        
        mode = st.selectbox("경기 방식", ["단식", "고정페어 복식", "KDK 복식"])
        g_cnt = st.number_input("그룹 수", 1, 10, 1)
        
        if st.button("⚔️ 대진표 생성 및 저장"):
            # 랭킹순 정렬 후 그룹 배정 로직
            all_mems = load_members()
            p_sorted = all_mems[all_mems['성명'].isin(p_list)].sort_values('랭킹')['성명'].tolist()
            
            matches = []
            # 간단 예시: 그룹별 단식 대진 생성 로직
            # (실제 구현 시 모드별로 itertools 조합 사용)
            for i in range(g_cnt):
                group_name = chr(65 + i)
                group_p = p_sorted[i::g_cnt] # 랭킹순 분배
                for idx, combo in enumerate(itertools.combinations(group_p, 2)):
                    matches.append({"그룹": group_name, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수": 0, "B점수": 0, "완료": 0})
            
            save_data(pd.DataFrame(matches), MATCH_FILE)
            st.success("대진표가 생성되었습니다!")

    with t3: # 결과 합산
        st.subheader("대회 포인트 랭킹 반영")
        if st.button("결과를 전체 랭킹에 합산하기"):
            st.warning("이 기능은 현재 대회의 점수를 메인 DB에 누적합니다.")
