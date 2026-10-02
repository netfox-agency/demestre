#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Générateur des landings Google Ads de DAVID DEMESTRE, couvreur à Quimper (29000).

  templates/page.html  +  SERVICES[...]  ->  <slug>/index.html

Usage :  python3 build.py

Tout le contenu rédactionnel vit ici. La structure vit dans templates/page.html.
Les pages générées ne s'éditent JAMAIS à la main : elles sont écrasées.

Brief client (SMS du 17/09/2026, retranscrit) : « Couverture », « Démoussage »,
« oui, au niveau couverture » pour les urgences, et « démoussage de toiture et
réparation au niveau de l'ardoise / couverture, tu mets ça en premier ».
D'où l'ordre des pages ci-dessous : le métier, puis la réparation (sa priorité),
puis le démoussage, puis la réfection.
"""

import html
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).parent

# ============================================================ CONSTANTES CLIENT
# ⚠️ PLACEHOLDER : numéro professionnel non encore communiqué.
# À remplacer ici (une édition = toutes les pages), puis relancer le build.
PHONE_DISPLAY = "06 00 00 00 00"
PHONE_TEL = "+33600000000"

# ⚠️ PLACEHOLDER : domaine à réserver. Proposition retenue faute de mieux ;
# « demestre-couverture.fr » est libre au moment de la rédaction.
URL_BASE = "https://demestre-couverture.fr"

# Clé Web3Forms à créer avec l'adresse email de l'entreprise.
WEB3FORMS_KEY = "REMPLACER_PAR_VOTRE_CLE_WEB3FORMS"

# Conversions Google Ads : tant qu'un identifiant contient XXXX, script.js
# ignore l'envoi (aucune conversion fantôme pendant la recette).
# Compte créé le 21/09/2026 : 594-379-1441, EUR, Europe/Paris, balisage
# automatique actif. L'identifiant ci-dessous est celui attribué au compte.
# ⚠️ Les deux LIBELLÉS restent en XXXX : les actions de conversion n'existent
# pas encore dans le compte (statut NOT_CONVERSION_TRACKED). Tant qu'ils sont
# en XXXX, rien n'est envoyé — c'est voulu.
ADS_GTAG = "AW-18467990702"
ADS_CONV_DEVIS = "AW-18467990702/XXXXdevisXXXX"
ADS_CONV_APPEL = "AW-18467990702/XXXXappelXXXX"

# ============================================================ IDENTITÉ
# Identité publiée au registre du commerce :
#   DEMESTRE David — entreprise individuelle
#   RCS Quimper 792 754 269, activité depuis le 13/09/2022
#   Nom commercial et enseigne : DEMESTRE DAVID
#   Établissement : 123 avenue Pierre Mendès France, 29000 Quimper
#
# Les points à vérifier avant diffusion sont listés dans README-INTERNE.md.
BRAND = "David Demestre Couverture"
BRAND_SHORT = "David Demestre"
BRAND_ALT = "DEMESTRE DAVID"            # enseigne exacte au RCS
BRAND_TAG = "Couverture · Ardoise · Démoussage"
ADRESSE = "123 avenue Pierre Mendès France, 29000 Quimper"
FOUNDING = "2022"

# Tant que le SIRET complet n'est pas renseigné, le pied de page n'affiche que
# le SIREN — on n'écrit que ce qui est vérifiable au registre.
SIREN = "792 754 269"
SIRET = ""                               # ex. "792 754 269 00028"
ASSUREUR_DECENNALE = ""                  # ex. "AXA, contrat n° 1234567"


def mentions():
    """Identification de l'annonceur : la loi l'impose, Google Ads la vérifie.
    On n'écrit que ce qui est vérifiable au registre tant que le reste manque."""
    bouts = ["%s — entreprise individuelle" % BRAND_ALT]
    bouts.append(("SIRET " + SIRET) if SIRET else ("RCS Quimper " + SIREN))
    if ASSUREUR_DECENNALE:
        bouts.append("Garantie décennale : " + ASSUREUR_DECENNALE)
    return " · ".join(bouts)


# ============================================================ AVIS
# ⚠️ N'INVENTEZ RIEN. Coller les vrais avis Google (texte exact, prénom, commune).
# Liste vide = section masquée. Format : ("texte", "Prénom", "Commune")
AVIS = [
]

# Bandeau de preuves, sous le hero. Quatre faits, aucun inventé : pas de note
# Google tant qu'il n'y a pas de fiche, pas de « 500 chantiers » sorti du chapeau.
PROOFS = [
    ("Ardoise", "la couverture du pays bigouden"),
    (FOUNDING, "artisan installé depuis"),
    ("35 km", "autour de Quimper"),
    ("48 h", "visite et devis gratuits"),
]

# ============================================================ ZONE
# Rayon d'environ 35 km autour de Quimper : la Cornouaille. Pays bigouden au
# sud-ouest, baie de Douarnenez au nord-ouest, Concarneau à l'est, Châteaulin
# au nord. Au-delà (Brest, Quimperlé, Lorient) le déplacement ne tient plus.
CITIES = [
    "Quimper", "Concarneau", "Douarnenez", "Pont-l'Abbé",
    "Fouesnant", "Bénodet", "Ergué-Gabéric", "Pluguffan",
    "Plomelin", "Plonéour-Lanvern", "Combrit", "Loctudy",
    "Plobannalec-Lesconil", "Le Guilvinec", "Penmarc'h", "Plomeur",
    "Trégunc", "Rosporden", "Briec", "Châteaulin",
    "Pont-Croix", "Audierne", "Locronan", "Plogastel-Saint-Germain",
    "Saint-Évarzec", "La Forêt-Fouesnant", "Gouesnac'h", "Clohars-Fouesnant",
]
# Les quatre communes mises en avant (pastilles pleines) : l'atelier et les
# trois villes qui portent le volume de recherche du département.
CITY_MAIN = {"Quimper", "Concarneau", "Douarnenez", "Pont-l'Abbé"}

GEO_REGION = "FR-29"
GEO_PLACENAME = "Quimper"
SCHEMA_ADDRESS = ('{"@type":"PostalAddress","streetAddress":"123 avenue Pierre Mendès France",'
                  '"addressLocality":"Quimper","postalCode":"29000",'
                  '"addressRegion":"Bretagne","addressCountry":"FR"}')
SCHEMA_GEO = '{"@type":"GeoCoordinates","latitude":47.9960,"longitude":-4.0975}'

FOOTER_GEO = "Quimper · Concarneau · Douarnenez · Pont-l'Abbé · Finistère (29)"
VILLE_PH = "Quimper, Concarneau, Douarnenez…"
RAPPEL_LINE = "David vous rappelle sous 48 h ouvrées."
CRUMB_ROOT = "Couvreur à Quimper"
FORM_HEAD_P = ("Quatre champs, une minute. David vous rappelle lui-même, avec une "
               "première estimation et une date de visite.")
ZONE_H2 = "De Quimper au pays bigouden, <em>dans un rayon de 35&nbsp;km.</em>"
ZONE_LEAD = ("David Demestre est installé à Quimper. De Douarnenez à Concarneau et "
             "de Châteaulin au Guilvinec, le déplacement est court : la visite se cale "
             "vite, et le suivi ne passe pas par un centre d'appel.")

ACCUEIL_H1 = "David Demestre, <em>couverture et ardoise.</em>"
ACCUEIL_LEAD = ("Couvreur installé à Quimper, sur toute la Cornouaille. "
                "Choisissez ce qui vous amène :")

# ============================================================ SERVICES

SERVICES = {

# ------------------------------------------------------------ 0. COUVREUR
# Page générique du métier. Elle existe parce que le groupe d'annonces le plus
# gros sera « couvreur + ville » : envoyer ce trafic sur « fuite de toiture »
# est un décalage message/page qui coûte du niveau de qualité ET de la
# conversion. C'est aussi elle que doit viser une future fiche Google.
"couvreur-cornouaille": {
  "generique": True,
  "territoire": True,
  "ouv": ("En Cornouaille, un toit travaille <em>toute l'année.</em>",
          "Pluie fine de novembre à mars, vent d'ouest qui soulève, embruns qui rongent les fixations : une couverture bretonne encaisse sans rien dire. La regarder tous les deux ans coûte moins cher que de la refaire une fois."),
  "carte": ("Tout le toit", "Ardoise, zinguerie, entretien : un seul artisan."),
  "nav": "couvreur, tous travaux",
  "lp": "couvreur_quimper",
  "title": "Couvreur en Cornouaille | David Demestre",
  "meta": "Couvreur en Cornouaille, installé à Quimper. Ardoise, fuite, démoussage, zinguerie, réfection. Concarneau, Douarnenez, Pont-l'Abbé. Devis gratuit.",
  "og_title": "Couvreur à Quimper : l'artisan qui décroche et qui monte voir",
  "og_desc": "Ardoise cassée, fuite, mousse, faîtage descellé, toiture à refaire. Un seul artisan, devis gratuit.",
  "slogan": "Un couvreur qui décroche, et qui monte voir.",
  "schema_desc": "Couvreur à Quimper : réparation de toiture et recherche de fuite, remplacement d'ardoises, démoussage, zinguerie et réfection de couverture, à Quimper, Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant et dans un rayon de 35 km.",
  "schema_catalog": "Travaux de couverture",
  "offers": [
    "Réparation de toiture et recherche de fuite",
    "Remplacement d'ardoises et reprise de crochets",
    "Démoussage de toiture",
    "Gouttières, noues et zinguerie",
    "Réfection de couverture en ardoise",
    "Bâchage d'urgence après coup de vent",
  ],

  "kicker": "Quimper · Concarneau · Douarnenez · Pont-l'Abbé · 35 km alentour",
  "h1": "Couvreur en Cornouaille, <em>et il monte voir.</em>",
  "hero_sub": "Vous avez l'artisan au téléphone, pas un standard : il passe, il chiffre, et c'est lui qui monte sur le toit.",
  "points": [
    "Un <b>seul interlocuteur</b> du premier appel à la facture",
    "L'<b>ardoise</b> : la couverture d'ici, et celle qu'il travaille",
    "Visite et devis <b>gratuits</b>, chiffrés poste par poste",
    "Réparation, démoussage, zinguerie, réfection : <b>tout le toit</b>",
  ],
  "form_title": "Parler à l'artisan",
  "form_cta": "Être rappelé gratuitement",
  "besoin": [
    "Fuite ou infiltration",
    "Ardoises cassées ou glissées",
    "Mousse et lichens sur le toit",
    "Gouttière, noue ou zinguerie",
    "Toiture à refaire",
    "Je ne sais pas, je veux un avis",
  ],
  "message_ph": "Ce que vous constatez, depuis quand, type de couverture, étage…",
  "hero_img": "hero-couvreur.jpg",
  "hero_alt": "Deux couvreurs reprenant une toiture, liteaux mis à nu sous un ciel couvert",
  "hero_cap": "Photo d'illustration : reprise d'une couverture, support mis à nu.",

  "risk_eyebrow": "Ce qui se joue",
  "risk_title": "Un toit ne se dégrade pas d'un coup, <em>il se dégrade en silence.</em>",
  "risk_lead": "Presque toutes les grosses réfections commencent par trois ardoises que personne n'a fait remplacer. Une visite ne coûte rien ; une couverture neuve coûte le prix d'une voiture.",
  "risks": [
    ("Le crochet lâche avant l'ardoise", "L'ardoise, elle, dure cent ans. Ce qui fatigue, c'est le crochet ou le clou qui la tient. Quand les fixations partent, les ardoises glissent une à une, et le toit s'ouvre par plaques."),
    ("L'eau prend son temps", "Une infiltration entre par un point et ressort trois mètres plus loin, après avoir suivi un chevron. Quand la tache apparaît au plafond, l'eau circule depuis des semaines."),
    ("La volige travaille", "Sous l'ardoise, il y a du bois. Un support humide en permanence se ramollit, ne tient plus les fixations, et la réparation devient une réfection."),
    ("Le vent finit le travail", "Un coup de vent d'ouest ne casse pas un toit sain. Il emporte ce qui était déjà descellé : rives, faîtage, ardoises de bordure."),
  ],
  "risk_cta": "Faire venir un couvreur",
  "risk_img": "ardoise-cassee.jpg",
  "risk_alt": "Toiture en ardoise avec plusieurs ardoises manquantes et glissées",
  "risk_cap": "Photo d'illustration : ardoises manquantes, support exposé.",

  "steps_title": "Regarder, dire, <em>chiffrer.</em>",
  "steps_lead": "Un devis de couverture honnête commence par une montée sur le toit. Tout ce qui se décide depuis le sol est une estimation, et vous la payez deux fois.",
  "steps": [
    ("Vous appelez", "Vous décrivez ce que vous voyez. Si c'est urgent, le passage se cale en priorité."),
    ("Il monte voir", "Contrôle de la couverture, des fixations, du faîtage, des rives, des noues et des solins. Photos à l'appui."),
    ("Un devis écrit", "Détaillé poste par poste, remis sous 48 h, valable un mois. Aucun acompte demandé au devis."),
    ("Le chantier", "C'est lui qui le fait. Vous savez qui monte, quand, et ce qui est repris."),
  ],
  "incl": [
    "Visite et diagnostic du toit, gratuits",
    "Photos avant et après intervention",
    "Remplacement d'ardoises et de fixations",
    "Reprise de faîtage, de rives et de solins",
    "Nettoyage des gouttières au passage",
    "Évacuation des gravats en fin de chantier",
  ],

  "ba_title": "Un toit qui tient, <em>ça se voit d'en bas.</em>",
  "ba_lead": "Une couverture saine se reconnaît à ses lignes : des rangs droits, un faîtage net, pas d'ardoise décalée. Quand la ligne se casse, c'est que la fixation a lâché.",
  "ba_before_img": "ardoise-mousse.jpg",
  "ba_before_alt": "Toiture grise envahie de mousse et de lichens",
  "ba_before_cap": "Fixations fatiguées, mousse installée : le toit boit.",
  "ba_after_img": "toit-ardoise-propre.jpg",
  "ba_after_alt": "Toiture en ardoise nette aux rangs réguliers après intervention",
  "ba_after_cap": "Rangs droits, faîtage net : la couverture reprend son rôle.",

  "prix_title": "Combien coûtent <em>des travaux de couverture ?</em>",
  "prix_lead": "Un toit se chiffre après l'avoir vu. La surface, la pente, l'accès et l'état du support font varier le prix du simple au triple : annoncer un chiffre au téléphone serait de la devinette.",
  "prix_cards": [
    ("Intervention ponctuelle", "Sur devis", "Ardoises remplacées, faîtage rescellé, solin repris, gouttière nettoyée.", True),
    ("Chantier complet", "Sur devis", "Réfection de couverture, zinguerie, reprise du support, évacuation comprise.", False),
  ],
  "prix_factors": [
    "La surface et la pente de la toiture",
    "L'accès et la nécessité d'un échafaudage",
    "L'état du support sous les ardoises",
    "Le type de couverture et le format des ardoises",
    "L'étendue de la zinguerie à reprendre",
    "L'urgence et le bâchage éventuel",
  ],

  "band_img": "bourg-cornouaille.jpg",
  "band_alt": "Maisons de pierre aux toits d'ardoise dans un bourg de Cornouaille",
  "band_title": "En Cornouaille, <em>les toits vieillissent face à l'ouest.</em>",
  "band_text": "Un appel, une visite, une réponse franche. Si votre toit peut attendre, il vous le dira aussi.",

  "faq": [
    ("La visite et le devis sont-ils vraiment gratuits ?", "Oui, tous les deux, et sans engagement. Rien n'est facturé pour venir voir, monter sur le toit et remettre un chiffrage écrit. Aucun acompte n'est demandé au devis."),
    ("Sous combien de temps intervenez-vous ?", "Le rappel se fait sous 48 h ouvrées, souvent le jour même. Pour la visite, cela dépend du planning en cours : une maison ouverte après un coup de vent passe avant un chantier programmé."),
    ("Quelles communes sont desservies ?", "Un rayon d'environ 35 km autour de Quimper : Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant, Bénodet, Le Guilvinec, Rosporden, Briec, Châteaulin, Audierne et les communes entre les deux. Un appel suffit pour savoir."),
    ("Travaillez-vous l'ardoise et la tuile ?", "L'ardoise avant tout : c'est la couverture d'ici, et c'est là que se joue la qualité du travail. La tuile mécanique, le zinc et le bac acier font aussi partie du métier, comme la zinguerie : gouttières, noues, rives et solins."),
    ("Qui vient sur le chantier ?", "L'artisan lui-même. Ce n'est pas un centre d'appel qui prend la demande et sous-traite le chantier : celui qui chiffre est celui qui monte."),
    ("Faut-il être présent pendant les travaux ?", "Pas nécessairement. Il faut un accès à la propriété, et un point d'eau pour un démoussage. Les photos avant et après vous sont remises."),
    ("Comment se passe le paiement ?", "Rien à l'établissement du devis. Pour un chantier important, un acompte à la commande est d'usage pour engager les matériaux : il est écrit sur le devis, jamais réclamé avant."),
    ("Quelle TVA s'applique sur les travaux ?", "Sur un logement achevé depuis plus de deux ans, les travaux de rénovation relèvent en général de la TVA à 10 %. Le taux applicable à votre situation figure sur le devis."),
  ],

  "final_title": "Un appel suffit <em>pour savoir où vous en êtes.</em>",
  "final_lead": "Décrivez ce que vous voyez, il vous dira si ça peut attendre, ce que ça implique, et ce que ça coûte.",
  "footer_desc": "Couvreur à Quimper : réparation de toiture et recherche de fuite, remplacement d'ardoises, démoussage, zinguerie et réfection de couverture, à Quimper, Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant et 35 km alentour.",
  "footer_tags": "Couverture · Ardoise · Démoussage · Zinguerie",
},

# ------------------------------------------------------------ 1. RÉPARATION
# ⚠️ C'est LA page prioritaire : « réparation au niveau de l'ardoise, tu mets ça
# en premier », et « oui, au niveau couverture » pour les urgences. C'est elle
# qui reçoit le budget d'enchères le plus élevé au lancement.
"reparation-fuite-toiture-finistere": {
  "ouv": ("L'eau entre rarement <em>là où la tache apparaît.</em>",
          "Une infiltration suit un chevron, longe une panne et ressort trois mètres plus loin. C'est pour ça qu'un diagnostic au téléphone ne vaut rien, et qu'il faut monter voir."),
  "carte": ("Réparation et fuites", "Recherche de fuite sur place, bâchage d'urgence."),
  "nav": "réparation et fuites",
  "lp": "reparation_quimper",
  "title": "Fuite de toiture en Sud-Finistère · Réparation | David Demestre",
  "meta": "Fuite de toiture, ardoises cassées, dégâts après tempête en Sud-Finistère. Couvreur à Quimper, intervention rapide sur Concarneau et Douarnenez.",
  "og_title": "Fuite de toiture à Quimper : un couvreur qui décroche",
  "og_desc": "Recherche de fuite, remplacement d'ardoises, bâchage d'urgence après tempête. Artisan couvreur installé à Quimper.",
  "slogan": "Une fuite ne s'arrange jamais toute seule.",
  "schema_desc": "Réparation de toiture, recherche de fuite, remplacement d'ardoises cassées et bâchage d'urgence après tempête à Quimper, Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant et dans un rayon de 35 km.",
  "schema_catalog": "Réparation et dépannage de toiture",
  "offers": [
    "Recherche de fuite de toiture",
    "Remplacement d'ardoises cassées ou glissées",
    "Reprise de crochets et de fixations",
    "Rescellement de faîtage et de rives",
    "Reprise de solin de cheminée et de noue zinc",
    "Bâchage d'urgence après coup de vent",
  ],

  "kicker": "Quimper · Concarneau · Douarnenez · Pont-l'Abbé · 35 km alentour",
  "h1": "Réparation de toiture et recherche de fuite <em>en Sud-Finistère.</em>",
  "hero_sub": "On monte, on trouve d'où vient l'eau, on répare, et on vous montre les photos.",
  "points": [
    "Recherche de fuite <b>sur place</b>, pas au téléphone",
    "Ardoises cassées ou glissées <b>remplacées à l'identique</b>",
    "Bâchage d'urgence possible après <b>coup de vent</b>",
    "Artisan de Quimper : <b>déplacement court</b>, pas de sous-traitance",
  ],
  "form_title": "Décrire ma fuite",
  "form_cta": "Être rappelé rapidement",
  "besoin": [
    "Fuite ou infiltration au plafond",
    "Ardoises cassées ou glissées",
    "Dégâts après tempête ou coup de vent",
    "Faîtage ou rive descellé",
    "Solin de cheminée ou noue",
    "Je ne sais pas d'où ça vient",
  ],
  "message_ph": "Depuis quand, à quel endroit, après quelle pluie, étage…",
  "hero_img": "hero-reparation.jpg",
  "hero_alt": "Couvreur portant des éléments de couverture sur un toit, ciel de fin de jour",
  "hero_cap": "Photo d'illustration : intervention sur une couverture ouverte.",

  "risk_eyebrow": "Ce qui se joue",
  "risk_title": "Ce qui coûte cher, <em>ce n'est pas l'ardoise.</em>",
  "risk_lead": "Une ardoise cassée se remplace pour presque rien. Ce qui coûte cher, c'est le mois de pluie qui est passé par le trou avant que vous n'appeliez. Et en Cornouaille, un mois de pluie, c'est vite fait.",
  "risks": [
    ("L'eau voyage avant de tomber", "Une infiltration entre à un endroit et ressort trois mètres plus loin. La tache au plafond n'indique jamais le point d'entrée : il faut monter."),
    ("Le support s'abîme sous l'ardoise", "Volige ou liteau humide en permanence finit par se ramollir et ne plus tenir les crochets. Le remplacement du support n'a plus rien à voir, en prix, avec une réparation de couverture."),
    ("L'isolant est perdu", "Une laine mouillée se tasse et ne remonte pas. Elle se remplace, et il faut ouvrir le plafond pour le faire."),
    ("L'assurance regarde la date", "Après un événement climatique, la déclaration se fait sous cinq jours ouvrés. Passé ce délai, la discussion devient beaucoup plus difficile."),
  ],
  "risk_cta": "Faire venir un couvreur",
  "risk_img": "ardoise-cassee.jpg",
  "risk_alt": "Toiture en ardoise dégradée, ardoises manquantes et support apparent",
  "risk_cap": "Photo d'illustration : couverture ouverte, l'eau entre directement.",

  "steps_title": "Trouver, réparer, <em>prouver.</em>",
  "steps_lead": "Une réparation de toiture bien faite, c'est un point d'entrée identifié et une photo qui le montre. Sinon la fuite revient à la pluie suivante, et il y en a une chaque semaine.",
  "steps": [
    ("Vous appelez", "Vous décrivez ce que vous voyez. Si la situation est urgente, on cale le passage en priorité."),
    ("Recherche sur le toit", "Contrôle de la couverture, des fixations, du faîtage, des rives, des noues et des solins. Photos à l'appui."),
    ("Réparation", "Remplacement des ardoises touchées, reprise des crochets, rescellement, reprise de zinguerie. Bâchage si la réfection doit attendre."),
    ("Vérification", "Contrôle de l'écoulement, photos remises, et conseil honnête sur ce qui tiendra ou pas."),
  ],
  "incl": [
    "Recherche du point d'entrée réel",
    "Photos avant et après réparation",
    "Remplacement des ardoises cassées ou glissées",
    "Reprise des crochets et des fixations",
    "Rescellement du faîtage et des rives",
    "Devis écrit avant toute intervention payante",
  ],

  "ba_title": "L'eau qui entre, <em>l'eau qui s'écoule.</em>",
  "ba_lead": "Une couverture saine ne retient pas l'eau : elle la conduit. Tout l'enjeu d'une réparation est de rendre au toit ce chemin.",
  "ba_before_img": "pluie-toit.jpg",
  "ba_before_alt": "Pluie ruisselant en nappe depuis le bord d'une toiture",
  "ba_before_cap": "L'eau déborde et ruisselle là où elle ne devrait pas passer.",
  "ba_after_img": "pose-ardoise.jpg",
  "ba_after_alt": "Couvreur reprenant le rampant d'une toiture, ciel dégagé",
  "ba_after_cap": "Le point d'entrée trouvé et repris sur place, photos à l'appui.",

  "prix_title": "Combien coûte une réparation <em>de toiture ?</em>",
  "prix_lead": "Une réparation se chiffre après avoir vu d'où vient l'eau. Annoncer un prix au téléphone avant d'être monté serait de la devinette, et vous le paieriez deux fois.",
  "prix_cards": [
    ("Petite réparation", "Sur devis", "Ardoises remplacées, crochets repris, faîtage rescellé, solin refait.", True),
    ("Intervention d'urgence", "Sur devis", "Bâchage après tempête, mise hors d'eau en attendant la réparation définitive.", False),
  ],
  "prix_factors": [
    "L'accès au point de fuite et la pente",
    "La nécessité d'un échafaudage ou d'une nacelle",
    "Le nombre d'ardoises et de fixations à reprendre",
    "Le format des ardoises et leur disponibilité",
    "L'état du support sous la couverture",
    "L'urgence et le bâchage éventuel",
  ],

  "band_img": "tempete-atlantique.jpg",
  "band_alt": "Ciel de tempête atlantique au-dessus de toits d'ardoise",
  "band_title": "Après le coup de vent, <em>c'est le toit qui parle.</em>",
  "band_text": "Ardoises envolées, faîtage descellé, rive arrachée : faites constater vite. La déclaration à l'assurance se fait sous cinq jours ouvrés.",

  "faq": [
    ("Intervenez-vous en urgence ?", "Selon le planning du jour et la gravité. Une maison ouverte après un coup de vent passe avant un chantier programmé. Le mieux est d'appeler directement : vous aurez une réponse franche sur le délai, pas une promesse en l'air."),
    ("Comment trouve-t-on l'origine d'une fuite ?", "En montant. L'eau entre souvent loin de l'endroit où elle tombe : elle suit un chevron, une volige, un écran sous toiture. On contrôle la couverture, le faîtage, les rives, les noues et les solins jusqu'à trouver le point d'entrée réel."),
    ("Mes ardoises glissent une par une, est-ce grave ?", "C'est le signe le plus courant en Bretagne, et il ne vient presque jamais de l'ardoise : ce sont les crochets ou les clous qui ont cédé. Tant que c'est localisé, la reprise est simple. Quand ça se généralise sur un pan entier, il faut regarder le support."),
    ("Une réparation suffit-elle ou faut-il tout refaire ?", "Cela dépend de l'âge et de l'état général. Si la couverture est encore saine et le problème localisé, la réparation est la bonne réponse. Si le toit est en fin de vie, réparer chaque hiver revient plus cher que de refaire une fois. On vous dit ce qu'on voit, même quand cela ne fait pas vendre."),
    ("Mon assurance prend-elle en charge ?", "Après un événement climatique, la garantie tempête de votre contrat multirisque habitation joue en général, avec une franchise. Il faut déclarer sous cinq jours ouvrés. Le devis détaillé et les photos servent au dossier."),
    ("Faites-vous le bâchage en attendant ?", "Oui, quand le toit est ouvert et que la réparation ne peut pas se faire tout de suite. La bâche met la maison hors d'eau et laisse le temps de faire les choses proprement."),
    ("Une visite de contrôle coûte-t-elle quelque chose ?", "Le diagnostic et le devis sont gratuits. Ce qui est facturé, c'est l'intervention, et elle est chiffrée avant d'être faite."),
    ("Nettoyez-vous les gouttières pendant l'intervention ?", "Oui, quand elles sont accessibles. Une descente bouchée est souvent la vraie cause d'une infiltration en pignon."),
  ],

  "final_title": "Dites-nous ce que vous voyez, <em>on vous dit ce que c'est.</em>",
  "final_lead": "Une tache au plafond, une ardoise au sol, un bruit d'eau dans les combles : décrivez, on vous rappelle et on monte voir.",
  "footer_desc": "Réparation de toiture, recherche de fuite, remplacement d'ardoises et bâchage d'urgence à Quimper, Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant et 35 km alentour.",
  "footer_tags": "Réparation de toiture · Recherche de fuite · Bâchage d'urgence",
},

# ------------------------------------------------------------ 2. DÉMOUSSAGE
# Sa seconde demande, mot pour mot : « Démouchage ». Le climat breton en fait
# une demande saisonnière très forte, et c'est le service d'entrée qui amène
# les chantiers de réparation derrière.
"demoussage-toiture-finistere": {
  "ouv": ("Ici, la mousse ne prend pas de vacances. <em>Elle pousse toute l'année.</em>",
          "Douceur de l'air, pluie fine, humidité qui ne redescend jamais vraiment : la Cornouaille est l'un des endroits de France où un toit verdit le plus vite. Et sur l'ardoise, la mousse ne se contente pas de salir."),
  "carte": ("Démoussage", "Nettoyage doux de la couverture, sans haute pression."),
  "nav": "démoussage de toiture",
  "lp": "demoussage_quimper",
  "title": "Démoussage de toiture en Sud-Finistère | David Demestre",
  "meta": "Démoussage de toiture en ardoise en Sud-Finistère : nettoyage doux sans haute pression, gouttières dégagées. Quimper, Concarneau, Douarnenez.",
  "og_title": "Démoussage de toiture à Quimper : le toit respire à nouveau",
  "og_desc": "Nettoyage sans haute pression, traitement, gouttières dégagées, contrôle des fixations au passage.",
  "slogan": "Un toit propre, c'est d'abord un toit qui sèche.",
  "schema_desc": "Démoussage de toiture en ardoise, nettoyage sans haute pression, traitement anti-mousse et nettoyage de gouttières à Quimper, Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant et dans un rayon de 35 km.",
  "schema_catalog": "Démoussage et entretien de toiture",
  "offers": [
    "Démoussage de toiture en ardoise",
    "Nettoyage doux sans haute pression",
    "Traitement anti-mousse rémanent",
    "Nettoyage des gouttières et des descentes",
    "Contrôle des fixations pendant l'intervention",
    "Reprise des ardoises fendues repérées",
  ],

  "kicker": "Quimper · Concarneau · Douarnenez · Pont-l'Abbé · 35 km alentour",
  "h1": "Démoussage de toiture <em>en Sud-Finistère.</em>",
  "hero_sub": "Nettoyage doux, traitement, gouttières dégagées, et un contrôle du toit pendant qu'il est sous les yeux.",
  "points": [
    "<b>Pas de haute pression</b> sur l'ardoise : elle la fend",
    "Gouttières et descentes <b>dégagées au passage</b>",
    "Contrôle des fixations et du faîtage <b>pendant l'intervention</b>",
    "Photos avant et après, <b>devis gratuit</b>",
  ],
  "form_title": "Demander un démoussage",
  "form_cta": "Recevoir mon devis gratuit",
  "besoin": [
    "Toiture verte ou noircie",
    "Mousse épaisse sur les ardoises",
    "Gouttières bouchées",
    "Traitement après nettoyage",
    "Entretien régulier",
    "Je ne sais pas, je veux un avis",
  ],
  "message_ph": "Surface approximative, pente, accès, dernière intervention…",
  "hero_img": "hero-demoussage.jpg",
  "hero_alt": "Toits d'ardoise d'une maison bretonne envahis de lichens jaunes",
  "hero_cap": "Photo d'illustration : ardoise colonisée par les lichens.",

  "risk_eyebrow": "Ce qui se joue",
  "risk_title": "La mousse ne salit pas un toit. <em>Elle le garde mouillé.</em>",
  "risk_lead": "Un tapis de mousse se comporte comme une éponge posée sur la couverture : il retient l'eau au lieu de la laisser filer. Tout ce qui suit vient de là.",
  "risks": [
    ("L'eau stagne au lieu de s'écouler", "Une ardoise est faite pour être mouillée quelques heures, pas en permanence. Sous la mousse, elle ne sèche plus entre deux pluies."),
    ("Le gel travaille dans la mousse", "L'eau retenue gèle, gonfle, et fait levier entre les rangs. C'est comme ça qu'une ardoise saine finit fendue."),
    ("Les racines soulèvent les rangs", "Les lichens s'accrochent, les mousses s'épaississent, et le recouvrement entre ardoises se réduit. L'eau passe par les côtés."),
    ("Les gouttières se remplissent", "La mousse arrachée par la pluie finit dans la descente. Une descente bouchée déborde sur la façade, et c'est le mur qui prend l'eau."),
  ],
  "risk_cta": "Faire nettoyer mon toit",
  "risk_img": "ardoise-mousse.jpg",
  "risk_alt": "Toiture grise colonisée par la mousse et les lichens jaunes",
  "risk_cap": "Photo d'illustration : mousse installée entre les rangs d'ardoises.",

  "steps_title": "Nettoyer sans abîmer, <em>puis traiter.</em>",
  "steps_lead": "Sur de l'ardoise, la méthode compte plus que le matériel. Un nettoyeur haute pression va vite, et il fend les ardoises qu'il rencontre.",
  "steps": [
    ("Vous appelez", "Surface approximative, type de couverture, accès. Une visite fixe le reste."),
    ("Nettoyage doux", "Grattage manuel et basse pression maîtrisée, dans le sens des rangs, sans jamais passer sous l'ardoise."),
    ("Traitement", "Produit anti-mousse rémanent appliqué sur couverture sèche : il finit de tuer les racines et retarde la repousse."),
    ("Gouttières et contrôle", "Descentes dégagées, écoulement vérifié, et signalement des ardoises fendues ou des fixations fatiguées repérées."),
  ],
  "incl": [
    "Nettoyage de toute la surface de couverture",
    "Aucune haute pression sur l'ardoise",
    "Traitement anti-mousse après séchage",
    "Gouttières et descentes dégagées",
    "Ramassage des déchets au sol",
    "Photos avant et après, et signalement des défauts vus",
  ],

  "ba_title": "Le même toit, <em>avant et après.</em>",
  "ba_lead": "Le résultat se voit tout de suite. Ce qui compte, c'est ce qui se passe l'hiver suivant : une couverture qui sèche entre deux pluies ne se dégrade plus.",
  "ba_before_img": "ardoise-lichens.jpg",
  "ba_before_alt": "Gros plan de lichens installés entre les rangs d'un toit",
  "ba_before_cap": "Avant : la mousse retient l'eau, le toit ne sèche plus.",
  "ba_after_img": "toit-ardoise-propre.jpg",
  "ba_after_alt": "Toiture en ardoise nettoyée, rangs nets et réguliers",
  "ba_after_cap": "Après : l'eau file, l'ardoise sèche, les rangs réapparaissent.",

  "prix_title": "Combien coûte <em>un démoussage ?</em>",
  "prix_lead": "Un démoussage se chiffre au mètre carré de toiture, mais deux toits de même surface ne coûtent pas la même chose : la pente, l'accès et l'épaisseur de la mousse changent tout.",
  "prix_cards": [
    ("Démoussage seul", "Sur devis", "Nettoyage de la couverture, gouttières dégagées, déchets ramassés.", True),
    ("Démoussage et traitement", "Sur devis", "Nettoyage, puis traitement anti-mousse rémanent sur couverture sèche.", False),
  ],
  "prix_factors": [
    "La surface développée de la toiture",
    "La pente et la difficulté d'accès",
    "L'épaisseur de la mousse et des lichens",
    "La nécessité d'un échafaudage",
    "Le linéaire de gouttières à dégager",
    "Le traitement, appliqué ou non",
  ],

  "band_img": "maison-bretonne.jpg",
  "band_alt": "Maison bretonne en pierre couverte d'ardoise, ciel gris",
  "band_title": "Un toit breton verdit <em>plus vite qu'ailleurs.</em>",
  "band_text": "Pluie fine, air doux, humidité permanente : ici, un contrôle tous les deux ou trois ans est la bonne fréquence, pas du zèle.",

  "faq": [
    ("À quelle fréquence faut-il démousser ?", "En Cornouaille, tous les deux à trois ans selon l'exposition. Un pan orienté au nord, ou à l'ombre d'arbres, verdit deux fois plus vite qu'un pan plein sud. Le signal, c'est quand le vert recouvre les rangs et que les gouttières se chargent."),
    ("Utilisez-vous un nettoyeur haute pression ?", "Non sur l'ardoise. La haute pression va vite, mais elle fend les ardoises les plus fines et elle pousse l'eau sous les rangs. Le nettoyage se fait au grattage et à basse pression maîtrisée, dans le sens de l'écoulement."),
    ("Faut-il appliquer un hydrofuge sur de l'ardoise ?", "Non. L'hydrofuge a un sens sur une tuile en terre cuite, qui est poreuse. L'ardoise naturelle ne l'est pas : le produit ne pénètre pas et ne sert à rien d'autre qu'à gonfler la facture. Ce qui a un effet, c'est le traitement anti-mousse."),
    ("Le traitement est-il dangereux pour le jardin ?", "Les produits utilisés sont prévus pour la toiture et appliqués sans ruissellement excessif. Les abords sensibles, le potager et le bassin sont protégés ou évités, et l'eau de pluie récupérée ne doit pas être utilisée pendant quelques semaines."),
    ("Combien de temps ça tient ?", "Après nettoyage et traitement, comptez trois à cinq ans avant que la mousse redevienne visible. Sans traitement, la repousse est nettement plus rapide sur un pan ombragé."),
    ("Intervenez-vous à quelle saison ?", "Toute l'année, hors gel et hors grand vent. Le printemps et le début de l'automne sont les meilleures périodes : la couverture sèche assez pour que le traitement tienne."),
    ("Faut-il être présent ?", "Non, un accès à la propriété et un point d'eau suffisent. Les photos avant et après vous sont remises."),
    ("Que se passe-t-il si vous trouvez un défaut ?", "Il vous est signalé, en photo, avec un avis franc : ce qui doit être repris tout de suite, et ce qui peut attendre. Rien n'est fait en plus sans votre accord écrit."),
  ],

  "final_title": "Votre toit a verdi ? <em>Ça se règle avant l'hiver.</em>",
  "final_lead": "Donnez la surface approximative et la commune : vous aurez un ordre d'idée au téléphone, et un devis ferme après la visite.",
  "footer_desc": "Démoussage de toiture en ardoise, nettoyage sans haute pression, traitement anti-mousse et nettoyage de gouttières à Quimper, Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant et 35 km alentour.",
  "footer_tags": "Démoussage · Traitement anti-mousse · Gouttières",
},

# ------------------------------------------------------------ 3. RÉFECTION
# Panier moyen le plus élevé du compte. Peu de volume, mais c'est cette page
# qui rentabilise les autres : un seul chantier signé paie plusieurs mois de
# budget d'annonces.
"renovation-toiture": {
  "ouv": ("Refaire un toit une fois, <em>ou le réparer tous les hivers.</em>",
          "À partir d'un certain âge, une couverture ne se répare plus : elle se tient. Chaque hiver ramène sa fuite, et la somme des dépannages dépasse le prix d'une réfection propre."),
  "carte": ("Réfection de toiture", "Couverture neuve en ardoise, support compris."),
  "nav": "réfection de toiture",
  "lp": "renovation_quimper",
  "title": "Réfection de toiture en ardoise à Quimper | David Demestre",
  "meta": "Réfection de toiture en ardoise à Quimper : dépose, reprise du support, couverture neuve, zinguerie. Concarneau, Douarnenez et 35 km.",
  "og_title": "Refaire sa toiture à Quimper : couverture neuve en ardoise",
  "og_desc": "Dépose, contrôle du support, couverture neuve, zinguerie reprise. Devis détaillé poste par poste.",
  "slogan": "Une couverture refaite une fois, pas réparée dix.",
  "schema_desc": "Réfection et rénovation de toiture en ardoise, dépose de l'ancienne couverture, reprise du support, pose d'ardoises neuves et zinguerie à Quimper, Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant et dans un rayon de 35 km.",
  "schema_catalog": "Réfection de toiture",
  "offers": [
    "Dépose de l'ancienne couverture",
    "Contrôle et reprise du support",
    "Pose d'ardoises neuves au crochet",
    "Écran sous toiture et ventilation",
    "Zinguerie : noues, rives, faîtage, gouttières",
    "Évacuation et recyclage des déchets de chantier",
  ],

  "kicker": "Quimper · Concarneau · Douarnenez · Pont-l'Abbé · 35 km alentour",
  "h1": "Un toit se refait une fois. <em>Autant le faire bien.</em>",
  "hero_sub": "Dépose, contrôle du support, couverture neuve, zinguerie reprise : un devis écrit poste par poste, et l'artisan qui l'a chiffré sur le chantier.",
  "points": [
    "Devis <b>détaillé poste par poste</b>, pas un prix au forfait",
    "Support contrôlé <b>avant de reposer quoi que ce soit</b>",
    "Ardoise, zinguerie et évacuation <b>par le même artisan</b>",
    "Chantier protégé et <b>nettoyé en fin de journée</b>",
  ],
  "form_title": "Faire chiffrer ma toiture",
  "form_cta": "Recevoir mon devis détaillé",
  "besoin": [
    "Toiture en fin de vie",
    "Fuites qui reviennent chaque hiver",
    "Ardoises qui glissent sur un pan entier",
    "Support ou charpente à vérifier",
    "Projet de rénovation complète",
    "Je veux surtout un avis et un chiffrage",
  ],
  "message_ph": "Surface approximative, année de la maison, ce que vous constatez…",
  "hero_img": "hero-renovation.jpg",
  "hero_alt": "Bâtiment ancien sous échafaudage et filets pendant la réfection de sa toiture",
  "hero_cap": "Photo d'illustration : toiture en cours de réfection.",

  "risk_eyebrow": "Ce qui se joue",
  "risk_title": "Le vrai coût, <em>c'est de repousser.</em>",
  "risk_lead": "Repousser une réfection ne fait pas économiser : ça transforme un chantier de couverture en chantier de charpente, d'isolation et de plafonds.",
  "risks": [
    ("Les dépannages s'additionnent", "Trois interventions à quelques centaines d'euros par hiver, pendant cinq ans, coûtent le prix d'un pan refait proprement, et le toit reste vieux."),
    ("Le support finit par céder", "Tant que le support est sain, la réfection reste un chantier de couverture. Quand la volige est morte, le devis change de catégorie."),
    ("L'isolation ne sert plus à rien", "Une laine qui a pris l'eau ne isole plus. On la découvre en déposant, et elle s'ajoute au chantier."),
    ("La vente s'en ressent", "Un toit visiblement en fin de vie se négocie à la baisse, et bien au-delà du coût réel des travaux."),
  ],
  "risk_cta": "Faire chiffrer ma toiture",
  "risk_img": "charpente-nue.jpg",
  "risk_alt": "Support de toiture mis à nu, voliges et chevrons apparents",
  "risk_cap": "Photo d'illustration : support mis à nu après dépose.",

  "steps_title": "Déposer, vérifier, <em>reposer.</em>",
  "steps_lead": "Un chantier de réfection se juge sur ce qui se passe entre la dépose et la pose : c'est là que se décide si le toit tiendra cinquante ans ou dix.",
  "steps": [
    ("Visite et chiffrage", "Montée sur le toit, état de la couverture et du support, mesures. Devis écrit sous 48 h, poste par poste."),
    ("Dépose et protection", "Échafaudage, protection des abords, dépose de l'ancienne couverture, évacuation."),
    ("Support et écran", "Contrôle des voliges et des chevrons, reprise de ce qui est mort, pose de l'écran sous toiture et ventilation."),
    ("Couverture et zinguerie", "Pose des ardoises neuves, faîtage, rives, noues, solins, gouttières. Nettoyage complet en fin de chantier."),
  ],
  "incl": [
    "Échafaudage et protection des abords",
    "Dépose et évacuation de l'ancienne couverture",
    "Contrôle du support et reprise des pièces mortes",
    "Écran sous toiture et ventilation",
    "Ardoises neuves posées au crochet",
    "Zinguerie complète et nettoyage de fin de chantier",
  ],

  "ba_title": "La différence <em>se voit de la rue.</em>",
  "ba_lead": "Une couverture neuve, ce n'est pas seulement un toit propre : c'est une maison qui cesse de perdre de la valeur chaque hiver.",
  "ba_before_img": "ardoise-cassee.jpg",
  "ba_before_alt": "Toiture en ardoise en fin de vie, rangs irréguliers et ardoises manquantes",
  "ba_before_cap": "Avant : rangs décalés, fixations mortes, fuites qui reviennent.",
  "ba_after_img": "toit-ardoise-neuf.jpg",
  "ba_after_alt": "Toiture en ardoise neuve aux rangs parfaitement alignés",
  "ba_after_cap": "Après : couverture neuve, zinguerie reprise, lignes droites.",

  "prix_title": "Combien coûte <em>une réfection de toiture ?</em>",
  "prix_lead": "C'est le poste où un prix inventé fait le plus de dégâts. Une réfection se chiffre après montée sur le toit, mesures prises et support examiné, et le devis détaille chaque poste.",
  "prix_cards": [
    ("Un pan de toiture", "Sur devis", "Dépose, reprise du support, ardoises neuves et zinguerie sur un versant.", True),
    ("Toiture complète", "Sur devis", "Réfection de l'ensemble de la couverture, zinguerie et évacuation comprises.", False),
  ],
  "prix_factors": [
    "La surface développée et la pente",
    "L'état réel du support sous l'ancienne couverture",
    "Le format et la qualité des ardoises retenues",
    "L'échafaudage et l'accès au chantier",
    "L'étendue de la zinguerie à refaire",
    "Le volume de déchets à évacuer",
  ],

  "band_img": "toits-quimper.jpg",
  "band_alt": "Toits d'ardoise de Quimper vus depuis les hauteurs",
  "band_title": "L'ardoise dure cent ans, <em>ce qui la tient beaucoup moins.</em>",
  "band_text": "Une réfection bien faite, c'est un support sain et des fixations neuves. Le reste se voit de la rue ; ça, ça se voit dans trente ans.",

  "faq": [
    ("Faut-il refaire tout le toit ou un seul pan ?", "Souvent un seul pan suffit, en général celui exposé à l'ouest ou au nord, qui vieillit plus vite. La visite le dit. Refaire un seul versant quand l'autre est sain n'est pas un demi-travail : c'est la réponse juste."),
    ("Peut-on réutiliser les anciennes ardoises ?", "Parfois, et c'est même une bonne pratique sur une maison de caractère : les ardoises saines sont triées et reposées, les cassées remplacées. Cela dépend de leur état et de l'épaisseur d'origine ; c'est tranché à la dépose, pas avant."),
    ("Combien de temps dure un chantier ?", "Pour une maison individuelle, comptez d'une à trois semaines selon la surface, l'accès et la météo. Les dates fermes sont données à la signature, pas au devis."),
    ("Que se passe-t-il s'il pleut pendant le chantier ?", "En Cornouaille, un chantier se conduit avec cette hypothèse en permanence. On ne dépose que ce qui peut être remis hors d'eau le jour même, et une bâche de sécurité reste sur place."),
    ("Y a-t-il des aides pour refaire une toiture ?", "Une réfection seule n'est en général pas aidée. Elle peut l'être quand elle s'accompagne d'une isolation des combles ou de la toiture : ce sont les travaux d'économie d'énergie qui ouvrent les dispositifs, pas la couverture. Les conditions changent régulièrement, à vérifier au moment du devis."),
    ("Faut-il une autorisation d'urbanisme ?", "Une déclaration préalable est nécessaire dès que l'aspect extérieur change, et systématiquement en secteur protégé. À Quimper, une partie du centre est concernée ; la mairie tranche en quelques minutes."),
    ("Quelles garanties sur les travaux ?", "Les travaux de couverture relèvent de la garantie décennale. L'attestation d'assurance vous est remise avec le devis, et elle doit mentionner explicitement les travaux de couverture."),
    ("Comment se passe le paiement ?", "Rien au devis. Un acompte à la commande engage les matériaux, puis des situations en cours de chantier, le solde à la réception. Tout est écrit sur le devis avant signature."),
  ],

  "final_title": "Faites chiffrer, <em>vous déciderez ensuite.</em>",
  "final_lead": "Un devis détaillé ne vous engage à rien, et c'est le seul moyen de savoir si votre toit vaut encore la peine d'être réparé.",
  "footer_desc": "Réfection de toiture en ardoise à Quimper : dépose, reprise du support, couverture neuve, zinguerie et évacuation, à Concarneau, Douarnenez, Pont-l'Abbé, Fouesnant et 35 km alentour.",
  "footer_tags": "Réfection de toiture · Ardoise · Zinguerie",
},

}


# ============================================================ PAGES DE VILLE
# « couvreur + ville » est la requête d'achat la plus tapée du métier : celui
# qui l'écrit cherche un artisan à appeler, pas un conseil. Elle a besoin de SA
# page, dont le titre reprend la requête mot pour mot — c'est ce qui manquait à
# ailleurs, et c'est la seule façon d'avoir du volume sans acheter du générique.
#
# Chaque page part du service « couvreur » et n'en change que ce qui parle de
# la commune : titre, H1, accroche, zone, schema. Tout le reste (process,
# avant/après, budget, FAQ, formulaires) est identique — c'est la structure qui
# convertit, on n'y touche pas.
VILLES_PAGES = {
 "couvreur-quimper": {
   "ville": "Quimper", "cp": "29000", "hab": "63 000",
   "lat": "47.9960", "lng": "-4.0975",
   "autour": "Ergué-Gabéric, Pluguffan, Plomelin, Briec et tout le bassin quimpérois",
   "trait": "Entre la vieille ville et les lotissements des coteaux, Quimper "
            "mélange l'ardoise ancienne à forte pente et la couverture des "
            "années 70 qui arrive en fin de vie.",
 },
 "couvreur-concarneau": {
   "ville": "Concarneau", "cp": "29900", "hab": "18 500",
   "lat": "47.8736", "lng": "-3.9187",
   "autour": "Trégunc, Rosporden, Melgven, Névez et l'arrière-pays concarnois",
   "trait": "À Concarneau, l'air marin ronge les fixations plus vite qu'ailleurs : "
            "sur le front de mer, ce sont les crochets qui lâchent avant l'ardoise.",
 },
 "couvreur-douarnenez": {
   "ville": "Douarnenez", "cp": "29100", "hab": "13 500",
   "lat": "48.0920", "lng": "-4.3290",
   "autour": "Poullan-sur-Mer, Pouldergat, Le Juch, Ploaré et toute la baie",
   "trait": "La baie de Douarnenez prend le vent d'ouest de plein fouet. "
            "Après un coup de vent, ce sont les rives et les faîtages qui "
            "partent en premier.",
 },
 "couvreur-pont-labbe": {
   "ville": "Pont-l'Abbé", "cp": "29120", "hab": "8 000",
   "lat": "47.8667", "lng": "-4.2222",
   "autour": "Combrit, Plomeur, Loctudy, Plobannalec-Lesconil et le pays bigouden",
   "trait": "Le pays bigouden est le pays de l'ardoise : maisons basses, forte "
            "pente, et des toitures qui encaissent l'humidité toute l'année.",
 },
}


def page_ville(slug, v):
    """Décline le service « couvreur » pour une commune."""
    import copy
    s = copy.deepcopy(SERVICES["couvreur-cornouaille"])
    # Le panorama du bâti appartient à la page régionale. Sur une page de
    # commune, il dilue : le visiteur cherche Concarneau, pas la Cornouaille.
    # Chaque page de ville a déjà son trait local dans son chapeau.
    s["territoire"] = False
    ville, cp = v["ville"], v["cp"]
    s["nav"] = "couvreur à " + ville
    s["lp"] = "couvreur_" + slug.split("-", 1)[1].replace("-", "_")
    s["carte"] = ("Couvreur à " + ville, "Ardoise, fuite, démoussage : un seul artisan.")
    s["title"] = "Couvreur à %s : devis gratuit | David Demestre" % ville
    s["meta"] = ("Couvreur à %s (%s) : ardoise, fuite de toiture, démoussage, "
                 "zinguerie, réfection. Visite et devis gratuits, sans acompte."
                 % (ville, cp))
    s["og_title"] = "Couvreur à %s : l'artisan qui décroche" % ville
    s["og_desc"] = ("Ardoise cassée, fuite, mousse, faîtage descellé, toiture à "
                    "refaire. Un seul artisan, devis gratuit.")
    s["slogan"] = "Un couvreur à %s qui décroche, et qui monte voir." % ville
    s["schema_desc"] = ("Couvreur à %s : réparation de toiture et recherche de "
                        "fuite, remplacement d'ardoises, démoussage, zinguerie et "
                        "réfection de couverture, à %s et alentour."
                        % (ville, ville))
    s["kicker"] = "%s · %s · devis gratuit" % (ville, v["autour"].split(",")[0])
    s["h1"] = "Couvreur à %s, <em>et il monte voir.</em>" % ville
    s["hero_sub"] = ("Vous avez l'artisan au téléphone, pas un standard : il passe "
                     "à %s, il chiffre, et c'est lui qui monte sur le toit." % ville)
    s["ouv"] = ("À %s, un toit travaille <em>toute l'année.</em>" % ville, v["trait"])
    s["form_title"] = "Parler à l'artisan"
    s["final_title"] = "Un appel suffit <em>pour savoir où vous en êtes.</em>"
    s["final_lead"] = ("Décrivez ce que vous voyez : il vous dira si ça peut "
                       "attendre, ce que ça implique, et ce que ça coûte.")
    s["footer_desc"] = ("Couvreur à %s (%s) : réparation de toiture et recherche "
                        "de fuite, remplacement d'ardoises, démoussage, zinguerie "
                        "et réfection, à %s et alentour." % (ville, cp, v["autour"]))
    s["footer_tags"] = "Couverture · Ardoise · Démoussage · %s" % ville
    return s



# ============================================================ TERRITOIRE
# La section qui prouve qu'on connaît la zone : un lecteur d'annuaire ne sait
# pas que les crochets rouillent plus vite à Concarneau.
# Elle ne sort que sur la page métier, la seule qui couvre tout le secteur.
TERRITOIRE = {
 "titre": "Le bâti change <em>tous les vingt kilomètres.</em>",
 "lead": "De la vieille ville de Quimper au Cap Sizun, on ne pose pas la même "
         "ardoise, et on ne répare pas les mêmes défauts. Un couvreur qui "
         "travaille ces quatre secteurs ne commande pas les mêmes fournitures.",
 "secteurs": [
  ("Quimper et le bassin quimpérois",
   "Ardoise ancienne à forte pente en vieille ville, souvent sur voliges. "
   "En périphérie, le pavillonnaire des années 70 arrive en fin de vie : "
   "ce sont les crochets qui lâchent, rarement l'ardoise."),
  ("Le pays bigouden : Pont-l'Abbé, Plomeur, Loctudy",
   "Maisons basses, pentes franches, et un vent qui ne tombe jamais vraiment. "
   "Les rives et les faîtages travaillent plus qu'ailleurs."),
  ("Le littoral : Concarneau, Fouesnant, Bénodet",
   "L'air marin ronge les fixations avant la couverture. Sur le front de mer, "
   "un crochet acier tient deux fois moins longtemps qu'à dix kilomètres "
   "dans les terres."),
  ("La baie de Douarnenez et le Cap Sizun",
   "Le vent d'ouest arrive sans rien pour le freiner. Après un coup de vent, "
   "ce sont toujours les mêmes points qui partent : rives, faîtage, "
   "ardoises de bordure."),
  ("L'intérieur : Briec, Châteaulin, Rosporden",
   "Plus abrité, mais du bâti agricole et des longères à grande surface de "
   "toiture, où une reprise partielle a souvent plus de sens qu'une réfection."),
 ],
}

# « Ce que nous faisons, et ce que nous ne faisons pas ». Dire ce qu'on NE fait
# PAS vaut plus que lister ce qu'on fait : c'est ce qui fait la différence entre
# un artisan et un intermédiaire qui sous-traite en silence.
CADRAGE = {
 "titre": "Ce qu'il fait, et ce qu'il ne fait pas",
 "fait": "Réparation de fuite et recherche du point d'entrée réel, remplacement "
         "d'ardoises et reprise de crochets, faîtage, rives et solins, "
         "gouttières et zinguerie, démoussage, et réfection complète de "
         "couverture. Il monte sur le toit avant de chiffrer, toujours : un "
         "devis fait depuis le sol ou sur photo ne tient pas devant l'état réel "
         "d'une couverture.",
 "non": "le désamiantage, qui est un métier à part avec sa propre "
        "certification — mieux vaut le dire que le sous-traiter en silence. "
        "Et le traitement hydrofuge sur ardoise naturelle : la pierre n'étant "
        "pas poreuse, le produit ne pénètre pas. On vous le vendra ailleurs, "
        "pas ici.",
}

# ============================================================ RENDU

def esc(text):
    """Échappe pour un attribut ou du JSON en gardant les balises <b>/<em> voulues."""
    return text.replace('"', "&quot;")


def json_txt(text):
    """Texte destiné au JSON-LD : pas de balises, pas de guillemets doubles."""
    out = re.sub(r"<[^>]+>", "", text)
    return out.replace('"', "'").replace("\n", " ")


# Photo de la section « zone d'intervention ». Choisies pour ne jamais répéter
# une image déjà présente sur la même page (le build le vérifie).
ZONE_IMG = {
    "couvreur-cornouaille": ("toits-quimper.jpg",      "Toits d'ardoise de Quimper vus depuis les hauteurs",
                           "Quimper, Concarneau, Douarnenez : 35 km autour de la ville."),
    "reparation-fuite-toiture-finistere": ("maison-bretonne.jpg",     "Maison bretonne en pierre couverte d'ardoise",
                           "Un déplacement court, c'est une intervention qui se cale vite."),
    "demoussage-toiture-finistere": ("bourg-cornouaille.jpg",   "Maisons aux toits d'ardoise dans un bourg de Cornouaille",
                           "Cornouaille : air doux, pluie fine, pans nord qui ne sèchent jamais."),
    "renovation-toiture": ("maison-bretonne.jpg",     "Maison bretonne en pierre couverte d'ardoise",
                           "Du pays bigouden à Concarneau, 35 km autour de Quimper."),
    # Pages de ville : la photo de zone alterne pour ne pas donner quatre pages
    # jumelles à qui en ouvrirait deux.
    "couvreur-quimper":    ("toits-quimper.jpg",       "Toits d'ardoise vus depuis les hauteurs",
                            "Quimper et tout le bassin quimpérois."),
    "couvreur-concarneau": ("maison-bretonne.jpg",     "Maison bretonne en pierre couverte d'ardoise",
                            "Concarneau, Trégunc, Rosporden et l'arrière-pays."),
    # La baie prend le vent d'ouest de plein fouet : la photo le dit.
    "couvreur-douarnenez": ("tempete-atlantique.jpg",  "Ciel de tempête au-dessus de toits d'ardoise",
                            "Douarnenez, Ploaré et toute la baie."),
    "couvreur-pont-labbe": ("toit-ardoise-neuf.jpg",   "Toiture en ardoise aux rangs réguliers",
                            "Pont-l'Abbé, Loctudy, Plomeur et le pays bigouden."),
}

CHECK_SVG = ('<svg viewBox="0 0 24 24" fill="none" aria-hidden="true">'
             '<path d="m5 12.5 4.5 4.5L19 7.5" stroke="currentColor" stroke-width="2.2" '
             'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def kicker_split(texte):
    """La pastille du hero liste les communes. Sur un téléphone de 375 px elle
    prend trois lignes et repousse le titre sous la ligne de flottaison : on
    garde les trois premières communes et on replie le reste."""
    bouts = [b.strip() for b in texte.split("\u00b7")]
    tete = " \u00b7 ".join(bouts[:3])
    if len(bouts) <= 3:
        return tete
    return tete + '<span class="pin-suite"> \u00b7 %s</span>' % " \u00b7 ".join(bouts[3:])


def build_proofs(items):
    """Bandeau de preuves sous le hero. Quatre faits, aucun inventé : tant que
    l'entreprise n'a pas de fiche Google, aucune note n'y figure."""
    return "\n    ".join("<div><b>%s</b><span>%s</span></div>" % (n, l)
                         for n, l in items)


def build_points(items):
    """Les quatre arguments du service, dans le hero, en liste à coches :
    c'est la forme retenue sur les pages de service de l'agence."""
    return "\n        ".join(
        "<li>%s<span>%s</span></li>" % (CHECK_SVG, t) for t in items)


def build_risks(items):
    out = []
    for i, (title, text) in enumerate(items, 1):
        out.append('<div class="risk"><span class="n">%02d</span><div><h3>%s</h3>'
                   '<p>%s</p></div></div>' % (i, title, text))
    return "\n        ".join(out)


def build_steps(items):
    out = []
    for i, (title, text) in enumerate(items, 1):
        # 01 plutôt que 1 : en serif italique, le chiffre à deux positions
        # tient la colonne, le chiffre seul flotte.
        out.append('<div class="step"><div class="n">%02d</div><h3>%s</h3><p>%s</p></div>'
                   % (i, title, text))
    return "\n      ".join(out)


def build_list(items, cls=None):
    tag = '<li>%s</li>' if not cls else '<li class="%s">%%s</li>' % cls
    return "\n        ".join(tag % i for i in items)


def build_price_cards(cards):
    out = []
    for label, value, text, featured in cards:
        # La mention accompagne le prix, pas l'intitulé : accrochée au libellé
        # elle passait à la ligne dès que celui-ci était long, et décalait la
        # carte d'à côté.
        pill = '<span class="pc-pill">le plus demandé</span>' if featured else ""
        out.append('<div class="price-card%s"><span class="pc-lab">%s</span>'
                   '<span class="pc-line"><span class="pc-val">%s</span>%s</span>'
                   '<p>%s</p></div>'
                   % (" featured" if featured else "", label, value, pill, text))
    return "\n        ".join(out)


def build_faq(items):
    out = []
    for q, a in items:
        first = ' open' if not out else ''
        out.append('<details%s><summary>%s<span class="pm"></span></summary>'
                   '<div class="ans">%s</div></details>' % (first, q, a))
    return "\n      ".join(out)


def build_schema_faq(items):
    return ",".join(
        '{"@type":"Question","name":"%s","acceptedAnswer":{"@type":"Answer","text":"%s"}}'
        % (json_txt(q), json_txt(a)) for q, a in items)


def build_offers(items):
    return ",".join(
        '{"@type":"Offer","itemOffered":{"@type":"Service","name":"%s"}}' % json_txt(o)
        for o in items)


def build_options(items):
    return "\n                ".join("<option>%s</option>" % o for o in items)


def build_zone(cities, main):
    """Pastilles de communes : les quatre principales pleines, les autres en
    contour. Une liste séparée par des points faisait un mur de texte."""
    out = []
    for c in cities:
        cls = "zone zone-main" if c in main else "zone"
        out.append('<span class="%s">%s</span>' % (cls, c))
    return "\n        ".join(out)


def build_schema_area(cities):
    return "[" + ",".join('{"@type":"City","name":"%s"}' % c for c in cities[:16]) + "]"


def build_avis():
    """Section avis : remplie si AVIS contient de vrais avis, masquée sinon."""
    if not AVIS:
        # Aucun avis collé : on n'affiche RIEN plutôt que des cartes à trous.
        # La note Google, elle, reste visible : elle est réelle et vérifiable.
        return " hidden", ""
    cards = []
    for texte, prenom, commune in AVIS:
        cards.append('<figure class="review"><div class="stars" aria-label="5 étoiles sur 5">'
                     '★★★★★</div><blockquote>%s</blockquote>'
                     '<figcaption>%s · %s</figcaption></figure>'
                     % (html.escape(texte), html.escape(prenom), html.escape(commune)))
    return "", "\n      ".join(cards)


def url_de(slug):
    """Chaque page d'atterrissage a son URL. La racine du domaine est
    volontairement laissée libre : elle ne porte qu'un sommaire, pour que
    le domaine reste disponible le jour où un vrai site s'y installera."""
    return "/%s/" % slug



def bento(current):  # noqa: D401
    """Grille photo des autres prestations : elle montre le métier au lieu de
    le décrire, et elle relie les landings entre elles."""
    out = []
    i = 0
    for slug, s in SERVICES.items():
        if slug == current or "carte" not in s:
            continue
        i += 1
        titre, phrase = s["carte"]
        out.append(
            '<a class="svc%s" href="%s">'
            '<img src="/assets/img/%s" alt="" loading="lazy" width="1600" height="900" />'
            '<span class="svc-in"><span class="svc-n">%02d</span>'
            '<span class="svc-t">%s</span><span class="svc-p">%s</span></span>'
            '<span class="svc-go" aria-hidden="true">\u2197</span></a>'
            % ("", "#devis", s["hero_img"], i, titre, phrase))
    return "\n      ".join(out)


def footer_links(current):
    links = []
    for slug, s in SERVICES.items():
        if slug == current:
            continue
        links.append('<a href="%s">%s</a>' % (url_de(slug), s["nav"]))
    return " · ".join(links)


AVIS_HIDDEN, AVIS_CARDS = build_avis()

# Le sommaire doit servir exactement les mêmes versions d'actifs que les
# landings, sinon il garde une feuille de style périmée.
_TPL = (ROOT / "templates" / "page.html").read_text(encoding="utf-8")
CSS_V = re.search(r"styles\.css\?v=(\d+)", _TPL).group(1)
JS_V = re.search(r"script\.js\?v=(\d+)", _TPL).group(1)

# ---------------------------------------------------------------- formulaire
# Généré ici plutôt que dupliqué dans le gabarit : deux formulaires qui
# divergent, ça ne se voit pas et ça fait perdre des demandes.
FORMULAIRE_HAUT = """<form class="js-devis" id="devis-form" novalidate>
          <input type="hidden" name="access_key" value="{{WEB3FORMS_KEY}}" />
          <input type="checkbox" name="botcheck" tabindex="-1" autocomplete="off" style="display:none" aria-hidden="true" />
          <!-- Traçabilité Google Ads : rempli automatiquement par script.js -->
          <input type="hidden" name="gclid" /><input type="hidden" name="source" /><input type="hidden" name="campagne" /><input type="hidden" name="mot_cle" /><input type="hidden" name="page" />

          <div class="field"><label for="nom">Votre nom <span class="req">*</span></label><input id="nom" name="nom" type="text" required autocomplete="name" placeholder="Nom et prénom" /></div>
          <div class="field"><label for="tel">Téléphone <span class="req">*</span></label><input id="tel" name="tel" type="tel" required autocomplete="tel" inputmode="tel" placeholder="06 12 34 56 78" /></div>
          <div class="field"><label for="ville">Commune <span class="req">*</span></label><input id="ville" name="ville" type="text" required autocomplete="address-level2" placeholder="{{VILLE_PH}}" /></div>
          <div class="field">
            <label for="besoin">Votre besoin</label>
            <div class="select-wrap">
              <select id="besoin" name="besoin">
                {{BESOIN_OPTIONS}}
              </select>
            </div>
          </div>
          <div class="field field-opt">
            <label for="message">Précisions <span class="opt">(facultatif)</span></label>
            <textarea id="message" name="message" rows="2" placeholder="{{MESSAGE_PLACEHOLDER}}"></textarea>
          </div>

          <label class="consent"><input type="checkbox" required /> <span>J'accepte d'être rappelé au sujet de ma demande.</span></label>

          <button type="submit" class="btn btn-accent btn-lg btn-block">{{FORM_CTA}}</button>
          <p class="form-note">Gratuit · Sans engagement · Aucune donnée revendue</p>

          <div class="form-success" role="status">
            <b>Demande bien reçue.</b><br>{{RAPPEL_LINE}}<br>
            <a href="tel:{{PHONE_TEL}}" class="js-tel">Plus pressé ? {{PHONE_DISPLAY}}</a>
          </div>
          <div class="form-error" role="alert">L'envoi a échoué. Appelez directement le <a href="tel:{{PHONE_TEL}}" class="js-tel">{{PHONE_DISPLAY}}</a>.</div>
        </form>"""


GLOBAL = {
    "PHONE_DISPLAY": PHONE_DISPLAY,
    "PHONE_TEL": PHONE_TEL,
    "URL_BASE": URL_BASE,
    "WEB3FORMS_KEY": WEB3FORMS_KEY,
    "ADS_GTAG": ADS_GTAG,
    "ADS_CONV_DEVIS": ADS_CONV_DEVIS,
    "ADS_CONV_APPEL": ADS_CONV_APPEL,
    "ZONE_LIST": build_zone(CITIES, CITY_MAIN),
    "SCHEMA_AREA": build_schema_area(CITIES),
    "AVIS_HIDDEN": AVIS_HIDDEN,
    "AVIS_CARDS": AVIS_CARDS,
    "FORMULAIRE_HAUT": FORMULAIRE_HAUT,

    # Identité de l'entreprise : une seule source, en tête de ce fichier.
    "BRAND": BRAND,
    "BRAND_SHORT": BRAND_SHORT,
    "BRAND_ALT": BRAND_ALT,
    "BRAND_TAG": BRAND_TAG,
    "ADRESSE": ADRESSE,
    "FOUNDING": FOUNDING,
    "MENTIONS": mentions(),
    "GEO_REGION": GEO_REGION,
    "GEO_PLACENAME": GEO_PLACENAME,
    "SCHEMA_ADDRESS": SCHEMA_ADDRESS,
    "SCHEMA_GEO": SCHEMA_GEO,
    "FOOTER_GEO": FOOTER_GEO,
    "VILLE_PH": VILLE_PH,
    "RAPPEL_LINE": RAPPEL_LINE,
    "CRUMB_ROOT": CRUMB_ROOT,
    "FORM_HEAD_P": FORM_HEAD_P,
    "ZONE_H2": ZONE_H2,
    "ZONE_LEAD": ZONE_LEAD,
    "PROOFS": build_proofs(PROOFS),
}


def bloc_territoire(s):
    """Section territoire : rendue seulement si le service la réclame."""
    if not s.get("territoire"):
        return {"TERRITOIRE_HIDDEN": " hidden", "TERRITOIRE_TITRE": "",
                "TERRITOIRE_LEAD": "", "TERRITOIRE_ITEMS": "",
                "CADRAGE_TITRE": "", "CADRAGE_FAIT": "", "CADRAGE_NON": ""}
    items = "\n        ".join(
        '<div class="secteur"><b>%s</b> — %s</div>' % (nom, txt)
        for nom, txt in TERRITOIRE["secteurs"])
    return {"TERRITOIRE_HIDDEN": "", "TERRITOIRE_TITRE": TERRITOIRE["titre"],
            "TERRITOIRE_LEAD": TERRITOIRE["lead"], "TERRITOIRE_ITEMS": items,
            "CADRAGE_TITRE": CADRAGE["titre"], "CADRAGE_FAIT": CADRAGE["fait"],
            "CADRAGE_NON": CADRAGE["non"]}


def tokens_for(slug, s):
    t = dict(GLOBAL)
    t.update({
        "CANONICAL": URL_BASE + url_de(slug),
        "LP_ID": s["lp"],
        "TITLE": s["title"],
        "META_DESC": esc(s["meta"]),
        "OG_TITLE": esc(s["og_title"]),
        "OG_DESC": esc(s["og_desc"]),
        "SCHEMA_SLOGAN": json_txt(s["slogan"]),
        "SCHEMA_DESC": json_txt(s["schema_desc"]),
        "SCHEMA_SERVICE_NAME": json_txt(s["schema_catalog"]),
        "SCHEMA_OFFERS": build_offers(s["offers"]),
        "SCHEMA_FAQ": build_schema_faq(s["faq"]),

        "HERO_KICKER": kicker_split(s["kicker"]),
        "H1": s["h1"],
        "HERO_SUB": s["hero_sub"],
        "HERO_POINTS": build_points(s["points"]),
        "HERO_IMG": s["hero_img"],
        "HERO_IMG_MOB": s["hero_img"].replace(".jpg", "-mob.jpg"),
        "HERO_IMG_ALT": esc(s["hero_alt"]),
        # La légende tient dans une pastille posée sur une bande de 157 px
        # sur téléphone : seul « Photo d'illustration » y reste, le détail
        # est masqué sous 860 px (VB n'affiche que ces deux mots).
        "HERO_IMG_CAPTION": (
            '%s<span class="cap-suite"> : %s</span>'
            % tuple(s["hero_cap"].rstrip(".").split(" : ", 1))
            if " : " in s["hero_cap"] else s["hero_cap"]),
        "ZONE_IMG": ZONE_IMG[slug][0],
        "ZONE_ALT": esc(ZONE_IMG[slug][1]),
        "ZONE_CAP": ZONE_IMG[slug][2],
        "FORM_TITLE": s["form_title"],
        "FORM_CTA": s["form_cta"],
        "BESOIN_OPTIONS": build_options(s["besoin"]),
        "MESSAGE_PLACEHOLDER": esc(s["message_ph"]),

        "RISK_EYEBROW": s["risk_eyebrow"],
        "RISK_TITLE": s["risk_title"],
        "RISK_LEAD": s["risk_lead"],
        "RISK_ITEMS": build_risks(s["risks"]),
        "RISK_CTA": s["risk_cta"],
        "RISK_IMG": s["risk_img"],
        "RISK_IMG_ALT": esc(s["risk_alt"]),
        "RISK_IMG_CAPTION": s["risk_cap"],

        "STEPS_TITLE": s["steps_title"],
        "STEPS_LEAD": s["steps_lead"],
        "STEPS": build_steps(s["steps"]),
        "INCL_LIST": build_list(s["incl"]),

        "BA_TITLE": s["ba_title"],
        "BA_LEAD": s["ba_lead"],
        "BA_BEFORE_IMG": s["ba_before_img"],
        "BA_BEFORE_ALT": esc(s["ba_before_alt"]),
        "BA_BEFORE_CAP": s["ba_before_cap"],
        "BA_AFTER_IMG": s["ba_after_img"],
        "BA_AFTER_ALT": esc(s["ba_after_alt"]),
        "BA_AFTER_CAP": s["ba_after_cap"],

        "PRIX_TITLE": s["prix_title"],
        "PRIX_LEAD": s["prix_lead"],
        "PRIX_CARDS": build_price_cards(s["prix_cards"]),
        "PRIX_FACTORS": build_list(s["prix_factors"]),

        "BAND_IMG": s["band_img"],
        "BAND_ALT": esc(s["band_alt"]),
        "BAND_TITLE": s["band_title"],
        "BAND_TEXT": s["band_text"],

        "FAQ_ITEMS": build_faq(s["faq"]),

        "FINAL_TITLE": s["final_title"],
        "FINAL_LEAD": s["final_lead"],
        "FOOTER_DESC": s["footer_desc"],
        "CRUMB": s["carte"][0] if "carte" in s else s["nav"],
        "OUV_TITRE": s["ouv"][0],
        "OUV_TEXTE": s["ouv"][1],
        "OUV_SPECIMEN": " · ".join(s["offers"][:3]),
        "BENTO": bento(slug),
        "BENTO_TITRE": ("Tout ce qui se passe sur un toit."
                        if s.get("generique") else "Il fait aussi le reste du toit."),
        "BENTO_LEAD": ("Ardoise, zinguerie, entretien, réfection : le même artisan "
                       "du diagnostic à la facture."
                       if s.get("generique") else
                       "Un seul interlocuteur pour tout ce qui touche à la toiture, "
                       "et un seul devis."),
        "FOOTER_SERVICES": ("Couverture en ardoise, réparation et recherche de fuite, "
                            "démoussage, zinguerie, réfection de toiture."),
        "FOOTER_TAGS": s["footer_tags"],
        **bloc_territoire(s),
    })
    return t


def french_spacing(html_text):
    """Espace insécable avant ? ! : ; et autour des guillemets, hors <script>.

    Sans ça, un « ? » se retrouve seul sur sa ligne quand le titre passe à la
    ligne. Les blocs <script> (JSON-LD) sont laissés intacts : une entité HTML
    y serait affichée telle quelle par Google.
    """
    parts = re.split(r"(<script.*?</script>)", html_text, flags=re.S)
    for i, part in enumerate(parts):
        if part.startswith("<script"):
            continue
        for sign in ("?", "!", ";", ":"):
            part = part.replace(" " + sign, "&nbsp;" + sign)
        part = part.replace("« ", "«&nbsp;").replace(" »", "&nbsp;»")
        # Apostrophe typographique entre deux lettres seulement : les
        # apostrophes de code (attributs, JS) ne sont jamais dans ce cas.
        part = re.sub(r"(\w)'(\w)", "\\1\u2019\\2", part)
        parts[i] = part
    return "".join(parts)


def render(template_text, slug, s):
    out = template_text
    jetons = tokens_for(slug, s)
    # Deux passes : le formulaire injecté contient lui-même des jetons
    # ({{FORM_CTA}}, {{PHONE_TEL}}…) qui doivent être résolus après lui.
    for _ in range(2):
        for k, v in jetons.items():
            out = out.replace("{{%s}}" % k, v)
    out = french_spacing(out)
    leftover = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", out)))
    if leftover:
        sys.exit("Jetons non résolus dans %s : %s" % (slug, ", ".join(leftover)))
    return out


ARROW_SVG = ('<svg class="go" viewBox="0 0 24 24" fill="none" aria-hidden="true">'
             '<path d="M9 6l6 6-6 6" stroke="currentColor" stroke-width="1.7" '
             'stroke-linecap="round" stroke-linejoin="round"/></svg>')


def render_accueil():
    """Sommaire de la racine. Ce n'est PAS un site : la racine reste libre
    pour le jour où un vrai site s'y installera. Elle oriente, c'est tout,
    et elle est en noindex comme les pages d'atterrissage."""
    tpl = (ROOT / "templates" / "accueil.html").read_text(encoding="utf-8")
    lignes = []
    for slug, s in SERVICES.items():
        titre, phrase = s["carte"]
        lignes.append(
            '<li><a href="%s"><span><b>%s</b><span>%s</span></span>%s</a></li>'
            % (url_de(slug), titre, phrase, ARROW_SVG))
    jetons = {
        "TITLE": BRAND + " · Quimper (29)",
        "MENU": "\n      ".join(lignes),
        "PHONE_TEL": PHONE_TEL,
        "PHONE_DISPLAY": PHONE_DISPLAY,
        "CSS_V": CSS_V,
        "JS_V": JS_V,
        "BRAND": BRAND,
        "BRAND_SHORT": BRAND_SHORT,
        "BRAND_TAG": BRAND_TAG,
        "ADRESSE": ADRESSE,
        "FOOTER_GEO": FOOTER_GEO,
        "MENTIONS": mentions(),
        "ACCUEIL_H1": ACCUEIL_H1,
        "ACCUEIL_LEAD": ACCUEIL_LEAD,
    }
    out = tpl
    for k, v in jetons.items():
        out = out.replace("{{%s}}" % k, v)
    out = french_spacing(out)
    leftover = sorted(set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", out)))
    if leftover:
        sys.exit("Jetons non résolus dans le sommaire : %s" % ", ".join(leftover))
    return out


def check_longueurs(slug, s):
    """Google tronque le titre vers 60 caractères et la méta vers 160. Un
    garde-fou au build vaut mieux qu'une relecture à l'œil."""
    if len(s["title"]) > 65:
        sys.exit("Titre trop long (%d car.) sur %s : %s" % (len(s["title"]), slug, s["title"]))
    if not 70 <= len(s["meta"]) <= 160:
        sys.exit("Méta de %d car. sur %s (viser 70-160) : %s" % (len(s["meta"]), slug, s["meta"]))


def check_images(slug, s):
    """Garde-fou : une image manquante casse la page sans prévenir en production."""
    missing = []
    for key in ("hero_img", "risk_img", "ba_before_img", "ba_after_img", "band_img"):
        if not (ROOT / "assets" / "img" / s[key]).exists():
            missing.append(s[key])
    # Le hero est l'élément LCP : sa version mobile n'est pas optionnelle.
    mob = s["hero_img"].replace(".jpg", "-mob.jpg")
    if not (ROOT / "assets" / "img" / mob).exists():
        missing.append(mob)
    if not (ROOT / "assets" / "img" / ZONE_IMG[slug][0]).exists():
        missing.append(ZONE_IMG[slug][0])
    # Deux fois la même photo sur une page se remarque tout de suite.
    used = [s["hero_img"], s["ba_before_img"], s["ba_after_img"],
            s["band_img"], ZONE_IMG[slug][0]]
    doublons = {i for i in used if used.count(i) > 1}
    if doublons:
        sys.exit("Image répétée sur %s : %s" % (slug, ", ".join(sorted(doublons))))
    if missing:
        sys.exit("Images manquantes pour %s : %s" % (slug, ", ".join(missing)))


def main():
    tpl = (ROOT / "templates" / "page.html").read_text(encoding="utf-8")
    for slug, s in SERVICES.items():
        check_longueurs(slug, s)
        check_images(slug, s)
        dest = ROOT / slug / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(render(tpl, slug, s), encoding="utf-8")
        print("  %s" % dest.relative_to(ROOT))
    for slug, v in VILLES_PAGES.items():
        s = page_ville(slug, v)
        check_longueurs(slug, s)
        check_images(slug, s)
        dest = ROOT / slug / "index.html"
        dest.parent.mkdir(parents=True, exist_ok=True)
        html_ville = render(tpl, slug, s)
        # La commune remplace Quimper partout où le gabarit parle de géographie.
        html_ville = (html_ville
            .replace('"addressLocality":"Quimper","postalCode":"29000"',
                     '"addressLocality":"%s","postalCode":"%s"' % (v["ville"], v["cp"]))
            .replace('"latitude":47.9960,"longitude":-4.0975',
                     '"latitude":%s,"longitude":%s' % (v["lat"], v["lng"]))
            .replace('content="Quimper" />', 'content="%s" />' % v["ville"]))
        dest.write_text(html_ville, encoding="utf-8")
        print("  %s" % dest.relative_to(ROOT))
    (ROOT / "index.html").write_text(render_accueil(), encoding="utf-8")
    print("  index.html  (sommaire, noindex)")
    print("%d pages de service + %d pages de ville + le sommaire."
          % (len(SERVICES), len(VILLES_PAGES)))


if __name__ == "__main__":
    main()
