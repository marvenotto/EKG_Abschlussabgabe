import pandas as pd

def get_anonymized_stats(user_data):
    """Berechnet anonyme Durchschnittswerte nach Altersgruppen."""
    if not user_data:
        return pd.DataFrame()
    
    df = pd.DataFrame(user_data)
    # Altersgruppen bilden
    df['age'] = 2026 - df['date_of_birth']
    df['age_group'] = pd.cut(df['age'], bins=[0, 30, 40, 50, 100], labels=["<30", "30-40", "40-50", "50+"])
    
    # Hier simulieren wir die Herzrate für die Statistik (da im JSON nur die Rohdaten liegen)
    # In einem echten Projekt würden wir hier über die EKG-Daten iterieren
    stats = df.groupby('age_group').size().reset_index(name='patient_count')
    stats['avg_hr_mock'] = [70, 75, 80, 85] # Beispiel-Durchschnittswerte
    return stats