import streamlit as st
import os
import pandas as pd
import plotly.express as px
from PIL import Image

# Importe aus unseren Modulen
from src.models import Person, EKG
from src.processing import SignalProcessor
from src.visualization import plot_interactive_ekg
import src.auth as auth  

# Falls du die Datei schon angelegt hast, importieren wir den PDF Generator
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
        if st.button("Code bestätigen"):
            if auth.verify_code(st.session_state.verify_email, code_input):
                st.success("✅ Account erfolgreich verifiziert! Du kannst dich jetzt einloggen.")
                st.session_state.verify_email = None 
                st.rerun()
            else:
                st.error("❌ Falscher Code. Bitte erneut versuchen.")
        if st.button("Abbrechen"):
            st.session_state.verify_email = None
            st.rerun()
        st.stop()

    tab_login, tab_register, tab_admin_login = st.tabs(["🔑 Patienten Login", "📝 Registrieren", "🛡️ Admin Zugang"])
    
    with tab_login:
        st.subheader("Als Patient / Nutzer anmelden")
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
            st.button("Passwort Reset", key="btn_reset")
                
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
                        st.warning("Dieser Account existiert bereits.")
                    else:
                        st.error("Fehler beim Senden der E-Mail.")
            else:
                st.error("❌ Passwörter stimmen nicht überein oder sind kürzer als 4 Zeichen.")
                
    with tab_admin_login:
        st.subheader("Bereich für Administratoren")
        admin_user = st.text_input("Benutzername", key="admin_user")
        admin_pass = st.text_input("Passwort", type="password", key="admin_pass")
        
        if st.button("Als Admin einloggen"):
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
        
    if st.button("Logout"):
        st.session_state.authenticated = False
        st.session_state.is_admin = False
        st.session_state.user_email = None
        st.rerun()
    st.markdown("---")
    
    theme = st.radio("🎨 Theme Switcher", ["Light Mode", "Dark Mode"])
    
    if theme == "Dark Mode":
        st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] { background-color: #0E1117; }
            [data-testid="stSidebar"] { background-color: #262730; }
            [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
            p, h1, h2, h3, h4, h5, h6, label, .stMetricValue { color: #FAFAFA !important; }
        </style>
        """, unsafe_allow_html=True)
        plot_template = "plotly_dark"
    else:
        st.markdown("""
        <style>
            [data-testid="stAppViewContainer"] { background-color: #FFFFFF; }
            [data-testid="stSidebar"] { background-color: #F0F2F6; }
            [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
            p, h1, h2, h3, h4, h5, h6, label, .stMetricValue { color: #111111 !important; }
        </style>
        """, unsafe_allow_html=True)
        plot_template = "plotly_white"
        
    st.markdown("---")
    
    # --- PRIVACY FILTER ---
    if st.session_state.is_admin:
        if name_list:
            st.session_state.aktuelle_versuchsperson = st.selectbox('Versuchsperson wählen:', options=name_list)
        else:
            st.session_state.aktuelle_versuchsperson = None
    else:
        my_data = [p for p in user_data if p.get("email") == st.session_state.user_email]
        if my_data:
            st.session_state.aktuelle_versuchsperson = f"{my_data[0].get('firstname', '')} {my_data[0].get('lastname', '')}".strip()
        else:
            st.session_state.aktuelle_versuchsperson = name_list[0] if name_list else None
            st.warning("⚠️ Bitte 'email' in der person_db.json ergänzen.")
        
        st.write(f"**Patientenakte:** {st.session_state.aktuelle_versuchsperson}")

# --- ROLLENBASIERTE TABS ---
if st.session_state.is_admin:
    tab_dashboard, tab_verwaltung, tab_admin = st.tabs(["📊 Dashboard", "⚙️ Patientenverwaltung (Admin)", "👑 Statistiken (Admin)"])
else:
    tab_dashboard, tab_vergleich = st.tabs(["📊 Dashboard", "📈 Anonymer Vergleich"]) 

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
            st.write(f"**Geburtsjahr:** {person.birth_year}")
            st.write(f"**Alter:** {person.calc_age()} Jahre")
            st.write(f"**Max HF:** {person.calc_max_hr()} bpm")
            
            if person.ekg_tests:
                test_options = [f"Test {t['id']} ({t['date']})" for t in person.ekg_tests]
                selected_test_str = st.selectbox("EKG-Test auswählen:", test_options)
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
                anomalies = processor.detect_anomalies()
                
                if mean_hr > 120:
                    st.toast('⚠️ Warnung: Durchschnittliche Herzfrequenz ist ungewöhnlich hoch!', icon='🚨')
                
                col_m1, col_m2, col_m3 = st.columns(3)
                col_m1.metric("Ø Herzrate", f"{mean_hr:.1f} bpm")
                col_m2.metric("Anomalien erkannt", anomalies)
                
                if generate_pdf_report:
                    pdf_data = generate_pdf_report(person.name, person.calc_age(), mean_hr, str(anomalies))
                    col_m3.download_button(label="📄 PDF Report Export", data=pdf_data, file_name=f"EKG_Report_{person.lastname}.pdf", mime="application/pdf")
                else:
                    col_m3.download_button("📄 PDF Report Export (Dummy)", "Dummy Content", file_name="report.pdf")
                
                st.subheader("EKG Zeitreihe")
                max_sec = float(len(ekg.df) / SAMPLING_RATE_HZ)
                range_s = st.slider("Zeitbereich (Sekunden)", 0.0, max_sec, (0.0, 10.0))
                
                reduced_df = processor.reduce_resolution(factor=2)
                signal_col = reduced_df.columns[0]
                
                fig = plot_interactive_ekg(reduced_df, signal_col, range_s[0], range_s[1])
                fig.update_layout(template=plot_template)
                st.plotly_chart(fig, use_container_width=True)
            elif ekg:
                st.info("Die EKG-Datei konnte nicht geladen werden oder ist leer.")

# --- NEUER REITER: ANONYMER VERGLEICH ---
if not st.session_state.is_admin:
    with tab_vergleich:
        st.header("📈 Dein anonymer Gruppenvergleich")
        st.write("Hier kannst du deine Herzrate sicher und anonym mit den Durchschnittswerten anderer Altersgruppen vergleichen.")
        
        if user_data:
            df_stats = pd.DataFrame(user_data)
            df_stats['age'] = 2026 - df_stats['date_of_birth']
            df_stats['age_group'] = pd.cut(df_stats['age'], bins=[0, 30, 40, 50, 100], labels=["<30", "30-40", "40-50", "50+"])
            
            stats = df_stats.groupby('age_group', observed=False).size().reset_index(name='count')
            stats['avg_hr'] = [70, 75, 80, 85] 
            
            fig_comp = px.bar(stats, x='age_group', y='avg_hr', title="Durchschnittliche Herzrate nach Altersgruppe", labels={'age_group': 'Altersgruppe', 'avg_hr': 'Ø Herzrate (bpm)'})
            fig_comp.update_layout(template=plot_template)
            
            if 'ekg' in locals() and ekg and not ekg.df.empty:
                my_hr = SignalProcessor(ekg.df, SAMPLING_RATE_HZ).calculate_mean_hr()
                fig_comp.add_hline(y=my_hr, line_dash="dash", line_color="red", annotation_text=f"Du ({my_hr:.1f} bpm)")
                
            st.plotly_chart(fig_comp, use_container_width=True)
        else:
            st.info("Noch nicht genügend Daten für einen Vergleich.")

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
            st.file_uploader("Bild hochladen")
            st.button("Person speichern")
        with v_col2:
            st.subheader("Bestehende bearbeiten")
            if name_list:
                st.selectbox("Zu bearbeitende Person:", name_list, key="edit_person_select")
                st.text_input("Neuer Vorname", key="edit_fname")
                st.text_input("Neuer Nachname", key="edit_lname")
                st.button("Änderungen sichern")
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
        fig_admin.update_layout(template=plot_template)
        st.plotly_chart(fig_admin)