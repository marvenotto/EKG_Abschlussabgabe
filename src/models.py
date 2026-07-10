import json
import os
import pandas as pd
from typing import List, Dict

class Person:
    """Modell zur Repräsentation, Altersberechnung und Verwaltung von Patientendaten."""
    
    def __init__(self, data_dict: dict):
        self.id = data_dict.get("id")
        self.firstname = data_dict.get("firstname", "")
        self.lastname = data_dict.get("lastname", "")
        self.name = f"{self.firstname} {self.lastname}".strip() or "Unbekannt"
        self.birth_year = data_dict.get("date_of_birth", 2000)
        self.picture_path = data_dict.get("picture_path", "data/pictures/none.jpg")
        self.ekg_tests = data_dict.get("ekg_tests", [])

    def calc_age(self, current_year: int = 2026) -> int:
        """Berechnet das aktuelle Alter der Person."""
        return current_year - self.birth_year

    def calc_max_hr(self) -> int:
        """Berechnet die maximale Herzfrequenz nach der medizinischen Faustregel (220 - Alter)."""
        return 220 - self.calc_age()

    @staticmethod
    def load_person_data(filepath: str) -> List[Dict]:
        """Lädt die gesamte Personendatenbank aus einer JSON-Datei."""
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)


class EKG:
    """Modell zur Repräsentation und zum automatisierten Laden eines EKG-Tests."""
    
    def __init__(self, ekg_id: int, file_path: str, sampling_rate: int = 500):
        self.id = ekg_id
        self.file_path = file_path
        self.sampling_rate = sampling_rate
        self.df = self._load_data()

    def _load_data(self) -> pd.DataFrame:
        """Lädt die EKG-Rohdaten flexibel aus einer Text- oder CSV-Datei."""
        if os.path.exists(self.file_path):
            try:
                return pd.read_csv(self.file_path, sep=None, engine='python')
            except Exception:
                return pd.DataFrame()
        return pd.DataFrame()
    
    def get_duration_minutes(self) -> float:
        """Berechnet die Gesamtlänge der EKG-Zeitreihe in Minuten."""
        if self.df.empty:
            return 0.0
        total_seconds = len(self.df) / self.sampling_rate
        return round(total_seconds / 60, 2)