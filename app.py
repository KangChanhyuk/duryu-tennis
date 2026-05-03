import streamlit as st
import pandas as pd
import os
import itertools
import random
import re
from streamlit_option_menu import option_menu

# --- 1. 기본 설정 및 데이터 관리 ---
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

# --- 2. 스타일 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    h1, h2, h3 { text-align: center; color: #002366; }
    .match-card { 
        border: 1px solid #ddd; border-radius: 12px; padding: 15px; 
        margin-bottom: 10px; background: #fdfdfd; box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .vs-text { font-size: 1.2rem; font-weight: bold; color: #ff4b4b; text-align: center; display: block; margin-top: 10px; }
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

if menu == "전체랭킹":
    st.markdown("<h1>🥇 전체 회원 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    st.dataframe(df[['랭킹', '상태', '성명', '4월 포인트', '부과점', '비고']], use_container_width=True, hide_index=True)

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
                    st.markdown("<div class='match-card'>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center; font-size:0.8rem; color:gray;'>MATCH {row['순서']}</p>", unsafe_allow_html=True)
                    c1, c2, c3, c4, c5 = st.columns([3, 1, 0.5, 1, 3])
                    c1.markdown(f"<h4 style='text-align:right;'>{row['팀A']}</h4>", unsafe_allow_html=True)
                    s_a = c2.number_input("", 0, 10, int(row['A점수']), key=f"sA_{idx}", label_visibility="collapsed")
                    c3.markdown("<span class='vs-text'>VS</span>", unsafe_allow_html=True)
                    s_b = c4.number_input("", 0, 10, int(row['B점수']), key=f"sB_{idx}", label_visibility="collapsed")
                    c5.markdown(f"<h4 style='text-align:left;'>{row['팀B']}</h4>", unsafe_allow_html=True)
                    if st.button(f"저장", key=f"btn_{idx}", use_container_width=True):
                        m_df.loc[idx, ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                        save_data(m_df, MATCH_FILE); st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

elif menu == "경기 결과":
    st.markdown("<h1>📊 대회 성적 집계</h1>", unsafe_allow_html=True)
    st.write("준비 중인 기능입니다. 매트릭스 형태로 성적이 표기될 예정입니다.")

elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 관리자 설정</h1>", unsafe_allow_html=True)
    t1, t2, t3 = st.tabs(["📁 대회 관리", "⚔️ 참가자 및 대진 생성", "📈 결과 반영"])
    
    with t1:
        new_ev = st.text_input("새 대회 명칭")
        if st.button("대회 생성"):
            os.makedirs(os.path.join(DATA_DIR, new_ev), exist_ok=True); st.rerun()
    
    with t2:
        st.subheader("참가자 입력 및 그룹별 인원 지정")
        raw_names = st.text_area("명단 붙여넣기 (쉼표/공백/엔터 자동인식)")
        p_list = [n.strip() for n in re.split(r'[,\s\n]+', raw_names) if n.strip()]
        st.info(f"인식된 인원: {len(p_list)}명")
        
        all_mems = load_members()
        p_ranked = all_mems[all_mems['성명'].isin(p_list)].sort_values('랭킹')
        final_p_sorted = p_ranked['성명'].tolist() + [n for n in p_list if n not in p_ranked['성명'].tolist()]

        col1, col2 = st.columns(2)
        with col1:
            g_cnt = st.number_input("그룹 수", 1, 10, 1)
            mode = st.selectbox("경기 방식", ["고정페어 복식", "KDK 복식", "단식"])
        with col2:
            group_sizes = []
            temp_rem = len(final_p_sorted)
            for i in range(g_cnt):
                g_label = chr(65 + i)
                size = st.number_input(f"{g_label}그룹 인원수", 0, len(final_p_sorted), 0, key=f"sz_{g_label}")
                group_sizes.append(size); temp_rem -= size
            if temp_rem != 0: st.warning(f"인원 불일치: {temp_rem}명")

        if st.button("⚔️ 대진표 생성"):
            if sum(group_sizes) != len(final_p_sorted): st.error("인원 합계가 맞지 않습니다.")
            else:
                matches, cur = [], 0
                for i, size in enumerate(group_sizes):
                    g_label, g_m = chr(65 + i), final_p_sorted[cur : cur + size]
                    cur += size
                    if mode == "고정페어 복식":
                        pairs, tmp = [], g_m.copy()
                        while len(tmp) >= 2: pairs.append(f"{tmp.pop(0)}/{tmp.pop(-1)}")
                        for idx, c in enumerate(itertools.combinations(pairs, 2)):
                            matches.append({"그룹": g_label, "순서": idx+1, "팀A": c[0], "팀B": c[1], "A점수": 0, "B점수": 0, "완료": 0})
                    elif mode == "KDK 복식":
                        for idx, c in enumerate(itertools.combinations(g_m, 4)):
                            matches.append({"그룹": g_label, "순서": idx+1, "팀A": f"{c[0]}/{c[1]}", "팀B": f"{c[2]}/{c[3]}", "A점수": 0, "B점수": 0, "완료": 0})
                    else:
                        for idx, c in enumerate(itertools.combinations(g_m, 2)):
                            matches.append({"그룹": g_label, "순서": idx+1, "팀A": c[0], "팀B": c[1], "A점수": 0, "B점수": 0, "완료": 0})
                save_data(pd.DataFrame(matches), MATCH_FILE); st.success("생성 완료!"); st.balloons()
