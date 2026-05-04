import streamlit as st
import pandas as pd
import os

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"

# ----------------------
# 랭킹 파일 로드 (핵심 수정 포함)
# ----------------------
def load_ranking(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # 컬럼 공백 제거
    df.columns = df.columns.str.strip()

    # 컬럼 자동 탐색
    current_col = None
    prev_col = None

    for col in df.columns:
        if "랭킹포인트" in col and "최종" in col:
            current_col = col
        elif "랭킹포인트" in col and "전" in col:
            prev_col = col

    # 필수 체크
    if current_col is None:
        st.error("❌ '현재 랭킹포인트' 컬럼을 찾을 수 없습니다.")
        st.stop()

    # 이름 통일
    rename_map = {}
    if "성명" in df.columns:
        rename_map["성명"] = "이름"

    rename_map[current_col] = "현재포인트"

    df = df.rename(columns=rename_map)

    if prev_col:
        df = df.rename(columns={prev_col: "이전포인트"})
    else:
        df["이전포인트"] = df["현재포인트"]

    # 없는 컬럼 기본 생성
    if "부과점" not in df.columns:
        df["부과점"] = ""

    return df


# ----------------------
# UI 시작
# ----------------------
st.title("🎾 두류랭킹 시스템")

uploaded = st.file_uploader("📂 랭킹 파일 업로드 (csv / xlsx)")

# ----------------------
# 업로드 처리
# ----------------------
if uploaded:
    rank_df = load_ranking(uploaded)
    rank_df.to_csv(RANK_FILE, index=False, encoding="utf-8-sig")
    st.success("✅ 랭킹 업로드 완료")


# ----------------------
# 랭킹 표시
# ----------------------
if os.path.exists(RANK_FILE):
    rank_df = pd.read_csv(RANK_FILE)

    # 안전 체크
    if "현재포인트" not in rank_df.columns:
        st.error("❌ 현재포인트 컬럼 없음. 엑셀 형식 확인 필요")
        st.stop()

    # 변동 계산
    changes = []
    for _, row in rank_df.iterrows():
        try:
            diff = row["현재포인트"] - row["이전포인트"]
        except:
            diff = 0

        if diff > 0:
            changes.append(f"⬆ {diff}")
        elif diff < 0:
            changes.append(f"⬇ {abs(diff)}")
        else:
            changes.append("-")

    rank_df["변동"] = changes

    # 정렬 + 순위 재계산
    rank_df = rank_df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
    rank_df["순위"] = rank_df.index + 1

    st.subheader("🏆 두류 랭킹")
    st.dataframe(rank_df, use_container_width=True)


# ----------------------
# 점수 반영 시스템
# ----------------------
st.subheader("🎯 경기 결과 반영")

result_input = st.text_area("결과 입력 (예: 홍길동,김철수,이영희)")

if st.button("📌 점수 반영"):
    if not os.path.exists(RANK_FILE):
        st.warning("랭킹 파일 먼저 업로드하세요")
        st.stop()

    rank_df = pd.read_csv(RANK_FILE)

    players = [p.strip() for p in result_input.split(",") if p.strip()]

    for i, p in enumerate(players):
        if i == 0:
            pt = 7
        elif i == 1:
            pt = 5
        elif i == 2:
            pt = 3
        else:
            pt = 1

        if p in rank_df["이름"].values:
            rank_df.loc[rank_df["이름"] == p, "현재포인트"] += pt
        else:
            new = pd.DataFrame([[p, pt, pt, ""]],
                               columns=["이름", "현재포인트", "이전포인트", "부과점"])
            rank_df = pd.concat([rank_df, new], ignore_index=True)

    # 👉 다음날 기준 자동 반영 (핵심)
    rank_df["이전포인트"] = rank_df["현재포인트"]

    rank_df.to_csv(RANK_FILE, index=False, encoding="utf-8-sig")

    st.success("✅ 랭킹 업데이트 완료")
