import streamlit as str
import pandas as pd
import time
import random
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration de la page de l'application
st.set_page_config(page_title="Gestionnaire de Campagne - Luxos RDC", layout="wide")

st.title("🚀 WHATSAPP AUTOSENDER v2.0 — Luxos RDC")
st.subheader("Campagne de suivi client KCC - Mode 100% Automatique")

# 1. Chargement de la liste des contacts
try:
    df = pd.read_csv('contacts_kcc.csv')
    
    # --- ÉTAPE 3 : LOGIQUE AUTOMATIQUE ET SÉCURITÉ ---
    # On inverse l'ordre pour commencer par le dernier contact (ex: 637) et remonter
    df_inverse = df.iloc[::-1]
    
    # On limite strictement à 100 contacts maximum pour la journée
    liste_campagne = df_inverse.head(100)
    
    st.success(f"📋 Fichier 'contacts_kcc.csv' chargé avec succès ! {len(liste_campagne)} contacts préparés pour aujourd'hui (Ordre Inversé).")
except FileNotFoundError:
    st.error("❌ Erreur : Le fichier 'contacts_kcc.csv' est introuvable. Veuillez l'ajouter sur GitHub.")
    liste_campagne = None

# Message prédéfini
message_bureau = (
    "Bonjour Monsieur/Madame, je suis Héritier Kalambayi, votre agent commercial au sein de "
    "Luxos RDC. Je vous contacte pour vous informer que je suis désormais votre interlocuteur "
    "privilégié au sein de l'entreprise. Pour votre projet immobilier..."
)

st.info(f"💬 **Message qui sera envoyé :**\n\n{message_bureau}")

# Bouton pour lancer la machine
if liste_campagne is not None:
    if st.button("▶️ Lancer la campagne automatique", type="primary"):
        st.warning("⚠️ Le navigateur va s'ouvrir. Si c'est la première fois, scannez rapidement le code QR sur votre écran PC !")
        
        # Configuration du robot Selenium
        options = webdriver.ChromeOptions()
        # options.add_argument("--headless") # Laissez décoché au début pour voir et scanner le QR code
        driver = webdriver.Chrome(options=options)
        
        # Ouvre d'abord WhatsApp Web pour vous laisser le temps de vous connecter
        driver.get("https://web.whatsapp.com")
        st.info("⏱️ Attente de connexion à WhatsApp Web (Scannez le QR Code si demandé)...")
        time.sleep(20) # 20 secondes pour être sûr que vous êtes connecté
        
        barre_progression = st.progress(0)
        total = len(liste_campagne)
        
        envois_reussis = 0
        erreurs = 0
        
        # Boucle d'envoi automatique
        for index, row in liste_campagne.iterrows():
            numero = str(row['telephone']).strip()
            # Nettoyage rapide du numéro si nécessaire
            if not numero.startswith('+'):
                numero = '+' + numero
                
            try:
                # Lien direct vers le contact avec le message pré-rempli
                url_contact = f"https://web.whatsapp.com/send?phone={numero}&text={message_bureau}"
                driver.get(url_contact)
                
                # Attente que le bouton d'envoi vert de WhatsApp apparaisse à l'écran
                bouton_envoi = WebDriverWait(driver, 25).until(
                    EC.element_to_be_clickable((By.XPATH, '//span[@data-icon="send"]'))
                )
                
                # Configuration ANTI-BAN : Pause aléatoire humaine avant de cliquer
                pause_humaine = random.randint(20, 45)
                st.write(f"⏳ Analyse du profil {numero}... Pause de sécurité de {pause_humaine}s")
                time.sleep(pause_humaine)
                
                # Le robot clique tout seul !
                bouton_envoi.click()
                envois_reussis += 1
                st.success(f"✅ Message envoyé avec succès à : {numero}")
                
                # Petite pause après l'envoi
                time.sleep(5)
                
            except Exception as e:
                erreurs += 1
                st.error(f"❌ Impossible d'envoyer au numéro {numero} (Pas de compte WhatsApp ou chargement trop long)")
            
            # Mise à jour de la barre de progression sur votre écran HP
            actuel = envois_reussis + erreurs
            barre_progression.progress(actuel / total)
            
        driver.quit()
        st.balloons()
        st.success(f"🏁 Campagne terminée ! {envois_reussis} envoyés avec succès, {erreurs} échecs.")
