import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cvv-smartexam-default-rtdb.firebaseio.com/'  # ✅ Your real Firebase URL
    })

st.set_page_config(page_title="CVV SmartExam - Teacher Panel", page_icon="👩‍🏫", layout="centered")
st.title("👩‍🏫 CVV SmartExam - Teacher Panel (Team Teaching Mode)")

# 🔐 Login Section
teacher_name = st.text_input("Enter your name").strip()
teacher_pass = st.text_input("Enter your password", type="password")

if teacher_name and teacher_pass:
    ref = db.reference(f"teachers/{teacher_name}")
    data = ref.get()

    if data and data.get("password") == teacher_pass:
        st.success(f"Welcome, {teacher_name}! 🌟")

        # 🏫 Batch Section
        st.header("🏫 Manage Batches & Subjects")
        batch_data = db.reference("batches").get()
        batch_options = list(batch_data.keys()) if batch_data else []
        selected_batch = st.selectbox("Select Batch or Create New", ["➕ Create New"] + batch_options)

        if selected_batch == "➕ Create New":
            new_batch = st.text_input("Enter new batch name (e.g., BCA2025)")
            if st.button("Create Batch") and new_batch:
                db.reference(f"batches/{new_batch}").set({})
                st.success(f"✅ Batch '{new_batch}' created!")
                selected_batch = new_batch
        else:
            new_batch = selected_batch

        if new_batch:
            # 📚 Subject Section
            subject_data = db.reference(f"batches/{new_batch}").get()
            subject_options = list(subject_data.keys()) if subject_data else []
            selected_subject = st.selectbox("Select Subject or Create New", ["➕ Create New"] + subject_options)

            if selected_subject == "➕ Create New":
                new_subject = st.text_input("Enter new subject name (e.g., Python)")
                if st.button("Create Subject") and new_subject:
                    db.reference(f"batches/{new_batch}/{new_subject}/questions").set({})
                    st.success(f"✅ Subject '{new_subject}' created!")
                    selected_subject = new_subject
            else:
                new_subject = selected_subject

            if selected_subject:
                st.subheader(f"📄 Managing: {new_batch} > {selected_subject}")

                # ➕ Add Question
                st.markdown("### ➕ Add Question")
                question = st.text_area("Enter Question")
                options = [st.text_input(f"Option {i+1}", key=f"opt_{i}") for i in range(4)]
                correct = st.selectbox("Select Correct Answer", options)

                if st.button("Add Question"):
                    if question and all(options) and correct:
                        q_ref = db.reference(f"batches/{new_batch}/{selected_subject}/questions").push()
                        q_ref.set({
                            "question": question,
                            "options": options,
                            "answer": correct
                        })
                        st.success("✅ Question added!")
                    else:
                        st.error("❌ Please fill all fields.")

                # 👁 View Questions
                st.markdown("### 👁 View & Manage Questions")
                q_data = db.reference(f"batches/{new_batch}/{selected_subject}/questions").get()

                if q_data:
                    for qid, qinfo in q_data.items():
                        with st.expander(qinfo['question']):
                            for i, opt in enumerate(qinfo['options']):
                                st.write(f"- {opt}")
                            st.markdown(f"✅ Correct Answer:** {qinfo['answer']}")
                            if st.button(f"🗑 Delete this question", key=qid):
                                db.reference(f"batches/{new_batch}/{selected_subject}/questions/{qid}").delete()
                                st.warning("❌ Question deleted! Please refresh to update.")
                else:
                    st.info("No questions yet.")

                # 📊 Results
                st.markdown("### 📊 View Student Results")
                result_ref = db.reference(f"results/{new_batch}/{selected_subject}")
                result_data = result_ref.get()

                if result_data:
                    for student, r in result_data.items():
                        st.markdown(f"👤 *{student}* — Score: {r['score']} / {r['total']}")
                else:
                    st.info("No student results yet.")

                # 🔁 Reset
                if st.button("🔁 Reset Results for this Subject"):
                    result_ref.delete()
                    st.success("✅ Results cleared!")

    else:
        st.error("Invalid name or password ❌")