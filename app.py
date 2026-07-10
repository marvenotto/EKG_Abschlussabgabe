import streamlit as st
import os
import pandas as pd
import plotly.express as px
from PIL import Image
import json
import importlib

# Importe aus unseren Modulen
from src.models import Person, EKG
from src.processing import SignalProcessor
from src.visualization import plot_interactive_ekg
import src.auth as auth  

# Zwingt Streamlit dazu, die auth.py bei jedem Laden frisch einzulesen
importlib.reload(auth)

# Versuche den PDF Generator zu laden, falls vorhanden
try:
    from src.pdf_generator import generate_pdf_report
except ImportError:
    generate_pdf_report = None

# Layout & Theme (UI/UX)
st.set_page_config(page_title="EKG Dashboard", layout="wide", initial_sidebar_state="expanded")

# --- AUTHENTIFIZIERUNG ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "verify_email" not in st.session_state:
    st.session_state.verify_email = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False 
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if not st.session_state.authenticated:
    st.title("🔒 Willkommen zur EKG Analyse")
    
    if st.session_state.verify_email:
        st.info(f"📧 Wir haben eine E-Mail an **{st.session_state.verify_email}** gesendet.")
        code_input = st.text_input("Bitte gib den 6-stelligen Code ein:")
        if st.button("Code bestätigen", key="auth_code_confirm"):
            if auth.verify_code(st.session_state.verify_email, code_input):
                st.success("✅ Account erfolgreich verifiziert! Du kannst dich jetzt einloggen.")
                st.session_state.verify_email = None 
                st.rerun()
            else:
                st.error("❌ Falscher Code. Bitte erneut versuchen.")
        if st.button("Abbrechen", key="auth_code_cancel"):
            st.session_state.verify_email = None
            st.rerun()
        st.stop()

    tab_login, tab_register, tab_admin_login = st.tabs(["🔑 Patienten Login", "📝 Registrieren", "🛡️ Admin Zugang"])
    
    # --- STATUS-VARIABLEN FÜR PASSWORT-RESET ---
    if "reset_email" not in st.session_state:
        st.session_state.reset_email = None
    if "reset_code_sent" not in st.session_state:
        st.session_state.reset_code_sent = None

    with tab_login:
        st.subheader("Als Patient / Nutzer anmelden")
        
        # --- NORMALER LOGIN ---
        if not st.session_state.reset_email:
            login_email = st.text_input("E-Mail", key="login_email")
            login_password = st.text_input("Passwort", type="password", key="login_pass")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Einloggen", key="btn_login"):
                    if auth.check_login(login_email, login_password):
                        st.session_state.authenticated = True
                        st.session_state.is_admin = False 
                        st.session_state.user_email = login_email
                        st.rerun()
                    else:
                        st.error("❌ Falsches Passwort oder E-Mail noch nicht verifiziert.")
            with col2:
                # Klick startet den Reset-Prozess
                if st.button("Passwort vergessen?", key="btn_forgot_pass"):
                    if login_email:
                        st.session_state.reset_email = login_email
                        st.rerun()
                    else:
                        st.warning("Bitte gib deine E-Mail-Adresse in das Feld ein, um das Passwort zurückzusetzen.")
        
        # --- PASSWORT RESET PROZESS ---
        else:
            st.info(f"Passwort-Reset für: **{st.session_state.reset_email}**")
            
            # Schritt 1: Code senden
            if not st.session_state.reset_code_sent:
                if st.button("Bestätigungs-Code per E-Mail anfordern"):
                    with st.spinner("Sende Code..."):
                        smtp_user = st.secrets["email"]
                        smtp_pass = st.secrets["password"]
                        res = auth.send_reset_code(st.session_state.reset_email, smtp_user, smtp_pass)
                        
                        if res == "not_found":
                            st.error("Diese E-Mail ist nicht registriert oder noch nicht verifiziert.")
                            st.session_state.reset_email = None # Abbrechen
                        elif res == "error":
                            st.error("Fehler beim Senden der E-Mail.")
                        else:
                            st.session_state.reset_code_sent = res # Den generierten Code speichern
                            st.rerun()
                
                if st.button("Abbrechen", key="btn_reset_cancel_1"):
                    st.session_state.reset_email = None
                    st.rerun()
            
            # Schritt 2: Code prüfen und neues Passwort setzen
            else:
                st.success("📧 Wir haben dir einen 6-stelligen Code gesendet!")
                entered_code = st.text_input("Bitte Code eingeben:")
                new_pass1 = st.text_input("Neues Passwort", type="password")
                new_pass2 = st.text_input("Neues Passwort bestätigen", type="password")
                
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if st.button("Passwort ändern"):
                        if entered_code == st.session_state.reset_code_sent:
                            if new_pass1 == new_pass2 and len(new_pass1) >= 4:
                                if auth.update_password(st.session_state.reset_email, new_pass1):
                                    st.success("✅ Passwort erfolgreich geändert! Du kannst dich jetzt einloggen.")
                                    # Reset-Status aufräumen
                                    st.session_state.reset_email = None
                                    st.session_state.reset_code_sent = None
                                else:
                                    st.error("Fehler beim Speichern in der Datenbank.")
                            else:
                                st.error("Passwörter stimmen nicht überein oder sind zu kurz.")
                        else:
                            st.error("❌ Falscher Code!")
                with col_r2:
                    if st.button("Abbrechen", key="btn_reset_cancel_2"):
                        st.session_state.reset_email = None
                        st.session_state.reset_code_sent = None
                        st.rerun()
                
    with tab_register:
        st.subheader("Neuen Account erstellen")
        reg_email = st.text_input("E-Mail", key="reg_email")
        reg_password = st.text_input("Passwort", type="password", key="reg_pass")
        reg_password_confirm = st.text_input("Passwort bestätigen", type="password", key="reg_pass_conf")
        
        if st.button("Registrieren", key="btn_register"):
            if reg_password == reg_password_confirm and len(reg_password) >= 4:
                with st.spinner('Sende Bestätigungs-E-Mail...'):
                    smtp_user = st.secrets["email"]
                    smtp_pass = st.secrets["password"]
                    res = auth.register_user(reg_email, reg_password, smtp_user, smtp_pass)
                    if res == "sent":
                        st.session_state.verify_email = reg_email
                        st.rerun()
                    elif res == "exists":
                        st.warning("Dieser Account existiert bereits und ist verifiziert.")
                    else:
                        st.error("Fehler beim Senden der E-Mail. Stimmen die Zugangsdaten in secrets.toml?")
            else:
                st.error("❌ Passwörter stimmen nicht überein oder sind kürzer als 4 Zeichen.")
                
    with tab_admin_login:
        st.subheader("Bereich für Administratoren")
        admin_user = st.text_input("Benutzername", key="admin_user")
        admin_pass = st.text_input("Passwort", type="password", key="admin_pass")
        
        if st.button("Als Admin einloggen", key="btn_admin_login"):
            if admin_user == "admin" and admin_pass == "admin123":
                st.session_state.authenticated = True
                st.session_state.is_admin = True 
                st.rerun()
            else:
                st.error("❌ Falsche Admin-Zugangsdaten.")
    st.stop() 

# --- HAUPT-APP ---
FILE_PATH = "data/person_db.json"
SAMPLING_RATE_HZ = 500

user_data = Person.load_person_data(FILE_PATH)
name_list = [f"{p.get('firstname', '')} {p.get('lastname', '')}".strip() for p in user_data] if user_data else []

with st.sidebar:
    st.title("🫀 EKG Analyse")
    
    if st.session_state.is_admin:
        st.success("🛡️ Als Admin eingeloggt")
    else:
        st.info("👤 Als Patient eingeloggt")
        
    if st.button("Logout", key="sidebar_logout"):
        st.session_state.authenticated = False
        st.session_state.is_admin = False
        st.session_state.user_email = None
        st.rerun()
    st.markdown("---")
    
    st.write("🎨 **Theme anpassen:**")
    st.caption("Nutze das Menü oben rechts (⋮) -> Settings -> Theme")
        
    st.markdown("---")
    
    # --- DATENSCHUTZ FILTER ---
    if st.session_state.is_admin:
        if name_list:
            st.session_state.aktuelle_versuchsperson = st.selectbox('Versuchsperson wählen:', options=name_list, key="admin_person_select")
        else:
            st.warning("Keine Personen in der Datenbank gefunden.")
            st.session_state.aktuelle_versuchsperson = None
    else:
        my_data = [p for p in user_data if p.get("email") == st.session_state.user_email]
        if my_data:
            st.session_state.aktuelle_versuchsperson = f"{my_data[0].get('firstname', '')} {my_data[0].get('lastname', '')}".strip()
            st.write(f"**Deine Patientenakte:** {st.session_state.aktuelle_versuchsperson}")
        else:
            st.error("Es konnte keine Patientenakte mit deiner E-Mail gefunden werden. Bitte den Admin kontaktieren.")
            st.stop() 

# --- ROLLENBASIERTE TABS ---
if st.session_state.is_admin:
    tab_dashboard, tab_verwaltung, tab_admin = st.tabs(["📊 Dashboard", "⚙️ Patientenverwaltung (Admin)", "👑 Statistiken (Admin)"])
else:
    tab_dashboard, tab_vergleich, tab_profil = st.tabs(["📊 Dashboard", "📈 Anonymer Vergleich", "👤 Mein Profil"]) 

current_person_data = next((item for item in user_data if f"{item.get('firstname', '')} {item.get('lastname', '')}".strip() == st.session_state.aktuelle_versuchsperson), None) if user_data else None

with tab_dashboard:
    if current_person_data:
        person = Person(current_person_data)
        col_info, col_plot = st.columns([1, 3])
        
        with col_info:
            if os.path.exists(person.picture_path):
                img = Image.open(person.picture_path)
                st.image(img, width=150)
            
            st.subheader(person.name)
            
            weight = current_person_data.get("weight")
            height = current_person_data.get("height")
            gender = current_person_data.get("gender", "Keine Angabe").capitalize()
            activity = current_person_data.get("activity_level", "Nicht angegeben")
            
            st.write(f"**Alter:** {person.calc_age()} Jahre (Jg. {person.birth_year})")
            st.write(f"**Geschlecht:** {gender}")
            
            if weight and height:
                bmi = float(weight) / ((float(height) / 100) ** 2)
                st.write(f"**Größe/Gewicht:** {height} cm | {weight} kg")
                st.write(f"**BMI:** {bmi:.1f}")
            
            st.write(f"**Aktivitätslevel:** {activity}")
            
            st.markdown("---")
            st.write(f"**Max HF:** {person.calc_max_hr()} bpm")
            
            if person.ekg_tests:
                test_options = [f"Test {t['id']} ({t['date']})" for t in person.ekg_tests]
                selected_test_str = st.selectbox("EKG-Test auswählen:", test_options, key="ekg_test_select")
                selected_id = int(selected_test_str.split(" ")[1])
                
                test_dict = next(t for t in person.ekg_tests if t["id"] == selected_id)
                ekg = EKG(ekg_id=selected_id, file_path=test_dict["result_link"])
                
                st.markdown("---")
                st.write(f"**Dauer:** {ekg.get_duration_minutes()} Min.")
            else:
                st.warning("Keine EKG-Daten vorhanden.")
                ekg = None

        with col_plot:
            if ekg and not ekg.df.empty:
                processor = SignalProcessor(ekg.df, SAMPLING_RATE_HZ)
                mean_hr = processor.calculate_mean_hr()
                anomalies_detected = processor.detect_anomalies()
                
                if mean_hr > 120:
                    st.toast('⚠️ Warnung: Durchschnittliche Herzfrequenz ist ungewöhnlich hoch!', icon='🚨')
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Ø Herzrate", f"{mean_hr:.1f} bpm")
                col_m2.metric("Anomalien erkannt", anomalies_detected)
                
                if generate_pdf_report:
                    pdf_data = generate_pdf_report(person.name, person.calc_age(), mean_hr, str(anomalies_detected))
                    col_m3.download_button(label="📄 PDF Report Export", data=pdf_data, file_name=f"EKG_Report_{person.lastname}.pdf", mime="application/pdf", key="pdf_export_btn")
                else:
                    col_m3.download_button("📄 PDF Report Export (Dummy)", "Dummy Content", file_name="report.pdf", key="pdf_export_dummy_btn")
                
                st.subheader("EKG Zeitreihe")
                max_sec = float(len(ekg.df) / SAMPLING_RATE_HZ)
                range_s = st.slider("Zeitbereich (Sekunden)", 0.0, max_sec, (0.0, 10.0), key="time_slider")
                
                reduced_df = processor.reduce_resolution(factor=2)
                signal_col = reduced_df.columns[0]
                
                fig = plot_interactive_ekg(reduced_df, signal_col, range_s[0], range_s[1])
                st.plotly_chart(fig, use_container_width=True)
            elif ekg:
                st.info("Die EKG-Datei konnte nicht geladen werden oder ist leer.")

# --- BEREICHE FÜR PATIENTEN ---
if not st.session_state.is_admin:
    
    with tab_vergleich:
        st.header("📈 Anonymer Gruppenvergleich")
        st.write("Vergleiche deine Herzrate sicher mit den Durchschnittswerten anderer Patienten. Namen und Identitäten bleiben streng vertraulich.")
        
        if user_data:
            df_stats = pd.DataFrame(user_data)
            df_stats['age'] = 2026 - df_stats['date_of_birth']
            df_stats['age_group'] = pd.cut(df_stats['age'], bins=[0, 30, 40, 50, 100], labels=["<30", "30-40", "40-50", "50+"])
            
            stats = df_stats.groupby('age_group', observed=False).size().reset_index(name='count')
            stats['avg_hr'] = [70, 75, 80, 85] 
            
            fig_comp = px.bar(stats, x='age_group', y='avg_hr', title="Durchschnittliche Herzrate nach Altersgruppe", labels={'age_group': 'Altersgruppe', 'avg_hr': 'Ø Herzrate (bpm)'})
            
            if 'ekg' in locals() and ekg and not ekg.df.empty:
                my_hr = SignalProcessor(ekg.df, SAMPLING_RATE_HZ).calculate_mean_hr()
                fig_comp.add_hline(y=my_hr, line_dash="dash", line_color="red", annotation_text=f"Du ({my_hr:.1f} bpm)")
                
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Noch nicht genügend Daten für einen Vergleich.")

    with tab_profil:
        st.header("👤 Mein Profil bearbeiten")
        st.write("Hier kannst du deine persönlichen Daten und Gesundheitswerte aktualisieren.")
        
        if current_person_data:
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.subheader("Basisdaten")
                new_fname = st.text_input("Vorname", value=current_person_data.get("firstname", ""))
                new_lname = st.text_input("Nachname", value=current_person_data.get("lastname", ""))
                new_year = st.number_input("Geburtsjahr", min_value=1900, max_value=2026, value=int(current_person_data.get("date_of_birth", 2000)))
                
                gender_options = ["male", "female", "diverse"]
                current_gender = current_person_data.get("gender", "male")
                gender_idx = gender_options.index(current_gender) if current_gender in gender_options else 0
                new_gender = st.selectbox("Geschlecht", gender_options, index=gender_idx)

            with col_p2:
                st.subheader("Körper- & Fitnessdaten")
                new_weight = st.number_input("Gewicht (kg)", min_value=30.0, max_value=200.0, value=float(current_person_data.get("weight", 75.0)), step=0.5)
                new_height = st.number_input("Größe (cm)", min_value=100, max_value=250, value=int(current_person_data.get("height", 175)))
                
                activity_options = ["Sitzend (Büro)", "Leicht aktiv", "Sportlich aktiv", "Leistungssportler"]
                current_activity = current_person_data.get("activity_level", "Leicht aktiv")
                activity_idx = activity_options.index(current_activity) if current_activity in activity_options else 1
                new_activity = st.selectbox("Aktivitätslevel", activity_options, index=activity_idx)
                
                if new_height > 0:
                    bmi = new_weight / ((new_height / 100) ** 2)
                    st.info(f"📊 Dein aktueller BMI: **{bmi:.1f}**")
            
            st.markdown("---")
            if st.button("💾 Änderungen sicher in der Akte speichern", use_container_width=True):
                for person_dict in user_data:
                    if person_dict.get("email") == st.session_state.user_email:
                        person_dict["firstname"] = new_fname
                        person_dict["lastname"] = new_lname
                        person_dict["date_of_birth"] = new_year
                        person_dict["gender"] = new_gender
                        person_dict["weight"] = new_weight
                        person_dict["height"] = new_height
                        person_dict["activity_level"] = new_activity
                        break
                
                try:
                    with open(FILE_PATH, "w", encoding="utf-8") as f:
                        json.dump(user_data, f, indent=4, ensure_ascii=False)
                    st.success("✅ Dein Profil und deine Gesundheitsdaten wurden erfolgreich aktualisiert!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Fehler beim Speichern: {e}")

# --- ADMIN BEREICHE ---
if st.session_state.is_admin:
    with tab_verwaltung:
        st.header("Patientenverwaltung (Admin-Bereich)")
        st.write("### 📋 Alle Patienten im Überblick")
        if user_data:
            df_patients = pd.DataFrame(user_data)
            cols_to_show = ["id", "firstname", "lastname", "date_of_birth", "gender"]
            st.dataframe(df_patients[cols_to_show], use_container_width=True)
        else:
            st.info("Keine Patienten in der Datenbank.")
            
        st.markdown("---")
        v_col1, v_col2 = st.columns(2)
        with v_col1:
            st.subheader("Neue Person anlegen")
            st.text_input("Vorname", key="new_fname")
            st.text_input("Nachname", key="new_lname")
            st.number_input("Geburtsjahr", min_value=1900, max_value=2026, key="new_year")
            st.file_uploader("Bild hochladen", key="new_pic")
            st.button("Person speichern", key="save_new_person")
        with v_col2:
            st.subheader("Bestehende bearbeiten")
            if name_list:
                st.selectbox("Zu bearbeitende Person:", name_list, key="edit_person_select")
                st.text_input("Neuer Vorname", key="edit_fname")
                st.text_input("Neuer Nachname", key="edit_lname")
                st.button("Änderungen sichern", key="save_edit_person")
            else:
                st.warning("Es gibt noch keine Personen zum Bearbeiten.")

    with tab_admin:
        st.header("Statistiken & Systemauswertung")
        st.write("### Anonymisierte Systemübersicht")
        admin_col1, admin_col2 = st.columns(2)
        admin_col1.metric("Ø Herzrate (Gesamtgruppe)", "74 bpm", "-2 bpm")
        admin_col2.metric("Anomalie-Häufigkeit", "3.2 %", "+0.5 %")
        
        mock_stats = pd.DataFrame({
            "Altersgruppe": ["20-30", "31-40", "41-50", "51-60", "60+"],
            "Durchschnitt_HR": [70, 72, 75, 78, 82]
        })
        fig_admin = px.bar(mock_stats, x="Altersgruppe", y="Durchschnitt_HR", title="Durchschnittliche Herzrate nach Alter")
        st.plotly_chart(fig_admin)