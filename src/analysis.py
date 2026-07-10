import pandas as pd

def get_anonymized_stats(user_data: list) -> pd.DataFrame:
    """
    Berechnet anonymisierte demografische Durchschnittswerte nach Altersgruppen
    für die statistische Auswertung im Admin-Dashboard.
    """
    if not user_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(user_data)
    
    # Altersgruppen auf Basis des Geburtsjahres bestimmen
    df['age'] = 2026 - df['date_of_birth']
    df['age_group'] = pd.cut(
        df['age'], 
        bins=[0, 30, 40, 50, 100], 
        labels=["<30", "30-40", "40-50", "50+"]
    )
    
    # Aggregation der Patientenzahlen pro Altersgruppe
    stats = df.groupby('age_group', observed=False).size().reset_index(name='patient_count')
    
    # Repräsentative Mock-Werte für die Visualisierung der Herzrate
    stats['avg_hr_mock'] = [70, 75, 80, 85]
    return stats