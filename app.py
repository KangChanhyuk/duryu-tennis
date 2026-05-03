import streamlit as st
import pandas as pd
import os
import random
import itertools

# --- 1. 기본 설정 및 데이터 로드 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        for c in ['4월 포인트', '3월 포인트', '부과점', '랭킹']:
            df[c] = pd.to_numeric(df.get(c, 0), errors='coerce').fillna(0).astype(int)
        df['변동'] = df['4월 포인트'] - df['3월 포인트']
        df['상태'] = df['변동'].apply(lambda x: "🔺" if x > 0 else ("🔻" if x < 0 else "—"))
        df['총점'] = df['4월 포인트'] + df['부과점']
        return df
    return pd.DataFrame(columns=['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '총점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 시인성 확보 (글자색 강제 고정) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    h1, h2, h3, p, label, span, div { color: #111 !important; }
    .match-card { border: 2px solid #002366; border-radius: 10px; padding: 15px; margin: 10px 0; background: #f9f9f9; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 ---
with st.sidebar:
    st.title("🎾 두류테니스")
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택 (과거 수정 가능)", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")
    menu = st.radio("메뉴", ["전체랭킹", "대진 및 경기현황", "경기 결과"] + (["관리자 설정"] if is_admin else []))

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 구현 ---
if menu == "전체랭킹":
    st.header("🥇 실시간 클럽 랭킹")
    df = load_members().sort_values('랭킹')
    st.table(df[['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '총점', '비고']])

elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택하세요.")
    else:
        df_m = pd.read_csv(MATCH_FILE)
        for i, r in df_m.iterrows():
            with st.container():
                st.markdown(f"<div class='match-card'><b>{r['그룹']} - {r['순서']}번 경기</b>", unsafe_allow_html=True)
                c1, c2, c3 = st.columns([2,1,2])
                s_a = c1.number_input(f"{r['팀A']}", 0, 10, int(r['A점수']), key=f"a{i}")
                s_b = c3.number_input(f"{r['팀B']}", 0, 10, int(r['B점수']), key=f"b{i}")
                if st.button(f"결과 저장 (경기 {i+1})", key=f"s{i}"):
                    df_m.at[i, 'A점수'], df_m.at[i, 'B점수'], df_m.at[i, '완료'] = s_a, s_b, 1
                    save_data(df_m, MATCH_FILE); st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

elif menu == "관리자 설정" and is_admin:
    st.header("⚙️ 관리자 시스템")
    tab1, tab2 = st.tabs(["👥 참가자 및 명단 관리", "⚔️ 대진표 생성"])
    
    with tab1:
        st.subheader("1. 회원 DB 관리 (엑셀/개별수정)")
        # 엑셀 업로드 (xlsx, csv 등 지원)
        up = st.file_uploader("엑셀 파일 업로드", type=['xlsx', 'xls', 'csv'])
        if up:
            df_up = pd.read_csv(up) if up.name.endswith('csv') else pd.read_excel(up)
            if st.button("DB 업로드 적용"): save_data(df_up, MEMBERS_FILE); st.rerun()
        
        st.divider()
        # [기능 확인] 개인별 수정 기능 (에디터)
        df_mem = load_members()
        ed_df = st.data_editor(df_mem, use_container_width=True, num_rows="dynamic")
        if st.button("수정사항 저장"): save_data(ed_df, MEMBERS_FILE); st.success("저장됨")

    with tab2:
        st.subheader("2. 대회 참가자 선발 (핵심 기능)")
        if not EV_PATH: st.error("사이드바에서 대회를 먼저 선택하세요.")
        else:
            # --- 요구하신 기능 집중 배치 섹션 ---
            st.info("💡 아래 세 가지 방법 중 편한 방법으로 참가자를 선발하세요.")
            
            # [기능 1] 텍스트 대량 입력
            st.markdown("### **(방법 1) 텍스트로 이름 붙여넣기**")
            text_names = st.text_area("쉼표(,)나 줄바꿈으로 이름을 입력하세요", help="예: 홍길동, 김철수, 이영희")
            
            st.divider()
            
            # [기능 2, 3] 전체선택 및 개별 체크박스
            st.markdown("### **(방법 2) 명단에서 체크박스로 선택**")
            all_mems = load_members().sort_values('성명')
            
            # 전체 선택/해제 체크박스
            is_all = st.checkbox("🔄 전체 인원 선택 / 해제")
            
            selected_from_check = []
            cols = st.columns(4) # 4열로 명단 배치
            for idx, row in all_mems.iterrows():
                with cols[idx % 4]:
                    if st.checkbox(row['성명'], value=is_all, key=f"sel_{row['성명']}"):
                        selected_from_check.append(row['성명'])
            
            # 최종 명단 취합 (텍스트 입력 + 체크박스 선택)
            manual_list = [n.strip() for n in text_names.replace('\n', ',').split(',') if n.strip()]
            final_participants = list(set(selected_from_check + manual_list))
            
            st.success(f"✅ 현재 선택된 인원: {len(final_participants)}명")
            st.write(", ".join(final_participants))
            
            st.divider()
            # 대진 생성 설정
            c1, c2 = st.columns(2)
            g_count = c1.number_input("조 개수", 1, 10, 1)
            mode = c2.selectbox("매칭 방식", ["고정페어 (스네이크)", "KDK (랜덤)"])
            
            if st.button("🚀 대진표 생성 및 저장"):
                if len(final_participants) < 4:
                    st.error("최소 4명 이상의 참가자가 필요합니다.")
                else:
                    # 랭킹순 정렬을 위해 DB 재참조
                    p_df = all_mems[all_mems['성명'].isin(final_participants)].sort_values('랭킹')
                    p_list = p_df['성명'].tolist()
                    
                    final_m = []
                    for g in range(g_count):
                        gn = f"{chr(65+g)}조"
                        mems = p_list[g::g_count]
                        if mode == "고정페어 (스네이크)":
                            pairs = []
                            t = mems[:]
                            while len(t) >= 2: pairs.append(f"{t.pop(0)} / {t.pop(-1)}")
                            for i, combo in enumerate(itertools.combinations(pairs, 2)):
                                final_m.append({"그룹":gn, "순서":i+1, "팀A":combo[0], "팀B":combo[1], "A점수":0, "B점수":0, "완료":0})
                        else: # KDK
                            random.shuffle(mems)
                            for i, combo in enumerate(itertools.combinations(mems, 4)):
                                if i >= len(mems): break
                                p = list(combo)
                                final_m.append({"그룹":gn, "순서":i+1, "팀A":f"{p[0]},{p[1]}", "팀B":f"{p[2]},{p[3]}", "A점수":0, "B점수":0, "완료":0})
                    
                    save_data(pd.DataFrame(final_m), MATCH_FILE)
                    st.success("대진표 생성 완료! '대진 및 경기현황' 메뉴를 확인하세요.")
