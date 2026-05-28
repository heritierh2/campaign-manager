"""
=============================================================
  GESTIONNAIRE DE CAMPAGNE v2.0
  Semi-manuel · Sécurisé · Aucun robot
  Déploiement Render via GitHub
=============================================================
"""

import streamlit as st
import pandas as pd
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
import base64
import time

# ============================================================
# CONFIGURATION DE LA PAGE
# ============================================================
st.set_page_config(
    page_title="Gestionnaire de Campagne",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# CSS PERSONNALISÉ
# ============================================================
STYLES = """
<style>
/* ---------- Thème ---------- */
:root {
    --wa: #25D366;  --wa-dark: #128C7E;
    --danger: #e74c3c; --danger-dark: #c0392b;
    --info: #3498db;  --sms: #4285F4;
    --email: #EA4335; --call: #27ae60;
}
.stApp { background: linear-gradient(135deg,#f5f7fa 0%,#e4edf5 100%); }

/* ---------- En-tête ---------- */
.hero {
    background: linear-gradient(135deg,#128C7E 0%,#25D366 50%,#128C7E 100%);
    padding: 26px 34px; border-radius: 16px; margin-bottom: 22px;
    box-shadow: 0 4px 20px rgba(37,211,102,.25); color:#fff; text-align:center;
}
.hero h1 { margin:0; font-size:2.1rem; font-weight:800; }
.hero p  { margin:4px 0 0; font-size:.95rem; opacity:.9; }

/* ---------- Cartes ---------- */
.card {
    background:#fff; border-radius:14px; padding:22px;
    margin-bottom:18px; box-shadow:0 2px 12px rgba(0,0,0,.07);
    border:1px solid #e8ecf1;
}
.card-title { font-size:1.2rem; font-weight:700; margin-bottom:14px; }

/* ---------- Statistiques ---------- */
.stat {
    color:#fff; padding:16px 20px; border-radius:12px;
    text-align:center; box-shadow:0 3px 14px rgba(0,0,0,.18);
}
.stat.purple  { background:linear-gradient(135deg,#667eea,#764ba2); }
.stat.green   { background:linear-gradient(135deg,#11998e,#38ef7d); }
.stat.red     { background:linear-gradient(135deg,#e74c3c,#c0392b); }
.stat.blue    { background:linear-gradient(135deg,#2193b0,#6dd5ed); }
.stat.orange  { background:linear-gradient(135deg,#f2994a,#f2c94c); }
.stat-num { font-size:2rem; font-weight:800; }
.stat-lbl { font-size:.82rem; opacity:.92; margin-top:2px; }

/* ---------- Boutons HTML ---------- */
.hbtn {
    color:#fff!important; border:none; padding:7px 14px; border-radius:8px;
    cursor:pointer; font-weight:600; font-size:.82rem; text-decoration:none;
    display:inline-flex; align-items:center; gap:5px; transition:all .2s;
    line-height:1.4;
}
.hbtn:hover { filter:brightness(.9); transform:translateY(-1px); }
.hbtn-wa    { background:var(--wa); }
.hbtn-copy  { background:var(--info); }
.hbtn-fail  { background:var(--danger); }
.hbtn-restore { background:var(--call); }
.hbtn-sms   { background:var(--sms); }
.hbtn-call  { background:var(--call); }
.hbtn-email { background:var(--email); }

/* ---------- Badges ---------- */
.badge {
    padding:3px 11px; border-radius:20px; font-size:.76rem;
    font-weight:600; display:inline-block;
}
.badge-pending { background:#fef3cd; color:#856404; }
.badge-failed  { background:#f8d7da; color:#721c24; }

/* ---------- Ligne contact ---------- */
.crow {
    background:#fff; border-radius:10px; padding:12px 16px;
    margin-bottom:8px; border:1px solid #eef2f7;
    display:flex; align-items:center; gap:10px;
    transition:all .2s;
}
.crow:hover { box-shadow:0 2px 10px rgba(0,0,0,.07); border-color:#c8d6e5; }
.crow.failed  { background:#fff5f5; border-color:#ffcccc; }
.crow.success { background:#f0fff4; border-color:#c6f6d5; }

/* ---------- Barre de progression ---------- */
.prog-bar { background:#e0e0e0; border-radius:10px; height:10px; overflow:hidden; }
.prog-fill { height:100%; border-radius:10px; transition:width .5s ease; }

/* ---------- Zone retargeting ---------- */
.retarget-zone {
    background:#fff3f3; border:2px dashed var(--danger);
    border-radius:12px; padding:20px;
}

/* ---------- Compteur SMS ---------- */
.cnt { font-size:.85rem; padding:4px 0; font-weight:600; }
.cnt.ok   { color:#27ae60; }
.cnt.warn { color:#f39c12; }
.cnt.over { color:#e74c3c; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] { background:linear-gradient(180deg,#1a1a2e,#16213e); }
[data-testid="stSidebar"] .stMarkdown { color:#e0e0e0; }
</style>
"""
st.markdown(STYLES, unsafe_allow_html=True)


# ============================================================
# INITIALISATION SESSION STATE
# ============================================================
def _defaults():
    """Valeurs par défaut persistées dans st.session_state."""
    return {
        "df": pd.DataFrame(),                          # contacts
        "failed": [],                                    # liste dicts {index,nom,numero,matricule}
        "col_map": {},                                   # mapping colonnes détectées
        "wa_msg": st.secrets.get("DEFAULT_WHATSAPP_MESSAGE",
                                 "Bonjour {nom}, nous avons une offre spéciale pour vous ! Contactez-nous au plus vite."),
        "sms_msg": st.secrets.get("DEFAULT_SMS_MESSAGE",
                                  "Bonjour {nom}, offre spéciale ! Répondez vite."),
        "smtp_server": st.secrets.get("SMTP_SERVER", "smtp.gmail.com"),
        "smtp_port": int(st.secrets.get("SMTP_PORT", "587")),
        "smtp_user": st.secrets.get("EMAIL_SENDER", ""),
        "smtp_pass": st.secrets.get("EMAIL_PASSWORD", ""),
        "email_subject": "",
        "email_body": "",
    }

for k, v in _defaults().items():
    if k not in st.session_state:
        st.session_state[k] = v


# ============================================================
# UTILITAIRES
# ============================================================
def clean_phone(raw):
    """Nettoie un numéro : espaces, tirets, parenthèses, préfixe 0 → 243."""
    if pd.isna(raw):
        return ""
    s = re.sub(r"[\s\-\.\(\)]+", "", str(raw).strip())
    if s.startswith("+"):
        s = s[1:]
    if s.startswith("0"):
        s = "243" + s[1:]          # RDC par défaut — modifiez si besoin
    return s


def detect_columns(df):
    """Détecte automatiquement les colonnes Nom / Numéro / Matricule / Email."""
    mapping = {}
    aliases = {
        "nom":      ["nom","name","noms","names","full_name","fullname","prenom","prénom"],
        "numero":   ["numéro","numero","number","phone","tel","telephone","téléphone","mobile","cell","cellular"],
        "matricule":["matricule","id","identifier","code","ref","reference","référence","matr"],
        "email":    ["email","e-mail","courriel","mail","adresse_email","adresse mail"],
    }
    for key, words in aliases.items():
        for col in df.columns:
            if col.strip().lower() in words:
                mapping[key] = col
                break
    # Fallback positionnel
    cols = list(df.columns)
    if "nom" not in mapping and len(cols) >= 1:
        mapping["nom"] = cols[0]
    if "numero" not in mapping and len(cols) >= 2:
        mapping["numero"] = cols[1]
    if "matricule" not in mapping and len(cols) >= 3:
        mapping["matricule"] = cols[2]
    if "email" not in mapping and len(cols) >= 4:
        mapping["email"] = cols[3]
    return mapping


def val(row, key):
    """Récupère la valeur d'une colonne mappée, sans 'nan'."""
    col = st.session_state.col_map.get(key, "")
    if not col:
        return ""
    v = str(row.get(col, "")).strip()
    return "" if v.lower() == "nan" else v


def get_email(row):
    """Extrait l'email d'une ligne."""
    e = val(row, "email")
    return e if e and "@" in e else None


def _b64(text):
    return base64.b64encode(text.encode("utf-8")).decode("utf-8")


def copy_btn(text, label="📋 Copier", uid="c"):
    """Bouton HTML/JS copiant *text* dans le presse-papiers."""
    b = _b64(text)
    return f"""<button id="{uid}" class="hbtn hbtn-copy" onclick="
(function(){{
  var t=decodeURIComponent(escape(atob('{b}')));
  navigator.clipboard.writeText(t).then(function(){{
    var b=document.getElementById('{uid}');
    var o=b.innerHTML; b.innerHTML='✓ Copié !'; b.style.background='#27ae60';
    setTimeout(function(){{b.innerHTML=o;b.style.background='#3498db';}},1800);
  }});
}})();">{label}</button>"""


def stat_card(n, label, cls="purple"):
    return f'<div class="stat {cls}"><div class="stat-num">{n}</div><div class="stat-lbl">{label}</div></div>'


# ============================================================
# SIDEBAR — Navigation + import rapide
# ============================================================
def sidebar():
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center;padding:18px 0">
            <div style="font-size:2.8rem">📊</div>
            <h2 style="color:#25D366;margin:8px 0 2px">Campagne</h2>
            <p style="color:#aaa;font-size:.82rem">Gestion Semi-Manuelle</p>
        </div><hr style="border-color:#333">""", unsafe_allow_html=True)

        page = st.radio(
            "Navigation",
            ["🏠 Tableau de bord", "📋 Contacts", "💬 WhatsApp",
             "📱 SMS", "📧 E-mails", "⚠️ Retargeting"],
            label_visibility="collapsed", key="_nav",
        )
        _map = {
            "🏠 Tableau de bord": "dash",
            "📋 Contacts":       "contacts",
            "💬 WhatsApp":       "whatsapp",
            "📱 SMS":            "sms",
            "📧 E-mails":        "email",
            "⚠️ Retargeting":    "retarget",
        }
        st.session_state["_page"] = _map.get(page, "dash")

        st.markdown("<hr style='border-color:#333'>", unsafe_allow_html=True)
        st.markdown("### 📂 Import Rapide")
        up = st.file_uploader("CSV", type=["csv"], key="_side_up", label_visibility="collapsed")
        if up is not None:
            try:
                df = pd.read_csv(up)
                df.columns = [c.strip() for c in df.columns]
                st.session_state.df = df
                st.session_state.failed = []
                st.session_state.col_map = detect_columns(df)
                st.success(f"✅ {len(df)} contacts chargés !")
            except Exception as exc:
                st.error(f"Erreur : {exc}")

        st.markdown("<hr style='border-color:#333'>", unsafe_allow_html=True)
        st.markdown("### ⚙️ État")
        n = len(st.session_state.df)
        f = len(st.session_state.failed)
        smtp_ok = bool(st.session_state.smtp_user)
        st.markdown(f"📋 Contacts : **{n}**")
        st.markdown(f"⚠️ Échecs : **{f}**")
        st.markdown(f"📧 SMTP : {'✅' if smtp_ok else '❌'}")


sidebar()
PAGE = st.session_state.get("_page", "dash")


# ============================================================
# PAGE : TABLEAU DE BORD
# ============================================================
def page_dashboard():
    df = st.session_state.df
    total = len(df)
    fail  = len(st.session_state.failed)
    ok    = total - fail if total else 0
    pct   = round(ok / total * 100, 1) if total else 0

    st.markdown("""<div class="hero">
        <h1>📊 Gestionnaire de Campagne</h1>
        <p>Semi-manuel · Sécurisé · Aucun robot · Conforme WhatsApp</p>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(stat_card(total, "Total Contacts"), unsafe_allow_html=True)
    c2.markdown(stat_card(ok, "Contacts Actifs", "green"), unsafe_allow_html=True)
    c3.markdown(stat_card(fail, "Sans WhatsApp", "red"), unsafe_allow_html=True)
    c4.markdown(stat_card(f"{pct}%", "Taux Réussite", "blue"), unsafe_allow_html=True)

    if total:
        st.markdown(f"""
        <div style="margin:10px 0 20px">
          <div style="display:flex;justify-content:space-between;margin-bottom:5px">
            <span style="font-weight:600">Progression</span>
            <span style="font-weight:600">{pct:.0f} %</span>
          </div>
          <div class="prog-bar">
            <div class="prog-fill" style="width:{pct}%;background:linear-gradient(90deg,#25D366,#128C7E)"></div>
          </div>
        </div>""", unsafe_allow_html=True)

    # Guide rapide
    st.markdown("""<div class="card"><div class="card-title">🚀 Guide Rapide</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:14px">
      <div style="padding:11px;background:#f0fff4;border-radius:10px;border-left:4px solid #25D366">
        <strong>1. Importer</strong><br><span style="font-size:.84rem;color:#555">Chargez un CSV ou liez une Google Sheet</span></div>
      <div style="padding:11px;background:#f0f7ff;border-radius:10px;border-left:4px solid #3498db">
        <strong>2. WhatsApp</strong><br><span style="font-size:.84rem;color:#555">Ouvrez WhatsApp, copiez-collez le message</span></div>
      <div style="padding:11px;background:#fff8f0;border-radius:10px;border-left:4px solid #f39c12">
        <strong>3. Retargeting</strong><br><span style="font-size:.84rem;color:#555">Marquez les échecs → SMS ou appel</span></div>
      <div style="padding:11px;background:#fef0f0;border-radius:10px;border-left:4px solid #e74c3c">
        <strong>4. SMS / Email</strong><br><span style="font-size:.84rem;color:#555">Relancez les contacts en échec</span></div>
    </div></div>""", unsafe_allow_html=True)

    if total:
        st.markdown('<div class="card"><div class="card-title">📋 Aperçu</div>', unsafe_allow_html=True)
        st.dataframe(df.head(10), use_container_width=True, height=280)
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PAGE : CONTACTS
# ============================================================
def page_contacts():
    st.markdown("""<div class="hero" style="padding:20px 28px">
        <h1>📋 Gestion des Contacts</h1>
        <p>Importez, visualisez et gérez votre liste</p>
    </div>""", unsafe_allow_html=True)

    # ---- Import ----
    ci1, ci2 = st.columns([2, 1])
    with ci1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 📂 Importer des Contacts")
        u1, u2 = st.columns(2)
        with u1:
            up = st.file_uploader("Charger un CSV", type=["csv"], key="_csv_main",
                                  help="Colonnes requises : Nom, Numéro")
            if up:
                try:
                    df = pd.read_csv(up)
                    df.columns = [c.strip() for c in df.columns]
                    st.session_state.df = df
                    st.session_state.failed = []
                    st.session_state.col_map = detect_columns(df)
                    st.success(f"✅ **{len(df)} contacts** chargés !")
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")
        with u2:
            st.markdown("**Format CSV attendu :**")
            st.code("Nom,Numéro,Matricule,Email\nJean Dupont,+243812345678,MAT001,jean@email.com\nMarie Curie,+243898765432,MAT002,marie@email.com", language="csv")
            st.info("💡 **Nom** et **Numéro** sont obligatoires.")
        st.markdown('</div>', unsafe_allow_html=True)

    with ci2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.markdown("### 🔗 Google Sheets")
        st.markdown("""<div style="font-size:.88rem;color:#555">
        1. Fichier → Partager → Publier sur le web → CSV<br>
        2. Collez l'URL ci-dessous</div>""", unsafe_allow_html=True)
        surl = st.text_input("URL CSV Google Sheet", key="_sheet_url",
                             placeholder="https://docs.google.com/spreadsheets/d/.../pub?output=csv")
        if st.button("📥 Charger Google Sheets", key="_load_sheet"):
            if surl:
                try:
                    df = pd.read_csv(surl)
                    df.columns = [c.strip() for c in df.columns]
                    st.session_state.df = df
                    st.session_state.failed = []
                    st.session_state.col_map = detect_columns(df)
                    st.success(f"✅ **{len(df)} contacts** chargés !")
                except Exception as e:
                    st.error(f"❌ Erreur : {e}")
            else:
                st.warning("⚠️ Entrez une URL valide.")
        st.markdown('</div>', unsafe_allow_html=True)

    df = st.session_state.df
    if df.empty:
        st.markdown("""<div style="text-align:center;padding:50px 20px;color:#888">
            <div style="font-size:3.5rem">📭</div>
            <h3>Aucun contact chargé</h3>
            <p>Importez un CSV ou connectez une Google Sheet ci-dessus.</p></div>""", unsafe_allow_html=True)
        return

    st.session_state.col_map = detect_columns(df)
    cm = st.session_state.col_map

    st.markdown(f"---\n### 📊 Liste des Contacts ({len(df)})")

    # Recherche & filtre
    sc1, sc2 = st.columns([3, 1])
    search = sc1.text_input("🔍 Rechercher", key="_search", placeholder="Nom ou numéro…")
    filt   = sc2.selectbox("Filtrer", ["Tous", "Actif", "Sans WhatsApp"], key="_filt")

    fidx = {c["index"] for c in st.session_state.failed}
    view = df.copy()
    if search:
        mask = view.apply(lambda r: any(search.lower() in str(v).lower() for v in r), axis=1)
        view = view[mask]
    if filt == "Sans WhatsApp":
        view = view[view.index.isin(fidx)]
    elif filt == "Actif":
        view = view[~view.index.isin(fidx)]

    # ---- Affichage ligne par ligne ----
    for idx, row in view.iterrows():
        nom  = val(row, "nom")
        num  = val(row, "numero")
        mat  = val(row, "matricule")
        ncl  = clean_phone(num)
        email = get_email(row)
        is_f = idx in fidx
        badge = '<span class="badge badge-failed">Sans WhatsApp</span>' if is_f \
                else '<span class="badge badge-pending">Actif</span>'

        st.markdown(f"""
        <div class="crow {'failed' if is_f else ''}">
          <div style="flex:0 0 36px;text-align:center;font-weight:700;color:#888">{idx+1}</div>
          <div style="flex:1">
            <strong>{nom}</strong><br>
            <span style="font-size:.84rem;color:#666">{num}</span>
            {f' · <span style="font-size:.82rem;color:#888">{mat}</span>' if mat else ''}
            {f' · <span style="font-size:.82rem;color:#888">{email}</span>' if email else ''}
          </div>
          <div>{badge}</div>
        </div>""", unsafe_allow_html=True)

        # --- Boutons d'action ---
        a1, a2, a3, a4, a5 = st.columns(5)

        # WhatsApp
        with a1:
            wa_url = f"https://wa.me/{ncl}"
            st.markdown(
                f'<a href="{wa_url}" target="_blank" rel="noopener" class="hbtn hbtn-wa">💬 WhatsApp</a>',
                unsafe_allow_html=True)

        # Copier message WA
        with a2:
            msg = st.session_state.wa_msg.replace("{nom}", nom).replace("{matricule}", mat)
            st.markdown(copy_btn(msg, "📋 Copier msg", f"cp_{idx}"), unsafe_allow_html=True)

        # Marquer / Restaurer
        with a3:
            if not is_f:
                if st.button("⚠️ Sans WA", key=f"fail_{idx}"):
                    if not any(c["index"] == idx for c in st.session_state.failed):
                        st.session_state.failed.append(
                            {"index": idx, "nom": nom, "numero": num, "matricule": mat})
                    st.rerun()
            else:
                if st.button("✅ Restaurer", key=f"rest_{idx}"):
                    st.session_state.failed = [c for c in st.session_state.failed if c["index"] != idx]
                    st.rerun()

        # SMS
        with a4:
            if is_f:
                st.markdown(
                    '<a href="https://messages.google.com/web/" target="_blank" rel="noopener" class="hbtn hbtn-sms">📱 SMS</a>',
                    unsafe_allow_html=True)

        # Appel
        with a5:
            st.markdown(
                f'<a href="tel:{num}" class="hbtn hbtn-call">📞 Appeler</a>',
                unsafe_allow_html=True)


# ============================================================
# PAGE : WHATSAPP
# ============================================================
def page_whatsapp():
    st.markdown("""<div class="hero" style="background:linear-gradient(135deg,#128C7E,#25D366)">
        <h1>💬 Module WhatsApp</h1>
        <p>Semi-manuel · Aucun robot · Conforme aux conditions WhatsApp</p>
    </div>""", unsafe_allow_html=True)

    df = st.session_state.df
    if df.empty:
        st.warning("⚠️ Chargez d'abord vos contacts.")
        return
    cm = st.session_state.col_map

    # ---- Message ----
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ✍️ Message de Campagne")
    st.markdown("Variables : **{nom}** · **{matricule}** · **{numero}**")

    m1, m2 = st.columns([3, 1])
    with m1:
        wa_msg = st.text_area("Votre message :", value=st.session_state.wa_msg,
                              height=140, key="_wa_msg")
        st.session_state.wa_msg = wa_msg
    with m2:
        preview = wa_msg.replace("{nom}", "Jean Dupont") \
                        .replace("{matricule}", "MAT001") \
                        .replace("{numero}", "+243812345678")
        st.markdown("**Aperçu :**")
        st.info(preview[:250] + ("…" if len(preview) > 250 else ""))
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Contacts actifs ----
    fidx = {c["index"] for c in st.session_state.failed}
    active = df[~df.index.isin(fidx)]
    st.markdown(f"---\n### 📨 Contacts Actifs ({len(active)})")

    if active.empty:
        st.info("Tous les contacts sont marqués Sans WhatsApp.")
        return

    # Copier tous
    all_msgs = []
    for idx, row in active.iterrows():
        nom = val(row, "nom"); mat = val(row, "matricule"); num = val(row, "numero")
        msg = wa_msg.replace("{nom}", nom).replace("{matricule}", mat)
        all_msgs.append(f"--- {nom} ({num}) ---\n{msg}")
    full = "\n\n".join(all_msgs)
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(copy_btn(full, "📋 Copier TOUS les messages", "all_wa"), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # Chaque contact
    for idx, row in active.iterrows():
        nom = val(row, "nom"); num = val(row, "numero"); mat = val(row, "matricule")
        ncl = clean_phone(num)
        msg = wa_msg.replace("{nom}", nom).replace("{matricule}", mat)
        wa_url = f"https://wa.me/{ncl}"

        with st.expander(f"💬 {nom} — {num}"):
            ec1, ec2 = st.columns([2, 1])
            with ec1:
                st.markdown("**Message à envoyer :**")
                st.code(msg, language=None)
            with ec2:
                st.markdown(
                    f'<a href="{wa_url}" target="_blank" rel="noopener" class="hbtn hbtn-wa" '
                    f'style="display:block;text-align:center;padding:12px;margin-bottom:8px">'
                    f'Ouvrir WhatsApp Web</a>', unsafe_allow_html=True)
                st.markdown(copy_btn(msg, "📋 Copier le message", f"wap_{idx}"), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("⚠️ Marquer Sans WhatsApp", key=f"wa_fail_{idx}"):
                    if not any(c["index"] == idx for c in st.session_state.failed):
                        st.session_state.failed.append(
                            {"index": idx, "nom": nom, "numero": num, "matricule": mat})
                    st.rerun()


# ============================================================
# PAGE : SMS
# ============================================================
def page_sms():
    st.markdown("""<div class="hero" style="background:linear-gradient(135deg,#2193b0,#6dd5ed)">
        <h1>📱 Module SMS</h1>
        <p>Via Google Messages Web · Compteur 160 caractères</p>
    </div>""", unsafe_allow_html=True)

    df = st.session_state.df
    if df.empty:
        st.warning("⚠️ Chargez d'abord vos contacts.")
        return

    # ---- Message SMS ----
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ✍️ Message SMS")
    st.markdown("Variables : **{nom}** · **{matricule}**")
    sms = st.text_area("Votre message :", value=st.session_state.sms_msg,
                       height=90, key="_sms_msg", max_chars=300)
    st.session_state.sms_msg = sms

    nchar = len(sms)
    segs  = max(1, (nchar + 159) // 160)
    css   = "ok" if nchar <= 160 else ("warn" if nchar <= 320 else "over")
    st.markdown(f'<div class="cnt {css}">{nchar} / 160 caractères · SMS segment(s) : {segs}</div>',
                unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Contacts en échec ----
    failed = st.session_state.failed
    st.markdown(f"---\n### 📨 Contacts Sans WhatsApp ({len(failed)})")

    if not failed:
        st.info("Aucun contact en échec. Marquez des contacts dans l'onglet WhatsApp ou Contacts.")
        return

    for c in failed:
        nom = c["nom"]; num = c["numero"]; mat = c.get("matricule", "")
        msg = sms.replace("{nom}", nom).replace("{matricule}", mat)

        with st.expander(f"📱 {nom} — {num}"):
            sc1, sc2 = st.columns([2, 1])
            with sc1:
                st.markdown("**Message SMS :**")
                st.code(msg, language=None)
                st.caption(f"{len(msg)} caractère(s)")
            with sc2:
                st.markdown(
                    '<a href="https://messages.google.com/web/" target="_blank" rel="noopener" '
                    'class="hbtn hbtn-sms" style="display:block;text-align:center;padding:12px;margin-bottom:8px">'
                    '📱 Ouvrir Google Messages</a>', unsafe_allow_html=True)
                st.markdown(copy_btn(msg, "📋 Copier le SMS", f"sm_{c['index']}"), unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f'<a href="tel:{num}" class="hbtn hbtn-call" '
                    f'style="display:block;text-align:center;padding:12px">📞 Appeler</a>',
                    unsafe_allow_html=True)


# ============================================================
# PAGE : EMAIL
# ============================================================
def page_email():
    st.markdown("""<div class="hero" style="background:linear-gradient(135deg,#EA4335,#fbbc05)">
        <h1>📧 Campagnes E-mail</h1>
        <p>Envoi via SMTP · Gmail ou Outlook Professionnel</p>
    </div>""", unsafe_allow_html=True)

    # ---- Config SMTP ----
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ⚙️ Configuration SMTP")
    s1, s2 = st.columns(2)
    with s1:
        srv = st.text_input("Serveur SMTP", value=st.session_state.smtp_server, key="_smtp_srv")
        port = st.number_input("Port", value=st.session_state.smtp_port, min_value=1, max_value=65535, key="_smtp_port")
    with s2:
        user = st.text_input("Adresse e-mail", value=st.session_state.smtp_user, key="_smtp_user")
        pwd  = st.text_input("Mot de passe d'application", type="password", value=st.session_state.smtp_pass, key="_smtp_pwd")

    if st.button("💾 Sauvegarder SMTP", key="_save_smtp"):
        st.session_state.smtp_server = srv
        st.session_state.smtp_port   = int(port)
        st.session_state.smtp_user   = user
        st.session_state.smtp_pass   = pwd
        st.success("✅ Configuration sauvegardée !")

    st.markdown("""<div style="background:#fff8e1;padding:12px;border-radius:10px;margin-top:10px;
    font-size:.86rem;border-left:4px solid #fbbc05">
    <strong>💡 Gmail :</strong> Utilisez un <strong>mot de passe d'application</strong>.<br>
    1️⃣ <a href="https://myaccount.google.com/apppasswords" target="_blank">myaccount.google.com/apppasswords</a><br>
    2️⃣ Créez un mot de passe pour « Courrier »<br>
    3️⃣ Collez les 16 caractères ci-dessus
    </div>""", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Rédaction ----
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### ✍️ Rédiger l'E-mail")
    subj = st.text_input("Objet :", value=st.session_state.email_subject, key="_em_subj")
    body = st.text_area("Corps du message :", value=st.session_state.email_body, height=180, key="_em_body")
    st.session_state.email_subject = subj
    st.session_state.email_body   = body
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Destinataires ----
    df = st.session_state.df
    cm = st.session_state.col_map
    email_col = cm.get("email")
    if df.empty:
        st.warning("⚠️ Chargez d'abord vos contacts.")
        return
    if not email_col:
        # Détection large
        for col in df.columns:
            if col.strip().lower() in ["email", "e-mail", "courriel", "mail"]:
                email_col = col; cm["email"] = col; st.session_state.col_map = cm; break
    if not email_col:
        st.error("❌ Aucune colonne Email détectée. Ajoutez-en à votre CSV.")
        return

    valid = [str(v).strip() for v in df[email_col].dropna() if "@" in str(v)]

    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"### 📨 Destinataires ({len(valid)} adresses valides)")
    targets = st.multiselect("Sélectionner :", options=valid, default=valid, key="_em_tgt")

    if targets:
        with st.expander(f"👁️ Aperçu ({len(targets)} destinataire(s))"):
            st.markdown(f"**Objet :** {subj}")
            st.markdown(f"**De :** {user}")
            st.markdown(f"**À :** {len(targets)} destinataire(s)")
            st.markdown("---")
            st.markdown(body)

    # Envoi
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("📤 Envoyer à tous", key="_em_send", type="primary"):
            if not user or not pwd:
                st.error("❌ Configurez le SMTP d'abord.")
            elif not subj or not body:
                st.error("❌ Objet et corps requis.")
            elif not targets:
                st.error("❌ Aucun destinataire.")
            else:
                prog = st.progress(0, text="Envoi en cours…")
                sent = 0; errs = []
                for i, rcpt in enumerate(targets):
                    try:
                        msg = MIMEMultipart()
                        msg["From"]    = user
                        msg["To"]      = rcpt
                        msg["Subject"] = subj
                        msg.attach(MIMEText(body, "plain", "utf-8"))
                        with smtplib.SMTP(srv, int(port)) as server:
                            server.starttls()
                            server.login(user, pwd)
                            server.sendmail(user, rcpt, msg.as_string())
                        sent += 1
                    except Exception as exc:
                        errs.append((rcpt, str(exc)))
                    prog.progress((i+1)/len(targets), text=f"Envoi {i+1}/{len(targets)}…")
                if sent:
                    st.success(f"✅ **{sent}** e-mail(s) envoyé(s) !")
                if errs:
                    st.error(f"❌ **{len(errs)}** échec(s) :")
                    for e, m in errs:
                        st.error(f"• {e} : {m}")

    with bc2:
        if st.button("🧪 E-mail test", key="_em_test"):
            if not user or not pwd:
                st.error("❌ Configurez le SMTP.")
            else:
                try:
                    msg = MIMEMultipart()
                    msg["From"]    = user
                    msg["To"]      = user
                    msg["Subject"] = "[TEST] Gestionnaire de Campagne"
                    msg.attach(MIMEText("Ceci est un e-mail test.", "plain", "utf-8"))
                    with smtplib.SMTP(srv, int(port)) as server:
                        server.starttls()
                        server.login(user, pwd)
                        server.sendmail(user, user, msg.as_string())
                    st.success("✅ E-mail test envoyé !")
                except Exception as exc:
                    st.error(f"❌ Erreur : {exc}")
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# PAGE : RETARGETING
# ============================================================
def page_retarget():
    st.markdown("""<div class="hero" style="background:linear-gradient(135deg,#e74c3c,#c0392b)">
        <h1>⚠️ Retargeting — Contacts en Échec</h1>
        <p>Sans WhatsApp · Prêts pour SMS, appel ou e-mail</p>
    </div>""", unsafe_allow_html=True)

    failed = st.session_state.failed
    if not failed:
        st.markdown("""<div style="text-align:center;padding:50px;color:#888">
            <div style="font-size:3.5rem">🎉</div>
            <h3>Aucun contact en échec</h3>
            <p>Tous actifs ou pas encore de contacts marqués.</p></div>""", unsafe_allow_html=True)
        return

    # Stats
    df = st.session_state.df
    cm = st.session_state.col_map
    ecol = cm.get("email")
    email_cnt = 0
    if ecol and not df.empty:
        for c in failed:
            if c["index"] in df.index and ecol in df.columns:
                ev = df.loc[c["index"], ecol]
                if pd.notna(ev) and "@" in str(ev):
                    email_cnt += 1

    t1, t2, t3 = st.columns(3)
    t1.markdown(stat_card(len(failed), "Sans WhatsApp", "red"), unsafe_allow_html=True)
    t2.markdown(stat_card(email_cnt, "Avec Email", "orange"), unsafe_allow_html=True)
    t3.markdown(stat_card(len(failed)-email_cnt, "SMS / Appel", "blue"), unsafe_allow_html=True)

    # ---- Zone texte brut ----
    st.markdown("---")
    st.markdown('<div class="card retarget-zone">', unsafe_allow_html=True)
    st.markdown("### 📋 Liste Brute — Sélectionnable et Copiable")
    lines = []
    for c in failed:
        parts = [c["nom"]]
        if c.get("numero"):  parts.append(c["numero"])
        if c.get("matricule"): parts.append(c["matricule"])
        lines.append(" + ".join(parts))
    raw = "\n".join(lines)
    st.text_area("Sélectionnez et copiez (Ctrl+A → Ctrl+C) :", value=raw, height=200, key="_ret_raw")
    st.markdown(copy_btn(raw, "📋 Copier toute la liste", "ret_all"), unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Actions rapides ----
    st.markdown("---")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("### 🚀 Actions Rapides")
    r1, r2, r3 = st.columns(3)

    with r1:
        st.markdown("#### 📱 SMS en masse")
        all_sms = []
        for c in failed:
            m = st.session_state.sms_msg.replace("{nom}", c["nom"]).replace("{matricule}", c.get("matricule",""))
            all_sms.append(f"--- {c['nom']} ({c['numero']}) ---\n{m}")
        st.markdown(copy_btn("\n\n".join(all_sms), "📋 Copier tous les SMS", "ret_sms"), unsafe_allow_html=True)
        st.markdown(
            '<a href="https://messages.google.com/web/" target="_blank" rel="noopener" '
            'class="hbtn hbtn-sms" style="display:block;text-align:center;padding:12px;margin-top:8px">'
            '📱 Ouvrir Google Messages</a>', unsafe_allow_html=True)

    with r2:
        st.markdown("#### 📞 Appels")
        for c in failed[:5]:
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:5px 0">
              <span style="font-size:.88rem">{c['nom']} — {c['numero']}</span>
              <a href="tel:{c['numero']}" class="hbtn hbtn-call" style="padding:4px 10px;font-size:.76rem">📞</a>
            </div>""", unsafe_allow_html=True)
        if len(failed) > 5:
            st.info(f"… et {len(failed)-5} autres")

    with r3:
        st.markdown("#### 📧 E-mail")
        if email_cnt:
            st.info(f"{email_cnt} contact(s) avec email. → Onglet **E-mails**")
        else:
            st.warning("Aucun email disponible.")

    st.markdown('</div>', unsafe_allow_html=True)

    # ---- Tableau détaillé ----
    st.markdown("---")
    st.markdown("### 📊 Tableau Détaillé")
    fdf = pd.DataFrame([{
        "Nom": c["nom"], "Numéro": c["numero"],
        "Matricule": c.get("matricule", ""), "Statut": "Sans WhatsApp"
    } for c in failed])
    st.dataframe(fdf, use_container_width=True, hide_index=True)

    # Export CSV
    csv_b64 = base64.b64encode(fdf.to_csv(index=False).encode()).decode()
    st.markdown(f"""
    <a href="data:file/csv;base64,{csv_b64}" download="contacts_echec.csv"
       style="display:inline-block;background:#27ae60;color:#fff;padding:10px 22px;
              border-radius:8px;text-decoration:none;font-weight:600">💾 Exporter en CSV</a>""",
       unsafe_allow_html=True)

    # Vider
    st.markdown("---")
    if st.button("🗑️ Vider la liste des contacts en échec", key="_clear_fail"):
        st.session_state.failed = []
        st.rerun()


# ============================================================
# ROUTEUR PRINCIPAL
# ============================================================
PAGES = {
    "dash":     page_dashboard,
    "contacts": page_contacts,
    "whatsapp": page_whatsapp,
    "sms":      page_sms,
    "email":    page_email,
    "retarget": page_retarget,
}

PAGES.get(PAGE, page_dashboard)()
