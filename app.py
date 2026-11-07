
import streamlit as st
import requests
import random
import json
import uuid
import html
import math
from datetime import datetime, timedelta, timezone

# ============================================
# 1. 기본 설정
# ============================================

st.set_page_config(
    page_title="Sleep Free",
    page_icon="🌙",
    layout="wide"
)

KST = timezone(timedelta(hours=9))

SPRITES = (
    "https://raw.githubusercontent.com/"
    "PokeAPI/sprites/master/sprites/pokemon"
)

POKEMON_LIST = [
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

DEX = {
    item[1]: item
    for item in POKEMON_LIST
}

RARITY_WEIGHTS = {
    "일반": 12,
    "희귀": 5,
    "초희귀": 1,
    "환상": 0.15
}


# ============================================
# 2. 기본 함수
# ============================================

def now():
    return datetime.now(KST)


def parse_time(value):
    dt = datetime.fromisoformat(value)

    if dt.tzinfo is None:
        raise ValueError("시간대가 없는 날짜입니다.")

    return dt.astimezone(KST)


def safe(value):
    return html.escape(str(value), quote=True)


def valid_number(value, low, high):
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and low <= value <= high
    )


def create_pokemon(
    number,
    level=None,
    shiny=None,
    uid=None
):
    name, number, types, rarity = DEX[number]

    if level is None:
        level = random.randint(1, 10)

    if shiny is None:
        shiny = random.random() < 0.05

    return {
        "uid": uid or str(uuid.uuid4()),
        "number": number,
        "name": name,
        "types": types,
        "rarity": rarity,
        "level": level,
        "shiny": shiny,
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
    starter = create_pokemon(
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
        "day_checks": []
    }


# ============================================
# 3. 기존 데이터 자동 변환
# ============================================

def migrate_profile(p):
    """
    이전 버전에서 collection이 없는 경우에도
    오류 없이 새 데이터 구조로 변환합니다.
    """

    if not isinstance(p, dict):
        return new_profile()

    # 이전 수면 목표 설정 복원
    goal = p.get(
        "goal_hours",
        p.get("target", 8.0)
    )

    if not valid_number(goal, 1, 14):
        goal = 8.0

    p["goal_hours"] = float(goal)

    # 기존 포켓몬 보관함 확인
    old_collection = p.get("collection")

    if not isinstance(old_collection, list):
        old_collection = []

    cleaned = []
    used_uids = set()

    for item in old_collection:
        if not isinstance(item, dict):
            continue

        number = item.get(
            "number",
            item.get("species_id")
        )

        if (
            type(number) is not int
            or number not in DEX
        ):
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

        uid = item.get("uid")

        if (
            not isinstance(uid, str)
            or not uid
            or uid in used_uids
        ):
            uid = str(uuid.uuid4())

        used_uids.add(uid)

        pokemon = create_pokemon(
            number,
            level=level,
            shiny=shiny,
            uid=uid
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

    # 보관함이 없는 이전 사용자에게 잠만보 지급
    if not cleaned:
        cleaned = [
            create_pokemon(
                143,
                level=5,
                shiny=False
            )
        ]

    p["collection"] = cleaned

    # 수면 파트너 확인
    valid_uids = {
        item["uid"]
        for item in cleaned
    }

    if p.get("partner_uid") not in valid_uids:
        p["partner_uid"] = cleaned[0]["uid"]

    # 이전 수면 시작 시간 복원
    if "sleep_start" not in p:
        p["sleep_start"] = p.get(
            "active_start"
        )

    if p["sleep_start"] is not None:
        try:
            start = parse_time(p["sleep_start"])

            if start > now():
                p["sleep_start"] = None

        except (ValueError, TypeError):
            p["sleep_start"] = None

    # 기존 수면 기록 보완
    records = p.get("records", [])

    if not isinstance(records, list):
        records = []

    cleaned_records = []

    for record in records:
        if not isinstance(record, dict):
            continue

        try:
            start = parse_time(record["start"])
            end = parse_time(record["end"])

            if end < start:
                continue

            target = record.get(
                "goal",
                record.get(
                    "target",
                    p["goal_hours"]
                )
            )

            if not valid_number(target, 1, 14):
                target = p["goal_hours"]

            awake = record.get(
                "awake_minutes",
                0.0
            )

            duration_minutes = (
                end - start
            ).total_seconds() / 60

            if not valid_number(
                awake,
                0,
                duration_minutes
            ):
                awake = 0.0

            cleaned_records.append({
                "uid": str(
                    record.get("uid")
                    or uuid.uuid4()
                ),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "goal": float(target),
                "awake_minutes": float(awake),
                "feeling": str(
                    record.get(
                        "feeling",
                        "미입력"
                    )
                )[:50],
                "memo": str(
                    record.get("memo", "")
                )[:500]
            })

        except (
            KeyError,
            ValueError,
            TypeError,
            OverflowError
        ):
            continue

    p["records"] = cleaned_records

    checks = p.get("day_checks", [])

    if not isinstance(checks, list):
        checks = []

    cleaned_checks = []

    for check in checks:
        if not isinstance(check, dict):
            continue

        try:
            when = parse_time(check["time"])
            sleepy = check["sleepiness"]

            if (
                type(sleepy) is int
                and 1 <= sleepy <= 5
            ):
                cleaned_checks.append({
                    "time": when.isoformat(),
                    "sleepiness": sleepy
                })

        except (
            KeyError,
            ValueError,
            TypeError
        ):
            continue

    p["day_checks"] = cleaned_checks

    return p


# ============================================
# 4. 세션 초기화
# ============================================

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

# 모든 기존 사용자 데이터 변환
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
    "sf_alarm_day": "",
    "sf_alarm_on": False,
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

today = now().date().isoformat()

if st.session_state.sf_alarm_day != today:
    st.session_state.sf_alarm_day = today
    st.session_state.sf_alarm_on = False


def profile():
    username = st.session_state.sf_user

    if username not in st.session_state.sf_profiles:
        st.session_state.sf_profiles[username] = (
            new_profile()
        )

    return st.session_state.sf_profiles[username]


def partner():
    p = profile()

    found = next(
        (
            item
            for item in p["collection"]
            if item["uid"] == p["partner_uid"]
        ),
        None
    )

    return found or p["collection"][0]


def go(page):
    st.session_state.sf_page = page
    st.rerun()


# ============================================
# 5. 포켓몬 이미지
# ============================================

@st.cache_data(
    ttl=86400,
    show_spinner=False
)
def get_image(number, shiny):
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


def pokemon_image(p, width=200):
    image = get_image(
        p["number"],
        p["shiny"]
    )

    if image is not None:
        st.image(image, width=width)

    else:
        st.markdown(
            f"""
            <div class="image-fallback">
                <div style="font-size:45px">🌙</div>
                {safe(p["name"])}
            </div>
            """,
            unsafe_allow_html=True
        )


def pokemon_details(p, width=220):
    pokemon_image(p, width)

    st.markdown(
        f"### {safe(p['name'])}"
    )

    st.write(
        f"Lv. {p['level']} · {p['rarity']}"
    )

    st.write(
        f"타입: {p['types']}"
    )

    if p["shiny"]:
        st.success("✨ 이로치 포켓몬!")

    st.caption(
        f"획득한 볼: {p['ball']}"
    )


# ============================================
# 6. 포켓몬 뽑기
# ============================================

def draw_pokemon():
    chosen = random.choices(
        POKEMON_LIST,
        weights=[
            RARITY_WEIGHTS[item[3]]
            for item in POKEMON_LIST
        ],
        k=1
    )[0]

    pokemon = create_pokemon(
        chosen[1]
    )

    profile()["collection"].append(pokemon)

    st.session_state.sf_last_draw = (
        pokemon["uid"]
    )

    go("draw")


# ============================================
# 7. 수면 기록
# ============================================

def start_sleep():
    p = profile()

    if p["sleep_start"] is None:
        p["sleep_start"] = now().isoformat()

    go("sleep")


def finish_sleep():
    p = profile()

    if p["sleep_start"] is None:
        return

    start = parse_time(
        p["sleep_start"]
    )

    end = now()

    if end < start:
        st.error(
            "수면 시작·종료 시간이 올바르지 않습니다."
        )
        return

    p["records"].append({
        "uid": str(uuid.uuid4()),
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
    elapsed = max(
        0.0,
        (
            parse_time(record["end"])
            - parse_time(record["start"])
        ).total_seconds() / 3600
    )

    estimated = max(
        0.0,
        elapsed - record["awake_minutes"] / 60
    )

    goal = max(
        1.0,
        record["goal"]
    )

    score = min(
        100,
        round(estimated / goal * 100)
    )

    return elapsed, estimated, score


# ============================================
# 8. 저장 및 불러오기
# ============================================

def save_data():
    return json.dumps(
        {
            "version": "sleep-free-pokemon-2",
            "profiles": st.session_state.sf_profiles
        },
        ensure_ascii=False,
        indent=2
    )


def load_data(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("파일이 너무 큽니다.")

    data = json.loads(raw)

    if not isinstance(data, dict):
        raise ValueError("파일 형식 오류")

    supported = [
        "sleep-free-pokemon-1",
        "sleep-free-pokemon-2",
        "sleep-free-1"
    ]

    if data.get("version") not in supported:
        raise ValueError(
            "지원하지 않는 저장 파일입니다."
        )

    incoming = data.get("profiles")

    if (
        not isinstance(incoming, dict)
        or not 1 <= len(incoming) <= 20
    ):
        raise ValueError("프로필 정보 오류")

    restored = {}

    for username, source in incoming.items():
        if (
            not isinstance(username, str)
            or not 1 <= len(username) <= 30
            or not isinstance(source, dict)
        ):
            raise ValueError("사용자 정보 오류")

        if (
            "collection" in source
            and (
                not isinstance(
                    source["collection"],
                    list
                )
                or len(source["collection"]) > 1500
            )
        ):
            raise ValueError("보관함 정보 오류")

        if (
            "records" in source
            and (
                not isinstance(
                    source["records"],
                    list
                )
                or len(source["records"]) > 5000
            )
        ):
            raise ValueError("수면 기록 정보 오류")

        if (
            "day_checks" in source
            and (
                not isinstance(
                    source["day_checks"],
                    list
                )
                or len(source["day_checks"]) > 5000
            )
        ):
            raise ValueError("낮 시간 기록 오류")

        restored[username] = migrate_profile(
            source
        )

    st.session_state.sf_profiles = restored
    st.session_state.sf_user = next(
        iter(restored)
    )

    st.session_state.sf_last_draw = None
    st.session_state.sf_alarm_on = False

    st.session_state.sf_notice = (
        "저장 파일을 불러왔어요."
    )

    go("home")


# ============================================
# 9. 화면 디자인
# ============================================

st.markdown("""
<style>

.stApp {
    background: linear-gradient(
        140deg,
        #06152e,
        #123460
    );
    color: #ffffff;
}

header[data-testid="stHeader"] {
    background: transparent;
}

.block-container {
    padding-top: 2rem;
    padding-bottom: 3rem;
}

h1, h2, h3, h4 {
    color: #ffffff !important;
}

[data-testid="stMarkdownContainer"] {
    color: #ffffff;
}

[data-testid="stMarkdownContainer"] p {
    color: #ffffff;
}

[data-testid="stCaptionContainer"] p {
    color: #cbdcf2 !important;
}

[data-testid="stWidgetLabel"] p {
    color: #ffffff !important;
}

[data-testid="stMetricLabel"] p,
[data-testid="stMetricValue"] {
    color: #ffffff !important;
}

div.stButton > button,
div.stDownloadButton > button {
    background: #8ed5ff !important;
    color: #071b33 !important;
    border: 1px solid #d7efff !important;
    border-radius: 14px !important;
    min-height: 50px;
}

div.stButton > button p,
div.stDownloadButton > button p {
    color: #071b33 !important;
    font-weight: 800 !important;
}

div.stButton > button:hover {
    background: #c7ecff !important;
}

div.stButton > button:disabled {
    opacity: 0.5;
}

[data-baseweb="input"] input,
[data-baseweb="textarea"] textarea {
    background: #eaf3ff !important;
    color: #0b2443 !important;
    -webkit-text-fill-color: #0b2443 !important;
}

[data-baseweb="select"] > div {
    background: #eaf3ff !important;
    color: #0b2443 !important;
}

[data-baseweb="select"] span,
[data-baseweb="select"] input {
    color: #0b2443 !important;
    -webkit-text-fill-color: #0b2443 !important;
}

[data-baseweb="popover"] {
    background: #f4f8ff !important;
}

[role="listbox"] {
    background: #f4f8ff !important;
}

[role="option"] {
    color: #0b2443 !important;
}

[role="option"]:hover {
    background: #dbeafe !important;
}

.hero {
    text-align: center;
    font-size: clamp(32px,5vw,49px);
    font-weight: 900;
    margin: 20px 0 10px;
    color: #ffffff;
}

.subtitle {
    text-align: center;
    color: #d4e4fa;
    margin-bottom: 25px;
    line-height: 1.7;
}

.panel {
    background: rgba(255,255,255,.085);
    border: 1px solid rgba(201,227,255,.26);
    border-radius: 21px;
    padding: 20px;
    margin: 10px 0 20px;
    color: white;
}

.panel p,
.panel b {
    color: white;
}

.sleep-scene {
    background: #02060e;
    border: 1px solid #334155;
    border-radius: 24px;
    text-align: center;
    padding: 75px 18px;
    margin: 20px 0;
    color: white;
}

.sleep-scene h2,
.sleep-scene p {
    color: white !important;
}

.image-fallback {
    border: 1px solid #304c75;
    border-radius: 20px;
    background: #172b49;
    text-align: center;
    padding: 24px;
    color: white;
    min-height: 140px;
}

.ball {
    width: 90px;
    height: 90px;
    margin: 5px auto 22px;
    border: 5px solid #142033;
    border-radius: 50%;
    position: relative;
    background: linear-gradient(
        to bottom,
        #ef4444 0%,
        #ef4444 44%,
        #142033 44%,
        #142033 56%,
        #ffffff 56%,
        #ffffff 100%
    );
    animation: shake .5s 3;
}

.ball:after {
    content: "";
    position: absolute;
    left: 50%;
    top: 50%;
    width: 28px;
    height: 28px;
    transform: translate(-50%,-50%);
    background: white;
    border: 6px solid #142033;
    border-radius: 50%;
}

@keyframes shake {
    0%,100% {
        transform:rotate(0);
    }
    25% {
        transform:rotate(-18deg);
    }
    75% {
        transform:rotate(18deg);
    }
}

@media (prefers-reduced-motion:reduce) {
    .ball {
        animation:none;
    }
}

</style>
""", unsafe_allow_html=True)


# ============================================
# 10. 오른쪽 메뉴
# ============================================

main, right = st.columns(
    [3, 1],
    gap="large"
)

with right:
    st.markdown("### 🌙 Sleep Free")

    usernames = list(
        st.session_state.sf_profiles
    )

    selected_user = st.selectbox(
        "사용자 프로필",
        usernames,
        index=usernames.index(
            st.session_state.sf_user
        )
    )

    if selected_user != st.session_state.sf_user:
        st.session_state.sf_user = selected_user
        st.session_state.sf_alarm_on = False
        go("home")

    with st.expander("＋ 사용자 추가"):
        new_name = st.text_input(
            "사용자 이름",
            max_chars=30
        )

        if st.button(
            "사용자 추가",
            use_container_width=True
        ):
            name = new_name.strip()

            if not name:
                st.warning(
                    "이름을 입력해 주세요."
                )

            elif name in st.session_state.sf_profiles:
                st.warning(
                    "이미 존재하는 사용자입니다."
                )

            elif len(st.session_state.sf_profiles) >= 20:
                st.warning(
                    "사용자는 최대 20명까지 추가할 수 있어요."
                )

            else:
                st.session_state.sf_profiles[name] = (
                    new_profile()
                )

                st.session_state.sf_user = name
                st.session_state.sf_alarm_on = False

                go("home")

    st.caption(
        "현재는 실제 계정 로그인이 아닌 "
        "프로필 구분 기능입니다."
    )

    p = profile()

    st.markdown(
        f"""
        <div class="panel">
            <b>
                📦 포켓몬 {len(p["collection"])}마리
            </b>
            <p>
                🌙 수면 파트너:
                {safe(partner()["name"])}
            </p>
            <p>
                📚 수면 기록:
                {len(p["records"])}회
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    menus = [
        ("🏠 홈", "home"),
        ("🎲 포켓몬 뽑기", "draw"),
        ("📦 포켓몬 보관함", "collection"),
        ("🌙 수면 추적", "sleep"),
        ("☀️ 낮 시간", "day"),
        ("📚 수면 기록", "history"),
        ("⚙️ 설정·기기 연결", "settings")
    ]

    for label, page_name in menus:
        if st.button(
            label,
            key=f"nav_{page_name}",
            use_container_width=True
        ):
            go(page_name)

    st.divider()

    st.download_button(
        "💾 기록·포켓몬 저장",
        data=save_data(),
        file_name="sleep_free_save.json",
        mime="application/json",
        use_container_width=True
    )

    with st.expander("📂 저장 파일 불러오기"):
        uploaded = st.file_uploader(
            "저장 파일(JSON)",
            type=["json"]
        )

        st.caption(
            "불러오면 현재 프로필과 기록이 "
            "저장 파일의 내용으로 교체됩니다."
        )

        if st.button(
            "불러오기",
            use_container_width=True
        ):
            if uploaded is None:
                st.warning(
                    "파일을 선택해 주세요."
                )

            else:
                try:
                    load_data(
                        uploaded.getvalue()
                    )

                except (
                    ValueError,
                    KeyError,
                    TypeError,
                    OverflowError,
                    AttributeError
                ) as error:
                    st.error(
                        f"불러오기 실패: {error}"
                    )

    st.caption(
        "세션이 종료되면 저장하지 않은 기록이 "
        "사라질 수 있어요."
    )


# ============================================
# 11. 메인 화면
# ============================================

with main:
    p = profile()
    page = st.session_state.sf_page

    if st.session_state.sf_notice:
        st.success(
            st.session_state.sf_notice
        )

        st.session_state.sf_notice = ""

    # ----------------------------------------
    # 홈
    # ----------------------------------------

    if page == "home":
        st.markdown(
            """
            <div class="hero">
                ☁️ 🌙 Sleep Free ☁️
            </div>
            <div class="subtitle">
                포켓몬과 함께 수면 습관을 기록해 보세요.
            </div>
            """,
            unsafe_allow_html=True
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
                    {safe(partner()["name"])}
                </div>
                """,
                unsafe_allow_html=True
            )

        st.markdown(
            """
            <div class="panel">
                어두운 밤에는 수면 시작과 종료를 기록하고,
                낮에는 졸림 상태를 직접 점검할 수 있어요.
            </div>
            """,
            unsafe_allow_html=True
        )

        a, b = st.columns(2)

        with a:
            label = (
                "🌙 수면 기록으로"
                if p["sleep_start"]
                else "🌙 수면 추적 시작"
            )

            if st.button(
                label,
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

        st.caption(
            "수면 시작과 종료 시각을 기록하는 기능이며, "
            "실제 수면 단계를 자동 측정하지는 않습니다."
        )

    # ----------------------------------------
    # 포켓몬 뽑기
    # ----------------------------------------

    elif page == "draw":
        st.markdown(
            """
            <div class="hero">
                🎲 포켓몬 뽑기
            </div>
            <div class="subtitle">
                새로운 수면 파트너를 만나 보세요!
            </div>
            """,
            unsafe_allow_html=True
        )

        uid = st.session_state.sf_last_draw

        found = next(
            (
                item
                for item in p["collection"]
                if item["uid"] == uid
            ),
            None
        )

        if found:
            st.markdown(
                '<div class="ball"></div>',
                unsafe_allow_html=True
            )

            pokemon_details(
                found,
                250
            )

            st.success(
                "포켓몬이 보관함에 추가됐어요!"
            )

            if st.button(
                "🌙 이 포켓몬과 함께 자기",
                use_container_width=True
            ):
                p["partner_uid"] = found["uid"]

                st.session_state.sf_notice = (
                    f'{found["name"]}을(를) '
                    "수면 파트너로 선택했어요."
                )

                go("home")

        else:
            pokemon_image(
                partner(),
                180
            )

            st.markdown(
                """
                <div class="panel">
                    몬스터볼을 던져 포켓몬을 만나 보세요.
                    이로치 포켓몬은 5% 확률로 등장해요!
                </div>
                """,
                unsafe_allow_html=True
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

    # ----------------------------------------
    # 포켓몬 보관함
    # ----------------------------------------

    elif page == "collection":
        st.markdown(
            '<div class="hero">📦 포켓몬 보관함</div>',
            unsafe_allow_html=True
        )

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
            f"✨ 이로치 **{shiny_count}마리**"
        )

        a, b = st.columns([2, 1])

        with a:
            search = st.text_input(
                "🔎 이름 검색"
            )

        with b:
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

            start = (
                page_number - 1
            ) * page_size

            visible = records[
                start:start + page_size
            ]

            columns = st.columns(3)

            for i, pokemon in enumerate(visible):
                with columns[i % 3]:
                    with st.container(
                        border=True
                    ):
                        pokemon_image(
                            pokemon,
                            150
                        )

                        shiny_label = (
                            " ✨"
                            if pokemon["shiny"]
                            else ""
                        )

                        st.markdown(
                            f"**{safe(pokemon['name'])}"
                            f"{shiny_label}**"
                        )

                        st.caption(
                            f"No. {pokemon['number']:04d} · "
                            f"Lv.{pokemon['level']} · "
                            f"{pokemon['rarity']}"
                        )

                        if (
                            pokemon["uid"]
                            == p["partner_uid"]
                        ):
                            st.success(
                                "🌙 현재 수면 파트너"
                            )

                        else:
                            if st.button(
                                "🌙 함께 자기",
                                key=(
                                    f"partner_{pokemon['uid']}"
                                ),
                                use_container_width=True
                            ):
                                p["partner_uid"] = (
                                    pokemon["uid"]
                                )

                                go("home")

        else:
            st.info(
                "조건에 맞는 포켓몬이 없어요."
            )

        if st.button(
            "🎲 포켓몬 더 뽑기",
            use_container_width=True
        ):
            draw_pokemon()

    # ----------------------------------------
    # 수면 추적
    # ----------------------------------------

    elif page == "sleep":
        if not p["sleep_start"]:
            st.markdown(
                """
                <div class="hero">
                    🌙 수면 시작
                </div>
                <div class="subtitle">
                    포켓몬과 함께 편안한 밤을 준비하세요.
                </div>
                """,
                unsafe_allow_html=True
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
            started = parse_time(
                p["sleep_start"]
            )

            st.markdown(
                f"""
                <div class="sleep-scene">
                    <h2>🌙 수면 기록 중</h2>
                    <p>
                        함께하는 포켓몬:
                        {safe(partner()["name"])}
                    </p>
                    <p>
                        시작 시각:
                        {started.strftime("%m월 %d일 %H:%M")}
                    </p>
                    <p>
                        잠에서 깬 뒤 종료 버튼을 눌러 주세요.
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
                "같은 세션에서는 새로고침해도 "
                "수면 시작 시간이 유지됩니다."
            )

    # ----------------------------------------
    # 수면 결과
    # ----------------------------------------

    elif page == "result":
        if not p["records"]:
            st.info(
                "아직 종료한 수면 기록이 없어요."
            )

        else:
            record = p["records"][-1]

            elapsed, estimated, score = (
                sleep_summary(record)
            )

            st.markdown(
                '<div class="hero">☀️ 수면 결과</div>',
                unsafe_allow_html=True
            )

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
                "목표 시간 달성도",
                f"{score}점"
            )

            if score >= 100:
                message = (
                    "목표 수면 시간에 도달했어요!"
                )

            elif score >= 80:
                message = (
                    "목표에 가까워지고 있어요."
                )

            else:
                message = (
                    "기록된 시간이 목표보다 짧아요."
                )

            st.info(
                f'{partner()["name"]}: {message}'
            )

            st.caption(
                "점수는 목표 수면 시간 대비 달성 비율이며, "
                "객관적인 수면의 질 점수는 아닙니다."
            )

            with st.form(
                f'review_{record["uid"]}'
            ):
                maximum = max(
                    0.0,
                    elapsed * 60
                )

                awake = st.number_input(
                    "잠드는 데 걸린 시간 + "
                    "중간에 깨어 있던 시간(분)",
                    min_value=0.0,
                    max_value=maximum,
                    value=min(
                        float(
                            record["awake_minutes"]
                        ),
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
                    "일어난 뒤 느낌",
                    feelings,
                    index=(
                        feelings.index(
                            record["feeling"]
                        )
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
                    "기록 반영"
                ):
                    record["awake_minutes"] = (
                        float(awake)
                    )

                    record["feeling"] = feeling
                    record["memo"] = memo

                    st.rerun()

            st.warning(
                "정확히 언제 졸음이 발생할지는 "
                "현재 기록만으로 예측할 수 없어요. "
                "낮 시간에 실제 졸림을 점검해 주세요."
            )

            if st.button(
                "☀️ 낮 시간으로",
                use_container_width=True
            ):
                go("day")

    # ----------------------------------------
    # 낮 시간
    # ----------------------------------------

    elif page == "day":
        st.markdown(
            """
            <div class="hero">
                ☀️ 낮 시간
            </div>
            <div class="subtitle">
                현재 졸림 정도를 직접 기록해 보세요.
            </div>
            """,
            unsafe_allow_html=True
        )

        pokemon_image(
            partner(),
            180
        )

        st.toggle(
            "🔔 졸림 알람 켜기 (기본 꺼짐)",
            key="sf_alarm_on"
        )

        st.caption(
            "알람은 매일 한국 시간 기준으로 "
            "꺼짐 상태로 초기화됩니다."
        )

        with st.form("day_check"):
            sleepy = st.select_slider(
                "현재 졸림 상태",
                options=[1, 2, 3, 4, 5],
                value=2,
                format_func=lambda value: {
                    1: "1 · 또렷함",
                    2: "2 · 약간 나른함",
                    3: "3 · 졸림을 느낌",
                    4: "4 · 깨어 있으려면 노력이 필요함",
                    5: "5 · 나도 모르게 눈이 감김"
                }[value]
            )

            submitted = st.form_submit_button(
                "현재 상태 점검"
            )

        if submitted:
            p["day_checks"].append({
                "time": now().isoformat(),
                "sleepiness": sleepy
            })

            if (
                st.session_state.sf_alarm_on
                and sleepy >= 4
            ):
                st.warning(
                    "🔔 졸림 알람: 휴식이 필요해요!"
                )

        if p["day_checks"]:
            check = p["day_checks"][-1]

            st.caption(
                "마지막 점검: "
                + parse_time(
                    check["time"]
                ).strftime("%m/%d %H:%M")
            )

            if check["sleepiness"] >= 4:
                st.warning(
                    "강한 졸림을 보고했어요. "
                    "집중이 필요한 활동을 멈추고 "
                    "안전한 곳에서 쉬어 주세요."
                )

            elif check["sleepiness"] == 3:
                st.info(
                    "졸림을 느끼고 있어요. "
                    "휴식이 필요한지 살펴보세요."
                )

            else:
                st.success(
                    "마지막 점검에서는 강한 졸림을 "
                    "보고하지 않았어요."
                )

        st.caption(
            "현재 기능은 사용자가 직접 입력한 "
            "졸림 정도를 바탕으로 안내합니다. "
            "웨어러블 실시간 측정 기능은 아닙니다."
        )

    # ----------------------------------------
    # 수면 기록 보관함
    # ----------------------------------------

    elif page == "history":
        st.markdown(
            '<div class="hero">📚 수면 기록 보관함</div>',
            unsafe_allow_html=True
        )

        if not p["records"]:
            st.info(
                "수면 추적을 완료하면 기록이 쌓여요."
            )

        else:
            records = list(
                reversed(p["records"])
            )

            for record in records[:100]:
                elapsed, estimated, score = (
                    sleep_summary(record)
                )

                end = parse_time(
                    record["end"]
                )

                with st.expander(
                    f"🌙 {end:%Y.%m.%d} · "
                    f"기록 {elapsed:.1f}시간 · "
                    f"달성도 {score}점"
                ):
                    start = parse_time(
                        record["start"]
                    )

                    st.write(
                        f"시작: {start:%m/%d %H:%M}"
                    )

                    st.write(
                        f"종료: {end:%m/%d %H:%M}"
                    )

                    st.write(
                        f"추정 수면 시간: "
                        f"{estimated:.1f}시간"
                    )

                    st.write(
                        f"기상 후 느낌: "
                        f"{record['feeling']}"
                    )

                    if record["memo"]:
                        st.write(
                            record["memo"]
                        )

    # ----------------------------------------
    # 설정
    # ----------------------------------------

    elif page == "settings":
        st.markdown(
            '<div class="hero">⚙️ 설정</div>',
            unsafe_allow_html=True
        )

        with st.form("settings_form"):
            goal = st.number_input(
                "목표 수면 시간",
                min_value=1.0,
                max_value=14.0,
                value=float(
                    p["goal_hours"]
                ),
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

        st.subheader("🌙 수면 파트너")

        pokemon_image(
            partner(),
            180
        )

        st.write(
            f'현재 파트너: **{partner()["name"]}**'
        )

        if st.button(
            "📦 보관함에서 파트너 선택",
            use_container_width=True
        ):
            go("collection")

        st.divider()

        st.subheader("⌚ 웨어러블 연결")

        st.info(
            "현재 웨어러블 기기는 연결되지 않았어요. "
            "실제 블루투스 연결과 데이터 동기화는 "
            "사용하는 기기에 맞춘 별도 구현이 필요해요."
        )


# ============================================
# 12. 앱 안내
# ============================================

with st.expander("📖 Sleep Free 안내"):
    st.write(
        "Sleep Free는 수면 습관을 기록하는 앱입니다. "
        "포켓몬을 뽑아 보관하고 수면 파트너로 선택할 수 있습니다. "
        "수면 시작과 종료 버튼만으로 실제 수면 단계나 "
        "수면의 질을 측정할 수는 없습니다. "
        "점수는 목표 시간 달성도이며, "
        "낮 시간 졸림 상태는 직접 입력하는 방식입니다. "
        "현재 버전은 Streamlit 서버와 인터넷 연결이 필요하고, "
        "실제 로그인 및 웨어러블 자동 연결은 지원하지 않습니다."
    )
