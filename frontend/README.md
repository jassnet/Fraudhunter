# Frontend (Next.js)

Dashboard UI for the Fraud Checker API.

## Run
```
cd frontend
npm install
npm run dev
```
Default base URL: `http://localhost:8000` (can override with `NEXT_PUBLIC_API_URL`).  
You can also start both frontend + backend together from the repo root with `python dev.py`.

## Available pages
- Dashboard: `/`
- Suspicious clicks: `/suspicious/clicks`
- Suspicious conversions: `/suspicious/conversions`
- Settings: `/settings`
