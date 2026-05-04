import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"

# ----------------------
# 상태 초기화
# ----------------------
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False

if "players" not in st.session_state:
    st.session_state.players = []

if "matches" not in st.session_state:
    st.session_state.matches = []

if "result_df" not in st.session_state:
    st.session_state.result_df = None

# ----------------------
# 사이드바 메뉴
# ----------------------
with st.sidebar:
    st.title("🎾 두류테니스클럽")

    menu = st.radio("메뉴 선택", [
        "🏆 두류랭킹",
        "👥 참가자 명단",
        "🎮 대진 및 진행",
        "📊 경기 결과",
        "🔐 관리자"
    ])

    if menu == "🔐 관리자":
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            if pw == "0502":
                st.session_state.is_admin = True
                st.success("관리자 로그인 성공")
            else:
                st.error("비밀번호 오류")

# ----------------------
# 랭킹 파일 로드 (엑셀 완전 대응)
# ----------------------
def load_ranking_file(uploaded_file):
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df.columns = df.columns.str.strip()

    current_col = None
    prev_col = None

    for col in df.columns:
        if "랭킹포인트" in col and "최종" in col:
            current_col = col
        elif "랭킹포인트" in col and "전" in col:
            prev_col = col

    if current_col is None:
        st.error("❌ '현재 랭킹포인트' 컬럼 없음")
        st.stop()

    rename_map = {}
    if "성명" in df.columns:
        rename_map["성명"] = "이름"

    rename_map[current_col] = "현재포인트"
    df = df.rename(columns=rename_map)

    if prev_col:
        df = df.rename(columns={prev_col: "이전포인트"})
    else:
        df["이전포인트"] = df["현재포인트"]

    if "부과점" not in df.columns:
        df["부과점"] = ""

    return df

# ----------------------
# 랭킹 불러오기
# ----------------------
def load_rank():
    if os.path.exists(RANK_FILE):
        return pd.read_csv(RANK_FILE)
    return pd.DataFrame(columns=["이름","현재포인트","이전포인트","부과점"])

# ----------------------
# 1️⃣ 두류랭킹
# ----------------------
if menu == "🏆 두류랭킹":

    st.title("🏆 두류 랭킹")

    uploaded = st.file_uploader("📂 랭킹 업로드 (csv/xlsx)")

    if uploaded:
        df = load_ranking_file(uploaded)
        df.to_csv(RANK_FILE, index=False, encoding="utf-8-sig")
        st.success("랭킹 업로드 완료")

    rank_df = load_rank()

    if len(rank_df) == 0:
        st.warning("랭킹 없음")
    else:
        # 변동 계산 (핵심 정확 로직)
        rank_df["변동값"] = rank_df["현재포인트"] - rank_df["이전포인트"]

        def arrow(x):
            if x > 0:
                return f"⬆ {x}"
            elif x < 0:
                return f"⬇ {abs(x)}"
            else:
                return "-"

        rank_df["변동"] = rank_df["변동값"].apply(arrow)

        # 정렬
        rank_df = rank_df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        rank_df["순위"] = rank_df.index + 1

        st.dataframe(rank_df, use_container_width=True)

# ----------------------
# 2️⃣ 참가자
# ----------------------
elif menu == "👥 참가자 명단":

    st.title("👥 참가자")

    players_input = st.text_area("쉼표로 입력")

    if st.button("저장"):
        st.session_state.players = [p.strip() for p in players_input.split(",") if p.strip()]
        st.success("저장 완료")

    st.write("참가자:", st.session_state.players)

# ----------------------
# 3️⃣ 대진
# ----------------------
elif menu == "🎮 대진 및 진행":

    st.title("🎮 대진")

    if not st.session_state.players:
        st.warning("참가자 먼저 입력")
    else:
        players = st.session_state.players

        matches = []
        for i in range(len(players)):
            for j in range(i+1, len(players)):
                matches.append((players[i], players[j]))

        st.session_state.matches = matches

        for m in matches:
            st.write(f"{m[0]} vs {m[1]}")

# ----------------------
# 4️⃣ 경기 결과
# ----------------------
elif menu == "📊 경기 결과":

    st.title("📊 경기 결과")

    if not st.session_state.matches:
        st.warning("대진 먼저 생성")
    else:
        scores = []

        for m in st.session_state.matches:
            col1, col2 = st.columns(2)
            with col1:
                s1 = st.number_input(m[0], key=f"{m[0]}_{m[1]}_1")
            with col2:
                s2 = st.number_input(m[1], key=f"{m[0]}_{m[1]}_2")

            scores.append((m[0], m[1], s1, s2))

        if st.button("결과 계산"):
            result = {}

            for a,b,s1,s2 in scores:
                for p in [a,b]:
                    if p not in result:
                        result[p] = {"승":0,"패":0}

                if s1 > s2:
                    result[a]["승"] +=1
                    result[b]["패"] +=1
                elif s2 > s1:
                    result[b]["승"] +=1
                    result[a]["패"] +=1

            df = pd.DataFrame(result).T.reset_index()
            df.columns = ["이름","승","패"]
            df = df.sort_values("승", ascending=False).reset_index(drop=True)
            df["순위"] = df.index + 1

            st.session_state.result_df = df
            st.dataframe(df)

        # 🔥 관리자만 반영
        if st.session_state.is_admin and st.session_state.result_df is not None:
            if st.button("🔥 포인트 반영"):

                rank_df = load_rank()

                # 👉 이전포인트 저장 (핵심)
                rank_df["이전포인트"] = rank_df["현재포인트"]

                for _, row in st.session_state.result_df.iterrows():
                    name = row["이름"]
                    r = row["순위"]

                    pt = 7 if r==1 else 5 if r==2 else 3 if r==3 else 1

                    if name in rank_df["이름"].values:
                        rank_df.loc[rank_df["이름"]==name, "현재포인트"] += pt
                    else:
                        new = pd.DataFrame([[name, pt, 0, ""]],
                            columns=["이름","현재포인트","이전포인트","부과점"])
                        rank_df = pd.concat([rank_df,new], ignore_index=True)

                rank_df.to_csv(RANK_FILE, index=False, encoding="utf-8-sig")

                st.success("랭킹 반영 완료")
