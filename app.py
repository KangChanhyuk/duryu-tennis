import streamlit as st
import pandas as pd
import random
import os

st.set_page_config(layout="wide")

# =============================
# 파일 초기 생성
# =============================
RANK_FILE = "ranking_master.csv"

if not os.path.exists(RANK_FILE):
    pd.DataFrame(columns=["이름", "현재포인트", "이전포인트"]).to_csv(RANK_FILE, index=False)

# =============================
# 상태 초기화
# =============================
def init_state():
    defaults = {
        "players": [],
        "groups": {},
        "pairs": {},
        "schedule": {},
        "scores": {},
        "is_admin": False
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# =============================
# 엑셀 유연 인식
# =============================
def smart_read(file):
    try:
        if file.name.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)
    except Exception as e:
        st.error(f"파일 읽기 실패: {e}")
        return None

    df.columns = [str(c).lower().strip() for c in df.columns]

    name_col = None
    point_col = None
    prev_col = None

    for c in df.columns:
        if "이름" in c or "name" in c:
            name_col = c
        elif "포인트" in c or "point" in c:
            if point_col is None:
                point_col = c
            else:
                prev_col = c

    if name_col is None:
        st.error("이름 컬럼 없음")
        return None

    df["이름"] = df[name_col].astype(str).str.strip().str.replace(" ", "")
    df["현재포인트"] = pd.to_numeric(df[point_col], errors="coerce").fillna(0) if point_col else 0
    df["이전포인트"] = pd.to_numeric(df[prev_col], errors="coerce").fillna(0) if prev_col else 0

    df = df[["이름", "현재포인트", "이전포인트"]]
    df = df.drop_duplicates(subset="이름")

    return df

# =============================
# 랭킹 로드 / 저장
# =============================
def load_rank():
    df = pd.read_csv(RANK_FILE)
    df["현재포인트"] = pd.to_numeric(df["현재포인트"], errors="coerce").fillna(0)
    df["이전포인트"] = pd.to_numeric(df["이전포인트"], errors="coerce").fillna(0)
    return df

def save_rank(df):
    df.to_csv(RANK_FILE, index=False)

# =============================
# 유틸
# =============================
def clean(x):
    return str(x).strip().replace(" ", "")

def team_name(t):
    # t는 항상 tuple로 처리
    t = tuple(t)
    return t[0] if len(t) == 1 else f"{t[0]}&{t[1]}"

# =============================
# 그룹 생성 (랭킹 기반)
# 버그수정: 랭킹에 없는 신규 플레이어도 배정되도록
# =============================
def make_groups(players, sizes):
    rank = load_rank().sort_values("현재포인트", ascending=False)

    # 랭킹에 있는 플레이어는 랭킹 순서로, 없는 플레이어는 뒤에 추가
    ordered_in_rank = [p for p in rank["이름"] if p in players]
    not_in_rank = [p for p in players if p not in ordered_in_rank]
    ordered = ordered_in_rank + not_in_rank

    groups = {g: [] for g in sizes}

    # 각 그룹에 몇 명씩 넣을지 인덱스 리스트 생성
    idx = []
    for g, s in sizes.items():
        idx += [g] * s

    for i, p in enumerate(ordered):
        if i < len(idx):
            groups[idx[i]].append(p)
        # 인원 초과분은 마지막 그룹에 추가
        else:
            last_group = list(groups.keys())[-1]
            groups[last_group].append(p)

    return groups

# =============================
# 페어 생성
# 버그수정: 홀수 인원 처리, KDK 홀수 처리
# =============================
def make_pairs(players, mode):
    if mode == "고정페어":
        pairs = []
        n = len(players)
        for i in range(n // 2):
            pairs.append((players[i], players[n - 1 - i]))
        # 홀수면 가운데 한 명은 단식으로
        if n % 2 == 1:
            pairs.append((players[n // 2],))
        return pairs

    if mode == "KDK":
        temp = players[:]
        random.shuffle(temp)
        pairs = []
        for i in range(0, len(temp) - 1, 2):
            pairs.append((temp[i], temp[i + 1]))
        # 홀수면 마지막 한 명은 단식으로
        if len(temp) % 2 == 1:
            pairs.append((temp[-1],))
        return pairs

    # 단식
    return [(p,) for p in players]

# =============================
# 2코트 대진 생성
# 버그수정: teams를 모두 tuple로 통일하여 해시 오류 방지
# =============================
def make_schedule(teams):
    # teams를 모두 tuple로 변환
    teams = [tuple(t) for t in teams]

    matches = [
        (teams[i], teams[j])
        for i in range(len(teams))
        for j in range(i + 1, len(teams))
    ]
    random.shuffle(matches)

    rounds = []

    while matches:
        used = set()
        r = []

        for m in matches[:]:
            t1, t2 = m
            if t1 in used or t2 in used:
                continue

            r.append(m)
            used.add(t1)
            used.add(t2)
            matches.remove(m)

            if len(r) == 2:
                break

        if not r:
            break

        rounds.append(r)

    return rounds

# =============================
# 메뉴
# =============================
menu = st.sidebar.radio("메뉴", ["두류랭킹", "대진 및 경기", "경기 결과", "관리자"])

# =============================
# 랭킹
# =============================
if menu == "두류랭킹":
    st.title("🏆 두류랭킹")

    df = load_rank()

    if len(df) == 0:
        st.warning("관리자에서 엑셀 업로드 필요")
    else:
        df = df.sort_values("현재포인트", ascending=False).reset_index(drop=True)
        df.insert(0, "랭킹", df.index + 1)
        st.dataframe(df, use_container_width=True, hide_index=True)

# =============================
# 대진 및 경기
# 버그수정: 저장 후 st.rerun() 추가, tuple 타입 통일
# =============================
elif menu == "대진 및 경기":
    st.title("🎾 대진")

    if not st.session_state.schedule:
        st.warning("관리자에서 대진 생성하세요")
    else:
        tabs = st.tabs(list(st.session_state.schedule.keys()))

        for idx, g in enumerate(st.session_state.schedule.keys()):
            with tabs[idx]:
                rounds = st.session_state.schedule[g]

                for ri, rd in enumerate(rounds):
                    st.markdown(f"### {ri + 1} 라운드")
                    cols = st.columns(2)

                    for i, m in enumerate(rd):
                        t1, t2 = tuple(m[0]), tuple(m[1])
                        n1 = team_name(t1)
                        n2 = team_name(t2)

                        with cols[i]:
                            st.write(f"**{n1}** vs **{n2}**")

                            key = f"{g}_{ri}_{i}"

                            # 이미 저장된 점수가 있으면 기본값으로 표시
                            score_key = (t1, t2)
                            saved = st.session_state.scores.get(score_key, (0, 0))

                            s1 = st.number_input(n1, 0, 50, int(saved[0]), key=key + "_1")
                            s2 = st.number_input(n2, 0, 50, int(saved[1]), key=key + "_2")

                            if st.button(f"저장", key=key + "_btn"):
                                st.session_state.scores[(t1, t2)] = (s1, s2)
                                st.success(f"{n1} {s1} : {s2} {n2} 저장됨")
                                st.rerun()

# =============================
# 경기 결과
# 버그수정: scores 키 타입 통일 (tuple), 결과 표시 개선
# =============================
elif menu == "경기 결과":
    st.title("📊 결과")

    rank = load_rank()
    scores = {}

    if not st.session_state.scores:
        st.warning("저장된 경기 결과가 없습니다")
    else:
        # 결과 요약 표시
        result_rows = []
        for (t1, t2), (s1, s2) in st.session_state.scores.items():
            t1 = tuple(t1)
            t2 = tuple(t2)
            n1 = team_name(t1)
            n2 = team_name(t2)

            if s1 > s2:
                winners = t1
                result = f"🏆 {n1} 승"
            elif s2 > s1:
                winners = t2
                result = f"🏆 {n2} 승"
            else:
                winners = None
                result = "무승부"

            result_rows.append({
                "팀1": n1,
                "점수1": int(s1),
                "점수2": int(s2),
                "팀2": n2,
                "결과": result
            })

            if winners:
                for p in winners:
                    scores[p] = scores.get(p, 0) + 3

        st.dataframe(pd.DataFrame(result_rows), use_container_width=True, hide_index=True)

        # 오늘 획득 포인트 표시
        if scores:
            st.subheader("오늘 획득 포인트")
            today_df = pd.DataFrame(
                [(p, pt) for p, pt in scores.items()],
                columns=["이름", "획득포인트"]
            ).sort_values("획득포인트", ascending=False)
            st.dataframe(today_df, use_container_width=True, hide_index=True)

        if st.button("🏆 랭킹 반영"):
            rank["이전포인트"] = rank["현재포인트"]

            for p, pt in scores.items():
                if p in rank["이름"].values:
                    rank.loc[rank["이름"] == p, "현재포인트"] += pt
                else:
                    new_row = pd.DataFrame(
                        [[p, pt, 0]],
                        columns=["이름", "현재포인트", "이전포인트"]
                    )
                    rank = pd.concat([rank, new_row], ignore_index=True)

            save_rank(rank)
            st.success("랭킹 반영 완료!")
            st.rerun()

# =============================
# 관리자
# 버그수정: 그룹 생성 전 pairs 설정 시 KeyError 방지
# =============================
elif menu == "관리자":
    st.title("⚙ 관리자")

    pw = st.text_input("비밀번호", type="password")

    if pw == "0502":
        st.session_state.is_admin = True

    if st.session_state.is_admin:

        st.subheader("📂 랭킹 업로드")

        file = st.file_uploader("엑셀 업로드", type=["csv", "xlsx"])

        if file:
            df = smart_read(file)
            if df is not None:
                save_rank(df)
                st.success("업로드 완료")

        st.divider()
        st.subheader("👥 참가자 입력")

        raw = st.text_area("쉼표로 구분", value=", ".join(st.session_state.players))

        if st.button("등록"):
            st.session_state.players = [clean(p) for p in raw.split(",") if p.strip()]
            st.success(f"{len(st.session_state.players)}명 등록됨: {', '.join(st.session_state.players)}")

        if st.session_state.players:
            st.write("현재 참가자:", ", ".join(st.session_state.players))

        st.divider()
        st.subheader("🏷 그룹 설정")

        count = st.number_input("그룹 수", 2, 6, 2)
        names = list("ABCDEF")[:count]

        sizes = {}
        total_assigned = 0
        for g in names:
            default_size = max(1, len(st.session_state.players) // count)
            s = st.number_input(f"{g} 인원", 1, 20, default_size, key=f"size_{g}")
            sizes[g] = s
            total_assigned += s

        if st.session_state.players:
            st.info(f"참가자 {len(st.session_state.players)}명 / 배정 {total_assigned}명")

        if st.button("그룹 생성"):
            if not st.session_state.players:
                st.error("먼저 참가자를 등록하세요")
            else:
                st.session_state.groups = make_groups(st.session_state.players, sizes)
                st.session_state.pairs = {}
                st.session_state.schedule = {}
                st.success("그룹 생성 완료")

        # 버그수정: groups가 있을 때만 페어 설정 표시
        if st.session_state.groups:
            st.divider()
            st.subheader("🎾 페어 / 방식 설정")

            for g, group_players in st.session_state.groups.items():
                st.write(f"**그룹 {g}** ({len(group_players)}명): {', '.join(group_players)}")
                mode = st.selectbox(
                    f"{g} 방식",
                    ["단식", "고정페어", "KDK"],
                    key=f"mode_{g}"
                )
                # 방식 선택 즉시 반영 (버튼 없이도 저장)
                st.session_state.pairs[g] = make_pairs(group_players, mode)

            st.divider()
            if st.button("🗓 대진 생성"):
                if not st.session_state.pairs:
                    st.error("페어/방식을 먼저 설정하세요")
                else:
                    st.session_state.schedule = {}
                    st.session_state.scores = {}  # 새 대진 시 기존 점수 초기화
                    for g, teams in st.session_state.pairs.items():
                        if len(teams) >= 2:
                            st.session_state.schedule[g] = make_schedule(teams)
                        else:
                            st.warning(f"그룹 {g}: 팀이 2개 미만이어서 대진을 만들 수 없습니다")
                    st.success("대진 생성 완료! '대진 및 경기' 메뉴에서 확인하세요")

        st.divider()
        st.subheader("🗑 데이터 초기화")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("대진/점수 초기화", type="secondary"):
                st.session_state.schedule = {}
                st.session_state.scores = {}
                st.session_state.pairs = {}
                st.session_state.groups = {}
                st.success("대진 및 점수 초기화 완료")
        with col2:
            if st.button("전체 초기화", type="secondary"):
                for k in ["players", "groups", "pairs", "schedule", "scores"]:
                    st.session_state[k] = [] if k == "players" else {}
                st.success("전체 초기화 완료")
