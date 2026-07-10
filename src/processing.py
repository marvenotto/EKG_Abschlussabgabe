import pandas as pd
import numpy as np
import neurokit2 as nk

class SignalProcessor:
    """Klasse für die Verarbeitung und Analyse von EKG-Signalen."""
    
    def __init__(self, df: pd.DataFrame, sampling_rate: int = 500):
        self.df = df
        self.sr = sampling_rate
        # Wir gehen davon aus, dass die Signal-Spalte "ECG" heißt. Ggf. anpassen!
        self.signal_col = "ECG" if "ECG" in df.columns else df.columns[0]

    def reduce_resolution(self, factor: int = 5) -> pd.DataFrame:
        """
        Reduziert die Auflösung der Datenbank für schnelleres Plotten in Streamlit.
        Nimmt nur jeden n-ten Datenpunkt (Optimierte Datenverarbeitung).
        """
        if self.df.empty:
            return self.df
        return self.df.iloc[::factor, :].copy()

    def calculate_mean_hr(self) -> float:
        """Berechnet die durchschnittliche Herzrate über den gesamten Zeitraum."""
        if self.df.empty:
            return 0.0
        try:
            # NeuroKit2 für genaue R-Zacken Erkennung
            signals, info = nk.ecg_process(self.df[self.signal_col], sampling_rate=self.sr)
            mean_hr = signals["ECG_Rate"].mean()
            return float(mean_hr)
        except Exception:
            return 0.0

    def detect_anomalies(self) -> int:
        """Automatisierte Erkennung von Anomalien (Extra-Funktion)."""
        if self.df.empty:
            return 0
        try:
            # Simple Anomalie-Erkennung: Herzraten außerhalb von 40-180 bpm
            signals, _ = nk.ecg_process(self.df[self.signal_col], sampling_rate=self.sr)
            anomalies = signals[(signals["ECG_Rate"] > 180) | (signals["ECG_Rate"] < 40)]
            return len(anomalies)
        except Exception:
            return 0