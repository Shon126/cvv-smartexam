import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# ✅ Initialize Firebase (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cvv-smartexam-v2-default-rtdb.asia-southeast1.firebasedatabase.app'  
    })

# ✅ Streamlit page config
st.set_page_config(page_title="CVV SmartExam - Admin Panel", page_icon="🛡", layout="centered")
st.title("🛡 CVV SmartExam - Admin Panel")

# 🔐 Admin Login
admin_pass = st.text_input("Enter Admin Password", type="password")
if admin_pass == "nohs126":  # password 
    st.success("Welcome, Admin  👑💙")

    # 👩‍🏫 View & Manage Teachers
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

    st.markdown("---")

    # ➕ Add New Teacher
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

    st.markdown("---")

    # ❌ Remove Teacher
    st.header("❌ Remove Teacher")
    teacher_names = list(teachers.keys()) if teachers else []
    teacher_to_remove = st.selectbox("Select teacher to remove", teacher_names)
    if st.button("Remove Selected Teacher"):
        db.reference(f"teachers/{teacher_to_remove}").delete()
        st.error(f"🚫 Teacher '{teacher_to_remove}' removed.")

    st.markdown("---")

    # 🏫 View/Delete Batches & Subjects
    st.header("🏫 Batches & Subjects")
    batches = db.reference("batches").get()
    if batches:
        for batch_name, subjects in batches.items():
            with st.expander(f"🎓 {batch_name}"):
                for subject_name, subject_data in subjects.items():
                    st.subheader(f"📚 {subject_name}")

                    # Show questions
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

else:
    if admin_pass:
        st.error("Wrong password, cutie ❌")