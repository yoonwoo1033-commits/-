
import streamlit as st
import streamlit.components.v1 as components
import requests
import random

st.set_page_config(
    page_title="랜덤 포켓몬",
    page_icon="⚡",
    layout="centered"
)

# 전체 포켓몬 목록 불러오기
@st.cache_data(ttl=86400)
def get_pokemon_list():
    url = "https://pokeapi.co/api/v2/pokemon-species?limit=2000"
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    return response.json()["results"]


@st.cache_data(ttl=86400)
def get_pokemon(species_url):
    species = requests.get(
        species_url, timeout=15
    ).json()

    number = species["id"]

    # 한국어 이름 찾기
    korean_name = next(
        (
            n["name"]
            for n in species["names"]
            if n["language"]["name"] == "ko"
        ),
        species["name"]
    )

    # 기본 모습 데이터
    pokemon = requests.get(
        f"https://pokeapi.co/api/v2/pokemon/{number}",
        timeout=15
    )
    pokemon.raise_for_status()
    pokemon = pokemon.json()

    image = (
        pokemon["sprites"]["other"]
        ["official-artwork"]["front_default"]
    )

    if not image:
        image = pokemon["sprites"]["front_default"]

    types = [
        t["type"]["name"]
        for t in pokemon["types"]
    ]

    return {
        "name": korean_name,
        "number": number,
        "image": image,
        "types": types
    }


def draw_pokemon():
    pokemon_list = get_pokemon_list()

    # API에 등록된 종 중 한 마리 선택
    chosen = random.choice(pokemon_list)

    return get_pokemon(chosen["url"])


# 세션 상태
if "entered" not in st.session_state:
    st.session_state.entered = False

if "pokemon" not in st.session_state:
    st.session_state.pokemon = None

if "effect" not in st.session_state:
    st.session_state.effect = "fireworks"


# 디자인
st.markdown("""
<style>
.stApp {
    background: linear-gradient(
        145deg, #06142F, #12366A
    );
    color: white;
}

h1, h2, h3, p {
    color: white !important;
}

.block-container {
    padding-top: 4rem;
}

div.stButton > button {
    background: #7DD3FC !important;
    color: #06142F !important;
    border: 2px solid white !important;
    border-radius: 16px !important;
    font-size: 21px !important;
    font-weight: 800 !important;
    min-height: 62px;
}

div.stButton > button p {
    color: #06142F !important;
}

div.stButton > button:hover {
    background: white !important;
    transform: scale(1.03);
}

.pokemon-card {
    background: rgba(255,255,255,0.09);
    border: 1px solid rgba(255,255,255,0.25);
    border-radius: 24px;
    padding: 24px;
    text-align: center;
}

.pokemon-name {
    font-size: 36px;
    font-weight: 900;
}

.pokemon-number {
    color: #BBD9FF !important;
    font-size: 18px;
}
</style>
""", unsafe_allow_html=True)


# 랜덤 축하 효과
def celebration(effect):
    html = """
    <html>
    <body style="margin:0;overflow:hidden;">
    <canvas id="c"></canvas>
    <script>
    const c = document.getElementById("c");
    const ctx = c.getContext("2d");

    c.width = window.innerWidth;
    c.height = 210;

    const effect = "EFFECT";
    const colors = [
        "#FFDD55", "#FF5588",
        "#55DDFF", "#AA88FF",
        "#66FFAA", "#FFFFFF"
    ];

    let particles = [];

    for (let i = 0; i < 150; i++) {
        let angle = Math.random() * Math.PI * 2;
        let speed = Math.random() * 4 + 1;

        particles.push({
            x: effect === "fireworks"
                ? c.width / 2
                : Math.random() * c.width,
            y: effect === "fireworks"
                ? c.height / 2
                : -Math.random() * 210,
            vx: effect === "fireworks"
                ? Math.cos(angle) * speed
                : Math.random() * 2 - 1,
            vy: effect === "fireworks"
                ? Math.sin(angle) * speed
                : Math.random() * 2 + 1,
            size: Math.random() * 5 + 2,
            color: colors[
                Math.floor(Math.random() * colors.length)
            ]
        });
    }

    let frame = 0;

    function animate() {
        ctx.clearRect(0,0,c.width,c.height);

        for (let p of particles) {
            p.x += p.vx;
            p.y += p.vy;

            if (effect === "fireworks") {
                p.vy += 0.025;
            }

            ctx.fillStyle = p.color;
            ctx.beginPath();

            if (effect === "stars") {
                ctx.fillRect(
                    p.x, p.y,
                    p.size, p.size
                );
            } else {
                ctx.arc(
                    p.x, p.y,
                    p.size, 0, Math.PI * 2
                );
                ctx.fill();
            }
        }

        frame++;

        if (frame < 150) {
            requestAnimationFrame(animate);
        }
    }

    animate();
    </script>
    </body>
    </html>
    """

    components.html(
        html.replace("EFFECT", effect),
        height=210
    )


def choose_new_pokemon():
    with st.spinner("포켓몬을 찾는 중..."):
        st.session_state.pokemon = draw_pokemon()

    st.session_state.effect = random.choice([
        "fireworks", "confetti", "stars"
    ])


# 시작 화면
if not st.session_state.entered:

    st.markdown(
        """
        <h1 style="
            text-align:center;
            font-size:48px;
            margin-top:60px;
        ">
            랜덤 포켓몬 뽑기
        </h1>

        <p style="
            text-align:center;
            font-size:20px;
            margin-bottom:45px;
        ">
            어떤 포켓몬이 등장할까요?
        </p>
        """,
        unsafe_allow_html=True
    )

    left, center, right = st.columns([1, 2, 1])

    with center:
        if st.button(
            "⚡ 들어가기",
            use_container_width=True
        ):
            try:
                choose_new_pokemon()
                st.session_state.entered = True
                st.rerun()
            except Exception:
                st.error(
                    "포켓몬을 불러오지 못했어요. "
                    "잠시 후 다시 시도해 주세요."
                )


# 포켓몬 등장 화면
else:

    pokemon = st.session_state.pokemon

    st.markdown(
        """
        <h1 style="text-align:center;">
            환영합니다!!
        </h1>
        <p style="text-align:center;">
            야생의 포켓몬이 나타났다!
        </p>
        """,
        unsafe_allow_html=True
    )

    celebration(st.session_state.effect)

    if pokemon:
        st.markdown(
            '<div class="pokemon-card">',
            unsafe_allow_html=True
        )

        st.markdown(
            f"""
            <p class="pokemon-number">
                도감 No. {pokemon['number']:04d}
            </p>
            """,
            unsafe_allow_html=True
        )

        if pokemon["image"]:
            st.image(
                pokemon["image"],
                width=260
            )

        st.markdown(
            f"""
            <div class="pokemon-name">
                {pokemon['name']}
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(
            "타입: " + ", ".join(pokemon["types"])
        )

        st.markdown(
            "</div>",
            unsafe_allow_html=True
        )

    st.write("")

    if st.button(
        "🎲 다시 뽑기",
        use_container_width=True
    ):
        try:
            choose_new_pokemon()
            st.rerun()
        except Exception:
            st.error("다시 시도해 주세요.")

    if st.button(
        "🏠 돌아가기",
        use_container_width=True
    ):
        st.session_state.entered = False
        st.session_state.pokemon = None
        st.rerun()
