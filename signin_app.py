import streamlit as st

# Sidebar buttons
sign_in = st.sidebar.button("Sign In", key="signin_button")
sign_up = st.sidebar.button("Sign Up", key="signup_button")
signin = False
if sign_in or signin == False and not sign_up:
    st.title("Sign In")
    email = st.text_input("Email",key="email")
    password = st.text_input("Password", type="password",key="password")
    sign_in_button = st.button("Sign In")
    if sign_in_button:
        # Here you would typically check the credentials against a database
        signin = True
        st.session_state["credentials_ready"]=True
        st.success("Sign In successful!")
    if st.session_state.get("credentials_ready"):
        email = st.session_state["email"]
        password = st.session_state["password"]
        st.write(f"Email: {email}")
        
        