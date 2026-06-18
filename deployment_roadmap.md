# Deployment Roadmap — Women's Health Survey

## 0. Prerequisites
- Python 3.11+
- PostgreSQL database (local or cloud)
- Git repository pushed to a Git provider (GitHub/GitLab/Bitbucket)

---

## 1. Local Development Setup
```bash
git clone <repo-url> && cd sample
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # fill DATABASE_URL, SECRET_KEY, PORT
uvicorn main:app --reload
```

## 2. Database Migrations
Tables are auto-created on startup via `models.database.init_db()`.
For production, use Alembic:
```bash
alembic init alembic
alembic revision --autogenerate -m "init"
alembic upgrade head
```

## 3. Render Deployment (render.yaml)
Service type: **Web Service**  
Plan: **Free**  
Build: `pip install -r requirements.txt`  
Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Database
Service type: **PostgreSQL**  
Plan: **Free**  
The `DATABASE_URL` env var is injected automatically via `fromDatabase`.

## 4. Environment Variables
| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (injected by Render) |
| `SECRET_KEY` | Flask/FastAPI session secret, auto-generated on Render |
| `PORT` | Port number (Render provides this automatically) |

## 5. CI/CD
Render auto-deploys on push to the default branch.  
Optional: add `render-build-hook` GitHub Action for pre-deploy tests.

## 6. Post-Deploy Checklist
- [ ] `/` returns 200
- [ ] `/survey/nurse` loads without 500
- [ ] Form submission writes to Postgres
- [ ] `/admin` shows submitted surveys

## 7. Future Enhancements
- Alembic migrations for schema changes
- Email notifications on survey submit
- Export to CSV from `/admin`
- Rate limiting / CAPTCHA for survey spam protection
