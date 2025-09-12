import streamlit as st

# Streamlit 세션 상태 초기화
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False


# 로그인 함수 정의
def login():

    if id == 'admin' and pw == 'password' :  # 예시로 ID와 PW를 'admin'과 'password'로 설정
        st.session_state["logged_in"] = True
        st.success("로그인에 성공했습니다!")
        st.rerun()
    else:
        st.error("ID 또는 Password가 올바르지 않습니다.")

# 로그인 화면
if not st.session_state["logged_in"]:
    st.title("Login",help="if you want to see the logged-in version...enter that(ID: admin, password: password)")
    id = st.text_input("ID")
    pw = st.text_input("Password", type="password")
    if st.button("LOGIN"):
        login()
