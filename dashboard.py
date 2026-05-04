import streamlit as st
import sqlite3
import pandas as pd
import os
from etl import fetch_historical_data
import altair as alt

st.set_page_config(page_title="OpenSound Pro", layout="wide", initial_sidebar_state="expanded")

# --- CSS INJECTION ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    html, body, [class*="css"], .stMarkdown { font-family: 'Outfit', sans-serif; }
    .stApp { background-color: #0e0e11; color: #f4f4f5; }
    #MainMenu, footer, header {visibility: hidden;}
    
    /* Hide radio button circles for a clean menu */
    div[role="radiogroup"] > label > div:first-child { display: none; }
    div[role="radiogroup"] > label {
        background: rgba(255,255,255,0.05);
        padding: 15px 20px;
        border-radius: 8px;
        margin-bottom: 8px;
        cursor: pointer;
        transition: 0.3s;
    }
    div[role="radiogroup"] > label:hover { background: rgba(255,255,255,0.1); }
    
    /* Metrics */
    div[data-testid="metric-container"] {
        border-left: 4px solid #8b5cf6;
        background: rgba(255,255,255,0.02);
        padding: 15px 20px;
        border-radius: 0 8px 8px 0;
    }
    div[data-testid="metric-container"] > div { font-size: 2.5rem !important; color: #fff; }
    div[data-testid="metric-container"] label { color: #a1a1aa !important; font-size: 1rem !important; text-transform: uppercase; }

    /* Section Titles */
    .section-title { font-size: 1.8rem; font-weight: 700; border-bottom: 1px solid #27272a; padding-bottom: 10px; margin-bottom: 20px; margin-top: 20px; color: #e4e4e7; }
</style>
""", unsafe_allow_html=True)

# --- LOAD DATA ---
@st.cache_data(ttl=300)
def load_data():
    if not os.path.exists('opensound.db'): return pd.DataFrame(), pd.DataFrame()
    try:
        conn = sqlite3.connect('opensound.db')
        df_charts = pd.read_sql_query("SELECT * FROM charts", conn)
        df_tracks = pd.read_sql_query("SELECT * FROM tracks", conn)
        conn.close()
        if df_charts.empty or df_tracks.empty: return pd.DataFrame(), df_tracks
        df = pd.merge(df_charts, df_tracks, on='track_key')
        df['date'] = pd.to_datetime(df['date'])
        df['month'] = df['date'].dt.month
        df['year'] = df['date'].dt.year
        return df, df_tracks
    except:
        return pd.DataFrame(), pd.DataFrame()

df, df_tracks = load_data()

# --- SIDEBAR NAVIGATION (Acts like a true app menu) ---
with st.sidebar:
    st.markdown("## 🎵 OpenSound Pro")
    st.caption("Music Intelligence Platform")
    st.markdown("---")
    
    if df.empty:
        menu = "Synchronisation requise"
    else:
        menu = st.radio(
            "Navigation",
            ["📊 Dashboard Principal", "🌤️ Analyse Saisonnière", "👑 Hall of Fame & Rookies", "🌍 Cartographie du Marché"],
            label_visibility="collapsed"
        )
    
    st.markdown("---")
    st.markdown("#### Données Source")
    if st.button("🔄 Forcer l'extraction Billboard", use_container_width=True):
        p_bar, s_text = st.progress(0), st.empty()
        def up(c, t, m=""):
            p_bar.progress(min(c/t, 1.0) if t>0 else 0)
            s_text.caption(m)
        try:
            fetch_historical_data(progress_callback=up)
            st.rerun()
        except Exception as e:
            st.error(str(e))

if df is None or df.empty:
    st.warning("Aucune donnée. Utilisez le bouton dans le menu de gauche.")
    st.stop()

# --- MAIN APP ROUTING ---

if menu == "📊 Dashboard Principal":
    st.markdown("<div class='section-title'>Aperçu Global du Marché (2015-2025)</div>", unsafe_allow_html=True)
    
    # Asymmetrical layout
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        st.metric("Titres Uniques", f"{len(df_tracks):,}".replace(',', ' '))
        st.write("")
        st.metric("Artistes Classés", f"{df_tracks['artist'].nunique():,}".replace(',', ' '))
    with col2:
        st.metric("Genre Leader", df_tracks['genre'].mode()[0])
        st.write("")
        avg_dur = df_tracks['duration_ms'].mean() / 1000 / 60
        st.metric("Format Moyen", f"{avg_dur:.2f} min")
    
    with col3:
        st.markdown("**Évolution de la durée de production**")
        dur_evol = df.groupby('year')['duration_ms'].mean().reset_index()
        dur_evol['duration_sec'] = dur_evol['duration_ms'] / 1000
        chart = alt.Chart(dur_evol).mark_area(
            line={'color':'#8b5cf6'},
            color=alt.Gradient(
                gradient='linear',
                stops=[alt.GradientStop(color='#8b5cf6', offset=0), alt.GradientStop(color='rgba(139,92,246,0)', offset=1)],
                x1=1, x2=1, y1=1, y2=0
            )
        ).encode(x=alt.X('year:O', title="Année"), y=alt.Y('duration_sec:Q', title="Secondes", scale=alt.Scale(zero=False)))
        st.altair_chart(chart, use_container_width=True)

elif menu == "🌤️ Analyse Saisonnière":
    st.markdown("<div class='section-title'>Comportement des Genres par Saison</div>", unsafe_allow_html=True)
    
    st.info("💡 **Note :** Le genre 'Pop' écrase les autres car c'est la valeur attribuée par défaut lorsque l'API d'Apple (iTunes) ne trouve pas le morceau exact ou bloque nos requêtes. Vous pouvez le masquer ci-dessous.")
    exclude_pop = st.toggle("🚫 Exclure le genre 'Pop' des graphiques pour voir les vraies tendances", value=True)
    
    def get_s(m):
        if m in [6,7,8]: return "Été"
        if m in [12,1,2]: return "Hiver"
        return "Autre"
    df['season'] = df['month'].apply(get_s)
    
    # Filtrage dynamique
    df_view = df[df['genre'] != 'Pop'] if exclude_pop else df
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<h3 style='color:#f59e0b;'>Hits de l'Été</h3>", unsafe_allow_html=True)
        sg = df_view[df_view['season']=='Été']['genre'].value_counts().head(6).reset_index()
        chart_s = alt.Chart(sg).mark_bar(color='#f59e0b', cornerRadiusEnd=4).encode(
            x='count:Q', y=alt.Y('genre:N', sort='-x', title="")
        )
        st.altair_chart(chart_s, use_container_width=True)
        
    with c2:
        st.markdown("<h3 style='color:#0ea5e9;'>Hits de l'Hiver</h3>", unsafe_allow_html=True)
        wg = df_view[df_view['season']=='Hiver']['genre'].value_counts().head(6).reset_index()
        chart_w = alt.Chart(wg).mark_bar(color='#0ea5e9', cornerRadiusEnd=4).encode(
            x='count:Q', y=alt.Y('genre:N', sort='-x', title="")
        )
        st.altair_chart(chart_w, use_container_width=True)

elif menu == "👑 Hall of Fame & Rookies":
    st.markdown("<div class='section-title'>Analyse des Talents</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns([1.5, 1])
    with c1:
        st.markdown("### Les Piliers de l'Industrie")
        st.caption("Artistes ayant dominé les charts sur la décennie.")
        legends = df['artist'].value_counts().head(8).reset_index()
        legends.columns = ['Artiste', 'Semaines dans le Top 100']
        # Use a visually different table display
        st.dataframe(legends, use_container_width=True, hide_index=True)
        
    with c2:
        st.markdown("### La Relève (2023-2025)")
        st.caption("Ils viennent de percer et n'étaient pas là avant.")
        recent = df[df['year']>=2023]['artist'].unique()
        old = df[df['year']<2023]['artist'].unique()
        emerging = [a for a in recent if a not in old][:8]
        for idx, artist in enumerate(emerging):
            st.markdown(f"<div style='background:rgba(255,255,255,0.05); padding:10px; margin-bottom:5px; border-radius:5px; border-left:3px solid #10b981;'>{artist}</div>", unsafe_allow_html=True)

elif menu == "🌍 Cartographie du Marché":
    st.markdown("<div class='section-title'>Parts de Marché & Origines</div>", unsafe_allow_html=True)
    
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Bascule des genres (2015 vs 2024)**")
        g15 = df[df['year']==2015]['genre'].value_counts(normalize=True).head(4)*100
        g24 = df[df['year']==2024]['genre'].value_counts(normalize=True).head(4)*100
        
        comp = pd.DataFrame({'2015 (%)': g15, '2024 (%)': g24}).fillna(0).round(1)
        st.dataframe(comp, use_container_width=True)
        
    with c2:
        st.markdown("**Pôles d'exportation musicaux**")
        st.caption("Exclut les origines non renseignées.")
        ko = df_tracks[df_tracks['artist_origin'] != 'Inconnu']
        oc = ko['artist_origin'].value_counts().head(6).reset_index()
        chart_o = alt.Chart(oc).mark_arc(innerRadius=50).encode(
            theta=alt.Theta(field="count", type="quantitative"),
            color=alt.Color(field="artist_origin", type="nominal", legend=alt.Legend(title="Origine"))
        )
        st.altair_chart(chart_o, use_container_width=True)
