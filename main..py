# main.py
import streamlit as st
import os

st.set_page_config(page_title="CVV SmartExam", page_icon="🎓", layout="centered")

st.title("🎓 Welcome to CVV SmartExam")
st.markdown("#### Please select your role to continue:")

role = st.selectbox("I am a...", ["Select", "Student", "Teacher", "Admin"])

if role == "Student":
    st.success("Redirecting to Student Panel...")
    os.system("streamlit run student.py")

elif role == "Teacher":
    st.success("Redirecting to Teacher Panel...")
    os.system("streamlit run teacher.py")

elif role == "Admin":
    st.success("Redirecting to Admin Panel...")
    os.system("streamlit run admin.py")