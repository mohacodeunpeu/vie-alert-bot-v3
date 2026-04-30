"""
Genere des CV + lettres d'exemples pour visualiser le rendu sur differents sous-roles.
Lance localement : python generate_sample_pdf.py

Sortie :
- sample_cover_letter.pdf
- samples/cv_business_dev_chine.pdf
- samples/lettre_business_dev_chine.pdf
- samples/cv_chef_produit_etats_unis.pdf
- samples/lettre_chef_produit_etats_unis.pdf
- samples/cv_financial_analyst_singapour.pdf
- samples/lettre_financial_analyst_singapour.pdf
- samples/cv_talent_acquisition_dubai.pdf
- samples/lettre_talent_acquisition_dubai.pdf
"""

import os
import auto_apply
import cover_letter as cl
import cv_generator


SAMPLES = [
    {
        "key": "business_dev_chine",
        "offer": {
            "id":         "242364",
            "titre":      "Business Developer (H/F)",
            "entreprise": "Decathlon Asia",
            "ville":      "Shanghai",
            "pays":       "CHINE",
            "duree":      12,
            "secteur":    "COMMERCE",
            "description": "Vous serez en charge du developpement commercial sur le marche chinois, "
                           "avec un focus sur le retail sport et l'expansion e-commerce sur Tmall et "
                           "JD.com. Pilotage de la relation avec les distributeurs locaux et reporting "
                           "au siege Asie.",
        },
    },
    {
        "key": "chef_produit_etats_unis",
        "offer": {
            "id":         "242679",
            "titre":      "Chef de Produit Marketing (H/F)",
            "entreprise": "L'Oreal USA",
            "ville":      "New York",
            "pays":       "ETATS-UNIS",
            "duree":      18,
            "secteur":    "MARKETING - COMMUNICATION",
            "description": "Au sein de la division marketing US, vous piloterez le lancement de "
                           "nouvelles references skincare : analyse de marche, briefs creatifs, "
                           "coordination R&D et trade marketing, suivi de la performance produit.",
        },
    },
    {
        "key": "financial_analyst_singapour",
        "offer": {
            "id":         "242668",
            "titre":      "Financial Analyst APAC (H/F)",
            "entreprise": "Engie Asia Pacific",
            "ville":      "Singapour",
            "pays":       "SINGAPOUR",
            "duree":      24,
            "secteur":    "FINANCE COMPTABILITE GESTION BANQUE",
            "description": "Au sein de la direction financiere APAC, vous participerez aux exercices "
                           "de budget et forecast, produirez des analyses de performance pour les "
                           "decideurs et participerez aux projets de transformation finance.",
        },
    },
    {
        "key": "brand_manager_dubai",
        "offer": {
            "id":         "242422",
            "titre":      "Brand Manager Middle East (H/F)",
            "entreprise": "L'Occitane Middle East",
            "ville":      "Dubai",
            "pays":       "EMIRATS ARABES UNIS",
            "duree":      18,
            "secteur":    "MARKETING - COMMUNICATION",
            "description": "Au sein de l'equipe brand regionale, vous piloterez le positionnement "
                           "des references skincare et fragrance sur le marche Moyen-Orient : "
                           "lancements produits, partenariats avec les retailers premium, "
                           "campagnes 360 et activation digitale sur les marches GCC.",
        },
    },
]


def main() -> None:
    os.makedirs("samples", exist_ok=True)

    # Sample principal a la racine (pour visibilite GitHub)
    main_offer = SAMPLES[0]["offer"]
    text = cl.generate(main_offer)
    pdf_letter = auto_apply._generate_cover_pdf(text, main_offer)
    with open("sample_cover_letter.pdf", "wb") as f:
        f.write(pdf_letter)
    print(f"OK sample_cover_letter.pdf ({len(pdf_letter)} octets)")

    pdf_cv = cv_generator.generate(main_offer)
    with open("sample_cv.pdf", "wb") as f:
        f.write(pdf_cv)
    print(f"OK sample_cv.pdf ({len(pdf_cv)} octets)")

    # Tous les samples (4 paires CV + lettre)
    for s in SAMPLES:
        key, offer = s["key"], s["offer"]
        try:
            text = cl.generate(offer)
            pdf_letter = auto_apply._generate_cover_pdf(text, offer)
            with open(f"samples/lettre_{key}.pdf", "wb") as f:
                f.write(pdf_letter)
            pdf_cv = cv_generator.generate(offer)
            with open(f"samples/cv_{key}.pdf", "wb") as f:
                f.write(pdf_cv)
            print(f"OK {key} : lettre {len(pdf_letter)} oct + cv {len(pdf_cv)} oct")
        except Exception as e:
            print(f"FAIL {key} : {e}")


if __name__ == "__main__":
    main()
