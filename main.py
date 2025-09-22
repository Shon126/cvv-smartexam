import streamlit as st
import streamlit.components.v1 as components
import firebase_admin
from firebase_admin import credentials, db
import random
import re

# -------------------------
# Helper: sanitize Firebase keys
# -------------------------
def safe_key(value: str) -> str:
    """Replace illegal Firebase RTDB path characters with underscores and tidy text."""
    if not isinstance(value, str):
        return ""
    v = value.strip()
    # replace illegal characters . # $ [ ] /
    return re.sub(r'[.#$\[\]/]', '_', v)

# -------------------------
# Firebase init (unchanged)
# -------------------------
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

# -------------------------
# Streamlit page config
# -------------------------
st.set_page_config(page_title="CVV SmartExam Portal", page_icon="📘", layout="centered")
st.title("📘 Welcome to CVV SmartExam Portal")

# Role selector
role = st.selectbox("Who are you?", ["Select Role", "Student", "Teacher", "Admin"])

# -------------------------
# STUDENT PANEL
# -------------------------
def student_panel():
    st.header("🎓 Student Panel")
    student_name = st.text_input("Enter your name").strip()

    # load batches (show a friendly default option so selectbox always has items)
    batch_data = db.reference("batches").get()
    batch_options = ["Select Batch"] + (list(batch_data.keys()) if batch_data else [])
    selected_batch = st.selectbox("Select your Batch", batch_options)

    # proceed only when real values are selected
    if not student_name:
        st.info("Please enter your name to continue.")
        return

    if selected_batch in ("Select Batch", "No batches available"):
        st.info("Please choose a batch.")
        return

    # load subjects for that batch
    subject_data = db.reference(f"batches/{safe_key(selected_batch)}").get()
    subject_options = ["Select Subject"] + (list(subject_data.keys()) if subject_data else [])
    selected_subject = st.selectbox("Choose Subject", subject_options)

    if selected_subject in ("Select Subject", "No subjects available"):
        st.info("Please choose a subject.")
        return

    # sanitize keys
    safe_batch = safe_key(selected_batch)
    safe_subject = safe_key(selected_subject)
    safe_name = safe_key(student_name)

    # check if already attempted
    result_ref = db.reference(f"results/{safe_batch}/{safe_subject}/{safe_name}")
    if result_ref.get():
        st.error("❌ You have already submitted this exam. Retaking is not allowed.")
        return

    st.success(f"Hello {student_name}! You're about to take the {selected_subject} exam 🎯")

    # keys for session_state to persist shuffle/order & question data
    ss_order_key = f"order__{safe_batch}__{safe_subject}__{safe_name}"
    ss_qdata_key = f"qdata__{safe_batch}__{safe_subject}__{safe_name}"
    ss_started_key = f"started__{safe_batch}__{safe_subject}__{safe_name}"

    # load questions from Firebase
    questions_ref = db.reference(f"batches/{safe_batch}/{safe_subject}/questions")
    all_questions = questions_ref.get()
    if not all_questions:
        st.warning("🚫 No questions found for this subject.")
        return

    # remove placeholder if present
    questions = {k: v for k, v in (all_questions.items() if isinstance(all_questions, dict) else []) if k != "_placeholder_"}
    if not questions:
        st.warning("🚫 No valid questions found for this subject.")
        return

    # If not started yet, show "Start Exam" button which will set order once.
    if ss_started_key not in st.session_state:
        st.markdown("Press **Start Exam** when you're ready. The questions will be fixed once you start.")
        if st.button("Start Exam 🎬"):
            q_keys = list(questions.keys())
            random.shuffle(q_keys)  # shuffle once
            st.session_state[ss_order_key] = q_keys
            st.session_state[ss_qdata_key] = questions
            st.session_state[ss_started_key] = True
            st.experimental_rerun()
        return

    # If started, retrieve order and qdata from session_state
    question_keys = st.session_state.get(ss_order_key, [])
    questions = st.session_state.get(ss_qdata_key, questions)

    if not question_keys:
        st.error("Unexpected error: question order missing. Please press Start Exam again.")
        # clear started so user can attempt again
        for k in (ss_order_key, ss_qdata_key, ss_started_key):
            if k in st.session_state:
                del st.session_state[k]
        return

    # display the questions inside a form so widget interactions don't cause mid-exam reruns
    form_key = f"form__{safe_batch}__{safe_subject}__{safe_name}"
    with st.form(key=form_key):
        st.markdown("---")
        st.markdown("### 📋 Questions")
        # We will store answer widget keys in a dict (stable keys so Streamlit preserves values)
        answers = {}
        for idx, qid in enumerate(question_keys):
            q = questions[qid]
            # Add a placeholder first so radios start unselected
            display_options = ["-- Select --"] + q['options']
            widget_key = f"ans__{safe_name}__{safe_batch}__{safe_subject}__{qid}"
            # index=0 ensures placeholder is selected visually until user chooses.
            answers[qid] = st.radio(f"Q{idx+1}: {q['question']}", display_options, index=0, key=widget_key)

        submit = st.form_submit_button("🎯 Submit Answers")
        if submit:
            # double-check no previous submission (race-safe)
            if result_ref.get():
                st.error("❌ Submission blocked. You have already taken this exam.")
            else:
                total = len(question_keys)
                score = 0
                result_summary = []

                for qid in question_keys:
                    chosen = answers[qid]
                    # treat placeholder as unanswered (None)
                    chosen_final = None if chosen == "-- Select --" else chosen
                    correct = questions[qid]['answer']
                    is_correct = (chosen_final == correct)
                    if is_correct:
                        score += 1

                    result_summary.append({
                        "question": questions[qid]['question'],
                        "your_answer": chosen_final,
                        "correct_answer": correct,
                        "is_correct": is_correct
                    })

                # Save to Firebase
                result_ref.set({
                    "name": student_name,
                    "subject": selected_subject,
                    "score": score,
                    "total": total,
                    "details": result_summary
                })

                st.success(f"✅ Submitted! You scored {score} out of {total}.")
                st.balloons()

                # show details
                with st.expander("📊 View Your Answers"):
                    for i, r in enumerate(result_summary):
                        st.markdown(f"Q{i+1}: {r['question']}")
                        st.markdown(f"- Your Answer: {r['your_answer']}")
                        if not r['is_correct']:
                            st.markdown(f"- ❌ Correct Answer: {r['correct_answer']}")
                        else:
                            st.markdown("- ✅ Correct!")
                        st.markdown("---")

                # cleanup the per-quiz session_state (keep 'started' marker removed to prevent reattempt)
                for k in (ss_order_key, ss_qdata_key, ss_started_key):
                    if k in st.session_state:
                        del st.session_state[k]

# -------------------------
# TEACHER PANEL (keeps safe_key usage)
# -------------------------
def teacher_panel():
    st.header("👩‍🏫 Teacher Panel")
    teacher_name = st.text_input("Enter your name").strip()
    teacher_pass = st.text_input("Enter your password", type="password")

    if teacher_name and teacher_pass:
        ref = db.reference(f"teachers/{safe_key(teacher_name)}")
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
                                continue  # Ignore dummy

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

                        updated_qs = db.reference(f"batches/{safe_key(new_batch)}/{safe_key(new_subject)}/questions").get()
                        if not updated_qs or all(k == "_placeholder_" for k in updated_qs.keys()):
                            db.reference(f"batches/{safe_key(new_batch)}/{safe_key(new_subject)}/questions").set({
                                "_placeholder_": "empty"
                            })
                    else:
                        st.info("No questions yet.")

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

# -------------------------
# ADMIN PANEL (keeps safe_key usage)
# -------------------------
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
                        db.reference(f"teachers/{safe_key(name)}/password").set(new_pass)
                        st.success("✅ Password updated!")
        else:
            st.info("No teachers found.")

        st.subheader("➕ Add New Teacher")
        new_teacher = st.text_input("New Teacher Name")
        first_time_pass = st.text_input("Set Initial Password", type="password")
        if st.button("Add Teacher"):
            if new_teacher and first_time_pass:
                ref = db.reference(f"teachers/{safe_key(new_teacher)}")
                if not ref.get():
                    ref.set({"password": first_time_pass})
                    st.success("✅ Teacher added!")
                else:
                    st.warning("Teacher already exists.")

        st.subheader("❌ Remove Teacher")
        teacher_names = list(teachers.keys()) if teachers else []
        teacher_to_remove = st.selectbox("Select teacher", teacher_names)
        if st.button("Remove Teacher"):
            db.reference(f"teachers/{safe_key(teacher_to_remove)}").delete()
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
                                        db.reference(f"batches/{safe_key(batch_name)}/{safe_key(subject_name)}/questions/{qid}").delete()
                                        st.warning("Deleted. Refresh to update.")
                                else:
                                    st.markdown(f"- ⚠ Skipped corrupted or placeholder data (ID: {qid})")

                        if st.button(f"🗑 Delete Subject {subject_name}", key=f"del_sub_{subject_name}"):
                            db.reference(f"batches/{safe_key(batch_name)}/{safe_key(subject_name)}").delete()
                            st.warning(f"Deleted subject '{subject_name}'")

                    if st.button(f"🗑 Delete Entire Batch {batch_name}", key=f"del_batch_{batch_name}"):
                        db.reference(f"batches/{safe_key(batch_name)}").delete()
                        st.error(f"Deleted batch '{batch_name}'")
    elif admin_pass:
        st.error("Wrong password, cutie ❌")

# -------------------------
# Main switch
# -------------------------
if role == "Student":
    student_panel()
elif role == "Teacher":
    teacher_panel()
elif role == "Admin":
    admin_panel()