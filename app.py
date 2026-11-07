
import streamlit as st
import streamlit.components.v1 as components
import random

st.set_page_config(
    page_title="환영합니다!",
    page_icon="🎆",
    layout="centered"
)

# 페이지 상태
if "entered" not in st.session_state:
    st.session_state.entered = False

if "effect" not in st.session_state:
    st.session_state.effect = "fireworks"

# CSS 스타일
st.markdown("""
<style>
.stApp {
    background: linear-gradient(145deg, #071633, #102D60);
    color: white;
}

h1, h2, h3, p {
    color: white !important;
}

.block-container {
    padding-top: 5rem;
}

/* 모든 버튼의 가독성 */
div.stButton > button {
    background-color: #7DD3FC !important;
    color: #06152F !important;
    border: 2px solid #FFFFFF !important;
    border-radius: 16px !important;
    font-size: 22px !important;
    font-weight: 800 !important;
    padding: 14px 25px !important;
    min-height: 65px !important;
    box-shadow: 0 5px 20px rgba(0,0,0,0.3);
    transition: 0.2s;
}

div.stButton > button p {
    color: #06152F !important;
}

div.stButton > button:hover {
    background-color: #FFFFFF !important;
    color: #06152F !important;
    transform: scale(1.04);
}

div.stButton > button:focus {
    color: #06152F !important;
}
</style>
""", unsafe_allow_html=True)


def celebration(effect):
    """다양한 축하 애니메이션"""

    html = """
    <html>
    <head>
    <style>
    body {
        margin: 0;
        overflow: hidden;
        background: transparent;
    }
    canvas {
        width: 100%;
        height: 100%;
        display: block;
    }
    </style>
    </head>
    <body>
    <canvas id="canvas"></canvas>

    <script>
    const canvas = document.getElementById("canvas");
    const ctx = canvas.getContext("2d");

    function resize() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    resize();
    window.addEventListener("resize", resize);

    const effect = "EFFECT_NAME";
    const particles = [];

    const colors = [
        "#FF4D6D", "#FFD166", "#06D6A0",
        "#4CC9F0", "#B388FF", "#FFFFFF"
    ];

    function rand(min, max) {
        return Math.random() * (max - min) + min;
    }

    function createParticles() {
        particles.length = 0;

        if (effect === "fireworks") {
            for (let j = 0; j < 7; j++) {
                const cx = rand(60, canvas.width - 60);
                const cy = rand(50, canvas.height * 0.65);

                for (let i = 0; i < 85; i++) {
                    const angle = Math.random() * Math.PI * 2;
                    const speed = rand(1, 5);

                    particles.push({
                        x: cx,
                        y: cy,
                        vx: Math.cos(angle) * speed,
                        vy: Math.sin(angle) * speed,
                        size: rand(2, 4),
                        color: colors[Math.floor(Math.random() * colors.length)],
                        life: rand(60, 120),
                        gravity: 0.025,
                        type: "circle"
                    });
                }
            }
        }

        else if (effect === "confetti") {
            for (let i = 0; i < 220; i++) {
                particles.push({
                    x: rand(0, canvas.width),
                    y: rand(-canvas.height, 0),
                    vx: rand(-1.5, 1.5),
                    vy: rand(1, 3.5),
                    size: rand(4, 10),
                    color: colors[Math.floor(Math.random() * colors.length)],
                    life: 500,
                    gravity: 0,
                    type: "rect"
                });
            }
        }

        else if (effect === "stars") {
            for (let i = 0; i < 160; i++) {
                particles.push({
                    x: rand(0, canvas.width),
                    y: rand(0, canvas.height),
                    vx: rand(-0.4, 0.4),
                    vy: rand(-0.6, 0.6),
                    size: rand(1, 5),
                    color: colors[Math.floor(Math.random() * colors.length)],
                    life: 500,
                    gravity: 0,
                    type: "star"
                });
            }
        }

        else if (effect === "balloons") {
            for (let i = 0; i < 55; i++) {
                particles.push({
                    x: rand(0, canvas.width),
                    y: rand(canvas.height, canvas.height * 2),
                    vx: rand(-0.5, 0.5),
                    vy: rand(-2.5, -1),
                    size: rand(10, 23),
                    color: colors[Math.floor(Math.random() * colors.length)],
                    life: 600,
                    gravity: 0,
                    type: "balloon"
                });
            }
        }
    }

    createParticles();

    function drawStar(x, y, radius, color) {
        ctx.fillStyle = color;
        ctx.beginPath();

        for (let i = 0; i < 10; i++) {
            const r = i % 2 === 0 ? radius : radius * 0.4;
            const angle = i * Math.PI / 5 - Math.PI / 2;
            const px = x + Math.cos(angle) * r;
            const py = y + Math.sin(angle) * r;

            if (i === 0) ctx.moveTo(px, py);
            else ctx.lineTo(px, py);
        }

        ctx.closePath();
        ctx.fill();
    }

    let frame = 0;

    function animate() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        for (const p of particles) {
            if (p.life <= 0) continue;

            p.x += p.vx;
            p.y += p.vy;
            p.vy += p.gravity;
            p.life--;

            ctx.globalAlpha = Math.min(1, p.life / 30);
            ctx.fillStyle = p.color;

            if (p.type === "circle") {
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();
            }

            else if (p.type === "rect") {
                ctx.save();
                ctx.translate(p.x, p.y);
                ctx.rotate(frame * 0.025 + p.x);
                ctx.fillRect(-p.size/2, -p.size/2, p.size, p.size);
                ctx.restore();
            }

            else if (p.type === "star") {
                drawStar(p.x, p.y, p.size * 2, p.color);
            }

            else if (p.type === "balloon") {
                ctx.beginPath();
                ctx.ellipse(
                    p.x, p.y,
                    p.size * 0.75, p.size,
                    0, 0, Math.PI * 2
                );
                ctx.fill();

                ctx.strokeStyle = "#FFFFFF88";
                ctx.beginPath();
                ctx.moveTo(p.x, p.y + p.size);
                ctx.lineTo(p.x, p.y + p.size + 18);
                ctx.stroke();
            }
        }

        ctx.globalAlpha = 1;
        frame++;

        if (frame < 420) {
            requestAnimationFrame(animate);
        }
    }

    animate();
    </script>
    </body>
    </html>
    """

    html = html.replace("EFFECT_NAME", effect)

    components.html(
        html,
        height=390,
        scrolling=False
    )


# 시작 화면
if not st.session_state.entered:

    st.markdown(
        """
        <h1 style="
            text-align:center;
            font-size:55px;
            margin-top:50px;
            font-weight:900;
        ">
            WELCOME
        </h1>

        <p style="
            text-align:center;
            font-size:20px;
            color:#D6E8FF !important;
            margin-bottom:50px;
        ">
            아래 버튼을 눌러 입장하세요!
        </p>
        """,
        unsafe_allow_html=True
    )

    left, center, right = st.columns([1, 2, 1])

    with center:
        if st.button(
            "🚀 들어가기",
            use_container_width=True
        ):
            st.session_state.effect = random.choice([
                "fireworks",
                "confetti",
                "stars",
                "balloons"
            ])
            st.session_state.entered = True
            st.rerun()


# 환영 화면
else:

    st.markdown(
        """
        <h1 style="
            text-align:center;
            font-size:52px;
            font-weight:900;
            margin-top:10px;
            text-shadow:0 0 25px #66CCFF;
        ">
            환영합니다!!
        </h1>

        <p style="
            text-align:center;
            font-size:19px;
            color:#D6E8FF !important;
        ">
            즐거운 시간을 보내세요!
        </p>
        """,
        unsafe_allow_html=True
    )

    celebration(st.session_state.effect)

    left, center, right = st.columns([1, 2, 1])

    with center:
        if st.button(
            "🏠 돌아가기",
            use_container_width=True
        ):
            st.session_state.entered = False
            st.rerun()
