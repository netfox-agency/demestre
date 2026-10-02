# David Demestre · Couvreur à Quimper — landings Google Ads

Huit pages d'atterrissage statiques pour David Demestre, couvreur en
Cornouaille (Quimper, 29). Aucune dépendance, aucun build côté hébergeur : le
dossier se dépose tel quel sur Cloudflare Pages, Netlify ou Vercel.

## Les pages

| URL | Sujet |
|---|---|
| `/reparation-fuite-toiture-finistere/` | fuite, ardoise cassée, urgence, tempête |
| `/couvreur-cornouaille/` | le métier sur toute la zone |
| `/demoussage-toiture-finistere/` | démoussage et nettoyage de toiture |
| `/renovation-toiture/` | réfection complète en ardoise |
| `/couvreur-quimper/` | couvreur à Quimper |
| `/couvreur-concarneau/` | couvreur à Concarneau |
| `/couvreur-douarnenez/` | couvreur à Douarnenez |
| `/couvreur-pont-labbe/` | couvreur à Pont-l'Abbé |

`index.html` est un sommaire de recette, en `noindex` comme les pages.

## Construire

Tout le contenu rédactionnel vit dans `build.py`, la structure dans
`templates/page.html`. **Les pages générées ne s'éditent jamais à la main** :
elles sont écrasées à chaque build.

```bash
python3 build.py
```

Le build refuse de produire une page dont le titre dépasse 65 caractères, dont
la méta sort de 70-160, dont une image manque, dont le hero n'a pas sa version
mobile, ou qui répète deux fois la même photo.

## Aperçu local

```bash
python3 -m http.server 4223 --directory .
```

## Ce que le dossier contient

```
build.py                     générateur : contenu + garde-fous
templates/page.html          structure commune aux 8 pages
templates/accueil.html       le sommaire
assets/styles.css            feuille de style unique
assets/script.js             suivi des conversions et envoi du formulaire
assets/fonts/                Bricolage Grotesque + Inter, auto-hébergés
assets/img/                  16 visuels + 4 versions mobile des heros
```

## Parti pris technique

- **Mobile d'abord** : sous 860 px, le formulaire passe avant l'argumentaire —
  le premier champ est à 899 px, soit un écran de scroll. Barre d'appel fixe.
- **Poids** : 193 Ko pour une page complète sur mobile, heros servis en
  `srcset` (900 px au lieu de 1 920).
- **Zéro requête tierce** : polices auto-hébergées, aucune CDN.
- **Aucun lien sortant** : une page publicitaire n'a pas de sortie.
- **Accessibilité** : cibles tactiles à 44 px, contrastes vérifiés, `alt` sur
  toutes les images, JSON-LD valide.

## À renseigner avant mise en ligne

Tout est centralisé en tête de `build.py` — une édition, huit pages :
le téléphone, le domaine, la clé du formulaire et les identifiants de
conversion. Tant qu'un identifiant contient `XXXX`, `script.js` n'envoie rien.

Les photos sont une banque d'images sous licence libre, à remplacer par les
chantiers réels dès qu'ils sont disponibles.
