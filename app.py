"""
=================================================================================
IMMOTEXT PRO — Générateur de contenus pour agences immobilières
=================================================================================
Ce fichier est volontairement un seul gros fichier (comme demandé), organisé
en grandes sections numérotées pour que vous puissiez vous y retrouver.

SOMMAIRE :
  1. Imports et configuration
  2. Constantes (plans tarifaires, statuts CRM, essai gratuit)
  3. Backend — génération de textes (annonces, email, script, SEO...)
  4. Backend — calculs financiers (notaire, rendement locatif)
  5. Backend — gestion du compte et de l'essai gratuit
  6. Backend — gestion des biens (CRUD)
  7. Backend — gestion des prospects / CRM (CRUD)
  8. Backend — historique
  9. Initialisation de la session (mémoire de l'application)
 10. Composants d'interface réutilisables (statut compte, mur de paiement)
 11. Pages de l'application (une fonction Python par page)
 12. Barre latérale et routage (quelle page afficher)
=================================================================================
"""

# ==============================================================================
# 1. IMPORTS ET CONFIGURATION
# ------------------------------------------------------------------------------
# datetime nous sert à calculer les jours restants de l'essai gratuit.
# io et csv nous servent à préparer des fichiers à télécharger, sans avoir
# besoin d'installer quoi que ce soit de plus que Streamlit.
# ==============================================================================
import streamlit as st
from datetime import date, timedelta
import io
import csv

# pandas est presque toujours déjà installé avec Streamlit (c'est une de ses
# dépendances), mais on se protège quand même avec un try/except : si jamais
# il n'est pas là, l'application continue de fonctionner, seul le petit
# graphique du tableau de bord sera désactivé.
try:
    import pandas as pd
    PANDAS_DISPONIBLE = True
except ImportError:
    PANDAS_DISPONIBLE = False

st.set_page_config(
    page_title="ImmoText Pro",
    page_icon="🏠",
    layout="wide"
)


# ==============================================================================
# 2. CONSTANTES
# ------------------------------------------------------------------------------
# On regroupe ici toutes les valeurs "fixes" de l'application : la durée de
# l'essai gratuit, les plans tarifaires, les statuts possibles d'un prospect.
# Les rassembler en haut du fichier permet de tout modifier facilement plus
# tard (par exemple changer un prix) sans avoir à chercher dans tout le code.
# ==============================================================================

DUREE_ESSAI_JOURS = 7

TYPES_DE_BIEN = ["Maison", "Appartement", "Terrain", "Local commercial"]

STATUTS_PROSPECT = ["Nouveau", "Contacté", "Visite prévue", "Offre faite", "Conclu", "Perdu"]

# Chaque plan tarifaire est un dictionnaire avec son prix, sa limite de biens
# (None = illimité) et la liste des fonctionnalités affichées sur la page Tarifs.
PLANS = {
    "essai": {
        "nom": "Essai gratuit",
        "prix_mensuel": 0,
        "max_biens": 3,
        "fonctionnalites": [
            "Jusqu'à 3 biens en même temps",
            "Toutes les annonces générées automatiquement",
            "CRM prospects inclus",
            f"Valable {DUREE_ESSAI_JOURS} jours",
        ],
    },
    "starter": {
        "nom": "Starter",
        "prix_mensuel": 19,
        "max_biens": 5,
        "fonctionnalites": [
            "Jusqu'à 5 biens en même temps",
            "Toutes les annonces générées automatiquement",
            "CRM prospects inclus",
            "Export des textes en fichier",
        ],
    },
    "pro": {
        "nom": "Pro",
        "prix_mensuel": 49,
        "max_biens": 30,
        "fonctionnalites": [
            "Jusqu'à 30 biens en même temps",
            "Tout Starter, en plus :",
            "Estimation de rendement locatif",
            "Mots-clés SEO automatiques",
            "Export CSV de votre portefeuille",
        ],
    },
    "agence": {
        "nom": "Agence",
        "prix_mensuel": 99,
        "max_biens": None,
        "fonctionnalites": [
            "Biens illimités",
            "Tout Pro, en plus :",
            "Plusieurs agents (à venir)",
            "Image de marque personnalisée",
            "Support prioritaire",
        ],
    },
}


# ==============================================================================
# 3. BACKEND — GÉNÉRATION DE TEXTES
# ------------------------------------------------------------------------------
# Ce sont des fonctions Python "pures" : elles prennent un bien (et parfois
# les infos de l'agence) en entrée, et renvoient toujours du texte.
# Aucune ligne Streamlit ici : on garde le "moteur" séparé de "l'affichage".
# ==============================================================================

def article_indefini(type_bien: str) -> str:
    """Renvoie 'une' ou 'un' selon le type de bien, pour des phrases naturelles."""
    genres = {"Maison": "une", "Appartement": "un", "Terrain": "un", "Local commercial": "un"}
    return genres.get(type_bien, "un")


def formater_prix(nombre: int) -> str:
    """Transforme 320000 en '320 000 €' (espace tous les 3 chiffres)."""
    return format(nombre, ",").replace(",", " ") + " €"


def tranche_de_prix(prix: int) -> str:
    """Classe un prix dans une tranche, utilisée pour les mots-clés SEO."""
    if prix < 150000:
        return "petit budget"
    elif prix < 300000:
        return "prix accessible"
    elif prix < 600000:
        return "milieu de gamme"
    elif prix < 1000000:
        return "haut de gamme"
    else:
        return "prestige"


def generer_annonce_classique(bien: dict) -> str:
    """Texte direct et factuel, idéal pour Leboncoin / SeLoger."""
    art = article_indefini(bien["type_bien"])
    texte = f"""{bien['titre'].upper()} - {bien['ville']}

À vendre : {art} {bien['type_bien'].lower()} de {bien['surface']} m², {bien['pieces']} pièces, située(e) à {bien['ville']}.

Prix : {formater_prix(bien['prix'])}

{bien['description_brute']}

Type de bien : {bien['type_bien']}
Surface habitable : {bien['surface']} m²
Nombre de pièces : {bien['pieces']}
Ville : {bien['ville']}

Contactez notre agence pour organiser une visite."""
    return texte


def generer_annonce_luxe(bien: dict) -> str:
    """Texte élégant, orienté émotion et investissement (site haut de gamme)."""
    art = article_indefini(bien["type_bien"])
    if bien["surface"] > 0:
        prix_m2 = round(bien["prix"] / bien["surface"])
    else:
        prix_m2 = 0

    texte = f"""✨ COUP DE CŒUR — {bien['titre']} à {bien['ville']}

Laissez-vous séduire par {art} {bien['type_bien'].lower()} d'exception de {bien['surface']} m², offrant {bien['pieces']} pièces baignées de lumière, idéalement située(e) au cœur de {bien['ville']}.

{bien['description_brute']}

Un investissement rare sur ce secteur recherché ({formater_prix(prix_m2)} / m²), à saisir sans attendre.

Prix de vente : {formater_prix(bien['prix'])}

Nos conseillers se tiennent à votre disposition pour une visite privée et confidentielle."""
    return texte


def generer_reseaux_sociaux(bien: dict) -> str:
    """Post ultra-dynamique pour Instagram et TikTok, avec émojis et hashtags."""
    ville_tag = bien["ville"].lower().replace(" ", "").replace("-", "")
    type_tag = bien["type_bien"].lower().replace(" ", "")

    texte = f"""🎬 NOUVEAU BIEN EXCLUSIF À {bien['ville'].upper()} ! 🏠

Vous cherchez le coup de cœur ? Regardez cette vidéo ! 👇

✨ {bien['titre']}
📏 {bien['surface']} m2 de pur bonheur
🚪 {bien['pieces']} pièces ultra-lumineuses
📍 Située(e) à {bien['ville']}

La description complète et le prix sont disponibles en cliquant sur le lien dans notre bio ! 📲
Contactez-nous en DM pour organiser une visite privée avant qu'il ne soit trop tard. 🕒

#immobilier #{ville_tag} #{type_tag} #realestate #visiteimmobiliere #immo #frenchrealestate"""
    return texte


def generer_email_relance(bien: dict, agence: dict) -> str:
    """Email professionnel à envoyer aux acheteurs potentiels du fichier client."""
    art = article_indefini(bien["type_bien"])
    texte = f"""Objet : 🌟 Nouveauté en avant-première : Bien disponible à {bien['ville']}

Bonjour,

Je me permets de vous contacter car nous venons de rentrer un nouveau bien qui correspond parfaitement à vos critères de recherche.

Il s'agit de {art} {bien['type_bien'].lower()} situé(e) à {bien['ville']}. Ce bien de {bien['pieces']} pièces développe une surface de {bien['surface']} m².

Voici une brève description :
« {bien['description_brute']} »

Ce bien est proposé au prix de {formater_prix(bien['prix'])}.

Les visites commencent cette semaine. Répondez directement à cet e-mail ou contactez-moi par téléphone pour bloquer votre créneau en priorité.

Bien cordialement,
{agence['nom_agent']}
{agence['nom_agence']}
{agence['telephone']} | {agence['email']}"""
    return texte


def generer_script_telephone(bien: dict, agence: dict) -> str:
    """Script d'appel téléphonique pour guider l'agent à l'oral."""
    texte = f"""📞 SCRIPT D'APPEL TÉLÉPHONIQUE (Nouveau bien : {bien['ville']})

[{agence['nom_agent'].upper()}] : "Bonjour [Nom du Client], c'est {agence['nom_agent']} de {agence['nom_agence']}. Je vous appelle car je viens de rentrer un bien qui va vous plaire, et j'ai tout de suite pensé à vous avant de publier l'annonce sur Leboncoin."

[{agence['nom_agent'].upper()}] : "C'est {article_indefini(bien['type_bien'])} {bien['type_bien'].lower()} de {bien['pieces']} pièces et {bien['surface']} m² située(e) sur le secteur de {bien['ville']}. Elle est affichée à {formater_prix(bien['prix'])}."

[APPUI SUR LA DESCRIPTION] : "Ce qui est top avec ce bien, c'est que : {bien['description_brute']}"

[ACCROCHE FINALE] : "Le prix au m² est très cohérent pour le secteur. J'ai deux créneaux de visite disponibles ce jeudi après-midi. Est-ce que vous êtes disponible plutôt à 14h ou à 16h ?" """
    return texte


def generer_annonce_anglais(bien: dict) -> str:
    """Version anglaise propre pour la clientèle internationale."""
    texte = f"""🇬🇧 EXCLUSIVE PROPERTIES — Lovely {bien['type_bien'].lower()} in {bien['ville']}

For sale: Beautiful {bien['pieces']}-room property, ideally located in {bien['ville']}.
Offering a comfortable living space of {bien['surface']} sqm.

Property description:
"{bien['description_brute']}"

An outstanding opportunity on the market.
Asking price: {formater_prix(bien['prix'])}

For more information or to schedule a private viewing, please contact our team."""
    return texte


def generer_mots_cles_seo(bien: dict) -> list:
    """Renvoie une liste de mots-clés utiles pour référencer l'annonce en ligne."""
    ville = bien["ville"]
    type_bien = bien["type_bien"].lower()
    tranche = tranche_de_prix(bien["prix"])

    mots_cles = [
        f"{type_bien} à vendre {ville}",
        f"{type_bien} {bien['pieces']} pièces {ville}",
        f"immobilier {ville}",
        f"{type_bien} {tranche} {ville}",
        f"acheter {type_bien} {ville}",
        f"agence immobilière {ville}",
        f"{type_bien} {bien['surface']} m2 {ville}",
    ]
    return mots_cles


# ==============================================================================
# 4. BACKEND — CALCULS FINANCIERS
# ==============================================================================

def calculer_frais_notaire(bien: dict) -> dict:
    """Calcule les frais de notaire et le budget total pour un bien ANCIEN (~8%)."""
    frais_notaire = round(bien["prix"] * 0.08)
    prix_total = bien["prix"] + frais_notaire

    if bien["surface"] > 0:
        prix_m2_total = round(prix_total / bien["surface"])
    else:
        prix_m2_total = 0

    return {
        "frais": frais_notaire,
        "total": prix_total,
        "prix_m2_notaire_inclus": prix_m2_total,
    }


def estimer_rendement_locatif(bien: dict) -> dict:
    """
    Estimation INDICATIVE du loyer et du rendement locatif brut, basée sur une
    hypothèse moyenne de marché (~4,8% brut par an). Ce n'est pas une étude de
    marché réelle : à affiner plus tard avec des données locales précises.
    """
    rendement_brut_hypothese = 0.048  # 4,8% par an, hypothèse moyenne de marché
    loyer_annuel = round(bien["prix"] * rendement_brut_hypothese)
    loyer_mensuel = round(loyer_annuel / 12)

    if bien["prix"] > 0:
        rendement_reel = round((loyer_annuel / bien["prix"]) * 100, 2)
    else:
        rendement_reel = 0

    return {
        "loyer_mensuel": loyer_mensuel,
        "loyer_annuel": loyer_annuel,
        "rendement_brut_pourcent": rendement_reel,
    }


# ==============================================================================
# 5. BACKEND — GESTION DU COMPTE ET DE L'ESSAI GRATUIT
# ------------------------------------------------------------------------------
# Ces fonctions gèrent la "barrière" : essai gratuit de 7 jours, puis blocage
# tant qu'aucun abonnement n'est choisi. Comme ce prototype n'a pas de vraie
# base de données, la date de départ de l'essai est stockée en mémoire de
# session (elle repart de zéro si vous fermez complètement l'application).
# Pour une vraie mise en production, il faudra stocker ça dans une base de
# données liée à un compte utilisateur (voir note technique page Tarifs).
# ==============================================================================

def jours_restants_essai(compte: dict) -> int:
    """Renvoie le nombre de jours restants avant la fin de l'essai gratuit."""
    date_inscription = date.fromisoformat(compte["date_inscription"])
    jours_ecoules = (date.today() - date_inscription).days
    return max(0, DUREE_ESSAI_JOURS - jours_ecoules)


def compte_est_actif(compte: dict) -> bool:
    """Renvoie True si l'utilisateur a un accès complet (essai en cours OU abonnement payant)."""
    if compte["plan"] != "essai":
        return True
    return jours_restants_essai(compte) > 0


def limite_biens_du_plan(compte: dict):
    """Renvoie le nombre maximum de biens autorisés par le plan actuel (None = illimité)."""
    if compte["plan"] == "essai" and not compte_est_actif(compte):
        return 0
    return PLANS[compte["plan"]]["max_biens"]


# ==============================================================================
# 6. BACKEND — GESTION DES BIENS (CRUD)
# ------------------------------------------------------------------------------
# CRUD = Create, Read, Update, Delete : les 4 opérations de base pour gérer
# une liste d'objets. Ici, on gère la liste des biens immobiliers de l'agent.
# ==============================================================================

def creer_nouveau_bien(titre="Nouveau bien", type_bien="Maison", prix=250000,
                        surface=80, pieces=4, ville="", description_brute=""):
    """Crée un dictionnaire 'bien' avec un identifiant unique auto-incrémenté."""
    nouvel_id = st.session_state.prochain_id_bien
    st.session_state.prochain_id_bien += 1
    return {
        "id": nouvel_id,
        "titre": titre,
        "type_bien": type_bien,
        "prix": prix,
        "surface": surface,
        "pieces": pieces,
        "ville": ville,
        "description_brute": description_brute,
        "date_ajout": date.today().isoformat(),
    }


def trouver_bien_par_id(id_bien):
    """Cherche un bien dans la liste grâce à son identifiant. Renvoie None si absent."""
    for bien in st.session_state.biens:
        if bien["id"] == id_bien:
            return bien
    return None


def supprimer_bien(id_bien):
    """Retire un bien de la liste (et les prospects qui lui étaient liés restent, mais orphelins)."""
    st.session_state.biens = [b for b in st.session_state.biens if b["id"] != id_bien]
    if st.session_state.bien_actif_id == id_bien:
        st.session_state.bien_actif_id = st.session_state.biens[0]["id"] if st.session_state.biens else None


def dupliquer_bien(id_bien):
    """Crée une copie d'un bien existant, utile pour un bien très similaire dans le même secteur."""
    original = trouver_bien_par_id(id_bien)
    if original is None:
        return
    copie = creer_nouveau_bien(
        titre=original["titre"] + " (copie)",
        type_bien=original["type_bien"],
        prix=original["prix"],
        surface=original["surface"],
        pieces=original["pieces"],
        ville=original["ville"],
        description_brute=original["description_brute"],
    )
    st.session_state.biens.append(copie)


# ==============================================================================
# 7. BACKEND — GESTION DES PROSPECTS / CRM (CRUD)
# ------------------------------------------------------------------------------
# Un mini CRM (Customer Relationship Management) pour suivre les acheteurs
# potentiels intéressés par vos biens, directement dans l'application.
# ==============================================================================

def creer_nouveau_prospect(nom, telephone, email, bien_interesse_id, statut="Nouveau", notes=""):
    nouvel_id = st.session_state.prochain_id_prospect
    st.session_state.prochain_id_prospect += 1
    return {
        "id": nouvel_id,
        "nom": nom,
        "telephone": telephone,
        "email": email,
        "bien_interesse_id": bien_interesse_id,
        "statut": statut,
        "notes": notes,
        "date_ajout": date.today().isoformat(),
    }


def supprimer_prospect(id_prospect):
    st.session_state.prospects = [p for p in st.session_state.prospects if p["id"] != id_prospect]


# ==============================================================================
# 8. BACKEND — HISTORIQUE
# ------------------------------------------------------------------------------
# Chaque fois que l'agent clique sur "Enregistrer dans l'historique" pour un
# texte généré, on garde une trace : quel type de contenu, pour quel bien,
# et quand. Utile pour se souvenir de ce qui a déjà été publié.
# ==============================================================================

def enregistrer_dans_historique(type_contenu, titre_bien):
    st.session_state.historique.insert(0, {
        "date": date.today().isoformat(),
        "type_contenu": type_contenu,
        "bien": titre_bien,
    })


# ==============================================================================
# 9. INITIALISATION DE LA SESSION (LA "MÉMOIRE" DE L'APPLICATION)
# ------------------------------------------------------------------------------
# st.session_state garde toutes ces données en mémoire tant que l'onglet du
# navigateur reste ouvert. On initialise chaque variable UNE SEULE FOIS,
# grâce à "if ... not in st.session_state", sinon tout serait effacé à
# chaque interaction (clic, saisie...).
# ==============================================================================

def initialiser_session():
    if "compte" not in st.session_state:
        st.session_state.compte = {
            "date_inscription": date.today().isoformat(),
            "plan": "essai",
        }

    if "agence" not in st.session_state:
        st.session_state.agence = {
            "nom_agence": "Mon Agence Immobilière",
            "nom_agent": "Camille Dupont",
            "telephone": "06 12 34 56 78",
            "email": "contact@monagence.fr",
        }

    if "prochain_id_bien" not in st.session_state:
        st.session_state.prochain_id_bien = 1

    if "prochain_id_prospect" not in st.session_state:
        st.session_state.prochain_id_prospect = 1

    if "biens" not in st.session_state:
        # On crée un bien d'exemple pour que l'application ne soit pas vide
        # au premier lancement, et que vous puissiez tester tout de suite.
        bien_exemple = creer_nouveau_bien(
            titre="Charmante maison familiale",
            type_bien="Maison",
            prix=320000,
            surface=110,
            pieces=5,
            ville="Bordeaux",
            description_brute="Belle maison lumineuse avec jardin, proche des écoles et commerces, garage attenant, aucun travaux à prévoir.",
        )
        st.session_state.biens = [bien_exemple]

    if "bien_actif_id" not in st.session_state:
        st.session_state.bien_actif_id = st.session_state.biens[0]["id"] if st.session_state.biens else None

    if "prospects" not in st.session_state:
        st.session_state.prospects = []

    if "historique" not in st.session_state:
        st.session_state.historique = []

    if "page" not in st.session_state:
        st.session_state.page = "🏠 Tableau de bord"


# ==============================================================================
# 10. COMPOSANTS D'INTERFACE RÉUTILISABLES
# ------------------------------------------------------------------------------
# Des petits blocs d'affichage utilisés sur plusieurs pages : le statut du
# compte (essai / abonné) dans la barre latérale, et le "mur de paiement"
# qui s'affiche quand l'essai gratuit est terminé.
# ==============================================================================

def acces_autorise() -> bool:
    """Raccourci pratique utilisé au début de chaque page qui doit être protégée."""
    return compte_est_actif(st.session_state.compte)


def afficher_statut_compte():
    """Affiche dans la barre latérale l'état du compte (essai ou abonnement)."""
    compte = st.session_state.compte

    if compte["plan"] != "essai":
        st.sidebar.success(f"✅ Abonnement {PLANS[compte['plan']]['nom']} actif")
    else:
        restants = jours_restants_essai(compte)
        if restants > 3:
            st.sidebar.info(f"🎁 Essai gratuit : {restants} jours restants")
        elif restants > 0:
            st.sidebar.warning(f"⏳ Essai gratuit : plus que {restants} jour(s) !")
        else:
            st.sidebar.error("🔒 Votre essai gratuit est terminé")

    # Petit outil de démonstration, pour tester le système sans attendre 7 jours.
    with st.sidebar.expander("🛠️ Mode démo (tester l'essai)"):
        st.caption("Ces boutons n'existent que pour tester le prototype rapidement.")
        if st.button("⏩ Avancer d'un jour", key="bouton_avancer_jour"):
            ancienne_date = date.fromisoformat(compte["date_inscription"])
            compte["date_inscription"] = (ancienne_date - timedelta(days=1)).isoformat()
            st.rerun()
        if st.button("🔄 Réinitialiser l'essai (7 jours)", key="bouton_reset_essai"):
            compte["date_inscription"] = date.today().isoformat()
            compte["plan"] = "essai"
            st.rerun()


def afficher_mur_paiement(nom_fonctionnalite: str):
    """S'affiche à la place d'une page quand l'essai gratuit est terminé."""
    st.error("🔒 Votre essai gratuit de 7 jours est terminé.")
    st.write(
        f"Pour continuer à utiliser **{nom_fonctionnalite}**, choisissez un abonnement ci-dessous. "
        "Vous pouvez aussi consulter votre tableau de bord gratuitement."
    )
    if st.button("💳 Voir les abonnements disponibles"):
        st.session_state.page = "💳 Abonnement & Tarifs"
        st.rerun()


# ==============================================================================
# 11. PAGES DE L'APPLICATION
# ------------------------------------------------------------------------------
# Une fonction par page. C'est ce qu'on appelle une "application multi-pages"
# faite à la main : on garde en mémoire (st.session_state.page) quelle page
# est actuellement affichée, et on appelle la bonne fonction en conséquence
# (voir la section 12, tout en bas du fichier).
# ==============================================================================

# ------------------------------------------------------------------------------
# 11.A — TABLEAU DE BORD
# ------------------------------------------------------------------------------
def afficher_page_tableau_de_bord():
    st.title("🏠 Tableau de bord")
    st.caption("Vue d'ensemble de votre activité.")

    biens = st.session_state.biens
    prospects = st.session_state.prospects
    valeur_portefeuille = sum(b["prix"] for b in biens)

    # 4 grosses métriques côte à côte
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Biens en gestion", len(biens))
    col2.metric("Valeur du portefeuille", formater_prix(valeur_portefeuille))
    col3.metric("Prospects suivis", len(prospects))
    col4.metric("Textes enregistrés", len(st.session_state.historique))

    st.divider()

    col_gauche, col_droite = st.columns(2)

    with col_gauche:
        st.subheader("💰 Répartition des prix par bien")
        if biens and PANDAS_DISPONIBLE:
            df = pd.DataFrame({
                "Bien": [b["titre"] for b in biens],
                "Prix": [b["prix"] for b in biens],
            }).set_index("Bien")
            st.bar_chart(df)
        elif not biens:
            st.info("Ajoutez un bien dans « Mes biens » pour voir apparaître le graphique.")
        else:
            st.caption("Le graphique nécessite le module pandas (normalement déjà installé avec Streamlit).")

    with col_droite:
        st.subheader("🕒 Derniers textes enregistrés")
        if st.session_state.historique:
            for entree in st.session_state.historique[:5]:
                st.write(f"**{entree['type_contenu']}** — {entree['bien']} _(le {entree['date']})_")
        else:
            st.info("Aucun texte enregistré pour l'instant. Rendez-vous dans « Générateur de contenus ».")


# ------------------------------------------------------------------------------
# 11.B — MES BIENS
# ------------------------------------------------------------------------------
def afficher_page_mes_biens():
    if not acces_autorise():
        afficher_mur_paiement("la gestion de vos biens")
        return

    st.title("🗂️ Mes biens")
    st.caption("Ajoutez, modifiez ou supprimez les biens de votre portefeuille.")

    compte = st.session_state.compte
    limite = limite_biens_du_plan(compte)
    nb_biens_actuels = len(st.session_state.biens)

    # --- Formulaire d'ajout d'un nouveau bien ---
    with st.expander("➕ Ajouter un nouveau bien", expanded=(nb_biens_actuels == 0)):
        if limite is not None and nb_biens_actuels >= limite:
            st.warning(
                f"Votre plan actuel ({PLANS[compte['plan']]['nom']}) est limité à {limite} biens. "
                "Passez à un plan supérieur pour en ajouter davantage."
            )
        else:
            with st.form("formulaire_ajout_bien", clear_on_submit=True):
                c1, c2 = st.columns(2)
                titre = c1.text_input("Titre de l'annonce", value="Nouveau bien")
                type_bien = c2.selectbox("Type de bien", TYPES_DE_BIEN)
                c3, c4, c5 = st.columns(3)
                prix = c3.number_input("Prix (€)", min_value=0, step=5000, value=250000)
                surface = c4.number_input("Surface (m²)", min_value=1, value=80)
                pieces = c5.number_input("Nombre de pièces", min_value=1, value=4)
                ville = st.text_input("Ville", value="")
                description = st.text_area("Description libre", value="", height=100)

                valide = st.form_submit_button("Ajouter ce bien")
                if valide:
                    nouveau = creer_nouveau_bien(
                        titre=titre, type_bien=type_bien, prix=prix,
                        surface=surface, pieces=pieces, ville=ville,
                        description_brute=description,
                    )
                    st.session_state.biens.append(nouveau)
                    st.session_state.bien_actif_id = nouveau["id"]
                    st.success(f"Bien « {titre} » ajouté !")
                    st.rerun()

    st.divider()

    # --- Liste des biens existants, chacun dans un expander avec son propre formulaire ---
    if not st.session_state.biens:
        st.info("Vous n'avez encore aucun bien. Ajoutez-en un ci-dessus pour commencer.")
        return

    for bien in st.session_state.biens:
        with st.expander(f"🏡 {bien['titre']} — {bien['ville']} — {formater_prix(bien['prix'])}"):
            with st.form(f"formulaire_edition_{bien['id']}"):
                c1, c2 = st.columns(2)
                nouveau_titre = c1.text_input("Titre", value=bien["titre"], key=f"titre_{bien['id']}")
                nouveau_type = c2.selectbox(
                    "Type de bien", TYPES_DE_BIEN,
                    index=TYPES_DE_BIEN.index(bien["type_bien"]) if bien["type_bien"] in TYPES_DE_BIEN else 0,
                    key=f"type_{bien['id']}"
                )
                c3, c4, c5 = st.columns(3)
                nouveau_prix = c3.number_input("Prix (€)", min_value=0, step=5000, value=bien["prix"], key=f"prix_{bien['id']}")
                nouvelle_surface = c4.number_input("Surface (m²)", min_value=1, value=bien["surface"], key=f"surface_{bien['id']}")
                nouvelles_pieces = c5.number_input("Pièces", min_value=1, value=bien["pieces"], key=f"pieces_{bien['id']}")
                nouvelle_ville = st.text_input("Ville", value=bien["ville"], key=f"ville_{bien['id']}")
                nouvelle_description = st.text_area("Description libre", value=bien["description_brute"], height=100, key=f"description_{bien['id']}")

                enregistrer = st.form_submit_button("💾 Enregistrer les modifications")
                if enregistrer:
                    bien["titre"] = nouveau_titre
                    bien["type_bien"] = nouveau_type
                    bien["prix"] = nouveau_prix
                    bien["surface"] = nouvelle_surface
                    bien["pieces"] = nouvelles_pieces
                    bien["ville"] = nouvelle_ville
                    bien["description_brute"] = nouvelle_description
                    st.success("Modifications enregistrées.")
                    st.rerun()

            # Les boutons d'action restent en dehors du formulaire (un formulaire
            # ne peut avoir qu'un seul bouton de validation).
            b1, b2, b3 = st.columns(3)
            if b1.button("✍️ Générer du contenu pour ce bien", key=f"selectionner_{bien['id']}"):
                st.session_state.bien_actif_id = bien["id"]
                st.session_state.page = "✍️ Générateur de contenus"
                st.rerun()
            if b2.button("📄 Dupliquer", key=f"dupliquer_{bien['id']}"):
                dupliquer_bien(bien["id"])
                st.rerun()
            if b3.button("🗑️ Supprimer", key=f"supprimer_{bien['id']}"):
                supprimer_bien(bien["id"])
                st.rerun()

    # --- Export CSV de tout le portefeuille ---
    st.divider()
    st.subheader("📤 Export de votre portefeuille")
    buffer_csv = io.StringIO()
    writer = csv.DictWriter(buffer_csv, fieldnames=["titre", "type_bien", "prix", "surface", "pieces", "ville"])
    writer.writeheader()
    for bien in st.session_state.biens:
        writer.writerow({cle: bien[cle] for cle in ["titre", "type_bien", "prix", "surface", "pieces", "ville"]})

    st.download_button(
        "⬇️ Télécharger la liste des biens (.csv)",
        data=buffer_csv.getvalue(),
        file_name="mes_biens.csv",
        mime="text/csv",
    )


# ------------------------------------------------------------------------------
# 11.C — GÉNÉRATEUR DE CONTENUS
# ------------------------------------------------------------------------------
def afficher_page_generateur():
    if not acces_autorise():
        afficher_mur_paiement("le générateur de contenus")
        return

    st.title("✍️ Générateur de contenus")

    if not st.session_state.biens:
        st.info("Ajoutez d'abord un bien dans « Mes biens » pour pouvoir générer du contenu.")
        return

    # --- Sélection du bien actif ---
    titres_biens = [f"{b['titre']} — {b['ville']}" for b in st.session_state.biens]
    index_actif = 0
    for i, b in enumerate(st.session_state.biens):
        if b["id"] == st.session_state.bien_actif_id:
            index_actif = i
            break

    choix = st.selectbox("Bien concerné", titres_biens, index=index_actif)
    bien = st.session_state.biens[titres_biens.index(choix)]
    st.session_state.bien_actif_id = bien["id"]

    agence = st.session_state.agence

    # On génère TOUS les contenus à partir du bien sélectionné.
    texte_classique = generer_annonce_classique(bien)
    texte_luxe = generer_annonce_luxe(bien)
    texte_reseaux = generer_reseaux_sociaux(bien)
    texte_email = generer_email_relance(bien, agence)
    texte_telephone = generer_script_telephone(bien, agence)
    texte_anglais = generer_annonce_anglais(bien)
    mots_cles = generer_mots_cles_seo(bien)
    budget = calculer_frais_notaire(bien)
    rendement = estimer_rendement_locatif(bien)

    st.divider()

    onglet_annonces, onglet_contact, onglet_international, onglet_budget, onglet_seo = st.tabs([
        "📋 Annonces", "📧 Contact acheteurs", "🇬🇧 International", "💰 Budget acheteur", "📈 SEO & Rendement"
    ])

    # Petite fonction locale pour éviter de répéter le même bloc 6 fois :
    # affiche le texte, un bouton pour l'enregistrer dans l'historique,
    # et un bouton pour le télécharger en .txt.
    def bloc_texte(titre_carte, texte, type_contenu, nom_fichier):
        st.write(f"**{titre_carte}**")
        st.code(texte, language=None)
        c1, c2 = st.columns(2)
        if c1.button("💾 Enregistrer dans l'historique", key=f"historique_{type_contenu}_{bien['id']}"):
            enregistrer_dans_historique(type_contenu, bien["titre"])
            st.success("Ajouté à l'historique !")
        c2.download_button(
            "⬇️ Télécharger (.txt)", data=texte, file_name=nom_fichier,
            key=f"telecharger_{type_contenu}_{bien['id']}"
        )

    with onglet_annonces:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("Version directe et factuelle (Leboncoin).")
            bloc_texte("Style Classique", texte_classique, "Annonce classique", "annonce_classique.txt")
        with col2:
            st.success("Version élégante, orientée coup de cœur et investissement.")
            bloc_texte("Style Luxe / Premium", texte_luxe, "Annonce luxe", "annonce_luxe.txt")
        with col3:
            st.warning("Version dynamique avec émojis et hashtags.")
            bloc_texte("Réseaux sociaux", texte_reseaux, "Post réseaux sociaux", "post_reseaux_sociaux.txt")

    with onglet_contact:
        col_email, col_tel = st.columns(2)
        with col_email:
            st.info("À envoyer aux acheteurs potentiels de votre fichier.")
            bloc_texte("Email de relance", texte_email, "Email de relance", "email_relance.txt")
        with col_tel:
            st.info("Un guide pour l'agent : quoi dire, dans quel ordre.")
            bloc_texte("Script d'appel", texte_telephone, "Script téléphone", "script_telephone.txt")

    with onglet_international:
        st.info("Pour la clientèle internationale.")
        st.caption("⚠️ La description libre n'est pas traduite automatiquement : écrivez-la en anglais si besoin.")
        bloc_texte("Annonce en anglais", texte_anglais, "Annonce anglaise", "annonce_anglais.txt")

    with onglet_budget:
        st.caption("Estimation avec des frais de notaire à 8 % (bien ancien).")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Prix de vente", formater_prix(bien["prix"]))
        m2.metric("Frais de notaire (8 %)", formater_prix(budget["frais"]))
        m3.metric("Budget total", formater_prix(budget["total"]))
        m4.metric("Prix au m² frais inclus", formater_prix(budget["prix_m2_notaire_inclus"]))

    with onglet_seo:
        col_seo, col_rendement = st.columns(2)
        with col_seo:
            st.subheader("🔑 Mots-clés SEO suggérés")
            st.caption("À utiliser dans le titre et la description de votre annonce en ligne.")
            for mot in mots_cles:
                st.write(f"- {mot}")
        with col_rendement:
            st.subheader("📈 Rendement locatif estimé")
            st.metric("Loyer mensuel estimé", formater_prix(rendement["loyer_mensuel"]))
            st.metric("Loyer annuel estimé", formater_prix(rendement["loyer_annuel"]))
            st.metric("Rendement brut estimé", f"{rendement['rendement_brut_pourcent']} %")
            st.caption(
                "⚠️ Estimation indicative basée sur une hypothèse moyenne de marché "
                "(4,8 % brut/an). Ne remplace pas une étude de marché locale."
            )


# ------------------------------------------------------------------------------
# 11.D — PROSPECTS (CRM)
# ------------------------------------------------------------------------------
def afficher_page_crm():
    if not acces_autorise():
        afficher_mur_paiement("le suivi des prospects")
        return

    st.title("👥 Prospects (CRM)")
    st.caption("Suivez les acheteurs potentiels intéressés par vos biens.")

    if not st.session_state.biens:
        st.info("Ajoutez d'abord un bien dans « Mes biens » avant de créer des prospects.")
        return

    # --- Formulaire d'ajout d'un prospect ---
    with st.expander("➕ Ajouter un prospect"):
        with st.form("formulaire_ajout_prospect", clear_on_submit=True):
            c1, c2 = st.columns(2)
            nom = c1.text_input("Nom du prospect")
            telephone = c2.text_input("Téléphone")
            email = st.text_input("Email")

            titres_biens = [f"{b['titre']} — {b['ville']}" for b in st.session_state.biens]
            choix_bien = st.selectbox("Bien qui l'intéresse", titres_biens)
            statut = st.selectbox("Statut", STATUTS_PROSPECT)
            notes = st.text_area("Notes", height=80)

            valide = st.form_submit_button("Ajouter ce prospect")
            if valide and nom:
                bien_lie = st.session_state.biens[titres_biens.index(choix_bien)]
                nouveau_prospect = creer_nouveau_prospect(
                    nom=nom, telephone=telephone, email=email,
                    bien_interesse_id=bien_lie["id"], statut=statut, notes=notes,
                )
                st.session_state.prospects.append(nouveau_prospect)
                st.success(f"Prospect « {nom} » ajouté !")
                st.rerun()

    st.divider()

    if not st.session_state.prospects:
        st.info("Aucun prospect pour l'instant.")
        return

    # --- Compteur par statut ---
    st.subheader("Vue d'ensemble")
    colonnes_statuts = st.columns(len(STATUTS_PROSPECT))
    for colonne, statut in zip(colonnes_statuts, STATUTS_PROSPECT):
        nb = len([p for p in st.session_state.prospects if p["statut"] == statut])
        colonne.metric(statut, nb)

    st.divider()

    # --- Liste des prospects ---
    st.subheader("Liste des prospects")
    for prospect in st.session_state.prospects:
        bien_lie = trouver_bien_par_id(prospect["bien_interesse_id"])
        nom_bien = bien_lie["titre"] if bien_lie else "(bien supprimé)"

        with st.expander(f"👤 {prospect['nom']} — intéressé(e) par « {nom_bien} »"):
            st.write(f"📞 {prospect['telephone']}  |  ✉️ {prospect['email']}")
            if prospect["notes"]:
                st.write(f"📝 {prospect['notes']}")

            c1, c2 = st.columns([2, 1])
            nouveau_statut = c1.selectbox(
                "Statut", STATUTS_PROSPECT,
                index=STATUTS_PROSPECT.index(prospect["statut"]),
                key=f"statut_{prospect['id']}"
            )
            prospect["statut"] = nouveau_statut

            if c2.button("🗑️ Supprimer", key=f"supprimer_prospect_{prospect['id']}"):
                supprimer_prospect(prospect["id"])
                st.rerun()


# ------------------------------------------------------------------------------
# 11.E — PARAMÈTRES AGENCE
# ------------------------------------------------------------------------------
def afficher_page_parametres():
    st.title("⚙️ Paramètres agence")
    st.caption("Ces informations sont utilisées automatiquement dans les emails et scripts d'appel.")

    agence = st.session_state.agence

    with st.form("formulaire_agence"):
        nom_agence = st.text_input("Nom de l'agence", value=agence["nom_agence"])
        nom_agent = st.text_input("Votre nom", value=agence["nom_agent"])
        telephone = st.text_input("Téléphone", value=agence["telephone"])
        email = st.text_input("Email", value=agence["email"])

        enregistrer = st.form_submit_button("💾 Enregistrer")
        if enregistrer:
            agence["nom_agence"] = nom_agence
            agence["nom_agent"] = nom_agent
            agence["telephone"] = telephone
            agence["email"] = email
            st.success("Paramètres enregistrés ! Ils seront utilisés dans vos prochains textes.")


# ------------------------------------------------------------------------------
# 11.F — ABONNEMENT & TARIFS
# ------------------------------------------------------------------------------
def afficher_page_tarifs():
    st.title("💳 Abonnement & Tarifs")
    st.caption(
        f"Essai gratuit de {DUREE_ESSAI_JOURS} jours, sans carte bancaire. "
        "Choisissez ensuite l'abonnement adapté à votre activité."
    )

    compte = st.session_state.compte
    colonnes = st.columns(len(PLANS))

    for colonne, (cle_plan, plan) in zip(colonnes, PLANS.items()):
        with colonne:
            with st.container(border=True):
                st.subheader(plan["nom"])
                if plan["prix_mensuel"] == 0:
                    st.write("**Gratuit**")
                else:
                    st.write(f"**{plan['prix_mensuel']} € / mois**")

                for fonctionnalite in plan["fonctionnalites"]:
                    st.write(f"- {fonctionnalite}")

                if compte["plan"] == cle_plan:
                    st.success("✅ Plan actuel")
                elif cle_plan == "essai":
                    st.caption("Plan de départ automatique.")
                else:
                    if st.button(f"Choisir {plan['nom']}", key=f"choisir_{cle_plan}"):
                        compte["plan"] = cle_plan
                        st.balloons()
                        st.success(f"Abonnement {plan['nom']} activé !")
                        st.rerun()

    st.divider()
    with st.expander("🔧 Note technique : comment brancher un vrai paiement"):
        st.write(
            "Dans ce prototype, cliquer sur « Choisir un plan » simule l'abonnement : "
            "aucun paiement réel n'est effectué, et l'information n'est gardée qu'en mémoire "
            "le temps de votre session.\n\n"
            "Pour une vraie mise en production, il faudrait :\n"
            "1. Créer un compte utilisateur persistant (base de données, ex. Supabase ou PostgreSQL).\n"
            "2. Intégrer un vrai système de paiement (ex. Stripe Checkout) qui déclenche "
            "la mise à jour du plan après un paiement confirmé (via un webhook).\n"
            "3. Remplacer `st.session_state` par une lecture/écriture en base de données, "
            "pour que l'abonnement soit conservé même après fermeture du navigateur."
        )


# ==============================================================================
# 12. BARRE LATÉRALE ET ROUTAGE
# ------------------------------------------------------------------------------
# On initialise d'abord toute la mémoire de l'application, puis on construit
# la barre latérale (statut du compte + menu de navigation), et enfin on
# affiche la page choisie en appelant la fonction correspondante.
# ==============================================================================

initialiser_session()

with st.sidebar:
    st.markdown("## 🏠 ImmoText Pro")
    afficher_statut_compte()
    st.divider()

    PAGES = [
        "🏠 Tableau de bord",
        "🗂️ Mes biens",
        "✍️ Générateur de contenus",
        "👥 Prospects (CRM)",
        "⚙️ Paramètres agence",
        "💳 Abonnement & Tarifs",
    ]
    st.session_state.page = st.radio("Navigation", PAGES, index=PAGES.index(st.session_state.page))

# On affiche la page choisie en comparant st.session_state.page à chaque nom de page.
if st.session_state.page == "🏠 Tableau de bord":
    afficher_page_tableau_de_bord()
elif st.session_state.page == "🗂️ Mes biens":
    afficher_page_mes_biens()
elif st.session_state.page == "✍️ Générateur de contenus":
    afficher_page_generateur()
elif st.session_state.page == "👥 Prospects (CRM)":
    afficher_page_crm()
elif st.session_state.page == "⚙️ Paramètres agence":
    afficher_page_parametres()
elif st.session_state.page == "💳 Abonnement & Tarifs":
    afficher_page_tarifs()
