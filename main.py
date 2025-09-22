import streamlit as st
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, db
import random
import re

# ----------------- Firebase Setup -----------------
if not firebase_admin._apps:
    cred = credentials.Certificate({
        "type": st.secrets["firebase"]["type"],
        "project_id": st.secrets["firebase"]["project_id"],
        "private_key_id": st.secrets["firebase"]["private_key_id"],
        "private_key": st.secrets["firebase"]["private_key"].replace('\\n', '\n'),
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

# ----------------- Streamlit Config -----------------
st.set_page_config(page_title="CVV SmartExam Portal", page_icon="📘", layout="centered")
st.title("📘 Welcome to CVV SmartExam Portal")

# ----------------- Utility -----------------
def safe_key(value: str) -> str:
    """Make Firebase-safe keys by replacing invalid characters."""
    return re.sub(r'[.#$\\[\\]/]', '_', value.strip())

# ----------------- Student Panel -----------------
def student_panel():
    st.header("🎓 Student Panel")
    student_name = st.text_input("Enter your name").strip()

    batch_data = db.reference("batches").get()
    batch_options = list(batch_data.keys()) if batch_data else []
    selected_batch = st.selectbox("Select your Batch", batch_options)

    if student_name and selected_batch:
        safe_batch = safe_key(selected_batch)
        subject_data = db.reference(f"batches/{safe_batch}").get()
        subject_options = list(subject_data.keys()) if subject_data else []
        selected_subject = st.selectbox("Choose Subject", subject_options)

        if selected_subject:
            safe_subject = safe_key(selected_subject)
            safe_name = safe_key(student_name)

            # 🚫 Prevent retake
            result_ref = db.reference(f"results/{safe_batch}/{safe_subject}/{safe_name}")
            if result_ref.get():
                st.error("❌ You have already submitted this exam. Retaking is not allowed.")
                st.stop()

            st.success(f"Welcome {student_name}! You're taking the {selected_subject} exam 🎯")

            # Load questions
            questions_ref = db.reference(f"batches/{safe_batch}/{safe_subject}/questions")
            questions = questions_ref.get()
            if questions:
                questions = {k: v for k, v in questions.items() if k != "_placeholder_"}

            if questions:
                st.markdown("---")

                # Session state keys
                ss_started_key = f"{safe_name}_{safe_batch}_{safe_subject}_started"
                ss_qdata_key = f"{safe_name}_{safe_batch}_{safe_subject}_qdata"
                ss_order_key = f"{safe_name}_{safe_batch}_{safe_subject}_order"
                ss_answers_key = f"{safe_name}_{safe_batch}_{safe_subject}_answers"

                # Start exam
                if not st.session_state.get(ss_started_key, False):
                    if st.button("Start Exam 🎬"):
                        q_keys = list(questions.keys())
                        random.shuffle(q_keys)  # shuffle once
                        st.session_state[ss_order_key] = q_keys
                        st.session_state[ss_qdata_key] = questions
                        st.session_state[ss_started_key] = True
                        st.session_state[ss_answers_key] = {}
                        try:
                            st.rerun()
                        except:
                            st.experimental_rerun()
                else:
                    st.markdown("### 📋 Questions")
                    answers = st.session_state.get(ss_answers_key, {})
                    q_order = st.session_state.get(ss_order_key, list(questions.keys()))
                    qdata = st.session_state.get(ss_qdata_key, questions)

                    for idx, qid in enumerate(q_order):
                        q = qdata[qid]
                        question_label = f"Q{idx+1}: {q['question']}"
                        unique_key = f"{safe_name}_{safe_batch}_{safe_subject}_{qid}_{idx}"
                        answers[qid] = st.radio(question_label, q['options'],
                                                key=unique_key,
                                                index=q['options'].index(answers[qid]) if qid in answers else 0)

                    st.session_state[ss_answers_key] = answers

                    if st.button("🎯 Submit Answers"):
                        if result_ref.get():
                            st.error("❌ Submission blocked. Already taken.")
                            st.stop()

                        score = 0
                        total = len(answers)
                        result_summary = {}

                        for qid in answers:
                            correct = qdata[qid]['answer']
                            chosen = answers[qid]
                            is_correct = chosen == correct

                            result_summary[qid] = {
                                "question": qdata[qid]['question'],
                                "your_answer": chosen,
                                "correct_answer": correct,
                                "is_correct": is_correct
                            }

                            if is_correct:
                                score += 1

                        # Save to Firebase
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

# ----------------- Teacher Panel -----------------
def teacher_panel():
    st.header("👩‍🏫 Teacher Panel")
    teacher_name = st.text_input("Enter your name").strip()
    teacher_pass = st.text_input("Enter your password", type="password")

    if teacher_name and teacher_pass:
        ref = db.reference(f"teachers/{teacher_name}")
        data = ref.get()

        if data and data.get("password") == teacher_pass:
            st.success(f"Welcome, {teacher_name}! 🌟")
            st.subheader("🏫 Manage Batches & Subjects")

            batch_data = db.reference("batches").get()
            batch_options = list(batch_data.keys()) if batch_data else []
            selected_batch = st.selectbox("Select Batch or Create New", ["➕ Create New"] + batch_options)

            new_batch = ""
            if selected_batch == "➕ Create New":
                new_batch = st.text_input("Enter new batch name").strip()
                if st.button("Create Batch") and new_batch:
                    db.reference(f"batches/{safe_key(new_batch)}").set({})
                    st.success(f"✅ Batch '{new_batch}' created!")
            else:
                new_batch = selected_batch

            if new_batch:
                subject_data = db.reference(f"batches/{safe_key(new_batch)}").get()
                subject_options = list(subject_data.keys()) if subject_data else []
                selected_subject = st.selectbox("Select Subject or Create New", ["➕ Create New"] + subject_options)

                new_subject = ""
                if selected_subject == "➕ Create New":
                    new_subject = st.text_input("Enter new subject name").strip()
                    if st.button("Create Subject") and new_subject:
                        db.reference(f"batches/{safe_key(new_batch)}/{safe_key(new_subject)}/questions").set({})
                        st.success(f"✅ Subject '{new_subject}' created!")
                else:
                    new_subject = selected_subject

                if new_subject:
                    st.markdown("### ➕ Add Question")
                    question = st.text_area("Enter Question").strip()
                    options = [st.text_input(f"Option {i+1}", key=f"opt_{i}") for i in range(4)]
                    correct = st.selectbox("Select Correct Answer", options)

                    if st.button("Add Question"):
                        if question and all(options) and correct:
                            q_ref = db.reference(f"batches/{safe_key(new_batch)}/{safe_key(new_subject)}/questions").push()
                            q_ref.set({
                                "question": question,
                                "options": options,
                                "answer": correct
                            })
                            st.success("✅ Question added!")
                        else:
                            st.error("❌ Please fill all fields before adding.")

                    st.markdown("### 👁 View & Manage Questions")
                    if st.button("🔁 Refresh Page"):
                        js = "window.location.reload();"
                        components.html(f"<script>{js}</script>", height=0)

                    q_data = db.reference(f"batches/{safe_key(new_batch)}/{safe_key(new_subject)}/questions").get()

                    if q_data:
                        for qid, qinfo in q_data.items():
                            if qid == "_placeholder_":
                                continue
                            with st.expander(qinfo['question']):
                                st.write("#### Options:")
                                for i, opt in enumerate(qinfo['options']):
                                    st.write(f"- {opt}")
                                st.markdown(f"✅ Correct Answer: {qinfo['answer']}")

                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button(f"🗑 Delete", key=f"del_{qid}"):
                                        db.reference(f"batches/{safe_key(new_batch)}/{safe_key(new_subject)}/questions/{qid}").delete()
                                        st.warning("❌ Deleted! Press refresh to update.")
                                with col2:
                                    if st.button(f"✏ Edit", key=f"edit_{qid}"):
                                        new_q = st.text_area("Edit Question", value=qinfo['question'], key=f"q_{qid}")
                                        new_opts = [st.text_input(f"Edit Option {i+1}", value=o, key=f"o_{qid}_{i}") for i, o in enumerate(qinfo['options'])]
                                        new_correct = st.selectbox("Choose New Correct", new_opts, index=new_opts.index(qinfo['answer']), key=f"c_{qid}")

                                        if st.button("💾 Save Changes", key=f"save_{qid}"):
                                            db.reference(f"batches/{safe_key(new_batch)}/{safe_key(new_subject)}/questions/{qid}").set({
                                                "question": new_q,
                                                "options": new_opts,
                                                "answer": new_correct
                                            })
                                            st.success("✅ Question updated! Press refresh to view.")

                    st.markdown("### 📊 View Student Results")
                    result_ref = db.reference(f"results/{safe_key(new_batch)}/{safe_key(new_subject)}")
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

# ----------------- Admin Panel -----------------
def admin_panel():
    st.header("🛡 Admin Panel")
    admin_pass = st.text_input("Enter Admin Password", type="password")

    real_admin_pass = st.secrets["admin"]["password"]

    if admin_pass == real_admin_pass:
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
                                if isinstance(qdata, dict) and 'question' in qdata and 'answer' in qdata:
                                    st.markdown(f"- Q: {qdata['question']}")
                                    st.markdown(f"✅ A: {qdata['answer']}")
                                    if st.button("❌ Delete Question", key=f"{qid}{batch_name}{subject_name}"):
                                        db.reference(f"batches/{batch_name}/{subject_name}/questions/{qid}").delete()
                                        st.warning("Deleted. Refresh to update.")
                                else:
                                    st.markdown(f"- ⚠ Skipped corrupted or placeholder data (ID: {qid})")

                        if st.button(f"🗑 Delete Subject {subject_name}", key=f"del_sub_{subject_name}"):
                            db.reference(f"batches/{batch_name}/{subject_name}").delete()
                            st.warning(f"Deleted subject '{subject_name}'")

                    if st.button(f"🗑 Delete Entire Batch {batch_name}", key=f"del_batch_{batch_name}"):
                        db.reference(f"batches/{batch_name}").delete()
                        st.error(f"Deleted batch '{batch_name}'")
    elif admin_pass:
        st.error("Wrong password, cutie ❌")

# ----------------- Role Switcher -----------------
role = st.selectbox("Who are you?", ["Select Role", "Student", "Teacher", "Admin"])
if role == "Student":
    student_panel()
elif role == "Teacher":
    teacher_panel()
elif role == "Admin":
    admin_panel()