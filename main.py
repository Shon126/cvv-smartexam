import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import random

# ✅ Firebase Initialization
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cvv-smartexam-v2-default-rtdb.asia-southeast1.firebasedatabase.app'
    })

# 🌟 Streamlit Page Config
st.set_page_config(page_title="CVV SmartExam", page_icon="🧠", layout="centered")
st.title("💡 CVV SmartExam")

# 🔘 Role Selection
role = st.selectbox("Select your role", ["Student", "Teacher", "Admin"])

# 🎓 STUDENT PANEL
if role == "Student":
    st.header("🎓 Student Portal")
    student_name = st.text_input("Enter your name").strip()
    batch_data = db.reference("batches").get()
    batch_options = list(batch_data.keys()) if batch_data else []
    selected_batch = st.selectbox("Select your Batch", batch_options)

    if student_name and selected_batch:
        subject_data = batch_data[selected_batch]
        subject_options = list(subject_data.keys()) if subject_data else []
        selected_subject = st.selectbox("Choose Subject", subject_options)

        if selected_subject:
            st.success(f"Welcome {student_name}! You're taking the {selected_subject} exam 🎯")
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
                    st.markdown(f"Q{idx+1}: {q['question']}")
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

                    db.reference(f"results/{selected_batch}/{selected_subject}/{student_name}").set({
                        "score": score,
                        "total": total
                    })

                    st.success(f"🎉 You scored {score} out of {total}!")

                    st.markdown("### 📖 Your Answers")
                    for i, qid in enumerate(question_ids):
                        r = result_summary[qid]
                        st.markdown(f"Q{i+1}: {r['question']}")
                        st.markdown(f"- Your Answer: {r['your_answer']}")
                        if not r['is_correct']:
                            st.markdown(f"- ❌ Correct Answer: {r['correct_answer']}")
                        else:
                            st.markdown(f"- ✅ Correct!")
            else:
                st.warning("No questions available for this subject yet.")

# 👩‍🏫 TEACHER PANEL
elif role == "Teacher":
    st.header("👩‍🏫 Teacher Panel")
    teacher_name = st.text_input("Enter your name").strip()
    teacher_pass = st.text_input("Enter your password", type="password")

    if teacher_name and teacher_pass:
        ref = db.reference(f"teachers/{teacher_name}")
        data = ref.get()

        if data and data.get("password") == teacher_pass:
            st.success(f"Welcome, {teacher_name}! 🌟")

            batch_data = db.reference("batches").get()
            batch_options = list(batch_data.keys()) if batch_data else []
            selected_batch = st.selectbox("Select Batch or Create New", ["➕ Create New"] + batch_options)

            new_batch = ""
            if selected_batch == "➕ Create New":
                new_batch = st.text_input("Enter new batch name (e.g., BCA2025)").strip()
                if st.button("Create Batch") and new_batch:
                    db.reference(f"batches/{new_batch}").set({})
                    st.success(f"✅ Batch '{new_batch}' created!")
            else:
                new_batch = selected_batch

            if new_batch:
                subject_data = db.reference(f"batches/{new_batch}").get()
                subject_options = list(subject_data.keys()) if subject_data else []
                selected_subject = st.selectbox("Select Subject or Create New", ["➕ Create New"] + subject_options)

                new_subject = ""
                if selected_subject == "➕ Create New":
                    new_subject = st.text_input("Enter new subject name (e.g., Python)").strip()
                    if st.button("Create Subject") and new_subject:
                        db.reference(f"batches/{new_batch}/{new_subject}/questions").set({})
                        st.success(f"✅ Subject '{new_subject}' created!")
                else:
                    new_subject = selected_subject

                if new_subject:
                    st.subheader(f"📄 Managing: {new_batch} > {new_subject}")

                    question = st.text_area("Enter Question").strip()
                    options = [st.text_input(f"Option {i+1}", key=f"opt_{i}") for i in range(4)]
                    correct = st.selectbox("Select Correct Answer", options)

                    if st.button("Add Question"):
                        if question and all(options) and correct:
                            q_ref = db.reference(f"batches/{new_batch}/{new_subject}/questions").push()
                            q_ref.set({
                                "question": question,
                                "options": options,
                                "answer": correct
                            })
                            st.success("✅ Question added!")
                        else:
                            st.error("❌ Please fill all fields before adding.")

                    st.markdown("### 👁 View & Manage Questions")
                    q_data = db.reference(f"batches/{new_batch}/{new_subject}/questions").get()
                    if q_data:
                        for qid, qinfo in q_data.items():
                            with st.expander(qinfo['question']):
                                for i, opt in enumerate(qinfo['options']):
                                    st.write(f"- {opt}")
                                st.markdown(f"✅ Correct Answer: {qinfo['answer']}")
                                if st.button(f"🗑 Delete this question", key=qid):
                                    db.reference(f"batches/{new_batch}/{new_subject}/questions/{qid}").delete()
                                    st.warning("❌ Question deleted! Please refresh to update.")
                    else:
                        st.info("No questions yet.")

                    st.markdown("### 📊 View Student Results")
                    result_ref = db.reference(f"results/{new_batch}/{new_subject}")
                    result_data = result_ref.get()
                    if result_data:
                        for student, r in result_data.items():
                            st.markdown(f"👤 {student} — Score: {r['score']} / {r['total']}")
                    else:
                        st.info("No student results yet.")

                    if st.button("🔁 Reset Results for this Subject"):
                        result_ref.delete()
                        st.success("✅ Results cleared!")
        else:
            st.error("Invalid name or password ❌")

# 🛡 ADMIN PANEL
elif role == "Admin":
    st.header("🛡 Admin Panel")
    admin_pass = st.text_input("Enter Admin Password", type="password")
    if admin_pass == "nohs126":
        st.success("Welcome, Admin 👑💙")

        st.header("👩‍🏫 All Registered Teachers")
        teachers = db.reference("teachers").get()
        if teachers:
            for name, details in teachers.items():
                with st.expander(f"🧑‍🏫 {name}"):
                    st.write(f"Current Password: {details.get('password', 'Not set')}")
                    new_pass = st.text_input(f"Reset password for {name}", key=f"pass_{name}")
                    if st.button(f"Update Password for {name}", key=f"btn_{name}"):
                        if new_pass:
                            db.reference(f"teachers/{name}/password").set(new_pass)
                            st.success(f"✅ Password updated for {name}")
                        else:
                            st.warning("⚠ Please enter a new password before updating.")
        else:
            st.info("ℹ No teachers registered yet.")

        st.header("➕ Add New Teacher")
        new_teacher = st.text_input("👤 Enter New Teacher Name")
        first_time_pass = st.text_input("🔑 Set Initial Password", type="password")
        if st.button("Add Teacher"):
            if new_teacher and first_time_pass:
                teacher_ref = db.reference(f"teachers/{new_teacher}")
                if teacher_ref.get():
                    st.warning("⚠ This teacher already exists.")
                else:
                    teacher_ref.set({"password": first_time_pass})
                    st.success(f"✅ Teacher '{new_teacher}' added successfully!")
            else:
                st.warning("⚠ Please enter both name and password.")

        st.header("❌ Remove Teacher")
        teacher_names = list(teachers.keys()) if teachers else []
        teacher_to_remove = st.selectbox("Select teacher to remove", teacher_names)
        if st.button("Remove Selected Teacher"):
            db.reference(f"teachers/{teacher_to_remove}").delete()
            st.error(f"🚫 Teacher '{teacher_to_remove}' removed.")

        st.header("🏫 Batches & Subjects")
        batches = db.reference("batches").get()
        if batches:
            for batch_name, subjects in batches.items():
                with st.expander(f"🎓 {batch_name}"):
                    for subject_name, subject_data in subjects.items():
                        st.subheader(f"📚 {subject_name}")
                        questions = subject_data.get("questions", {})
                        if questions:
                            for qid, qdata in questions.items():
                                st.markdown(f"- Q: {qdata.get('question', 'N/A')}")
                                st.markdown(f"✅ Answer: {qdata.get('answer', 'N/A')}")
                                if st.button("❌ Delete this question", key=f"{qid}{batch_name}{subject_name}"):
                                    db.reference(f"batches/{batch_name}/{subject_name}/questions/{qid}").delete()
                                    st.warning("❌ Question deleted. Please refresh to see updates.")
                        else:
                            st.write("No questions found in this subject.")

                        if st.button(f"🗑 Delete Subject '{subject_name}'", key=f"del_subject_{batch_name}_{subject_name}"):
                            db.reference(f"batches/{batch_name}/{subject_name}").delete()
                            st.warning(f"🗑 Subject '{subject_name}' deleted from batch '{batch_name}'.")

                    if st.button(f"🗑 Delete Entire Batch '{batch_name}'", key=f"del_batch_{batch_name}"):
                        db.reference(f"batches/{batch_name}").delete()
                        st.error(f"🚫 Batch '{batch_name}' deleted completely.")
        else:
            st.info("ℹ No batches created yet.")
    elif admin_pass:
        st.error("Wrong password, cutie ❌")