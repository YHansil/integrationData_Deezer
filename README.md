# OpenSound Pro — Intégration & analyse de données musicales (2015–2025)

Ce projet met en place une mini **chaîne d’intégration de données (ETL)** et un **dashboard Streamlit** pour explorer l’évolution des tendances musicales sur la période **2015–2025**.

L’application :
- récupère des classements **Billboard Hot 100** (dataset historique),
- enrichit les titres avec des métadonnées (genre, durée, date de sortie) via **iTunes Search API**,
- tente d’estimer l’**origine des artistes** via **MusicBrainz**,
- stocke le tout dans une base **SQLite** (`opensound.db`),
- propose des visualisations interactives (Altair) dans une interface Streamlit.

## 🎯 Objectif

Le but est de disposer d’un **outil d’analyse “music intelligence”** permettant de :
- suivre les **genres dominants** et leurs bascules dans le temps,
- comprendre des **effets saisonniers** (été/hiver) sur les hits,
- identifier les **artistes les plus présents** dans les classements (hall of fame) et les nouveaux entrants (rookies),
- esquisser une **cartographie du marché** (parts de marché par genre, origines d’artistes lorsque disponible).

## 🧱 Architecture (fichiers principaux)

- `etl.py`
  - crée/initialise les tables SQLite `tracks` et `charts`
  - télécharge et filtre le dataset Billboard (2015–2025)
  - enrichit les titres (iTunes) et l’origine des artistes (MusicBrainz)
  - alimente `opensound.db`

- `dashboard.py`
  - application **Streamlit**
  - charge les données depuis `opensound.db`
  - propose plusieurs vues :
    - **Dashboard principal** (KPIs + évolution durée moyenne)
    - **Analyse saisonnière** (genres par saison)
    - **Hall of Fame & Rookies**
    - **Cartographie du marché**

- `run_all.ps1`
  - script PowerShell pour installer les dépendances et lancer l’app.

## 🚀 Lancer le projet

### Prérequis
- Python 3.9+ (recommandé)

### Installation et exécution (Windows)

Depuis PowerShell :

```powershell
./run_all.ps1
```

Le script installe les dépendances puis lance :

```bash
python -m streamlit run dashboard.py
```

### Installation manuelle (tous OS)

```bash
python -m pip install streamlit pandas requests altair
python -m streamlit run dashboard.py
```

## 🔄 Charger / régénérer les données

Dans l’application, utilisez le bouton **« Forcer l'extraction Billboard »** dans la barre latérale.

Cela :
1. recrée/met à jour le schéma SQLite,
2. télécharge les charts historiques,
3. enrichit et insère les titres.

## 📝 Notes & limites

- Le genre **"Pop"** peut apparaître de manière sur-représentée : il est utilisé comme **valeur par défaut** lorsque l’API iTunes ne retourne pas de correspondance exploitable (ou en cas de limitation).
- L’origine des artistes (**MusicBrainz**) est volontairement appelée de façon parcimonieuse (ex. 1 artiste sur 10) pour limiter les requêtes ; beaucoup de valeurs peuvent rester à `Inconnu`.
- `opensound.db` est une base locale : si vous la supprimez, l’application repartira de zéro lors de la prochaine extraction.

## 📚 Sources de données / APIs

- Dataset Billboard Hot 100 (JSON) : https://github.com/mhollingshead/billboard-hot-100
- iTunes Search API : https://affiliate.itunes.apple.com/resources/documentation/itunes-store-web-service-search-api/
- MusicBrainz API : https://musicbrainz.org/doc/MusicBrainz_API
