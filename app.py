import streamlit as st
import pandas as pd
import os
import random
import shutil
import re

# --- 1. 환경 설정 및 데이터 로드 (기존 로직 유지) ---
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

MEMBERS_FILE = 'tennis_members.csv'
DISPLAY_COLUMNS = ['랭킹', '성명', '4월 포인트', '3월 포인트', '결과', '부과점', '그룹', '비고']

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        for col in ['부과점', '랭킹', '4월 포인트', '3월 포인트']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
        return df
    return pd.DataFrame(columns=DISPLAY_COLUMNS)

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 대진표 알고리즘 (KDK 유지 + 고정조 풀리그 강화) ---
KDK_TABLE = {
    4: ["14:23", "13:24", "12:34"],
    5: ["12:34", "13:25", "14:35", "15:24", "23:45"],
    6: ["13:24", "15:46", "23:56", "14:35", "26:34", "16:25"],
    8: ["12:34", "56:78", "13:57", "24:68", "15:26", "37:48", "16:38", "25:47"],
    10: ["12:35", "67:8A", "23:46", "78:19", "34:57", "89:2A", "45:68", "13:9A", "56:79", "1A:24"],
    12: ["12:34", "56:78", "9A:BC", "13:57", "24:68", "9B:15", "48:9C", "67:AB", "AC:23"]
}

def parse_kdk(code, names):
    def get_n(c):
        idx = int(c, 16) - 1
        return names[idx] if idx < len(names) else "미배정"
    side_a, side_b = code.split(":")
    return f"{get_n(side_a[0])}, {get_n(side_a[1])}", f"{get_n(side_b[0])}, {get_n(side_b[1])}"

def generate_fixed_league(names, games_per_person):
    """고정조 풀리그: 2인 1조를 유지하며 1인당 지정된 게임 수만큼 대진 생성"""
    teams = []
    for i in range(0, len(names), 2):
        if i+1 < len(names):
            teams.append(f"{names[i]}, {names[i+1]}")
    
    matches = []
    num_teams = len(teams)
    match_count = 0
    max_matches = (len(names) * games_per_person) // 4  # 전체 총 경기 수 계산
    
    for i in range(num_teams):
        for j in range(i + 1, num_teams):
            if match_count >= max_matches: break
            matches.append({'순서': match_count + 1, '팀A': teams[i], '팀B': teams[j]})
            match_count += 1
    return matches[:max_matches]

# --- 3. UI 스타일 (헤더 중앙 정렬 완벽 보정) ---
st.set_page_config(page_title="두류 테니스 클럽", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .main-header { background-color: #1E3A8A; color: white; padding: 20px; border-radius: 10px; text-align: center; margin-bottom: 25px; }
    
    /* 데이터프레임 헤더(항목 제목)와 내용 모두 가운데 정렬 */
    div[data-testid="stDataFrame"] div[data-testid="stTable"] th,
    div[data-testid="stDataFrame"] div[aria-label="Data Grid"] div[role="columnheader"],
    div[data-testid="stDataFrame"] div[role="columnheader"] p {
        text-align: center !important;
        justify-content: center !important;
    }
    
    div[data-testid="stDataFrame"] td, 
    div[data-testid="stDataFrame"] div[role="gridcell"] {
        text-align: center !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. 사이드바 메뉴 ---
with st.sidebar:
    st.title("🎾 두류 테니스")
    event_list = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + event_list)
    menu = st.radio("메뉴 이동", ["🏆 전체 랭킹", "📅 경기 기록실", "📊 최종 성적 요약", "⚙️ 관리자 설정"])
    is_admin = (st.text_input("관리자 암호", type="password") == "0502")

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None
PART_FILE = os.path.join(EV_PATH, "participants.csv") if EV_PATH else None

# --- 5. 메뉴별 기능 ---
if menu == "⚙️ 관리자 설정" and is_admin:
    t1, t2, t3, t4 = st.tabs(["👥 회원/참여자 관리", "📁 대회 생성", "🚀 대진표 생성", "🗑️ 관리"])
    
    with t1:
        st.subheader("1. 전체 회원 DB 수정")
        df_m = load_members()
        ed_m = st.data_editor(df_m, num_rows="dynamic", use_container_width=True, hide_index=True)
        if st.button("회원 DB 저장"): save_data(ed_m, MEMBERS_FILE); st.rerun()
        
        st.divider()
        if EV_PATH:
            st.subheader("2. 참여자 명단 수정 및 교체")
            p_curr_df = pd.read_csv(PART_FILE) if os.path.exists(PART_FILE) else pd.DataFrame(columns=['성명'])
            # 명단 교체가 자유롭도록 데이터 에디터 활용 (이름 수정 가능)
            ed_p = st.data_editor(p_curr_df, num_rows="dynamic", use_container_width=True, hide_index=True, key="part_editor")
            
            p_text = st.text_area("명단 일괄 입력 (쉼표/줄바꿈 구분)", value=", ".join(p_curr_df['성명'].tolist()))
            
            if st.button("참여자 명단 최종 확정"):
                if p_text:
                    raw_names = re.findall(r'[가-힣a-zA-Z0-9]+', p_text)
                    save_data(pd.DataFrame({'성명': raw_names}), PART_FILE)
                else:
                    save_data(ed_p, PART_FILE)
                st.success("명단이 확정되었습니다."); st.rerun()

    with t2:
        new_name = st.text_input("새 대회 이름")
        if st.button("대회 생성"):
            if new_name:
                path = os.path.join(DATA_DIR, new_name)
                if not os.path.exists(path): os.makedirs(path); st.success("생성 완료"); st.rerun()

    with t3:
        if EV_PATH and os.path.exists(PART_FILE):
            p_list = pd.read_csv(PART_FILE)['성명'].tolist()
            num_g = st.number_input("나눌 그룹 수", 1, 10, 2)
            g_configs = []
            ptr = 0
            
            for i in range(int(num_g)):
                letter = chr(65 + i) # A, B, C, D...
                with st.expander(f"📍 {letter} 그룹 설정", expanded=True):
                    c1, c2, c3, c4 = st.columns(4)
                    gn = c1.text_input("그룹명", f"{letter}그룹", key=f"gn_{i}")
                    gm = c2.selectbox("방식", ["KDK", "고정조"], key=f"gm_{i}")
                    gs = c3.number_input("인원수", 4, 100, 8, key=f"gs_{i}")
                    g_pk = c4.number_input("1인당 게임수", 1, 10, 3, key=f"gpk_{i}")
                    
                    mems = p_list[ptr : ptr + int(gs)]
                    g_configs.append({'name': gn, 'mode': gm, 'mems': mems, 'games': g_pk})
                    st.info(f"배정: {', '.join(mems)}")
                    ptr += int(gs)
            
            if st.button("🚀 대진표 생성"):
                total_matches = []
                for gc in g_configs:
                    names = gc['mems']
                    if len(names) < 4: continue
                    if gc['mode'] == "KDK":
                        random.shuffle(names)
                        codes = KDK_TABLE.get(len(names), [])
                        max_m = (len(names) * gc['games']) // 4
                        for idx, code in enumerate(codes[:max_m]):
                            tA, tB = parse_kdk(code, names)
                            total_matches.append({'순서': idx+1, '그룹': gc['name'], '팀A': tA, '팀B': tB, 'A점수':0, 'B점수':0, '완료':0})
                    else:
                        fixed_m = generate_fixed_league(names, gc['games'])
                        for m in fixed_m:
                            total_matches.append({'순서': m['순서'], '그룹': gc['name'], '팀A': m['팀A'], '팀B': m['팀B'], 'A점수':0, 'B점수':0, '완료':0})
                save_data(pd.DataFrame(total_matches), MATCH_FILE); st.rerun()

    with t4:
        if sel_ev != "선택 안함" and st.button(f"🚨 {sel_ev} 삭제"):
            shutil.rmtree(EV_PATH); st.rerun()

elif menu == "🏆 전체 랭킹":
    df = load_members()
    if not df.empty:
        st.dataframe(df[DISPLAY_COLUMNS].sort_values('랭킹'), use_container_width=True, hide_index=True)

elif menu == "📅 경기 기록실":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        df_m = pd.read_csv(MATCH_FILE)
        tabs = st.tabs([f"📍 {gn}" for gn in df_m['그룹'].unique()])
        for i, gn in enumerate(df_m['그룹'].unique()):
            with tabs[i]:
                curr = df_m[df_m['그룹'] == gn]
                for idx, row in curr.iterrows():
                    with st.expander(f"{row['순서']}R: {row['팀A']} VS {row['팀B']} {'✅' if row['완료'] else ''}"):
                        c1, c2, c3 = st.columns([3, 3, 2])
                        sa = c1.number_input(f"{row['팀A']}", 0, 30, int(row['A점수']), key=f"sa_{idx}")
                        sb = c2.number_input(f"{row['팀B']}", 0, 30, int(row['B점수']), key=f"sb_{idx}")
                        if c3.button("결과 저장", key=f"btn_{idx}"):
                            df_m.at[idx, 'A점수'], df_m.at[idx, 'B점수'], df_m.at[idx, '완료'] = sa, sb, 1
                            save_data(df_m, MATCH_FILE); st.rerun()

elif menu == "📊 최종 성적 요약":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        df_m = pd.read_csv(MATCH_FILE)
        for gn in df_m['그룹'].unique():
            st.subheader(f"🏆 {gn} 순위표")
            gm = df_m[(df_m['그룹'] == gn) & (df_m['완료'] == 1)]
            p_all = []
            for t in df_m[df_m['그룹']==gn]['팀A'].tolist() + df_m[df_m['그룹']==gn]['팀B'].tolist():
                p_all.extend(t.split(", "))
            
            stats = []
            for p in sorted(list(set(p_all))):
                pm = gm[gm['팀A'].str.contains(p) | gm['팀B'].str.contains(p)]
                w, l, d = 0, 0, 0
                for _, r in pm.iterrows():
                    my, op = (r['A점수'], r['B점수']) if p in r['팀A'] else (r['B점수'], r['A점수'])
                    if my > op: w += 1
                    elif my < op: l += 1
                    d += (my - op)
                stats.append({'성명': p, '승': w, '패': l, '득실차': d})
            
            if stats:
                res_df = pd.DataFrame(stats).sort_values(['승', '득실차'], ascending=False).reset_index(drop=True)
                res_df.insert(0, '순위', res_df.index + 1)
                st.dataframe(res_df, use_container_width=True, hide_index=True)