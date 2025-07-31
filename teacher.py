# teacher.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# Firebase Init
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://your-database-url.firebaseio.com/'  # CHANGE THIS ❤
    })

# 🌈 Page Config
st.set_page_config(page_title="CVV SmartExam - Teacher", page_icon="👩‍🏫", layout="centered")

# 💄 UI Styling
st.markdown("""
    <style>
    .main {
        background-color: #f3f4f6;
        padding: 20px;
        border-radius: 12px;
    }
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        color: #222;
    }
    .stTextInput>div>div>input,
    .stTextArea textarea {
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #ccc;
        font-size: 16px;
    }
    .stButton > button {
        background-color: #2f855a;
        color: white;
        padding: 10px 20px;
        border-radius: 10px;
        border: none;
        font-size: 16px;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# 🔐 Teacher Login
st.title("👩‍🏫 CVV SmartExam - Teacher Panel")

password = st.text_input("Enter Teacher Password", type="password")
if password != "cvv123":
    st.warning("Please enter the correct password to continue.")
    st.stop()

# 🎓 Select Batch & Subject
batch = st.text_input("Enter Batch (e.g., BCA2025)")
subject = st.text_input("Enter Subject (e.g., Python)")

if batch and subject:
    st.success(f"Managing: {batch} > {subject}")

    # 📝 Add Questions
    st.subheader("➕ Add a New Question")
    question = st.text_area("Question Text")
    options = []
    for i in range(4):
        options.append(st.text_input(f"Option {i + 1}", key=f"opt_{i}"))

    correct_answer = st.selectbox("Select the Correct Answer", options)

    if st.button("Add Question"):
        if question and all(options) and correct_answer:
            ref = db.reference(f"batches/{batch}/{subject}/questions")
            new_q_ref = ref.push()
            new_q_ref.set({
                "question": question,
                "options": options,
                "answer": correct_answer
            })
            st.success("✅ Question added successfully!")
        else:
            st.error("❗ Please fill all fields before adding the question.")

    # 📊 View Results
    st.subheader("📋 View Student Results")
    results_ref = db.reference(f"results/{batch}/{subject}")
    results_data = results_ref.get()

    if results_data:
        for student, data in results_data.items():
            st.markdown(f"👤 {student}** — Score: {data['score']} / {data['total']}")
    else:
        st.info("No results found yet.")