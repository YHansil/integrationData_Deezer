import streamlit as st
import sqlite3
import pandas as pd
import os
from etl import fetch_historical_data

# Configuration de la page (doit être la première commande)
st.set_page_config(page_title="OpenSound Intelligence", layout="wide", initial_sidebar_state="expanded")

# --- INJECTION DE CSS PERSONNALISÉ POUR UN DESIGN ÉPURÉ ET PROFESSIONNEL ---
st.markdown("""
<style>
    /* Importation d'une police professionnelle (Inter) */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Nettoyage de l'interface par défaut de Streamlit */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Style des cartes de métriques (KPI) */
    div[data-testid="metric-container"] {
        background-color: #1e1e24;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border: 1px solid #2d2d35;
    }
    
    div[data-testid="metric-container"] > div {
        color: #e0e0e0;
    }
    
    div[data-testid="metric-container"] label {
        color: #8c8c9b !important;
        font-weight: 400 !important;
        font-size: 1rem !important;
    }

    /* Titres professionnels */
    h1, h2, h3 {
        color: #f8f9fa;
        font-weight: 600;
        letter-spacing: -0.5px;
    }
    
    h1 {
        margin-bottom: 30px;
        padding-bottom: 10px;
        border-bottom: 1px solid #2d2d35;
    }

    /* Style des onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 400;
    }
</style>
""", unsafe_allow_html=True)

st.title("OpenSound Intelligence")
st.markdown("<p style='color: #8c8c9b; font-size: 1.1rem; margin-top: -20px; margin-bottom: 30px;'>Analyse Stratégique du Marché Musical (2015-2025)</p>", unsafe_allow_html=True)

# --- CHARGEMENT DES DONNÉES ---
@st.cache_data(ttl=300) # Mise en cache pour fluidifier l'interface
def load_data():
    if not os.path.exists('opensound.db'):
        return pd.DataFrame(), pd.DataFrame()
    try:
        conn = sqlite3.connect('opensound.db')
        df_charts = pd.read_sql_query("SELECT * FROM charts", conn)
        df_tracks = pd.read_sql_query("SELECT * FROM tracks", conn)
        conn.close()
        
        if df_charts.empty or df_tracks.empty:
            return pd.DataFrame(), df_tracks
            
        df = pd.merge(df_charts, df_tracks, on='track_key')
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        return df, df_tracks
    except Exception as e:
        return pd.DataFrame(), pd.DataFrame()

with st.sidebar:
    st.markdown("### Gestion des Données")
    st.caption("Synchronisation avec le répertoire Billboard Top 100 et enrichissement via API.")
    st.write("")
    if st.button("Lancer l'extraction historique", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total, message=""):
            percent = min(current / total, 1.0) if total > 0 else 0.0
            progress_bar.progress(percent)
            status_text.caption(message)
            
        try:
            fetch_historical_data(progress_callback=update_progress)
            st.success("Synchronisation terminée.")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur système : {e}")

df, df_tracks = load_data()

if df is None or df.empty:
    st.info("La base de données est actuellement vide. Veuillez lancer l'extraction depuis le panneau latéral.")
else:
    # --- KPI GÉNÉRAUX ---
    st.markdown("### Vue d'ensemble")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Volume Analysé", f"{len(df_tracks):,}".replace(',', ' '))
    c2.metric("Artistes Uniques", f"{df_tracks['artist'].nunique():,}".replace(',', ' '))
    c3.metric("Style Dominant", df_tracks['genre'].mode()[0])
    avg_duration = df_tracks['duration_ms'].mean() / 1000 / 60
    c4.metric("Durée Moyenne", f"{avg_duration:.2f} min")

    st.markdown("<br>", unsafe_allow_html=True)

    # --- SÉPARATION EN ONGLETS POUR PLUS DE CLARTÉ ---
    tab_season, tab_longevity, tab_market = st.tabs(["Saisonnalité & Styles", "Longévité des Artistes", "Indicateurs Marché"])

    with tab_season:
        st.markdown("#### Tendances Saisonnières")
        st.caption("Comparaison des genres prédominants selon les cycles estivaux et hivernaux.")
        
        def get_season(month):
            if month in [6, 7, 8]: return "Été"
            if month in [12, 1, 2]: return "Hiver"
            return "Autres"

        df['season'] = df['month'].apply(get_season)
        summer_genres = df[df['season'] == "Été"]['genre'].value_counts().head(5)
        winter_genres = df[df['season'] == "Hiver"]['genre'].value_counts().head(5)
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Top Styles (Période Estivale)**")
            st.bar_chart(summer_genres, color="#ff9f43")
        with col2:
            st.markdown("**Top Styles (Période Hivernale)**")
            st.bar_chart(winter_genres, color="#00d2d3")

    with tab_longevity:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("#### Présence Historique")
            st.caption("Artistes cumulant le plus d'apparitions dans le classement sur la décennie.")
            top_legends = df['artist'].value_counts().head(10).reset_index()
            top_legends.columns = ['Artiste', 'Apparitions (Semaines)']
            st.dataframe(top_legends, use_container_width=True, hide_index=True)
            
        with col2:
            st.markdown("#### Émergence Récente")
            st.caption("Nouveaux entrants identifiés à partir de 2023, absents des périodes précédentes.")
            recent_artists = df[df['year'] >= 2023]['artist'].unique()
            old_artists = df[df['year'] < 2023]['artist'].unique()
            emerging = [a for a in recent_artists if a not in old_artists][:10]
            df_emerging = pd.DataFrame(emerging, columns=['Artiste Émergent'])
            st.dataframe(df_emerging, use_container_width=True, hide_index=True)

    with tab_market:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### Origine Géographique")
            st.caption("Distribution des artistes par zone d'origine (hors inconnus).")
            known_origins = df_tracks[df_tracks['artist_origin'] != 'Inconnu']
            origin_counts = known_origins['artist_origin'].value_counts().head(8)
            st.bar_chart(origin_counts, color="#5f27cd")
            
        with col2:
            st.markdown("#### Format de Production")
            st.caption("Évolution de la durée moyenne des morceaux au fil des années.")
            duration_evol = df.groupby('year')['duration_ms'].mean() / 1000
            st.line_chart(duration_evol, color="#ee5253")
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("#### Évolution des Parts de Marché (2015 vs 2024)")
        st.caption("Comparaison de la répartition des genres musicaux à 9 ans d'intervalle.")
        
        g2015 = df[df['year'] == 2015]['genre'].value_counts(normalize=True).head(5) * 100
        g2024 = df[df['year'] == 2024]['genre'].value_counts(normalize=True).head(5) * 100
        
        c_a, c_b = st.columns(2)
        with c_a:
            df_2015 = g2015.reset_index()
            df_2015.columns = ['Genre', 'Part (%)']
            df_2015['Part (%)'] = df_2015['Part (%)'].round(1).astype(str) + ' %'
            st.markdown("**Année 2015**")
            st.dataframe(df_2015, use_container_width=True, hide_index=True)
        with c_b:
            df_2024 = g2024.reset_index()
            df_2024.columns = ['Genre', 'Part (%)']
            df_2024['Part (%)'] = df_2024['Part (%)'].round(1).astype(str) + ' %'
            st.markdown("**Année 2024**")
            st.dataframe(df_2024, use_container_width=True, hide_index=True)
