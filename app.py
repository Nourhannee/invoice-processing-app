import os
import streamlit as st
from langchain.messages import HumanMessage, SystemMessage
from langchain_groq.chat_models import ChatGroq
from groq import Groq
import base64
import json
import re
import io
from datetime import datetime
from PIL import Image
import PyPDF2

try:
    import pytesseract
except ImportError:
    pytesseract = None

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="InvoiceIQ — Intelligent Invoice Processor",
    page_icon="🧾",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@300;400;500&display=swap');

/* Base */
html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

/* Background */
.stApp {
    background: #0b0c0f;
    color: #e8e4dc;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }

/* Hero header */
.hero {
    text-align: center;
    padding: 3rem 0 2rem;
    border-bottom: 1px solid #1e2028;
    margin-bottom: 2.5rem;
}
.hero-badge {
    display: inline-block;
    background: #1a1c22;
    border: 1px solid #2e3040;
    color: #7c85ff;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.15em;
    padding: 0.35rem 0.9rem;
    border-radius: 20px;
    margin-bottom: 1.2rem;
}
.hero h1 {
    font-size: 3.2rem;
    font-weight: 800;
    letter-spacing: -0.03em;
    margin: 0 0 0.5rem;
    background: linear-gradient(135deg, #e8e4dc 30%, #7c85ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.hero p {
    color: #5a5e6e;
    font-size: 1rem;
    letter-spacing: 0.03em;
}

/* Upload zone */
.upload-wrapper .stFileUploader > div {
    border: 1.5px dashed #2a2d3a !important;
    background: #0f1015 !important;
    border-radius: 12px !important;
    padding: 2.5rem !important;
    transition: border-color 0.2s;
}
.upload-wrapper .stFileUploader > div:hover {
    border-color: #7c85ff !important;
}

/* Section labels */
.section-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.2em;
    color: #3d4055;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}

/* Cards */
.card {
    background: #0f1015;
    border: 1px solid #1a1c24;
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1rem;
}
.card-accent {
    border-left: 3px solid #7c85ff;
}
.card-success {
    border-left: 3px solid #4ade80;
}
.card-warning {
    border-left: 3px solid #facc15;
}
.card-error {
    border-left: 3px solid #f87171;
}

/* Field display */
.field-row {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    padding: 0.55rem 0;
    border-bottom: 1px solid #141519;
}
.field-row:last-child { border-bottom: none; }
.field-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #4a4e62;
    letter-spacing: 0.05em;
}
.field-value {
    font-weight: 600;
    font-size: 0.9rem;
    color: #e8e4dc;
    text-align: right;
    max-width: 60%;
}
.field-missing {
    color: #f87171;
    font-style: italic;
    font-weight: 400;
}

/* Validation pill */
.validation-pill {
    display: inline-block;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    padding: 0.2rem 0.7rem;
    border-radius: 20px;
    margin: 0.2rem 0.2rem 0 0;
}
.pill-pass { background: #0d2a1a; color: #4ade80; border: 1px solid #1a4a2e; }
.pill-fail { background: #2a0d0d; color: #f87171; border: 1px solid #4a1a1a; }
.pill-warn { background: #2a200d; color: #facc15; border: 1px solid #4a380d; }

/* Line items table */
.line-items-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    margin-top: 0.5rem;
}
.line-items-table th {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    color: #3d4055;
    padding: 0.5rem 0.75rem;
    border-bottom: 1px solid #1a1c24;
    text-align: left;
}
.line-items-table td {
    padding: 0.55rem 0.75rem;
    border-bottom: 1px solid #141519;
    color: #c8c4bc;
}
.line-items-table tr:last-child td { border-bottom: none; }
.line-items-table td:last-child, .line-items-table th:last-child {
    text-align: right;
}

/* JSON block */
.json-block {
    background: #080a0c;
    border: 1px solid #1a1c24;
    border-radius: 8px;
    padding: 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: #7c85ff;
    line-height: 1.7;
    overflow-x: auto;
    white-space: pre;
}

/* Status indicator */
.status-dot {
    display: inline-block;
    width: 8px; height: 8px;
    border-radius: 50%;
    margin-right: 0.4rem;
}
.dot-green { background: #4ade80; box-shadow: 0 0 6px #4ade80; }
.dot-yellow { background: #facc15; box-shadow: 0 0 6px #facc15; }
.dot-red { background: #f87171; box-shadow: 0 0 6px #f87171; }

/* Process button */
.stButton > button {
    background: linear-gradient(135deg, #4a52cc, #7c85ff) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 0.75rem 2rem !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.95rem !important;
    font-weight: 600 !important;
    letter-spacing: 0.03em !important;
    width: 100% !important;
    transition: opacity 0.2s !important;
}
.stButton > button:hover { opacity: 0.88 !important; }

/* Confidence bar */
.conf-bar-bg {
    background: #1a1c24;
    border-radius: 4px;
    height: 6px;
    margin-top: 0.4rem;
    overflow: hidden;
}
.conf-bar-fill {
    height: 100%;
    border-radius: 4px;
    background: linear-gradient(90deg, #4a52cc, #7c85ff);
}

/* Spinner override */
.stSpinner > div { border-top-color: #7c85ff !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #0f1015;
    border-radius: 8px;
    padding: 0.25rem;
    border: 1px solid #1a1c24;
    gap: 0;
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: #4a4e62 !important;
    font-family: 'Syne', sans-serif !important;
    font-size: 0.82rem !important;
    border-radius: 6px !important;
    padding: 0.4rem 1rem !important;
}
.stTabs [aria-selected="true"] {
    background: #1a1c2e !important;
    color: #7c85ff !important;
}
.stTabs [data-baseweb="tab-panel"] { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── Hero ──────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="hero">
    <div class="hero-badge">✦ AI-POWERED · LANGCHAIN · GROQ</div>
    <h1>InvoiceIQ</h1>
    <p>Intelligent invoice parsing & financial data extraction</p>
</div>
""", unsafe_allow_html=True)

# ─── Helpers ──────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file_bytes: bytes) -> str:
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes), strict=False)
        text = ""
        for page in reader.pages:
            text += page.extract_text() or ""
        return text.strip()
    except Exception:
        return ""


def file_to_base64(file_bytes: bytes) -> str:
    return base64.standard_b64encode(file_bytes).decode("utf-8")


def extract_text_from_image(file_bytes: bytes) -> str:
    if pytesseract is None:
        raise RuntimeError("pytesseract is not installed. Install pytesseract and Tesseract OCR to process image invoices.")
    try:
        image = Image.open(io.BytesIO(file_bytes))
    except Exception as e:
        raise RuntimeError(f"Unable to open image for OCR: {e}")
    return pytesseract.image_to_string(image, lang="eng").strip()


def is_tesseract_available() -> bool:
    if pytesseract is None:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def get_image_media_type(filename: str) -> str:
    ext = filename.lower().rsplit(".", 1)[-1]
    return {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "gif": "image/gif", "webp": "image/webp"}.get(ext, "image/jpeg")


EXTRACTION_PROMPT = """You are an expert financial document analyst specializing in invoice processing.

Analyze the provided invoice and extract ALL available information. Return ONLY a valid JSON object with this exact schema:

{
  "invoice_number": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "vendor": {
    "name": "string or null",
    "address": "string or null",
    "email": "string or null",
    "phone": "string or null",
    "tax_id": "string or null"
  },
  "bill_to": {
    "name": "string or null",
    "address": "string or null",
    "email": "string or null"
  },
  "line_items": [
    {
      "description": "string",
      "quantity": number or null,
      "unit_price": number or null,
      "amount": number or null
    }
  ],
  "subtotal": number or null,
  "tax_rate": number or null,
  "tax_amount": number or null,
  "discount": number or null,
  "total_amount": number or null,
  "currency": "USD/EUR/GBP/etc or null",
  "payment_terms": "string or null",
  "payment_method": "string or null",
  "notes": "string or null",
  "po_number": "string or null",
  "confidence_score": 0.0-1.0,
  "extraction_notes": "brief notes about data quality or issues"
}

Rules:
- Use null for any field not found
- Numbers must be actual numbers, not strings
- Dates must be in YYYY-MM-DD format when possible
- confidence_score reflects overall extraction quality (0=unusable, 1=perfect)
- Return ONLY the JSON object, no markdown, no explanation"""


def _content_text_from_blocks(content_blocks) -> str:
    if isinstance(content_blocks, list):
        return "\n".join(
            block.get("text", "") for block in content_blocks
            if isinstance(block, dict) and block.get("type") == "text"
        ).strip()
    return str(content_blocks)


def _call_langchain_groq(content_blocks) -> dict:
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in secrets. Please set it in .streamlit/secrets.toml or as an environment variable.")
    client = ChatGroq(
        model="llama-3.1-8b-instant",
        api_key=api_key,
        temperature=0.0,
        max_tokens=2000,
    )
    content_text = _content_text_from_blocks(content_blocks)
    messages = [[
        SystemMessage(content=EXTRACTION_PROMPT),
        HumanMessage(content=content_text),
    ]]
    response = client.generate(messages)
    if getattr(response, "generations", None):
        raw = response.generations[0][0].text.strip()
    else:
        raw = str(response).strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def _call_direct_groq(content_blocks) -> dict:
    api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in secrets. Please set it in .streamlit/secrets.toml or as an environment variable.")
    client = Groq(api_key=api_key)
    content_text = _content_text_from_blocks(content_blocks)
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": EXTRACTION_PROMPT},
            {"role": "user", "content": content_text},
        ],
        max_tokens=2000,
    )
    raw = response.choices[0].message.content.strip()
    raw = re.sub(r"^```[a-z]*\n?", "", raw)
    raw = re.sub(r"\n?```$", "", raw)
    return json.loads(raw)


def call_groq_api(content_blocks) -> dict:
    try:
        return _call_langchain_groq(content_blocks)
    except Exception as e:
        try:
            return _call_direct_groq(content_blocks)
        except Exception as e2:
            raise RuntimeError(
                f"LangChain call failed: {type(e).__name__}: {e}\nDirect Groq fallback failed: {type(e2).__name__}: {e2}"
            )


def validate_invoice(data: dict) -> list:
    checks = []

    # Required fields
    required = ["invoice_number", "invoice_date", "vendor", "total_amount"]
    for f in required:
        val = data.get(f)
        present = val is not None and val != "" and (not isinstance(val, dict) or any(v for v in val.values()))
        checks.append({"label": f"Field: {f}", "status": "pass" if present else "fail", "msg": "Present" if present else "Missing"})

    # Math validation
    if data.get("line_items") and data.get("subtotal") is not None:
        calc = sum((i.get("amount") or 0) for i in data["line_items"])
        diff = abs(calc - data["subtotal"])
        ok = diff < 1.0
        checks.append({"label": "Line items sum → subtotal", "status": "pass" if ok else "warn",
                        "msg": f"Δ {diff:.2f}" if not ok else "Matches"})

    if data.get("subtotal") is not None and data.get("tax_amount") is not None and data.get("total_amount") is not None:
        expected = data["subtotal"] + data["tax_amount"] - (data.get("discount") or 0)
        diff = abs(expected - data["total_amount"])
        ok = diff < 1.0
        checks.append({"label": "Subtotal + Tax → Total", "status": "pass" if ok else "warn",
                        "msg": f"Expected {expected:.2f}, got {data['total_amount']:.2f}" if not ok else "Matches"})

    # Date logic
    inv_d = data.get("invoice_date")
    due_d = data.get("due_date")
    if inv_d and due_d:
        try:
            ok = datetime.strptime(due_d, "%Y-%m-%d") >= datetime.strptime(inv_d, "%Y-%m-%d")
            checks.append({"label": "Due date after invoice date", "status": "pass" if ok else "fail",
                            "msg": "Valid" if ok else "Due date before invoice date"})
        except Exception:
            pass

    return checks


def fmt_currency(val, currency=""):
    if val is None:
        return None
    sym = {"USD": "$", "EUR": "€", "GBP": "£", "EGP": "E£"}.get((currency or "").upper(), "")
    return f"{sym}{val:,.2f}"


# ─── Upload Area ──────────────────────────────────────────────────────────────
col_up, col_gap, col_info = st.columns([3, 0.3, 1.7])

with col_up:
    st.markdown('<div class="section-label">Upload Invoice</div>', unsafe_allow_html=True)
    st.markdown('<div class="upload-wrapper">', unsafe_allow_html=True)
    uploaded = st.file_uploader(
        "Drop your invoice here",
        type=["pdf", "png", "jpg", "jpeg", "webp", "txt"],
        label_visibility="collapsed",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if uploaded:
        st.markdown(f"""
        <div class="card" style="margin-top:0.75rem;">
            <div class="field-row">
                <span class="field-label">FILENAME</span>
                <span class="field-value">{uploaded.name}</span>
            </div>
            <div class="field-row">
                <span class="field-label">SIZE</span>
                <span class="field-value">{uploaded.size / 1024:.1f} KB</span>
            </div>
            <div class="field-row">
                <span class="field-label">TYPE</span>
                <span class="field-value">{uploaded.type}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

with col_info:
    st.markdown('<div class="section-label">Supported Formats</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
        <div class="field-row"><span class="field-label">PDF</span><span class="field-value" style="font-size:0.78rem;color:#4a4e62">Text + scanned</span></div>
        <div class="field-row"><span class="field-label">PNG / JPG</span><span class="field-value" style="font-size:0.78rem;color:#4a4e62">Photo invoices</span></div>
        <div class="field-row"><span class="field-label">WEBP</span><span class="field-value" style="font-size:0.78rem;color:#4a4e62">Web screenshots</span></div>
        <div class="field-row"><span class="field-label">TXT</span><span class="field-value" style="font-size:0.78rem;color:#4a4e62">Plain text</span></div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-label" style="margin-top:1rem;">Extracted Fields</div>', unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
        <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:#3d4055;line-height:2;">
        Invoice # · Date · Due Date<br>Vendor & Buyer details<br>Line items breakdown<br>Subtotal / Tax / Total<br>Payment terms · PO #
        </div>
    </div>
    """, unsafe_allow_html=True)

# ─── Process Button ───────────────────────────────────────────────────────────
st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
btn_col, _ = st.columns([2, 3])
with btn_col:
    process_clicked = st.button("⚡  Process Invoice", disabled=(uploaded is None))

# ─── Processing & Results ─────────────────────────────────────────────────────
if process_clicked and uploaded:
    file_bytes = uploaded.read()
    fname = uploaded.name.lower()
    content_blocks = []
    preview_text = None

    with st.spinner("Analyzing invoice with LangChain…"):
        try:
            # Build message content
            if fname.endswith(".txt"):
                text = file_bytes.decode("utf-8", errors="replace")
                preview_text = text[:500]
                content_blocks = [{"type": "text", "text": f"Invoice content:\n\n{text}"}]

            elif fname.endswith(".pdf"):
                text = extract_text_from_pdf(file_bytes)
                if text:
                    preview_text = text[:500]
                    content_blocks = [{"type": "text", "text": f"Invoice (extracted from PDF):\n\n{text}"}]
                else:
                    if not is_tesseract_available():
                        st.error("Scanned PDF detected, but OCR is unavailable. Install Tesseract OCR and restart the app.")
                        st.stop()
                    try:
                        ocr_text = extract_text_from_image(file_bytes)
                    except Exception as e:
                        st.error(f"Scanned PDF OCR failed: {e}")
                        st.stop()
                    if not ocr_text:
                        st.error("Scanned PDF OCR extracted no text. Please upload a clearer PDF or image.")
                        st.stop()
                    preview_text = ocr_text[:500]
                    content_blocks = [{"type": "text", "text": f"Invoice content extracted from scanned PDF:\n\n{ocr_text}"}]
            else:
                # Image
                if not is_tesseract_available():
                    st.error("Image OCR is unavailable. Install Tesseract OCR and restart the app.")
                    st.stop()
                try:
                    text = extract_text_from_image(file_bytes)
                except Exception as e:
                    st.error(f"Image OCR failed: {e}")
                    st.stop()
                if not text:
                    st.error("Image OCR extracted no text. Please upload a clearer image.")
                    st.stop()
                preview_text = text[:500]
                content_blocks = [{"type": "text", "text": f"Invoice content extracted from image:\n\n{text}"}]

            data = call_groq_api(content_blocks)
            validations = validate_invoice(data)
            currency = data.get("currency") or ""

            # ── Results ──────────────────────────────────────────────────────
            st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
            st.markdown('<div class="section-label">Extraction Results</div>', unsafe_allow_html=True)

            tab1, tab2, tab3, tab4 = st.tabs(["📋  Summary", "📦  Line Items", "✅  Validation", "{ }  Raw JSON"])

            # ── Tab 1: Summary ────────────────────────────────────────────────
            with tab1:
                conf = data.get("confidence_score", 0)
                conf_pct = int(conf * 100)
                conf_color = "#4ade80" if conf >= 0.75 else "#facc15" if conf >= 0.5 else "#f87171"
                dot = "dot-green" if conf >= 0.75 else "dot-yellow" if conf >= 0.5 else "dot-red"

                st.markdown(f"""
                <div class="card card-accent">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.75rem;">
                        <span style="font-size:0.8rem;font-weight:600;color:#e8e4dc;">
                            <span class="status-dot {dot}"></span>Confidence Score
                        </span>
                        <span style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;color:{conf_color};font-weight:700;">{conf_pct}%</span>
                    </div>
                    <div class="conf-bar-bg"><div class="conf-bar-fill" style="width:{conf_pct}%;background:linear-gradient(90deg,#4a52cc,{conf_color});"></div></div>
                    <div style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;color:#4a4e62;margin-top:0.6rem;">{data.get('extraction_notes') or 'No notes'}</div>
                </div>
                """, unsafe_allow_html=True)

                c1, c2 = st.columns(2)
                with c1:
                    st.markdown('<div class="section-label">Invoice Details</div>', unsafe_allow_html=True)

                    def fv(label, val, missing_label="Not found"):
                        display = f'<span class="field-value">{val}</span>' if val is not None else f'<span class="field-value field-missing">— {missing_label}</span>'
                        return f'<div class="field-row"><span class="field-label">{label}</span>{display}</div>'

                    st.markdown(f"""
                    <div class="card">
                        {fv("INVOICE #", data.get("invoice_number"))}
                        {fv("DATE", data.get("invoice_date"))}
                        {fv("DUE DATE", data.get("due_date"))}
                        {fv("PO NUMBER", data.get("po_number"))}
                        {fv("CURRENCY", data.get("currency"))}
                        {fv("PAYMENT TERMS", data.get("payment_terms"))}
                        {fv("PAYMENT METHOD", data.get("payment_method"))}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="section-label" style="margin-top:1rem;">Financial Summary</div>', unsafe_allow_html=True)
                    st.markdown(f"""
                    <div class="card card-success">
                        {fv("SUBTOTAL", fmt_currency(data.get("subtotal"), currency))}
                        {fv("TAX RATE", f"{data.get('tax_rate')}%" if data.get('tax_rate') is not None else None)}
                        {fv("TAX AMOUNT", fmt_currency(data.get("tax_amount"), currency))}
                        {fv("DISCOUNT", fmt_currency(data.get("discount"), currency))}
                        <div class="field-row" style="border-bottom:none;padding-top:0.75rem;">
                            <span class="field-label" style="font-size:0.8rem;color:#a0a4b4;">TOTAL AMOUNT</span>
                            <span class="field-value" style="font-size:1.3rem;color:#4ade80;">{fmt_currency(data.get("total_amount"), currency) or "— Not found"}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                with c2:
                    st.markdown('<div class="section-label">Vendor</div>', unsafe_allow_html=True)
                    vendor = data.get("vendor") or {}
                    st.markdown(f"""
                    <div class="card">
                        {fv("NAME", vendor.get("name"))}
                        {fv("ADDRESS", vendor.get("address"))}
                        {fv("EMAIL", vendor.get("email"))}
                        {fv("PHONE", vendor.get("phone"))}
                        {fv("TAX ID", vendor.get("tax_id"))}
                    </div>
                    """, unsafe_allow_html=True)

                    st.markdown('<div class="section-label" style="margin-top:1rem;">Bill To</div>', unsafe_allow_html=True)
                    bill = data.get("bill_to") or {}
                    st.markdown(f"""
                    <div class="card">
                        {fv("NAME", bill.get("name"))}
                        {fv("ADDRESS", bill.get("address"))}
                        {fv("EMAIL", bill.get("email"))}
                    </div>
                    """, unsafe_allow_html=True)

                    if data.get("notes"):
                        st.markdown('<div class="section-label" style="margin-top:1rem;">Notes</div>', unsafe_allow_html=True)
                        st.markdown(f"""
                        <div class="card">
                            <span style="font-size:0.82rem;color:#6a6e82;">{data["notes"]}</span>
                        </div>
                        """, unsafe_allow_html=True)

            # ── Tab 2: Line Items ─────────────────────────────────────────────
            with tab2:
                items = data.get("line_items") or []
                if items:
                    rows = ""
                    for i, item in enumerate(items, 1):
                        qty = f"{item.get('quantity'):.2f}" if item.get("quantity") is not None else "—"
                        up = fmt_currency(item.get("unit_price"), currency) or "—"
                        amt = fmt_currency(item.get("amount"), currency) or "—"
                        rows += f"""<tr>
                            <td style="color:#4a4e62;font-family:'JetBrains Mono',monospace;font-size:0.7rem;">{i:02d}</td>
                            <td>{item.get('description') or '—'}</td>
                            <td style="text-align:center;">{qty}</td>
                            <td style="text-align:right;">{up}</td>
                            <td>{amt}</td>
                        </tr>"""

                    st.markdown(f"""
                    <div class="card">
                        <table class="line-items-table">
                            <thead>
                                <tr>
                                    <th>#</th>
                                    <th>DESCRIPTION</th>
                                    <th style="text-align:center;">QTY</th>
                                    <th style="text-align:right;">UNIT PRICE</th>
                                    <th>AMOUNT</th>
                                </tr>
                            </thead>
                            <tbody>{rows}</tbody>
                        </table>
                    </div>
                    """, unsafe_allow_html=True)

                    total_items = sum((i.get("amount") or 0) for i in items)
                    st.markdown(f"""
                    <div style="text-align:right;padding:0.5rem 0.75rem;font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#4a4e62;">
                        ITEMS TOTAL: <span style="color:#e8e4dc;font-weight:600;">{fmt_currency(total_items, currency)}</span>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="card" style="text-align:center;padding:3rem;">
                        <span style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#3d4055;">No line items extracted</span>
                    </div>
                    """, unsafe_allow_html=True)

            # ── Tab 3: Validation ─────────────────────────────────────────────
            with tab3:
                pass_c = sum(1 for c in validations if c["status"] == "pass")
                warn_c = sum(1 for c in validations if c["status"] == "warn")
                fail_c = sum(1 for c in validations if c["status"] == "fail")

                sc1, sc2, sc3 = st.columns(3)
                for col, label, count, color, bg in [
                    (sc1, "PASSED", pass_c, "#4ade80", "#0d2a1a"),
                    (sc2, "WARNINGS", warn_c, "#facc15", "#2a200d"),
                    (sc3, "FAILED", fail_c, "#f87171", "#2a0d0d"),
                ]:
                    with col:
                        st.markdown(f"""
                        <div style="background:{bg};border-radius:10px;padding:1rem;text-align:center;border:1px solid {color}22;">
                            <div style="font-size:2rem;font-weight:800;color:{color};">{count}</div>
                            <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:{color};letter-spacing:0.15em;">{label}</div>
                        </div>
                        """, unsafe_allow_html=True)

                st.markdown("<div style='height:1rem'></div>", unsafe_allow_html=True)
                for check in validations:
                    s = check["status"]
                    pill_cls = {"pass": "pill-pass", "warn": "pill-warn", "fail": "pill-fail"}[s]
                    icon = {"pass": "✓", "warn": "⚠", "fail": "✗"}[s]
                    card_cls = {"pass": "card-success", "warn": "card-warning", "fail": "card-error"}[s]
                    st.markdown(f"""
                    <div class="card {card_cls}" style="padding:0.9rem 1.2rem;">
                        <div style="display:flex;justify-content:space-between;align-items:center;">
                            <span style="font-size:0.85rem;">{check["label"]}</span>
                            <span class="validation-pill {pill_cls}">{icon} {check["msg"]}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

            # ── Tab 4: Raw JSON ───────────────────────────────────────────────
            with tab4:
                json_str = json.dumps(data, indent=2, ensure_ascii=False)
                st.markdown(f'<div class="json-block">{json_str}</div>', unsafe_allow_html=True)
                st.download_button(
                    "⬇  Download JSON",
                    data=json_str,
                    file_name=f"invoice_{data.get('invoice_number') or 'extracted'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json",
                )

        except json.JSONDecodeError as e:
            st.markdown(f"""
            <div class="card card-error">
                <div style="font-weight:600;color:#f87171;">JSON Parsing Error</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#6a6e82;margin-top:0.5rem;">{str(e)}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div class="card card-error">
                <div style="font-weight:600;color:#f87171;">API Error</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#6a6e82;margin-top:0.5rem;">{str(e)}</div>
            </div>
            """, unsafe_allow_html=True)
        except Exception as e:
            st.markdown(f"""
            <div class="card card-error">
                <div style="font-weight:600;color:#f87171;">Processing Error</div>
                <div style="font-family:'JetBrains Mono',monospace;font-size:0.75rem;color:#6a6e82;margin-top:0.5rem;">{str(e)}</div>
            </div>
            """, unsafe_allow_html=True)
