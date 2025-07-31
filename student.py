import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import random

# ✅ Initialize Firebase once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cvv-smartexam-v2-default-rtdb.firebaseio.com'
    })

# 🌸 Streamlit Page Setup
st.set_page_config(page_title="CVV SmartExam - Student", page_icon="🎓", layout="centered")
st.title("🎓 CVV SmartExam - Student Portal")

# 👤 Student Login
student_name = st.text_input("Enter your name").strip()
batch_data = db.reference("batches").get()
batch_options = list(batch_data.keys()) if batch_data else []
selected_batch = st.selectbox("Select your Batch", batch_options)

if student_name and selected_batch:
    subject_data = batch_data[selected_batch]
    subject_options = list(subject_data.keys()) if subject_data else []

    selected_subject = st.selectbox("Choose Subject", subject_options)

    if selected_subject:
        st.success(f"Welcome {student_name}! You're taking the *{selected_subject}* exam 🎯")

        # 🔍 Load Questions
        questions_ref = db.reference(f"batches/{selected_batch}/{selected_subject}/questions")
        questions = questions_ref.get()

        if questions:
            st.markdown("---")
            st.markdown("### 📋 Questions")

            question_ids = list(questions.keys())
            random.shuffle(question_ids)

            answers = {}
            for idx, qid in enumerate(question_ids):
                q = questions[qid]
                st.markdown(f"*Q{idx+1}: {q['question']}*")
                answers[qid] = st.radio("Select your answer:", q['options'], key=qid)

            if st.button("🎯 Submit Answers"):
                score = 0
                total = len(question_ids)
                result_summary = {}

                for qid in question_ids:
                    correct = questions[qid]['answer']
                    chosen = answers[qid]
                    result_summary[qid] = {
                        "question": questions[qid]['question'],
                        "your_answer": chosen,
                        "correct_answer": correct,
                        "is_correct": (chosen == correct)
                    }
                    if chosen == correct:
                        score += 1

                # ✅ Save Result
                db.reference(f"results/{selected_batch}/{selected_subject}/{student_name}").set({
                    "score": score,
                    "total": total
                })

                st.success(f"🎉 You scored {score} out of {total}!")

                # 👁 Show Detailed Result
                st.markdown("### 📖 Your Answers")
                for i, qid in enumerate(question_ids):
                    r = result_summary[qid]
                    st.markdown(f"*Q{i+1}: {r['question']}*")
                    st.markdown(f"- Your Answer: {r['your_answer']}")
                    if not r['is_correct']:
                        st.markdown(f"- ❌ Correct Answer: {r['correct_answer']}")
                    else:
                        st.markdown(f"- ✅ Correct!")

        else:
            st.warning("No questions available for this subject yet.")