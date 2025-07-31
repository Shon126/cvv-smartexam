# student.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import random

# Firebase Init
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://your-database-url.firebaseio.com/'  # CHANGE THIS ❤
    })

# 🌈 Set Page Config
st.set_page_config(page_title="CVV SmartExam - Student", page_icon="🧑‍🎓", layout="centered")

# 💅 UI Styling
st.markdown("""
    <style>
    .main {
        background: linear-gradient(to right, #fdfbfb, #ebedee);
        padding: 20px;
        border-radius: 12px;
    }
    h1, h2, h3 {
        font-family: 'Segoe UI', sans-serif;
        color: #333;
    }
    .stButton > button {
        background-color: #4CAF50;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        border: none;
        font-size: 16px;
        margin-top: 10px;
    }
    .stTextInput>div>div>input {
        padding: 10px;
        border-radius: 8px;
        border: 1px solid #ccc;
    }
    .stSelectbox>div>div {
        padding: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# 🎓 Title
st.title("🎓 CVV SmartExam - Student Panel")

# 🧑‍🎓 Student Info Inputs
name = st.text_input("Enter your name")
batch = st.selectbox("Select your batch", list((db.reference("batches").get() or {}).keys()))

if batch:
    subjects_ref = db.reference(f"batches/{batch}")
    subjects = list(subjects_ref.get().keys())
    if subjects:
        subject = st.selectbox("Select subject", subjects)
    else:
        st.warning("No subjects found in this batch yet.")
        subject = None
else:
    subject = None

# 🚀 Load Questions
if st.button("Start Exam") and name and batch and subject:
    questions_ref = db.reference(f"batches/{batch}/{subject}/questions")
    questions_data = questions_ref.get()

    if not questions_data:
        st.warning("No questions available for this subject 💔")
    else:
        questions = list(questions_data.items())
        random.shuffle(questions)
        score = 0
        user_answers = {}

        st.subheader(f"📝 Answer the following questions:")

        for i, (qid, qdata) in enumerate(questions, start=1):
            st.write(f"{i}. {qdata['question']}")
            answer = st.radio(
                f"Your Answer (Q{i})", qdata['options'], key=f"q_{i}"
            )
            user_answers[qid] = answer

        if st.button("Submit Exam"):
            result_ref = db.reference("results").child(batch).child(subject).child(name)
            correct_count = 0
            total = len(questions)

            results_to_store = {}

            for qid, qdata in questions_data.items():
                correct_ans = qdata['answer']
                chosen_ans = user_answers.get(qid, "")
                results_to_store[qid] = {
                    "question": qdata['question'],
                    "your_answer": chosen_ans,
                    "correct_answer": correct_ans,
                    "is_correct": chosen_ans == correct_ans
                }
                if chosen_ans == correct_ans:
                    correct_count += 1

            result_ref.set({
                "score": correct_count,
                "total": total,
                "details": results_to_store
            })

            st.success(f"✅ You scored {correct_count} out of {total}")
            st.write("📊 Detailed Review:")
            for i, (qid, res) in enumerate(results_to_store.items(), start=1):
                st.write(f"{i}. {res['question']}")
                st.write(f"- Your Answer: {res['your_answer']}")
                st.write(f"- Correct Answer: {res['correct_answer']}")
                if res['is_correct']:
                    st.success("✔ Correct")
                else:
                    st.error("❌ Incorrect")
else:
    st.info("Please fill all fields and press Start Exam.")