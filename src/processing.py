import pandas as pd
import neurokit2 as nk

class SignalProcessor:
    """Klasse für die biosignalanalytische Filterung und Analyse von EKG-Zeitreihen."""
    
    def __init__(self, df: pd.DataFrame, sampling_rate: int = 500):
        self.df = df
        self.sr = sampling_rate
        self.signal_col = "ECG" if "ECG" in df.columns else df.columns[0]

    def reduce_resolution(self, factor: int = 5) -> pd.DataFrame:
        """Reduziert die Datenauflösung (Downsampling) für eine performante Visualisierung im Webinterface."""
        if self.df.empty:
            return self.df
        return self.df.iloc[::factor, :].copy()

    def calculate_mean_hr(self) -> float:
        """Berechnet die durchschnittliche Herzrate (bpm) mittels präziser R-Zacken-Detektion."""
        if self.df.empty:
            return 0.0
        try:
            signals, info = nk.ecg_process(self.df[self.signal_col], sampling_rate=self.sr)
            mean_hr = signals["ECG_Rate"].mean()
            return float(mean_hr)
        except Exception:
            return 0.0

    def detect_anomalies(self) -> int:
        """Identifiziert pathologische Abweichungen außerhalb des physiologischen Bereichs (40-180 bpm)."""
        if self.df.empty:
            return 0
        try:
            signals, _ = nk.ecg_process(self.df[self.signal_col], sampling_rate=self.sr)
            anomalies = signals[(signals["ECG_Rate"] > 180) | (signals["ECG_Rate"] < 40)]
            return len(anomalies)
        except Exception:
            return 0