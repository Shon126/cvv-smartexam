import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import random

# Firebase Init
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"],
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        "universe_domain": st.secrets["firebase"]["universe_domain"]
    })
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://cvv-smartexam-v2-default-rtdb.asia-southeast1.firebasedatabase.app"
    })

# Streamlit UI
st.title("🎓 CVV SmartExam - Student Panel")

name = st.text_input("Enter your name").strip()
batch_data = db.reference("batches").get()
batch_options = list(batch_data.keys()) if batch_data else []
batch = st.selectbox("Select your batch", ["Select"] + batch_options)

if name and batch != "Select":
    subject_data = db.reference(f"questions/{batch}").get()
    if not subject_data:
        st.warning("⚠ No subjects available for this batch yet.")
        st.stop()

    subject = st.selectbox("Select subject", ["Select"] + list(subject_data.keys()))

    if subject != "Select":
        # 🔐 Check if student already submitted
        result_check = db.reference(f"results/{batch}/{subject}/{name}").get()
        if result_check:
            st.error("❌ You have already submitted this exam. Only one attempt allowed.")
            st.stop()

        questions = subject_data[subject]
        st.markdown("---")
        st.subheader(f"📘 Exam: {subject}")

        user_answers = {}
        for i, q in enumerate(questions):
            options = q["options"]
            user_choice = st.radio(f"{i+1}. {q['question']}", options, key=i)
            user_answers[str(i)] = user_choice

        if st.button("✅ Submit Exam"):
            correct_count = 0
            wrong_count = 0
            total = len(questions)
            correct_answers = []

            for i, q in enumerate(questions):
                correct = q["answer"]
                user = user_answers[str(i)]
                correct_answers.append({
                    "question": q["question"],
                    "your_answer": user,
                    "correct_answer": correct,
                    "is_correct": user == correct
                })
                if user == correct:
                    correct_count += 1
                else:
                    wrong_count += 1

            # Save result to Firebase
            db.reference(f"results/{batch}/{subject}/{name}").set({
                "name": name,
                "subject": subject,
                "score": correct_count,
                "total": total,
                "details": correct_answers
            })

            st.success("🎉 Exam submitted successfully!")
            st.balloons()
            st.markdown(f"*Your Score:* {correct_count} / {total}")

            # Show detailed result
            with st.expander("📊 View Answers"):
                for i, q in enumerate(correct_answers):
                    st.markdown(f"*Q{i+1}. {q['question']}*")
                    st.markdown(f"- Your answer: {q['your_answer']}")
                    st.markdown(f"- Correct answer: {q['correct_answer']}")
                    st.markdown("---")