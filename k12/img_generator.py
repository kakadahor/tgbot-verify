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
    """Use xhtml2pdf + fitz to generate PNG screenshot."""
    try:
        import io
        import fitz
        from xhtml2pdf import pisa
        
        # 1. Generate HTML
        html = _render_template(first_name, last_name)
        
        # 2. Render HTML to PDF in memory
        pdf_buffer = io.BytesIO()
        pisa.CreatePDF(html, dest=pdf_buffer)
        pdf_data = pdf_buffer.getvalue()
        
        # 3. Convert PDF to PNG using fitz
        doc = fitz.open(stream=pdf_data, filetype='pdf')
        page = doc.load_page(0)
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        return pix.tobytes('png')
        
    except ImportError:
        raise Exception("xhtml2pdf and pymupdf required: pip install xhtml2pdf pymupdf")
    except Exception as e:
        raise Exception(f"Image generation failed: {str(e)}")


# Backward compatibility: default to PDF generation
def generate_teacher_image(first_name: str, last_name: str) -> bytes:
    return generate_teacher_pdf(first_name, last_name)
