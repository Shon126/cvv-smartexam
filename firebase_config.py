# firebase_config.py

import firebase_admin
from firebase_admin import credentials, firestore, db

# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        'databaseURL': "https://cvv-smartexam-default-rtdb.firebaseio.com"
    })

# Firestore client
firestore_db = firestore.client()

# Realtime database reference
realtime_db = db.reference()