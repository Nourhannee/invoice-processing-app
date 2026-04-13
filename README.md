# InvoiceIQ — Intelligent Invoice Processing System

An AI-powered Streamlit app that processes invoices (PDF, images, text) and extracts structured financial data using Groq (Llama model).

---

## Features
- Upload PDF, PNG, JPG, WEBP, or TXT invoices
- AI extraction: invoice number, dates, vendor, buyer, line items, totals, tax, discounts
- Validation checks: required fields, math consistency, date logic
- Structured JSON export
- Confidence scoring per document

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Tesseract OCR (required for image uploads)
- Windows: install from https://github.com/tesseract-ocr/tesseract/releases
- macOS: `brew install tesseract`
- Linux: `sudo apt install tesseract-ocr`

### 3. Set your Groq API key
```bash
export GROQ_API_KEY=your_groq_api_key_here
```
Or create `.streamlit/secrets.toml`:
```toml
GROQ_API_KEY = "your_groq_api_key_here"
```

### 3. Run the app
```bash
streamlit run app.py
```

---

## Architecture

```
Invoice Upload (PDF/Image/Text)
        │
        ▼
  File Processor
  ├── PDF → PyPDF2 text extraction (or base64 for scanned)
  ├── Image → text extraction (OCR not implemented, text-only for Groq)
  └── Text → direct string pass
        │
        ▼
  Groq llama-3.3-70b-versatile (via Groq API)
  └── Structured JSON extraction via prompt engineering
        │
        ▼
  Validation Engine
  ├── Required field checks
  ├── Math consistency (line items → subtotal → total)
  └── Date logic validation
        │
        ▼
  Streamlit UI
  ├── Summary view
  ├── Line items table
  ├── Validation report
  └── Raw JSON + download
```

---

## Extracted Fields

| Category | Fields |
|----------|--------|
| Invoice | Number, Date, Due Date, PO Number, Currency |
| Vendor | Name, Address, Email, Phone, Tax ID |
| Bill To | Name, Address, Email |
| Financials | Subtotal, Tax Rate, Tax Amount, Discount, Total |
| Line Items | Description, Quantity, Unit Price, Amount |
| Metadata | Payment Terms, Payment Method, Notes |
