# 🎾 두류 테니스 클럽 FINAL RANKING SYSTEM (엑셀 완전 연동)
# 실행: streamlit run app.py

import streamlit as st
import pandas as pd
import os
from datetime import datetime

st.set_page_config(layout="wide")

RANK_FILE = "ranking_master.csv"

# ----------------------
# 파일 로드 (CSV + XLSX 자동 인식)
# ----------------------
def load_ranking(file):
    if file.name.endswith(".csv"):
        df = pd.read_csv(file)
    else:
        df = pd.read_excel(file)

    # 컬럼 자동 정리
    df.columns = [c.strip() for c in df.columns]

    # 필요한 컬럼 매핑
    col_map = {
        "성명": "이름",
        "랭킹": "순위",
        "4월(최종) 랭킹포인트": "현재포인트",
        "3월(전) 랭킹포인트": "이전포인트",
        "부과점": "보너스"
    }

    for k,v in col_map.items():
        if k in df.columns:
            df.rename(columns={k:v}, inplace=True)

    return df

# ----------------------
# 업로드
# ----------------------
st.title("🎾 두류랭킹 시스템")

uploaded = st.file_uploader("📂 랭킹 파일 업로드 (csv / xlsx)")

if uploaded:
    rank_df = load_ranking(uploaded)
    rank_df.to_csv(RANK_FILE, index=False, encoding="utf-8-sig")
    st.success("랭킹 업로드 완료")

# ----------------------
# 랭킹 로드
# ----------------------
if os.path.exists(RANK_FILE):
    rank_df = pd.read_csv(RANK_FILE)

    # 변동 계산
    changes = []

    for _,row in rank_df.iterrows():
        if "현재포인트" in row and "이전포인트" in row:
            diff = row["현재포인트"] - row["이전포인트"]
            if diff > 0:
                changes.append(f"⬆ {diff}")
            elif diff < 0:
                changes.append(f"⬇ {abs(diff)}")
            else:
                changes.append("-")
        else:
            changes.append("-")

    rank_df["변동"] = changes

    # 정렬
    rank_df = rank_df.sort_values("현재포인트", ascending=False)
    rank_df["순위"] = range(1, len(rank_df)+1)

    st.subheader("🏆 두류 랭킹")
    st.dataframe(rank_df, use_container_width=True)

# ----------------------
# 경기 결과 반영
# ----------------------
st.subheader("🎯 경기 결과 반영")

result_input = st.text_area("결과 입력 (예: 홍길동,김철수,이영희)")

if st.button("점수 반영"):
    if os.path.exists(RANK_FILE):
        rank_df = pd.read_csv(RANK_FILE)

        players = [p.strip() for p in result_input.split(",") if p.strip()]

        for i,p in enumerate(players):
            if i == 0:
                pt = 7
            elif i == 1:
                pt = 5
            elif i == 2:
                pt = 3
            else:
                pt = 1

            if p in rank_df["이름"].values:
                rank_df.loc[rank_df["이름"]==p, "현재포인트"] += pt
            else:
                new = pd.DataFrame([[len(rank_df)+1, p, pt, 0, ""]],
                                   columns=["순위","이름","현재포인트","이전포인트","보너스"])
                rank_df = pd.concat([rank_df, new])

        # 이전포인트 갱신 (다음날 기준)
        rank_df["이전포인트"] = rank_df["현재포인트"]

        rank_df.to_csv(RANK_FILE, index=False, encoding="utf-8-sig")

        st.success("랭킹 업데이트 완료")

# ----------------------
# 설명
# ----------------------
st.markdown("""
### 📌 지원 형식
- CSV / XLSX 모두 가능
- 컬럼 자동 인식:
  - 성명 → 이름
  - 랭킹 → 순위
  - 4월(최종) 랭킹포인트 → 현재포인트
  - 3월(전) 랭킹포인트 → 이전포인트
  - 부과점 → 보너스

### 📊 기능
- 자동 순위 계산
- 상승/하락 화살표
- 점수 반영 후 다음날 기준 자동 업데이트
""")
