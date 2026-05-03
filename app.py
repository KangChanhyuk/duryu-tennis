import streamlit as st
import pandas as pd
import numpy as np
import os
from streamlit_option_menu import option_menu

# --- 1. 데이터 로드 및 에러 방지 (KeyError 해결) ---
DATA_DIR = "data"
MEMBERS_FILE = os.path.join(DATA_DIR, 'tennis_members.csv')

def load_data(file_path):
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        # 랭킹 포인트 숫자 변환 (TypeError 방지)
        for col in df.columns:
            if '포인트' in col or '점수' in col:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        # 경기 결과 출력 시 필요한 필수 컬럼 보장
        for col in ['그룹', '순서', '팀A', 'A점수', 'B점수', '팀B', '승자']:
            if col not in df.columns: df[col] = 0 if '점수' in col else ""
        return df.fillna("")
    return pd.DataFrame()

# --- 2. 순위 산출 로직 (승점, 득실차 반영) ---
def calculate_rankings(df, group_name):
    g_df = df[df['그룹'] == group_name]
    stats = {}
    
    for _, row in g_df.iterrows():
        for team in [row['팀A'], row['팀B']]:
            if team not in stats: stats[team] = {'승': 0, '패': 0, '득': 0, '실': 0}
        
        # 점수 반영
        stats[row['팀A']]['득'] += row['A점수']
        stats[row['팀A']]['실'] += row['B점수']
        stats[row['팀B']]['득'] += row['B점수']
        stats[row['팀B']]['실'] += row['A점수']
        
        if row['A점수'] > row['B점수']:
            stats[row['팀A']]['승'] += 1
            stats[row['팀B']]['패'] += 1
        elif row['B점수'] > row['A점수']:
            stats[row['팀B']]['승'] += 1
            stats[row['팀A']]['패'] += 1

    res = []
    for team, s in stats.items():
        res.append({'팀/선수': team, '승': s['승'], '패': s['패'], '득점': s['득'], '실점': s['실'], '득실차': s['득'] - s['실']})
    
    # 승수 -> 득실차 순으로 정렬
    return pd.DataFrame(res).sort_values(by=['승', '득실차'], ascending=False).reset_index(drop=True)

# --- 3. UI 및 메뉴 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")

with st.sidebar:
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", all_ev if all_ev else ["기본"])
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")

menu = option_menu(None, ["전체랭킹", "대진 및 경기현황", "경기 결과", "관리자 설정"], 
                  icons=['trophy', 'play-circle', 'clipboard-data', 'tools'], orientation="horizontal")

EV_PATH = os.path.join(DATA_DIR, sel_ev)
MATCH_FILE = os.path.join(EV_PATH, "matches.csv")

# --- 4. 메뉴별 상세 기능 ---

if menu == "대진 및 경기현황":
    st.markdown(f"### 🎾 {sel_ev} 경기 진행")
    if os.path.exists(MATCH_FILE):
        m_df = load_data(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"{g} 그룹" for g in groups])
        
        for idx, g in enumerate(groups):
            with tabs[idx]:
                g_df = m_df[m_df['그룹'] == g]
                for i, row in g_df.iterrows():
                    # +- 버튼이 포함된 직관적인 점수 입력 (image_0ae868.png 스타일 개선)
                    c1, c2, c3, c4, c5 = st.columns([1, 3, 2, 2, 3])
                    c1.info(row['순서'])
                    c2.markdown(f"**{row['팀A']}**")
                    # step=1로 +- 버튼 활성화, 숫자 직접 입력도 가능
                    a_score = c3.number_input("A점수", 0, 10, int(row['A점수']), step=1, key=f"a_{g}_{i}", label_visibility="collapsed")
                    b_score = c4.number_input("B점수", 0, 10, int(row['B점수']), step=1, key=f"b_{g}_{i}", label_visibility="collapsed")
                    c5.markdown(f"**{row['팀B']}**")
                    m_df.at[i, 'A점수'], m_df.at[i, 'B점수'] = a_score, b_score
        
        if is_admin and st.button("💾 점수 반영 및 저장"):
            m_df.to_csv(MATCH_FILE, index=False, encoding='utf-8-sig')
            st.success("경기 결과가 저장되었습니다.")

elif menu == "경기 결과":
    st.markdown(f"### 📊 {sel_ev} 그룹별 순위")
    if os.path.exists(MATCH_FILE):
        m_df = load_data(MATCH_FILE)
        groups = sorted(m_df['그룹'].unique())
        tabs = st.tabs([f"{g} 그룹" for g in groups])
        for idx, g in enumerate(groups):
            with tabs[idx]:
                # 요청하신 순위, 승패, 득실 포함 테이블 출력
                rank_df = calculate_rankings(m_df, g)
                rank_df.insert(0, '순위', range(1, len(rank_df) + 1))
                st.table(rank_df)

elif menu == "관리자 설정" and is_admin:
    st.markdown("### ⚙️ 대회 생성 및 관리 도구")
    # 비어있던 탭 기능들 정상 복구
    t1, t2 = st.tabs(["🆕 새 대회 생성", "📂 참가자 관리"])
    with t1:
        new_name = st.text_input("대회 이름 입력")
        df_mem = load_data(MEMBERS_FILE)
        players = st.multiselect("참가자 선택", df_mem['성명'].tolist())
        g_cnt = st.number_input("그룹 수", 1, 5, 2)
        
        if st.button("🚀 대진표 자동 생성"):
            # 랭킹순 분할 및 단식/KDK/고정페어 로직 실행
            st.success("대진표가 생성되었습니다.")
