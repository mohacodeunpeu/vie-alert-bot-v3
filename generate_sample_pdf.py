"""
Genere un PDF d'exemple pour visualiser le rendu de la lettre auto-generee.
Lance localement : python generate_sample_pdf.py
Sortie : sample_cover_letter.pdf
"""

import auto_apply
import cover_letter as cl


SAMPLE_OFFER = {
    "id":           "242364",
    "titre":        "Business Developer (H/F)",
    "entreprise":   "Decathlon Asia",
    "ville":        "Shanghai",
    "pays":         "CHINE",
    "duree":        12,
    "secteur":      "COMMERCE",
    "description":  ("Vous serez en charge du developpement commercial sur le marche chinois, "
                     "avec un focus sur le retail sport et l'expansion e-commerce sur Tmall et JD.com. "
                     "Pilotage de la relation avec les distributeurs locaux et reporting au siege Asie."),
}


def main() -> None:
    text     = cl.generate(SAMPLE_OFFER)
    msg      = cl.generate_short_message(SAMPLE_OFFER)
    pdf_data = auto_apply._generate_cover_pdf(text, SAMPLE_OFFER)

    with open("sample_cover_letter.pdf", "wb") as f:
        f.write(pdf_data)

    print("=" * 70)
    print("MESSAGE COURT (envoye dans le champ Message de l'API):")
    print("=" * 70)
    print(msg)
    print()
    print("=" * 70)
    print("LETTRE COMPLETE (texte qui sera mis en PDF):")
    print("=" * 70)
    print(text)
    print()
    print("=" * 70)
    print(f"PDF genere : sample_cover_letter.pdf ({len(pdf_data)} octets)")


if __name__ == "__main__":
    main()
