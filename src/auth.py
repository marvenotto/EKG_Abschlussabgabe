import json
import os
import hashlib
import smtplib
import random
from email.mime.text import MIMEText

USER_DB = "data/users.json"

def load_users() -> dict:
    """Lädt die registrierten Benutzerdaten aus der lokalen JSON-Datenbank."""
    if not os.path.exists(USER_DB):
        return {}
    with open(USER_DB, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users: dict):
    """Speichert die Benutzerdaten sicher in der JSON-Datenbank."""
    with open(USER_DB, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=4)

def hash_pass(pwd: str) -> str:
    """Verschlüsselt ein Passwort mittels SHA-256 zur sicheren Verwahrung."""
    return hashlib.sha256(pwd.encode()).hexdigest()

def send_email(to_email: str, subject: str, body: str, smtp_user: str, smtp_pass: str) -> bool:
    """Versendet eine automatisierte E-Mail über den konfigurierten Gmail-SMTP-Server."""
    try:
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = smtp_user
        msg['To'] = to_email

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("E-Mail Fehler:", e)
        return False

def register_user(email: str, password: str, smtp_user: str, smtp_pass: str) -> str:
    """Registriert einen neuen Account und sendet ein 6-stelliges OTP zur Verifizierung."""
    users = load_users()
    if email in users and users[email].get("verified"):
        return "exists"
    
    code = str(random.randint(100000, 999999))
    
    users[email] = {
        "password": hash_pass(password),
        "verified": False,
        "code": code
    }
    save_users(users)
    
    body = f"Willkommen bei der EKG Analyse App!\n\nDein Verifizierungscode lautet: {code}\n\nBitte gib diesen Code in der App ein."
    success = send_email(email, "Dein Verifizierungscode (EKG App)", body, smtp_user, smtp_pass)
    return "sent" if success else "error"

def verify_code(email: str, code: str) -> bool:
    """Überprüft den eingegebenen Verifizierungscode eines Benutzers."""
    users = load_users()
    if email in users and users[email]["code"] == code:
        users[email]["verified"] = True
        save_users(users)
        return True
    return False

def check_login(email: str, password: str) -> bool:
    """Prüft die Login-Anmeldedaten gegen die verschlüsselten Hashes in der Datenbank."""
    users = load_users()
    if email in users:
        if users[email]["verified"] and users[email]["password"] == hash_pass(password):
            return True
    return False

def send_reset_code(email: str, smtp_user: str, smtp_pass: str) -> str:
    """Generiert und versendet einen Bestätigungs-Code zum Zurücksetzen des Passworts."""
    users = load_users()
    if email not in users or not users[email].get("verified", False):
        return "not_found"

    reset_code = str(random.randint(100000, 999999))
    body = f"Dein Code zum Zurücksetzen des Passworts lautet: {reset_code}\n\nBitte gib diesen Code in der App ein."
    success = send_email(email, 'Passwort Reset EKG Dashboard', body, smtp_user, smtp_pass)
    
    return reset_code if success else "error"

def update_password(email: str, new_password: str) -> bool:
    """Aktualisiert das Passwort eines bestehenden Benutzers mit einem neuen Hash."""
    users = load_users()
    if email in users:
        users[email]["password"] = hash_pass(new_password)
        save_users(users)
        return True
    return False