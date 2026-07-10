import plotly.express as px
import pandas as pd

def plot_interactive_ekg(df: pd.DataFrame, signal_col: str, start_s: float, end_s: float, sr: int = 500):
    """
    Erstellt ein interaktives EKG-Diagramm mit Plotly für den ausgewählten Zeitbereich.
    """
    start_idx = int(start_s * sr)
    end_idx = int(end_s * sr)
    
    df_window = df.iloc[start_idx:end_idx].copy()
    
    # Zeitachse in Sekunden erstellen
    df_window['Time_s'] = [start_s + (i / sr) for i in range(len(df_window))]
    
    fig = px.line(df_window, x='Time_s', y=signal_col, 
                  title="Interaktives EKG-Signal",
                  labels={'Time_s': 'Zeit (Sekunden)', signal_col: 'Amplitude (mV)'})
    
    fig.update_layout(
        template="plotly_dark", # Passt gut zum Dark Mode Theme-Switcher
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(rangeslider=dict(visible=True)) # Range-Slider für UX
    )
    return fig