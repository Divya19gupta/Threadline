# 📋 Threadline

### Your job hunt, tracked.

**Threadline** is an AI-powered job application tracker that turns job postings and Gmail replies into a structured, automatically updated application pipeline.

> 🤖 Extract the job → 📧 read the reply → 🧠 classify the outcome → ⚠️ flag uncertainty
> 
---

## 🎯 Why this project?

Threadline started as a simple job tracker, but became a practical exercise in building an **end-to-end AI system that knows when it might be wrong**.

The interesting part isn't just:

> *"Can AI classify an email?"*

It's:

> **"Can AI automate the boring parts without silently making bad decisions for me?"**

---

## ✨ What it does

**1. Paste a job posting**  
A LangGraph agent extracts the company, role, recruiter details, and application link.

**2. Track everything locally**  
Applications are stored in a local SQLite database with full CRUD support.

**3. Check Gmail for updates**  
Threadline searches Gmail and extracts the full email body from the MIME structure (`text/plain` + `text/html`).

**4. Classify the outcome**  
A fine-tuned DistilBERT model classifies emails as:

`interview` · `rejected` · `test` · `offer`

**5. Don't trust the model blindly**  
Status updates only happen when confidence ≥ **0.35**. Otherwise → `needs review`.

---

## 🧠 Architecture

```text
                  ┌──────────────────┐
                  │    Streamlit     │
                  │       UI         │
                  └────────┬─────────┘
                           │
                  ┌────────▼─────────┐
                  │  Backend Logic   │
                  └─────┬─────┬──────┘
                        │     │
              ┌─────────▼┐   └─────────────┐
              │  SQLite  │                 │
              └──────────┘        ┌────────▼────────┐
                                  │   AI Services   │
                                  │                 │
                                  │ LangGraph +     │
                                  │ Gemini +        │
                                  │ DistilBERT      │
                                  └────────┬────────┘
                                           │
                                  ┌────────▼────────┐
                                  │  Gmail API      │
                                  │ OAuth + Search  │
                                  └─────────────────┘
```

### 🔹 Extraction Agent

A **two-node LangGraph**:

```text
extract_fields → conditional edge → save_to_db
```

Gemini extracts structured job information. If extraction fails, nothing is written to the database.

### 🔹 Status Classifier

Fine-tuned **DistilBERT** trained on ~**68 hand-labeled emails**.

```text
Email
  ↓
DistilBERT
  ↓
Prediction + confidence
  ↓
confidence ≥ 0.35 ?
  ├── YES → update status
  └── NO  → needs review
```

Unambiguous phrases such as `"unfortunately, we will not be moving forward"` use deterministic overrides instead of the model.

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| Agents | LangGraph + Google Gemini (`gemini-2.5-flash`) |
| Classifier | HuggingFace Transformers + DistilBERT + PyTorch |
| Evaluation | Custom eval harness + hand-verified ground truth |
| Backend | Python + SQLite |
| Frontend | Streamlit |
| Email | Gmail API + OAuth 2.0 + BeautifulSoup4 |

**Extraction accuracy:** `80% field-level`  
**Classifier dataset:** `~68 labeled emails`  
**Random baseline:** `~25%` for 4 classes

---

## 🔐 Privacy by Design

Threadline is **local-first**.

- 📦 Applications, CVs/cover letters, OAuth token → local machine
- 🧠 Raw email content → processed in memory only
- 💾 Only the derived status label is persisted
- 🔑 Gmail scope → `gmail.readonly`
- 🚫 Cannot send, delete, or modify emails
- 🌐 External services → Gemini API + authorized Gmail API

This follows the core GDPR principle of **data minimization (Art. 5(1)(c))**.

---

## ⚠️ Honest Limitations

- **Small training set:** ~68 emails → not enough for highly confident predictions on ambiguous text.
- **No `not_relevant` class:** keyword-based relevance filtering is currently used as a stopgap.
- **Keyword-based Gmail search:** can surface irrelevant results; semantic retrieval is a future improvement.
- **No email idempotency:** Gmail checks re-process emails rather than tracking processed message IDs.
- **No automatic application detection:** applications must currently be added explicitly.
- **Local-only:** no hosted/multi-user version.

These limitations are also why the confidence gate and deterministic overrides exist.

---

## 🔮 What's Next?

- [ ] Add `not_relevant` training class
- [ ] Track processed email IDs + `accept` / `dismiss`
- [ ] Add embeddings-based semantic email retrieval
- [ ] Detect new applications from confirmation emails
- [ ] Hosted multi-user version with **FastAPI + Postgres + OAuth verification**

---

## 🚀 Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd Threadline

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up your Gemini API key

Create `.env`:

```env
GOOGLE_API_KEY=your_key_here
```

### 3. Set up Gmail API access

1. Create a Google Cloud project
2. Enable the Gmail API
3. Configure OAuth consent and add yourself as a test user
4. Create OAuth credentials of type **Desktop app**
5. Save them as `data/credentials.json`

The first time you use **"Check Gmail for updates"**, a browser window will prompt you to authorize access. A `token.json` will then be saved locally.

> **Note:** Unverified apps have refresh tokens that expire every 7 days. This is a Google restriction, not a bug.

### 4. Run

```bash
streamlit run app.py
```

---
### 🤖 Illustration

<img width="1409" height="768" alt="Screenshot 2026-08-23 at 3 54 49 PM" src="https://github.com/user-attachments/assets/1203b1b1-8be3-402a-8c2d-5c36f21bd3b0" />

---
### 📌 Built with

`Python` · `LangGraph` · `Gemini` · `DistilBERT` · `PyTorch` · `Streamlit` · `SQLite` · `Gmail API`
