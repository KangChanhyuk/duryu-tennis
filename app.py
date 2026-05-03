import streamlit as st
import pandas as pd
import os
import random
import itertools
import numpy as np

# --- 1. 데이터 관리 로직 ---
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

# --- 2. 스타일 및 가시성 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    h1, h2, h3, p, label, span, div { color: #111 !important; }
    .match-table { width: 100%; border-collapse: collapse; margin: 10px 0; }
    .match-table th, .match-table td { border: 1px solid #ddd; padding: 8px; text-align: center; color: black; }
    .match-table th { background-color: #f2f2f2; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 구성 ---
with st.sidebar:
    st.title("🎾 두류테니스")
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택 (과거 수정 가능)", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")
    menu = st.radio("메뉴", ["전체랭킹", "대진 및 경기현황", "경기 결과"] + (["관리자 설정"] if is_admin else []))

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 기능 구현 ---

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
                
                # [기능] 매트릭스 대진표 (시각화용)
                st.subheader(f"📊 {g} 매트릭스 현황")
                players = sorted(list(set(g_df['팀A'].tolist() + g_df['팀B'].tolist())))
                matrix_df = pd.DataFrame(index=players, columns=players).fillna("-")
                for _, row in g_df.iterrows():
                    res = f"{int(row['A점수'])}:{int(row['B점수'])}" if row['완료'] == 1 else "예정"
                    matrix_df.at[row['팀A'], row['팀B']] = res
                    matrix_df.at[row['팀B'], row['팀A']] = res if row['완료'] == 0 else f"{int(row['B점수'])}:{int(row['A점수'])}"
                st.dataframe(matrix_df, use_container_width=True)

                st.subheader(f"📝 경기 순서 및 점수 입력")
                for idx, row in g_df.iterrows():
                    c1, c2, c3, c4 = st.columns([1, 3, 1, 3])
                    c1.markdown(f"**M-{row['순서']}**")
                    sc_a = c2.number_input(f"{row['팀A']}", 0, 10, int(row['A점수']), key=f"a_{idx}")
                    c3.markdown("vs")
                    sc_b = c4.number_input(f"{row['팀B']}", 0, 10, int(row['B점수']), key=f"b_{idx}")
                    
                    if st.button(f"Update Match {row['순서']}", key=f"btn_{idx}"):
                        df_m.at[idx, 'A점수'], df_m.at[idx, 'B점수'], df_m.at[idx, '완료'] = sc_a, sc_b, 1
                        save_data(df_m, MATCH_FILE)
                        st.success("점수가 반영되었습니다.")
                        st.rerun()
                    st.divider()

elif menu == "관리자 설정" and is_admin:
    st.header("⚙️ 관리자 정밀 설정")
    t1, t2 = st.tabs(["👥 회원 및 대회 관리", "⚔️ 랭킹순 그룹 배정 및 대진 생성"])
    
    with t1:
        st.subheader("회원 명단 관리")
        df_mem = load_members()
        # [기능] 개인별 수정
        ed_df = st.data_editor(df_mem, use_container_width=True, num_rows="dynamic")
        if st.button("회원 정보 저장"): save_data(ed_df, MEMBERS_FILE); st.success("저장 완료")
        
        st.divider()
        new_ev = st.text_input("새 대회명 생성")
        if st.button("대회 생성"): os.makedirs(os.path.join(DATA_DIR, new_ev), exist_ok=True); st.rerun()

    with t2:
        if not EV_PATH: st.error("사이드바에서 대회를 선택하세요.")
        else:
            st.subheader("랭킹 기반 그룹 자동 분배")
            all_mems = load_members().sort_values('랭킹')
            
            # [기능] 전체선택, 텍스트입력, 체크박스
            st.markdown("### **1. 참가자 선발**")
            text_names = st.text_area("명단 붙여넣기 (이름을 쉼표로 구분)")
            is_all = st.checkbox("전체 회원 선택")
            
            sel_names = []
            cols = st.columns(5)
            for idx, row in all_mems.iterrows():
                with cols[idx % 5]:
                    if st.checkbox(row['성명'], value=is_all, key=f"chk_{row['성명']}"):
                        sel_names.append(row['성명'])
            
            manual_list = [n.strip() for n in text_names.split(',') if n.strip()]
            final_list = list(set(sel_names + manual_list))
            st.write(f"현재 선택된 인원: {len(final_list)}명")

            st.divider()
            st.markdown("### **2. 그룹 및 인원 설정**")
            g_num = st.number_input("나눌 그룹 수 (A, B, C...)", 1, 10, 2)
            
            # [기능] 그룹별 명수 조절 (랭킹순 자동 배분)
            p_sorted = all_mems[all_mems['성명'].isin(final_list)].sort_values('랭킹')['성명'].tolist()
            
            group_setup = {}
            total_assigned = 0
            for i in range(g_num):
                g_name = chr(65 + i)
                # 남은 인원을 그룹 수로 나누어 기본값 설정
                default_size = (len(p_sorted) - total_assigned) // (g_num - i)
                size = st.number_input(f"Group {g_name} 인원", 1, len(p_sorted), default_size)
                group_setup[g_name] = p_sorted[total_assigned : total_assigned + size]
                total_assigned += size
            
            if st.button("⚔️ 대진표 확정 및 생성"):
                if total_assigned != len(p_sorted):
                    st.error(f"인원 설정 오류: 선택된 인원은 {len(p_sorted)}명이나 설정된 총합은 {total_assigned}명입니다.")
                else:
                    final_matches = []
                    for g_name, members in group_setup.items():
                        # 리그전(풀리그) 대진 생성
                        for idx, combo in enumerate(itertools.combinations(members, 2)):
                            final_matches.append({
                                "그룹": g_name, "순서": idx+1, 
                                "팀A": combo[0], "팀B": combo[1], 
                                "A점수": 0, "B점수": 0, "완료": 0
                            })
                    save_data(pd.DataFrame(final_matches), MATCH_FILE)
                    st.success(f"{sel_ev} 대진표가 생성되었습니다!")
