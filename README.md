# ShadowWatch

ShadowWatch is an offline supervisory analytics platform for SOC assessment.

## Tech Stack

- Frontend: React
- Backend: FastAPI
- Database: PostgreSQL
- Analytics: Python, Pandas, Scikit-learn
- NLP: TF-IDF and Cosine Similarity

## Setup

### Backend

cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r ../requirements.txt

Create .env from .env.example.

Run:

uvicorn main:app --reload

API contracts, import commands and tests: [Backend handoff](docs/backend_api.md).
Workplan verification: [Deepa backend checklist](docs/deepa_backend_verification.md).

### Frontend

cd frontend
npm install
npm run dev

### Database

Create PostgreSQL database and run:

psql -U shadowwatch_user -d shadowwatch_db -h localhost -f database/schema.sql
