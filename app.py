from flask import Flask, render_template, request, jsonify
import numpy as np
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication_application

transformations = (standard_transformations + (implicit_multiplication_application,))

# whitelist of allowed names for safety
from sympy import sin, cos, tan, asin, acos, atan, exp, log, sqrt, pi, E, Abs
ALLOWED_NAMES = {
    'sin': sin, 'cos': cos, 'tan': tan,
    'asin': asin, 'acos': acos, 'atan': atan,
    'exp': exp, 'log': log, 'sqrt': sqrt, 'pi': pi, 'E': E, 'Abs': Abs
}

app = Flask(__name__)


def safe_parse(expr_str):
    # Remove leading 'y=' if present
    expr_str = expr_str.strip()
    if expr_str.startswith('y='):
        expr_str = expr_str[2:]
    return expr_str


def safe_parse_expr(expr_text, local_dict=None):
    """Parse expression using sympy.parse_expr with a whitelist to avoid executing unsafe code.
    Returns a sympy expression or raises an exception.
    """
    if local_dict is None:
        local_dict = {}
    # merge allowed names
    names = {**ALLOWED_NAMES, **local_dict}
    # replace common ^ notation
    expr_text = expr_text.replace('^', '**')
    return parse_expr(expr_text, local_dict=names, transformations=transformations)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evaluate', methods=['POST'])
def evaluate():
    data = request.get_json() or {}
    expr = data.get('expression', '')
    xmin = float(data.get('xmin', -10))
    xmax = float(data.get('xmax', 10))
    points = int(data.get('points', 500))
    mode = data.get('mode', 'cartesian')  # cartesian or parametric or implicit

    expr = safe_parse(expr)
    expr = expr.replace('θ', 'theta').replace('Θ', 'theta')
    expr = expr.replace('π', 'pi')

    import re
    ineq_match = re.search(r'(<=|>=|<|>)', expr)

    try:
        # Parametric: x=..., y=... or two comma-separated expressions
        if mode == 'parametric' or (',' in expr and ('x=' in expr and 'y=' in expr or ('(' in expr and ')' in expr and expr.count(',')==1))):
            parts = [p.strip() for p in expr.split(',')]
            if '=' in parts[0]:
                xpart = parts[0].split('=', 1)[1]
                ypart = parts[1].split('=', 1)[1]
            else:
                xpart, ypart = parts[0], parts[1]
            try:
                t = sp.symbols('t')
                xsym = safe_parse_expr(xpart, {'t': t})
                ysym = safe_parse_expr(ypart, {'t': t})
            except Exception as e:
                return jsonify({'error': f'Parse error in parametric parts: {e}'}), 400
            tvals = np.linspace(xmin, xmax, points)
            xfunc = sp.lambdify(t, xsym, modules=['numpy'])
            yfunc = sp.lambdify(t, ysym, modules=['numpy'])
            xv = xfunc(tvals)
            yv = yfunc(tvals)
            xv = np.array(xv, dtype=float).tolist()
            yv = np.array(yv, dtype=float).tolist()
            return jsonify({'x': xv, 'y': yv, 'expr': expr, 'mode': 'parametric'})

        # Surface (3D): z = f(x,y)
        if 'z=' in expr or (('=' in expr) and ('z' in expr) and ('x' in expr or 'y' in expr)):
            left, right = expr.split('=', 1)
            zexpr = right
            x, y = sp.symbols('x y')
            try:
                zsym = safe_parse_expr(zexpr, {'x': x, 'y': y})
            except Exception as e:
                return jsonify({'error': f'Parse error in surface expression: {e}'}), 400
            zfunc = sp.lambdify((x, y), zsym, modules=['numpy'])
            xv = np.linspace(xmin, xmax, int(np.sqrt(points)))
            yv = np.linspace(xmin, xmax, int(np.sqrt(points)))
            X, Y = np.meshgrid(xv, yv)
            Z = zfunc(X, Y)
            try:
                Z = np.array(Z, dtype=float)
            except Exception:
                Z = np.array(Z)
            return jsonify({'X': X.tolist(), 'Y': Y.tolist(), 'Z': Z.tolist(), 'expr': expr, 'mode': 'surface'})

        # Polar: r = f(theta) or r = f(t)
        if expr.startswith('r=') or ' r(' in expr or ('theta' in expr and 'r' in expr):
            if expr.startswith('r='):
                rexpr = expr.split('=', 1)[1]
            else:
                rexpr = expr
            t = sp.symbols('t')
            try:
                rexpr = rexpr.replace('theta', 't')
                rsym = safe_parse_expr(rexpr, {'t': t})
            except Exception as e:
                return jsonify({'error': f'Parse error in polar expression: {e}'}), 400
            tvals = np.linspace(xmin, xmax, points)
            rfunc = sp.lambdify(t, rsym, modules=['numpy'])
            rval = rfunc(tvals)
            xv = np.array(rval) * np.cos(tvals)
            yv = np.array(rval) * np.sin(tvals)
            return jsonify({'x': xv.tolist(), 'y': yv.tolist(), 'expr': expr, 'mode': 'polar'})

        # Inequalities
        if ineq_match and ('x' in expr or 'y' in expr):
            op = ineq_match.group(1)
            parts = re.split(r'(<=|>=|<|>)', expr, maxsplit=1)
            left = parts[0]
            op = parts[1]
            right = parts[2]
            x, y = sp.symbols('x y')
            try:
                f = safe_parse_expr(f'({left})-({right})', {'x': x, 'y': y})
            except Exception as e:
                return jsonify({'error': f'Parse error in inequality: {e}'}), 400
            fx = sp.lambdify((x, y), f, modules=['numpy'])
            xv = np.linspace(xmin, xmax, int(np.sqrt(points)))
            yv = np.linspace(xmin, xmax, int(np.sqrt(points)))
            X, Y = np.meshgrid(xv, yv)
            Z = fx(X, Y)
            if op == '>':
                mask = (Z > 0).astype(int)
            elif op == '<':
                mask = (Z < 0).astype(int)
            elif op == '>=':
                mask = (Z >= 0).astype(int)
            elif op == '<=':
                mask = (Z <= 0).astype(int)
            else:
                mask = (Z != 0).astype(int)
            return jsonify({'X': X.tolist(), 'Y': Y.tolist(), 'Z': mask.tolist(), 'expr': expr, 'mode': 'inequality', 'op': op})

        # Implicit (contour): equations involving x and y
        if '=' in expr and 'x' in expr and 'y' in expr and not expr.startswith('y='):
            left, right = expr.split('=', 1)
            x, y = sp.symbols('x y')
            try:
                f = safe_parse_expr(f'({left})-({right})', {'x': x, 'y': y})
            except Exception as e:
                return jsonify({'error': f'Parse error in implicit expression: {e}'}), 400
            fx = sp.lambdify((x, y), f, modules=['numpy'])
            xv = np.linspace(xmin, xmax, int(np.sqrt(points)))
            yv = np.linspace(xmin, xmax, int(np.sqrt(points)))
            X, Y = np.meshgrid(xv, yv)
            Z = fx(X, Y)
            return jsonify({'X': X.tolist(), 'Y': Y.tolist(), 'Z': Z.tolist(), 'expr': expr, 'mode': 'implicit'})

        # Equations in x only: solve for roots
        if '=' in expr and 'x' in expr and 'y' not in expr:
            left, right = expr.split('=', 1)
            x = sp.symbols('x')
            try:
                left_sym = safe_parse_expr(left, {'x': x})
                right_sym = safe_parse_expr(right, {'x': x})
            except Exception as e:
                return jsonify({'error': f'Parse error in equation: {e}'}), 400
            eq = sp.Eq(left_sym, right_sym)
            sols = sp.solve(eq, x)
            numeric_roots = []
            for s in sols:
                try:
                    val = complex(s.evalf())
                    if abs(val.imag) < 1e-9:
                        numeric_roots.append(float(val.real))
                    else:
                        numeric_roots.append(None)
                except Exception:
                    numeric_roots.append(None)
            # also sample f(x)=left-right
            try:
                fexpr = left_sym - right_sym
                f = sp.lambdify(x, fexpr, modules=['numpy'])
                xv = np.linspace(xmin, xmax, points)
                yv = f(xv)
                yv = np.array(yv, dtype=complex)
                yv = [float(v.real) if abs(v.imag) < 1e-9 else None for v in yv]
                return jsonify({'x': xv.tolist(), 'y': yv, 'expr': expr, 'mode': 'equation', 'roots': numeric_roots})
            except Exception:
                return jsonify({'expr': expr, 'mode': 'equation', 'roots': numeric_roots})

        # Default: cartesian y = f(x)
        x = sp.symbols('x')
        try:
            expr_sym = safe_parse_expr(expr, {'x': x})
        except Exception as e:
            return jsonify({'error': f'Parse error: {e}', 'expr': expr}), 400

        roots = None
        try:
            if ('=' not in expr) and ('x' in expr) and ('y' not in expr):
                sols = sp.solve(sp.Eq(expr_sym, 0), x)
                numeric_roots = []
                for s in sols:
                    try:
                        val = complex(s.evalf())
                        if abs(val.imag) < 1e-9:
                            numeric_roots.append(float(val.real))
                        else:
                            numeric_roots.append(None)
                    except Exception:
                        numeric_roots.append(None)
                roots = numeric_roots
        except Exception:
            roots = None

        func = sp.lambdify(x, expr_sym, modules=['numpy'])
        xv = np.linspace(xmin, xmax, points)
        yv = func(xv)
        xv = np.array(xv, dtype=float).tolist()
        yv = np.array(yv, dtype=complex)
        yv = [float(v.real) if abs(v.imag) < 1e-9 else None for v in yv]
        resp = {'x': xv, 'y': yv, 'expr': expr, 'mode': 'cartesian'}
        if roots is not None:
            resp['roots'] = roots
        return jsonify(resp)

    except Exception as e:
        return jsonify({'error': str(e), 'expr': expr}), 400


@app.route('/algebra', methods=['POST'])
def algebra():
    data = request.get_json() or {}
    action = data.get('action')
    expr = data.get('expr', '')
    expr = safe_parse(expr)
    try:
        x = sp.symbols('x')
        if action == 'simplify':
            e = safe_parse_expr(expr, {'x': x})
            res = sp.simplify(e)
            return jsonify({'result': str(res)})
        elif action == 'factor':
            e = safe_parse_expr(expr, {'x': x})
            res = sp.factor(e)
            return jsonify({'result': str(res)})
        elif action == 'expand':
            e = safe_parse_expr(expr, {'x': x})
            res = sp.expand(e)
            return jsonify({'result': str(res)})
        elif action == 'derivative':
            e = safe_parse_expr(expr, {'x': x})
            res = sp.diff(e, x)
            return jsonify({'result': str(res)})
        elif action == 'solve':
            e = safe_parse_expr(expr, {'x': x})
            sols = sp.solve(sp.Eq(e, 0), x)
            sols_eval = []
            for s in sols:
                try:
                    sols_eval.append(str(s))
                except Exception:
                    sols_eval.append(None)
            return jsonify({'result': sols_eval})
        else:
            return jsonify({'error': 'Unknown action'}), 400
    except Exception as e:
        return jsonify({'error': f'Algebra error: {e}'}), 400


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    # In production use a WSGI server (gunicorn). Keep debug disabled when
    # running directly to avoid exposing Werkzeug debug pages.
    app.run(host='0.0.0.0', port=port, debug=False)

