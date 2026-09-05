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
pip install -r requirements.txt

Create .env from .env.example.

Run:

uvicorn main:app --reload

### Frontend

cd frontend
npm install
npm run dev

### Database

Create PostgreSQL database and run:

psql -U shadowwatch_user -d shadowwatch_db -h localhost -f database/schema.sql
