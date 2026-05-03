import streamlit as st
import pandas as pd
import os
import random
import itertools
from datetime import datetime

# --- 1. 환경 설정 및 데이터 로직 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_members():
    """전체 멤버 로드 및 데이터 정제"""
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        # 필수 컬럼 보장
        cols = ['랭킹', '성명', '4월 포인트', '3월 포인트', '부과점', '비고']
        for c in cols:
            if c not in df.columns:
                df[c] = 0 if '포인트' in c or c == '랭킹' or c == '부과점' else ""
        
        # 데이터 타입 고정
        df['랭킹'] = pd.to_numeric(df['랭킹'], errors='coerce').fillna(999).astype(int)
        df['4월 포인트'] = pd.to_numeric(df['4월 포인트'], errors='coerce').fillna(0).astype(int)
        df['3월 포인트'] = pd.to_numeric(df['3월 포인트'], errors='coerce').fillna(0).astype(int)
        # 변동 계산 (에러 방지용 안전 장치)
        df['변동'] = df['3월 포인트'] - df['4월 포인트'] 
        return df
    return pd.DataFrame(columns=['랭킹', '성명', '4월 포인트', '3월 포인트', '변동', '부과점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 스타일 설정 (가운데 정렬 및 가독성) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #ffffff; }
    .centered { text-align: center; font-family: 'Pretendard', sans-serif; }
    h1, h2, h3 { text-align: center; color: #002366; }
    [data-testid="stMetricValue"] { text-align: center; }
    .stDataFrame { margin: 0 auto; }
    .match-container {
        border: 2px solid #002366;
        border-radius: 15px;
        padding: 20px;
        margin: 15px 0;
        background-color: #f0f2f6;
    }
    .team-name { font-size: 1.2rem; font-weight: 800; color: #002366; text-align: center; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { border: 1px solid #ddd; padding: 12px; text-align: center; color: black; }
    th { background-color: #002366; color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 메뉴 ---
with st.sidebar:
    st.markdown("<h1 class='centered'>🎾 두류테니스</h1>", unsafe_allow_html=True)
    events = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + events)
    
    admin_pw = st.text_input("🔑 관리자 암호", type="password")
    is_admin = (admin_pw == "0502")
    
    menu = st.radio("메뉴 이동", ["전체랭킹", "대진 및 경기현황", "경기 결과", "경기 기록"] + (["관리자 설정"] if is_admin else []))

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 기능부 구현 ---

# [메뉴 1: 전체랭킹]
if menu == "전체랭킹":
    st.markdown("<h1 class='centered'>🥇 클럽 전체 랭킹</h1>", unsafe_allow_html=True)
    df = load_members().sort_values('랭킹')
    
    # 변동 아이콘 표시
    def get_arrow(val):
        if val > 0: return "🔺"
        elif val < 0: return "🔻"
        return "—"
    
    df['상태'] = df['변동'].apply(get_arrow)
    display_df = df[['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '비고']]
    
    st.table(display_df) # 많은 정보를 한 번에 보기 위해 table 사용

# [메뉴 2: 대진 및 경기현황]
elif menu == "대진 및 경기현황":
    if not MATCH_FILE or not os.path.exists(MATCH_FILE):
        st.warning("대회를 선택하거나 관리자 설정에서 대진표를 생성해주세요.")
    else:
        st.markdown(f"<h1>📅 {sel_ev} 경기 현황</h1>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        
        groups = df_m['그룹'].unique()
        tabs = st.tabs([f"📍 {g}" for g in groups])
        
        for idx, gn in enumerate(groups):
            with tabs[idx]:
                curr_g = df_m[df_m['그룹'] == gn]
                for i, row in curr_g.iterrows():
                    st.markdown(f"<div class='match-container'>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align:center;'><b>경기 순서 {row['순서']}</b></p>", unsafe_allow_html=True)
                    c1, c2, c3, c4 = st.columns([4, 1, 1, 4])
                    
                    with c1:
                        st.markdown(f"<p class='team-name'>{row['팀A']}</p>", unsafe_allow_html=True)
                        score_a = st.number_input("득점", 0, 10, int(row['A점수']), key=f"score_a_{i}")
                    with c2: st.markdown("<h2 style='margin-top:20px;'>:</h2>", unsafe_allow_html=True)
                    with c3: st.markdown("<h2 style='margin-top:20px;'>:</h2>", unsafe_allow_html=True)
                    with c4:
                        st.markdown(f"<p class='team-name'>{row['팀B']}</p>", unsafe_allow_html=True)
                        score_b = st.number_input("득점", 0, 10, int(row['B점수']), key=f"score_b_{i}")
                    
                    if st.button("결과 자동 반영 및 저장", key=f"save_{i}"):
                        df_m.at[i, 'A점수'], df_m.at[i, 'B점수'], df_m.at[i, '완료'] = score_a, score_b, 1
                        save_data(df_m, MATCH_FILE)
                        st.success("점수가 양방향으로 기록되었습니다!")
                        st.rerun()
                    st.markdown("</div>", unsafe_allow_html=True)

# [메뉴 3: 경기 결과 (매트릭스)]
elif menu == "경기 결과":
    if MATCH_FILE and os.path.exists(MATCH_FILE):
        st.markdown("<h1>📊 대회 결과 요약 (Matrix)</h1>", unsafe_allow_html=True)
        df_m = pd.read_csv(MATCH_FILE)
        for gn in df_m['그룹'].unique():
            st.subheader(f"[{gn}] 교차 스코어보드")
            gm = df_m[df_m['그룹'] == gn]
            teams = sorted(list(set(gm['팀A'].tolist() + gm['팀B'].tolist())))
            
            # 매트릭스 생성
            mat = pd.DataFrame(index=teams, columns=teams).fillna("-")
            stats = {t: {'승':0, '패':0, '득':0, '실':0} for t in teams}
            
            for _, r in gm.iterrows():
                if r['완료']:
                    mat.at[r['チームA'], r['팀B']] = f"{int(r['A점수'])}:{int(r['B점수'])}"
                    mat.at[r['팀B'], r['팀A']] = f"{int(r['B점수'])}:{int(r['A점수'])}"
                    # 통계 계산
                    stats[r['팀A']]['득'] += r['A점수']; stats[r['팀A']]['실'] += r['B점수']
                    stats[r['팀B']]['득'] += r['B점수']; stats[r['팀B']]['실'] += r['A점수']
                    if r['A점수'] > r['B점수']: stats[r['팀A']]['승'] += 1; stats[r['팀B']]['패'] += 1
                    elif r['B점수'] > r['A점수']: stats[r['팀B']]['승'] += 1; stats[r['팀A']]['패'] += 1
            
            st.write(mat) # 매트릭스 출력
            
            # 순위 요약
            res_list = []
            for t, s in stats.items():
                res_list.append({'팀':t, '승':s['승'], '패':s['패'], '득실차':s['득']-s['실']})
            res_df = pd.DataFrame(res_list).sort_values(['승', '득실차'], ascending=False)
            st.table(res_df)

# [메뉴 4: 관리자 설정 (종합)]
elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1>⚙️ 두류테니스 관리자 모드</h1>", unsafe_allow_html=True)
    tabs = st.tabs(["📁 대회 생성/삭제", "👥 참가자 현황/수정", "🚀 대진표 생성", "🔄 결과 랭킹 반영"])
    
    with tabs[0]: # 대회 생성/삭제
        c1, c2 = st.columns(2)
        new_ev = c1.text_input("새 대회 명칭")
        if c1.button("대회 폴더 생성"):
            os.makedirs(os.path.join(DATA_DIR, new_ev), exist_ok=True)
            st.success("폴더가 생성되었습니다.")
        
        del_ev = c2.selectbox("삭제할 대회", ["선택"] + events)
        if c2.button("대회 삭제") and del_ev != "선택":
            import shutil
            shutil.rmtree(os.path.join(DATA_DIR, del_ev))
            st.rerun()

    with tabs[1]: # 참가자 현황 (엑셀 업로드 포함)
        st.subheader("파일 업로드 (xlsx, xls, csv 지원)")
        up_file = st.file_uploader("파일 선택", type=['xlsx', 'xls', 'csv'])
        if up_file:
            if up_file.name.endswith('csv'): df_up = pd.read_csv(up_file)
            else: df_up = pd.read_excel(up_file)
            if st.button("업로드 파일로 멤버 DB 교체"):
                save_data(df_up, MEMBERS_FILE); st.success("DB 교체 완료!")
        
        st.divider()
        df_edit = load_members()
        st.write("직접 수정 (체크박스로 선택 및 편집)")
        final_edit = st.data_editor(df_edit, use_container_width=True, num_rows="dynamic")
        if st.button("수정사항 저장"):
            save_data(final_edit, MEMBERS_FILE); st.success("저장 성공!")

    with tabs[2]: # 대진표 생성 (스네이크 고정페어 & KDK)
        if not EV_PATH: st.info("왼쪽에서 대회를 먼저 선택하세요.")
        else:
            df_mems = load_members().sort_values('랭킹')
            selected = st.multiselect("참가자 선택 (랭킹순 자동정렬)", df_mems['성명'].tolist())
            
            col1, col2, col3 = st.columns(3)
            g_count = col1.number_input("그룹 개수", 1, 10, 1)
            g_mode = col2.selectbox("경기 방식", ["고정페어 (랭킹순 매칭)", "KDK (랜덤)"])
            
            if st.button("🚀 그룹별 대진표 자동 생성"):
                # 랭킹순 인원 분배 (A->B->C...)
                selected_df = df_mems[df_mems['성명'].isin(selected)]
                p_list = selected_df['성명'].tolist()
                
                all_m = []
                for g_idx in range(g_count):
                    g_name = f"{chr(65+g_idx)}그룹"
                    mems = p_list[g_idx::g_count] # 랭킹순 분배
                    
                    if g_mode == "고정페어 (랭킹순 매칭)":
                        # 스네이크 방식: 1위+최하위, 2위+차하위
                        pairs = []
                        temp_m = mems[:]
                        while len(temp_m) >= 2:
                            pairs.append(f"{temp_m.pop(0)} / {temp_m.pop(-1)}")
                        # 페어끼리 리그전
                        for idx, combo in enumerate(itertools.combinations(pairs, 2)):
                            all_m.append({"그룹": g_name, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수":0, "B점수":0, "완료":0})
                    
                    else: # KDK 랜덤
                        random.shuffle(mems)
                        # KDK 간이 로직 (인원의 1.5배수 경기 생성)
                        for idx, combo in enumerate(itertools.combinations(mems, 4)):
                            if idx >= len(mems)*1.2: break
                            p = list(combo)
                            all_m.append({"그룹": g_name, "순서": idx+1, "팀A": f"{p[0]},{p[1]}", "팀B": f"{p[2]},{p[3]}", "A점수":0, "B점수":0, "완료":0})
                
                save_data(pd.DataFrame(all_m), MATCH_FILE)
                st.success("대진표가 생성되었습니다!")

    with tabs[3]: # 결과 반영 및 자동 합산
        st.subheader("대회 결과 랭킹 합산")
        if MATCH_FILE and os.path.exists(MATCH_FILE):
            df_curr_m = pd.read_csv(MATCH_FILE)
            if st.button("현재 대회 승점을 랭킹 포인트에 합산하기"):
                df_ranking = load_members()
                # 승리 시 10점, 패배 시 5점 예시 (수정 가능)
                for _, r in df_curr_m[df_curr_m['완료'] == 1].iterrows():
                    for t, s_my, s_op in [(r['팀A'], r['A점수'], r['B점수']), (r['팀B'], r['B점수'], r['A점수'])]:
                        players = [p.strip() for p in t.replace('/', ',').split(',')]
                        for p in players:
                            if p in df_ranking['성명'].values:
                                idx = df_ranking[df_ranking['성명'] == p].index[0]
                                bonus = 10 if s_my > s_op else 5
                                df_ranking.at[idx, '4월 포인트'] += bonus
                save_data(df_ranking, MEMBERS_FILE)
                st.success("포인트가 자동 합산되었습니다!")
