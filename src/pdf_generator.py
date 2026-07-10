from fpdf import FPDF
import os

def generate_pdf_report(name: str, age: int, mean_hr: float, anomalies: str) -> bytes:
    """Erstellt einen PDF-Report mit den wichtigsten EKG-Ergebnissen."""
    pdf = FPDF()
    pdf.add_page()
    
    # Titel
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Medizinischer EKG-Untersuchungsbericht", ln=True, align='C')
    pdf.ln(10)
    
    # Patienteninfos
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Patienten-Name: {name}", ln=True)
    pdf.cell(0, 10, f"Alter: {age} Jahre", ln=True)
    pdf.ln(5)
    
    # Ergebnisse
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "Diagnostische Ergebnisse:", ln=True)
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, f"Durchschnittliche Herzfrequenz: {mean_hr:.1f} bpm", ln=True)
    pdf.cell(0, 10, f"Erkannte Anomalien: {anomalies}", ln=True)
    pdf.ln(15)
    
    # Fußzeile
    pdf.set_font("Arial", 'I', 10)
    pdf.cell(0, 10, "Befund: Der Bericht wurde automatisch vom EKG-Dashboard generiert.", ln=True)
    
    temp_file = "temp_report.pdf"
    pdf.output(temp_file)

    with open(temp_file, "rb") as f:
        pdf_bytes = f.read()

    if os.path.exists(temp_file):
        os.remove(temp_file)
        
    return pdf_bytes