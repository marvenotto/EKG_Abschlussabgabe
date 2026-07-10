import json
import os
import hashlib
import smtplib
import random
from email.mime.text import MIMEText

# Hier speichern wir die Nutzer (Passwörter werden verschlüsselt!)
USER_DB = "data/users.json"

def load_users():
    if not os.path.exists(USER_DB):
        return {}
    with open(USER_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USER_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

def hash_pass(pwd):
    """Verschlüsselt das Passwort, damit es nicht als Klartext gespeichert wird."""
    return hashlib.sha256(pwd.encode()).hexdigest()

def send_email(to_email, subject, body, smtp_user, smtp_pass):
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email

        # Verbindung zu Gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("E-Mail Fehler:", e)
        return False

def register_user(email, password, smtp_user, smtp_pass):
    users = load_users()
    if email in users and users[email].get("verified"):
        return "exists"
    
    # Generiere einen 6-stelligen Verifizierungscode
    code = str(random.randint(100000, 999999))
    
    # Speichere den Nutzer als "noch nicht verifiziert"
    users[email] = {
        "password": hash_pass(password),
        "verified": False,
        "code": code
    }
    save_users(users)
    
    # E-Mail senden
    body = f"Willkommen bei der EKG Analyse App!\n\nDein Verifizierungscode lautet: {code}\n\nBitte gib diesen Code in der App ein."
    success = send_email(email, "Dein Verifizierungscode (EKG App)", body, smtp_user, smtp_pass)
    return "sent" if success else "error"

def verify_code(email, code):
    users = load_users()
    if email in users and users[email]["code"] == code:
        users[email]["verified"] = True
        save_users(users)
        return True
    return False

def check_login(email, password):
    users = load_users()
    if email in users:
        # Prüfen ob verifiziert UND ob das verschlüsselte Passwort stimmt
        if users[email]["verified"] and users[email]["password"] == hash_pass(password):
            return True
    return False

def send_reset_code(email: str, smtp_user: str, smtp_pass: str) -> str:
    """Prüft, ob der User existiert und sendet einen Reset-Code per E-Mail."""
    users = load_users()
    
    # Prüfen, ob die E-Mail existiert und verifiziert ist
    if email not in users or not users[email].get("verified", False):
        return "not_found"

    reset_code = str(random.randint(100000, 999999))
    
    body = f"Dein Code zum Zurücksetzen des Passworts lautet: {reset_code}\n\nBitte gib diesen Code in der App ein."
    success = send_email(email, 'Passwort Reset EKG Dashboard', body, smtp_user, smtp_pass)
    
    if success:
        return reset_code
    else:
        return "error"

def update_password(email: str, new_password: str) -> bool:
    """Aktualisiert das Passwort eines Nutzers in der users.json"""
    users = load_users()
    if email in users:
        users[email]["password"] = hash_pass(new_password)
        save_users(users)
        return True
    return False