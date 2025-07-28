import pyrebase
import requests

FIREBASE_CONFIG = {
    "apiKey": "YOUR_API_KEY",
    "authDomain": "your-project.firebaseapp.com",
    "databaseURL": "https://your-project.firebaseio.com",
    "projectId": "your-project",
    "storageBucket": "your-project.appspot.com",
    "messagingSenderId": "000000000000",
    "appId": "YOUR_APP_ID"
}

FIREBASE_USER = "YOUR_EMAIL@gmail.com"
FIREBASE_PASSWORD = "YOUR_PASSWORD"

# Authenticate and get ID token
firebase = pyrebase.initialize_app(FIREBASE_CONFIG)
auth = firebase.auth()
user = auth.sign_in_with_email_and_password(FIREBASE_USER, FIREBASE_PASSWORD)
id_token = user["idToken"]

# Compose URL for full database root deletion
url = f"{FIREBASE_CONFIG['databaseURL']}/.json?auth={id_token}"

# Send DELETE request
response = requests.delete(url)
response.raise_for_status()

print("🗑️ All data successfully deleted from Firebase Realtime Database.")
