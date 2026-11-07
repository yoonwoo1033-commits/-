
import json
import random
import uuid
from datetime import datetime, timedelta, timezone

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Sleep Free", page_icon="🌙", layout="wide")
KST = timezone(timedelta(hours=9))

POKEMON = [
    (1, "이상해씨"), (4, "파이리"), (7, "꼬부기"),
    (25, "피카츄"), (35, "삐삐"), (37, "식스테일"),
    (39, "푸린"), (52, "나옹"), (54, "고라파덕"),
    (58, "가디"), (63, "캐이시"), (92, "고오스"),
    (133, "이브이"), (143, "잠만보"), (147, "미뇽"),
    (151, "뮤"), (152, "치코리타"), (155, "브케인"),
    (158, "리아코"), (175, "토게피"), (179, "메리프"),
    (183, "마릴"), (194, "우파"), (216, "깜지곰"),
    (252, "나무지기"), (255, "아차모"), (258, "물짱이"),
    (280, "랄토스"), (371, "아공이"), (387, "모부기"),
    (390, "불꽃숭이"), (393, "팽도리"), (403, "꼬링크"),
    (443, "딥상어동"), (447, "리오르"),
    (495, "주리비얀"), (498, "뚜꾸리"), (501, "수댕이"),
    (650, "도치마론"), (653, "푸호꼬"), (656, "개구마르"),
    (722, "나몰빼미"), (725, "냐오불"), (728, "누리공"),
    (810, "흥나숭"), (813, "염버니"), (816, "울머기"),
    (906, "나오하"), (909, "뜨아거"), (912, "꾸왁스")
]

NAMES = dict(POKEMON)

FIELDS = {
    "quality": "수면 점수 (0~100)",
    "asleep": "실제 수면 시간 (분)",
    "latency": "잠드는 데 걸린 시간 (분)",
    "snoring": "코골이 시간 (분)",
    "awake": "중간에 깨어 있던 시간 (분)",
    "deep": "깊은 수면 (분)",
    "rem": "REM 수면 (분)",
    "light": "얕은 수면 (분)"
}


def now():
    return datetime.now(KST)


def dt(value):
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def new_mon(number=143):
    return {
        "uid": str(uuid.uuid4()),
        "number": number,
        "level": random.randint(1, 10),
        "shiny": random.random() < 0.05
    }


def new_profile():
    mon = new_mon()
    return {
        "collection": [mon],
        "partner_uid": mon["uid"],
        "goal_hours": 8.0,
        "sleep_start": None,
        "records": [],
        "cycles": [],
        "naps": [],
        "day_checks": []
    }


def migrate(p):
    if not isinstance(p, dict):
        return new_profile()

    p.setdefault("goal_hours", 8.0)
    p.setdefault("sleep_start", None)

    for key in ("records", "cycles", "naps", "day_checks"):
        if not isinstance(p.get(key), list):
            p[key] = []

        for item in p[key]:
            if isinstance(item, dict):
                item.setdefault("uid", str(uuid.uuid4()))

    if not isinstance(p.get("collection"), list) or not p["collection"]:
        p["collection"] = [new_mon()]

    for mon in p["collection"]:
        mon.setdefault("uid", str(uuid.uuid4()))
        mon.setdefault("level", 5)
        mon.setdefault("shiny", False)

    ids = {m["uid"] for m in p["collection"]}

    if p.get("partner_uid") not in ids:
        p["partner_uid"] = p["collection"][0]["uid"]

    return p


if "profiles" not in st.session_state:
    st.session_state.profiles = {"트레이너": new_profile()}

if "user" not in st.session_state:
    st.session_state.user = "트레이너"

if "page" not in st.session_state:
    st.session_state.page = "🏠 홈"

for username in list(st.session_state.profiles):
    st.session_state.profiles[username] = migrate(
        st.session_state.profiles[username]
    )

if st.session_state.user not in st.session_state.profiles:
    st.session_state.user = next(iter(st.session_state.profiles))


def profile():
    return st.session_state.profiles[st.session_state.user]


def partner():
    p = profile()
    return next(
        (
            m for m in p["collection"]
            if m["uid"] == p["partner_uid"]
        ),
        p["collection"][0]
    )


def mon_image(mon, width=180):
    number = mon["number"]
    kind = "shiny" if mon.get("shiny") else ""

    if kind:
        url = (
            "https://raw.githubusercontent.com/"
            "PokeAPI/sprites/master/sprites/pokemon/"
            f"shiny/{number}.png"
        )
    else:
        url = (
            "https://raw.githubusercontent.com/"
            "PokeAPI/sprites/master/sprites/pokemon/"
            f"{number}.png"
        )

    st.image(url, width=width)


def combine(d, t):
    return datetime.combine(d, t, tzinfo=KST)


def interval_form(start, end):
    a, b = st.columns(2)

    with a:
        sd = st.date_input("시작 날짜", value=start.date())
        stime = st.time_input(
            "시작 시각",
            value=start.time().replace(tzinfo=None)
        )

    with b:
        ed = st.date_input("종료 날짜", value=end.date())
        etime = st.time_input(
            "종료 시각",
            value=end.time().replace(tzinfo=None)
        )

    return combine(sd, stime), combine(ed, etime)


def choose(records, key):
    choices = ["새 기록"] + [
        r["uid"] for r in records
        if isinstance(r, dict) and "uid" in r
    ]

    labels = {
        r["uid"]: r.get(
            "end", r.get("time", "기록")
        )[:16].replace("T", " ")
        for r in records
        if isinstance(r, dict) and "uid" in r
    }

    choice = st.selectbox(
        "기록 선택",
        choices,
        format_func=lambda x: labels.get(x, x),
        key=key
    )

    return next(
        (r for r in records if r.get("uid") == choice),
        None
    )


def save(records, old, value):
    value["uid"] = (
        old["uid"] if old else str(uuid.uuid4())
    )

    if old:
        records[records.index(old)] = value
    else:
        records.append(value)

    st.success("저장했어요!")


def delete(records, old, key):
    if old and st.checkbox(
        "이 기록 삭제 확인",
        key="confirm_" + key
    ):
        if st.button(
            "기록 삭제",
            key="delete_" + key
        ):
            records.remove(old)
            st.rerun()


# =====================================
# 화면 디자인 및 글자 색상
# =====================================

st.markdown("""
<style>
.stApp {
    background: linear-gradient(140deg, #07152b, #17365c);
    color: #f8fafc;
}

h1, h2, h3 {
    color: #ffffff !important;
}

[data-testid="stWidgetLabel"] p,
[data-testid="stCaptionContainer"] p {
    color: #f4f7ff !important;
}

/* 오류 및 안내 상자: 밝은 배경 + 검은 글씨 */
[data-testid="stAlert"] {
    background: #f0f7ff !important;
    border: 1px solid #b4d5ef !important;
}

[data-testid="stAlert"] *,
[data-testid="stAlert"] p,
[data-testid="stAlert"] span {
    color: #102238 !important;
    -webkit-text-fill-color: #102238 !important;
}

/* 입력창 */
[data-baseweb="input"],
[data-baseweb="input"] input,
[data-baseweb="textarea"],
[data-baseweb="textarea"] textarea {
    background: #ffffff !important;
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

/* 선택창 */
[data-baseweb="select"] > div {
    background: #ffffff !important;
    color: #111827 !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] input {
    color: #111827 !important;
    -webkit-text-fill-color: #111827 !important;
}

/* 드롭다운 */
[data-baseweb="popover"],
[role="listbox"] {
    background: #ffffff !important;
    color: #111827 !important;
}

[role="option"],
[role="option"] * {
    color: #111827 !important;
}

/* 버튼 */
div.stButton > button,
div.stDownloadButton > button,
div.stFormSubmitButton > button {
    background: #9bdcff !important;
    color: #0b223d !important;
    border-radius: 12px;
    border: 0;
    min-height: 44px;
}

div.stButton > button *,
div.stDownloadButton > button *,
div.stFormSubmitButton > button * {
    color: #0b223d !important;
}

[data-testid="stMetricValue"],
[data-testid="stMetricLabel"] * {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)


# =====================================
# 메뉴
# =====================================

PAGES = [
    "🏠 홈",
    "🎲 포켓몬 뽑기",
    "📦 보관함",
    "🌙 수면 추적",
    "📝 Sleep Cycle 입력",
    "☀️ 졸림 기록",
    "💤 낮잠 기록",
    "📊 데이터 분석",
    "📚 기록 보기",
    "⚙️ 설정·백업"
]

with st.sidebar:
    st.title("🌙 Sleep Free")

    users = list(st.session_state.profiles)

    selected = st.selectbox(
        "사용자",
        users,
        index=users.index(st.session_state.user)
    )

    if selected != st.session_state.user:
        st.session_state.user = selected
        st.rerun()

    with st.expander("사용자 추가"):
        name = st.text_input("새 이름")

        if st.button("추가"):
            name = name.strip()

            if not name or name in st.session_state.profiles:
                st.error("사용할 수 없는 이름이에요.")
            else:
                st.session_state.profiles[name] = new_profile()
                st.session_state.user = name
                st.rerun()

    st.caption(
        "프로필은 로그인 계정이 아니며 "
        "다른 기기와 동기화되지 않아요."
    )

    page = st.radio(
        "메뉴",
        PAGES,
        index=(
            PAGES.index(st.session_state.page)
            if st.session_state.page in PAGES
            else 0
        )
    )

    st.session_state.page = page

    st.caption(
        f"포켓몬 {len(profile()['collection'])}마리 · "
        f"수면 기록 {len(profile()['cycles'])}회"
    )


p = profile()

st.title("🌙 Sleep Free")
st.caption("포켓몬과 함께하는 수면 기록 연구실")


# =====================================
# 홈
# =====================================

if page == "🏠 홈":
    st.subheader("오늘의 수면 파트너")

    mon_image(partner(), 220)

    st.write(
        f"**{NAMES.get(partner()['number'], '포켓몬')}** "
        f"· Lv.{partner()['level']}"
    )

    st.info(
        "밤에는 수면을 기록하고, 아침에는 Sleep Cycle "
        "수치를 입력하세요. 낮에는 졸림과 낮잠을 "
        "기록할 수 있어요."
    )

    a, b = st.columns(2)

    with a:
        if st.button(
            "🎲 포켓몬 만나기",
            use_container_width=True
        ):
            st.session_state.page = "🎲 포켓몬 뽑기"
            st.rerun()

    with b:
        if st.button(
            "📝 수면 지표 입력",
            use_container_width=True
        ):
            st.session_state.page = "📝 Sleep Cycle 입력"
            st.rerun()


# =====================================
# 포켓몬 뽑기
# =====================================

elif page == "🎲 포켓몬 뽑기":
    st.subheader("몬스터볼을 던져 보세요!")

    if st.button("🎲 뽑기", use_container_width=True):
        number = random.choice(POKEMON)[0]
        mon = new_mon(number)

        p["collection"].append(mon)
        st.session_state.last_mon = mon

    mon = st.session_state.get("last_mon")

    if mon:
        mon_image(mon, 220)

        st.success(
            f"{NAMES.get(mon['number'], '포켓몬')} 등장!"
            + (" ✨ 이로치!" if mon["shiny"] else "")
        )


# =====================================
# 포켓몬 보관함
# =====================================

elif page == "📦 보관함":
    st.subheader("내 포켓몬")

    mons = list(reversed(p["collection"]))

    for start in range(0, len(mons), 3):
        cols = st.columns(3)

        for col, mon in zip(
            cols, mons[start:start + 3]
        ):
            with col:
                with st.container(border=True):
                    mon_image(mon, 120)

                    st.write(
                        f"**{NAMES.get(mon['number'], '포켓몬')}** "
                        f"Lv.{mon['level']}"
                    )

                    if mon["uid"] == p["partner_uid"]:
                        st.caption("🌙 현재 파트너")

                    elif st.button(
                        "파트너 선택",
                        key="mon_" + mon["uid"]
                    ):
                        p["partner_uid"] = mon["uid"]
                        st.rerun()


# =====================================
# 수면 추적
# =====================================

elif page == "🌙 수면 추적":
    st.subheader("수면 시간 기록")

    mon_image(partner(), 180)

    if not p["sleep_start"]:
        if st.button("🌙 지금 수면 시작"):
            p["sleep_start"] = now().isoformat()
            st.rerun()

    else:
        start = dt(p["sleep_start"])

        st.info(
            f"수면 시작: {start:%Y-%m-%d %H:%M}"
        )

        if st.button("☀️ 수면 종료"):
            end = now()

            if end > start:
                p["records"].append({
                    "uid": str(uuid.uuid4()),
                    "start": start.isoformat(),
                    "end": end.isoformat(),
                    "goal": p["goal_hours"],
                    "awake_minutes": 0,
                    "feeling": "미입력",
                    "memo": ""
                })

                p["sleep_start"] = None
                st.success("수면 시간을 기록했어요.")
                st.rerun()

    st.caption(
        "시작·종료 시각 기록 기능이며 "
        "실제 수면 단계를 자동 측정하지 않아요."
    )


# =====================================
# Sleep Cycle 수면 지표 입력
# =====================================

elif page == "📝 Sleep Cycle 입력":
    st.subheader("Sleep Cycle 지표 입력")

    st.info(
        "수면 앱에 표시된 값만 입력하세요. "
        "없는 항목은 '입력 안 함'을 유지하면 됩니다. "
        "수면 시간은 분 단위예요. "
        "예: 6시간 30분 → 390분."
    )

    records = p["cycles"]
    old = choose(records, "cycle_choose")

    end = (
        dt(old["end"])
        if old
        else now().replace(second=0, microsecond=0)
    )

    start = (
        dt(old["start"])
        if old
        else end - timedelta(hours=7)
    )

    with st.form(
        "cycle_form_" + (old["uid"] if old else "new")
    ):
        a, b = interval_form(start, end)

        st.markdown("#### 수면 지표")

        values = {}
        cols = st.columns(2)

        for i, (key, label) in enumerate(FIELDS.items()):
            with cols[i % 2]:
                previous = old.get(key) if old else None

                enabled = st.checkbox(
                    f"{label} 입력",
                    value=previous is not None,
                    key="use_" + key
                )

                if enabled:
                    values[key] = st.number_input(
                        label,
                        min_value=0.0,
                        max_value=(
                            100.0
                            if key == "quality"
                            else 4320.0
                        ),
                        value=float(previous or 0),
                        step=1.0,
                        key="value_" + key
                    )
                else:
                    values[key] = None

        memo = st.text_area(
            "메모",
            value=old.get("memo", "") if old else ""
        )

        submitted = st.form_submit_button(
            "💾 수면 지표 저장",
            use_container_width=True
        )

    if submitted:
        minutes = (b - a).total_seconds() / 60
        errors = []

        if minutes <= 0:
            errors.append(
                "종료 시각이 시작 시각보다 늦어야 해요. "
                "날짜도 확인하세요."
            )

        if minutes > 4320:
            errors.append(
                "기록 시간은 최대 72시간까지 허용해요."
            )

        if b > now():
            errors.append(
                "종료 시각이 현재보다 미래예요."
            )

        for key, label in FIELDS.items():
            if (
                key != "quality"
                and values[key] is not None
                and values[key] > minutes
            ):
                errors.append(
                    f"'{label}' 값이 전체 기록 시간"
                    f"({minutes:.0f}분)보다 커요."
                )

        if not any(
            values[k] is not None for k in FIELDS
        ):
            errors.append(
                "수면 지표를 최소 한 개 선택해 "
                "입력해 주세요."
            )

        if errors:
            for error in errors:
                st.error(error)

        else:
            record = {
                "start": a.isoformat(),
                "end": b.isoformat(),
                "memo": memo,
                **values
            }

            save(records, old, record)

    delete(records, old, "cycle")

    st.caption(
        "수면 단계 및 점수는 Sleep Cycle의 추정값이며 "
        "의료적 진단 자료가 아니에요."
    )


# =====================================
# 낮 시간 졸림 기록
# =====================================

elif page == "☀️ 졸림 기록":
    st.subheader("시간대별 졸림")

    st.info(
        "하루 여러 번 입력할 수 있어요. "
        "1은 또렷함, 5는 매우 졸림을 의미해요."
    )

    records = p["day_checks"]
    old = choose(records, "day_choose")

    when = dt(old["time"]) if old else now()

    with st.form(
        "day_form_" + (old["uid"] if old else "new")
    ):
        date = st.date_input(
            "날짜",
            value=when.date()
        )

        time = st.time_input(
            "시각",
            value=when.time().replace(tzinfo=None)
        )

        level = st.slider(
            "졸림 정도",
            1, 5,
            int(old["sleepiness"]) if old else 2
        )

        submitted = st.form_submit_button(
            "💾 졸림 저장"
        )

    if submitted:
        moment = combine(date, time)

        if moment > now():
            st.error(
                "미래 시각은 입력할 수 없어요."
            )
        else:
            save(
                records,
                old,
                {
                    "time": moment.isoformat(),
                    "sleepiness": level
                }
            )

    delete(records, old, "day")

    for r in sorted(
        records,
        key=lambda r: r["time"],
        reverse=True
    )[:15]:
        st.write(
            f"{dt(r['time']):%m/%d %H:%M} "
            f"· 졸림 {r['sleepiness']}/5"
        )


# =====================================
# 낮잠 기록
# =====================================

elif page == "💤 낮잠 기록":
    st.subheader("낮잠 시작·종료")

    records = p["naps"]
    old = choose(records, "nap_choose")

    end = (
        dt(old["end"])
        if old
        else now().replace(second=0, microsecond=0)
    )

    start = (
        dt(old["start"])
        if old
        else end - timedelta(minutes=30)
    )

    with st.form(
        "nap_form_" + (old["uid"] if old else "new")
    ):
        a, b = interval_form(start, end)

        memo = st.text_area(
            "메모",
            value=old.get("memo", "") if old else ""
        )

        submitted = st.form_submit_button(
            "💾 낮잠 저장"
        )

    if submitted:
        minutes = (b - a).total_seconds() / 60

        if not 0 < minutes <= 1440:
            st.error(
                "시작·종료 날짜와 시각을 확인하세요. "
                "낮잠은 최대 24시간까지 입력할 수 있어요."
            )

        elif b > now():
            st.error(
                "종료 시각이 미래예요."
            )

        else:
            save(
                records,
                old,
                {
                    "start": a.isoformat(),
                    "end": b.isoformat(),
                    "memo": memo
                }
            )

    delete(records, old, "nap")

    for r in sorted(
        records,
        key=lambda r: r["start"],
        reverse=True
    )[:15]:
        a, b = dt(r["start"]), dt(r["end"])

        st.write(
            f"{a:%m/%d %H:%M} ~ "
            f"{b:%m/%d %H:%M} "
            f"· {(b-a).total_seconds()/60:.0f}분"
        )


# =====================================
# 데이터 분석
# =====================================

elif page == "📊 데이터 분석":
    st.subheader("수면 변화 분석")

    if p["cycles"]:
        rows = []

        for r in p["cycles"]:
            rows.append({
                "날짜": dt(r["end"]).date().isoformat(),
                "수면 점수": r.get("quality"),
                "수면 시간(분)": r.get("asleep")
            })

        df = pd.DataFrame(rows).sort_values("날짜")

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        daily = df.groupby("날짜")[
            ["수면 점수", "수면 시간(분)"]
        ].mean()

        st.line_chart(daily)

    else:
        st.info(
            "Sleep Cycle 기록을 입력하면 "
            "그래프가 나타나요."
        )

    if p["day_checks"]:
        df = pd.DataFrame([
            {
                "시각": dt(r["time"]),
                "졸림": r["sleepiness"]
            }
            for r in p["day_checks"]
        ]).sort_values("시각")

        st.subheader("졸림 변화")
        st.line_chart(df.set_index("시각"))

    if p["naps"]:
        df = pd.DataFrame([
            {
                "날짜": dt(r["start"]).date().isoformat(),
                "낮잠(분)": (
                    dt(r["end"]) - dt(r["start"])
                ).total_seconds() / 60
            }
            for r in p["naps"]
        ])

        st.subheader("낮잠 시간")

        st.bar_chart(
            df.groupby("날짜")["낮잠(분)"].sum()
        )

    st.caption(
        "수면 앱의 추정치와 주관적 졸림 기록을 "
        "시각화한 것으로 인과관계나 진단을 "
        "의미하지 않아요."
    )

    for key in ("cycles", "naps", "day_checks"):
        if p[key]:
            st.download_button(
                f"{key} CSV 저장",
                pd.DataFrame(p[key]).to_csv(
                    index=False
                ).encode("utf-8-sig"),
                file_name=f"{key}.csv",
                mime="text/csv",
                key="csv_" + key
            )


# =====================================
# 전체 기록 보기
# =====================================

elif page == "📚 기록 보기":
    st.subheader("전체 기록")

    for title, key in [
        ("수면 시작·종료", "records"),
        ("Sleep Cycle", "cycles"),
        ("낮잠", "naps"),
        ("졸림", "day_checks")
    ]:
        with st.expander(
            f"{title} ({len(p[key])}개)"
        ):
            if p[key]:
                st.dataframe(
                    pd.DataFrame(p[key]),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.write("아직 기록이 없어요.")


# =====================================
# 설정 및 데이터 백업
# =====================================

elif page == "⚙️ 설정·백업":
    st.subheader("설정")

    p["goal_hours"] = st.number_input(
        "목표 수면 시간",
        min_value=1.0,
        max_value=14.0,
        value=float(p["goal_hours"]),
        step=0.5
    )

    st.subheader("데이터 백업")

    backup = json.dumps(
        {
            "version": "sleep-free-pokemon-2",
            "profiles": st.session_state.profiles
        },
        ensure_ascii=False,
        indent=2
    )

    st.download_button(
        "💾 JSON 백업 다운로드",
        backup,
        file_name="sleep_free_save.json",
        mime="application/json"
    )

    uploaded = st.file_uploader(
        "JSON 백업 복원",
        type=["json"]
    )

    if st.button("백업 복원"):
        if uploaded is None:
            st.error(
                "JSON 파일을 선택해 주세요."
            )
        else:
            try:
                raw = uploaded.getvalue()

                if len(raw) > 5_000_000:
                    raise ValueError(
                        "파일이 너무 커요."
                    )

                data = json.loads(raw)
                restored = data.get("profiles")

                if (
                    not isinstance(restored, dict)
                    or not restored
                    or len(restored) > 20
                ):
                    raise ValueError(
                        "백업 파일의 프로필 형식이 잘못됐어요."
                    )

                clean = {}

                for name, record in restored.items():
                    if (
                        not isinstance(name, str)
                        or not isinstance(record, dict)
                    ):
                        raise ValueError(
                            "프로필 정보가 잘못됐어요."
                        )

                    clean[name] = migrate(record)

                st.session_state.profiles = clean
                st.session_state.user = next(iter(clean))

                st.success("복원했어요.")
                st.rerun()

            except (
                ValueError,
                TypeError,
                KeyError
            ) as error:
                st.error(
                    f"복원 실패: {error}"
                )

    st.warning(
        "현재 버전은 Streamlit 세션에 저장하므로 "
        "브라우저 세션이 끝나거나 서버가 재시작되면 "
        "데이터가 사라질 수 있어요. "
        "중요한 기록은 매번 JSON으로 백업해 주세요. "
        "사용자 프로필은 보안 로그인 기능이 아닙니다."
    )
