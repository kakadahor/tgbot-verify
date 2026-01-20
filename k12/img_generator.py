"""Teacher Verification Document Generation (PDF + PNG)"""
import random
from datetime import datetime
from io import BytesIO
from pathlib import Path

from xhtml2pdf import pisa


def _render_template(first_name: str, last_name: str) -> str:
    """Read template, replace name/employee ID/date, and expand CSS variables."""
    full_name = f"{first_name} {last_name}"
    employee_id = random.randint(1000000, 9999999)
    # Format: "January 16, 2026" - more formal and official
    current_date = datetime.now().strftime("%B %d, %Y")

    template_path = Path(__file__).parent / "card-temp.html"
    html = template_path.read_text(encoding="utf-8")

    # Expand CSS variables for xhtml2pdf compatibility
    color_map = {
        "var(--primary-blue)": "#0056b3",
        "var(--border-gray)": "#dee2e6",
        "var(--bg-gray)": "#f8f9fa",
    }
    for placeholder, color in color_map.items():
        html = html.replace(placeholder, color)

    # Replace sample name / employee ID / date (template has name in two places + span)
    html = html.replace("Sarah J. Connor", full_name)
    html = html.replace("E-9928104", f"E-{employee_id}")
    html = html.replace('id="currentDate"></span>', f'id="currentDate">{current_date}</span>')

    return html


def generate_teacher_pdf(first_name: str, last_name: str) -> bytes:
    """Generate teacher verification PDF document bytes."""
    html = _render_template(first_name, last_name)

    output = BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=output, encoding="utf-8")
    if pisa_status.err:
        raise Exception("PDF generation failed")

    pdf_data = output.getvalue()
    output.close()
    return pdf_data


def generate_teacher_png(first_name: str, last_name: str) -> bytes:
    """Use WeasyPrint to generate PNG screenshot."""
    try:
        from weasyprint import HTML
        html = _render_template(first_name, last_name)
        # Scale 2x for quality (resolution=150)
        return HTML(string=html).write_png(resolution=150)
    except ImportError:
        raise Exception("weasyprint required: pip install weasyprint")
    except Exception as e:
        raise Exception(f"Image generation failed: {str(e)}")


# Backward compatibility: default to PDF generation
def generate_teacher_image(first_name: str, last_name: str) -> bytes:
    return generate_teacher_pdf(first_name, last_name)
