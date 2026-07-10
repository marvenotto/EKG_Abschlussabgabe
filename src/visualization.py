import plotly.express as px
import pandas as pd

def plot_interactive_ekg(df: pd.DataFrame, signal_col: str, start_s: float, end_s: float, sr: int = 500):
    """
    Erstellt ein interaktives Liniendiagramm inklusive Range-Slider für einen frei wählbaren EKG-Zeitbereich.
    """
    start_idx = int(start_s * sr)
    end_idx = int(end_s * sr)
    
    df_window = df.iloc[start_idx:end_idx].copy()
    
    # Erstellung einer synchronisierten Zeitachse in Sekunden
    df_window['Time_s'] = [start_s + (i / sr) for i in range(len(df_window))]
    
    fig = px.line(
        df_window, 
        x='Time_s', 
        y=signal_col, 
        title="Interaktives EKG-Signal",
        labels={'Time_s': 'Zeit (Sekunden)', signal_col: 'Amplitude (mV)'}
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        xaxis=dict(rangeslider=dict(visible=True))
    )
    return fig