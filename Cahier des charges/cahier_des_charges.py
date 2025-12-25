from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import csv

# Configuration Chrome
chrome_options = Options()
chrome_options.add_argument("--start-maximized")  # Ouvrir en plein écran
# chrome_options.add_argument("--headless")  # Décommentez pour ne pas voir le navigateur

# Initialiser le driver (assurez-vous d'avoir chromedriver installé)
driver = webdriver.Chrome(options=chrome_options)

# Liste des appellations
appellations = [
    ("Abouriou", "sud_ouest"),
    ("Alicante Bouschet", "languedoc"),
    ("Aligoté", "bourgogne"),
    ("Aligoté", "savoie"),
    ("Altesse", "savoie"),
    ("Arbane", "champagne"),
    ("Arrufiac", "sud_ouest"),
    ("Auxerrois", "alsace"),
    ("Auxerrois", "lorraine"),
    ("Barbarossa", "corse"),
    ("Baroque", "sud_ouest"),
    ("Biancu Gentile", "corse"),
    ("Bourboulenc", "rhone"),
    ("Bourboulenc", "languedoc"),
    ("Braquet", "provence"),
    ("Cabernet Franc", "bordeaux"),
    ("Cabernet Franc", "loire"),
    ("Cabernet Sauvignon", "bordeaux"),
    ("Cabernet Sauvignon", "languedoc"),
    ("Calitor", "provence"),
    ("Carignan", "languedoc"),
    ("Carignan", "rhone"),
    ("Carignan Blanc", "languedoc"),
    ("Carménère", "bordeaux"),
    ("Chardonnay", "bourgogne"),
    ("Chardonnay", "champagne"),
    ("Chasselas", "savoie"),
    ("Chasselas", "alsace"),
    ("Chenin Blanc", "loire"),
    ("Cinsault", "rhone"),
    ("Cinsault", "provence"),
    ("Clairette", "rhone"),
    ("Clairette", "languedoc"),
    ("Clairette Rose", "rhone"),
    ("Colombard", "bordeaux"),
    ("Colombard", "sud_ouest"),
    ("Counoise", "rhone"),
    ("Courbu Blanc", "sud_ouest"),
    ("César", "bourgogne"),
    ("Douce Noire", "savoie"),
    ("Duras", "sud_ouest")
]

# Fichier CSV pour stocker les URLs trouvées
with open('urls_trouvees.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Appellation', 'Région', 'URL'])
    
    for i, (appellation, region) in enumerate(appellations):
        print(f"\n[{i+1}/{len(appellations)}] Recherche: {appellation} ({region})")
        
        # Construire la requête Google
        query = f"{appellation} {region} cahier des charges AOC"
        url_recherche = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        # Ouvrir la recherche Google
        driver.get(url_recherche)
        
        print(f"Recherche ouverte: {query}")
        print("Attente de 10 secondes pour que vous cliquiez sur le premier résultat...")
        
        # Attente pour que vous cliquiez manuellement ou avec PyAutoGUI
        time.sleep(10)
        
        # Récupérer l'URL actuelle (après votre clic)
        current_url = driver.current_url
        
        # Écrire dans le CSV
        writer.writerow([appellation, region, current_url])
        print(f"URL enregistrée: {current_url[:80]}...")
        
        # Retour à Google pour la prochaine recherche
        time.sleep(2)

# Fermer le navigateur à la fin
driver.quit()
print("\n✅ Toutes les recherches ont été ouvertes !")
print("📄 URLs sauvegardées dans 'urls_trouvees.csv'")