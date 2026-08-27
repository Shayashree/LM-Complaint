# Legal Metrology Compliance System Backend

Production-ready backend API service for the **Legal Metrology (Packaged Commodities) Compliance System** built with Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL, and OpenCV.

---

## System Architecture

```mermaid
flowchart TD
    Inspector[Inspector Client] -->|Upload Packaging Photo| UploadAPI[POST /api/scans/upload]
    UploadAPI -->|Save File| Storage[Local Object Storage]
    UploadAPI -->|Estimate Readability & Contrast| CVService[OpenCV Image Service]
    
    Inspector -->|Run Compliance Audit| InspectAPI[POST /api/inspections]
    InspectAPI -->|Raw Text Extract| OCRService[PaddleOCR / Mock Provider]
    OCRService -->|Text & Coordinates| DeclService[Declaration Extractor]
    DeclService -->|Map Structured Keys| RuleEngine[Rule Engine]
    RuleEngine -->|Validate Declarations| CompEngine[Compliance Engine]
    
    CompEngine -->|Create Infraction Case| Violations[Violations Table]
    CompEngine -->|Link BBoxes & Crops| Evidence[Evidence Management]
    
    Inspector -->|Officer Verdict| SignOffAPI[POST /api/inspections/:id/verify]
    Supervisor[Supervisor Client] -->|Approve Case| SupervisorAPI[POST /api/inspections/:id/supervisor-review]
    
    SupervisorAPI -->|Compile Findings Report| ReportService[ReportLab PDF Compiler]
    ReportService -->|Download Document| ReportsStorage[Reports Storage]
```

---

## Directory Structures
*   `app/api/`: Endpoint route modules (Auth, Scans, Inspections, Violations, Reports, Rules, Dashboard, Audit Logs).
*   `app/models/`: Database schemas (SQLAlchemy) mapping compliance history.
*   `app/services/`: Image preprocessing, OCR providers, and rules engine.
*   `app/core/`: Security and RBAC permission middleware.
*   `tests/`: Unit testing for engines.

---

## Local Setup & Run

### Prerequisite: Setup Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Configure environment
Copy `.env.example` to `.env` and fill database connection details:
```bash
Copy-Item .env.example .env
```

### Seeding Sandbox Database
To seed the database with initial roles, sample rules, and inspections history for Parle-G, Surf Excel, and Haldiram's:
```bash
python -m app.db.seed
```

### Running Backend
```bash
uvicorn app.main:app --reload
```
Swagger UI will be available at **`http://localhost:8000/docs`**.

---

## Running Automated Tests
```bash
pytest -v
```

---

## Docker Compose Setup
To run the complete system (FastAPI app + PostgreSQL database) as container services:
```bash
docker compose up --build
```

---

## Sandbox Demo Credentials
*   **Inspector**: `inspector@example.com` / `Password123` (Employee ID: `LMI-88902`)
*   **Supervisor**: `supervisor@example.com` / `Password123` (Employee ID: `LMS-77102`)
*   **Rule Administrator**: `ruleadmin@example.com` / `Password123` (Employee ID: `LMA-44390`)
*   **Auditor**: `auditor@example.com` / `Password123` (Employee ID: `LMA-99021`)
