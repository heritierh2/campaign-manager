# 📊 Gestionnaire de Campagne - Semi-manuel & Sécurisé

Application web Streamlit pour la gestion de campagnes de contacts via WhatsApp, SMS, appels et e-mails.

## 🚀 Fonctionnalités

- **Gestion des Contacts** : Import CSV ou Google Sheets, recherche et filtrage
- **Module WhatsApp** : Ouverture de WhatsApp Web par contact, copie du message personnalisé
- **Retargeting** : Marquage "Sans WhatsApp", zone d'export texte brut
- **Module SMS** : Compteur 160 caractères, lien Google Messages Web
- **Appels** : Bouton "Appeler" avec protocole tel:
- **E-mails** : Envoi SMTP via Gmail ou Outlook

---

## 📁 Structure du Projet

```
campaign-manager/
├── app.py                      # Application principale Streamlit
├── requirements.txt            # Dépendances Python
├── render.yaml                 # Configuration Render
├── .streamlit/
│   ├── config.toml             # Configuration Streamlit
│   └── secrets.toml            # Secrets (à personnaliser)
└── README.md                   # Ce fichier
```

---

## 🛠️ Déploiement sur Render (GRATUIT)

### Étape 1 : Créer un dépôt GitHub

1. Allez sur [github.com](https://github.com) et connectez-vous
2. Cliquez sur **"New repository"**
3. Nommez-le `campaign-manager`
4. Cochez **"Private"** (recommandé car secrets)
5. Cliquez **"Create repository"**

### Étape 2 : Uploader les fichiers sur GitHub

**Option A : Via l'interface web GitHub**
1. Sur la page du dépôt, cliquez **"uploading an existing file"**
2. Glissez-déposez TOUS les fichiers du dossier `campaign-manager/`
3. ⚠️ N'oubliez PAS le dossier `.streamlit/` avec ses 2 fichiers
4. Cliquez **"Commit changes"**

**Option B : Via Git en ligne de commande**
```bash
cd campaign-manager
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/VOTRE-USER/campaign-manager.git
git branch -M main
git push -u origin main
```

### Étape 3 : Configurer Render

1. Allez sur [render.com](https://render.com) et inscrivez-vous (gratuit avec GitHub)
2. Cliquez **"New +"** → **"Web Service"**
3. Connectez votre dépôt GitHub `campaign-manager`
4. Configurez :
   - **Name** : `campaign-manager`
   - **Runtime** : `Python 3`
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true --server.enableCORS false --server.enableXsrfProtection false`
   - **Instance Type** : `Free`
5. Cliquez **"Advanced"** → ajoutez les variables d'environnement :
   - `PYTHON_VERSION` = `3.11.6`
   - `STREAMLIT_SERVER_HEADLESS` = `true`
6. Cliquez **"Create Web Service"**

### Étape 4 : Configurer les Secrets (optionnel)

Dans Render, allez dans **"Environment"** et ajoutez :
- `SMTP_SERVER` = `smtp.gmail.com`
- `SMTP_PORT` = `587`
- `EMAIL_SENDER` = `votre.email@gmail.com`
- `EMAIL_PASSWORD` = `votre-mot-de-passe-application`

⚠️ Pour Gmail, utilisez un **mot de passe d'application** (pas votre mot de passe habituel) :
1. Allez sur https://myaccount.google.com/apppasswords
2. Créez un mot de passe pour "Courrier"
3. Utilisez ce mot de passe de 16 caractères

### Étape 5 : Accéder à l'Application

Après le déploiement (2-5 minutes), Render vous donnera une URL du type :
`https://campaign-manager-xxxx.onrender.com`

---

## 📋 Format CSV Attendu

```csv
Nom,Numéro,Matricule,Email
Jean Dupont,+243812345678,MAT001,jean@email.com
Marie Curie,+243898765432,MAT002,marie@email.com
Pierre Martin,+243811223344,MAT003,pierre@email.com
```

Les colonnes **Nom** et **Numéro** sont obligatoires. Les colonnes **Matricule** et **Email** sont optionnelles.

---

## 🔒 Sécurité

- **Aucun bot WhatsApp** : L'application ouvre WhatsApp Web manuellement, vous copiez-collez le message. Aucune automatisation qui pourrait bloquer votre compte.
- **Semi-manuel** : Vous gardez le contrôle de chaque envoi.
- **Secrets protégés** : Les mots de passe SMTP sont dans les variables d'environnement Render, jamais exposés.

---

## 💰 Coût

**100% GRATUIT** avec l'offre gratuite de Render :
- 750 heures/mois (suffisant pour un service continu)
- L'application se met en veille après 15 min d'inactivité (réveil en ~30s)

---

## ❓ Résolution de Problèmes

| Problème | Solution |
|----------|----------|
| L'application ne démarre pas | Vérifiez la Start Command dans Render |
| Erreur "Module not found" | Vérifiez que `requirements.txt` est à la racine |
| WhatsApp ne s'ouvre pas | Les popups peuvent être bloqués par le navigateur. Autorisez-les. |
| E-mail non envoyé | Vérifiez le mot de passe d'application Gmail |
| L'application est lente au premier accès | Normal sur l'offre gratuite (réveil du serveur) |
