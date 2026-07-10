import importlib
import json
import os
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image

try:
    from .models import Person, EKG
    from .processing import SignalProcessor
    from .visualization import plot_interactive_ekg
    import src.auth as auth
    from .pdf_generator import generate_pdf_report
except ImportError:  # pragma: no cover - fallback for direct execution
    from src.models import Person, EKG
    from src.processing import SignalProcessor
    from src.visualization import plot_interactive_ekg
    import src.auth as auth
    from src.pdf_generator import generate_pdf_report


importlib.reload(auth)


def run_dashboard() -> None:
    """Startet die Streamlit-App für die EKG-Analyse."""
    st.set_page_config(page_title="EKG Dashboard", layout="wide", initial_sidebar_state="expanded")

    # Session State initialisieren
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "verify_email" not in st.session_state:
        st.session_state.verify_email = None
    if "setup_profile_email" not in st.session_state:
        st.session_state.setup_profile_email = None
    if "is_admin" not in st.session_state:
        st.session_state.is_admin = False
    if "user_email" not in st.session_state:
        st.session_state.user_email = None
    if "reset_email" not in st.session_state:
        st.session_state.reset_email = None
    if "reset_code_sent" not in st.session_state:
        st.session_state.reset_code_sent = None

    # Authentifizierung und Login-Flow
    if not st.session_state.authenticated:
        st.title("🔒 Willkommen zur EKG Analyse")

        if st.session_state.verify_email:
            st.info(f"📧 Wir haben eine E-Mail an **{st.session_state.verify_email}** gesendet.")
            code_input = st.text_input("Bitte gib den 6-stelligen Code ein:")

            if st.button("Code bestätigen", key="auth_code_confirm"):
                if auth.verify_code(st.session_state.verify_email, code_input):
                    st.session_state.setup_profile_email = st.session_state.verify_email
                    st.session_state.verify_email = None
                    st.rerun()
                else:
                    st.error("❌ Falscher Code. Bitte erneut versuchen.")

            if st.button("Abbrechen", key="auth_code_cancel"):
                st.session_state.verify_email = None
                st.rerun()

            st.stop()

        if st.session_state.setup_profile_email:
            st.success("✅ E-Mail erfolgreich verifiziert!")
            st.header("👋 Willkommen! Lass uns dein Profil einrichten.")
            st.write("Bitte gib deine Gesundheitsdaten ein, damit wir deine EKG-Werte korrekt analysieren können.")

            col_setup1, col_setup2 = st.columns(2)
            with col_setup1:
                st.subheader("Basisdaten")
                setup_fname = st.text_input("Vorname", key="setup_fname")
                setup_lname = st.text_input("Nachname", key="setup_lname")
                setup_year = st.number_input("Geburtsjahr", min_value=1900, max_value=2026, value=2000, key="setup_year")
                setup_gender = st.selectbox("Geschlecht", ["male", "female", "diverse"], key="setup_gender")

            with col_setup2:
                st.subheader("Körper- & Fitnessdaten")
                setup_weight = st.number_input("Gewicht (kg)", min_value=30.0, max_value=200.0, value=75.0, step=0.5, key="setup_weight")
                setup_height = st.number_input("Größe (cm)", min_value=100, max_value=250, value=175, key="setup_height")
                setup_activity = st.selectbox("Aktivitätslevel", ["Sitzend (Büro)", "Leicht aktiv", "Sportlich aktiv", "Leistungssportler"], key="setup_activity")

            if st.button("💾 Profil speichern & Registrierung abschließen", use_container_width=True, key="setup_save_btn"):
                if setup_fname and setup_lname:
                    aktueller_file_path = "data/person_db.json"
                    aktuelle_personen = Person.load_person_data(aktueller_file_path)

                    if not any(p.get("email") == st.session_state.setup_profile_email for p in aktuelle_personen):
                        neue_id = max([p.get("id", 0) for p in aktuelle_personen]) + 1 if aktuelle_personen else 1

                        neue_akte = {
                            "id": neue_id,
                            "firstname": setup_fname,
                            "lastname": setup_lname,
                            "email": st.session_state.setup_profile_email,
                            "date_of_birth": setup_year,
                            "gender": setup_gender,
                            "weight": setup_weight,
                            "height": setup_height,
                            "activity_level": setup_activity,
                            "picture_path": "data/pictures/none.jpg",
                            "ekg_tests": []
                        }
                        aktuelle_personen.append(neue_akte)

                        with open(aktueller_file_path, "w", encoding="utf-8") as f:
                            json.dump(aktuelle_personen, f, indent=4, ensure_ascii=False)

                    st.session_state.setup_profile_email = None
                    st.session_state.show_success_msg = True
                    st.rerun()
                else:
                    st.error("⚠️ Bitte gib zumindest deinen Vor- und Nachnamen ein.")
            st.stop()

        if st.session_state.get("show_success_msg"):
            st.success("🎉 Profil erfolgreich erstellt! Du kannst dich jetzt einloggen.")
            st.session_state.show_success_msg = False

        tab_login, tab_register, tab_admin_login = st.tabs(["🔑 Patienten Login", "📝 Registrieren", "🛡️ Admin Zugang"])

        with tab_login:
            st.subheader("Als Patient / Nutzer anmelden")

            if not st.session_state.reset_email:
                login_email = st.text_input("E-Mail", key="login_email")
                login_password = st.text_input("Passwort", type="password", key="login_password")

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
                    if st.button("Passwort vergessen?", key="btn_forgot_pass"):
                        if login_email:
                            st.session_state.reset_email = login_email
                            st.rerun()
                        else:
                            st.warning("Bitte gib deine E-Mail-Adresse in das Feld ein, um das Passwort zurückzusetzen.")

            else:
                st.info(f"Passwort-Reset für: **{st.session_state.reset_email}**")

                if not st.session_state.reset_code_sent:
                    if st.button("Bestätigungs-Code per E-Mail anfordern"):
                        with st.spinner("Sende Code..."):
                            smtp_user = st.secrets["email"]
                            smtp_pass = st.secrets["password"]
                            res = auth.send_reset_code(st.session_state.reset_email, smtp_user, smtp_pass)

                            if res == "not_found":
                                st.error("Diese E-Mail ist nicht registriert oder noch nicht verifiziert.")
                                st.session_state.reset_email = None
                            elif res == "error":
                                st.error("Fehler beim Senden der E-Mail.")
                            else:
                                st.session_state.reset_code_sent = res
                                st.rerun()

                    if st.button("Abbrechen", key="btn_reset_cancel_1"):
                        st.session_state.reset_email = None
                        st.rerun()
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
                    with st.spinner("Sende Bestätigungs-E-Mail..."):
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
                if admin_user.strip() == "admin" and admin_pass.strip() == "admin123":
                    st.session_state.authenticated = True
                    st.session_state.is_admin = True
                    st.rerun()
                else:
                    st.error("❌ Falsche Admin-Zugangsdaten.")
        st.stop()

    # Daten laden und Sidebar konfigurieren
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

        if st.session_state.is_admin:
            if name_list:
                st.session_state.aktuelle_versuchsperson = st.selectbox("Versuchsperson wählen:", options=name_list, key="admin_person_select")
            else:
                st.warning("Keine Personen in der Datenbank gefunden.")
                st.session_state.aktuelle_versuchsperson = None
        else:
            my_data = [p for p in user_data if p.get("email") == st.session_state.user_email]

            if my_data:
                st.session_state.aktuelle_versuchsperson = f"{my_data[0].get('firstname', '')} {my_data[0].get('lastname', '')}".strip()
                st.write(f"**Deine Patientenakte:** {st.session_state.aktuelle_versuchsperson}")
            else:
                neue_id = max([p.get("id", 0) for p in user_data]) + 1 if user_data else 1
                vorlaeufiger_name = st.session_state.user_email.split("@")[0].capitalize()

                neue_akte = {
                    "id": neue_id,
                    "firstname": vorlaeufiger_name,
                    "lastname": "Neu",
                    "email": st.session_state.user_email,
                    "date_of_birth": 2000,
                    "gender": "male",
                    "weight": 75.0,
                    "height": 175,
                    "activity_level": "Leicht aktiv",
                    "picture_path": "data/pictures/none.jpg",
                    "ekg_tests": []
                }
                user_data.append(neue_akte)

                with open(FILE_PATH, "w", encoding="utf-8") as f:
                    json.dump(user_data, f, indent=4, ensure_ascii=False)

                st.rerun()

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
                        st.toast("⚠️ Warnung: Durchschnittliche Herzfrequenz ist ungewöhnlich hoch!", icon="🚨")

                    col_m1, col_m2, col_m3 = st.columns(3)
                    col_m1.metric("Ø Herzrate", f"{mean_hr:.1f} bpm")
                    col_m2.metric("Anomalien erkannt", anomalies_detected)

                    if generate_pdf_report:
                        pdf_data = generate_pdf_report(person.name, person.calc_age(), mean_hr, str(anomalies_detected))
                        st.download_button(label="📄 PDF Report Export", data=pdf_data, file_name=f"EKG_Report_{person.lastname}.pdf", mime="application/pdf", key="pdf_export_btn")
                    else:
                        st.download_button("📄 PDF Report Export (Dummy)", "Dummy Content", file_name="report.pdf", key="pdf_export_dummy_btn")

                    st.subheader("EKG Zeitreihe")
                    max_sec = float(len(ekg.df) / SAMPLING_RATE_HZ)
                    range_s = st.slider("Zeitbereich (Sekunden)", 0.0, max_sec, (0.0, 10.0), key="time_slider")

                    reduced_df = processor.reduce_resolution(factor=2)
                    signal_col = reduced_df.columns[0]

                    fig = plot_interactive_ekg(reduced_df, signal_col, range_s[0], range_s[1])
                    st.plotly_chart(fig, use_container_width=True)
                elif ekg:
                    st.info("Die EKG-Datei konnte nicht geladen werden oder ist leer.")

    if not st.session_state.is_admin:
        with tab_vergleich:
            st.header("📈 Anonymer Gruppenvergleich")
            st.write("Vergleiche deine Herzrate sicher mit den Durchschnittswerten anderer Patienten. Namen und Identitäten bleiben streng vertraulich.")

            if user_data:
                df_stats = pd.DataFrame(user_data)
                df_stats["age"] = 2026 - df_stats["date_of_birth"]
                df_stats["age_group"] = pd.cut(df_stats["age"], bins=[0, 30, 40, 50, 100], labels=["<30", "30-40", "40-50", "50+"])

                stats = df_stats.groupby("age_group", observed=False).size().reset_index(name="count")
                stats["avg_hr"] = [70, 75, 80, 85]

                fig_comp = px.bar(stats, x="age_group", y="avg_hr", title="Durchschnittliche Herzrate nach Altersgruppe", labels={"age_group": "Altersgruppe", "avg_hr": "Ø Herzrate (bpm)"})

                if "ekg" in locals() and ekg and not ekg.df.empty:
                    my_hr = SignalProcessor(ekg.df, SAMPLING_RATE_HZ).calculate_mean_hr()
                    fig_comp.add_hline(y=my_hr, line_dash="dash", line_color="red", annotation_text=f"Du ({my_hr:.1f} bpm)")

                st.plotly_chart(fig_comp, use_container_width=True)
            else:
                st.info("Noch nicht genügend Daten für einen Vergleich.")

        with tab_profil:
            st.header("👤 Mein Profil bearbeiten")
            st.write("Hier kannst du deine persönlichen Daten aktualisieren, ein Profilbild hochladen und neue EKG-Messungen einreichen.")

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

                    st.markdown("---")
                    st.subheader("🖼️ Profilbild hochladen")
                    uploaded_picture = st.file_uploader("Wähle ein Profilbild (JPG/PNG):", type=["jpg", "jpeg", "png"], key="profile_pic_uploader")

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
                    st.subheader("📥 Neue EKG-Daten hochladen")
                    uploaded_ekg = st.file_uploader("Wähle eine EKG-Datei (CSV/TXT):", type=["csv", "txt"], key="ekg_data_uploader")
                    ekg_date = st.date_input("Messdatum für das EKG:", key="ekg_date_input")

                st.markdown("---")
                if st.button("💾 Änderungen und Uploads sicher speichern", use_container_width=True):
                    os.makedirs("data/pictures", exist_ok=True)
                    os.makedirs("data", exist_ok=True)

                    for person_dict in user_data:
                        if person_dict.get("email") == st.session_state.user_email:
                            person_dict["firstname"] = new_fname
                            person_dict["lastname"] = new_lname
                            person_dict["date_of_birth"] = new_year
                            person_dict["gender"] = new_gender
                            person_dict["weight"] = new_weight
                            person_dict["height"] = new_height
                            person_dict["activity_level"] = new_activity

                            if uploaded_picture is not None:
                                file_extension = os.path.splitext(uploaded_picture.name)[1]
                                target_pic_path = f"data/pictures/user_{person_dict['id']}{file_extension}"
                                with open(target_pic_path, "wb") as f:
                                    f.write(uploaded_picture.getbuffer())
                                person_dict["picture_path"] = target_pic_path

                            if uploaded_ekg is not None:
                                bestehende_tests = person_dict.get("ekg_tests", [])
                                neue_ekg_id = max([t.get("id", 0) for t in bestehende_tests]) + 1 if bestehende_tests else 1
                                target_ekg_path = f"data/ekg_{person_dict['id']}_test_{neue_ekg_id}.csv"
                                with open(target_ekg_path, "wb") as f:
                                    f.write(uploaded_ekg.getbuffer())
                                neuer_test_eintrag = {
                                    "id": neue_ekg_id,
                                    "date": ekg_date.strftime("%d.%m.%Y"),
                                    "result_link": target_ekg_path
                                }
                                if "ekg_tests" not in person_dict:
                                    person_dict["ekg_tests"] = []
                                person_dict["ekg_tests"].append(neuer_test_eintrag)
                                st.toast(f"▶️ EKG Test {neue_ekg_id} erfolgreich hinzugefügt!", icon="📈")
                            break

                    try:
                        with open(FILE_PATH, "w", encoding="utf-8") as f:
                            json.dump(user_data, f, indent=4, ensure_ascii=False)
                        st.success("✅ Dein Profil, Bild und EKG-Daten wurden erfolgreich aktualisiert!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Fehler beim Speichern: {e}")

    if st.session_state.is_admin:
        with tab_verwaltung:
            st.header("Patientenverwaltung (Admin-Bereich)")
            st.write("### 📋 Alle Patienten im Überblick")
            if user_data:
                df_patients = pd.DataFrame(user_data)
                cols_to_show = ["id", "firstname", "lastname", "email", "date_of_birth"]
                cols_to_show = [c for c in cols_to_show if c in df_patients.columns]
                st.dataframe(df_patients[cols_to_show], use_container_width=True)
            else:
                st.info("Keine Patienten in der Datenbank.")

            st.markdown("---")
            v_col1, v_col2 = st.columns(2)

            with v_col1:
                st.subheader("Neue Person anlegen")
                new_fname = st.text_input("Vorname", key="new_fname")
                new_lname = st.text_input("Nachname", key="new_lname")
                new_email = st.text_input("E-Mail (für Patienten-Login)", key="new_email_input")
                new_year = st.number_input("Geburtsjahr", min_value=1900, max_value=2026, value=2000, key="new_year")

                if st.button("➕ Person speichern", key="save_new_person"):
                    if new_fname and new_lname and new_email:
                        new_id = max([p.get("id", 0) for p in user_data]) + 1 if user_data else 1

                        new_person = {
                            "id": new_id,
                            "firstname": new_fname,
                            "lastname": new_lname,
                            "email": new_email,
                            "date_of_birth": new_year,
                            "gender": "Keine Angabe",
                            "weight": 70.0,
                            "height": 170,
                            "activity_level": "Nicht angegeben",
                            "picture_path": "data/pictures/none.jpg",
                            "ekg_tests": []
                        }
                        user_data.append(new_person)

                        with open(FILE_PATH, "w", encoding="utf-8") as f:
                            json.dump(user_data, f, indent=4, ensure_ascii=False)

                        st.success(f"✅ Akte für {new_fname} {new_lname} wurde erfolgreich angelegt!")
                        st.rerun()
                    else:
                        st.error("⚠️ Bitte Vorname, Nachname UND E-Mail eintragen.")

            with v_col2:
                st.subheader("Bestehende bearbeiten & löschen")
                if name_list:
                    selected_name = st.selectbox("Zu bearbeitende Person:", name_list, key="edit_person_select")
                    person_to_edit = next((p for p in user_data if f"{p.get('firstname', '')} {p.get('lastname', '')}".strip() == selected_name), None)

                    if person_to_edit:
                        edit_fname = st.text_input("Vorname", value=person_to_edit.get("firstname", ""))
                        edit_lname = st.text_input("Nachname", value=person_to_edit.get("lastname", ""))
                        edit_email = st.text_input("E-Mail", value=person_to_edit.get("email", ""))
                        edit_year = st.number_input("Geburtsjahr", min_value=1900, max_value=2026, value=int(person_to_edit.get("date_of_birth", 2000)))

                        col_btn1, col_btn2 = st.columns(2)
                        with col_btn1:
                            if st.button("💾 Änderungen sichern", use_container_width=True):
                                person_to_edit["firstname"] = edit_fname
                                person_to_edit["lastname"] = edit_lname
                                person_to_edit["email"] = edit_email
                                person_to_edit["date_of_birth"] = edit_year

                                with open(FILE_PATH, "w", encoding="utf-8") as f:
                                    json.dump(user_data, f, indent=4, ensure_ascii=False)
                                st.success("✅ Aktualisiert!")
                                st.rerun()

                        with col_btn2:
                            if st.button("🗑️ Profil löschen", type="primary", use_container_width=True):
                                user_data.remove(person_to_edit)

                                with open(FILE_PATH, "w", encoding="utf-8") as f:
                                    json.dump(user_data, f, indent=4, ensure_ascii=False)
                                st.success("🗑️ Akte wurde restlos entfernt!")
                                st.rerun()
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


if __name__ == "__main__":
    import subprocess
    import sys

    env = os.environ.copy()
    env["EKG_MAIN_DIRECT_RUN"] = "1"
    subprocess.run([sys.executable, "-m", "streamlit", "run", str(Path(__file__).resolve().parents[1] / "main.py")], env=env, check=True)
