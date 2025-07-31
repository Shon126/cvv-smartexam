# admin.py
import streamlit as st
import firebase_admin
from firebase_admin import credentials, db

# Firebase Init
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': 'https://your-database-url.firebaseio.com/'  # CHANGE THIS ❤
    })

st.set_page_config(page_title="CVV SmartExam - Admin", page_icon="🛡", layout="centered")
st.title("🛡 CVV SmartExam - Admin Panel")

# 🔐 Admin Login
admin_username = st.text_input("Admin Username")
admin_password = st.text_input("Admin Password", type="password")

if st.button("Login"):
    if admin_username == "admin" and admin_password == "admin123":
        st.success("Logged in as Admin 👑")

        # ➕ Add Teacher
        st.header("➕ Add a New Teacher")
        new_teacher = st.text_input("Teacher Name")
        new_password = st.text_input("Password", type="password")
        if st.button("Add Teacher"):
            if new_teacher and new_password:
                ref = db.reference('teachers')
                all_teachers = ref.get() or {}
                if new_teacher in all_teachers:
                    st.warning("Teacher already exists!")
                else:
                    ref.child(new_teacher).set({"password": new_password})
                    st.success(f"Teacher '{new_teacher}' added ✅")
            else:
                st.error("Please fill both fields.")

        # 👩‍🏫 View Teachers
        st.header("👨‍🏫 All Teachers")
        teachers = db.reference("teachers").get() or {}
        for name, data in teachers.items():
            col1, col2, col3 = st.columns([3, 2, 2])
            with col1:
                st.write(f"👤 {name}")
            with col2:
                if st.button(f"❌ Remove", key=f"remove_{name}"):
                    db.reference("teachers").child(name).delete()
                    st.warning(f"Deleted teacher: {name}")
                    st.experimental_rerun()
            with col3:
                new_pass = st.text_input(f"New Pass ({name})", key=f"pass_{name}")
                if st.button(f"🔁 Reset", key=f"reset_{name}"):
                    if new_pass:
                        db.reference("teachers").child(name).update({"password": new_pass})
                        st.success(f"Password reset for {name}")
                    else:
                        st.error("Enter new password first")

        # 📦 View/Delete Batches
        st.header("📦 All Batches")
        batches = db.reference("batches").get() or {}
        if not batches:
            st.info("No batches found.")
        else:
            for batch, subs in batches.items():
                with st.expander(f"📚 {batch}"):
                    st.write("Subjects:")
                    for subject, details in subs.items():
                        st.write(f"📝 {subject} - Created by: {details.get('teacher', 'Unknown')}")
                    if st.button(f"🗑 Delete {batch}", key=f"del_batch_{batch}"):
                        db.reference("batches").child(batch).delete()
                        st.warning(f"Batch '{batch}' deleted ❌")
                        st.experimental_rerun()

    else:
        st.error("Wrong admin credentials 💔")