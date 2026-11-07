import html
import json
import random
import uuid

import requests
import streamlit as st
import streamlit.components.v1 as components


st.set_page_config(
    page_title="포켓몬 뽑기",
    page_icon="⚡",
    layout="wide",
)

API = "https://pokeapi.co/api/v2"
SHINY_CHANCE = 0.05

TYPES = {
    "normal": "노말", "fire": "불꽃", "water": "물",
    "electric": "전기", "grass": "풀", "ice": "얼음",
    "fighting": "격투", "poison": "독", "ground": "땅",
    "flying": "비행", "psychic": "에스퍼", "bug": "벌레",
    "rock": "바위", "ghost": "고스트", "dragon": "드래곤",
    "dark": "악", "steel": "강철", "fairy": "페어리",
}

BALLS = [
    # 이름, 위쪽 색상, 장식 글자, 확률
    ("몬스터볼", "#ef4444", "", 45),
    ("슈퍼볼", "#2563eb", "S", 25),
    ("하이퍼볼", "#292d38", "H", 18),
    ("마스터볼", "#9333ea", "M", 2),
    ("프레미어볼", "#f1f5f9", "", 10),
]


@st.cache_data(ttl=86400, show_spinner=False)
def get_json(url):
    response = requests.get(url, timeout=20)
    response.raise_for_status()
    return response.json()


@st.cache_data(ttl=86400, show_spinner=False)
def species_list():
    result = []
    url = f"{API}/pokemon-species?limit=1000"

    while url:
        data = get_json(url)
        result.extend(data["results"])
        url = data["next"]

    return result


def draw():
    species = get_json(random.choice(species_list())["url"])

    form = next(
        (
            item for item in species["varieties"]
            if item["is_default"]
        ),
        species["varieties"][0],
    )
    pokemon = get_json(form["pokemon"]["url"])

    name = next(
        (
            item["name"] for item in species["names"]
            if item["language"]["name"] == "ko"
        ),
        species["name"],
    )

    sprites = pokemon.get("sprites") or {}
    artwork = (
        (sprites.get("other") or {}).get("official-artwork") or {}
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
        BALLS, weights=[item[3] for item in BALLS], k=1
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
        "ball_mark": ball[2],
    }


def show_encounter(p, animate=True):
    # 매번 다른 문서를 전달해 다시 뽑을 때도 효과를 재실행
    data = json.dumps(
        {**p, "animate": animate, "render_id": str(uuid.uuid4())},
        ensure_ascii=True,
    ).replace("<", "\\u003c")

    document = """
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<style>
* {box-sizing:border-box}
html,body {
    margin:0; background:transparent; color:white;
    font-family:system-ui,sans-serif;
}
.scene {
    position:relative; height:590px; overflow:hidden;
    text-align:center;
}
canvas {
    position:absolute; inset:0; width:100%; height:100%;
    pointer-events:none; z-index:5;
}
.ball-stage {
    position:absolute; inset:0; display:flex;
    align-items:center; justify-content:center;
    flex-direction:column; z-index:2;
    transition:opacity .3s;
}
.ball {
    width:130px; height:130px; position:relative;
    filter:drop-shadow(0 12px 18px #0007);
}
.half {
    position:absolute; width:130px; height:65px;
    border:5px solid #182237; overflow:hidden;
    transition:transform .65s ease,opacity .65s;
}
.top {
    top:0; border-radius:70px 70px 0 0;
    background:var(--ball);
}
.bottom {
    bottom:0; border-radius:0 0 70px 70px;
    background:#f8fafc;
}
.mark {
    display:block; margin-top:8px; font-size:32px;
    font-weight:900; color:#facc15;
    -webkit-text-stroke:1px #182237;
}
.belt {
    position:absolute; top:59px; width:130px;
    height:12px; background:#182237;
}
.lock {
    position:absolute; left:47px; top:47px;
    width:36px; height:36px; border:7px solid #182237;
    background:white; border-radius:50%;
}
.ball-label {margin-top:25px; color:#dbeafe}
.shaking .ball {animation:shake .45s ease-in-out 3}
.open .top {transform:translateY(-75px) rotate(-25deg);opacity:0}
.open .bottom {transform:translateY(75px) rotate(20deg);opacity:0}
.open .belt,.open .lock {opacity:0;transition:opacity .2s}
.finished .ball-stage {opacity:0;pointer-events:none}
.flash {
    position:absolute; left:50%; top:50%;
    width:20px; height:20px; background:white;
    border-radius:50%; opacity:0; z-index:3;
    pointer-events:none;
}
.open .flash {animation:flash .8s ease-out}
.card {
    position:relative; margin:20px auto; padding:22px;
    width:min(94%,430px); border-radius:26px;
    border:1px solid var(--rarity);
    background:linear-gradient(145deg,#ffffff17,#ffffff05);
    opacity:0; visibility:hidden;
    transform:translateY(25px) scale(.8);
}
.revealed .card {
    visibility:visible; opacity:1; transform:none;
    transition:opacity .6s,transform .6s;
}
.shiny-card {
    box-shadow:0 0 30px #facc1533;
    border:2px solid #fde68a;
}
.pokemon {
    display:block; margin:auto; width:245px;
    height:245px; max-width:95%; object-fit:contain;
    filter:drop-shadow(0 0 24px #ffffff25);
}
h2 {font-size:32px;margin:8px 0 14px}
.number {color:#bdd7fa;font-size:15px}
.badge {
    display:inline-block; padding:7px 12px;
    margin:4px; border-radius:24px; background:#ffffff14;
}
.rarity {color:var(--rarity);font-weight:800}
.shiny {color:#fde68a;border:1px solid #facc1580}
.detail {color:#c8ddfa;line-height:1.8}
.missing {height:245px;display:grid;place-items:center;color:#c8ddfa}
@keyframes shake {
    0%,100% {transform:rotate(0)}
    25% {transform:rotate(-22deg) translateX(-8px)}
    75% {transform:rotate(22deg) translateX(8px)}
}
@keyframes flash {
    0% {opacity:0;transform:translate(-50%,-50%) scale(1)}
    35% {opacity:1;box-shadow:0 0 90px 70px #dbeafe}
    100% {opacity:0;transform:translate(-50%,-50%) scale(25)}
}
@media(prefers-reduced-motion:reduce) {
    .shaking .ball {animation:none}
    .half,.card {transition:none!important}
    .open .flash {animation:none}
}
</style>
</head>
<body>
<div id="scene" class="scene">
    <canvas id="fx"></canvas>
    <div class="ball-stage">
        <div class="ball">
            <div class="half top"><span id="mark" class="mark"></span></div>
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
        <div id="missing" class="missing" hidden>画像</div>
        <h2 id="name"></h2>
        <span id="level" class="badge"></span>
        <span id="rarity" class="badge rarity"></span>
        <div><span id="shiny" class="badge"></span></div>
        <p id="types" class="detail"></p>
        <div id="ball-info" class="detail"></div>
    </div>
</div>
<script>
const p = __DATA__;
const scene = document.getElementById("scene");
const image = document.getElementById("pokemon");
const missing = document.getElementById("missing");
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;

scene.style.setProperty("--ball", p.ball_color);
scene.style.setProperty("--rarity", p.color);
function text(id,value) {document.getElementById(id).textContent=value}
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

function imageFailed() {
    image.style.display="none";
    missing.hidden=false;
    missing.style.display="grid";
    missing.textContent="이미지를 불러올 수 없어요";
}
missing.style.display="none";

// 이미지가 준비된 후 연출 시작. 느릴 경우 최대 5초까지만 대기.
let launched=false;
function launch() {
    if(launched) return;
    launched=true;

    if(!p.animate || reduced) {
        scene.classList.add("finished","revealed");
        return;
    }

    text("ball-label",p.ball+"이 흔들리고 있어요!");
    requestAnimationFrame(() => {
        requestAnimationFrame(() => scene.classList.add("shaking"));
    });

    setTimeout(() => scene.classList.add("open"),1450);
    setTimeout(() => {
        scene.classList.add("finished","revealed");
        celebrate();
    },2050);
}
image.onload=launch;
image.onerror=() => {imageFailed();launch()};
if(p.image) {
    image.src=p.image;
    if(image.complete && image.naturalWidth>0) launch();
} else {
    imageFailed();launch();
}
setTimeout(launch,5000);

const canvas=document.getElementById("fx");
const ctx=canvas.getContext("2d");
let width,height,particles=[],start,last,nextBurst=0;
function resize() {
    width=canvas.clientWidth;height=canvas.clientHeight;
    const dpr=devicePixelRatio||1;
    canvas.width=width*dpr;canvas.height=height*dpr;
    ctx.setTransform(dpr,0,0,dpr,0,0);
}
resize();
addEventListener("resize",resize);

function burst() {
    const colors=p.shiny
        ? ["#facc15","#fde68a","#ffffff"]
        : ["#7dd3fc","#f9a8d4","#c4b5fd","#86efac","#ffffff"];
    const x=width*(.15+Math.random()*.7);
    const y=height*(.15+Math.random()*.45);
    for(let i=0;i<60;i++) {
        const a=Math.random()*Math.PI*2;
        const speed=35+Math.random()*150;
        particles.push({
            x,y,vx:Math.cos(a)*speed,vy:Math.sin(a)*speed,
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
        const px=x+Math.cos(a)*s,py=y+Math.sin(a)*s;
        if(i===0)ctx.moveTo(px,py);else ctx.lineTo(px,py);
    }
    ctx.closePath();ctx.fill();
}
function frame(now) {
    if(start===undefined){start=now;last=now}
    const elapsed=(now-start)/1000;
    const dt=Math.min((now-last)/1000,.05);last=now;
    ctx.clearRect(0,0,width,height);
    if(elapsed<3.5 && elapsed>=nextBurst) {
        burst();nextBurst=elapsed+.5;
    }
    for(const q of particles) {
        q.life-=dt;q.x+=q.vx*dt;q.y+=q.vy*dt;
        q.vy+=25*dt;
        ctx.globalAlpha=Math.max(0,Math.min(1,q.life));
        ctx.fillStyle=q.color;
        if(p.shiny)star(q.x,q.y,q.size*2);
        else {
            ctx.beginPath();ctx.arc(q.x,q.y,q.size,0,Math.PI*2);
            ctx.fill();
        }
    }
    ctx.globalAlpha=1;
    particles=particles.filter(q=>q.life>0);
    if(elapsed<3.5||particles.length)requestAnimationFrame(frame);
}
function celebrate() {
    if(!reduced)requestAnimationFrame(frame);
}
</script>
</body>
</html>
"""
    components.html(
        document.replace("__DATA__", data),
        height=600,
        scrolling=False,
    )


# 저장 파일에서 허용할 값만 복원
def validate_saved_pokemon(item):
    if not isinstance(item, dict):
        raise ValueError("잘못된 포켓몬 기록")

    ball = next(b for b in BALLS if b[0] == item["ball"])

    name = item["name"]
    number = item["number"]
    level = item["level"]
    shiny = item["shiny"]
    rarity = item["rarity"]
    types = item["types"]
    uid = item["uid"]
    image = item.get("image")

    if not isinstance(name, str) or not 1 <= len(name) <= 100:
        raise ValueError("잘못된 이름")
    if type(number) is not int or not 1 <= number <= 100000:
        raise ValueError("잘못된 도감 번호")
    if type(level) is not int or not 1 <= level <= 100:
        raise ValueError("잘못된 레벨")
    if type(shiny) is not bool:
        raise ValueError("잘못된 이로치 정보")
    if not isinstance(types, str) or len(types) > 100:
        raise ValueError("잘못된 타입")
    if not isinstance(uid, str) or len(uid) > 100:
        raise ValueError("잘못된 기록 번호")

    colors = {
        "일반": "#cbd5e1", "희귀": "#7dd3fc",
        "초희귀": "#c4b5fd", "전설": "#facc15",
        "환상": "#f9a8d4",
    }
    if rarity not in colors:
        raise ValueError("잘못된 희귀도")

    prefix = (
        "https://raw.githubusercontent.com/"
        "PokeAPI/sprites/master/"
    )
    if image is not None:
        if not isinstance(image, str) or not image.startswith(prefix):
            raise ValueError("지원하지 않는 이미지 주소")

    return {
        "uid": uid, "name": name, "number": number,
        "level": level, "shiny": shiny, "image": image,
        "types": types, "rarity": rarity,
        "color": colors[rarity],
        "ball": ball[0], "ball_color": ball[1],
        "ball_mark": ball[2],
    }


st.markdown("""
<style>
.stApp {
    background:linear-gradient(145deg,#06142f,#12366a);
    color:white;
}
header[data-testid="stHeader"] {background:transparent}
h1,h2,h3 {color:white!important}
.block-container {padding-top:2.5rem}
div.stButton>button,div.stDownloadButton>button {
    background:#7dd3fc!important;
    color:#06142f!important;
    border:2px solid #e0f2fe!important;
    border-radius:14px!important;
    min-height:52px;
}
div.stButton>button p,div.stDownloadButton>button p {
    color:#06142f!important;font-weight:800!important;
}
div.stButton>button:hover {background:white!important}
.hero {
    text-align:center;font-size:clamp(28px,5vw,44px);
    font-weight:900;margin:25px 0 15px;color:white;
}
.subtitle {text-align:center;color:#c8ddfa;margin-bottom:30px}
.collection-box {
    padding:20px;border:1px solid #8abfff66;
    border-radius:20px;background:#ffffff0b;
    margin-bottom:15px;color:white;
}
.collection-box h3 {margin:0 0 12px}
.collection-box p {color:#c8ddfa}
.record {
    background:#ffffff0b;border-radius:15px;
    padding:14px;margin-bottom:16px;color:white;
}
</style>
""", unsafe_allow_html=True)

for key, value in {
    "page": "home",
    "current": None,
    "collection": [],
    "play_animation": False,
}.items():
    if key not in st.session_state:
        st.session_state[key] = value


def new_draw():
    try:
        with st.spinner("포켓몬을 찾는 중..."):
            pokemon = draw()

        st.session_state.current = pokemon
        st.session_state.collection.append(pokemon)
        st.session_state.page = "encounter"
        st.session_state.play_animation = True
        st.rerun()

    except (requests.RequestException, ValueError, KeyError, IndexError):
        st.error("불러오지 못했어요. 잠시 후 다시 눌러 주세요.")


main, right = st.columns([3, 1], gap="large")

with right:
    collection = st.session_state.collection
    shiny_count = sum(p["shiny"] for p in collection)
    unique_count = len({p["number"] for p in collection})

    st.markdown(
        f"""
        <div class="collection-box">
            <h3>📦 내 포켓몬 보관함</h3>
            <p>보관한 포켓몬: <b>{len(collection)}마리</b></p>
            <p>발견한 종류: <b>{unique_count}종</b></p>
            <p>✨ 이로치: <b>{shiny_count}마리</b></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("📦 보관함 들어가기", use_container_width=True):
        st.session_state.page = "collection"
        st.rerun()

    if st.button("🏠 홈으로", use_container_width=True):
        st.session_state.page = "home"
        st.rerun()

    save_data = json.dumps(
        {"version": 1, "pokemon": collection},
        ensure_ascii=False,
        indent=2,
    )

    st.download_button(
        "💾 저장 파일 다운로드",
        data=save_data,
        file_name="my_pokemon.json",
        mime="application/json",
        use_container_width=True,
    )

    with st.expander("📂 저장 파일 불러오기"):
        uploaded = st.file_uploader(
            "이전에 다운로드한 JSON 파일",
            type=["json"],
        )

        if st.button("불러오기", use_container_width=True):
            if uploaded is None:
                st.warning("저장 파일을 먼저 선택해 주세요.")
            else:
                try:
                    if uploaded.size > 10 * 1024 * 1024:
                        raise ValueError("파일 크기 초과")

                    saved = json.loads(uploaded.getvalue())
                    if saved.get("version") != 1:
                        raise ValueError("지원하지 않는 버전")

                    records = saved["pokemon"]
                    if not isinstance(records, list) or len(records) > 10000:
                        raise ValueError("기록 개수 오류")

                    restored = [
                        validate_saved_pokemon(item)
                        for item in records
                    ]

                    # 같은 저장 파일을 여러 번 불러와도 중복 추가 방지
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
                    ValueError, KeyError, TypeError,
                    StopIteration, AttributeError,
                ):
                    st.error("올바른 포켓몬 저장 파일인지 확인해 주세요.")

    st.caption(
        "뽑을 때마다 현재 접속 기록에 자동 보관돼요. "
        "접속 종료 전에 저장 파일을 다운로드해 주세요."
    )


with main:
    if st.session_state.page == "home":
        st.markdown(
            '<div class="hero">⚡ 랜덤 포켓몬 뽑기</div>'
            '<div class="subtitle">'
            '볼을 열어 새로운 포켓몬을 만나 보세요!'
            '</div>',
            unsafe_allow_html=True,
        )

        if st.button("🚀 들어가기", use_container_width=True):
            new_draw()

    elif st.session_state.page == "encounter":
        st.markdown(
            '<div class="hero">포켓몬이 나타났다!</div>',
            unsafe_allow_html=True,
        )

        play = st.session_state.play_animation
        st.session_state.play_animation = False

        show_encounter(
            st.session_state.current,
            animate=play,
        )

        st.caption("✅ 이 포켓몬은 보관함에 자동으로 저장됐어요.")

        a, b = st.columns(2)
        with a:
            if st.button("🎲 다시 뽑기", use_container_width=True):
                new_draw()
        with b:
            if st.button("🏠 돌아가기", use_container_width=True):
                st.session_state.page = "home"
                st.rerun()

    elif st.session_state.page == "collection":
        st.markdown(
            '<div class="hero">📦 내 포켓몬 보관함</div>',
            unsafe_allow_html=True,
        )

        if not st.session_state.collection:
            st.info("아직 포켓몬이 없어요. 홈에서 먼저 뽑아 보세요.")

        else:
            query = st.text_input("🔎 이름으로 검색")
            only_shiny = st.checkbox("✨ 이로치만 보기")
            order = st.selectbox(
                "정렬",
                ["최근에 뽑은 순", "레벨 높은 순", "도감 번호순"],
            )

            records = [
                p for p in st.session_state.collection
                if query.strip() in p["name"]
                and (not only_shiny or p["shiny"])
            ]

            if order == "레벨 높은 순":
                records.sort(key=lambda p: p["level"], reverse=True)
            elif order == "도감 번호순":
                records.sort(key=lambda p: p["number"])
            else:
                records.reverse()

            st.write(f"총 {len(records)}마리")

            # 보관함이 커져도 한 번에 너무 많이 출력하지 않도록 분할
            page_size = 12
            total_pages = max(
                1, (len(records) + page_size - 1) // page_size
            )
            page_number = st.selectbox(
                "페이지",
                range(1, total_pages + 1),
                key=f"collection_page_{total_pages}",
            )
            start = (page_number - 1) * page_size
            visible = records[start:start + page_size]

            columns = st.columns(3)

            for i, p in enumerate(visible):
                with columns[i % 3]:
                    if p["image"]:
                        st.image(p["image"], width=170)
                    else:
                        st.write("✨ 이미지 미제공")

                    shiny_label = "✨ 이로치" if p["shiny"] else "일반 색상"

                    st.markdown(
                        f"""
                        <div class="record">
                            <b>{html.escape(p["name"])}</b><br>
                            No. {p["number"]:04d} · Lv. {p["level"]}<br>
                            {html.escape(p["rarity"])} · {shiny_label}<br>
                            {html.escape(p["types"])}<br>
                            {html.escape(p["ball"])}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )


with st.expander("📖 뽑기 규칙"):
    st.write(
        "포켓몬은 API에 등록된 모든 종의 기본 형태 중 동일 확률로 뽑습니다. "
        "레벨은 1~100, 이로치 확률은 5%입니다. "
        "희귀도는 환상·전설 여부와 API의 포획률 수치로 구분합니다. "
        "몬스터볼 45%, 슈퍼볼 25%, 하이퍼볼 18%, "
        "프레미어볼 10%, 마스터볼 2%이며 볼은 연출용입니다. "
        "레벨·확률·희귀도 등급은 앱 자체 규칙입니다. "
        "기기의 동작 줄이기 설정이 켜져 있으면 애니메이션은 생략됩니다."
    )
