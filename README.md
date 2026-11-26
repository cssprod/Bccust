# BC Parenting Log

Local-first evidence log for BC family law custody cases. Paste your text conversation, get an AI analysis against the BC Family Law Act, and export court-ready exhibits (PDF/CSV/Excel). Runs 100% offline via Ollama — nothing leaves your machine.

## Setup

```bash
# 1. Install Python dependencies
pip install -r requirements.txt

# 2. Install Ollama (https://ollama.com) and pull a model
ollama pull llama3.1:8b

# 3. Start Ollama
ollama serve

# 4. Run the app
cd bc_custody_log
streamlit run app.py
```

Open http://localhost:8501

## How it works

1. **Case setup** — enter your case name and court
2. **Input** — paste raw texts or upload a `.txt`/`.csv` export (iMessage, WhatsApp, SMS formats supported)
3. **Analyze** — Ollama analyzes chunks against the BC Family Law Act (s. 1, 37, 41, 61) and returns structured infractions with verbatim quotes
4. **Review** — editable evidence table with severity, category, verbatim quote, and objective court summary
5. **Export** — PDF, CSV, or Excel with exhibit numbers and legal disclaimer

## Privacy

- Runs entirely on your computer via Ollama
- No text messages, names, or case details leave your machine
- Optional anonymizer redacts real names to `[Applicant]`/`[Respondent]`/`[Child]` before AI processing

## Legal disclaimer

This tool organizes communication records for informational and clerical preparation only. It does not provide legal advice, and users must retain original unedited device screenshots to authenticate evidence for BC Provincial or Supreme Court.
