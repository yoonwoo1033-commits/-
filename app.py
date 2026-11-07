
import streamlit as st
import requests
import random
import json
import uuid
import html
from urllib.parse import urlparse

# =====================================
# 기본 설정
# =====================================

st.set_page_config(
    page_title="포켓몬 어드벤처",
    page_icon="⚡",
    layout="wide"
)

API = "https://pokeapi.co/api/v2"
SPRITES = (
    "https://raw.githubusercontent.com/"
    "PokeAPI/sprites/master/sprites/pokemon"
)

SHINY_RATE = 0.05

TYPES = {
    "normal": "노말",
    "fire": "불꽃",
    "water": "물",
    "electric": "전기",
    "grass": "풀",
    "ice": "얼음",
    "fighting": "격투",
    "poison": "독",
    "ground": "땅",
    "flying": "비행",
    "psychic": "에스퍼",
    "bug": "벌레",
    "rock": "바위",
    "ghost": "고스트",
    "dragon": "드래곤",
    "dark": "악",
    "steel": "강철",
    "fairy": "페어리"
}

BALLS = [
    ("몬스터볼", 50),
    ("슈퍼볼", 25),
    ("하이퍼볼", 15),
    ("프레미어볼", 8),
    ("마스터볼", 2)
]

RPS = {
    "가위": "✌️",
    "바위": "✊",
    "보": "🖐️"
}

BEATS = {
    "가위": "보",
    "바위": "가위",
    "보": "바위"
}

# 처음에는 기본 단계 포켓몬이 주로 등장
# 대표적인 기본 단계 포켓몬 도감 번호
STARTER_POOL = [
    1, 4, 7, 10, 13, 16, 19, 21, 23,
    25, 27, 29, 32, 35, 37, 39, 41,
    43, 46, 48, 50, 52, 54, 56, 58,
    60, 63, 66, 69, 72, 74, 77, 79,
    81, 84, 86, 88, 90, 92, 95, 96,
    98, 100, 102, 104, 109, 111, 116,
    118, 120, 129, 133, 137, 147,
    152, 155, 158, 161, 163, 165, 167,
    170, 172, 175, 177, 179, 183, 187,
    190, 191, 193, 194, 198, 200, 204,
    209, 216, 218, 220, 223, 228, 231,
    236, 238, 239, 240, 246, 252, 255,
    258, 261, 263, 265, 270, 273, 276,
    278, 280, 283, 285, 287, 290, 293,
    296, 298, 300, 304, 307, 309, 311,
    312, 315, 316, 318, 320, 322, 325,
    328, 331, 333, 339, 341, 343, 345,
    347, 349, 353, 355, 360, 361, 363,
    366, 371, 374, 387, 390, 393, 396,
    399, 401, 403, 406, 408, 410, 412,
    415, 417, 418, 420, 422, 425, 427,
    431, 433, 434, 436, 438, 439, 440,
    443, 446, 447, 449, 451, 453, 456,
    458, 459, 495, 498, 501, 504, 506,
    509, 511, 513, 515, 517, 519, 522,
    524, 527, 529, 531, 532, 535, 540,
    543, 546, 548, 550, 551, 554, 557,
    559, 562, 564, 566, 568, 570, 572,
    574, 577, 580, 582, 585, 588, 590,
    592, 595, 597, 599, 602, 605, 607,
    610, 613, 616, 619, 622, 624, 627,
    629, 633, 636, 650, 653, 656, 659,
    661, 664, 667, 669, 672, 674, 677,
    679, 682, 684, 686, 688, 690, 692,
    694, 696, 698, 704, 708, 710, 712,
    714, 722, 725, 728, 731, 734, 736,
    739, 742, 744, 746, 747, 749, 751,
    753, 755, 757, 759, 761, 767, 769,
    782, 810, 813, 816, 819, 821, 824,
    827, 829, 831, 833, 835, 837, 840,
    843, 846, 848, 850, 852, 854, 856,
    859, 868, 872, 878, 885, 906, 909,
    912, 915, 917, 919, 921, 924, 926,
    928, 932, 935, 938, 940, 942, 944,
    946, 948, 951, 953, 955, 957, 960,
    963, 965, 969, 971, 974, 996
]

# =====================================
# API
# =====================================

@st.cache_data(ttl=86400, show_spinner=False)
def api_get(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=86400, show_spinner=False)
def species_list():
    result = []
    url = f"{API}/pokemon-species?limit=1000"

    while url:
        data = api_get(url)
        result.extend(data["results"])
        url = data["next"]

    return result


def get_korean_name(species):
    return next(
        (
            x["name"]
            for x in species["names"]
            if x["language"]["name"] == "ko"
        ),
        species["name"]
    )


def get_default_form(species):
    varieties = species.get("varieties", [])

    if not varieties:
        raise ValueError("포켓몬 형태가 없습니다.")

    default = next(
        (x for x in varieties if x["is_default"]),
        varieties[0]
    )

    return api_get(default["pokemon"]["url"])


def get_sprite_urls(pokemon, shiny):
    sprites = pokemon.get("sprites") or {}
    other = sprites.get("other") or {}
    artwork = other.get("official-artwork") or {}

    number = pokemon["id"]

    if shiny:
        urls = [
            artwork.get("front_shiny"),
            sprites.get("front_shiny"),
            f"{SPRITES}/shiny/{number}.png"
        ]
    else:
        urls = [
            artwork.get("front_default"),
            sprites.get("front_default"),
            f"{SPRITES}/{number}.png"
        ]

    # 이로치 이미지가 없는 경우 일반 이미지도 후보로 추가
    if shiny:
        urls.extend([
            artwork.get("front_default"),
            sprites.get("front_default")
        ])

    return list(dict.fromkeys(x for x in urls if x))


def get_rarity(species):
    if species.get("is_mythical"):
        return "환상"

    if species.get("is_legendary"):
        return "전설"

    rate = species.get("capture_rate", 255)

    if rate <= 45:
        return "초희귀"
    if rate <= 100:
        return "희귀"

    return "일반"


def build_pokemon(species_id, level=None, shiny=None):
    species = api_get(
        f"{API}/pokemon-species/{species_id}"
    )

    pokemon = get_default_form(species)

    if level is None:
        level = random.randint(1, 10)

    if shiny is None:
        shiny = random.random() < SHINY_RATE

    ball = random.choices(
        [x[0] for x in BALLS],
        weights=[x[1] for x in BALLS],
        k=1
    )[0]

    return {
        "uid": str(uuid.uuid4()),
        "species_id": species_id,
        "pokemon_id": pokemon["id"],
        "name": get_korean_name(species),
        "level": level,
        "shiny": shiny,
        "rarity": get_rarity(species),
        "types": [
            TYPES.get(
                t["type"]["name"],
                t["type"]["name"]
            )
            for t in pokemon["types"]
        ],
        "images": get_sprite_urls(pokemon, shiny),
        "ball": ball
    }


def draw_pokemon():
    # 기본 단계 90%, 전체 종 10%
    if random.random() < 0.9:
        sid = random.choice(STARTER_POOL)
    else:
        entry = random.choice(species_list())
        sid = int(entry["url"].rstrip("/").split("/")[-1])

    return build_pokemon(sid)


# =====================================
# 상태 관리
# =====================================

defaults = {
    "page": "home",
    "coins": 100,
    "collection": [],
    "current_uid": None,
    "selected_uid": None,
    "battle_result": None,
    "wins": 0,
    "losses": 0,
    "draws": 0,
    "total_draws": 0
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


def find_pokemon(uid):
    return next(
        (
            p for p in st.session_state.collection
            if p["uid"] == uid
        ),
        None
    )


def go(page):
    st.session_state.page = page
    st.rerun()


# =====================================
# 이미지 표시
# =====================================

@st.cache_data(ttl=86400, show_spinner=False)
def working_image(urls):
    # 이미지가 실제로 열리는지 검사
    for url in urls:
        try:
            response = requests.get(url, timeout=8)

            if (
                response.ok
                and response.headers.get(
                    "content-type", ""
                ).startswith("image/")
            ):
                return response.content

        except requests.RequestException:
            continue

    return None


def show_pokemon_image(p, width=220):
    urls = p.get("images", [])

    if isinstance(urls, dict):
        urls = (
            urls.get("shiny", [])
            if p.get("shiny")
            else urls.get("normal", [])
        )

    try:
        data = working_image(tuple(urls))

        if data:
            st.image(data, width=width)
        else:
            st.markdown(
                f"""
                <div class="missing-image">
                    ⚡<br>{html.escape(p['name'])}
                </div>
                """,
                unsafe_allow_html=True
            )

    except Exception:
        st.info("포켓몬 이미지를 불러오지 못했습니다.")


# =====================================
# 게임 기능
# =====================================

def new_draw():
    try:
        with st.spinner("야생 포켓몬을 찾는 중..."):
            p = draw_pokemon()

        st.session_state.collection.append(p)
        st.session_state.current_uid = p["uid"]
        st.session_state.total_draws += 1
        go("encounter")

    except (requests.RequestException, ValueError, KeyError):
        st.error(
            "포켓몬 데이터를 불러오지 못했어요. "
            "잠시 후 다시 시도해 주세요."
        )


def level_cost(level):
    return 10 + level * 3


def level_up(uid):
    p = find_pokemon(uid)

    if not p:
        return

    if p["level"] >= 100:
        st.warning("이미 최대 레벨입니다.")
        return

    cost = level_cost(p["level"])

    if st.session_state.coins < cost:
        st.warning("코인이 부족합니다.")
        return

    st.session_state.coins -= cost
    p["level"] += 1
    st.rerun()


def get_evolution_options(species_id):
    species = api_get(
        f"{API}/pokemon-species/{species_id}"
    )

    chain_url = species["evolution_chain"]["url"]
    chain_data = api_get(chain_url)

    options = []

    def walk(node):
        sid = int(
            node["species"]["url"]
            .rstrip("/")
            .split("/")[-1]
        )

        if sid == species_id:
            for child in node.get("evolves_to", []):
                target_id = int(
                    child["species"]["url"]
                    .rstrip("/")
                    .split("/")[-1]
                )

                details = child.get("evolution_details") or []
                detail = details[0] if details else {}

                options.append({
                    "id": target_id,
                    "level": detail.get("min_level") or 20
                })

        for child in node.get("evolves_to", []):
            walk(child)

    walk(chain_data["chain"])
    return options


def evolve(uid, target_id, cost):
    p = find_pokemon(uid)

    if not p:
        return

    if st.session_state.coins < cost:
        st.warning("코인이 부족합니다.")
        return

    try:
        with st.spinner("진화하는 중..."):
            evolved = build_pokemon(
                target_id,
                level=p["level"],
                shiny=p["shiny"]
            )

        evolved["uid"] = p["uid"]
        evolved["ball"] = p["ball"]

        st.session_state.coins -= cost
        p.update(evolved)
        st.rerun()

    except (requests.RequestException, ValueError, KeyError):
        st.error("진화 정보를 불러오지 못했습니다.")


def play_rps(choice):
    opponent = random.choice(list(RPS))

    if choice == opponent:
        result = "draw"
        reward = 5
        st.session_state.draws += 1

    elif BEATS[choice] == opponent:
        result = "win"
        reward = 30
        st.session_state.wins += 1

    else:
        result = "lose"
        reward = 0
        st.session_state.losses += 1

    st.session_state.coins += reward

    st.session_state.battle_result = {
        "mine": choice,
        "opponent": opponent,
        "result": result,
        "reward": reward
    }


# =====================================
# 저장 파일
# =====================================

def save_game():
    return {
        "version": 3,
        "coins": st.session_state.coins,
        "collection": st.session_state.collection,
        "wins": st.session_state.wins,
        "losses": st.session_state.losses,
        "draws": st.session_state.draws,
        "total_draws": st.session_state.total_draws
    }


def load_game(raw):
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("파일이 너무 큽니다.")

    data = json.loads(raw)

    if data.get("version") != 3:
        raise ValueError("지원하지 않는 저장 파일입니다.")

    coins = data["coins"]
    records = data["collection"]

    if type(coins) is not int or not 0 <= coins <= 100000000:
        raise ValueError("코인 정보 오류")

    if not isinstance(records, list) or len(records) > 1000:
        raise ValueError("보관함 정보 오류")

    validated = []

    for p in records:
        if not isinstance(p, dict):
            raise ValueError("포켓몬 기록 오류")

        sid = p["species_id"]
        level = p["level"]
        shiny = p["shiny"]

        if type(sid) is not int or not 1 <= sid <= 100000:
            raise ValueError("도감 번호 오류")

        if type(level) is not int or not 1 <= level <= 100:
            raise ValueError("레벨 오류")

        if type(shiny) is not bool:
            raise ValueError("이로치 정보 오류")

        rebuilt = build_pokemon(sid, level, shiny)

        uid = p.get("uid")
        if isinstance(uid, str) and len(uid) <= 100:
            rebuilt["uid"] = uid

        if p.get("ball") in [x[0] for x in BALLS]:
            rebuilt["ball"] = p["ball"]

        validated.append(rebuilt)

    stats = {}

    for key in ["wins", "losses", "draws", "total_draws"]:
        value = data.get(key, 0)

        if type(value) is not int or not 0 <= value <= 10000000:
            raise ValueError("전적 정보 오류")

        stats[key] = value

    # 모든 검증이 끝난 뒤에만 저장 데이터 반영
    st.session_state.coins = coins
    st.session_state.collection = validated

    for key, value in stats.items():
        st.session_state[key] = value

    st.session_state.current_uid = None
    st.session_state.selected_uid = None
    st.session_state.battle_result = None
    go("collection")


# =====================================
# CSS
# =====================================

st.markdown("""
<style>
.stApp {
    background:linear-gradient(
        145deg,#06142f,#12366a
    );
    color:white;
}

header[data-testid="stHeader"] {
    background:transparent;
}

h1,h2,h3 {
    color:white!important;
}

.block-container {
    padding-top:2rem;
}

div.stButton>button,
div.stDownloadButton>button {
    background:#7dd3fc!important;
    color:#06142f!important;
    border:2px solid #e0f2fe!important;
    border-radius:14px!important;
    min-height:48px;
}

div.stButton>button p,
div.stDownloadButton>button p {
    color:#06142f!important;
    font-weight:800!important;
}

div.stButton>button:hover {
    background:white!important;
}

.hero {
    font-size:clamp(28px,5vw,42px);
    font-weight:900;
    text-align:center;
    margin:20px 0;
    color:white;
}

.subtitle {
    color:#c8ddfa;
    text-align:center;
    margin-bottom:28px;
}

.game-card {
    background:#ffffff12;
    border:1px solid #ffffff30;
    border-radius:20px;
    padding:22px;
    margin:12px 0 22px;
}

.coin {
    color:#fde68a;
    font-size:26px;
    font-weight:900;
}

.missing-image {
    min-height:180px;
    display:flex;
    align-items:center;
    justify-content:center;
    flex-direction:column;
    color:#c8ddfa;
    font-weight:700;
    background:#ffffff0b;
    border-radius:18px;
}

.pokemon-title {
    font-size:30px;
    font-weight:900;
    color:white;
}

.shiny-text {
    color:#fde68a;
    font-weight:900;
}

.ball {
    width:100px;
    height:100px;
    margin:18px auto;
    border-radius:50%;
    border:6px solid #182237;
    background:linear-gradient(
        to bottom,
        #ef4444 0%,
        #ef4444 44%,
        #182237 44%,
        #182237 56%,
        white 56%,
        white 100%
    );
    position:relative;
    animation:ballshake .55s ease-in-out 3;
}

.ball:after {
    content:"";
    position:absolute;
    width:30px;
    height:30px;
    background:white;
    border:7px solid #182237;
    border-radius:50%;
    left:50%;
    top:50%;
    transform:translate(-50%,-50%);
}

@keyframes ballshake {
    0%,100% {transform:rotate(0deg)}
    25% {transform:rotate(-18deg)}
    75% {transform:rotate(18deg)}
}

@media(prefers-reduced-motion:reduce) {
    .ball {animation:none}
}
</style>
""", unsafe_allow_html=True)


# =====================================
# 공통 포켓몬 정보
# =====================================

def show_pokemon_details(p, width=240):
    show_pokemon_image(p, width)

    st.markdown(
        f'<div class="pokemon-title">'
        f'{html.escape(p["name"])}</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"**Lv. {p['level']}** · {p['rarity']}"
    )

    st.write("타입: " + " / ".join(p["types"]))

    if p["shiny"]:
        st.markdown(
            '<div class="shiny-text">'
            '✨ 이로치 포켓몬 ✨</div>',
            unsafe_allow_html=True
        )

    st.caption(f"획득한 볼: {p['ball']}")


# =====================================
# 오른쪽 메뉴
# =====================================

main, sidebar = st.columns([3, 1], gap="large")

with sidebar:
    st.subheader("🎒 트레이너")

    st.markdown(
        f'<div class="coin">'
        f'🪙 {st.session_state.coins:,}</div>',
        unsafe_allow_html=True
    )

    collection = st.session_state.collection

    st.write(f"📦 보유: {len(collection)}마리")
    st.write(
        f"✨ 이로치: "
        f"{sum(p['shiny'] for p in collection)}마리"
    )

    st.divider()

    if st.button("🏠 홈", use_container_width=True):
        go("home")

    if st.button("🎲 포켓몬 뽑기", use_container_width=True):
        new_draw()

    if st.button("⚔️ 배틀", use_container_width=True):
        go("battle")

    if st.button("📦 보관함", use_container_width=True):
        go("collection")

    if st.button("🌱 육성실", use_container_width=True):
        go("training")

    st.divider()

    st.download_button(
        "💾 게임 저장",
        data=json.dumps(
            save_game(),
            ensure_ascii=False,
            indent=2
        ),
        file_name="pokemon_save_v3.json",
        mime="application/json",
        use_container_width=True
    )

    with st.expander("📂 게임 불러오기"):
        uploaded = st.file_uploader(
            "저장 파일 선택",
            type=["json"]
        )

        if st.button("불러오기", use_container_width=True):
            if uploaded is None:
                st.warning("파일을 선택해 주세요.")
            else:
                try:
                    with st.spinner("저장 기록 복원 중..."):
                        load_game(uploaded.getvalue())

                except (
                    ValueError,
                    KeyError,
                    TypeError,
                    requests.RequestException
                ) as e:
                    st.error(f"불러오기 실패: {e}")

    st.caption(
        "게임 기록은 현재 접속 세션에 보관됩니다. "
        "장기 보관하려면 저장 파일을 다운로드하세요."
    )


# =====================================
# 메인 화면
# =====================================

with main:

    # 홈
    if st.session_state.page == "home":
        st.markdown(
            '<div class="hero">⚡ 포켓몬 어드벤처</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            '<div class="subtitle">'
            '포켓몬을 수집하고 배틀로 성장시키세요!'
            '</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="game-card">
                <h3>나만의 포켓몬 육성 게임</h3>
                <p>
                    처음에는 낮은 레벨의 포켓몬을 얻습니다.
                    배틀로 코인을 모으고 레벨업과 진화에
                    사용해 보세요.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        a, b = st.columns(2)

        with a:
            if st.button(
                "🎲 새로운 포켓몬 만나기",
                use_container_width=True
            ):
                new_draw()

            if st.button(
                "🌱 포켓몬 육성하기",
                use_container_width=True
            ):
                go("training")

        with b:
            if st.button(
                "⚔️ 가위바위보 배틀",
                use_container_width=True
            ):
                go("battle")

            if st.button(
                "📦 내 포켓몬 보관함",
                use_container_width=True
            ):
                go("collection")

    # 포켓몬 뽑기 결과
    elif st.session_state.page == "encounter":
        st.markdown(
            '<div class="hero">'
            '야생의 포켓몬이 나타났다!</div>',
            unsafe_allow_html=True
        )

        p = find_pokemon(st.session_state.current_uid)

        if p is None:
            st.warning("포켓몬 기록을 찾지 못했습니다.")

        else:
            st.markdown(
                '<div class="ball"></div>',
                unsafe_allow_html=True
            )

            show_pokemon_details(p, 270)

            st.success("보관함에 자동 저장됐어요!")

            a, b = st.columns(2)

            with a:
                if st.button(
                    "🎲 다시 뽑기",
                    use_container_width=True
                ):
                    new_draw()

            with b:
                if st.button(
                    "🌱 육성하기",
                    use_container_width=True
                ):
                    st.session_state.selected_uid = p["uid"]
                    go("training")

    # 배틀
    elif st.session_state.page == "battle":
        st.markdown(
            '<div class="hero">'
            '⚔️ 가위바위보 배틀</div>',
            unsafe_allow_html=True
        )

        st.write(
            "승리하면 30코인, "
            "무승부면 5코인을 획득합니다."
        )

        a, b, c = st.columns(3)

        a.metric("🏆 승리", st.session_state.wins)
        b.metric("🤝 무승부", st.session_state.draws)
        c.metric("💨 패배", st.session_state.losses)

        st.markdown("### 무엇을 낼까요?")

        columns = st.columns(3)

        for col, choice in zip(columns, RPS):
            with col:
                if st.button(
                    f"{RPS[choice]} {choice}",
                    key=f"rps_{choice}",
                    use_container_width=True
                ):
                    play_rps(choice)
                    st.rerun()

        result = st.session_state.battle_result

        if result:
            st.divider()

            a, b = st.columns(2)

            with a:
                st.subheader("나")
                st.markdown(
                    f"## {RPS[result['mine']]} "
                    f"{result['mine']}"
                )

            with b:
                st.subheader("상대")
                st.markdown(
                    f"## {RPS[result['opponent']]} "
                    f"{result['opponent']}"
                )

            if result["result"] == "win":
                st.success("🏆 승리! +30코인")

            elif result["result"] == "draw":
                st.info("🤝 무승부! +5코인")

            else:
                st.warning("💨 패배! 다시 도전해 보세요.")

            if st.button(
                "🌱 코인으로 육성하기",
                use_container_width=True
            ):
                go("training")

    # 보관함
    elif st.session_state.page == "collection":
        st.markdown(
            '<div class="hero">'
            '📦 내 포켓몬 보관함</div>',
            unsafe_allow_html=True
        )

        collection = st.session_state.collection

        if not collection:
            st.info("아직 포켓몬이 없습니다.")

        else:
            search = st.text_input("🔎 포켓몬 검색")
            only_shiny = st.checkbox("✨ 이로치만 보기")

            order = st.selectbox(
                "정렬",
                [
                    "최근 획득순",
                    "레벨 높은 순",
                    "도감 번호순"
                ]
            )

            filtered = [
                p for p in collection
                if search in p["name"]
                and (not only_shiny or p["shiny"])
            ]

            if order == "최근 획득순":
                filtered.reverse()

            elif order == "레벨 높은 순":
                filtered.sort(
                    key=lambda p: p["level"],
                    reverse=True
                )

            else:
                filtered.sort(
                    key=lambda p: p["species_id"]
                )

            st.write(f"총 {len(filtered)}마리")

            page_size = 9
            total_pages = max(
                1,
                (len(filtered) + page_size - 1) // page_size
            )

            page = st.selectbox(
                "페이지",
                range(1, total_pages + 1)
            )

            start = (page - 1) * page_size
            visible = filtered[start:start + page_size]

            cols = st.columns(3)

            for i, p in enumerate(visible):
                with cols[i % 3]:
                    show_pokemon_image(p, 160)

                    st.markdown(
                        f"**{html.escape(p['name'])}**"
                    )

                    st.write(
                        f"Lv. {p['level']} · {p['rarity']}"
                    )

                    if p["shiny"]:
                        st.write("✨ 이로치")

                    if st.button(
                        "🌱 육성",
                        key=f"train_{p['uid']}",
                        use_container_width=True
                    ):
                        st.session_state.selected_uid = p["uid"]
                        go("training")

    # 육성실
    elif st.session_state.page == "training":
        st.markdown(
            '<div class="hero">'
            '🌱 포켓몬 육성실</div>',
            unsafe_allow_html=True
        )

        collection = st.session_state.collection

        if not collection:
            st.info("먼저 포켓몬을 뽑아 주세요.")

        else:
            by_uid = {
                p["uid"]: p for p in collection
            }

            ids = list(by_uid)

            if st.session_state.selected_uid not in by_uid:
                st.session_state.selected_uid = ids[0]

            def label(uid):
                p = by_uid[uid]
                prefix = "✨ " if p["shiny"] else ""
                return (
                    f"{prefix}{p['name']} "
                    f"· Lv. {p['level']}"
                )

            selected = st.selectbox(
                "육성할 포켓몬",
                options=ids,
                format_func=label,
                key="selected_uid"
            )

            p = by_uid[selected]

            show_pokemon_details(p, 260)

            st.divider()

            st.subheader("⬆️ 레벨업")

            if p["level"] < 100:
                cost = level_cost(p["level"])

                st.write(
                    f"Lv. {p['level']} → "
                    f"Lv. {p['level'] + 1}"
                )

                st.write(f"필요 코인: 🪙 {cost}")

                if st.button(
                    f"레벨업 ({cost}코인)",
                    use_container_width=True
                ):
                    level_up(selected)

            else:
                st.success("최대 레벨입니다!")

            st.divider()

            st.subheader("✨ 진화")

            try:
                options = get_evolution_options(
                    p["species_id"]
                )

                if not options:
                    st.info("더 이상 진화할 수 없습니다.")

                for option in options:
                    target = api_get(
                        f"{API}/pokemon-species/"
                        f"{option['id']}"
                    )

                    name = get_korean_name(target)
                    required = min(
                        option["level"], 100
                    )
                    cost = 100

                    st.markdown(
                        f"### {p['name']} → {name}"
                    )

                    st.write(
                        f"필요 레벨: Lv. {required}"
                    )

                    st.write(
                        f"필요 코인: 🪙 {cost}"
                    )

                    available = (
                        p["level"] >= required
                        and st.session_state.coins >= cost
                    )

                    if st.button(
                        f"✨ {name}(으)로 진화",
                        key=f"evo_{selected}_{option['id']}",
                        disabled=not available,
                        use_container_width=True
                    ):
                        evolve(
                            selected,
                            option["id"],
                            cost
                        )

                    if p["level"] < required:
                        st.caption(
                            "아직 진화에 필요한 레벨이 아닙니다."
                        )

            except (requests.RequestException, ValueError, KeyError):
                st.warning(
                    "진화 정보를 불러오지 못했습니다. "
                    "잠시 후 다시 시도해 주세요."
                )


with st.expander("📖 게임 규칙"):
    st.write(
        "포켓몬은 처음 Lv.1~10으로 등장합니다. "
        "기본 단계 포켓몬이 주로 등장하며, "
        "일부 진화형도 등장할 수 있습니다. "
        "이로치 확률은 5%입니다. "
        "가위바위보 승리 시 30코인, "
        "무승부 시 5코인을 얻습니다. "
        "코인으로 레벨업과 진화를 할 수 있습니다. "
        "진화 시 레벨과 이로치 여부가 유지됩니다. "
        "진화 조건은 게임을 위해 단순화한 자체 규칙입니다. "
        "코인은 실제 금전적 가치가 없는 게임 재화입니다."
    )
