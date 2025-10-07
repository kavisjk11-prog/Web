# backend/report.py
import os
from datetime import datetime
import html
import json

REPORTS_DIR = os.path.join(os.path.dirname(__file__), "..", "reports")
os.makedirs(REPORTS_DIR, exist_ok=True)

def _safe_html(s: str) -> str:
    return html.escape(str(s))

def generate_html_report(scenario: dict, email: str) -> str:
    """Create an HTML report file and return its path."""
    safe_name = "".join(c for c in scenario.get("scenario_name", "report") if c.isalnum() or c in (" ", "_", "-")).strip()
    timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    filename = f"ROI_Report_{safe_name}_{timestamp}.html"
    path = os.path.join(REPORTS_DIR, filename)

    inputs = scenario.get("inputs", {})
    results = scenario.get("results", {})

    html_body = f"""
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8"/>
        <title>ROI Report - {_safe_html(safe_name)}</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 30px; }}
          h1 {{ color: #0b5; }}
          table {{ border-collapse: collapse; width: 100%; max-width: 800px; }}
          td, th {{ border: 1px solid #ddd; padding: 8px; }}
          th {{ background: #f4f4f4; text-align: left; }}
          .kpi {{ font-size: 1.2rem; font-weight: bold; }}
        </style>
      </head>
      <body>
        <h1>Invoicing ROI Report</h1>
        <p><strong>Scenario:</strong> {_safe_html(safe_name)}</p>
        <p><strong>Requested by (email):</strong> {_safe_html(email)}</p>
        <hr/>
        <h2>Inputs</h2>
        <table>
          <tbody>
    """
    for k, v in inputs.items():
        html_body += f"<tr><th>{_safe_html(k)}</th><td>{_safe_html(v)}</td></tr>"

    html_body += """
          </tbody>
        </table>

        <h2>Results</h2>
        <table>
          <tbody>
    """
    for k, v in results.items():
        # If nested dict, pretty print
        if isinstance(v, dict) or isinstance(v, list):
            v = json.dumps(v)
        html_body += f"<tr><th>{_safe_html(k)}</th><td class='kpi'>{_safe_html(v)}</td></tr>"

    html_body += """
          </tbody>
        </table>

        <p style="margin-top:30px;font-size:0.9rem;color:#666;">Generated on UTC: {ts}</p>
      </body>
    </html>
    """.format(ts=_safe_html(timestamp))

    with open(path, "w", encoding="utf-8") as f:
        f.write(html_body)

    return path

def generate_report(scenario: dict, email: str) -> dict:
    """
    Generate report: always create HTML; try to create PDF (if weasyprint available).
    Returns dict: { 'html_path': ..., 'pdf_path': ... or None }
    """
    html_path = generate_html_report(scenario, email)
    pdf_path = None

    try:
        # WeasyPrint is optional; only use if importable and works
        from weasyprint import HTML
        pdf_filename = os.path.splitext(os.path.basename(html_path))[0] + ".pdf"
        pdf_path_full = os.path.join(REPORTS_DIR, pdf_filename)
        HTML(filename=html_path).write_pdf(pdf_path_full)
        pdf_path = pdf_path_full
    except Exception:
        # If weasyprint not installed or fails on the system, fall back gracefully
        pdf_path = None

    return {"html_path": html_path, "pdf_path": pdf_path}
