
import streamlit as st

st.set_page_config(
    page_title="환영합니다",
    page_icon="🎆",
    layout="centered"
)

# 배경 및 글씨 디자인
st.markdown("""
<style>
.stApp {
    background-color: #081B42;
    color: white;
}

h1, h2, h3, p {
    color: white !important;
}

.stButton > button {
    background-color: white;
    color: #081B42;
    border: none;
    border-radius: 14px;
    padding: 15px 45px;
    font-size: 22px;
    font-weight: bold;
}

.stButton > button:hover {
    background-color: #DCE8FF;
    color: #081B42;
}
</style>
""", unsafe_allow_html=True)

# 버튼 클릭 상태 저장
if "entered" not in st.session_state:
    st.session_state.entered = False

st.write("")
st.write("")
st.write("")

if not st.session_state.entered:
    st.markdown(
        "<h1 style='text-align:center;'>WELCOME</h1>",
        unsafe_allow_html=True
    )

    st.write("")

    _, center, _ = st.columns([1, 2, 1])

    with center:
        if st.button("들어가기", use_container_width=True):
            st.session_state.entered = True
            st.rerun()

else:
    st.markdown(
        """
        <h1 style='text-align:center;
                   font-size:55px;
                   margin-top:80px;'>
            환영합니다!!
        </h1>
        """,
        unsafe_allow_html=True
    )

    # 폭죽 효과
    st.balloons()
    st.snow()
