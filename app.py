elif menu == "관리자 설정" and is_admin:
    st.markdown("<h1 style='text-align:center;'>⚙️ 관리자 컨트롤 타워</h1>", unsafe_allow_html=True)
    
    # 에러의 원인: 여기서 t1, t2, t3를 먼저 정의해야 합니다!
    t1, t2, t3 = st.tabs(["📁 대회 관리", "⚔️ 참가자 및 대진 생성", "📈 결과 반영"])

    with t1:
        st.subheader("대회 폴더 관리")
        new_ev_name = st.text_input("새 대회 명칭 (예: 2026_05_정기전)")
        if st.button("대회 생성"):
            if new_ev_name:
                os.makedirs(os.path.join(DATA_DIR, new_ev_name), exist_ok=True)
                st.success(f"'{new_ev_name}' 대회가 생성되었습니다.")
                st.rerun()
            else:
                st.error("대회 명칭을 입력하세요.")

    with t2:
        st.subheader("1. 참가자 입력 및 그룹 배정")
        raw_names = st.text_area("명단 붙여넣기 (쉼표/공백/엔터 자동인식)", placeholder="홍길동 김철수...")
        # 이름 추출 로직
        p_list = [n.strip() for n in re.split(r'[,\s\n]+', raw_names) if n.strip()]
        st.info(f"✅ 현재 인식된 총 인원: {len(p_list)}명")

        # 랭킹 데이터 로드 및 정렬
        all_mems = load_members()
        p_ranked = all_mems[all_mems['성명'].isin(p_list)].sort_values('랭킹')
        p_sorted_names = p_ranked['성명'].tolist()
        
        # DB에 없는 사람은 하위권으로 추가
        not_in_db = [name for name in p_list if name not in p_sorted_names]
        final_p_sorted = p_sorted_names + not_in_db

        col1, col2 = st.columns(2)
        with col1:
            g_cnt = st.number_input("그룹 수", 1, 10, 1)
            mode = st.selectbox("경기 방식", ["고정페어 복식", "KDK 복식", "단식"])
        
        with col2:
            group_sizes = []
            st.write("📋 그룹별 인원 설정 (상위 랭커부터 배정)")
            temp_remaining = len(final_p_sorted)
            for i in range(g_cnt):
                g_label = chr(65 + i)
                size = st.number_input(f"{g_label}그룹 인원수", 0, len(final_p_sorted), 0, key=f"g_size_{g_label}")
                group_sizes.append(size)
                temp_remaining -= size
            
            if temp_remaining != 0:
                st.warning(f"인원 불일치: {temp_remaining}명이 남거나 초과되었습니다.")

        if st.button("⚔️ 맞춤 대진표 생성", use_container_width=True):
            if not EV_PATH:
                st.error("사이드바에서 대회를 먼저 선택해주세요.")
            elif sum(group_sizes) != len(final_p_sorted):
                st.error("그룹별 인원 합계가 전체 인원과 다릅니다.")
            else:
                matches = []
                current_idx = 0
                for i, size in enumerate(group_sizes):
                    g_label = chr(65 + i)
                    g_members = final_p_sorted[current_idx : current_idx + size]
                    current_idx += size
                    
                    if not g_members: continue

                    # 고정페어: 1위-꼴찌 조합
                    if mode == "고정페어 복식":
                        pairs = []
                        temp_m = g_members.copy()
                        while len(temp_m) >= 2:
                            p1 = temp_m.pop(0)
                            p2 = temp_m.pop(-1)
                            pairs.append(f"{p1}/{p2}")
                        for idx, combo in enumerate(itertools.combinations(pairs, 2)):
                            matches.append({"그룹": g_label, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수": 0, "B점수": 0, "완료": 0})
                    
                    # KDK: 랜덤 복식 조합
                    elif mode == "KDK 복식":
                        # 4명씩 묶어 경기 생성 (예시 로직)
                        if len(g_members) >= 4:
                            for idx, combo in enumerate(itertools.combinations(g_members, 4)):
                                c = list(combo)
                                random.shuffle(c)
                                matches.append({"그룹": g_label, "순서": idx+1, "팀A": f"{c[0]}/{c[1]}", "팀B": f"{c[2]}/{c[3]}", "A점수": 0, "B점수": 0, "완료": 0})
                    
                    # 단식
                    else:
                        for idx, combo in enumerate(itertools.combinations(g_members, 2)):
                            matches.append({"그룹": g_label, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수": 0, "B점수": 0, "완료": 0})

                save_data(pd.DataFrame(matches), MATCH_FILE)
                st.success(f"{mode} 대진표 생성 완료!")
                st.balloons()

    with t3:
        st.subheader("대회 결과 반영")
        st.write("경기가 모두 종료된 후 포인트 합산 기능을 사용하세요.")
