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
