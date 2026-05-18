# LegalPlain — AI-Powered Legal Document Simplifier

> Simplifies complex legal documents into plain language with risk highlighting and concise summaries.
> **Live at:** [legalplain.onrender.com](https://legalplain.onrender.com)

---

## What it does

Legal texts — contracts, NDAs, policies, compliance notices — are dense and hard to understand for non-experts. Misreading even one clause can lead to financial loss or legal disputes.

LegalPlain solves this by:
- Converting legal jargon into clear, plain-English explanations
- Generating structured summaries of obligations, deadlines, and risks
- Highlighting clauses with a colour-coded risk system (Red / Yellow / Green)
- Processing documents with a **privacy-first approach** — no files are stored after analysis

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | HTML, CSS, JavaScript |
| NLP / AI | Natural Language Processing (clause analysis, summarisation) |
| Deployment | Render |
| Security | Zero document retention, encrypted login data |

---

## Key Features

- **Plain Language Simplification** — breaks down legal jargon into everyday language
- **Risk Highlighting**
  - 🔴 Red → High-risk clauses
  - 🟡 Yellow → Moderate risk
  - 🟢 Green → Favourable or safe terms
- **Concise Summaries** — structured output covering obligations, deadlines, and opportunities
- **PDF Upload Support** — results available within minutes of upload
- **Privacy by Design** — documents discarded after processing; only login data retained securely

---

## Target Users

- **Individuals** — leases, employment offers, service contracts
- **Startups & SMEs** — vendor contracts, NDAs, compliance documents
- **NGOs & Enterprises** — large-scale contract review with confidentiality

---

## Running Locally

```bash
git clone https://github.com/kirti734/legaldocumentsummarizer
cd legaldocumentsummarizer
pip install -r requirements.txt
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## Roadmap

- [ ] Multilingual support
- [ ] Interactive Q&A (context-aware answers about uploaded documents)
- [ ] Industry-specific adaptations (healthcare, real estate, finance)

---

## Live Demo

Try it now → [legalplain.onrender.com](https://legalplain.onrender.com)
