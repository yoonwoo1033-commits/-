import base64
import html
import io
import json
import math
import struct
import uuid
import wave
from datetime import datetime, timedelta, timezone

import streamlit as st


# =====================================
# 기본 설정
# =====================================

st.set_page_config(
    page_title="Sleep Free",
    page_icon="🌙",
    layout="wide",
)

KST = timezone(timedelta(hours=9))


def now():
    return datetime.now(KST)


def stamp():
    return now().isoformat()


def parse_time(value):
    result = datetime.fromisoformat(value)

    if result.tzinfo is None:
        raise ValueError("시간대 정보가 없습니다.")

    return result.astimezone(KST)


def safe(value):
    return html.escape(str(value), quote=True)


COMPANIONS = {
    "잠만보": 143,
    "피카츄": 25,
    "이브이": 133,
    "푸린": 39,
    "뮤": 151,
}


def new_profile():
    return {
        "target": 8.0,
        "companion": "잠만보",
        "active_start": None,
        "records": [],
        "day_checks": [],
    }


defaults = {
    "sf_page": "home",
    "sf_profiles": {"트레이너": new_profile()},
    "sf_user": "트레이너",
    "sf_notice": "",
    "sf_alarm_day": "",
    "sf_alarm_on": False,
    "sf_sound": False,
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# 매일 한국 시간 기준으로 알람 꺼짐
today = now().date().isoformat()

if st.session_state.sf_alarm_day != today:
    st.session_state.sf_alarm_day = today
    st.session_state.sf_alarm_on = False
    st.session_state.sf_sound = False


def profile():
    return st.session_state.sf_profiles[st.session_state.sf_user]


def go(page):
    st.session_state.sf_page = page
    st.session_state.sf_sound = False
    st.rerun()


# =====================================
# 디자인
# =====================================

tracking = (
    st.session_state.sf_page == "sleep"
    and profile()["active_start"] is not None
)

background = "#03060b" if tracking else (
    "linear-gradient(145deg,#07152e,#173d70)"
)

st.markdown(
    """
<style>
.stApp {
    background: BACKGROUND;
    color: #ffffff;
}
header[data-testid="stHeader"] {
    background: transparent;
}
.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}
h1,h2,h3,h4 {
    color: white !important;
}
div.stButton > button,
div.stDownloadButton > button {
    background: #244f7b !important;
    color: white !important;
    border: 1px solid #a7ccec !important;
    border-radius: 15px !important;
    min-height: 52px;
}
div.stButton > button p,
div.stDownloadButton > button p {
    color: white !important;
    font-weight: 750 !important;
}
div.stButton > button:hover {
    background: #356b9e !important;
    border-color: white !important;
}
.hero {
    color: white;
    text-align: center;
    font-size: clamp(34px,6vw,54px);
    font-weight: 850;
    margin: 25px 0 8px;
}
.subtitle {
    text-align: center;
    color: #c3d6ed;
    margin-bottom: 24px;
    line-height: 1.8;
}
.card {
    border: 1px solid #ffffff28;
    background: #ffffff0c;
    border-radius: 22px;
    padding: 22px;
    margin: 14px 0 22px;
    color: white;
}
.clouds {
    text-align: center;
    font-size: 52px;
    letter-spacing: 18px;
    opacity: .55;
    margin: 16px 0;
}
.companion {
    text-align: center;
}
.companion img {
    width: 210px;
    height: 210px;
    object-fit: contain;
    filter: drop-shadow(0 12px 22px #0005);
}
.companion p {
    color: #d7e6f8;
}
.score {
    font-size: 70px;
    font-weight: 900;
    text-align: center;
    color: #bce4ff;
}
.quiet {
    text-align: center;
    padding: 65px 20px;
    color: #e2e8f0;
    line-height: 2;
}
.record-title {
    font-size: 19px;
    font-weight: 800;
    margin-bottom: 10px;
}
</style>
""".replace("BACKGROUND", background),
    unsafe_allow_html=True,
)


def companion(message="오늘도 편안한 밤을 함께해요."):
    name = profile()["companion"]
    number = COMPANIONS[name]

    image = (
        "https://raw.githubusercontent.com/PokeAPI/sprites/"
        "master/sprites/pokemon/other/official-artwork/"
        f"{number}.png"
    )

    st.markdown(
        f"""
        <div class="companion">
            <img src="{image}" alt="{safe(name)}"
                 onerror="this.style.display='none'">
            <p><b>{safe(name)}</b> · {safe(message)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =====================================
# 수면 기록
# =====================================

def start_sleep():
    p = profile()

    if p["active_start"] is None:
        p["active_start"] = stamp()

    go("sleep")


def finish_sleep():
    p = profile()

    if p["active_start"] is None:
        return

    start = parse_time(p["active_start"])
    end = now()

    if end < start:
        st.error("기록 시간이 올바르지 않습니다.")
        return

    p["records"].append({
        "uid": str(uuid.uuid4()),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "target": float(p["target"]),
        "awake_minutes": 0,
        "feeling": "아직 입력하지 않음",
        "memo": "",
    })

    p["active_start"] = None
    go("result")


def sleep_summary(record):
    elapsed = max(
        0.0,
        (
            parse_time(record["end"])
            - parse_time(record["start"])
        ).total_seconds() / 3600,
    )

    estimate = max(
        0.0,
        elapsed - record["awake_minutes"] / 60,
    )

    score = round(
        min(1.0, estimate / record["target"]) * 100
    )

    return elapsed, estimate, score


# =====================================
# 저장·불러오기
# =====================================

def export_game():
    # 알람 활성화 상태는 저장하지 않음
    return json.dumps(
        {
            "version": "sleep-free-1",
            "profiles": st.session_state.sf_profiles,
        },
        ensure_ascii=False,
        indent=2,
    )


def valid_number(value, low, high):
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and low <= value <= high
    )


def import_game(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("파일이 너무 큽니다.")

    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("저장 파일 형식이 올바르지 않습니다.")

    if data.get("version") != "sleep-free-1":
        raise ValueError("Sleep Free 저장 파일이 아닙니다.")

    source = data.get("profiles")

    if not isinstance(source, dict) or not 1 <= len(source) <= 30:
        raise ValueError("사용자 정보가 올바르지 않습니다.")

    rebuilt = {}

    for name, p in source.items():
        if not isinstance(name, str) or not 1 <= len(name) <= 30:
            raise ValueError("사용자 이름 오류")

        if not isinstance(p, dict):
            raise ValueError("프로필 정보 오류")

        if not valid_number(p.get("target"), 1, 14):
            raise ValueError("목표 시간 오류")

        if p.get("companion") not in COMPANIONS:
            raise ValueError("캐릭터 정보 오류")

        active = p.get("active_start")

        if active is not None:
            if not isinstance(active, str):
                raise ValueError("진행 중 기록 오류")
            if parse_time(active) > now():
                raise ValueError("미래의 시작 시각입니다.")

        records = p.get("records", [])
        checks = p.get("day_checks", [])

        if not isinstance(records, list) or len(records) > 5000:
            raise ValueError("수면 기록 개수 오류")

        if not isinstance(checks, list) or len(checks) > 5000:
            raise ValueError("낮 시간 기록 개수 오류")

        cleaned_records = []

        for r in records:
            if not isinstance(r, dict):
                raise ValueError("수면 기록 오류")

            start = parse_time(r["start"])
            end = parse_time(r["end"])

            if end < start or end > now():
                raise ValueError("수면 시각 오류")

            if not valid_number(r.get("target"), 1, 14):
                raise ValueError("기록 목표 시간 오류")

            if not valid_number(r.get("awake_minutes"), 0, 100000):
                raise ValueError("깨어 있던 시간 오류")

            feeling = r.get("feeling", "")
            memo = r.get("memo", "")

            if (
                not isinstance(feeling, str)
                or len(feeling) > 100
                or not isinstance(memo, str)
                or len(memo) > 1000
            ):
                raise ValueError("메모 오류")

            cleaned_records.append({
                "uid": str(uuid.uuid4()),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "target": float(r["target"]),
                "awake_minutes": float(r["awake_minutes"]),
                "feeling": feeling,
                "memo": memo,
            })

        cleaned_checks = []

        for c in checks:
            if not isinstance(c, dict):
                raise ValueError("낮 시간 기록 오류")

            when = parse_time(c["time"])
            sleepy = c["sleepiness"]

            if type(sleepy) is not int or not 1 <= sleepy <= 5:
                raise ValueError("졸림 상태 오류")

            cleaned_checks.append({
                "time": when.isoformat(),
                "sleepiness": sleepy,
            })

        rebuilt[name] = {
            "target": float(p["target"]),
            "companion": p["companion"],
            "active_start": active,
            "records": cleaned_records,
            "day_checks": cleaned_checks,
        }

    # 전체 검증 완료 후 반영
    st.session_state.sf_profiles = rebuilt
    st.session_state.sf_user = next(iter(rebuilt))
    st.session_state.sf_alarm_on = False
    st.session_state.sf_sound = False
    st.session_state.sf_notice = "저장 기록을 불러왔어요."
    go("home")


# =====================================
# 알람 소리: 사용자가 켠 경우에만 재생 시도
# =====================================

def alarm_audio():
    sample_rate = 16000
    buffer = io.BytesIO()

    with wave.open(buffer, "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)

        frames = bytearray()

        for i in range(sample_rate):
            t = i / sample_rate
            pulse = 1 if (t % 0.35) < 0.18 else 0
            fade = min(1, t * 30, (1 - t) * 30)

            value = int(
                7000
                * math.sin(2 * math.pi * 660 * t)
                * pulse
                * fade
            )
            frames.extend(struct.pack("<h", value))

        output.writeframes(frames)

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode("ascii")

    st.markdown(
        f"""
        <audio controls autoplay>
            <source src="data:audio/wav;base64,{encoded}"
                    type="audio/wav">
        </audio>
        """,
        unsafe_allow_html=True,
    )

    st.caption(
        "자동 재생이 차단되면 재생 버튼을 눌러 주세요."
    )


# =====================================
# 오른쪽 메뉴
# =====================================

main, right = st.columns([3, 1], gap="large")

with right:
    st.subheader("🌙 Sleep Free")

    users = list(st.session_state.sf_profiles)
    current_index = users.index(st.session_state.sf_user)

    selected_user = st.selectbox(
        "사용자 프로필",
        users,
        index=current_index,
    )

    if selected_user != st.session_state.sf_user:
        st.session_state.sf_user = selected_user
        st.session_state.sf_alarm_on = False
        go("home")

    st.caption("프로필 선택 기능이며 비밀번호 로그인은 아니에요.")

    with st.expander("＋ 사용자 추가"):
        with st.form("new_user_form"):
            username = st.text_input("이름", max_chars=30)
            add = st.form_submit_button("추가")

        if add:
            username = username.strip()

            if not username:
                st.warning("이름을 입력해 주세요.")
            elif username in st.session_state.sf_profiles:
                st.warning("이미 있는 이름이에요.")
            elif len(st.session_state.sf_profiles) >= 30:
                st.warning("사용자는 최대 30명까지 추가할 수 있어요.")
            else:
                st.session_state.sf_profiles[username] = new_profile()
                st.session_state.sf_user = username
                st.session_state.sf_alarm_on = False
                go("home")

    p = profile()

    st.markdown(
        f"""
        <div class="card">
            <b>{safe(st.session_state.sf_user)}의 수면 기록</b><br><br>
            📚 {len(p["records"])}회 기록<br>
            🎯 목표 {p["target"]:g}시간<br>
            🌙 {"기록 진행 중" if p["active_start"] else "기록 대기 중"}
        </div>
        """,
        unsafe_allow_html=True,
    )

    for label, destination in [
        ("🏠 홈", "home"),
        ("🌙 수면 기록", "sleep"),
        ("☀️ 낮 시간", "day"),
        ("📚 내 수면 보관함", "history"),
        ("⚙️ 설정·기기 연결", "settings"),
    ]:
        if st.button(label, use_container_width=True):
            go(destination)

    st.divider()

    st.download_button(
        "💾 기록 저장",
        data=export_game(),
        file_name="sleep_free_save.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("📂 기록 불러오기"):
        uploaded = st.file_uploader(
            "Sleep Free 저장 파일",
            type=["json"],
        )

        st.caption(
            "불러오면 현재 프로필과 기록을 파일 내용으로 교체해요."
        )

        if st.button("불러오기", use_container_width=True):
            if uploaded is None:
                st.warning("파일을 선택해 주세요.")
            else:
                try:
                    import_game(uploaded.getvalue())
                except (
                    ValueError, KeyError, TypeError,
                    AttributeError, OverflowError,
                ):
                    st.error(
                        "파일 형식을 확인해 주세요. "
                        "현재 기록은 변경하지 않았어요."
                    )

    st.caption(
        "접속이 끊기거나 세션이 초기화되면 기록이 사라질 수 있어요. "
        "장기 보관하려면 저장 파일을 다운로드해 주세요."
    )


# =====================================
# 메인 화면
# =====================================

with main:
    p = profile()
    page = st.session_state.sf_page

    if st.session_state.sf_notice:
        st.success(st.session_state.sf_notice)
        st.session_state.sf_notice = ""

    # 홈
    if page == "home":
        st.markdown(
            '<div class="clouds">☁️ 🌙 ☁️</div>'
            '<div class="hero">Sleep Free</div>'
            '<div class="subtitle">'
            '편안한 밤을 기록하고, 낮의 내 상태를 살펴보세요.'
            '</div>',
            unsafe_allow_html=True,
        )

        companion()

        if p["active_start"]:
            st.info("진행 중인 수면 기록이 있어요.")

            if st.button(
                "🌙 진행 중인 기록으로",
                use_container_width=True,
            ):
                go("sleep")
        else:
            if st.button(
                "🌙 수면 추적 시작",
                use_container_width=True,
            ):
                start_sleep()

        if st.button(
            "☀️ 낮 시간으로 전환",
            use_container_width=True,
        ):
            go("day")

        st.caption(
            "버튼을 누른 시각부터 종료 시각까지 기록해요. "
            "실제로 잠든 시각이나 수면 단계를 자동 측정하지는 않아요."
        )

    # 수면 중
    elif page == "sleep":
        if not p["active_start"]:
            st.markdown(
                '<div class="hero">🌙 편안한 밤을 준비하세요</div>',
                unsafe_allow_html=True,
            )
            companion("잠자리에 들 준비가 되면 시작해 주세요.")

            if st.button(
                "수면 추적 시작",
                use_container_width=True,
            ):
                start_sleep()

        else:
            start = parse_time(p["active_start"])

            st.markdown(
                f"""
                <div class="quiet">
                    <div style="font-size:50px">🌙</div>
                    <h2>수면 기록 중</h2>
                    <p>시작: {start.strftime("%m월 %d일 %H:%M")}</p>
                    <p>편안히 쉬세요.<br>
                    일어난 뒤 아래 버튼을 눌러 주세요.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "수면 끝날 때 버튼 누르기",
                use_container_width=True,
            ):
                finish_sleep()

            st.caption(
                "화면을 계속 켜 둘 필요는 없지만, "
                "접속 세션이 종료되면 진행 기록이 사라질 수 있어요."
            )

    # 수면 결과
    elif page == "result":
        if not p["records"]:
            st.info("아직 종료한 수면 기록이 없어요.")

        else:
            r = p["records"][-1]
            elapsed, estimate, score = sleep_summary(r)

            st.markdown(
                '<div class="hero">☀️ 오늘의 수면 기록</div>',
                unsafe_allow_html=True,
            )

            if score >= 100:
                message = "설정한 목표 시간에 도달했어요."
            elif score >= 80:
                message = "목표 시간에 가까워졌어요."
            else:
                message = "기록된 시간이 목표보다 짧았어요."

            companion(message)

            a, b = st.columns(2)
            a.metric("전체 기록 시간", f"{elapsed:.1f}시간")
            b.metric("추정 수면 시간", f"{estimate:.1f}시간")

            st.markdown(
                f'<div class="score">{score}점</div>'
                '<div class="subtitle">목표 시간 달성도</div>',
                unsafe_allow_html=True,
            )

            st.caption(
                "점수 = 추정 수면 시간 ÷ 당시 목표 시간 × 100, "
                "최대 100점. 수면의 질이나 건강 상태를 뜻하지 않아요."
            )

            with st.form(f"review_{r['uid']}"):
                st.subheader("기록 보완")

                awake = st.number_input(
                    "잠드는 데 걸린 시간과 중간에 깬 시간의 합(분)",
                    min_value=0.0,
                    max_value=max(
                        float(elapsed * 60),
                        float(r["awake_minutes"]),
                    ),
                    value=float(r["awake_minutes"]),
                    step=5.0,
                )

                feelings = [
                    "아직 입력하지 않음",
                    "개운함",
                    "보통",
                    "피곤함",
                    "매우 피곤함",
                ]

                feeling = st.selectbox(
                    "일어난 뒤 느낌",
                    feelings,
                    index=(
                        feelings.index(r["feeling"])
                        if r["feeling"] in feelings else 0
                    ),
                )

                memo = st.text_area(
                    "메모",
                    value=r["memo"],
                    max_chars=1000,
                )

                if st.form_submit_button("결과 반영"):
                    r["awake_minutes"] = float(awake)
                    r["feeling"] = feeling
                    r["memo"] = memo
                    st.rerun()

            st.info(
                "오늘 정확히 몇 시에 졸릴지는 현재 기록만으로 "
                "예측할 수 없어요. 낮 시간 화면에서 "
                "실제 졸림 상태를 점검해 주세요."
            )

            if st.button(
                "☀️ 낮 시간 점검하기",
                use_container_width=True,
            ):
                go("day")

    # 낮 시간
    elif page == "day":
        st.markdown(
            '<div class="hero">☀️ 낮 시간 점검</div>'
            '<div class="subtitle">'
            '지금 느끼는 졸림을 직접 기록해 주세요.'
            '</div>',
            unsafe_allow_html=True,
        )

        companion("지금 몸의 신호를 살펴볼까요?")

        st.toggle(
            "🔔 졸림 알람 켜기",
            key="sf_alarm_on",
        )

        st.caption(
            "매일 한국 시간 0시 이후 앱을 실행하거나 조작하면 "
            "꺼짐으로 초기화돼요. 자동 감시 알람은 아니에요."
        )

        with st.form("day_check_form"):
            sleepy = st.select_slider(
                "현재 상태",
                options=[1, 2, 3, 4, 5],
                value=2,
                format_func=lambda x: {
                    1: "1 · 또렷하고 깨어 있음",
                    2: "2 · 약간 나른함",
                    3: "3 · 졸리지만 깨어 있기 어렵지 않음",
                    4: "4 · 깨어 있으려면 노력이 필요함",
                    5: "5 · 나도 모르게 눈이 감기거나 고개가 떨어짐",
                }[x],
            )

            checked = st.form_submit_button(
                "현재 상태 점검",
                use_container_width=True,
            )

        if checked:
            p["day_checks"].append({
                "time": stamp(),
                "sleepiness": sleepy,
            })

            st.session_state.sf_sound = (
                st.session_state.sf_alarm_on and sleepy >= 4
            )

        if p["day_checks"]:
            latest = p["day_checks"][-1]
            level = latest["sleepiness"]

            st.caption(
                "마지막 점검: "
                + parse_time(latest["time"]).strftime("%m/%d %H:%M")
            )

            if level >= 4:
                st.warning(
                    "입력한 상태는 졸림이 강한 상태예요. "
                    "집중이 필요한 활동을 잠시 멈추고 "
                    "안전한 곳에서 쉬어 주세요."
                )
            elif level == 3:
                st.info(
                    "졸림을 느끼고 있어요. "
                    "상태가 더 심해지는지 살펴보세요."
                )
            else:
                st.success(
                    "현재 입력에서는 강한 졸림을 보고하지 않았어요."
                )

        if st.session_state.sf_sound:
            alarm_audio()
            st.session_state.sf_sound = False

        st.caption(
            "자가 보고 결과이며 수면 발생 확률이나 의학적 진단이 아니에요. "
            "이전 점검 결과는 현재 상태와 다를 수 있어요."
        )

    # 기록 보관함
    elif page == "history":
        st.markdown(
            '<div class="hero">📚 내 수면 보관함</div>',
            unsafe_allow_html=True,
        )

        records = list(reversed(p["records"]))

        if not records:
            st.info("첫 수면 기록을 남겨 보세요.")

        else:
            page_size = 9
            pages = (len(records) + page_size - 1) // page_size

            selected_page = st.selectbox(
                "페이지",
                range(1, pages + 1),
            )

            start_index = (selected_page - 1) * page_size
            visible = records[start_index:start_index + page_size]
            columns = st.columns(3)

            for i, r in enumerate(visible):
                start = parse_time(r["start"])
                end = parse_time(r["end"])
                elapsed, estimate, score = sleep_summary(r)

                with columns[i % 3]:
                    st.markdown(
                        f"""
                        <div class="card">
                            <div class="record-title">
                                🌙 {end.strftime("%Y.%m.%d")}
                            </div>
                            {start.strftime("%m/%d %H:%M")}
                            → {end.strftime("%m/%d %H:%M")}<br><br>
                            기록 {elapsed:.1f}시간<br>
                            추정 수면 {estimate:.1f}시간<br>
                            목표 달성도 {score}점<br>
                            기상 후 느낌: {safe(r["feeling"])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                    if r["memo"]:
                        st.caption(r["memo"])

    # 설정
    elif page == "settings":
        st.markdown(
            '<div class="hero">⚙️ 설정</div>',
            unsafe_allow_html=True,
        )

        with st.form("settings_form"):
            target = st.number_input(
                "내 목표 수면 시간",
                min_value=1.0,
                max_value=14.0,
                value=float(p["target"]),
                step=0.5,
            )

            names = list(COMPANIONS)

            selected_companion = st.selectbox(
                "함께할 포켓몬",
                names,
                index=names.index(p["companion"]),
            )

            if st.form_submit_button("설정 저장"):
                p["target"] = float(target)
                p["companion"] = selected_companion
                st.session_state.sf_notice = "설정을 저장했어요."
                st.rerun()

        st.caption(
            "목표 시간은 개인 설정값이에요. "
            "과거 기록의 점수는 당시 목표 시간을 기준으로 유지돼요."
        )

        st.divider()
        st.subheader("⌚ 웨어러블 연결")

        st.info(
            "현재 버전: 연결되지 않음\n\n"
            "실시간 센서 데이터는 수신하지 않아요. "
            "기기 모델과 데이터 제공 방식에 맞춘 연동이 필요해요."
        )

        st.write(
            "지원하지 않는 기기를 연결했다고 표시하거나 "
            "심박수·수면 단계를 임의로 생성하지 않아요."
        )


with st.expander("📖 Sleep Free 안내"):
    st.write(
        "Sleep Free는 수면 시각 기록과 자가 점검을 돕는 앱입니다. "
        "실제 수면 단계, 수면의 질, 잠들 시각을 자동 측정하지 않습니다. "
        "알람은 사용자가 켠 뒤 낮 시간 점검을 제출한 경우에만 작동하며, "
        "브라우저 자동 재생 정책에 따라 소리가 제한될 수 있습니다. "
        "현재 버전은 Streamlit 서버와 인터넷 연결이 필요합니다. "
        "포켓몬 이미지는 외부 서버에서 표시합니다. "
        "프로필은 같은 접속 세션 안에서 기록을 구분하는 기능이며 "
        "개인 계정 인증 기능은 아닙니다."
    )
