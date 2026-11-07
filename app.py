
import streamlit as st
import pandas as pd
import requests
import random
import json
import uuid
import html
import math
import io
import csv

from datetime import datetime, timedelta, timezone

# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="Sleep Free",
    page_icon="🌙",
    layout="wide",
    initial_sidebar_state="expanded"
)

KST = timezone(timedelta(hours=9))

SPRITES = (
    "https://raw.githubusercontent.com/"
    "PokeAPI/sprites/master/sprites/pokemon"
)

POKEMON = [
    ("이상해씨", 1, "풀 / 독", "일반"),
    ("파이리", 4, "불꽃", "일반"),
    ("꼬부기", 7, "물", "일반"),
    ("캐터피", 10, "벌레", "일반"),
    ("구구", 16, "노말 / 비행", "일반"),
    ("피카츄", 25, "전기", "희귀"),
    ("삐삐", 35, "페어리", "희귀"),
    ("식스테일", 37, "불꽃", "희귀"),
    ("푸린", 39, "노말 / 페어리", "희귀"),
    ("나옹", 52, "노말", "일반"),
    ("고라파덕", 54, "물", "일반"),
    ("가디", 58, "불꽃", "희귀"),
    ("발챙이", 60, "물", "일반"),
    ("캐이시", 63, "에스퍼", "희귀"),
    ("고오스", 92, "고스트 / 독", "희귀"),
    ("잉어킹", 129, "물", "일반"),
    ("이브이", 133, "노말", "희귀"),
    ("잠만보", 143, "노말", "초희귀"),
    ("미뇽", 147, "드래곤", "초희귀"),
    ("뮤", 151, "에스퍼", "환상"),
    ("치코리타", 152, "풀", "희귀"),
    ("브케인", 155, "불꽃", "희귀"),
    ("리아코", 158, "물", "희귀"),
    ("토게피", 175, "페어리", "희귀"),
    ("메리프", 179, "전기", "일반"),
    ("마릴", 183, "물 / 페어리", "일반"),
    ("우파", 194, "물 / 땅", "일반"),
    ("깜지곰", 216, "노말", "일반"),
    ("나무지기", 252, "풀", "희귀"),
    ("아차모", 255, "불꽃", "희귀"),
    ("물짱이", 258, "물", "희귀"),
    ("랄토스", 280, "에스퍼 / 페어리", "희귀"),
    ("아공이", 371, "드래곤", "초희귀"),
    ("모부기", 387, "풀", "희귀"),
    ("불꽃숭이", 390, "불꽃", "희귀"),
    ("팽도리", 393, "물", "희귀"),
    ("꼬링크", 403, "전기", "일반"),
    ("딥상어동", 443, "드래곤 / 땅", "초희귀"),
    ("리오르", 447, "격투", "희귀"),
    ("주리비얀", 495, "풀", "희귀"),
    ("뚜꾸리", 498, "불꽃", "희귀"),
    ("수댕이", 501, "물", "희귀"),
    ("도치마론", 650, "풀", "희귀"),
    ("푸호꼬", 653, "불꽃", "희귀"),
    ("개구마르", 656, "물", "희귀"),
    ("나몰빼미", 722, "풀 / 비행", "희귀"),
    ("냐오불", 725, "불꽃", "희귀"),
    ("누리공", 728, "물", "희귀"),
    ("흥나숭", 810, "풀", "희귀"),
    ("염버니", 813, "불꽃", "희귀"),
    ("울머기", 816, "물", "희귀"),
    ("나오하", 906, "풀", "희귀"),
    ("뜨아거", 909, "불꽃", "희귀"),
    ("꾸왁스", 912, "물", "희귀")
]

DEX = {p[1]: p for p in POKEMON}

RARITY_WEIGHTS = {
    "일반": 12,
    "희귀": 5,
    "초희귀": 1,
    "환상": 0.15
}

CYCLE_FIELDS = {
    "quality": ("수면의 질 / 점수 (0~100)", 100),
    "asleep": ("실제 수면 시간 (분)", 1440),
    "latency": ("잠들기까지 걸린 시간 (분)", 1440),
    "snoring": ("코골이 시간 (분)", 1440),
    "awake": ("깨어 있던 시간 (분)", 1440),
    "light": ("얕은 수면 (분)", 1440),
    "deep": ("깊은 수면 (분)", 1440),
    "rem": ("REM 수면 (분)", 1440)
}


# ==========================================
# 2. 공통 함수
# ==========================================

def now():
    return datetime.now(KST)


def esc(value):
    return html.escape(str(value), quote=True)


def uid():
    return str(uuid.uuid4())


def parse_dt(value):
    dt = datetime.fromisoformat(value)

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=KST)

    return dt.astimezone(KST)


def combine_dt(date_value, time_value):
    return datetime.combine(
        date_value,
        time_value,
        tzinfo=KST
    )


def valid_number(value, low, high):
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and low <= value <= high
    )


def optional_number(value, maximum):
    if value is None or str(value).strip() == "":
        return None

    number = float(value)

    if not math.isfinite(number):
        raise ValueError("올바른 숫자를 입력해 주세요.")

    if not 0 <= number <= maximum:
        raise ValueError(
            f"0~{maximum} 범위로 입력해 주세요."
        )

    return number


def duration_minutes(start, end):
    return (
        end - start
    ).total_seconds() / 60


# ==========================================
# 3. 포켓몬 데이터
# ==========================================

def make_pokemon(
    number,
    level=None,
    shiny=None,
    pokemon_uid=None
):
    name, number, types, rarity = DEX[number]

    return {
        "uid": pokemon_uid or uid(),
        "number": number,
        "name": name,
        "types": types,
        "rarity": rarity,
        "level": level if level is not None
        else random.randint(1, 10),
        "shiny": shiny if shiny is not None
        else random.random() < 0.05,
        "ball": random.choices(
            [
                "몬스터볼",
                "슈퍼볼",
                "하이퍼볼",
                "프레미어볼",
                "마스터볼"
            ],
            weights=[50, 25, 15, 8, 2],
            k=1
        )[0]
    }


def new_profile():
    starter = make_pokemon(
        143,
        level=5,
        shiny=False
    )

    return {
        "goal_hours": 8.0,
        "collection": [starter],
        "partner_uid": starter["uid"],
        "sleep_start": None,
        "records": [],
        "cycles": [],
        "day_checks": [],
        "naps": []
    }


def migrate_profile(source):
    """
    이전 버전 데이터에 항목이 빠져 있어도
    앱이 실행되도록 기본값을 보완합니다.
    """

    if not isinstance(source, dict):
        return new_profile()

    p = dict(source)

    goal = p.get(
        "goal_hours",
        p.get("target", 8.0)
    )

    if not valid_number(goal, 1, 14):
        goal = 8.0

    p["goal_hours"] = float(goal)

    collection = p.get("collection", [])

    if not isinstance(collection, list):
        collection = []

    cleaned = []
    seen = set()

    for item in collection:
        if not isinstance(item, dict):
            continue

        number = item.get("number")

        if type(number) is not int:
            continue

        if number not in DEX:
            continue

        level = item.get("level", 5)

        if (
            type(level) is not int
            or not 1 <= level <= 100
        ):
            level = 5

        shiny = item.get("shiny", False)

        if type(shiny) is not bool:
            shiny = False

        pokemon_uid = item.get("uid")

        if (
            not isinstance(pokemon_uid, str)
            or not pokemon_uid
            or pokemon_uid in seen
        ):
            pokemon_uid = uid()

        seen.add(pokemon_uid)

        pokemon = make_pokemon(
            number,
            level=level,
            shiny=shiny,
            pokemon_uid=pokemon_uid
        )

        if item.get("ball") in [
            "몬스터볼",
            "슈퍼볼",
            "하이퍼볼",
            "프레미어볼",
            "마스터볼"
        ]:
            pokemon["ball"] = item["ball"]

        cleaned.append(pokemon)

    if not cleaned:
        cleaned = [
            make_pokemon(
                143,
                level=5,
                shiny=False
            )
        ]

    p["collection"] = cleaned

    valid_uids = {
        item["uid"]
        for item in cleaned
    }

    if p.get("partner_uid") not in valid_uids:
        p["partner_uid"] = cleaned[0]["uid"]

    if "sleep_start" not in p:
        p["sleep_start"] = p.get(
            "active_start"
        )

    if p["sleep_start"]:
        try:
            start = parse_dt(p["sleep_start"])

            if start > now():
                p["sleep_start"] = None

        except (ValueError, TypeError):
            p["sleep_start"] = None

    for key in [
        "records",
        "cycles",
        "day_checks",
        "naps"
    ]:
        if not isinstance(p.get(key), list):
            p[key] = []

    cleaned_records = []

    for record in p["records"]:
        if not isinstance(record, dict):
            continue

        try:
            start = parse_dt(record["start"])
            end = parse_dt(record["end"])

            if end < start:
                continue

            awake = record.get(
                "awake_minutes",
                0
            )

            maximum = duration_minutes(
                start,
                end
            )

            if not valid_number(
                awake,
                0,
                maximum
            ):
                awake = 0

            target = record.get(
                "goal",
                record.get(
                    "target",
                    p["goal_hours"]
                )
            )

            if not valid_number(target, 1, 14):
                target = p["goal_hours"]

            cleaned_records.append({
                "uid": str(record.get("uid") or uid()),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "goal": float(target),
                "awake_minutes": float(awake),
                "feeling": str(
                    record.get("feeling", "미입력")
                )[:50],
                "memo": str(
                    record.get("memo", "")
                )[:500]
            })

        except (
            KeyError,
            ValueError,
            TypeError
        ):
            continue

    p["records"] = cleaned_records

    for key in ["cycles", "naps", "day_checks"]:
        valid = []

        for record in p[key]:
            if not isinstance(record, dict):
                continue

            try:
                item = dict(record)

                if key == "day_checks":
                    item["time"] = parse_dt(
                        item["time"]
                    ).isoformat()

                    level = item["sleepiness"]

                    if (
                        type(level) is not int
                        or not 1 <= level <= 5
                    ):
                        continue

                else:
                    start = parse_dt(item["start"])
                    end = parse_dt(item["end"])

                    if end <= start:
                        continue

                    item["start"] = start.isoformat()
                    item["end"] = end.isoformat()

                    if key == "cycles":
                        for field in CYCLE_FIELDS:
                            item.setdefault(field, None)

                item["uid"] = str(
                    item.get("uid") or uid()
                )

                valid.append(item)

            except (
                KeyError,
                ValueError,
                TypeError
            ):
                continue

        p[key] = valid

    return p


# ==========================================
# 4. 세션 초기화
# ==========================================

if "sf_profiles" not in st.session_state:
    st.session_state.sf_profiles = {
        "트레이너": new_profile()
    }

if (
    not isinstance(
        st.session_state.sf_profiles,
        dict
    )
    or not st.session_state.sf_profiles
):
    st.session_state.sf_profiles = {
        "트레이너": new_profile()
    }

for username in list(
    st.session_state.sf_profiles.keys()
):
    st.session_state.sf_profiles[username] = (
        migrate_profile(
            st.session_state.sf_profiles[username]
        )
    )

defaults = {
    "sf_user": "트레이너",
    "sf_page": "home",
    "sf_last_draw": None,
    "sf_notice": ""
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

if (
    st.session_state.sf_user
    not in st.session_state.sf_profiles
):
    st.session_state.sf_user = next(
        iter(st.session_state.sf_profiles)
    )


def profile():
    username = st.session_state.sf_user

    if username not in st.session_state.sf_profiles:
        st.session_state.sf_profiles[username] = (
            new_profile()
        )

    return st.session_state.sf_profiles[username]


def partner():
    p = profile()

    return next(
        (
            pokemon
            for pokemon in p["collection"]
            if pokemon["uid"] == p["partner_uid"]
        ),
        p["collection"][0]
    )


def go(page):
    st.session_state.sf_page = page
    st.rerun()


def notify(message):
    st.session_state.sf_notice = message


# ==========================================
# 5. 포켓몬 이미지
# ==========================================

@st.cache_data(
    ttl=86400,
    show_spinner=False,
    max_entries=200
)
def get_pokemon_image(number, shiny):
    urls = []

    if shiny:
        urls.extend([
            f"{SPRITES}/other/official-artwork/shiny/{number}.png",
            f"{SPRITES}/shiny/{number}.png"
        ])

    urls.extend([
        f"{SPRITES}/other/official-artwork/{number}.png",
        f"{SPRITES}/{number}.png"
    ])

    for url in urls:
        try:
            response = requests.get(
                url,
                timeout=5
            )

            if (
                response.ok
                and response.headers.get(
                    "Content-Type",
                    ""
                ).startswith("image/")
                and len(response.content) < 5000000
            ):
                return response.content

        except requests.RequestException:
            continue

    return None


def pokemon_image(pokemon, width=200):
    image = get_pokemon_image(
        pokemon["number"],
        pokemon["shiny"]
    )

    if image:
        st.image(image, width=width)

    else:
        st.markdown(
            f"""
            <div class="image-fallback">
                🌙
                <p>{esc(pokemon["name"])}</p>
            </div>
            """,
            unsafe_allow_html=True
        )


def draw_pokemon():
    selected = random.choices(
        POKEMON,
        weights=[
            RARITY_WEIGHTS[item[3]]
            for item in POKEMON
        ],
        k=1
    )[0]

    pokemon = make_pokemon(selected[1])

    profile()["collection"].append(pokemon)

    st.session_state.sf_last_draw = pokemon["uid"]

    go("draw")


# ==========================================
# 6. 수면 시작·종료
# ==========================================

def start_sleep():
    p = profile()

    if p["sleep_start"] is None:
        p["sleep_start"] = now().isoformat()

    go("sleep")


def finish_sleep():
    p = profile()

    if not p["sleep_start"]:
        return

    start = parse_dt(p["sleep_start"])
    end = now()

    if end <= start:
        st.error("수면 시간이 올바르지 않습니다.")
        return

    p["records"].append({
        "uid": uid(),
        "start": start.isoformat(),
        "end": end.isoformat(),
        "goal": p["goal_hours"],
        "awake_minutes": 0.0,
        "feeling": "미입력",
        "memo": ""
    })

    p["sleep_start"] = None

    go("result")


def sleep_summary(record):
    start = parse_dt(record["start"])
    end = parse_dt(record["end"])

    elapsed = max(
        0,
        duration_minutes(start, end) / 60
    )

    estimated = max(
        0,
        elapsed - record["awake_minutes"] / 60
    )

    goal = max(
        1,
        record["goal"]
    )

    score = min(
        100,
        round(estimated / goal * 100)
    )

    return elapsed, estimated, score


# ==========================================
# 7. 저장·복원
# ==========================================

def export_json():
    data = {
        "version": "sleep-free-pokemon-2",
        "profiles": st.session_state.sf_profiles
    }

    return json.dumps(
        data,
        ensure_ascii=False,
        indent=2
    )


def import_json(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("파일이 너무 큽니다.")

    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("잘못된 파일입니다.")

    if data.get("version") not in [
        "sleep-free-pokemon-1",
        "sleep-free-pokemon-2"
    ]:
        raise ValueError(
            "지원하지 않는 저장 파일입니다."
        )

    incoming = data.get("profiles")

    if (
        not isinstance(incoming, dict)
        or not 1 <= len(incoming) <= 20
    ):
        raise ValueError("프로필 정보가 잘못됐습니다.")

    restored = {}

    for username, source in incoming.items():
        if (
            not isinstance(username, str)
            or not 1 <= len(username) <= 30
            or not isinstance(source, dict)
        ):
            raise ValueError("사용자 정보 오류")

        for key in [
            "collection",
            "records",
            "cycles",
            "naps",
            "day_checks"
        ]:
            items = source.get(key, [])

            if (
                not isinstance(items, list)
                or len(items) > 5000
            ):
                raise ValueError(
                    f"{key} 데이터 오류"
                )

        restored[username] = migrate_profile(
            source
        )

    st.session_state.sf_profiles = restored
    st.session_state.sf_user = next(
        iter(restored)
    )

    notify("저장 파일을 불러왔어요.")

    go("home")


def csv_data(records):
    if not records:
        return b""

    output = io.StringIO()

    fields = list(
        dict.fromkeys(
            key
            for record in records
            for key in record.keys()
        )
    )

    writer = csv.DictWriter(
        output,
        fieldnames=fields
    )

    writer.writeheader()

    for record in records:
        clean = {}

        for key, value in record.items():
            if (
                isinstance(value, str)
                and value.startswith(
                    ("=", "+", "-", "@")
                )
            ):
                clean[key] = "'" + value
            else:
                clean[key] = value

        writer.writerow(clean)

    return output.getvalue().encode("utf-8-sig")


# ==========================================
# 8. 디자인
# ==========================================

st.markdown("""
<style>

/* 전체 배경 */
.stApp {
    background: linear-gradient(
        140deg,
        #06152e,
        #123460
    );
    color: #f8fbff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

/* 제목 */
.stApp h1,
.stApp h2,
.stApp h3,
.stApp h4 {
    color: #ffffff !important;
}

/* 일반 글자 */
.stApp [data-testid="stMarkdownContainer"] {
    color: #f8fbff;
}

.stApp [data-testid="stWidgetLabel"] p {
    color: #f8fbff !important;
    font-weight: 600;
}

.stApp [data-testid="stCaptionContainer"] p {
    color: #cbdcf2 !important;
}

/* 버튼 */
.stApp div.stButton > button,
.stApp div.stDownloadButton > button,
.stApp div.stFormSubmitButton > button {
    background: #9edcff !important;
    color: #09213c !important;
    border: 1px solid #d9efff !important;
    border-radius: 13px !important;
    min-height: 48px;
}

.stApp div.stButton > button *,
.stApp div.stDownloadButton > button *,
.stApp div.stFormSubmitButton > button * {
    color: #09213c !important;
    font-weight: 700 !important;
}

.stApp div.stButton > button:hover {
    background: #c9ecff !important;
}

/* 입력창 */
.stApp [data-baseweb="input"] {
    background: #eaf3ff !important;
}

.stApp [data-baseweb="input"] input {
    background: #eaf3ff !important;
    color: #10243c !important;
    -webkit-text-fill-color: #10243c !important;
}

.stApp [data-baseweb="textarea"] {
    background: #eaf3ff !important;
}

.stApp [data-baseweb="textarea"] textarea {
    background: #eaf3ff !important;
    color: #10243c !important;
    -webkit-text-fill-color: #10243c !important;
}

/* 선택창 */
.stApp [data-baseweb="select"] > div {
    background: #eaf3ff !important;
    color: #10243c !important;
}

.stApp [data-baseweb="select"] span,
.stApp [data-baseweb="select"] input {
    color: #10243c !important;
    -webkit-text-fill-color: #10243c !important;
}

/* 드롭다운 목록 */
[data-baseweb="popover"],
[role="listbox"] {
    background: #eaf3ff !important;
}

[role="option"] {
    color: #10243c !important;
}

[role="option"]:hover {
    background: #cde6ff !important;
}

/* 알림창 */
.stApp [data-testid="stAlert"] {
    color: inherit !important;
}

.stApp [data-testid="stAlert"] p {
    color: inherit !important;
}

/* 통계 */
.stApp [data-testid="stMetricLabel"] p,
.stApp [data-testid="stMetricValue"] {
    color: #ffffff !important;
}

/* 화면 제목 */
.hero {
    text-align: center;
    font-size: clamp(30px, 5vw, 46px);
    font-weight: 900;
    color: white;
    margin: 18px 0;
}

.subtitle {
    text-align: center;
    color: #d5e6fb;
    margin-bottom: 25px;
}

/* 안내 카드 */
.panel {
    background: rgba(255,255,255,0.09);
    border: 1px solid rgba(210,230,255,0.25);
    border-radius: 20px;
    padding: 20px;
    margin: 12px 0 20px;
    color: white;
}

.panel * {
    color: white;
}

/* 포켓몬 이미지 오류 대체 */
.image-fallback {
    background: #173354;
    border-radius: 18px;
    text-align: center;
    padding: 35px;
    font-size: 35px;
    color: white;
}

/* 수면 화면 */
.sleep-scene {
    background: #020712;
    border: 1px solid #345077;
    border-radius: 24px;
    text-align: center;
    padding: 60px 20px;
    margin: 20px 0;
}

.sleep-scene h2,
.sleep-scene p {
    color: white !important;
}

/* 몬스터볼 */
.ball {
    width: 90px;
    height: 90px;
    margin: 15px auto;
    border: 5px solid #142033;
    border-radius: 50%;
    background: linear-gradient(
        to bottom,
        #ef4444 0%,
        #ef4444 44%,
        #142033 44%,
        #142033 56%,
        white 56%,
        white 100%
    );
    position: relative;
    animation: shake .5s 3;
}

.ball:after {
    content: "";
    position: absolute;
    left: 50%;
    top: 50%;
    width: 28px;
    height: 28px;
    transform: translate(-50%, -50%);
    background: white;
    border: 6px solid #142033;
    border-radius: 50%;
}

@keyframes shake {
    0%,100% {transform:rotate(0)}
    25% {transform:rotate(-18deg)}
    75% {transform:rotate(18deg)}
}

@media (prefers-reduced-motion: reduce) {
    .ball {animation:none}
}

</style>
""", unsafe_allow_html=True)


# ==========================================
# 9. 공통 화면 함수
# ==========================================

def page_title(title, subtitle=None):
    st.markdown(
        f'<div class="hero">{esc(title)}</div>',
        unsafe_allow_html=True
    )

    if subtitle:
        st.markdown(
            f'<div class="subtitle">{esc(subtitle)}</div>',
            unsafe_allow_html=True
        )


def record_selector(records, key):
    options = ["new"] + [
        record["uid"]
        for record in records
    ]

    labels = {}

    for record in records:
        record_uid = record["uid"]

        if "end" in record:
            when = parse_dt(record["end"])
        else:
            when = parse_dt(record["time"])

        labels[record_uid] = when.strftime(
            "%Y-%m-%d %H:%M"
        )

    selected = st.selectbox(
        "새 기록 또는 수정할 기록",
        options,
        format_func=lambda value: (
            "＋ 새 기록"
            if value == "new"
            else labels.get(value, "기록")
        ),
        key=key
    )

    return next(
        (
            record
            for record in records
            if record["uid"] == selected
        ),
        None
    )


def datetime_inputs(start, end):
    left, right = st.columns(2)

    with left:
        start_date = st.date_input(
            "시작 날짜",
            value=start.date()
        )

        start_time = st.time_input(
            "시작 시각",
            value=start.time().replace(
                tzinfo=None
            )
        )

    with right:
        end_date = st.date_input(
            "종료 날짜",
            value=end.date()
        )

        end_time = st.time_input(
            "종료 시각",
            value=end.time().replace(
                tzinfo=None
            )
        )

    return (
        combine_dt(start_date, start_time),
        combine_dt(end_date, end_time)
    )


def save_record(records, old, record):
    if old is None:
        record["uid"] = uid()
        records.append(record)

    else:
        record["uid"] = old["uid"]

        index = next(
            i
            for i, item in enumerate(records)
            if item["uid"] == old["uid"]
        )

        records[index] = record

    notify("기록을 저장했어요.")
    st.rerun()


def delete_record(records, old, key):
    if old is None:
        return

    confirm = st.checkbox(
        "선택한 기록 삭제 확인",
        key=f"confirm_{key}_{old['uid']}"
    )

    if confirm:
        if st.button(
            "🗑️ 기록 삭제",
            key=f"delete_{key}_{old['uid']}"
        ):
            records[:] = [
                record
                for record in records
                if record["uid"] != old["uid"]
            ]

            notify("기록을 삭제했어요.")
            st.rerun()


# ==========================================
# 10. Sleep Cycle 입력 페이지
# ==========================================

def cycle_page():
    page_title(
        "🌙 Sleep Cycle 기록",
        "수면 앱에서 확인한 지표를 직접 입력하세요."
    )

    st.info(
        "앱에 표시되지 않는 지표는 비워두세요. "
        "수면 시간은 분 단위로 입력합니다. "
        "예: 6시간 30분 = 390분"
    )

    records = profile()["cycles"]

    old = record_selector(
        records,
        "cycle_selector"
    )

    if old:
        start = parse_dt(old["start"])
        end = parse_dt(old["end"])

    else:
        end = now().replace(
            second=0,
            microsecond=0
        )

        start = end - timedelta(hours=7)

    with st.form(
        f"cycle_form_{old['uid'] if old else 'new'}"
    ):
        start_dt, end_dt = datetime_inputs(
            start,
            end
        )

        st.subheader("📊 수면 지표")

        values = {}

        columns = st.columns(2)

        for index, (key, info) in enumerate(
            CYCLE_FIELDS.items()
        ):
            label, maximum = info

            previous = (
                old.get(key)
                if old
                else None
            )

            with columns[index % 2]:
                values[key] = st.text_input(
                    label,
                    value=(
                        ""
                        if previous is None
                        else str(previous)
                    ),
                    placeholder="없으면 빈칸"
                )

        memo = st.text_area(
            "메모",
            value=old.get("memo", "") if old else "",
            max_chars=500
        )

        submitted = st.form_submit_button(
            "💾 수면 데이터 저장",
            use_container_width=True
        )

        if submitted:
            try:
                minutes = duration_minutes(
                    start_dt,
                    end_dt
                )

                if not 0 < minutes <= 1440:
                    raise ValueError(
                        "수면 시작·종료 시각을 확인해 주세요."
                    )

                if end_dt > now():
                    raise ValueError(
                        "미래 시각은 저장할 수 없어요."
                    )

                record = {
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "memo": memo
                }

                for key, (_, maximum) in (
                    CYCLE_FIELDS.items()
                ):
                    value = optional_number(
                        values[key],
                        maximum
                    )

                    if (
                        key != "quality"
                        and value is not None
                        and value > minutes
                    ):
                        raise ValueError(
                            f"{CYCLE_FIELDS[key][0]}이 "
                            "전체 기록 시간보다 길어요."
                        )

                    record[key] = value

                if any(
                    item is not old
                    and item["start"] == record["start"]
                    and item["end"] == record["end"]
                    for item in records
                ):
                    raise ValueError(
                        "같은 시간의 기록이 이미 있어요."
                    )

                save_record(
                    records,
                    old,
                    record
                )

            except (ValueError, TypeError) as error:
                st.error(str(error))

    delete_record(
        records,
        old,
        "cycle"
    )

    st.caption(
        "Sleep Cycle 점수와 수면 단계는 앱의 추정값입니다. "
        "실제 생리학적 수면 측정 결과와 "
        "동일하다고 볼 수는 없습니다."
    )


# ==========================================
# 11. 낮잠 기록 페이지
# ==========================================

def nap_page():
    page_title(
        "💤 낮잠 기록",
        "낮잠을 언제, 얼마나 잤는지 기록하세요."
    )

    records = profile()["naps"]

    old = record_selector(
        records,
        "nap_selector"
    )

    if old:
        start = parse_dt(old["start"])
        end = parse_dt(old["end"])

    else:
        end = now().replace(
            second=0,
            microsecond=0
        )

        start = end - timedelta(minutes=30)

    with st.form(
        f"nap_form_{old['uid'] if old else 'new'}"
    ):
        start_dt, end_dt = datetime_inputs(
            start,
            end
        )

        minutes = duration_minutes(
            start_dt,
            end_dt
        )

        if minutes > 0:
            st.metric(
                "낮잠 시간",
                f"{minutes:.0f}분"
            )

        memo = st.text_area(
            "낮잠 메모",
            value=old.get("memo", "") if old else "",
            max_chars=500
        )

        submitted = st.form_submit_button(
            "💾 낮잠 저장",
            use_container_width=True
        )

        if submitted:
            if not 0 < minutes <= 1440:
                st.error(
                    "낮잠 시작·종료 시간을 확인해 주세요."
                )

            elif end_dt > now():
                st.error(
                    "미래 시각은 저장할 수 없어요."
                )

            elif any(
                item is not old
                and parse_dt(item["start"]) < end_dt
                and parse_dt(item["end"]) > start_dt
                for item in records
            ):
                st.error(
                    "기존 낮잠 기록과 시간이 겹쳐요."
                )

            else:
                record = {
                    "start": start_dt.isoformat(),
                    "end": end_dt.isoformat(),
                    "memo": memo
                }

                save_record(
                    records,
                    old,
                    record
                )

    delete_record(
        records,
        old,
        "nap"
    )

    st.subheader("📚 최근 낮잠")

    if not records:
        st.info("아직 낮잠 기록이 없어요.")

    for record in sorted(
        records,
        key=lambda x: x["start"],
        reverse=True
    )[:20]:
        start = parse_dt(record["start"])
        end = parse_dt(record["end"])

        minutes = duration_minutes(
            start,
            end
        )

        st.write(
            f"💤 {start:%m/%d %H:%M}"
            f" ~ {end:%H:%M} "
            f"· **{minutes:.0f}분**"
        )


# ==========================================
# 12. 낮 시간 졸림 기록
# ==========================================

def day_page():
    page_title(
        "☀️ 낮 시간 점검",
        "하루 중 졸림이 나타나는 시간대를 기록하세요."
    )

    pokemon_image(
        partner(),
        170
    )

    records = profile()["day_checks"]

    old = record_selector(
        records,
        "day_selector"
    )

    when = (
        parse_dt(old["time"])
        if old
        else now()
    )

    with st.form(
        f"day_form_{old['uid'] if old else 'new'}"
    ):
        date = st.date_input(
            "졸림을 느낀 날짜",
            value=when.date()
        )

        time = st.time_input(
            "졸림을 느낀 시각",
            value=when.time().replace(
                tzinfo=None
            )
        )

        level = st.select_slider(
            "졸림 정도",
            options=[1, 2, 3, 4, 5],
            value=(
                old["sleepiness"]
                if old
                else 2
            ),
            format_func=lambda value: {
                1: "1 · 또렷함",
                2: "2 · 약간 나른함",
                3: "3 · 졸림",
                4: "4 · 매우 졸림",
                5: "5 · 깨어 있기 어려움"
            }[value]
        )

        submitted = st.form_submit_button(
            "💾 졸림 기록 저장",
            use_container_width=True
        )

        if submitted:
            moment = combine_dt(
                date,
                time
            )

            if moment > now():
                st.error(
                    "미래 시각은 기록할 수 없어요."
                )

            else:
                record = {
                    "time": moment.isoformat(),
                    "sleepiness": level
                }

                save_record(
                    records,
                    old,
                    record
                )

    delete_record(
        records,
        old,
        "day"
    )

    if records:
        latest = max(
            records,
            key=lambda x: x["time"]
        )

        if latest["sleepiness"] >= 4:
            st.warning(
                "최근 기록에서 강한 졸림을 보고했어요. "
                "필요하다면 안전한 곳에서 휴식하세요."
            )

    st.subheader("🕒 최근 졸림 기록")

    for record in sorted(
        records,
        key=lambda x: x["time"],
        reverse=True
    )[:20]:
        when = parse_dt(record["time"])

        st.write(
            f"{when:%m/%d %H:%M}"
            f" · 졸림 **{record['sleepiness']}/5**"
        )

    if st.button(
        "💤 낮잠 기록하기",
        use_container_width=True
    ):
        go("nap")

    st.caption(
        "졸림 정도는 사용자가 직접 입력하는 "
        "주관적 평가입니다. 자동 감지 기능은 아닙니다."
    )


# ==========================================
# 13. 데이터 분석
# ==========================================

def analysis_page():
    page_title(
        "📊 수면 데이터 분석",
        "기록이 쌓이면 수면과 졸림의 변화를 살펴볼 수 있어요."
    )

    p = profile()

    st.subheader("🌙 Sleep Cycle 수면 기록")

    cycle_rows = []

    for record in p["cycles"]:
        end = parse_dt(record["end"])

        cycle_rows.append({
            "날짜": end.date().isoformat(),
            "수면 시간(분)": record.get("asleep"),
            "수면 점수": record.get("quality"),
            "잠들기까지(분)": record.get("latency"),
            "코골이(분)": record.get("snoring")
        })

    if cycle_rows:
        df = pd.DataFrame(cycle_rows)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        daily = df.groupby(
            "날짜",
            as_index=True
        ).agg({
            "수면 시간(분)": lambda x: (
                x.sum()
                if x.notna().any()
                else float("nan")
            ),
            "수면 점수": "mean"
        })

        st.subheader("📈 수면 시간 변화")

        st.line_chart(
            daily[["수면 시간(분)"]]
        )

        st.subheader("📈 수면 점수 변화")

        st.line_chart(
            daily[["수면 점수"]]
        )

    else:
        st.info(
            "Sleep Cycle 데이터를 입력하면 "
            "그래프가 나타나요."
        )

    st.divider()

    st.subheader("☀️ 졸림 변화")

    if p["day_checks"]:
        day_rows = []

        for record in p["day_checks"]:
            when = parse_dt(record["time"])

            day_rows.append({
                "시각": when,
                "졸림 정도": record["sleepiness"]
            })

        day_df = pd.DataFrame(
            day_rows
        ).sort_values("시각")

        st.line_chart(
            day_df.set_index("시각")
        )

        st.dataframe(
            day_df,
            use_container_width=True,
            hide_index=True
        )

    else:
        st.info(
            "낮 시간 졸림을 기록하면 "
            "시간대별 그래프가 나타나요."
        )

    st.divider()

    st.subheader("💤 낮잠 분석")

    nap_rows = []

    for record in p["naps"]:
        start = parse_dt(record["start"])
        end = parse_dt(record["end"])

        nap_rows.append({
            "날짜": start.date().isoformat(),
            "시작": start.strftime("%H:%M"),
            "종료": end.strftime("%H:%M"),
            "낮잠 시간(분)": duration_minutes(
                start,
                end
            )
        })

    if nap_rows:
        nap_df = pd.DataFrame(nap_rows)

        st.dataframe(
            nap_df,
            use_container_width=True,
            hide_index=True
        )

        daily_naps = nap_df.groupby(
            "날짜"
        )["낮잠 시간(분)"].sum()

        st.bar_chart(daily_naps)

    else:
        st.info("아직 낮잠 기록이 없어요.")

    st.divider()

    st.subheader("🔍 수면과 졸림의 관계")

    if cycle_rows and p["day_checks"]:
        sleep_df = pd.DataFrame(cycle_rows)

        sleep_daily = sleep_df.groupby(
            "날짜"
        )["수면 점수"].mean()

        sleepy_rows = []

        for record in p["day_checks"]:
            when = parse_dt(record["time"])

            sleepy_rows.append({
                "날짜": when.date().isoformat(),
                "졸림": record["sleepiness"]
            })

        sleepy_df = pd.DataFrame(sleepy_rows)

        sleepy_daily = sleepy_df.groupby(
            "날짜"
        )["졸림"].mean()

        combined = pd.concat(
            [
                sleep_daily,
                sleepy_daily
            ],
            axis=1
        ).dropna()

        if (
            len(combined) >= 3
            and combined["수면 점수"].nunique() > 1
            and combined["졸림"].nunique() > 1
        ):
            correlation = combined.corr().iloc[0, 1]

            st.metric(
                "수면 점수와 같은 날짜 평균 졸림의 상관계수",
                f"{correlation:.3f}"
            )

            st.caption(
                f"분석에 사용된 날짜: {len(combined)}일. "
                "상관관계는 인과관계가 아니며, "
                "기록 시간대와 횟수에 영향을 받습니다."
            )

        else:
            st.info(
                "두 지표가 모두 있는 날짜가 "
                "3일 이상 쌓이면 상관관계를 계산해요."
            )

    st.divider()

    st.subheader("📥 CSV 다운로드")

    for label, key in [
        ("Sleep Cycle", "cycles"),
        ("낮잠", "naps"),
        ("졸림", "day_checks")
    ]:
        if p[key]:
            st.download_button(
                f"{label} CSV 다운로드",
                data=csv_data(p[key]),
                file_name=f"sleep_free_{key}.csv",
                mime="text/csv",
                key=f"csv_{key}",
                use_container_width=True
            )


# ==========================================
# 14. 오른쪽 메뉴
# ==========================================

main, right = st.columns(
    [3, 1],
    gap="large"
)

with right:
    st.markdown("### 🌙 Sleep Free")

    usernames = list(
        st.session_state.sf_profiles
    )

    selected = st.selectbox(
        "사용자 프로필",
        usernames,
        index=usernames.index(
            st.session_state.sf_user
        )
    )

    if selected != st.session_state.sf_user:
        st.session_state.sf_user = selected
        go("home")

    with st.expander("＋ 사용자 추가"):
        username = st.text_input(
            "사용자 이름",
            max_chars=30
        )

        if st.button(
            "사용자 추가",
            use_container_width=True
        ):
            name = username.strip()

            if not name:
                st.warning("이름을 입력해 주세요.")

            elif name in st.session_state.sf_profiles:
                st.warning("이미 있는 이름입니다.")

            elif len(st.session_state.sf_profiles) >= 20:
                st.warning("최대 20명까지 추가할 수 있어요.")

            else:
                st.session_state.sf_profiles[name] = (
                    new_profile()
                )

                st.session_state.sf_user = name
                go("home")

    p = profile()

    st.markdown(
        f"""
        <div class="panel">
            <b>📦 포켓몬 {len(p["collection"])}마리</b>
            <p>🌙 파트너: {esc(partner()["name"])}</p>
            <p>📚 수면 기록: {len(p["records"])}회</p>
            <p>📝 Sleep Cycle: {len(p["cycles"])}회</p>
        </div>
        """,
        unsafe_allow_html=True
    )

    menus = [
        ("🏠 홈", "home"),
        ("🎲 포켓몬 뽑기", "draw"),
        ("📦 포켓몬 보관함", "collection"),
        ("🌙 수면 추적", "sleep"),
        ("📝 Sleep Cycle 입력", "cycle"),
        ("☀️ 낮 시간 점검", "day"),
        ("💤 낮잠 기록", "nap"),
        ("📊 데이터 분석", "analysis"),
        ("📚 수면 기록", "history"),
        ("⚙️ 설정", "settings")
    ]

    for label, page in menus:
        if st.button(
            label,
            key=f"nav_{page}",
            use_container_width=True
        ):
            go(page)

    st.divider()

    st.download_button(
        "💾 전체 기록 백업",
        data=export_json(),
        file_name="sleep_free_save.json",
        mime="application/json",
        use_container_width=True
    )

    with st.expander("📂 저장 파일 불러오기"):
        uploaded = st.file_uploader(
            "JSON 파일",
            type=["json"]
        )

        st.caption(
            "불러오면 현재 데이터가 "
            "저장 파일의 내용으로 교체됩니다."
        )

        if st.button(
            "불러오기",
            use_container_width=True
        ):
            if uploaded is None:
                st.warning("파일을 선택해 주세요.")

            else:
                try:
                    import_json(
                        uploaded.getvalue()
                    )

                except (
                    ValueError,
                    TypeError,
                    KeyError
                ) as error:
                    st.error(
                        f"불러오기 실패: {error}"
                    )

    st.caption(
        "현재는 실제 로그인 기능이 아닙니다. "
        "세션이 종료되면 데이터가 사라질 수 있으므로 "
        "주기적으로 백업하세요."
    )


# ==========================================
# 15. 메인 페이지
# ==========================================

with main:
    p = profile()
    page = st.session_state.sf_page

    if st.session_state.sf_notice:
        st.success(
            st.session_state.sf_notice
        )

        st.session_state.sf_notice = ""

    # --------------------------------------
    # 홈
    # --------------------------------------

    if page == "home":
        page_title(
            "☁️ 🌙 Sleep Free ☁️",
            "포켓몬과 함께 수면 습관을 기록해 보세요."
        )

        left, center, right_home = st.columns(
            [1, 2, 1]
        )

        with center:
            pokemon_image(
                partner(),
                250
            )

            st.markdown(
                f"""
                <div style="
                    text-align:center;
                    color:white;
                    font-weight:800;
                ">
                    오늘 함께 잘 포켓몬:
                    {esc(partner()["name"])}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            """
            <div class="panel">
                🌙 밤에는 수면을 기록하고,
                ☀️ 낮에는 졸림과 낮잠을 기록하세요.
                Sleep Cycle 데이터를 입력하면
                수면 패턴을 분석할 수 있어요.
            </div>
            """,
            unsafe_allow_html=True
        )

        a, b = st.columns(2)

        with a:
            if st.button(
                "🌙 수면 시작",
                use_container_width=True
            ):
                if p["sleep_start"]:
                    go("sleep")
                else:
                    start_sleep()

            if st.button(
                "🎲 포켓몬 뽑기",
                use_container_width=True
            ):
                draw_pokemon()

        with b:
            if st.button(
                "☀️ 낮 시간 점검",
                use_container_width=True
            ):
                go("day")

            if st.button(
                "📦 수면 파트너 선택",
                use_container_width=True
            ):
                go("collection")

        if st.button(
            "📝 Sleep Cycle 데이터 입력",
            use_container_width=True
        ):
            go("cycle")

    # --------------------------------------
    # 포켓몬 뽑기
    # --------------------------------------

    elif page == "draw":
        page_title(
            "🎲 포켓몬 뽑기",
            "새로운 수면 파트너를 만나 보세요."
        )

        last_uid = st.session_state.sf_last_draw

        found = next(
            (
                item
                for item in p["collection"]
                if item["uid"] == last_uid
            ),
            None
        )

        if found:
            st.markdown(
                '<div class="ball"></div>',
                unsafe_allow_html=True
            )

            pokemon_image(found, 250)

            st.markdown(
                f"### {esc(found['name'])}"
            )

            st.write(
                f"Lv.{found['level']} · "
                f"{found['rarity']} · "
                f"{found['types']}"
            )

            if found["shiny"]:
                st.success("✨ 이로치 포켓몬!")

            st.success(
                "보관함에 포켓몬이 추가됐어요."
            )

            if st.button(
                "🌙 이 포켓몬과 함께 자기",
                use_container_width=True
            ):
                p["partner_uid"] = found["uid"]
                go("home")

        else:
            pokemon_image(
                partner(),
                180
            )

        if st.button(
            "✨ 몬스터볼 던지기",
            use_container_width=True
        ):
            draw_pokemon()

        if st.button(
            "📦 보관함으로",
            use_container_width=True
        ):
            go("collection")

    # --------------------------------------
    # 포켓몬 보관함
    # --------------------------------------

    elif page == "collection":
        page_title("📦 포켓몬 보관함")

        collection = p["collection"]

        unique = len({
            item["number"]
            for item in collection
        })

        shiny_count = sum(
            item["shiny"]
            for item in collection
        )

        st.write(
            f"보유 **{len(collection)}마리** · "
            f"발견 **{unique}종** · "
            f"이로치 **{shiny_count}마리**"
        )

        search = st.text_input("🔎 포켓몬 검색")

        shiny_only = st.checkbox(
            "이로치만 보기"
        )

        order = st.selectbox(
            "정렬",
            [
                "최근 획득순",
                "레벨 높은 순",
                "도감 번호순"
            ]
        )

        records = [
            item
            for item in collection
            if search.strip() in item["name"]
            and (
                not shiny_only
                or item["shiny"]
            )
        ]

        if order == "최근 획득순":
            records.reverse()

        elif order == "레벨 높은 순":
            records.sort(
                key=lambda item: item["level"],
                reverse=True
            )

        else:
            records.sort(
                key=lambda item: item["number"]
            )

        if records:
            page_size = 9

            total_pages = (
                len(records) + page_size - 1
            ) // page_size

            page_number = st.selectbox(
                "페이지",
                range(1, total_pages + 1)
            )

            start_index = (
                page_number - 1
            ) * page_size

            visible = records[
                start_index:start_index + page_size
            ]

            columns = st.columns(3)

            for index, pokemon in enumerate(visible):
                with columns[index % 3]:
                    with st.container(border=True):
                        pokemon_image(
                            pokemon,
                            150
                        )

                        st.markdown(
                            f"**{esc(pokemon['name'])}**"
                        )

                        st.caption(
                            f"No.{pokemon['number']:04d} "
                            f"· Lv.{pokemon['level']} "
                            f"· {pokemon['rarity']}"
                        )

                        if (
                            pokemon["uid"]
                            == p["partner_uid"]
                        ):
                            st.success(
                                "🌙 현재 파트너"
                            )

                        else:
                            if st.button(
                                "🌙 함께 자기",
                                key=f"partner_{pokemon['uid']}",
                                use_container_width=True
                            ):
                                p["partner_uid"] = (
                                    pokemon["uid"]
                                )

                                go("home")

        else:
            st.info("검색 결과가 없어요.")

        if st.button(
            "🎲 포켓몬 더 뽑기",
            use_container_width=True
        ):
            draw_pokemon()

    # --------------------------------------
    # 수면 추적
    # --------------------------------------

    elif page == "sleep":
        if not p["sleep_start"]:
            page_title(
                "🌙 수면 시작",
                "포켓몬과 함께 잠자리에 들어요."
            )

            pokemon_image(
                partner(),
                220
            )

            if st.button(
                "🌙 수면 추적 시작",
                use_container_width=True
            ):
                start_sleep()

        else:
            started = parse_dt(
                p["sleep_start"]
            )

            st.markdown(
                f"""
                <div class="sleep-scene">
                    <h2>🌙 수면 기록 중</h2>
                    <p>
                        수면 파트너:
                        {esc(partner()["name"])}
                    </p>
                    <p>
                        시작 시각:
                        {started:%m/%d %H:%M}
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

            if st.button(
                "☀️ 수면 종료",
                use_container_width=True
            ):
                finish_sleep()

            st.caption(
                "수면 시작과 종료 사이의 시간을 기록합니다. "
                "실제 잠든 시간을 자동으로 측정하지는 않아요."
            )

    # --------------------------------------
    # 수면 결과
    # --------------------------------------

    elif page == "result":
        if not p["records"]:
            st.info("수면 기록이 없어요.")

        else:
            record = p["records"][-1]

            elapsed, estimated, score = (
                sleep_summary(record)
            )

            page_title("☀️ 수면 결과")

            pokemon_image(
                partner(),
                200
            )

            a, b, c = st.columns(3)

            a.metric(
                "기록 시간",
                f"{elapsed:.1f}시간"
            )

            b.metric(
                "추정 수면 시간",
                f"{estimated:.1f}시간"
            )

            c.metric(
                "목표 달성도",
                f"{score}점"
            )

            st.caption(
                "달성도는 목표 시간 대비 기록된 "
                "추정 수면 시간의 비율입니다. "
                "수면의 질 점수가 아닙니다."
            )

            with st.form(
                f"result_form_{record['uid']}"
            ):
                maximum = max(
                    0.0,
                    elapsed * 60
                )

                awake = st.number_input(
                    "잠들기까지 + 중간에 깨어 있던 시간(분)",
                    min_value=0.0,
                    max_value=maximum,
                    value=min(
                        float(record["awake_minutes"]),
                        maximum
                    ),
                    step=5.0
                )

                feelings = [
                    "미입력",
                    "개운함",
                    "보통",
                    "피곤함",
                    "매우 피곤함"
                ]

                feeling = st.selectbox(
                    "기상 후 느낌",
                    feelings,
                    index=(
                        feelings.index(record["feeling"])
                        if record["feeling"] in feelings
                        else 0
                    )
                )

                memo = st.text_area(
                    "메모",
                    value=record["memo"],
                    max_chars=500
                )

                if st.form_submit_button(
                    "기록 저장"
                ):
                    record["awake_minutes"] = float(awake)
                    record["feeling"] = feeling
                    record["memo"] = memo

                    notify("수면 기록을 수정했어요.")
                    st.rerun()

            if st.button(
                "📝 Sleep Cycle 지표 입력",
                use_container_width=True
            ):
                go("cycle")

    # --------------------------------------
    # 추가 기록 페이지
    # --------------------------------------

    elif page == "cycle":
        cycle_page()

    elif page == "nap":
        nap_page()

    elif page == "day":
        day_page()

    elif page == "analysis":
        analysis_page()

    # --------------------------------------
    # 수면 기록 보관함
    # --------------------------------------

    elif page == "history":
        page_title("📚 수면 기록 보관함")

        st.subheader("🌙 수면 추적 기록")

        if not p["records"]:
            st.info("아직 수면 기록이 없어요.")

        for record in reversed(p["records"][-100:]):
            elapsed, estimated, score = (
                sleep_summary(record)
            )

            end = parse_dt(record["end"])

            with st.expander(
                f"{end:%Y-%m-%d} · "
                f"{elapsed:.1f}시간"
            ):
                st.write(
                    f"추정 수면 시간: {estimated:.1f}시간"
                )

                st.write(
                    f"목표 달성도: {score}점"
                )

                st.write(
                    f"기상 후 느낌: {record['feeling']}"
                )

                if record["memo"]:
                    st.write(record["memo"])

        st.divider()

        st.subheader("📝 Sleep Cycle 기록")

        if not p["cycles"]:
            st.info(
                "아직 Sleep Cycle 기록이 없어요."
            )

        for record in reversed(p["cycles"][-100:]):
            end = parse_dt(record["end"])

            with st.expander(
                f"{end:%Y-%m-%d} · Sleep Cycle"
            ):
                for key, info in CYCLE_FIELDS.items():
                    label = info[0]
                    value = record.get(key)

                    st.write(
                        f"{label}: "
                        f"{value if value is not None else '미입력'}"
                    )

    # --------------------------------------
    # 설정
    # --------------------------------------

    elif page == "settings":
        page_title("⚙️ 설정")

        with st.form("settings_form"):
            goal = st.number_input(
                "목표 수면 시간",
                min_value=1.0,
                max_value=14.0,
                value=float(p["goal_hours"]),
                step=0.5
            )

            if st.form_submit_button(
                "설정 저장"
            ):
                p["goal_hours"] = float(goal)

                st.success(
                    "목표 수면 시간을 저장했어요."
                )

        st.divider()

        st.subheader("🌙 현재 수면 파트너")

        pokemon_image(
            partner(),
            180
        )

        st.write(
            f"**{partner()['name']}**"
        )

        if st.button(
            "📦 파트너 변경",
            use_container_width=True
        ):
            go("collection")

        st.divider()

        st.subheader("⌚ 기기 연결")

        st.info(
            "현재 버전은 Sleep Cycle 수동 입력 방식입니다. "
            "Sleep Cycle 계정 자동 동기화나 "
            "웨어러블 연결은 지원하지 않습니다."
        )


# ==========================================
# 16. 앱 안내
# ==========================================

with st.expander("📖 Sleep Free 안내"):
    st.write(
        "Sleep Free는 포켓몬 수집과 수면 습관 "
        "기록을 결합한 웹앱입니다. "
        "Sleep Cycle 지표는 직접 입력하고, "
        "낮 시간 졸림과 낮잠을 기록할 수 있습니다. "
        "수면 점수는 외부 앱의 추정값이며, "
        "이 앱은 의료 진단 도구가 아닙니다. "
        "데이터는 현재 Streamlit 세션에 저장되므로 "
        "중요한 기록은 JSON으로 백업해 주세요."
    )
