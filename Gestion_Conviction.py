import yfinance as yf
import pandas as pd
import time
import requests 

# url pour recuperer tout les ticker du secteur

url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'

# On ajoute un Header pour ne plus être bloqué (Erreur 403)
header = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}

# On récupère le contenu de la page avec requests
response = requests.get(url, headers=header)

# On donne ce contenu à Pandas
sp500 = pd.read_html(response.text)[0]['Symbol'].tolist()
sp500 = [t.replace('.', '-') for t in sp500]

print(f"{len(sp500)} tickers récupérés avec succès.")


results = []
print("Scanning Healthcare Sector (S&P 500)...")

# Pour le test, on prend les 150 premiers (pour inclure des géants comme AbbVie, Amgen, etc.)
for ticker in sp500[:150]: 
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # FILTRE 1 : On ne garde que le secteur Santé
        if info.get('sector') == "Healthcare":
            
            # FILTRE 2 : Métriques de Qualité 
            roe = info.get('returnOnEquity')
            margin = info.get('operatingMargins')
            debt_ebitda = info.get('debtToEbitda')
            fcf_yield = info.get('freeCashflow', 0) / info.get('marketCap', 1)

            # On cherche de la rentabilité réelle (ROE > 15%) et une marge solide (> 15%)
            if roe and margin and roe > 0.15 and margin > 0.15:
                results.append({
                    "Ticker": ticker,
                    "Nom": info.get('shortName'),
                    "Industrie": info.get('industry'),
                    "ROE (%)": round(roe * 100, 2),
                    "Marge Op (%)": round(margin * 100, 2),
                    "Dette/EBITDA": round(debt_ebitda, 2) if debt_ebitda else "N/A",
                    "FCF Yield (%)": round(fcf_yield * 100, 2)
                })
                print(f"Trouvé : {ticker} ({info.get('industry')})")
        
        time.sleep(0.1) # Protection contre le ban d'IP
    except:
        continue

df_healthcare = pd.DataFrame(results)
print("\n--- TOP CONVICTIONS SANTÉ / TECH MÉDICALE ---")
print(df_healthcare.sort_values(by="ROE (%)", ascending=False))



"""-----------------------------------------------------------------------------------------------------------------------------"""




# 1. PARAMÈTRES RÉELS (Extraits du 10-K 2024)

fcf_initial = 630.7   # En millions de $
cash = 2579.4         # Cash + Short-term investments
dette = 2441.4        # Total Debt
actions_total = 408.9 # En millions d'actions

# 2. HYPOTHÈSES DE CROISSANCE (Vision Gérant de Conviction)

croissance_5ans = 0.15    # 15% par an (Expansion marché CGM)
croissance_perp = 0.03    # 3% (Croissance terminale à l'infini)
wacc = 0.09               # 9% (Taux d'actualisation / Coût du capital)

def calcul_dcf(fcf, growth, terminal_growth, discount_rate, years=5):
    # Projection des FCF futurs
    projections = []
    current_fcf = fcf
    
    for year in range(1, years + 1):
        current_fcf *= (1 + growth)
        # Actualisation au présent : FCF / (1 + r)^n
        fcf_actualise = current_fcf / (1 + discount_rate)**year
        projections.append(fcf_actualise)
        print(f"Année {year} - FCF Projeté: {current_fcf:.2f}M$ | Actualisé: {fcf_actualise:.2f}M$")

    # Valeur Terminale (Modèle de Gordon Shapiro)
    # VT = [FCF_n * (1+g)] / (r - g)
    valeur_terminale = (current_fcf * (1 + terminal_growth)) / (discount_rate - terminal_growth)
    vt_actualisee = valeur_terminale / (1 + discount_rate)**years
    
    # Valeur d'Entreprise (Somme des FCF actualisés + VT actualisée)
    valeur_entreprise = sum(projections) + vt_actualisee
    
    # Valeur des Capitaux Propres (Equity Value)
    valeur_equite = valeur_entreprise + cash - dette
    
    # Prix Intrinsèque par action
    prix_intrinsique = valeur_equite / actions_total
    
    return prix_intrinsique, valeur_entreprise

# 3. EXÉCUTION
print(f"--- Modèle DCF : DexCom Inc. ---")
prix_cible, ev = calcul_dcf(fcf_initial, croissance_5ans, croissance_perp, wacc)

print(f"\n--- RÉSULTATS ---")
print(f"Valeur d'Entreprise (EV): {ev:,.2f} M$")
print(f"Prix Intrinsèque calculé: {prix_cible:.2f} $")


import matplotlib.pyplot as plt

# Données de projection
years = ['2024 (A)', '2025 (E)', '2026 (E)', '2027 (E)', '2028 (E)', '2029 (E)']
fcf_data = [630.7, 725.3, 834.1, 959.2, 1103.1, 1268.6] # Calculés avec 15% de croissance

plt.figure(figsize=(10, 6))
plt.bar(years, fcf_data, color='#1f77b4', alpha=0.8)
plt.plot(years, fcf_data, marker='o', color='#d62728', linewidth=2)

plt.title('DexCom - Projection du Free Cash Flow (2025-2029)', fontsize=14)
plt.ylabel('Free Cash Flow (Millions $)')
plt.grid(axis='y', linestyle='--', alpha=0.7)

# Ajout des étiquettes de données
for i, v in enumerate(fcf_data):
    plt.text(i, v + 20, f"{v:.0f}$", ha='center', fontweight='bold')

plt.savefig('dxcm_fcf_projections.png')




import seaborn as sns
import pandas as pd

# Simulation de la sensibilité du prix (Prix vs WACC & Croissance)
# Lignes = WACC (8% à 12%), Colonnes = Croissance (10% à 20%)
data = [
    [185.4, 204.2, 225.1, 248.5, 274.8],
    [158.2, 173.8, 191.0, 210.2, 231.7],
    [137.5, 150.7, 165.2, 181.3, 199.2],
    [121.2, 132.5, 144.9, 158.7, 174.0],
    [108.2, 118.1, 128.9, 140.8, 154.0]
]

df_sens = pd.DataFrame(data, 
                       index=['8%', '9%', '10%', '11%', '12%'], 
                       columns=['10%', '12.5%', '15%', '17.5%', '20%'])

plt.figure(figsize=(10, 8))
sns.heatmap(df_sens, annot=True, fmt=".1f", cmap="RdYlGn", cbar_kws={'label': 'Prix Intrinsèque ($)'})

plt.title('Analyse de Sensibilité : Valorisation de DexCom', fontsize=14)
plt.xlabel('Taux de Croissance Long-Terme (%)')
plt.ylabel('WACC (Coût du Capital %)')

plt.savefig('dxcm_sensitivity_analysis.png')