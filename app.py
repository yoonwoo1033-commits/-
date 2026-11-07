
import streamlit as st
import requests
import random
import json
import uuid
import html

st.set_page_config(
    page_title="포켓몬 어드벤처",
    page_icon="⚡",
    layout="wide"
)

API = "https://pokeapi.co/api/v2"
SPRITE_BASE = (
    "https://raw.githubusercontent.com/"
    "PokeAPI/sprites/master/sprites/pokemon"
)

TYPE_KO = {
    "normal": "노말", "fire": "불꽃",
    "water": "물", "grass": "풀",
    "electric": "전기", "ice": "얼음",
    "fighting": "격투", "poison": "독",
    "ground": "땅", "flying": "비행",
    "psychic": "에스퍼", "bug": "벌레",
    "rock": "바위", "ghost": "고스트",
    "dragon": "드래곤", "dark": "악",
    "steel": "강철", "fairy": "페어리"
}

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

# -----------------------------
# API
# -----------------------------

@st.cache_data(ttl=86400)
def api_get(url):
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=86400)
def all_species():
    results = []
    url = f"{API}/pokemon-species?limit=1000"

    while url:
        data = api_get(url)
        results.extend(data["results"])
        url = data["next"]

    return results


def species_id_from_url(url):
    return int(url.rstrip("/").split("/")[-1])


def get_name(species):
    return next(
        (
            n["name"]
            for n in species["names"]
            if n["language"]["name"] == "ko"
        ),
        species["name"]
    )


def get_default_pokemon(species):
    varieties = species.get("varieties", [])

    default = next(
        (v for v in varieties if v["is_default"]),
        varieties[0] if varieties else None
    )

    if default is None:
        raise ValueError("포켓몬 형태 없음")

    return api_get(default["pokemon"]["url"])


def get_images(pokemon):
    sprites = pokemon.get("sprites") or {}
    other = sprites.get("other") or {}
    artwork = other.get("official-artwork") or {}

    number = pokemon["id"]

    return {
        "normal": [
            artwork.get("front_default"),
            sprites.get("front_default"),
            f"{SPRITE_BASE}/{number}.png"
        ],
        "shiny": [
            artwork.get("front_shiny"),
            sprites.get("front_shiny"),
            f"{SPRITE_BASE}/shiny/{number}.png"
        ]
    }


def get_evolution_chain(species):
    chain_url = species["evolution_chain"]["url"]
    data = api_get(chain_url)

    result = []

    def walk(node, parent=None):
        sid = species_id_from_url(node["species"]["url"])

        # 여러 진화 조건 중 하나를 사용
        detail = (
            node["evolution_details"][0]
            if node.get("evolution_details")
            else {}
        )

        result.append({
            "id": sid,
            "parent": parent,
            "min_level": detail.get("min_level"),
            "trigger": (
                detail.get("trigger") or {}
            ).get("name")
        })

        for child in node.get("evolves_to", []):
            walk(child, sid)

    walk(data["chain"])
    return result


def get_evolutions(species_id):
    species = api_get(
        f"{API}/pokemon-species/{species_id}"
    )
    chain = get_evolution_chain(species)

    return [
        node for node in chain
        if node["parent"] == species_id
    ]


# -----------------------------
# 포켓몬 생성
# -----------------------------

def build_pokemon(species_id, level=None, shiny=None):
    species = api_get(
        f"{API}/pokemon-species/{species_id}"
    )
    pokemon = get_default_pokemon(species)

    if level is None:
        level = random.randint(1, 10)

    if shiny is None:
        shiny = random.random() < 0.05

    images = get_images(pokemon)

    if species["is_mythical"]:
        rarity = "환상"
    elif species["is_legendary"]:
        rarity = "전설"
    elif species["capture_rate"] <= 45:
        rarity = "초희귀"
    elif species["capture_rate"] <= 100:
        rarity = "희귀"
    else:
        rarity = "일반"

    return {
        "uid": str(uuid.uuid4()),
        "species_id": species_id,
        "pokemon_id": pokemon["id"],
        "name": get_name(species),
        "level": level,
        "shiny": shiny,
        "rarity": rarity,
        "types": [
            TYPE_KO.get(
                t["type"]["name"],
                t["type"]["name"]
            )
            for t in pokemon["types"]
        ],
        "images": images,
        "ball": random.choice([
            "몬스터볼", "슈퍼볼",
            "하이퍼볼", "프레미어볼"
        ])
    }


def draw_pokemon():
    species_list = all_species()

    # 처음부터 최종 진화형이 자주 등장하지 않도록
    # 진화 계열의 시작 단계에 높은 가중치
    for _ in range(12):
        entry = random.choice(species_list)
        sid = species_id_from_url(entry["url"])

        species = api_get(
            f"{API}/pokemon-species/{sid}"
        )

        chain = get_evolution_chain(species)
        node = next(
            (x for x in chain if x["id"] == sid),
            None
        )

        if node and node["parent"] is None:
            return build_pokemon(sid)

        # 진화형도 낮은 확률로 등장
        if random.random() < 0.08:
            return build_pokemon(sid)

    # 재시도 횟수 초과 시 선택된 종 사용
    return build_pokemon(sid)


# -----------------------------
# 세션 상태
# -----------------------------

defaults = {
    "page": "home",
    "coins": 100,
    "collection": [],
    "current": None,
    "selected_uid": None,
    "battle_result": None,
    "wins": 0,
    "losses": 0,
    "draws": 0,
    "total_draws": 0,
    "animation": False
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


# -----------------------------
# 이미지 출력
# -----------------------------

def pokemon_image(p, width=220):
    candidates = (
        p["images"]["shiny"]
        if p["shiny"]
        else p["images"]["normal"]
    )

    candidates = [url for url in candidates if url]

    # 브라우저가 이미지를 불러오지 못하면
    # 자동으로 다음 이미지 주소 시도
    data = json.dumps(candidates).replace(
        "<", "\\u003c"
    )

    markup = f"""
    <div style="
        height:{width + 20}px;
        display:flex;
        align-items:center;
        justify-content:center;
    ">
        <img id="poke" style="
            max-width:95%;
            max-height:{width}px;
            object-fit:contain;
            filter:drop-shadow(0 8px 20px #0005);
        ">
    </div>

    <script>
    const urls = {data};
    const img = document.getElementById("poke");
    let index = 0;

    function nextImage() {{
        if(index >= urls.length) {{
            img.style.display = "none";
            return;
        }}
        img.src = urls[index++];
    }}

    img.onerror = nextImage;
    nextImage();
    </script>
    """

    components.html(
        markup,
        height=width + 25
    )


# -----------------------------
# 몬스터볼 애니메이션
# -----------------------------

def ball_animation(p):
    shiny = json.dumps(p["shiny"])

    markup = """
    <style>
    body {
        margin:0;
        overflow:hidden;
        background:transparent;
    }

    .stage {
        height:180px;
        display:flex;
        align-items:center;
        justify-content:center;
    }

    .ball {
        width:95px;
        height:95px;
        border-radius:50%;
        background:
            linear-gradient(
                to bottom,
                #ef4444 0%,
                #ef4444 45%,
                #111827 45%,
                #111827 55%,
                white 55%,
                white 100%
            );
        border:5px solid #111827;
        position:relative;
        animation:shake 0.5s 3;
        box-shadow:0 10px 25px #0006;
    }

    .ball:after {
        content:"";
        position:absolute;
        width:28px;
        height:28px;
        background:white;
        border:7px solid #111827;
        border-radius:50%;
        left:50%;
        top:50%;
        transform:translate(-50%,-50%);
    }

    .open {
        animation:disappear .6s forwards;
    }

    @keyframes shake {
        0%,100% {transform:rotate(0)}
        25% {transform:rotate(-22deg)}
        75% {transform:rotate(22deg)}
    }

    @keyframes disappear {
        to {
            transform:scale(3);
            opacity:0;
        }
    }

    .sparkle {
        position:absolute;
        font-size:35px;
        animation:pop 1s ease-out forwards;
    }

    @keyframes pop {
        from {
            opacity:0;
            transform:scale(0);
        }
        to {
            opacity:1;
            transform:scale(2);
        }
    }
    </style>

    <div class="stage" id="stage">
        <div class="ball" id="ball"></div>
    </div>

    <script>
    const shiny = SHINY_VALUE;
    const ball = document.getElementById("ball");

    setTimeout(() => {
        ball.classList.add("open");

        if(shiny) {
            const stage = document.getElementById("stage");
            const star = document.createElement("div");
            star.className = "sparkle";
            star.textContent = "✨🌟✨";
            stage.appendChild(star);
        }
    }, 1600);
    </script>
    """

    components.html(
        markup.replace("SHINY_VALUE", shiny),
        height=190
    )


# -----------------------------
# 게임 기능
# -----------------------------

def new_draw():
    try:
        with st.spinner("포켓몬을 찾고 있어요..."):
            p = draw_pokemon()

        st.session_state.collection.append(p)
        st.session_state.current = p
        st.session_state.total_draws += 1
        st.session_state.animation = True
        st.session_state.page = "encounter"
        st.rerun()

    except Exception:
        st.error("포켓몬을 불러오지 못했습니다.")


def level_cost(level):
    return 10 + level * 3


def level_up(uid):
    p = find_pokemon(uid)

    if p is None:
        return

    if p["level"] >= 100:
        st.warning("최대 레벨입니다.")
        return

    cost = level_cost(p["level"])

    if st.session_state.coins < cost:
        st.warning("코인이 부족합니다.")
        return

    st.session_state.coins -= cost
    p["level"] += 1
    st.rerun()


def evolve_pokemon(uid, target_id, cost):
    p = find_pokemon(uid)

    if p is None:
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

        # 기존 포켓몬의 고유 ID와 볼 유지
        evolved["uid"] = p["uid"]
        evolved["ball"] = p["ball"]

        st.session_state.coins -= cost
        p.update(evolved)
        st.success("진화 성공!")
        st.rerun()

    except Exception:
        st.error("진화 데이터를 불러오지 못했습니다.")


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


# -----------------------------
# 디자인
# -----------------------------

st.markdown("""
<style>
.stApp {
    background:linear-gradient(145deg,#06142f,#12366a);
    color:white;
}

h1,h2,h3 {
    color:white!important;
}

.block-container {
    padding-top:2rem;
}

div.stButton>button {
    background:#7dd3fc!important;
    color:#06142f!important;
    border:2px solid white!important;
    border-radius:14px!important;
    min-height:48px;
}

div.stButton>button p {
    color:#06142f!important;
    font-weight:800!important;
}

div.stButton>button:hover {
    background:white!important;
}

.hero {
    font-size:40px;
    font-weight:900;
    text-align:center;
    margin:25px 0;
    color:white;
}

.card {
    padding:20px;
    background:#ffffff12;
    border:1px solid #ffffff30;
    border-radius:20px;
    margin-bottom:20px;
}

.info {
    color:#c8ddfa;
}

.coin {
    color:#fde68a;
    font-size:24px;
    font-weight:900;
}

.shiny {
    color:#fde68a;
    font-weight:800;
}
</style>
""", unsafe_allow_html=True)


# -----------------------------
# 화면 레이아웃
# -----------------------------

main, sidebar = st.columns([3, 1], gap="large")

with sidebar:
    st.markdown("### 🎒 트레이너 정보")

    st.markdown(
        f'<div class="coin">🪙 {st.session_state.coins} 코인</div>',
        unsafe_allow_html=True
    )

    st.write(
        f"📦 보유 포켓몬: "
        f"{len(st.session_state.collection)}마리"
    )

    shiny_count = sum(
        p["shiny"] for p in st.session_state.collection
    )

    st.write(f"✨ 이로치: {shiny_count}마리")

    st.divider()

    if st.button("🏠 홈", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    if st.button("🎲 포켓몬 뽑기", use_container_width=True):
        new_draw()

    if st.button("⚔️ 배틀", use_container_width=True):
        st.session_state.page = "battle"
        st.rerun()

    if st.button("📦 보관함", use_container_width=True):
        st.session_state.page = "collection"
        st.rerun()

    if st.button("🌱 육성실", use_container_width=True):
        st.session_state.page = "training"
        st.rerun()

    st.divider()

    save_data = {
        "version": 2,
        "coins": st.session_state.coins,
        "collection": st.session_state.collection,
        "wins": st.session_state.wins,
        "losses": st.session_state.losses,
        "draws": st.session_state.draws,
        "total_draws": st.session_state.total_draws
    }

    st.download_button(
        "💾 게임 저장",
        data=json.dumps(
            save_data,
            ensure_ascii=False,
            indent=2
        ),
        file_name="pokemon_save.json",
        mime="application/json",
        use_container_width=True
    )

    with st.expander("📂 게임 불러오기"):
        uploaded = st.file_uploader(
            "저장 파일 선택",
            type=["json"]
        )

        if st.button("불러오기"):
            if uploaded:
                try:
                    if uploaded.size > 5 * 1024 * 1024:
                        raise ValueError("파일 크기 초과")

                    data = json.loads(uploaded.getvalue())

                    if data["version"] != 2:
                        raise ValueError("버전 불일치")

                    coins = data["coins"]
                    collection = data["collection"]

                    if (
                        type(coins) is not int
                        or not 0 <= coins <= 100000000
                        or not isinstance(collection, list)
                        or len(collection) > 10000
                    ):
                        raise ValueError("저장 데이터 오류")

                    validated = []

                    for p in collection:
                        if not isinstance(p, dict):
                            raise ValueError("포켓몬 데이터 오류")

                        sid = p["species_id"]
                        level = p["level"]
                        shiny = p["shiny"]

                        if (
                            type(sid) is not int
                            or not 1 <= sid <= 100000
                            or type(level) is not int
                            or not 1 <= level <= 100
                            or type(shiny) is not bool
                        ):
                            raise ValueError("포켓몬 정보 오류")

                        # 외부 파일의 HTML이나 이미지 주소를
                        # 그대로 신뢰하지 않고 API로 다시 구성
                        rebuilt = build_pokemon(
                            sid, level, shiny
                        )

                        rebuilt["uid"] = str(uuid.uuid4())
                        validated.append(rebuilt)

                    st.session_state.coins = coins
                    st.session_state.collection = validated

                    for key in ["wins", "losses", "draws", "total_draws"]:
                        value = data.get(key, 0)
                        if type(value) is not int or not 0 <= value <= 10000000:
                            raise ValueError("전적 정보 오류")
                        st.session_state[key] = value

                    st.session_state.page = "collection"
                    st.rerun()

                except Exception:
                    st.error(
                        "저장 파일을 확인해 주세요. "
                        "이전 버전의 저장 파일은 지원하지 않습니다."
                    )


# -----------------------------
# 홈
# -----------------------------

with main:

    if st.session_state.page == "home":
        st.markdown(
            '<div class="hero">⚡ 포켓몬 어드벤처</div>',
            unsafe_allow_html=True
        )

        st.markdown(
            """
            <div class="card">
                <h3>나만의 포켓몬을 키워 보세요!</h3>
                <p class="info">
                    포켓몬을 뽑고 배틀로 코인을 모으세요.
                    코인으로 레벨업하고 진화시킬 수 있습니다.
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
                st.session_state.page = "training"
                st.rerun()

        with b:
            if st.button(
                "⚔️ 가위바위보 배틀",
                use_container_width=True
            ):
                st.session_state.page = "battle"
                st.rerun()

            if st.button(
                "📦 내 포켓몬 보기",
                use_container_width=True
            ):
                st.session_state.page = "collection"
                st.rerun()

    # -------------------------
    # 포켓몬 등장
    # -------------------------

    elif st.session_state.page == "encounter":
        p = st.session_state.current

        st.markdown(
            '<div class="hero">야생의 포켓몬이 나타났다!</div>',
            unsafe_allow_html=True
        )

        if st.session_state.animation:
            ball_animation(p)
            st.session_state.animation = False

        pokemon_image(p, 270)

        st.markdown(
            f"## {html.escape(p['name'])}"
        )

        st.write(
            f"Lv. {p['level']} · {p['rarity']}"
        )

        if p["shiny"]:
            st.markdown(
                '<div class="shiny">✨ 이로치 포켓몬!</div>',
                unsafe_allow_html=True
            )

        st.write("타입: " + " / ".join(p["types"]))
        st.write("몬스터볼: " + p["ball"])

        st.success("보관함에 자동 저장되었습니다!")

        a, b = st.columns(2)

        with a:
            if st.button("🎲 다시 뽑기", use_container_width=True):
                new_draw()

        with b:
            if st.button("🌱 육성하기", use_container_width=True):
                st.session_state.selected_uid = p["uid"]
                st.session_state.page = "training"
                st.rerun()

    # -------------------------
    # 배틀
    # -------------------------

    elif st.session_state.page == "battle":
        st.markdown(
            '<div class="hero">⚔️ 가위바위보 배틀</div>',
            unsafe_allow_html=True
        )

        st.write("승리하면 30코인, 무승부면 5코인을 얻습니다.")

        a, b, c = st.columns(3)

        a.metric("승리", st.session_state.wins)
        b.metric("무승부", st.session_state.draws)
        c.metric("패배", st.session_state.losses)

        st.markdown("### 무엇을 낼까요?")

        columns = st.columns(3)

        for col, choice in zip(columns, RPS):
            with col:
                if st.button(
                    f"{RPS[choice]} {choice}",
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
                st.warning("💨 패배! 다음에 다시 도전하세요.")

    # -------------------------
    # 보관함
    # -------------------------

    elif st.session_state.page == "collection":
        st.markdown(
            '<div class="hero">📦 내 포켓몬 보관함</div>',
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
                ["최근 획득순", "레벨 높은 순", "도감 번호순"]
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
                filtered.sort(key=lambda p: p["species_id"])

            st.write(f"총 {len(filtered)}마리")

            page_size = 9
            total_pages = max(
                1, (len(filtered) + page_size - 1) // page_size
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
                    pokemon_image(p, 160)

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
                        st.session_state.page = "training"
                        st.rerun()

    # -------------------------
    # 육성실
    # -------------------------

    elif st.session_state.page == "training":
        st.markdown(
            '<div class="hero">🌱 포켓몬 육성실</div>',
            unsafe_allow_html=True
        )

        collection = st.session_state.collection

        if not collection:
            st.info("먼저 포켓몬을 뽑아 주세요.")

        else:
            by_uid = {p["uid"]: p for p in collection}
            ids = list(by_uid)

            if st.session_state.selected_uid not in by_uid:
                st.session_state.selected_uid = ids[0]

            def label(uid):
                p = by_uid[uid]
                shiny = "✨ " if p["shiny"] else ""
                return f"{shiny}{p['name']} · Lv. {p['level']}"

            selected = st.selectbox(
                "육성할 포켓몬",
                options=ids,
                format_func=label,
                key="selected_uid"
            )

            p = by_uid[selected]

            pokemon_image(p, 260)

            st.markdown(f"## {html.escape(p['name'])}")

            st.write(
                f"현재 레벨: **Lv. {p['level']}**"
            )

            st.write(
                f"희귀도: {p['rarity']}"
            )

            if p["shiny"]:
                st.write("✨ 이로치 포켓몬")

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
                    f"레벨업하기 ({cost}코인)",
                    use_container_width=True
                ):
                    level_up(selected)

            else:
                st.success("최대 레벨에 도달했습니다!")

            st.divider()

            st.subheader("✨ 진화")

            try:
                evolutions = get_evolutions(p["species_id"])

                if not evolutions:
                    st.info("현재 진화할 수 있는 다음 단계가 없습니다.")

                for evo in evolutions:
                    target_species = api_get(
                        f"{API}/pokemon-species/{evo['id']}"
                    )

                    target_name = get_name(target_species)

                    # 단순화된 자체 진화 규칙
                    required_level = evo["min_level"] or 20
                    required_level = min(required_level, 100)
                    evolution_cost = 100

                    st.write(
                        f"**{p['name']} → {target_name}**"
                    )

                    st.write(
                        f"필요 레벨: Lv. {required_level}"
                    )

                    st.write(
                        f"필요 코인: 🪙 {evolution_cost}"
                    )

                    can_evolve = (
                        p["level"] >= required_level
                        and st.session_state.coins >= evolution_cost
                    )

                    if st.button(
                        f"✨ {target_name}(으)로 진화",
                        key=f"evo_{selected}_{evo['id']}",
                        disabled=not can_evolve,
                        use_container_width=True
                    ):
                        evolve_pokemon(
                            selected,
                            evo["id"],
                            evolution_cost
                        )

                    if p["level"] < required_level:
                        st.caption("레벨이 부족합니다.")

            except Exception:
                st.warning(
                    "진화 정보를 불러오지 못했습니다. "
                    "잠시 후 다시 시도해 주세요."
                )


with st.expander("📖 게임 규칙"):
    st.write(
        "처음 포켓몬을 획득하면 Lv.1~10으로 등장합니다. "
        "가위바위보 승리 시 30코인, 무승부 시 5코인을 얻습니다. "
        "코인으로 레벨업과 진화를 진행할 수 있습니다. "
        "진화 시 레벨과 이로치 여부는 유지됩니다. "
        "진화 조건은 게임 플레이를 위해 단순화한 자체 규칙입니다. "
        "포켓몬 데이터는 PokéAPI에서 불러옵니다. "
        "저장 파일은 이 버전의 JSON 형식을 사용합니다."
    )
