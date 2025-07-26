# download_firebase.py
import pyrebase
import requests
import json

FIREBASE_CONFIG = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "your-project.firebaseapp.com",
    "databaseURL": "https://your-project.firebaseio.com",
    "projectId": "your-project",
    "storageBucket": "your-project.appspot.com",
    "messagingSenderId": "000000000000",
    "appId": "YOUR_APP_ID"
}

FIREBASE_USER = "chelaxian@gmail.com"
FIREBASE_PASSWORD = "YOUR_PASSWORD"

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
auth = firebase.auth()
user = auth.sign_in_with_email_and_password(FIREBASE_USER, FIREBASE_PASSWORD)
id_token = user["idToken"]

url = f"{FIREBASE_CONFIG['databaseURL']}/.json?auth={id_token}"
response = requests.get(url)
response.raise_for_status()

with open("dump.json", "w", encoding="utf-8") as f:
    json.dump(response.json(), f, ensure_ascii=False, indent=2)

print("✅ Firebase database downloaded to dump.json")
