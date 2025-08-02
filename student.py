import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import random
import uuid  # ✅ for unique keys

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

# UI
st.title("🎓 CVV SmartExam - Student Panel")

name = st.text_input("Enter your full name").strip()
batch_data = db.reference("batches").get()
batch_options = list(batch_data.keys()) if batch_data else []
batch = st.selectbox("Select your batch", ["Select"] + batch_options)

if name and batch != "Select":
    subject_data = db.reference(f"questions/{batch}").get()
    if not subject_data:
        st.warning("⚠ No subjects available for this batch.")
        st.stop()

    subject = st.selectbox("Select subject", ["Select"] + list(subject_data.keys()))

    if subject != "Select":
        # 🔐 Prevent re-submission
        result_ref = db.reference(f"results/{batch}/{subject}/{name}")
        if result_ref.get():
            st.error("⚠ You have already submitted this exam. You can't attempt it again.")
            st.stop()

        questions = subject_data[subject]
        st.subheader(f"📘 {subject} Exam")
        st.markdown("---")

        # Randomize questions
        random.shuffle(questions)
        user_answers = {}

        for idx, q in enumerate(questions):
            question_id = str(uuid.uuid4())  # ✅ unique key to avoid reuse
            st.markdown(f"*Q{idx+1}. {q['question']}*")
            user_choice = st.radio("Choose one:", q['options'], key=question_id)
            user_answers[str(idx)] = {"question": q['question'], "selected": user_choice, "correct": q['answer']}

        if st.button("✅ Submit Exam"):
            correct = sum(1 for i in user_answers if user_answers[i]['selected'] == user_answers[i]['correct'])
            total = len(questions)
            details = []

            for ans in user_answers.values():
                details.append({
                    "question": ans["question"],
                    "your_answer": ans["selected"],
                    "correct_answer": ans["correct"],
                    "is_correct": ans["selected"] == ans["correct"]
                })

            # ✅ Save result to Firebase
            result_ref.set({
                "name": name,
                "subject": subject,
                "score": correct,
                "total": total,
                "details": details
            })

            st.success(f"🎉 Exam submitted! You scored {correct} out of {total}.")
            st.balloons()

            with st.expander("📊 View Your Answers"):
                for i, d in enumerate(details):
                    st.markdown(f"*Q{i+1}. {d['question']}*")
                    st.markdown(f"- Your answer: {d['your_answer']}")
                    if d['is_correct']:
                        st.markdown("- ✅ Correct!")
                    else:
                        st.markdown(f"- ❌ Correct answer: {d['correct_answer']}")
                    st.markdown("---")