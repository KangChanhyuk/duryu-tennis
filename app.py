import streamlit as st
import pandas as pd
import os
import itertools

# --- 1. 데이터 관리 ---
DATA_DIR = "data"
MEMBERS_FILE = 'tennis_members.csv'
if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR)

def load_members():
    if os.path.exists(MEMBERS_FILE):
        df = pd.read_csv(MEMBERS_FILE).fillna("")
        for c in ['4월 포인트', '3월 포인트', '부과점', '랭킹']:
            df[c] = pd.to_numeric(df.get(c, 0), errors='coerce').fillna(0).astype(int)
        # 랭킹 변동 및 총점 계산
        df['변동'] = df['4월 포인트'] - df['3월 포인트']
        df['상태'] = df['변동'].apply(lambda x: "🔺" if x > 0 else ("🔻" if x < 0 else "—"))
        df['총점'] = df['4월 포인트'] + df['부과점']
        return df
    return pd.DataFrame(columns=['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '총점', '비고'])

def save_data(df, path):
    df.to_csv(path, index=False, encoding='utf-8-sig')

# --- 2. 디자인 설정 (시인성 확보) ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    h1, h2, h3, p, label, span, div { color: #111 !important; }
    .match-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; background: #fefefe; margin-bottom: 10px; }
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

# --- 4. 메인 기능 ---

if menu == "전체랭킹":
    st.header("🥇 실시간 클럽 랭킹")
    df = load_members().sort_values('랭킹')
    st.table(df[['랭킹', '상태', '성명', '4월 포인트', '3월 포인트', '부과점', '총점', '비고']])

elif menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택하세요.")
    else:
        df_m = pd.read_csv(MATCH_FILE)
        groups = sorted(df_m['그룹'].unique())
        
        # [기능] 그룹별 탭 구분
        tabs = st.tabs([f"Group {g}" for g in groups])
        
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = df_m[df_m['그룹'] == g]
                
                # [기능] 매트릭스 대진표
                st.subheader(f"📊 {g}조 매트릭스")
                players = sorted(list(set(g_df['팀A'].tolist() + g_df['팀B'].tolist())))
                matrix = pd.DataFrame("-", index=players, columns=players)
                for _, row in g_df.iterrows():
                    res = f"{int(row['A점수'])}:{int(row['B점수'])}" if row['완료'] == 1 else "예정"
                    matrix.at[row['팀A'], row['팀B']] = res
                st.dataframe(matrix, use_container_width=True)

                st.subheader("📝 경기 결과 입력")
                for idx, row in g_df.iterrows():
                    with st.container():
                        c1, c2, c3, c4 = st.columns([1, 3, 1, 3])
                        c1.write(f"**순서 {row['순서']}**")
                        sc_a = c2.number_input(f"{row['팀A']}", 0, 10, int(row['A점수']), key=f"a_{idx}")
                        c3.write("vs")
                        sc_b = c4.number_input(f"{row['팀B']}", 0, 10, int(row['B점수']), key=f"b_{idx}")
                        if st.button(f"저장 (M-{idx})", key=f"sv_{idx}"):
                            df_m.at[idx, 'A점수'], df_m.at[idx, 'B점수'], df_m.at[idx, '완료'] = sc_a, sc_b, 1
                            save_data(df_m, MATCH_FILE)
                            st.rerun()
                        st.divider()

elif menu == "관리자 설정" and is_admin:
    st.header("⚙️ 관리자 정밀 설정")
    t1, t2 = st.tabs(["👥 회원 관리", "⚔️ 랭킹순 그룹 배정"])
    
    with t1:
        df_mem = load_members()
        ed_df = st.data_editor(df_mem, use_container_width=True, num_rows="dynamic")
        if st.button("회원 정보 업데이트"): save_data(ed_df, MEMBERS_FILE); st.success("저장 완료")
        
        st.divider()
        new_ev = st.text_input("새 대회 폴더 생성")
        if st.button("폴더 생성"): os.makedirs(os.path.join(DATA_DIR, new_ev), exist_ok=True); st.rerun()

    with t2:
        if not EV_PATH: st.error("사이드바에서 대회를 먼저 선택하세요.")
        else:
            st.subheader("상위 랭커부터 그룹 자동 배정")
            all_mems = load_members().sort_values('랭킹') # 랭킹순 정렬
            
            # 참가자 선택 섹션 (전체선택, 텍스트, 체크박스 통합)
            c1, c2 = st.columns(2)
            with c1:
                is_all = st.checkbox("전체 회원 선택")
                sel_names = []
                for idx, row in all_mems.iterrows():
                    if st.checkbox(f"{row['성명']} (Rank {row['랭킹']})", value=is_all, key=f"p_{idx}"):
                        sel_names.append(row['성명'])
            with c2:
                text_in = st.text_area("텍스트로 이름 추가 (쉼표 구분)")
                manual = [n.strip() for n in text_in.split(',') if n.strip()]
                final_p = list(set(sel_names + manual))
            
            st.info(f"확정 인원: {len(final_p)}명 (랭킹순으로 그룹이 나뉩니다)")
            
            # 그룹핑 로직
            g_num = st.number_input("나눌 그룹 수", 1, 10, 2)
            p_sorted = all_mems[all_mems['성명'].isin(final_p)].sort_values('랭킹')['성명'].tolist()
            
            group_data = {}
            current_idx = 0
            for i in range(g_num):
                g_label = chr(65 + i) # A, B, C...
                size = st.number_input(f"{g_label}그룹 인원수 (상위 랭커 순 배정)", 1, len(p_sorted), 4, key=f"size_{g_label}")
                group_data[g_label] = p_sorted[current_idx : current_idx + size]
                current_idx += size
                if group_data[g_label]:
                    st.write(f"📍 {g_label}조 명단: {', '.join(group_data[g_label])}")

            if st.button("⚔️ 대진표 최종 생성"):
                matches = []
                for g_label, members in group_data.items():
                    for idx, combo in enumerate(itertools.combinations(members, 2)):
                        matches.append({"그룹": g_label, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수": 0, "B점수": 0, "완료": 0})
                save_data(pd.DataFrame(matches), MATCH_FILE)
                st.success("랭킹 기반 대진표 생성 완료!")
