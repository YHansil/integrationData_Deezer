try {
    Write-Host "Installation des dependances..."
    python -m pip install streamlit pandas requests
    
    Write-Host "Lancement du dashboard..."
    python -m streamlit run dashboard.py
} catch {
    Write-Host "Une erreur est survenue : $_" -ForegroundColor Red
}
pause
