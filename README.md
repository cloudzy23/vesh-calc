# vesh-calc

Simple Flask-based math/graphing app (SymPy + NumPy + Plotly).

## Deploy notes

- Language: Python 3.11 (or 3.10)
- Build command: `pip install -r requirements.txt`
- Start command (Render/production): `gunicorn app:app --bind 0.0.0.0:$PORT --workers 1 --timeout 120`

If deploy fails during `pip install`, ensure `requirements.txt` contains valid package names (no duplicates or concatenated tokens). This repo includes a cleaned `requirements.txt`.

## Local run

Install deps and run:

```powershell
python -m pip install -r requirements.txt
python app.py
```

The app will run on http://localhost:5000 by default.

## Troubleshooting
- If the worker crashes with OOM, upgrade the instance size on Render or reduce memory usage.
- Check Render build logs for pip errors if installation fails.
veshcalc - simple function plotter (Flask + Plotly)

Requirements
- Python 3.8+
- pip install flask sympy numpy plotly

Run
1. pip install flask sympy numpy plotly
2. python app.py
3. Open http://localhost:5000

Project structure
- app.py - Flask entrypoint
- templates/index.html - HTML UI
- static/script.js - frontend logic
- static/style.css - styles

Notes
- Supports cartesian and basic parametric expressions. Implicit plotting returns a grid for contour plotting.

Examples to try
- sin(x)
- x^2 - 4  (quadratic with roots at x = -2 and 2)
- y=cos(x)
- x=cos(t), y=sin(t)  (unit circle parametric)
- x^2+y^2=1  (implicit circle)

Deploying to Vercel (recommended)
1. Push this repository to GitHub.
2. In your GitHub repository settings, add a secret named `VERCEL_TOKEN` with a Vercel Personal Token (create one at https://vercel.com/account/tokens).
3. The included GitHub Actions workflow `.github/workflows/vercel-deploy.yml` will run on pushes to `main` (or `master`) and deploy to Vercel.

Manual deploy using Vercel CLI (local)
- Install Vercel CLI: `npm i -g vercel` or run via `npx vercel`.
- From the project root run `vercel` and follow the interactive prompts, or `vercel --prod` to push to production.

Notes on availability
- Once deployed to Vercel, the site will be reachable from any device with a browser. Vercel runs the Python serverless function for `/api/app.py` and serves the frontend.
- Consider hosting the frontend as static files on Vercel and keep `/api` for compute if you observe cold-starts or slow responses.
