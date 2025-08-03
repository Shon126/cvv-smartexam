import streamlit as st
import firebase_admin
from firebase_admin import credentials, db
import random

if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),  # Important for multiline key
        "client_email": st.secrets["firebase"]["client_email"],
        "client_id": st.secrets["firebase"]["client_id"],
        "auth_uri": st.secrets["firebase"]["auth_uri"],
        "token_uri": st.secrets["firebase"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["firebase"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["firebase"]["client_x509_cert_url"],
        "universe_domain": st.secrets["firebase"]["universe_domain"]
    })
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cvv-smartexam-v2-default-rtdb.asia-southeast1.firebasedatabase.app'
    })
# 🌐 Streamlit Config
st.set_page_config(page_title="CVV SmartExam Portal", page_icon="📘", layout="centered")
st.title("📘 Welcome to CVV SmartExam Portal")

# 🎭 Role Selector
role = st.selectbox("Who are you?", ["Select Role", "Student", "Teacher", "Admin"])

# 🎓 STUDENT PANEL
def student_panel():
    st.header("🎓 Student Panel")
    student_name = st.text_input("Enter your name").strip()

    batch_data = db.reference("batches").get()
    batch_options = list(batch_data.keys()) if batch_data else []
    selected_batch = st.selectbox("Select your Batch", batch_options)

    if student_name and selected_batch:
        # ✅ Load subjects from teacher-added question sets
        subject_data = db.reference(f"batches/{selected_batch}").get()
        subject_options = list(subject_data.keys()) if subject_data else []
        selected_subject = st.selectbox("Choose Subject", subject_options)

        if selected_subject:
            # 🚫 Check if already attempted
            result_ref = db.reference(f"results/{selected_batch}/{selected_subject}/{student_name}")
            if result_ref.get():
                st.error("❌ You have already submitted this exam. Retaking is not allowed.")
                st.stop()

            st.success(f"Welcome {student_name}! You're taking the {selected_subject} exam 🎯")

            questions_ref = db.reference(f"batches/{selected_batch}/{selected_subject}/questions")
            questions = questions_ref.get()

            if questions:
                st.markdown("---")
                st.markdown("### 📋 Questions")
                question_keys = list(questions.keys())
                random.shuffle(question_keys)
                answers = {}
                result_summary = {}

                for idx, qid in enumerate(question_keys):
                    q = questions[qid]
                    question_label = f"Q{idx+1}: {q['question']}"
                    unique_key = f"{student_name}{selected_batch}{selected_subject}{qid}{idx}"
                    answers[qid] = st.radio(question_label, q['options'], key=unique_key)

                if st.button("🎯 Submit Answers"):
                    if result_ref.get():
                        st.error("❌ Submission blocked. You have already taken this exam.")
                        st.stop()

                    score = 0
                    total = len(answers)

                    for qid in answers:
                        correct = questions[qid]['answer']
                        chosen = answers[qid]
                        is_correct = chosen == correct

                        result_summary[qid] = {
                            "question": questions[qid]['question'],
                            "your_answer": chosen,
                            "correct_answer": correct,
                            "is_correct": is_correct
                        }

                        if is_correct:
                            score += 1

                    # 💾 Save result to Firebase
                    result_ref.set({
                        "name": student_name,
                        "subject": selected_subject,
                        "score": score,
                        "total": total,
                        "details": list(result_summary.values())
                    })

                    st.success(f"✅ Submitted! You scored {score} out of {total}.")
                    st.balloons()

                    with st.expander("📊 View Your Answers"):
                        for i, r in enumerate(result_summary.values()):
                            st.markdown(f"Q{i+1}: {r['question']}")
                            st.markdown(f"- Your Answer: {r['your_answer']}")
                            if not r['is_correct']:
                                st.markdown(f"- ❌ Correct Answer: {r['correct_answer']}")
                            else:
                                st.markdown("- ✅ Correct!")
                            st.markdown("---")
            else:
                st.warning("🚫 No questions found for this subject.")
# 👩‍🏫 TEACHER PANEL
def student_panel():
    st.header("🎓 Student Panel")
    student_name = st.text_input("Enter your name").strip()

    batch_data = db.reference("batches").get()
    batch_options = list(batch_data.keys()) if batch_data else []
    selected_batch = st.selectbox("Select your Batch", batch_options)

    if student_name and selected_batch:
        # ✅ Load subjects from teacher-added question sets
        subject_data = db.reference(f"batches/{selected_batch}").get()
        subject_options = list(subject_data.keys()) if subject_data else []
        selected_subject = st.selectbox("Choose Subject", subject_options)

        if selected_subject:
            # 🚫 Check if already attempted
            result_ref = db.reference(f"results/{selected_batch}/{selected_subject}/{student_name}")
            if result_ref.get():
                st.error("❌ You have already submitted this exam. Retaking is not allowed.")
                st.stop()

            st.success(f"Welcome {student_name}! You're taking the {selected_subject} exam 🎯")

            questions_ref = db.reference(f"batches/{selected_batch}/{selected_subject}/questions")
            questions = questions_ref.get()

            # 🔧 Check for empty or placeholder-only subject
            if questions:
                # 🔧 Remove placeholders if they exist
                questions = {k: v for k, v in questions.items() if k != "_placeholder_"}

            if questions:
                st.markdown("---")
                st.markdown("### 📋 Questions")
                question_keys = list(questions.keys())
                random.shuffle(question_keys)
                answers = {}
                result_summary = {}

                for idx, qid in enumerate(question_keys):
                    q = questions[qid]
                    question_label = f"Q{idx+1}: {q['question']}"
                    unique_key = f"{student_name}{selected_batch}{selected_subject}{qid}{idx}"
                    answers[qid] = st.radio(question_label, q['options'], key=unique_key)

                if st.button("🎯 Submit Answers"):
                    if result_ref.get():
                        st.error("❌ Submission blocked. You have already taken this exam.")
                        st.stop()

                    score = 0
                    total = len(answers)

                    for qid in answers:
                        correct = questions[qid]['answer']
                        chosen = answers[qid]
                        is_correct = chosen == correct

                        result_summary[qid] = {
                            "question": questions[qid]['question'],
                            "your_answer": chosen,
                            "correct_answer": correct,
                            "is_correct": is_correct
                        }

                        if is_correct:
                            score += 1

                    # 💾 Save result to Firebase
                    result_ref.set({
                        "name": student_name,
                        "subject": selected_subject,
                        "score": score,
                        "total": total,
                        "details": list(result_summary.values())
                    })

                    st.success(f"✅ Submitted! You scored {score} out of {total}.")
                    st.balloons()

                    with st.expander("📊 View Your Answers"):
                        for i, r in enumerate(result_summary.values()):
                            st.markdown(f"Q{i+1}: {r['question']}")
                            st.markdown(f"- Your Answer: {r['your_answer']}")
                            if not r['is_correct']:
                                st.markdown(f"- ❌ Correct Answer: {r['correct_answer']}")
                            else:
                                st.markdown("- ✅ Correct!")
                            st.markdown("---")
            else:
                st.warning("🚫 No questions found for this subject.")
# 🛡 ADMIN PANEL
def admin_panel():
    st.header("🛡 Admin Panel")
    admin_pass = st.text_input("Enter Admin Password", type="password")

    if admin_pass == "nohs126":
        st.success("Welcome, Admin 👑💙")
        st.subheader("👩‍🏫 Manage Teachers")

        teachers = db.reference("teachers").get()
        if teachers:
            for name, details in teachers.items():
                with st.expander(f"🧑‍🏫 {name}"):
                    st.write(f"Password: {details.get('password', 'N/A')}")
                    new_pass = st.text_input(f"Reset password for {name}", key=f"pass_{name}")
                    if st.button(f"Update Password", key=f"btn_{name}"):
                        db.reference(f"teachers/{name}/password").set(new_pass)
                        st.success("✅ Password updated!")
        else:
            st.info("No teachers found.")

        st.subheader("➕ Add New Teacher")
        new_teacher = st.text_input("New Teacher Name")
        first_time_pass = st.text_input("Set Initial Password", type="password")
        if st.button("Add Teacher"):
            if new_teacher and first_time_pass:
                ref = db.reference(f"teachers/{new_teacher}")
                if not ref.get():
                    ref.set({"password": first_time_pass})
                    st.success("✅ Teacher added!")
                else:
                    st.warning("Teacher already exists.")

        st.subheader("❌ Remove Teacher")
        teacher_names = list(teachers.keys()) if teachers else []
        teacher_to_remove = st.selectbox("Select teacher", teacher_names)
        if st.button("Remove Teacher"):
            db.reference(f"teachers/{teacher_to_remove}").delete()
            st.error("🚫 Teacher removed!")

        st.subheader("🏫 Manage Batches")
        batches = db.reference("batches").get()
        if batches:
            for batch_name, subjects in batches.items():
                with st.expander(f"🎓 {batch_name}"):
                    for subject_name, subject_data in subjects.items():
                        st.markdown(f"#### 📚 {subject_name}")
                        questions = subject_data.get("questions", {})
                        if questions:
                            for qid, qdata in questions.items():
                                st.markdown(f"- Q: {qdata['question']}")
                                st.markdown(f"✅ A: {qdata['answer']}")
                                if st.button("❌ Delete Question", key=f"{qid}{batch_name}{subject_name}"):
                                    db.reference(f"batches/{batch_name}/{subject_name}/questions/{qid}").delete()
                                    st.warning("Deleted. Refresh to update.")

                        if st.button(f"🗑 Delete Subject {subject_name}", key=f"del_sub_{subject_name}"):
                            db.reference(f"batches/{batch_name}/{subject_name}").delete()
                            st.warning(f"Deleted subject '{subject_name}'")

                    if st.button(f"🗑 Delete Entire Batch {batch_name}", key=f"del_batch_{batch_name}"):
                        db.reference(f"batches/{batch_name}").delete()
                        st.error(f"Deleted batch '{batch_name}'")
    elif admin_pass:
        st.error("Wrong password, cutie ❌")

# 🚦 Interface Switcher
if role == "Student":
    student_panel()
elif role == "Teacher":
    teacher_panel()
elif role == "Admin":
    admin_panel()