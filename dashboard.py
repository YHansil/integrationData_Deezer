import streamlit as st
import sqlite3
import pandas as pd
import os
from etl import fetch_historical_data
from datetime import datetime

st.set_page_config(page_title="OpenSound Intelligence Dashboard", layout="wide")

st.title("🚀 OpenSound Intelligence : Analyse Stratégique (2015-2025)")

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
            
        # Merger pour avoir les infos complètes
        df = pd.merge(df_charts, df_tracks, on='track_key')
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        return df, df_tracks
    except Exception as e:
        # On ne bloque pas tout le dashboard, on renvoie du vide
        return pd.DataFrame(), pd.DataFrame()

with st.sidebar:
    st.header("⚙️ Acquisition de Données")
    st.write("Récupération du Top 100 réel (Billboard) enrichi pour chaque mois depuis 2015.")
    if st.button("⚡ Lancer l'analyse historique complète"):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(current, total, message=""):
            percent = min(current / total, 1.0) if total > 0 else 0.0
            progress_bar.progress(percent)
            status_text.text(message)
            
        try:
            fetch_historical_data(progress_callback=update_progress)
            st.success("Données historiques chargées !")
            st.rerun()
        except Exception as e:
            st.error(f"Erreur : {e}")

df, df_tracks = load_data()

if df is None or df.empty:
    st.warning("⚠️ Base de données vide. Veuillez lancer l'analyse historique via la barre latérale pour récupérer le Top 100 mondial (2015-2025).")
else:
    # --- KPI GÉNÉRAUX ---
    st.header("📊 Vue d'ensemble du Marché")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Morceaux analysés", len(df_tracks))
    c2.metric("Artistes uniques", df_tracks['artist'].nunique())
    c3.metric("Genre dominant", df_tracks['genre'].mode()[0])
    avg_duration = df_tracks['duration_ms'].mean() / 1000 / 60
    c4.metric("Durée moyenne (min)", f"{avg_duration:.2f}")

    # --- ANALYSE SAISONNIÈRE ---
    st.divider()
    st.header("☀️ Analyse Saisonnière : Quel style domine selon la période ?")
    # On définit les saisons
    def get_season(month):
        if month in [6, 7, 8]: return "Été (Juin-Août)"
        if month in [12, 1, 2]: return "Hiver (Déc-Fév)"
        return "Autres"

    df['season'] = df['month'].apply(get_season)
    summer_genres = df[df['season'] == "Été (Juin-Août)"]['genre'].value_counts().head(5)
    winter_genres = df[df['season'] == "Hiver (Déc-Fév)"]['genre'].value_counts().head(5)
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Top Styles en Été")
        st.bar_chart(summer_genres)
    with col2:
        st.subheader("Top Styles en Hiver")
        st.bar_chart(winter_genres)

    # --- LONGEVITÉ ARTISTE ---
    st.divider()
    st.header("⏳ Longévité vs Émergence")
    
    # Artistes avec le plus de semaines dans le Top 100 (toutes années confondues)
    top_legends = df['artist'].value_counts().head(10)
    
    # Artistes apparus seulement récemment (ex: 2023-2025)
    recent_artists = df[df['year'] >= 2023]['artist'].unique()
    old_artists = df[df['year'] < 2023]['artist'].unique()
    emerging = [a for a in recent_artists if a not in old_artists][:10]
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Les Piliers (Plus de présence)")
        st.table(top_legends)
    with col2:
        st.subheader("Artistes Émergents (Top 10 récents)")
        st.write(emerging)

    # --- CRITÈRES DE DÉCISION LABEL ---
    st.divider()
    st.header("🎯 Aide à la décision pour le Label")
    
    tab1, tab2, tab3 = st.tabs(["Origine Géographique", "Évolution de la Durée", "Styles Émergents"])
    
    with tab1:
        origin_counts = df_tracks['artist_origin'].value_counts().head(10)
        st.write("D'où viennent les succès mondiaux ?")
        st.bar_chart(origin_counts)
        
    with tab2:
        # Évolution de la durée moyenne par année
        duration_evol = df.groupby('year')['duration_ms'].mean() / 1000
        st.write("Les morceaux deviennent-ils plus courts ? (secondes)")
        st.line_chart(duration_evol)
        
    with tab3:
        # Comparaison des genres 2015 vs 2024
        g2015 = df[df['year'] == 2015]['genre'].value_counts(normalize=True).head(5)
        g2024 = df[df['year'] == 2024]['genre'].value_counts(normalize=True).head(5)
        st.write("Évolution des parts de marché des genres (2015 vs 2024)")
        col_a, col_b = st.columns(2)
        col_a.write("2015")
        col_a.table(g2015)
        col_b.write("2024")
        col_b.table(g2024)
