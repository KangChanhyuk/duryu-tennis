import streamlit as st
import pandas as pd
import os
import itertools
import re

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

# --- 2. 스타일 및 UI 설정 ---
st.set_page_config(page_title="두류테니스클럽", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: white !important; }
    .count-badge { 
        background-color: #002366; color: white !important; padding: 12px; 
        border-radius: 10px; font-size: 1.2rem; font-weight: bold; text-align: center;
        margin-bottom: 15px; border: 2px solid #001a4d;
    }
    .match-box { 
        border: 1px solid #e6e9ef; border-radius: 8px; padding: 15px; 
        margin-bottom: 10px; background-color: #f8f9fa;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 사이드바 ---
with st.sidebar:
    st.title("🎾 두류테니스")
    all_ev = sorted([d for d in os.listdir(DATA_DIR) if os.path.isdir(os.path.join(DATA_DIR, d))], reverse=True)
    sel_ev = st.selectbox("📅 대회 선택", ["선택 안함"] + all_ev)
    is_admin = (st.text_input("🔑 관리자 암호", type="password") == "0502")
    menu = st.radio("메뉴", ["전체랭킹", "대진 및 경기현황"] + (["관리자 설정"] if is_admin else []))

EV_PATH = os.path.join(DATA_DIR, sel_ev) if sel_ev != "선택 안함" else None
MATCH_FILE = os.path.join(EV_PATH, "matches.csv") if EV_PATH else None

# --- 4. 메뉴별 기능 ---

if menu == "대진 및 경기현황":
    if not MATCH_FILE: st.info("대회를 선택하세요.")
    else:
        full_df = pd.read_csv(MATCH_FILE)
        groups = sorted(full_df['그룹'].unique())
        tabs = st.tabs([f"🏆 {g}그룹" for g in groups])
        
        for i, g in enumerate(groups):
            with tabs[i]:
                g_df = full_df[full_df['그룹'] == g].copy()
                st.subheader(f"📊 {g}조 경기 입력")
                for idx, row in g_df.iterrows():
                    with st.container():
                        st.markdown("<div class='match-box'>", unsafe_allow_html=True)
                        c1, c2, c3, c4, c5 = st.columns([0.8, 3, 0.5, 3, 1.5])
                        c1.write(f"**M-{row['순서']}**")
                        s_a = c2.number_input(f"{row['팀A']}", 0, 10, int(row['A점수']), key=f"sA_{g}_{idx}")
                        c3.markdown("<center>vs</center>", unsafe_allow_html=True)
                        s_b = c4.number_input(f"{row['팀B']}", 0, 10, int(row['B점수']), key=f"sB_{g}_{idx}")
                        if c5.button("저장", key=f"btn_{g}_{idx}", use_container_width=True):
                            full_df.loc[idx, ['A점수', 'B점수', '완료']] = [s_a, s_b, 1]
                            save_data(full_df, MATCH_FILE)
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

elif menu == "관리자 설정" and is_admin:
    t1, t2 = st.tabs(["👥 회원 DB 관리", "⚔️ 랭킹순 그룹 배정"])
    
    with t2:
        if not EV_PATH: st.error("대회를 먼저 선택하세요.")
        else:
            all_mems = load_members().sort_values('랭킹')
            st.subheader("1. 참가자 확정")
            c1, c2 = st.columns([1, 1])
            with c1:
                is_all = st.checkbox("전체 회원 선택")
                sel_names = [r['성명'] for _, r in all_mems.iterrows() if st.checkbox(f"{r['성명']} (R-{r['랭킹']})", value=is_all, key=f"chk_{r['성명']}")]
            
            with c2:
                raw_input = st.text_area("명단 붙여넣기 (쉼표, 공백, 줄바꿈 자동 인식)", placeholder="이름 이름 이름...")
                # [핵심] 쉼표, 공백, 줄바꿈을 모두 구분자로 사용하여 이름 추출
                manual_names = re.split(r'[,\s\n]+', raw_input)
                manual_names = [n.strip() for n in manual_names if n.strip()]
                
                final_p = list(set(sel_names + manual_names))
                st.markdown(f"<div class='count-badge'>선택된 총 인원: {len(final_p)}명</div>", unsafe_allow_html=True)
                if final_p: st.caption(f"확인된 명단: {', '.join(final_p)}")

            st.divider()
            st.subheader("2. 그룹별 인원 배정 (상위 랭커부터)")
            p_sorted = all_mems[all_mems['성명'].isin(final_p)].sort_values('랭킹')['성명'].tolist()
            
            g_count = st.number_input("그룹 수", 1, 10, 2)
            group_setup = {}
            current_pos = 0
            total_assigned = 0

            for i in range(g_count):
                label = chr(65 + i)
                size = st.number_input(f"{label}그룹 인원수", 0, len(p_sorted), 0, key=f"size_{label}")
                group_setup[label] = p_sorted[current_pos : current_pos + size]
                current_pos += size
                total_assigned += size
                if group_setup[label]:
                    st.success(f"{label}조 명단: {', '.join(group_setup[label])}")

            if total_assigned != len(final_p):
                st.warning(f"인원이 맞지 않습니다. (참가 {len(final_p)}명 / 배정 {total_assigned}명)")
            elif st.button("⚔️ 랭킹 기반 대진표 생성", use_container_width=True):
                matches = []
                for label, members in group_setup.items():
                    for idx, combo in enumerate(itertools.combinations(members, 2)):
                        matches.append({"그룹": label, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수": 0, "B점수": 0, "완료": 0})
                save_data(pd.DataFrame(matches), MATCH_FILE)
                st.balloons()
