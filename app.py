        elif order == "레벨 높은 순":
            records.sort(key=lambda x: x["level"], reverse=True)
        else:
            records.sort(key=lambda x: x["number"])
        if records:
            size = 9
            total = (len(records) + size - 1) // size
            page_no = st.selectbox("페이지", list(range(1, total + 1)), key="collection_page")
            cols = st.columns(3)
            for i, pokemon in enumerate(records[(page_no - 1) * size:page_no * size]):
                with cols[i % 3]:
                    with st.container(border=True):
                        pokemon_image(pokemon, 150)
                        st.markdown(f'**{esc(pokemon["name"])}** {"✨" if pokemon["shiny"] else ""}')
                        st.caption(f'No. {pokemon["number"]:04d} · Lv.{pokemon["level"]} · {pokemon["rarity"]}')
                        if pokemon["uid"] == p["partner_uid"]:
                            st.success("🌙 현재 수면 파트너")
                        else:
                            if st.button("🌙 함께 자기", key=f'partner_{pokemon["uid"]}', use_container_width=True):
                                p["partner_uid"] = pokemon["uid"]
                                st.session_state.sf_notice = f'{pokemon["name"]}을(를) 수면 파트너로 선택했어요.'
                                go("home")
        else:
            st.info("조건에 맞는 포켓몬이 없어요.")
        if st.button("🎲 더 뽑기", use_container_width=True):
            draw_pokemon()

    elif page == "sleep":
        if not p["sleep_start"]:
            st.markdown('<div class="hero">🌙 수면 시작</div><div class="subtitle">포켓몬과 함께 편안한 시간을 준비해요.</div>', unsafe_allow_html=True)
            pokemon_image(partner(), 220)
            if st.button("🌙 수면 추적 시작", use_container_width=True):
                start_sleep()
        else:
            started = parse_dt(p["sleep_start"])
            st.markdown(f'<div class="sleep-scene"><h2>🌙 수면 기록 중</h2><p>함께하는 포켓몬: {esc(partner()["name"])}</p><p>기록 시작: {started.strftime("%m월 %d일 %H:%M")}</p><p>잠에서 깬 뒤 아래 버튼을 눌러 주세요.</p></div>', unsafe_allow_html=True)
            if st.button("☀️ 수면 종료", use_container_width=True):
                finish_sleep()
            st.caption("화면 안에서 이동해도 시작 시각이 유지돼요. 새로고침·재접속으로 세션이 바뀌면 기록이 사라질 수 있어요.")

    elif page == "result":
        if not p["records"]:
            st.info("종료한 수면 기록이 없어요.")
        else:
            r = p["records"][-1]
            elapsed, est, score = summary(r)
            st.markdown('<div class="hero">☀️ 수면 결과</div>', unsafe_allow_html=True)
            pokemon_image(partner(), 200)
            a, b, c = st.columns(3)
            a.metric("기록 시간", f"{elapsed:.1f}시간")
            b.metric("추정 수면 시간", f"{est:.1f}시간")
            c.metric("목표 시간 달성도", f"{score}점")
            message = "목표 시간에 도달했어요!" if score >= 100 else "목표에 가까워지고 있어요." if score >= 80 else "기록된 시간이 목표보다 짧아요."
            st.info(f'{partner()["name"]}: {message}')
            st.caption("점수는 목표 수면 시간 대비 기록의 비율을 나타냅니다. 객관적인 수면의 질 점수가 아닙니다.")
            with st.form(f'review_{r["uid"]}'):
                max_awake = max(0., elapsed * 60)
                awake = st.number_input("잠드는 데 걸린 시간 + 중간에 깨어 있던 시간(분)", min_value=0., max_value=max_awake, value=min(float(r["awake_minutes"]), max_awake), step=5.)
                feelings = ["미입력", "개운함", "보통", "피곤함", "매우 피곤함"]
                feeling = st.selectbox("일어난 뒤 느낌", feelings, index=feelings.index(r["feeling"]) if r["feeling"] in feelings else 0)
                memo = st.text_area("메모", value=r["memo"], max_chars=500)
                if st.form_submit_button("기록 반영"):
                    r.update({"awake_minutes": float(awake), "feeling": feeling, "memo": memo})
                    st.rerun()
            if st.button("📝 Sleep Cycle 결과를 별도 기록",use_container_width=True): go("cycle")
            st.warning("오늘 정확히 언제 졸음이 발생할지는 이 기록만으로 예측할 수 없어요. 낮 시간 화면에서 실제 졸림을 점검해 주세요.")
            if st.button("☀️ 낮 시간으로", use_container_width=True):
                go("day")

    elif page == "cycle":
        cycle_page()

    elif page == "nap":
        nap_page()

    elif page == "analysis":
        analysis_page()

    elif page == "day":
        day_page()

    elif page == "history":
        st.subheader("📝 Sleep Cycle 지표 기록")
        for record in sorted(p["cycles"], key=lambda r:r["end"], reverse=True)[:100]:
            with st.expander(f'{parse_dt(record["end"]):%Y/%m/%d} · Sleep Cycle 수동 입력'):
                st.write(f'{parse_dt(record["start"]):%m/%d %H:%M} → {parse_dt(record["end"]):%m/%d %H:%M}')
                for key,(label,_) in CYCLE_FIELDS.items():
                    st.write(f'{label}: {record[key] if record[key] is not None else "미입력"}')
                if record["memo"]: st.write(record["memo"])
        st.caption("수정·삭제는 Sleep Cycle 입력 화면에서 기록을 선택해 주세요.")
        st.divider()
        st.markdown('<div class="hero">📚 수면 기록 보관함</div>', unsafe_allow_html=True)
        if not p["records"]:
            st.info("수면 추적을 완료하면 기록이 쌓여요.")
        else:
            entries = list(reversed(p["records"]))
            for r in entries[:100]:
                elapsed, est, score = summary(r)
                end = parse_dt(r["end"])
                with st.expander(f'🌙 {end:%Y.%m.%d} · 기록 {elapsed:.1f}시간 · 목표 달성도 {score}점'):
                    st.write(f'시작: {parse_dt(r["start"]):%m/%d %H:%M} / 종료: {end:%m/%d %H:%M}')
                    st.write(f'추정 수면 시간: {est:.1f}시간 · 기상 후 느낌: {r["feeling"]}')
                    if r["memo"]:
                        st.write(r["memo"])
            if len(entries) > 100:
                st.caption("화면에는 최근 100개만 표시되며 저장 파일에는 전체 기록이 포함됩니다.")

    elif page == "settings":
        st.markdown('<div class="hero">⚙️ 설정</div>', unsafe_allow_html=True)
        with st.form("settings"):
            goal = st.number_input("목표 수면 시간", min_value=1., max_value=14., value=float(p["goal_hours"]), step=.5)
            if st.form_submit_button("저장"):
                p["goal_hours"] = float(goal)
                st.success("목표 수면 시간을 저장했어요.")
        st.subheader("🌙 수면 파트너")
        pokemon_image(partner(), 180)
        st.write(f'현재 파트너: **{partner()["name"]}**')
        if st.button("📦 보관함에서 파트너 선택", use_container_width=True):
            go("collection")
        st.divider()
        st.subheader("⌚ 웨어러블 연결")
        st.info("현재는 웨어러블 기기와 연결되어 있지 않아요. 실제 블루투스 연결과 데이터 동기화는 사용 기기에 맞는 별도 기능이 필요해요.")
        st.caption("수면 기록, 포켓몬, 파트너 선택은 JSON으로 저장할 수 있습니다. 이 버전은 Streamlit 서버와 인터넷 연결이 필요하며 실제 계정 로그인 및 오프라인 실행은 지원하지 않습니다.")

with st.expander("📖 안내 및 측정 한계"):
    st.write("Sleep Cycle 지표는 수동 입력하며 계정 자동 연동이 아닙니다. 낮잠·시간대별 졸림 기록은 수정·삭제할 수 있습니다. 기존 버튼 수면 기록과 Sleep Cycle 기록은 별도 보관해 중복 합산하지 않습니다. Sleep Free는 수면 습관을 기록하는 앱입니다. 포켓몬은 수면 파트너로만 사용되며 배틀·코인·레벨업은 없습니다. 수면 시작/종료 버튼만으로 수면의 질이나 수면 단계를 측정할 수는 없습니다. 점수는 목표 시간 달성도이고, 졸림 상태는 사용자가 직접 입력한 값입니다. 웹 앱을 떠난 상태의 실시간 알림, 자동 블루투스 연결, 재접속 시 자동 저장은 현재 버전에 포함되지 않습니다.")
