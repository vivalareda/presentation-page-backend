import os
from datetime import datetime
from io import BytesIO

from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer

app = Flask(__name__)
# Configure CORS to allow requests from your React app
CORS(
    app,
    resources={
        r"/*": {
            "origins": ["http://localhost:3001"],
            "methods": ["GET", "POST"],
            "allow_headers": ["Content-Type"],
        }
    },
)


class ETSReport:
    def __init__(self, data=None):
        self.teacher = data.get("teacher") if data else None
        self.project_name = data.get("project_name") if data else None
        self.course_code = data.get("course_code") if data else None
        self.course_name = data.get("course_name") if data else None
        self.group_number = data.get("group_number") if data else None
        self.authors = (
            [student["name"] for student in data.get("students", [])] if data else None
        )
        self.code = (
            [student["code"] for student in data.get("students", [])] if data else None
        )
        self.date = datetime.now()
        self.styles = getSampleStyleSheet()

    def create_title_style(self):
        """Create custom styles for the document"""
        title_style = ParagraphStyle(
            "CustomTitle",
            parent=self.styles["Normal"],
            fontSize=16,
            leading=20,
            alignment=1,
            spaceAfter=30,
        )
        return title_style

    def create_normal_style(self):
        """Create normal text style"""
        normal_style = ParagraphStyle(
            "CustomNormal",
            parent=self.styles["Normal"],
            fontSize=12,
            leading=16,
            alignment=1,
            spaceAfter=12,
        )
        return normal_style

    def generate_pdf(self):
        """Generate the PDF report in memory"""
        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=1.5 * inch,
            leftMargin=1.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.55 * inch,
        )

        story = []

        logo = Image("ets_logo.png", width=2 * inch, height=1.2 * inch)
        story.append(logo)
        story.append(Spacer(1, 50))

        title_style = self.create_title_style()
        normal_style = self.create_normal_style()

        story.append(Paragraph("ÉCOLE DE TECHNOLOGIE SUPÉRIEURE", title_style))
        story.append(Spacer(1, 30))

        story.append(Paragraph("RAPPORT DE LABORATOIRE", normal_style))
        story.append(Paragraph(f"PRÉSENTÉ À {self.teacher}", normal_style))
        story.append(Spacer(1, 30))

        story.append(Paragraph("DANS LE CADRE DU COURS", normal_style))
        story.append(Paragraph(f"{self.course_code} {self.course_name}", normal_style))
        story.append(Paragraph(f"GROUPE {self.group_number}", normal_style))
        story.append(Spacer(1, 40))

        story.append(Paragraph(self.project_name or "", title_style))
        story.append(Spacer(1, 30))

        story.append(Paragraph("PAR", normal_style))
        story.append(Spacer(1, 20))
        print("Student code: ", self.code)
        for student in zip(self.authors or [], self.code or []):
            story.append(Paragraph(f"{student[0]} - {student[1]}", normal_style))
        story.append(Spacer(1, 30))

        date_fr = self.date.strftime("%d %B %Y").upper()
        story.append(Paragraph(date_fr, normal_style))

        doc.build(story)

        buffer.seek(0)
        return buffer


@app.route("/preview", methods=["POST"])
def preview_report():
    try:
        data = request.get_json()

        report = ETSReport(data)

        pdf_buffer = report.generate_pdf()

        return send_file(pdf_buffer, mimetype="application/pdf", as_attachment=False)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download", methods=["POST"])
def download_report():
    try:
        data = request.get_json()
        print("Students codes:")
        print(student["code"] for student in data.get("students", []))

        report = ETSReport(data)

        pdf_buffer = report.generate_pdf()

        return send_file(
            pdf_buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name="rapport_ets.pdf",
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy"})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
