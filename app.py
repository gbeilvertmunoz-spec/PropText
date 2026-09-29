import streamlit as st

# ==============================================================================
# 1. CONFIGURATION DE LA PAGE
# ------------------------------------------------------------------------------
# Ceci doit être la toute première commande Streamlit du fichier.
# layout="wide" permet d'utiliser toute la largeur de l'écran.
# ==============================================================================
st.set_page_config(
    page_title="Générateur d'annonces immobilières",
    page_icon="🏠",
    layout="wide"
)


# ==============================================================================
# 2. LE BACKEND (LE MOTEUR PYTHON)
# ------------------------------------------------------------------------------
# C'est ici que se trouve la "logique métier" de votre Micro-SaaS.
# Ce sont des fonctions Python "pures" : elles prennent le dictionnaire
# `maison` en entrée et renvoient du texte (ou des chiffres pour les frais
# de notaire). Aucune ligne Streamlit dans cette partie.
# ==============================================================================

def generer_annonce_classique(maison: dict) -> str:
    """Texte direct et factuel, idéal pour Leboncoin / SeLoger."""
    texte = f"""{maison['titre'].upper()} - {maison['ville']}

À vendre : maison de {maison['surface']} m², {maison['pieces']} pièces, située à {maison['ville']}.

Prix : {format(maison['prix'], ",").replace(",", " ")} €

{maison['description_brute']}

Surface habitable : {maison['surface']} m²
Nombre de pièces : {maison['pieces']}
Ville : {maison['ville']}

Contactez notre agence pour organiser une visite."""
    return texte


def generer_annonce_luxe(maison: dict) -> str:
    """Texte élégant, orienté émotion et investissement (site haut de gamme)."""
    # On calcule le prix au m² : argument très utilisé dans le luxe / l'investissement
    if maison['surface'] > 0:
        prix_m2 = round(maison['prix'] / maison['surface'])
    else:
        prix_m2 = 0

    texte = f"""✨ COUP DE CŒUR — {maison['titre']} à {maison['ville']}

Laissez-vous séduire par ce bien d'exception de {maison['surface']} m², offrant {maison['pieces']} pièces baignées de lumière, idéalement situé au cœur de {maison['ville']}.

{maison['description_brute']}

Un investissement rare sur ce secteur recherché ({format(prix_m2, ",").replace(",", " ")} € / m²), à saisir sans attendre.

Prix de vente : {format(maison['prix'], ",").replace(",", " ")} €

Nos conseillers se tiennent à votre disposition pour une visite privée et confidentielle."""
    return texte


def generer_reseaux_sociaux(maison: dict) -> str:
    """
    Génère un post ultra-dynamique pour Instagram et TikTok
    avec des émojis accrocheurs et des hashtags automatiques.
    """
    # On crée un hashtag personnalisé selon la ville (minuscules, sans espaces)
    ville_tag = maison['ville'].lower().replace(" ", "")

    texte = f"""🎬 NOUVEAU BIEN EXCLUSIF À {maison['ville'].upper()} ! 🏠

Vous cherchez le coup de cœur ? Regardez cette vidéo ! 👇

✨ {maison['titre']}
📏 {maison['surface']} m2 de pur bonheur
🚪 {maison['pieces']} pièces ultra-lumineuses
📍 Située à {maison['ville']}

La description complète et le prix sont disponibles en cliquant sur le lien dans notre bio ! 📲
Contactez-nous en DM pour organiser une visite privée avant qu'il ne soit trop tard. 🕒

#immobilier #{ville_tag} #realestate #visiteimmobiliere #maisonavendre #immo #frenchrealestate"""
    return texte


def generer_email_relance(maison: dict) -> str:
    """Génère un email professionnel pour envoyer aux acheteurs potentiels."""
    texte = f"""Objet : 🌟 Nouveauté en avant-première : Bien disponible à {maison['ville']}

Bonjour,

Je me permets de vous contacter car nous venons de rentrer un nouveau bien qui correspond parfaitement à vos critères de recherche.

Il s'agit d'une opportunité située à {maison['ville']}. Ce bien de {maison['pieces']} pièces développe une surface de {maison['surface']} m².

Voici une brève description :
"{maison['description_brute']}"

Ce bien est proposé au prix de {format(maison['prix'], ",").replace(",", " ")} €.

Les visites commencent cette semaine. Répondez directement à cet e-mail ou contactez-moi par téléphone pour bloquer votre créneau en priorité.

Bien cordialement,
[Votre Nom / Nom de l'Agence]"""
    return texte


def generer_script_telephone(maison: dict) -> str:
    """Génère un script d'appel téléphonique pour guider l'agent à l'oral."""
    texte = f"""📞 SCRIPT D'APPEL TÉLÉPHONIQUE (Nouveau bien : {maison['ville']})

[L'AGENT] : "Bonjour [Nom du Client], c'est [Votre Nom] de l'agence immobilière. Je vous appelle car je viens de rentrer un bien qui va vous plaire, et j'ai tout de suite pensé à vous avant de publier l'annonce sur Leboncoin.

[L'AGENT] : "C'est une maison de {maison['pieces']} pièces et {maison['surface']} m² située sur le secteur de {maison['ville']}. Elle est affichée à {format(maison['prix'], ",").replace(",", " ")} €."

[L'AGENT - S'appuyer sur la description] : "Ce qui est top avec ce bien, c'est que : {maison['description_brute']}"

[L'AGENT - L'ACCROCHE] : "Le prix au m² est très cohérent pour le secteur. J'ai deux créneaux de visite disponibles ce jeudi après-midi. Est-ce que vous êtes disponible plutôt à 14h ou à 16h ?" """
    return texte


def generer_annonce_anglais(maison: dict) -> str:
    """Génère une version anglaise propre pour la clientèle internationale."""
    texte = f"""🇬🇧 EXCLUSIVE PROPERTIES — Lovely home in {maison['ville']}

For sale: Beautiful {maison['pieces']}-room property, ideally located in {maison['ville']}.
Offering a comfortable living space of {maison['surface']} sqm.

Property description:
"{maison['description_brute']}"

An outstanding opportunity on the market.
Asking price: {format(maison['prix'], ",").replace(",", " ")} €

For more information or to schedule a private viewing, please contact our team."""
    return texte


def calculer_frais_notaire(maison: dict) -> dict:
    """Calcule automatiquement les frais de notaire et le budget total."""
    frais_notaire = round(maison['prix'] * 0.08)  # 8% du prix de vente (bien ancien)
    prix_total = maison['prix'] + frais_notaire

    if maison['surface'] > 0:
        prix_m2_total = round(prix_total / maison['surface'])
    else:
        prix_m2_total = 0

    # Contrairement aux autres fonctions, celle-ci renvoie un dictionnaire de
    # chiffres (et non un texte) : on l'affichera avec des "métriques".
    return {
        "frais": frais_notaire,
        "total": prix_total,
        "prix_m2_notaire_inclus": prix_m2_total
    }


def formater_prix(nombre: int) -> str:
    """Petit outil d'affichage : 320000 devient '320 000 €'."""
    return format(nombre, ",").replace(",", " ") + " €"


# ==============================================================================
# 3. INITIALISATION DES DONNÉES (LE DICTIONNAIRE "maison")
# ------------------------------------------------------------------------------
# On utilise st.session_state pour que le dictionnaire "survive" entre les
# interactions de l'utilisateur (sinon Streamlit le réinitialiserait à
# chaque fois qu'on bouge un curseur).
# On ne fait cette initialisation QU'UNE SEULE FOIS grâce au "if... not in".
# ==============================================================================
if "maison" not in st.session_state:
    st.session_state.maison = {
        "titre": "Charmante maison familiale",
        "prix": 320000,
        "surface": 110,
        "pieces": 5,
        "ville": "Bordeaux",
        "description_brute": "Belle maison lumineuse avec jardin, proche des écoles et commerces, garage attenant, aucun travaux à prévoir."
    }


# ==============================================================================
# 4. LE FRONTEND (L'INTERFACE VISUELLE)
# ==============================================================================

st.title("🏠 Générateur d'annonces immobilières")
st.caption("Modifiez les informations dans la barre latérale, tous les textes se mettent à jour instantanément.")

st.divider()


# ------------------------------------------------------------------------------
# 4.A - BARRE LATÉRALE (À GAUCHE) : LES CHAMPS DE SAISIE
# ------------------------------------------------------------------------------
# "with st.sidebar:" place tout ce qui est indenté en dessous dans la
# barre latérale grise à gauche de l'écran.
with st.sidebar:
    st.subheader("📝 Informations du bien")

    # st.text_input crée un champ de texte simple.
    # La "value=" pré-remplit le champ avec la valeur du dictionnaire.
    # Dès que l'utilisateur modifie le champ, Streamlit relance tout le script
    # (c'est normal !) et le dictionnaire est mis à jour.
    st.session_state.maison["titre"] = st.text_input(
        "Titre de l'annonce",
        value=st.session_state.maison["titre"]
    )

    st.session_state.maison["ville"] = st.text_input(
        "Ville",
        value=st.session_state.maison["ville"]
    )

    # st.number_input : idéal pour le prix, avec des boutons "+" et "-" intégrés.
    # step= définit de combien on augmente/diminue à chaque clic.
    st.session_state.maison["prix"] = st.number_input(
        "Prix (€)",
        min_value=0,
        step=5000,
        value=st.session_state.maison["prix"]
    )

    # st.slider : parfait pour une surface, on glisse au lieu de taper.
    st.session_state.maison["surface"] = st.slider(
        "Surface (m²)",
        min_value=10,
        max_value=500,
        value=st.session_state.maison["surface"]
    )

    # st.number_input pour un nombre entier de pièces, avec +/-.
    st.session_state.maison["pieces"] = st.number_input(
        "Nombre de pièces",
        min_value=1,
        max_value=20,
        step=1,
        value=st.session_state.maison["pieces"]
    )

    # st.text_area : un champ plus grand, sur plusieurs lignes,
    # pour la description libre écrite par l'agent.
    st.session_state.maison["description_brute"] = st.text_area(
        "Description libre (points forts, équipements...)",
        value=st.session_state.maison["description_brute"],
        height=150
    )


# On récupère le dictionnaire à jour dans une variable simple, plus facile à lire
maison = st.session_state.maison

# On appelle TOUTES nos fonctions du backend avec les données à jour.
# Comme Streamlit relance le script à chaque modification, ces textes sont
# toujours générés en direct, automatiquement.
texte_classique = generer_annonce_classique(maison)
texte_luxe = generer_annonce_luxe(maison)
texte_reseaux = generer_reseaux_sociaux(maison)
texte_email = generer_email_relance(maison)
texte_telephone = generer_script_telephone(maison)
texte_anglais = generer_annonce_anglais(maison)
budget = calculer_frais_notaire(maison)


# ------------------------------------------------------------------------------
# 4.B - LES ONGLETS (ZONE PRINCIPALE)
# ------------------------------------------------------------------------------
# Avec 7 résultats à afficher, on les range dans des onglets cliquables
# pour garder l'écran propre. st.tabs renvoie un objet par onglet.
onglet_annonces, onglet_contact, onglet_anglais, onglet_budget = st.tabs([
    "📋 Annonces",
    "📧 Contact acheteurs",
    "🇬🇧 International",
    "💰 Budget acheteur"
])


# ------------------------------------------------------------------------------
# ONGLET 1 : LES 3 ANNONCES (Classique, Luxe, Réseaux sociaux)
# ------------------------------------------------------------------------------
with onglet_annonces:
    # st.columns(3) découpe l'écran en 3 colonnes de même largeur
    col_1, col_2, col_3 = st.columns(3)

    with col_1:
        st.subheader("📋 Style Classique")
        st.info("Version directe et factuelle (Leboncoin).")
        # st.code() affiche le texte dans un bloc ET ajoute automatiquement
        # une icône de copie 📋 en haut à droite : c'est notre bouton
        # "Copier le texte" fourni nativement par Streamlit.
        # wrap_lines=True renvoie à la ligne les phrases trop longues.
        st.code(texte_classique, language=None, wrap_lines=True)

    with col_2:
        st.subheader("✨ Style Luxe / Premium")
        st.success("Version élégante, orientée coup de cœur et investissement.")
        st.code(texte_luxe, language=None, wrap_lines=True)

    with col_3:
        st.subheader("🎬 Réseaux sociaux")
        st.warning("Version dynamique avec émojis et hashtags (Instagram / TikTok).")
        st.code(texte_reseaux, language=None, wrap_lines=True)


# ------------------------------------------------------------------------------
# ONGLET 2 : EMAIL DE RELANCE + SCRIPT TÉLÉPHONE
# ------------------------------------------------------------------------------
with onglet_contact:
    col_email, col_tel = st.columns(2)

    with col_email:
        st.subheader("📧 Email de relance")
        st.info("À envoyer aux acheteurs potentiels de votre fichier.")
        st.code(texte_email, language=None, wrap_lines=True)

    with col_tel:
        st.subheader("📞 Script d'appel")
        st.info("Un guide pour l'agent : quoi dire, dans quel ordre.")
        st.code(texte_telephone, language=None, wrap_lines=True)


# ------------------------------------------------------------------------------
# ONGLET 3 : ANNONCE EN ANGLAIS
# ------------------------------------------------------------------------------
with onglet_anglais:
    st.subheader("🇬🇧 Annonce en anglais")
    st.info("Pour la clientèle internationale.")
    # Petite alerte : la description libre est écrite en français par l'agent
    st.caption("⚠️ La description libre saisie dans la barre latérale n'est pas traduite : pensez à l'écrire en anglais pour cette version.")
    st.code(texte_anglais, language=None, wrap_lines=True)


# ------------------------------------------------------------------------------
# ONGLET 4 : BUDGET ACHETEUR (FRAIS DE NOTAIRE)
# ------------------------------------------------------------------------------
with onglet_budget:
    st.subheader("💰 Budget total de l'acheteur")
    st.caption("Estimation avec des frais de notaire à 8 % (bien ancien).")

    # st.metric affiche un gros chiffre avec un petit titre au-dessus.
    # On en place 4 côte à côte grâce à st.columns(4).
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Prix de vente", formater_prix(maison["prix"]))
    m2.metric("Frais de notaire (8 %)", formater_prix(budget["frais"]))
    m3.metric("Budget total", formater_prix(budget["total"]))
    m4.metric("Prix au m² frais inclus", formater_prix(budget["prix_m2_notaire_inclus"]))
