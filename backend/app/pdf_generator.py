from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
import os


def generate_pdf(filename, duration, language, transcript,
                 corrected_transcript, evaluation):

    os.makedirs("reports", exist_ok=True)

    pdf_path = os.path.join(
        "reports",
        f"{os.path.splitext(filename)[0]}_report.pdf"
    )

    doc = SimpleDocTemplate(pdf_path)
    styles = getSampleStyleSheet()

    elements = []

    elements.append(Paragraph("<b>Pronunciation Assessment Report</b>", styles["Title"]))

    elements.append(Paragraph(f"<b>Filename:</b> {filename}", styles["BodyText"]))
    elements.append(Paragraph(f"<b>Duration:</b> {duration} seconds", styles["BodyText"]))
    elements.append(Paragraph(f"<b>Language:</b> {language}", styles["BodyText"]))

    elements.append(Paragraph("<br/><b>Transcript</b>", styles["Heading2"]))
    elements.append(Paragraph(transcript, styles["BodyText"]))

    elements.append(Paragraph("<br/><b>Corrected Transcript</b>", styles["Heading2"]))
    elements.append(Paragraph(corrected_transcript, styles["BodyText"]))

    elements.append(Paragraph("<br/><b>Evaluation Scores</b>", styles["Heading2"]))

    elements.append(Paragraph(
        f"Overall Score: {evaluation['overall_score']}",
        styles["BodyText"]
    ))

    elements.append(Paragraph(
        f"Pronunciation Score: {evaluation['pronunciation_score']}",
        styles["BodyText"]
    ))

    elements.append(Paragraph(
        f"Fluency Score: {evaluation['fluency_score']}",
        styles["BodyText"]
    ))

    elements.append(Paragraph(
        f"Clarity Score: {evaluation['clarity_score']}",
        styles["BodyText"]
    ))

    elements.append(Paragraph(
        f"Pace: {evaluation['pace']}",
        styles["BodyText"]
    ))

    elements.append(Paragraph("<br/><b>Mispronounced Words</b>", styles["Heading2"]))

    if evaluation["mispronounced_words"]:
        for word in evaluation["mispronounced_words"]:
            elements.append(
                Paragraph(
                    f"""
                    <b>{word['word']}</b><br/>
                    Severity: {word['severity']}<br/>
                    Issue: {word['issue']}<br/>
                    Tip: {word['tip']}
                    """,
                    styles["BodyText"]
                )
            )
    else:
        elements.append(
            Paragraph(
                "No significant pronunciation issues detected.",
                styles["BodyText"]
            )
        )

    elements.append(Paragraph("<br/><b>Strengths</b>", styles["Heading2"]))

    for item in evaluation["strengths"]:
        elements.append(
            Paragraph(f"• {item}", styles["BodyText"])
        )

    elements.append(Paragraph("<br/><b>Suggestions</b>", styles["Heading2"]))

    for item in evaluation["suggestions"]:
        elements.append(
            Paragraph(f"• {item}", styles["BodyText"])
        )

    elements.append(Paragraph("<br/><b>Overall Feedback</b>", styles["Heading2"]))
    elements.append(
        Paragraph(
            evaluation["overall_feedback"],
            styles["BodyText"]
        )
    )

    doc.build(elements)

    return pdf_path