import streamlit as st
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# Configuration de l'interface
st.set_page_config(page_title="Luxos RDC - Autosender", layout="wide")
st.title("🚀 WHATSAPP AUTOSENDER v2.0 — Luxos RDC")

# Chargement du fichier CSV (Zai utilise contacts_kcc_v3.csv)
try:
    df = pd.read_csv('contacts_kcc_v3.csv')
    
    # Ordre inversé : Commencer par le dernier contact (637) et remonter
    df_inverse = df.iloc[::-1]
    
    # Limite Anti-ban : Prendre les 100 premiers de cette liste inversée
    liste_campagne = df_inverse.head(100)
    
    st.success(f"✅ Fichier 'contacts_kcc_v3.csv' chargé ! {len(liste_campagne)} contacts prêts (Ordre inversé).")
except FileNotFoundError:
    st.error("❌ Erreur : Placez le fichier 'contacts_kcc_v3.csv' dans le dossier 'Campagne'.")
    liste_campagne = None

message_bureau = (
    "Bonjour Monsieur/Madame, je suis Héritier Kalambayi, votre agent commercial au sein de "
    "Luxos RDC. Je vous contacte pour vous informer que je suis désormais votre interlocuteur "
    "privilégié au sein de l'entreprise. Pour votre projet immobilier..."
)

st.info(f"📋 **Message configuré :**\n\n{message_bureau}")

if liste_campagne is not None:
    if st.button("🚀 DÉMARRER LA CAMPAGNE AUTOMATIQUE", type="primary"):
        st.warning("⚡ Ouverture de Google Chrome... Préparez-vous à scanner le QR Code.")
        
        # Configuration propre pour PC local (sans plantage)
        options = webdriver.ChromeOptions()
        options.add_argument("--start-maximized")
        
        # Utilisation de webdriver-manager pour éviter les erreurs de version de Chrome
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        
        # Étape cruciale : Ouvrir WhatsApp et attendre le scan
        driver.get("https://web.whatsapp.com")
        st.info("📲 En attente du scan du QR Code WhatsApp Business...")
        
        # Le script fait une vraie pause pour vous laisser scanner tranquillement
        time.sleep(25) 
        
        barre = st.progress(0)
        total = len(liste_campagne)
        succes, echecs = 0, 0
        
        for index, row in liste_campagne.iterrows():
            numero = str(row['telephone']).strip()
            if not numero.startswith('+'):
                numero = '+' + numero
                
            try:
                # Navigation vers le contact
                url_contact = f"https://web.whatsapp.com/send?phone={numero}&text={message_bureau}"
                driver.get(url_contact)
                
                # Attente du bouton envoyer de WhatsApp (max 30 secondes)
                bouton_envoi = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                )
                
                # Délais anti-ban de Zai (Pause entre 20 et 70 secondes)
                delai = random.randint(20, 70)
                st.write(f"⏳ Traitement de {numero}... Pause de sécurité de {delai} secondes.")
                time.sleep(delai)
                
                # Clic automatique
                bouton_envoi.click()
                succes += 1
                st.success(f"➡️ Envoyé à : {numero}")
                time.sleep(5)
                
            except Exception as e:
                echecs += 1
                st.error(f"⚠️ Erreur ou pas de compte WhatsApp pour {numero}")
            
            # Mise à jour de la barre
            barre.progress((succes + echecs) / total)
            
        driver.quit()
        st.balloons()
        st.success(f"🏁 Campagne finie ! {succes} envoyés, {echecs} échecs.")
