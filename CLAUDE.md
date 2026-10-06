# CLAUDE.md — vie-alert-bot-v3

## REGLES CRITIQUES
1. NE JAMAIS envoyer d'images. L'API crash avec "image exceeds 2000px". Utilise pdftotext pour inspecter les PDFs, jamais d'image.
2. Mode autonome. Pas de confirmation entre etapes. Resume court a la fin.
3. Push = rien a redeployer. Tout tourne sur GitHub Actions (bot.yml, cron */5,
   qui rafraichit le token puis lance le bot). Le Procfile est un reste de Railway.
4. Conventional commits (feat/fix/refactor/chore).

## PROJET
Bot de candidatures auto V.I.E. via Business France.
Stack: Python, GitHub Actions (bot + refresh token), Discord notifs.
Owner: Amine (mohamedbenpro47@gmail.com), Bachelor REM (Bac+3), commerce / recrutement.

## FAITS — REGLE ABSOLUE (06/10/2026)
Son plus haut diplome est le Bachelor REM (Bac+3, Paris Nord Business School,
2026). Il n'a NI master NI MBA, et n'a jamais ete a PSB. Il n'est ni en poste ni
en formation : disponible immediatement. DEFI GROUPE est termine (juil. 2026),
PROMAN Group (charge d'affaires, 2026) est son poste le plus recent.
Source de verite : profil.json de hellowork-automation-pro, statut « verifie ».
Aucun chiffre (CA, nb de candidats, % d'engagement), outil (HubSpot, Sales
Navigator) ou langue (chinois) n'entre dans un CV ou une lettre s'il n'y est pas.
Jusqu'au 06/10/2026 ce bot envoyait « MBA en cours (PSB Paris) » et « 360 k€/mois » :
les recruteurs l'ont rappele dessus (Bessand, VIE246499).

## FONCTIONS
- Surveille nouvelles offres V.I.E.
- Notif Discord pour TOUTES les offres
- Postule auto sur offres ciblees
- Genere CV + lettre personnalises
- Recoit confirmations Business France

## FILTRE GEOGRAPHIQUE
Inclus: Hors Europe (sauf ES/PT), Asie, Moyen-Orient, Ameriques, Oceanie.
Exclus: Europe (sauf ES/PT), Afrique.
Secteurs: commerce, finance, marketing.

## PROFILE
- LinkedIn: PROFILE['qr_url']
- CV video futur: PROFILE['video_cv_url'] (vide pour l'instant)
- CV doit refleter son vrai niveau (Bac+3) de facon pro, jamais robot/template

## DEMARRAGE SESSION
Toujours commencer par:
git status
git log -10 --oneline
ls samples/

## DERNIER ETAT CONNU
Samples a 1 page chacun, CV et lettres.
Accents : le texte etait ecrit SANS accent dans cv_generator.py et cover_letter.py.
Ce n'etait pas une contrainte de fpdf — la police de base couvre le latin-1, donc
« Negociation » passe tres bien. Seul le symbole EUR est refuse, d'ou « k EUR »
via _safe(). Ne jamais reecrire ces textes sans accents.

## AMELIORATIONS A FAIRE

### 1. Bug layout langues — FAIT
Regle par un calage automatique : cv_generator.SCALES essaie de la typographie
confortable vers la serree et garde la premiere echelle qui tient sur une page
(MAX_CONTENT_Y = 278). Avant, les polices etaient figees a 8,3 pt « pour tenir »
et le contenu s'arretait a 195 mm sur 285 : serre ET un tiers de page blanc.
Les samples tiennent maintenant a 266-277 mm, en polices 12 a 24 % plus grandes.

### 2. CV personnalise profond — FAIT
Avant chaque generation:
- ANALYSER offre (titre, missions, profil ideal, mots-cles ATS)
- REORDONNER experiences pour matcher
- REECRIRE bullets avec vocabulaire offre (sans mentir)
- Skills section adaptee
- Titre CV adapte au poste
Qualite > vitesse. 30-60s de plus OK.

### 3. Lettre 100% naturelle
- Hook varie (5-8 styles rotation)
- Referencer 2-3 elements offre
- Pont concret experiences <-> besoins entreprise
- Ton pro mais humain
- 1 page

### 4. QR Code CV — FAIT
Le code etait deja ecrit et ne s'executait jamais : `qrcode` manquait de
requirements.txt et l'ImportError etait avalee dans _make_qr_png. Aucun CV parti
en production n'a donc jamais porte de QR. Paquet declare (+ pillow).
Verifier apres toute modif de requirements : un CV genere doit contenir /Image.

### 5. Filtre geographique
Verifier code, etendre si besoin (voir section FILTRE).

## CONVENTIONS
- Python: f-strings, type hints, fonctions courtes
- Pas de print(), utiliser logging
- snake_case variables, UPPER_CASE constantes

## WORKFLOW
1. git status + git log
2. Lire fichiers AVANT modifier
3. Implementer
4. Regenerer 4 samples (Brand Manager Dubai, Business Dev Chine, Chef Produit USA, Financial Analyst Singapour)
5. Verifier qualite via pdftotext (jamais image)
6. Commit + push
7. Confirmer Railway redeploy

## NE PAS CASSER
- Filtre geographique (sauf demande explicite)
- Conventional commits
- Structure PROFILE dict
- Samples sur 1 page
- Discord notifs

## IDEE FUTURE
App/site separe pour generateur CV/lettre.
Input: poste + entreprise. Output: CV + lettre ATS-perfect.
Stack a etudier: Next.js, FastAPI+React, ou Streamlit.
A discuter quand bot principal stable.
