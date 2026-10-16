#!/usr/bin/env python3
"""Déploie ce dossier sur Cloudflare Pages, en envoi direct.

    python3 deploy.py            # ce qui partirait
    python3 deploy.py --appliquer

Pourquoi ce script plutôt que wrangler : wrangler exige Node 22 et la machine
est en Node 20. Il refait le même travail à la main.

Deux pièges, qui coûtent chacun une heure si on les redécouvre :

1. L'empreinte attendue par Pages n'est PAS celle du fichier. C'est
   blake3(base64_du_contenu + extension_sans_point), en hexadécimal, tronquée
   à 32 caractères. Une empreinte calculée autrement laisse passer l'envoi
   puis fait échouer le déploiement sans message utile.

2. Le jeton d'accès de wrangler dure une heure. On le renouvelle avec le
   refresh_token de ~/.wrangler/config/default.toml et le client_id public de
   wrangler. Python n'a pas ses certificats racine sur cette machine : on
   passe par curl, jamais par urllib.

Dépendance : blake3. Si absent :
    python3 -m venv .venv-deploy && .venv-deploy/bin/pip install blake3
    .venv-deploy/bin/python deploy.py --appliquer
"""
import base64
import json
import mimetypes
import pathlib
import re
import subprocess
import sys

try:
    from blake3 import blake3
except ImportError:
    sys.exit("blake3 manquant. Voir l'en-tête de ce fichier.")

PROJET = "demestre"
COMPTE = "1adfc5fee18c4e9c6ea400654992791f"
CLIENT_ID = "54d11594-84e4-41aa-b438-e81b8fa78ee7"   # client public de wrangler
API = "https://api.cloudflare.com/client/v4"
RACINE = pathlib.Path(__file__).parent

# Ce qui ne doit JAMAIS partir en ligne : le générateur, les gabarits et toute
# la documentation interne (elle parle des autres clients et des faiblesses du
# dossier).
EXCLUS_DOSSIERS = {".git", ".venv-deploy", "templates", "ads-import", "__pycache__"}
EXCLUS_FICHIERS = {"build.py", "deploy.py", ".gitignore", ".DS_Store"}
EXCLUS_SUFFIXES = {".md", ".py", ".bak"}


def jeton():
    """Renouvelle le jeton d'acces et REECRIT le jeton tourne dans la config.

    ⚠️ Cloudflare fait TOURNER le refresh_token a chaque usage : l'ancien est
    immediatement invalide. Si on ne reecrit pas le nouveau dans
    ~/.wrangler/config/default.toml, la session est cassee au renouvellement
    suivant, pour ce script comme pour wrangler lui-meme (`invalid_grant`).
    C'est exactement ce que fait wrangler ; on ne fait que l'imiter.
    """
    cfg = pathlib.Path.home() / ".wrangler/config/default.toml"
    if not cfg.exists():
        sys.exit("Session wrangler absente. Lancer `npx wrangler login` une fois.")
    refresh = re.search(r'refresh_token = "(.*?)"', cfg.read_text()).group(1)
    out = subprocess.run(
        ["curl", "-s", "--max-time", "30", "-X", "POST",
         "https://dash.cloudflare.com/oauth2/token",
         "-H", "Content-Type: application/x-www-form-urlencoded",
         "--data-urlencode", "grant_type=refresh_token",
         "--data-urlencode", "refresh_token=" + refresh,
         "--data-urlencode", "client_id=" + CLIENT_ID],
        capture_output=True, text=True).stdout
    d = json.loads(out)
    if "access_token" not in d:
        sys.exit("Renouvellement du jeton refusé : %s\n"
                 "Si c'est « invalid_grant », la session est a refaire :\n"
                 "    npx wrangler login" % json.dumps(d)[:200])
    if d.get("refresh_token") and d["refresh_token"] != refresh:
        txt = cfg.read_text()
        txt = re.sub(r'refresh_token = ".*?"',
                     'refresh_token = "%s"' % d["refresh_token"], txt)
        txt = re.sub(r'oauth_token = ".*?"',
                     'oauth_token = "%s"' % d["access_token"], txt)
        cfg.write_text(txt)
        print("   (jeton de rafraichissement tourne, config wrangler mise a jour)")
    return d["access_token"]


def curl(url, tok, *args):
    out = subprocess.run(
        ["curl", "-s", "--max-time", "120", url,
         "-H", "Authorization: Bearer " + tok, *args],
        capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return {"success": False, "brut": out[:300]}


def fichiers():
    for p in sorted(RACINE.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(RACINE)
        if set(rel.parts[:-1]) & EXCLUS_DOSSIERS or rel.parts[0] in EXCLUS_DOSSIERS:
            continue
        if rel.name in EXCLUS_FICHIERS or p.suffix in EXCLUS_SUFFIXES:
            continue
        yield rel, p


def main() -> int:
    appliquer = "--appliquer" in sys.argv
    manifeste, charges, octets = {}, {}, 0
    for rel, p in fichiers():
        brut = p.read_bytes()
        b64 = base64.b64encode(brut).decode()
        h = blake3((b64 + p.suffix[1:]).encode()).hexdigest()[:32]
        manifeste["/" + rel.as_posix()] = h
        charges[h] = {"key": h, "value": b64, "base64": True,
                      "metadata": {"contentType":
                                   mimetypes.guess_type(p.name)[0]
                                   or "application/octet-stream"}}
        octets += len(brut)

    print("%d fichiers, %.0f Ko" % (len(manifeste), octets / 1024))
    if not appliquer:
        print("Simulation. Ajouter --appliquer pour envoyer.")
        return 0

    tok = jeton()
    r = curl(f"{API}/accounts/{COMPTE}/pages/projects/{PROJET}/upload-token", tok)
    if not r.get("success"):
        print("Jeton d'envoi refusé :", r.get("errors") or r); return 1
    jwt = r["result"]["jwt"]

    r = curl(f"{API}/pages/assets/check-missing", jwt, "-X", "POST",
             "-H", "Content-Type: application/json",
             "--data", json.dumps({"hashes": list(charges)}))
    if not r.get("success"):
        print("check-missing en échec :", r.get("errors") or r); return 1
    manquants = r["result"]
    print("%d à envoyer sur %d" % (len(manquants), len(charges)))

    # Par paquets : un seul gros corps se fait rejeter.
    envoi = [charges[h] for h in manquants]
    tmp = RACINE / ".lot.json"
    for i in range(0, len(envoi), 12):
        tmp.write_text(json.dumps(envoi[i:i + 12]))
        r = curl(f"{API}/pages/assets/upload", jwt, "-X", "POST",
                 "-H", "Content-Type: application/json", "--data", "@" + str(tmp))
        if not r.get("success"):
            print("Envoi en échec :", r.get("errors") or r); return 1
        print("   paquet %d" % (i // 12 + 1))
    tmp.unlink(missing_ok=True)

    man = RACINE / ".manifeste.json"
    man.write_text(json.dumps(manifeste))
    r = curl(f"{API}/accounts/{COMPTE}/pages/projects/{PROJET}/deployments", tok,
             "-X", "POST", "-F", "manifest=<" + str(man), "-F", "branch=main")
    man.unlink(missing_ok=True)
    if not r.get("success"):
        print("Déploiement refusé :", r.get("errors") or r); return 1
    print("\nDéployé :", r["result"].get("url"))
    print("En ligne sur https://demestrecouverture.fr/ dans quelques secondes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
