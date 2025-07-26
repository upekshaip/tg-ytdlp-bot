# upload_to_firebase.py
import pyrebase
import requests
import json

FIREBASE_CONFIG = {
    "apiKey": "YOUR_NEW_API_KEY",
    "authDomain": "your-new-project.firebaseapp.com",
    "databaseURL": "https://your-new-project.firebaseio.com",
    "projectId": "your-new-project",
    "storageBucket": "your-new-project.appspot.com",
    "messagingSenderId": "000000000000",
    "appId": "YOUR_NEW_APP_ID"
}

FIREBASE_USER = "chelaxian@gmail.com"
FIREBASE_PASSWORD = "YOUR_PASSWORD"

firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
auth = firebase.auth()
user = auth.sign_in_with_email_and_password(FIREBASE_USER, FIREBASE_PASSWORD)
id_token = user["idToken"]

with open("dump.json", "r", encoding="utf-8") as f:
    data = json.load(f)

url = f"{FIREBASE_CONFIG['databaseURL']}/.json?auth={id_token}"
response = requests.put(url, json=data)
response.raise_for_status()

print("✅ Firebase database uploaded from dump.json")
