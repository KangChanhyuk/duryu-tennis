# [관리자 설정] - "⚔️ 참가자 및 대진 생성" 탭 내부 로직

with t2:
    st.subheader("1. 참가자 입력 및 그룹 배정")
    raw_names = st.text_area("명단 붙여넣기 (쉼표/공백/엔터 자동인식)", placeholder="홍길동 김철수...")
    p_list = [n.strip() for n in re.split(r'[,\s\n]+', raw_names) if n.strip()]
    st.info(f"✅ 현재 인식된 총 인원: {len(p_list)}명")

    # 랭킹 데이터 로드 및 참가자 필터링
    all_mems = load_members()
    # 전체 회원 DB에 있는 사람만 랭킹순으로 정렬
    p_ranked = all_mems[all_mems['성명'].isin(p_list)].sort_values('랭킹')
    p_sorted_names = p_ranked['성명'].tolist()
    
    # DB에 없는 이름은 하위 랭킹으로 간주하여 뒤에 추가
    not_in_db = [name for name in p_list if name not in p_sorted_names]
    final_p_sorted = p_sorted_names + not_in_db

    col1, col2 = st.columns(2)
    with col1:
        g_cnt = st.number_input("그룹 수", 1, 10, 2)
        mode = st.selectbox("경기 방식", ["고정페어 복식", "KDK 복식", "단식"])
    
    with col2:
        group_sizes = []
        st.write("📋 그룹별 인원 설정 (상위 랭커부터 배정)")
        remaining_p = len(final_p_sorted)
        for i in range(g_cnt):
            g_label = chr(65 + i)
            # 고정페어와 KDK는 짝수(복식)여야 하므로 2단위 설정을 권장
            size = st.number_input(f"{g_label}그룹 인원수", 0, remaining_p, 0, key=f"g_size_{g_label}")
            group_sizes.append(size)
            remaining_p -= size
        
        if remaining_p > 0:
            st.warning(f"미배정 인원: {remaining_p}명")

    if st.button("⚔️ 맞춤 대진표 생성", use_container_width=True):
        if sum(group_sizes) != len(final_p_sorted):
            st.error("설정한 그룹별 인원 합계가 전체 인원과 다릅니다.")
        else:
            matches = []
            current_idx = 0
            
            for i, size in enumerate(group_sizes):
                g_label = chr(65 + i)
                g_members = final_p_sorted[current_idx : current_idx + size]
                current_idx += size
                
                if not g_members: continue

                # --- 경기 방식별 로직 ---
                
                # 1. 고정페어 복식 (1위-꼴찌, 2위-차하위 조합)
                if mode == "고정페어 복식":
                    pairs = []
                    temp_m = g_members.copy()
                    while len(temp_m) >= 2:
                        p1 = temp_m.pop(0) # 상위 랭커
                        p2 = temp_m.pop(-1) # 하위 랭커
                        pairs.append(f"{p1}/{p2}")
                    
                    # 페어 간 풀리그 대진 생성
                    for idx, combo in enumerate(itertools.combinations(pairs, 2)):
                        matches.append({"그룹": g_label, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수": 0, "B점수": 0, "완료": 0})

                # 2. KDK 복식 (매 경기 파트너 변경 - 랜덤)
                elif mode == "KDK 복식":
                    # KDK는 복잡한 수식이 필요하므로 여기서는 모든 가능한 조합 중 랜덤 추출
                    # (실제 KDK는 인원수에 따른 매칭표가 있으나 기본 로직으로 구현)
                    for idx, combo in enumerate(itertools.combinations(g_members, 4)):
                        c = list(combo)
                        random.shuffle(c)
                        matches.append({"그룹": g_label, "순서": idx+1, "팀A": f"{c[0]}/{c[1]}", "팀B": f"{c[2]}/{c[3]}", "A점수": 0, "B점수": 0, "완료": 0})
                
                # 3. 단식
                else:
                    for idx, combo in enumerate(itertools.combinations(g_members, 2)):
                        matches.append({"그룹": g_label, "순서": idx+1, "팀A": combo[0], "팀B": combo[1], "A점수": 0, "B점수": 0, "완료": 0})

            save_data(pd.DataFrame(matches), MATCH_FILE)
            st.success(f"{mode} 대진표 생성 완료!")
            st.balloons()
