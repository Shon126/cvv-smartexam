import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# Initialize Firebase
    if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://cvv-smartexam-v2-default-rtdb.firebaseio.com'
    })
st.set_page_config(page_title="CVV SmartExam - Admin Panel", page_icon="🛡", layout="centered")

st.title("🛡 CVV SmartExam - Admin Panel")

# 🔐 Admin Login
admin_pass = st.text_input("Enter Admin Password", type="password")
if admin_pass == "cvvadmin123":  # 👉 You can change this
    st.success("Welcome, Admin Queen! 👑💙")

    # 👩‍🏫 View All Teachers
    st.header("👩‍🏫 All Registered Teachers")
    teachers = db.reference("teachers").get()
    if teachers:
        for name, details in teachers.items():
            with st.expander(f"🧑‍🏫 {name}"):
                st.write(f"Password: {details.get('password')}")
                new_pass = st.text_input(f"Reset password for {name}", key=name)
                if st.button(f"Update Password for {name}", key=f"btn_{name}") and new_pass:
                    db.reference(f"teachers/{name}/password").set(new_pass)
                    st.success(f"✅ Password updated for {name}")
    else:
        st.info("No teachers registered yet.")

    st.markdown("---")

    # 🏫 View/Delete Batches & Subjects
    st.header("🏫 Batches & Subjects")
    batches = db.reference("batches").get()
    if batches:
        for batch_name, subjects in batches.items():
            with st.expander(f"🎓 {batch_name}"):
                for subject_name in subjects:
                    st.subheader(f"📚 {subject_name}")
                    
                    # Show questions
                    questions = db.reference(f"batches/{batch_name}/{subject_name}/questions").get()
                    if questions:
                        for qid, qdata in questions.items():
                            st.markdown(f"*Q:* {qdata['question']}")
                            st.markdown(f"✅ Correct: {qdata['answer']}")
                            if st.button("❌ Delete this question", key=f"{qid}{batch_name}{subject_name}"):
                                db.reference(f"batches/{batch_name}/{subject_name}/questions/{qid}").delete()
                                st.warning("Question deleted. Refresh to update.")
                    else:
                        st.write("No questions found.")

                    if st.button(f"🗑 Delete Subject '{subject_name}'", key=f"del_{batch_name}_{subject_name}"):
                        db.reference(f"batches/{batch_name}/{subject_name}").delete()
                        st.warning(f"Deleted subject '{subject_name}' from '{batch_name}'.")

                if st.button(f"🗑 Delete Entire Batch '{batch_name}'", key=f"del_batch_{batch_name}"):
                    db.reference(f"batches/{batch_name}").delete()
                    st.error(f"Batch '{batch_name}' deleted.")

    else:
        st.info("No batches created yet.")

else:
    if admin_pass:
        st.error("Wrong password, cutie ❌")