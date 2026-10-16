# 📄 AI Resume Analyzer & Job Matcher

A privacy-focused, offline-capable web application that analyzes resumes (PDF, DOCX, TXT), parses structured candidate data, matches qualifications against job descriptions, and provides actionable improvement feedback with transparent scoring.

---

## 🚀 Key Features

1. **Multi-Format Document Extraction**
   - Extracts clean text from **PDF** (`pdfplumber`), **Word** (`python-docx`), and **Plain Text** (`.txt`) files.
   - Robust error handling for corrupt files, empty uploads, and scanned PDFs lacking a text layer.
   - Zero persistent disk storage — all processing happens in-memory with session safety.

2. **Intelligent Resume Parsing**
   - **Candidate Profile:** Name (best-effort heuristic), email, phone, and links (LinkedIn, GitHub, Portfolio).
   - **Section Detection:** Professional summary, technical skills, experience, education, and projects.
   - **Experience & Metrics:** Extracts roles, date intervals, bullet points, and estimates total years of professional experience.
   - Missing fields gracefully return `"Not found"` rather than failing.

3. **Curated Skills Taxonomy & Alias Normalization**
   - Categorized skills catalog (`config/skills.json`) covering:
     - *Programming Languages*
     - *Frameworks & Libraries*
     - *Databases*
     - *Cloud & DevOps*
     - *Data & Machine Learning*
     - *Soft Skills*
     - *Tools*
   - Handles abbreviations and aliases (e.g., `k8s` → `Kubernetes`, `js` → `JavaScript`, `reactjs` → `React`).
   - Boundary-safe matching preventing substring confusion (e.g., `Java` vs `JavaScript`, `C++`, `Go`).

4. **Transparent Job Description Matching**
   - Matches candidate qualifications against target job descriptions.
   - Extracts frequent keywords and non-dictionary terms.
   - Categorizes matched skills and identified skill gaps.
   - Computes section-level alignment for skills, experience, and education.

5. **Actionable Suggestions & Weak-Signal Detection**
   - **Keyword Gaps:** Prioritized guidance citing exact frequency of missing terms in the JD.
   - **Quantified Achievements:** Audits experience bullets for measurable metrics (percentages, numbers, currencies).
   - **Passive Phrasing:** Identifies weak phrases (`"was responsible for"`, `"assisted with"`) and recommends high-impact action verbs.
   - **Cliché Buzzwords:** Flags overused corporate jargon (`"synergy"`, `"go-getter"`, `"team player"`).
   - **Contact & Summary Audit:** Flags missing links, phone numbers, or excessively long/short summaries.

6. **Interactive Dashboard & Multi-Format Export**
   - Clean Streamlit dashboard with tabs: *Overview*, *Keywords & Skills*, *Actionable Suggestions*, and *Extracted Data*.
   - Visual category distribution bar chart.
   - One-click downloads for **JSON**, **Markdown**, and **Plain Text** analysis reports.

---

## 🧮 How the Match Score is Calculated

The overall match score (0–100%) uses a transparent, explainable formula:

$$\text{Overall Score} = (0.50 \times \text{Skills Score}) + (0.35 \times \text{Experience Score}) + (0.15 \times \text{Education Score})$$

### Component Breakdown:
1. **Technical Skills Score (50% weight):**
   $$\text{Skills Score} = \left(\frac{\text{Matched JD Skills}}{\text{Total JD Skills}}\right) \times 100$$
2. **Experience Relevance Score (35% weight):**
   - Presence of structured work experience section (40 pts)
   - Years of experience alignment with senior/mid requirements (up to 25 pts)
   - Ratio of required JD terms contextualized in work experience (up to 35 pts)
3. **Education Alignment Score (15% weight):**
   - Verification of recognized degrees (Bachelor's, Master's, Ph.D., Associate) (60 pts)
   - Alignment with required degree level mentioned in the JD (up to 40 pts)

*When no job description is supplied, the application displays pure resume intelligence without generating an arbitrary match score.*

---

## 📂 Project Structure

```
resume-analyzer/
├── app.py                      # Streamlit UI application
├── requirements.txt            # Pinned dependencies
├── README.md                   # Project documentation
├── .gitignore                  # Git ignore rules
├── config/
│   └── skills.json             # Categorized skills catalog with aliases
├── src/
│   ├── __init__.py             # Package marker
│   ├── extractor.py            # PDF, DOCX, and TXT text extraction
│   ├── parser.py               # Metadata, contact, section, and experience parser
│   ├── skills.py               # Skill catalog, regex matching, alias normalization
│   ├── matcher.py              # JD matching engine & transparent scoring
│   ├── suggestions.py          # Weak-signal audits and tailored advice
│   ├── report.py               # JSON, Markdown, and TXT report generators
│   └── utils.py                # Logger, file path resolution, text cleaning
└── tests/
    ├── test_extractor.py       # Extraction & error handling tests
    ├── test_parser.py          # Section & metadata parsing tests
    ├── test_skills.py          # Skill catalog & alias matching tests
    ├── test_matcher.py         # Matcher edge cases & suggestion tests
    └── sample_data/            # Sample test assets
        ├── sample_resume.txt
        ├── sample_resume.docx
        ├── sample_resume.pdf
        └── sample_job_description.txt
```

---

## 🛠️ Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.10 and 3.11+)
- `pip` package manager

### 1. Clone & Navigate
```bash
git clone https://github.com/ANafeesh/AI-Resume-Analyzer.git
cd "Resume Analyzer Project"
```

### 2. Create and Activate Virtual Environment
**On Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Launch the Streamlit App
```bash
streamlit run app.py
```
Open your browser to `http://localhost:8501`.

---

## 🧪 Running Unit Tests

Run the full pytest suite:

```bash
pytest
```

For verbose output with execution timing:
```bash
pytest -v
```

All 25 unit tests cover:
- Text extraction across PDF, DOCX, and TXT formats.
- Handling empty streams, corrupted files, and unsupported extensions.
- Contact extraction (Email, Phone, LinkedIn, GitHub) and `"Not found"` fallbacks.
- Multi-line education entries and date-interval deductions.
- Case-insensitivity and alias normalization (`k8s` → `Kubernetes`).
- Word-boundary isolation (`Java` does not match `JavaScript`).
- Scoring edge cases: empty JD, zero matches, and perfect alignment.

---

## 🖼️ Screenshots

*(Place application dashboard screenshots here)*

| Overview Dashboard | Keywords & Gap Analysis |
| :---: | :---: |
| ![Dashboard Overview Placeholder](docs/screenshots/overview.png) | ![Keywords Placeholder](docs/screenshots/keywords.png) |

| Actionable Suggestions | Extracted Profile |
| :---: | :---: |
| ![Suggestions Placeholder](docs/screenshots/suggestions.png) | ![Extracted Data Placeholder](docs/screenshots/extracted.png) |

---

## 📄 License
MIT License. Free for personal and commercial use.
