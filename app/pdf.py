from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import io

BLEU_CDG = colors.HexColor("#004B6B")
BLEU_CLAIR = colors.HexColor("#E6EFF4")

def generer_devis_pdf(devis, client, lignes):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                             rightMargin=15*mm, leftMargin=15*mm,
                             topMargin=15*mm, bottomMargin=20*mm)

    styles = getSampleStyleSheet()
    story = []

    # --- EN-TÊTE ---
    style_titre = ParagraphStyle("titre", fontSize=20, textColor=BLEU_CDG, spaceAfter=2)
    style_sous = ParagraphStyle("sous", fontSize=9, textColor=colors.grey)
    style_normal = ParagraphStyle("normal", fontSize=9, spaceAfter=2)
    style_bold = ParagraphStyle("bold", fontSize=9, fontName="Helvetica-Bold")
    style_right = ParagraphStyle("right", fontSize=9, alignment=TA_RIGHT)

    entete = [
        [
            Paragraph("CDG Serrurerie", style_titre),
            Paragraph(f"<b>DEVIS N° {devis.numero}</b>", 
                      ParagraphStyle("dnum", fontSize=14, textColor=BLEU_CDG, alignment=TA_RIGHT))
        ],
        [
            Paragraph("66 avenue des Champs-Élysées, 75008 Paris<br/>"
                      "Tél : +33 1 89 70 64 60 | +33 7 83 31 72 83<br/>"
                      "cdgserrurerie@gmail.com | cdgserrurerie.fr", style_sous),
            Paragraph(f"Date : {devis.created_at.strftime('%d/%m/%Y')}", style_right)
        ]
    ]
    t_entete = Table(entete, colWidths=[100*mm, 80*mm])
    t_entete.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))
    story.append(t_entete)
    story.append(Spacer(1, 6*mm))

    # --- CLIENT ---
    client_data = [
        [Paragraph("<b>CLIENT</b>", style_bold), ""],
        [Paragraph(client.nom, style_normal), ""],
    ]
    if client.adresse:
        client_data.append([Paragraph(client.adresse, style_normal), ""])
    if client.ville:
        client_data.append([Paragraph(client.ville, style_normal), ""])
    if client.email:
        client_data.append([Paragraph(client.email, style_normal), ""])
    if client.telephone:
        client_data.append([Paragraph(client.telephone, style_normal), ""])

    t_client = Table(client_data, colWidths=[90*mm, 90*mm])
    t_client.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,0), BLEU_CLAIR),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t_client)
    story.append(Spacer(1, 6*mm))

    # --- ADRESSE INTERVENTION ---
    if devis.adresse_intervention:
        story.append(Paragraph(f"<b>Adresse d'intervention :</b> {devis.adresse_intervention}", style_normal))
        story.append(Spacer(1, 4*mm))

    # --- LIGNES DEVIS ---
    data = [["Désignation", "Qté", "Prix HT", "TVA", "Total HT"]]
    total_ht = 0
    total_tva = 0

    for ligne in lignes:
        ht = ligne.quantite * ligne.prix_unitaire_ht
        tva_montant = ht * (ligne.tva / 100)
        total_ht += ht
        total_tva += tva_montant
        data.append([
            ligne.designation,
            str(ligne.quantite),
            f"{ligne.prix_unitaire_ht:.2f} €",
            f"{ligne.tva:.0f}%",
            f"{ht:.2f} €"
        ])

    total_ttc = total_ht + total_tva
    data.append(["", "", "", "Total HT", f"{total_ht:.2f} €"])
    data.append(["", "", "", "TVA", f"{total_tva:.2f} €"])
    data.append(["", "", "", "Total TTC", f"{total_ttc:.2f} €"])

    t_lignes = Table(data, colWidths=[80*mm, 15*mm, 25*mm, 20*mm, 25*mm])
    t_lignes.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), BLEU_CDG),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("ROWBACKGROUNDS", (0,1), (-1,-4), [colors.white, BLEU_CLAIR]),
        ("BACKGROUND", (0,-3), (-1,-1), BLEU_CLAIR),
        ("FONTNAME", (0,-3), (-1,-1), "Helvetica-Bold"),
        ("ALIGN", (1,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-4), 0.3, colors.lightgrey),
        ("LINEABOVE", (0,-3), (-1,-3), 1, BLEU_CDG),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING", (0,0), (-1,-1), 5),
    ]))

    story.append(t_lignes)
    story.append(Spacer(1, 8*mm))

    # --- PAIEMENT ---
    story.append(Paragraph("<b>Règlement :</b> Virement bancaire", style_normal))
    story.append(Paragraph("IBAN : FR76 2823 3000 0129 4487 3028 268 | BIC : REVOFRP2", style_normal))
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("Devis valable 30 jours.",
                            ParagraphStyle("grey", fontSize=8, textColor=colors.grey)))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    return io.BytesIO(pdf_bytes)  