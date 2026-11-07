
import streamlit as st
import streamlit.components.v1 as components
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
SHINY_CHANCE = 0.05

TYPES = {
    "normal": "노말", "fire": "불꽃", "water": "물",
    "electric": "전기", "grass": "풀", "ice": "얼음",
    "fighting": "격투", "poison": "독", "ground": "땅",
    "flying": "비행", "psychic": "에스퍼", "bug": "벌레",
    "rock": "바위", "ghost": "고스트", "dragon": "드래곤",
    "dark": "악", "steel": "강철", "fairy": "페어리"
}

BALLS = [
    ("몬스터볼", "#ef4444", "", 45),
    ("슈퍼볼", "#2563eb", "S", 25),
    ("하이퍼볼", "#292d38", "H", 18),
    ("마스터볼", "#9333ea", "M", 2),
    ("프레미어볼", "#f1f5f9", "", 10)
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


# ----------------------------
# 데이터 불러오기
# ----------------------------

@st.cache_data(ttl=86400, show_spinner=False)
def get_json(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=86400, show_spinner=False)
def get_species_list():
    result = []
    url = f"{API}/pokemon-species?limit=1000"

    while url:
        data = get_json(url)
        result.extend(data["results"])
        url = data["next"]

    return result


def draw_pokemon():
    chosen = random.choice(get_species_list())
    species = get_json(chosen["url"])

    default_form = next(
        (
            item for item in species["varieties"]
            if item["is_default"]
        ),
        species["varieties"][0]
    )

    pokemon = get_json(default_form["pokemon"]["url"])

    name = next(
        (
            item["name"]
            for item in species["names"]
            if item["language"]["name"] == "ko"
        ),
        species["name"]
    )

    sprites = pokemon.get("sprites") or {}
    artwork = (
        (sprites.get("other") or {})
        .get("official-artwork") or {}
    )

    shiny = random.random() < SHINY_CHANCE

    if shiny:
        image = (
            artwork.get("front_shiny")
            or sprites.get("front_shiny")
        )
    else:
        image = (
            artwork.get("front_default")
            or sprites.get("front_default")
        )

    if species.get("is_mythical"):
        rarity, color = "환상", "#f9a8d4"
    elif species.get("is_legendary"):
        rarity, color = "전설", "#facc15"
    elif species["capture_rate"] <= 45:
        rarity, color = "초희귀", "#c4b5fd"
    elif species["capture_rate"] <= 100:
        rarity, color = "희귀", "#7dd3fc"
    else:
        rarity, color = "일반", "#cbd5e1"

    ball = random.choices(
        BALLS,
        weights=[item[3] for item in BALLS],
        k=1
    )[0]

    return {
        "uid": str(uuid.uuid4()),
        "name": name,
        "number": species["id"],
        "level": random.randint(1, 100),
        "shiny": shiny,
        "image": image,
        "types": " / ".join(
            TYPES.get(t["type"]["name"], t["type"]["name"])
            for t in pokemon["types"]
        ),
        "rarity": rarity,
        "color": color,
        "ball": ball[0],
        "ball_color": ball[1],
        "ball_mark": ball[2]
    }


# ----------------------------
# 상태 초기화
# ----------------------------

defaults = {
    "page": "home",
    "current": None,
    "collection": [],
    "play_animation": False,
    "battle_partner": None,
    "battle_result": None,
    "battle_reward": None,
    "battle_stats": {
        "win": 0,
        "draw": 0,
        "lose": 0
    }
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value


# ----------------------------
# 화면 디자인
# ----------------------------

st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #06142f, #12366a);
    color: white;
}

header[data-testid="stHeader"] {
    background: transparent;
}

h1, h2, h3 {
    color: white !important;
}

.block-container {
    padding-top: 2.5rem;
}

div.stButton > button,
div.stDownloadButton > button {
    background: #7dd3fc !important;
    color: #06142f !important;
    border: 2px solid #e0f2fe !important;
    border-radius: 14px !important;
    min-height: 52px;
}

div.stButton > button p,
div.stDownloadButton > button p {
    color: #06142f !important;
    font-weight: 800 !important;
}

div.stButton > button:hover {
    background: white !important;
}

.hero {
    text-align: center;
    font-size: clamp(28px, 5vw, 44px);
    font-weight: 900;
    margin: 25px 0 15px;
    color: white;
}

.subtitle {
    text-align: center;
    color: #c8ddfa;
    margin-bottom: 30px;
}

.collection-box {
    padding: 20px;
    border: 1px solid #8abfff66;
    border-radius: 20px;
    background: #ffffff0b;
    margin-bottom: 15px;
    color: white;
}

.collection-box h3 {
    margin: 0 0 12px;
}

.collection-box p {
    color: #c8ddfa;
}

.record {
    background: #ffffff0b;
    border-radius: 15px;
    padding: 14px;
    margin-bottom: 16px;
    color: white;
}

.menu-card {
    padding: 25px;
    background: #ffffff10;
    border: 1px solid #ffffff30;
    border-radius: 22px;
    min-height: 180px;
}
</style>
""", unsafe_allow_html=True)


# ----------------------------
# 포켓몬 등장 애니메이션
# ----------------------------

def show_encounter(p, animate=True):
    data = json.dumps(
        {
            **p,
            "animate": animate,
            "render_id": str(uuid.uuid4())
        },
        ensure_ascii=True
    ).replace("<", "\\u003c")

    document = """
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<style>
* {box-sizing:border-box}

html,body {
    margin:0;
    background:transparent;
    color:white;
    font-family:system-ui,sans-serif;
}

.scene {
    position:relative;
    height:590px;
    overflow:hidden;
    text-align:center;
}

canvas {
    position:absolute;
    inset:0;
    width:100%;
    height:100%;
    pointer-events:none;
    z-index:5;
}

.ball-stage {
    position:absolute;
    inset:0;
    display:flex;
    align-items:center;
    justify-content:center;
    flex-direction:column;
    z-index:2;
    transition:opacity .3s;
}

.ball {
    width:130px;
    height:130px;
    position:relative;
    filter:drop-shadow(0 12px 18px #0007);
}

.half {
    position:absolute;
    width:130px;
    height:65px;
    border:5px solid #182237;
    overflow:hidden;
    transition:transform .65s ease,opacity .65s;
}

.top {
    top:0;
    border-radius:70px 70px 0 0;
    background:var(--ball);
}

.bottom {
    bottom:0;
    border-radius:0 0 70px 70px;
    background:#f8fafc;
}

.mark {
    display:block;
    margin-top:8px;
    font-size:32px;
    font-weight:900;
    color:#facc15;
}

.belt {
    position:absolute;
    top:59px;
    width:130px;
    height:12px;
    background:#182237;
}

.lock {
    position:absolute;
    left:47px;
    top:47px;
    width:36px;
    height:36px;
    border:7px solid #182237;
    background:white;
    border-radius:50%;
}

.ball-label {
    margin-top:25px;
    color:#dbeafe;
}

.shaking .ball {
    animation:shake .45s ease-in-out 3;
}

.open .top {
    transform:translateY(-75px) rotate(-25deg);
    opacity:0;
}

.open .bottom {
    transform:translateY(75px) rotate(20deg);
    opacity:0;
}

.open .belt,
.open .lock {
    opacity:0;
    transition:opacity .2s;
}

.finished .ball-stage {
    opacity:0;
    pointer-events:none;
}

.flash {
    position:absolute;
    left:50%;
    top:50%;
    width:20px;
    height:20px;
    background:white;
    border-radius:50%;
    opacity:0;
    z-index:3;
    pointer-events:none;
}

.open .flash {
    animation:flash .8s ease-out;
}

.card {
    position:relative;
    margin:20px auto;
    padding:22px;
    width:min(94%,430px);
    border-radius:26px;
    border:1px solid var(--rarity);
    background:linear-gradient(145deg,#ffffff17,#ffffff05);
    opacity:0;
    visibility:hidden;
    transform:translateY(25px) scale(.8);
}

.revealed .card {
    visibility:visible;
    opacity:1;
    transform:none;
    transition:opacity .6s,transform .6s;
}

.shiny-card {
    box-shadow:0 0 30px #facc1533;
    border:2px solid #fde68a;
}

.pokemon {
    display:block;
    margin:auto;
    width:245px;
    height:245px;
    max-width:95%;
    object-fit:contain;
}

h2 {
    font-size:32px;
    margin:8px 0 14px;
}

.number {
    color:#bdd7fa;
    font-size:15px;
}

.badge {
    display:inline-block;
    padding:7px 12px;
    margin:4px;
    border-radius:24px;
    background:#ffffff14;
}

.rarity {
    color:var(--rarity);
    font-weight:800;
}

.shiny {
    color:#fde68a;
    border:1px solid #facc1580;
}

.detail {
    color:#c8ddfa;
    line-height:1.8;
}

.missing {
    height:245px;
    display:grid;
    place-items:center;
    color:#c8ddfa;
}

@keyframes shake {
    0%,100% {transform:rotate(0)}
    25% {transform:rotate(-22deg) translateX(-8px)}
    75% {transform:rotate(22deg) translateX(8px)}
}

@keyframes flash {
    0% {
        opacity:0;
        transform:translate(-50%,-50%) scale(1)
    }
    35% {
        opacity:1;
        box-shadow:0 0 90px 70px #dbeafe
    }
    100% {
        opacity:0;
        transform:translate(-50%,-50%) scale(25)
    }
}
</style>
</head>
<body>

<div id="scene" class="scene">
    <canvas id="fx"></canvas>

    <div class="ball-stage">
        <div class="ball">
            <div class="half top">
                <span id="mark" class="mark"></span>
            </div>
            <div class="half bottom"></div>
            <div class="belt"></div>
            <div class="lock"></div>
        </div>
        <div id="ball-label" class="ball-label"></div>
    </div>

    <div class="flash"></div>

    <div id="card" class="card">
        <div id="number" class="number"></div>
        <img id="pokemon" class="pokemon" alt="">
        <div id="missing" class="missing" hidden>
            이미지를 불러올 수 없어요
        </div>
        <h2 id="name"></h2>
        <span id="level" class="badge"></span>
        <span id="rarity" class="badge rarity"></span>
        <div>
            <span id="shiny" class="badge"></span>
        </div>
        <p id="types" class="detail"></p>
        <div id="ball-info" class="detail"></div>
    </div>
</div>

<script>
const p = __DATA__;

const scene = document.getElementById("scene");
const image = document.getElementById("pokemon");
const missing = document.getElementById("missing");

scene.style.setProperty("--ball", p.ball_color);
scene.style.setProperty("--rarity", p.color);

function text(id,value) {
    document.getElementById(id).textContent=value;
}

text("mark",p.ball_mark);
text("ball-label",p.ball+" 준비 중...");
text("number","도감 No. "+String(p.number).padStart(4,"0"));
text("name",p.name);
text("level","Lv. "+p.level);
text("rarity",p.rarity);
text("types",p.types);
text("ball-info",p.ball+"에서 등장!");
text("shiny",p.shiny ? "✨ 이로치 포켓몬!" : "일반 색상");

image.alt=p.name;

if(p.shiny) {
    document.getElementById("card").classList.add("shiny-card");
    document.getElementById("shiny").classList.add("shiny");
}

let launched=false;

function launch() {
    if(launched)return;
    launched=true;

    if(!p.animate) {
        scene.classList.add("finished","revealed");
        return;
    }

    text("ball-label",p.ball+"이 흔들리고 있어요!");

    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            scene.classList.add("shaking");
        });
    });

    setTimeout(() => scene.classList.add("open"),1450);

    setTimeout(() => {
        scene.classList.add("finished","revealed");
        celebrate();
    },2050);
}

image.onload=launch;

image.onerror=() => {
    image.style.display="none";
    missing.hidden=false;
    launch();
};

if(p.image) {
    image.src=p.image;
    if(image.complete && image.naturalWidth>0)launch();
} else {
    image.style.display="none";
    missing.hidden=false;
    launch();
}

setTimeout(launch,5000);

const canvas=document.getElementById("fx");
const ctx=canvas.getContext("2d");

let width,height,particles=[],start,last,nextBurst=0;

function resize() {
    width=canvas.clientWidth;
    height=canvas.clientHeight;
    const dpr=devicePixelRatio||1;
    canvas.width=width*dpr;
    canvas.height=height*dpr;
    ctx.setTransform(dpr,0,0,dpr,0,0);
}

resize();

const colors=p.shiny
    ? ["#facc15","#fde68a","#ffffff"]
    : ["#7dd3fc","#f9a8d4","#c4b5fd","#86efac","#ffffff"];

function burst() {
    const x=width*(.15+Math.random()*.7);
    const y=height*(.15+Math.random()*.45);

    for(let i=0;i<60;i++) {
        const a=Math.random()*Math.PI*2;
        const speed=35+Math.random()*150;

        particles.push({
            x,y,
            vx:Math.cos(a)*speed,
            vy:Math.sin(a)*speed,
            life:1.4+Math.random()*1.2,
            size:2+Math.random()*4,
            color:colors[Math.floor(Math.random()*colors.length)]
        });
    }
}

function star(x,y,r) {
    ctx.beginPath();

    for(let i=0;i<10;i++) {
        const a=i*Math.PI/5-Math.PI/2;
        const s=i%2?r*.35:r;
        const px=x+Math.cos(a)*s;
        const py=y+Math.sin(a)*s;

        if(i===0)ctx.moveTo(px,py);
        else ctx.lineTo(px,py);
    }

    ctx.closePath();
    ctx.fill();
}

function frame(now) {
    if(start===undefined) {
        start=now;
        last=now;
    }

    const elapsed=(now-start)/1000;
    const dt=Math.min((now-last)/1000,.05);
    last=now;

    ctx.clearRect(0,0,width,height);

    if(elapsed<3.5 && elapsed>=nextBurst) {
        burst();
        nextBurst=elapsed+.5;
    }

    for(const q of particles) {
        q.life-=dt;
        q.x+=q.vx*dt;
        q.y+=q.vy*dt;
        q.vy+=25*dt;

        ctx.globalAlpha=Math.max(0,Math.min(1,q.life));
        ctx.fillStyle=q.color;

        if(p.shiny) {
            star(q.x,q.y,q.size*2);
        } else {
            ctx.beginPath();
            ctx.arc(q.x,q.y,q.size,0,Math.PI*2);
            ctx.fill();
        }
    }

    ctx.globalAlpha=1;
    particles=particles.filter(q=>q.life>0);

    if(elapsed<3.5||particles.length) {
        requestAnimationFrame(frame);
    }
}

function celebrate() {
    requestAnimationFrame(frame);
}
</script>
</body>
</html>
"""

    components.html(
        document.replace("__DATA__", data),
        height=600,
        scrolling=False
    )


# ----------------------------
# 포켓몬 뽑기
# ----------------------------

def new_draw():
    try:
        with st.spinner("포켓몬을 찾는 중..."):
            pokemon = draw_pokemon()

        st.session_state.current = pokemon
        st.session_state.collection.append(pokemon)
        st.session_state.page = "encounter"
        st.session_state.play_animation = True
        st.rerun()

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        IndexError
    ):
        st.error("포켓몬을 불러오지 못했어요. 다시 시도해 주세요.")


# ----------------------------
# 가위바위보 배틀
# ----------------------------

def play_rps(my_choice):
    opponent = random.choice(list(RPS))

    if my_choice == opponent:
        result = "draw"
    elif BEATS[my_choice] == opponent:
        result = "win"
    else:
        result = "lose"

    st.session_state.battle_stats[result] += 1

    st.session_state.battle_result = {
        "my_choice": my_choice,
        "opponent_choice": opponent,
        "result": result
    }

    st.session_state.battle_reward = None

    if result == "win":
        st.session_state.battle_reward = {
            "status": "pending",
            "pokemon": None
        }


def receive_reward():
    reward = st.session_state.battle_reward

    if not reward or reward["status"] != "pending":
        return

    try:
        with st.spinner("승리 보상을 준비하는 중..."):
            pokemon = draw_pokemon()

        st.session_state.collection.append(pokemon)
        st.session_state.battle_reward = {
            "status": "received",
            "pokemon": pokemon
        }
        st.session_state.play_animation = True
        st.rerun()

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        IndexError
    ):
        st.error("보상을 불러오지 못했어요. 다시 시도해 주세요.")


# ----------------------------
# 저장 파일 검증
# ----------------------------

def validate_saved_pokemon(item):
    if not isinstance(item, dict):
        raise ValueError("잘못된 기록")

    ball = next(b for b in BALLS if b[0] == item["ball"])

    colors = {
        "일반": "#cbd5e1",
        "희귀": "#7dd3fc",
        "초희귀": "#c4b5fd",
        "전설": "#facc15",
        "환상": "#f9a8d4"
    }

    if item["rarity"] not in colors:
        raise ValueError("잘못된 희귀도")

    if not isinstance(item["name"], str) or not 1 <= len(item["name"]) <= 100:
        raise ValueError("잘못된 이름")

    if type(item["number"]) is not int or not 1 <= item["number"] <= 100000:
        raise ValueError("잘못된 번호")

    if type(item["level"]) is not int or not 1 <= item["level"] <= 100:
        raise ValueError("잘못된 레벨")

    if type(item["shiny"]) is not bool:
        raise ValueError("잘못된 이로치 정보")

    if not isinstance(item["types"], str) or len(item["types"]) > 100:
        raise ValueError("잘못된 타입")

    if not isinstance(item["uid"], str) or len(item["uid"]) > 100:
        raise ValueError("잘못된 ID")

    image = item.get("image")

    prefix = (
        "https://raw.githubusercontent.com/"
        "PokeAPI/sprites/master/"
    )

    if image is not None:
        if not isinstance(image, str) or not image.startswith(prefix):
            raise ValueError("잘못된 이미지 주소")

    return {
        "uid": item["uid"],
        "name": item["name"],
        "number": item["number"],
        "level": item["level"],
        "shiny": item["shiny"],
        "image": image,
        "types": item["types"],
        "rarity": item["rarity"],
        "color": colors[item["rarity"]],
        "ball": ball[0],
        "ball_color": ball[1],
        "ball_mark": ball[2]
    }


# ----------------------------
# 오른쪽 보관함 메뉴
# ----------------------------

main, right = st.columns([3, 1], gap="large")

with right:
    collection = st.session_state.collection
    shiny_count = sum(p["shiny"] for p in collection)
    unique_count = len({p["number"] for p in collection})

    st.markdown(
        f"""
        <div class="collection-box">
            <h3>📦 내 포켓몬 보관함</h3>
            <p>보유: <b>{len(collection)}마리</b></p>
            <p>발견: <b>{unique_count}종</b></p>
            <p>✨ 이로치: <b>{shiny_count}마리</b></p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("📦 보관함 들어가기", use_container_width=True):
        st.session_state.page = "collection"
        st.rerun()

    if st.button("⚔️ 가위바위보 배틀", use_container_width=True):
        st.session_state.page = "battle"
        st.rerun()

    if st.button("🏠 홈으로", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    save_data = json.dumps(
        {
            "version": 1,
            "pokemon": collection
        },
        ensure_ascii=False,
        indent=2
    )

    st.download_button(
        "💾 저장 파일 다운로드",
        data=save_data,
        file_name="my_pokemon.json",
        mime="application/json",
        use_container_width=True
    )

    with st.expander("📂 저장 파일 불러오기"):
        uploaded = st.file_uploader(
            "이전에 저장한 JSON 파일",
            type=["json"]
        )

        if st.button("불러오기", use_container_width=True):
            if uploaded is None:
                st.warning("파일을 선택해 주세요.")
            else:
                try:
                    if uploaded.size > 10 * 1024 * 1024:
                        raise ValueError("파일이 너무 큽니다.")

                    saved = json.loads(uploaded.getvalue())

                    if saved.get("version") != 1:
                        raise ValueError("지원하지 않는 버전")

                    records = saved["pokemon"]

                    if not isinstance(records, list) or len(records) > 10000:
                        raise ValueError("잘못된 기록 개수")

                    restored = [
                        validate_saved_pokemon(item)
                        for item in records
                    ]

                    existing = {
                        item["uid"]
                        for item in st.session_state.collection
                    }

                    for item in restored:
                        if item["uid"] not in existing:
                            st.session_state.collection.append(item)
                            existing.add(item["uid"])

                    st.session_state.page = "collection"
                    st.rerun()

                except (
                    ValueError,
                    KeyError,
                    TypeError,
                    StopIteration,
                    AttributeError
                ):
                    st.error("올바른 저장 파일인지 확인해 주세요.")

    st.caption(
        "포켓몬은 현재 접속 세션에 저장됩니다. "
        "나중에도 보관하려면 JSON 파일을 다운로드해 주세요."
    )


# ----------------------------
# 메인 페이지
# ----------------------------

with main:

    # 홈
    if st.session_state.page == "home":
        st.markdown(
            '<div class="hero">⚡ 포켓몬 어드벤처</div>'
            '<div class="subtitle">'
            '포켓몬을 만나고, 파트너와 함께 배틀에 도전하세요!'
            '</div>',
            unsafe_allow_html=True
        )

        a, b = st.columns(2)

        with a:
            st.subheader("🎲 포켓몬 뽑기")
            st.write(
                "몬스터볼에서 랜덤 포켓몬이 등장합니다. "
                "이로치와 전설의 포켓몬도 만나 보세요!"
            )

            if st.button("🚀 포켓몬 뽑기", use_container_width=True):
                new_draw()

        with b:
            st.subheader("⚔️ 가위바위보 배틀")
            st.write(
                "내 포켓몬을 파트너로 선택하고 대결하세요. "
                "승리하면 새로운 포켓몬을 얻습니다!"
            )

            if st.button("⚔️ 배틀 시작", use_container_width=True):
                st.session_state.page = "battle"
                st.rerun()

    # 포켓몬 등장
    elif st.session_state.page == "encounter":
        st.markdown(
            '<div class="hero">포켓몬이 나타났다!</div>',
            unsafe_allow_html=True
        )

        play = st.session_state.play_animation
        st.session_state.play_animation = False

        show_encounter(
            st.session_state.current,
            animate=play
        )

        st.success("포켓몬이 보관함에 자동으로 저장됐어요!")

        a, b, c = st.columns(3)

        with a:
            if st.button("🎲 다시 뽑기", use_container_width=True):
                new_draw()

        with b:
            if st.button("⚔️ 함께 배틀하기", use_container_width=True):
                st.session_state.battle_partner = (
                    st.session_state.current["uid"]
                )
                st.session_state.page = "battle"
                st.rerun()

        with c:
            if st.button("🏠 돌아가기", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()

    # 가위바위보
    elif st.session_state.page == "battle":
        st.markdown(
            '<div class="hero">⚔️ 포켓몬 가위바위보 배틀</div>'
            '<div class="subtitle">'
            '파트너와 함께 상대 트레이너에게 도전하세요!'
            '</div>',
            unsafe_allow_html=True
        )

        collection = st.session_state.collection

        if not collection:
            st.info("포켓몬이 없어요. 먼저 포켓몬을 뽑아 주세요!")

            if st.button("🎲 첫 포켓몬 뽑기", use_container_width=True):
                new_draw()

        else:
            by_uid = {p["uid"]: p for p in collection}
            partner_ids = list(by_uid)

            if st.session_state.battle_partner not in by_uid:
                st.session_state.battle_partner = partner_ids[0]

            def partner_label(uid):
                p = by_uid[uid]
                shiny = "✨ " if p["shiny"] else ""
                return f"{shiny}{p['name']} · Lv. {p['level']}"

            selected_id = st.selectbox(
                "함께할 포켓몬",
                options=partner_ids,
                format_func=partner_label,
                key="battle_partner"
            )

            partner = by_uid[selected_id]

            a, b = st.columns([1, 2])

            with a:
                if partner["image"]:
                    st.image(partner["image"], width=180)

            with b:
                st.subheader(partner["name"])
                st.write(
                    f"Lv. {partner['level']} · {partner['rarity']}"
                )
                st.write(f"타입: {partner['types']}")

            stats = st.session_state.battle_stats

            a, b, c = st.columns(3)
            a.metric("🏆 승리", stats["win"])
            b.metric("🤝 무승부", stats["draw"])
            c.metric("💨 패배", stats["lose"])

            reward = st.session_state.battle_reward
            pending = (
                reward is not None
                and reward["status"] == "pending"
            )

            st.markdown("### 무엇을 낼까요?")

            columns = st.columns(3)

            for column, choice in zip(columns, RPS):
                with column:
                    if st.button(
                        f"{RPS[choice]} {choice}",
                        key=f"choice_{choice}",
                        use_container_width=True,
                        disabled=pending
                    ):
                        play_rps(choice)
                        st.rerun()

            result = st.session_state.battle_result

            if result:
                st.divider()

                mine, opponent = st.columns(2)

                with mine:
                    st.subheader("나")
                    st.markdown(
                        f"## {RPS[result['my_choice']]} "
                        f"{result['my_choice']}"
                    )

                with opponent:
                    st.subheader("상대")
                    st.markdown(
                        f"## {RPS[result['opponent_choice']]} "
                        f"{result['opponent_choice']}"
                    )

                if result["result"] == "win":
                    st.success("🏆 승리! 새로운 포켓몬을 획득했어요!")

                    if pending:
                        receive_reward()

                        if st.button(
                            "🎁 보상 다시 받기",
                            use_container_width=True
                        ):
                            receive_reward()

                    elif reward and reward["status"] == "received":
                        play = st.session_state.play_animation
                        st.session_state.play_animation = False

                        show_encounter(
                            reward["pokemon"],
                            animate=play
                        )

                        st.caption(
                            "보상 포켓몬이 보관함에 저장됐어요."
                        )

                elif result["result"] == "draw":
                    st.info("🤝 무승부! 다시 도전하세요.")

                else:
                    st.warning("💨 패배! 다음에는 이길 수 있을 거예요.")

    # 보관함
    elif st.session_state.page == "collection":
        st.markdown(
            '<div class="hero">📦 내 포켓몬 보관함</div>',
            unsafe_allow_html=True
        )

        if not st.session_state.collection:
            st.info("아직 포켓몬이 없어요.")

        else:
            query = st.text_input("🔎 이름 검색")
            only_shiny = st.checkbox("✨ 이로치만 보기")

            order = st.selectbox(
                "정렬",
                ["최근에 뽑은 순", "레벨 높은 순", "도감 번호순"]
            )

            records = [
                p for p in st.session_state.collection
                if query.strip() in p["name"]
                and (not only_shiny or p["shiny"])
            ]

            if order == "레벨 높은 순":
                records.sort(
                    key=lambda p: p["level"],
                    reverse=True
                )
            elif order == "도감 번호순":
                records.sort(key=lambda p: p["number"])
            else:
                records.reverse()

            st.write(f"총 {len(records)}마리")

            page_size = 12
            total_pages = max(
                1,
                (len(records) + page_size - 1) // page_size
            )

            page_number = st.selectbox(
                "페이지",
                range(1, total_pages + 1),
                key=f"collection_page_{total_pages}"
            )

            start = (page_number - 1) * page_size
            visible = records[start:start + page_size]

            columns = st.columns(3)

            for i, p in enumerate(visible):
                with columns[i % 3]:
                    if p["image"]:
                        st.image(p["image"], width=170)
                    else:
                        st.write("이미지 없음")

                    shiny_label = (
                        "✨ 이로치" if p["shiny"] else "일반 색상"
                    )

                    st.markdown(
                        f"""
                        <div class="record">
                            <b>{html.escape(p["name"])}</b><br>
                            No. {p["number"]:04d}
                            · Lv. {p["level"]}<br>
                            {html.escape(p["rarity"])}
                            · {shiny_label}<br>
                            {html.escape(p["types"])}<br>
                            {html.escape(p["ball"])}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    if st.button(
                        "⚔️ 파트너로 배틀",
                        key=f"partner_{p['uid']}",
                        use_container_width=True
                    ):
                        st.session_state.battle_partner = p["uid"]
                        st.session_state.page = "battle"
                        st.rerun()


with st.expander("📖 게임 규칙"):
    st.write(
        "포켓몬은 PokéAPI에 등록된 종 중 무작위로 등장합니다. "
        "레벨은 1~100, 이로치 확률은 5%입니다. "
        "가위바위보에서 승리하면 포켓몬 한 마리를 보상으로 받습니다. "
        "패배하거나 무승부일 때는 보상이 없습니다. "
        "레벨과 희귀도는 가위바위보 승패에 영향을 주지 않습니다. "
        "포켓몬 보관 기록은 JSON 파일로 저장하고 복원할 수 있습니다."
    )
