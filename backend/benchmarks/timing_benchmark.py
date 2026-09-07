import random
import statistics
import sys
import time
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from pyomo.environ import (  # noqa: E402
    ConcreteModel, Set, Var, Constraint, Objective,
    Binary, NonNegativeIntegers, minimize, SolverFactory,
)
from data_input import build_input_data
from model_milp import solve_balanced, solve_model, is_solved, SOLVER_NAMES

N_REPEATS = 3
TIME_LIMIT_SPARSE = 60   # igual que el limite por defecto de /solve
TIME_LIMIT_DENSE = 180

INSTANCE_SPECS = {
    "I1": dict(n_tfg=8, n_docentes=8, n_dias=2, n_aulas=2, hora_fin="13:00"),
    "I2": dict(n_tfg=14, n_docentes=12, n_dias=3, n_aulas=2, hora_fin="13:00"),
    "I3": dict(n_tfg=20, n_docentes=16, n_dias=4, n_aulas=3, hora_fin="14:00"),
    "I4": dict(n_tfg=30, n_docentes=25, n_dias=5, n_aulas=3, hora_fin="14:00"),
}

# Instancias sinteticas reproducibles (misma semilla siempre)
def build_instance(n_tfg, n_docentes, n_dias, n_aulas, hora_fin, tribunal_size=3,
                    pct_disponibilidad=0.8, pct_ingles_tfg=0.2, pct_acepta_ingles=0.5,
                    hora_inicio="09:00", duracion_defensa=30, seed=42):
    rng = random.Random(seed)

    docentes = [
        {"id": f"D{i}", "nombre": f"Docente {i}",
         "acepta_ingles": rng.random() < pct_acepta_ingles, "activo": True}
        for i in range(1, n_docentes + 1)
    ]
    tfgs = [
        {"id": f"T{i}", "titulo": f"TFG {i}", "estudiante": f"Estudiante {i}",
         "tutor_id": f"D{((i - 1) % n_docentes) + 1}",
         "idioma": "Inglés" if rng.random() < pct_ingles_tfg else "Castellano"}
        for i in range(1, n_tfg + 1)
    ]

    dias, cursor = [], date.fromisoformat("2026-06-01")
    while len(dias) < n_dias:
        if cursor.weekday() < 5:
            dias.append(cursor.isoformat())
        cursor += timedelta(days=1)

    periodo = {
        "fecha_inicio": dias[0], "fecha_fin": dias[-1],
        "hora_inicio_dia": hora_inicio, "hora_fin_dia": hora_fin,
        "duracion_defensa": duracion_defensa, "num_miembros": tribunal_size,
        "num_aulas": n_aulas, "max_tribunales": None,
    }

    h_ini, m_ini = (int(x) for x in hora_inicio.split(":"))
    h_fin, m_fin = (int(x) for x in hora_fin.split(":"))
    bloques, cursor_min = [], h_ini * 60 + m_ini
    while cursor_min < h_fin * 60 + m_fin:
        bloques.append(f"{cursor_min // 60:02d}:{cursor_min % 60:02d}")
        cursor_min += 30

    disponibilidad = [
        {"docente_id": d["id"], "fecha": fecha, "hora_inicio": hora}
        for d in docentes for fecha in dias for hora in bloques
        if rng.random() < pct_disponibilidad
    ]
    return {"periodo": periodo, "docentes": docentes, "tfgs": tfgs, "disponibilidad": disponibilidad}

# Reconstruccion de la formulacion densa original (ver memoria, Cap. 5.5)
def build_dense_model(data):
    T, D, S, A = list(data["T"]), list(data["D"]), list(data["S"]), list(data["A"])
    k = int(data.get("tribunal_size", 3))
    eligible = set(data["eligible"])
    avail_slots = data["avail_slots"]
    load_max = data["load_max"]

    m = ConcreteModel()
    m.T, m.D, m.S, m.A = (Set(initialize=x, ordered=True) for x in (T, D, S, A))
    m.y = Var(m.T, m.S, m.A, domain=Binary)
    m.x = Var(m.D, m.T, m.S, m.A, domain=Binary)
    m.z = Var(m.D, domain=NonNegativeIntegers)
    m.Lmax = Var(domain=NonNegativeIntegers)
    m.Lmin = Var(domain=NonNegativeIntegers)

    m.R1 = Constraint(m.T, rule=lambda m, t: sum(m.y[t, s, a] for s in m.S for a in m.A) == 1)
    m.R2 = Constraint(m.S, m.A, rule=lambda m, s, a: sum(m.y[t, s, a] for t in m.T) <= 1)
    m.R3 = Constraint(m.T, m.S, m.A, rule=lambda m, t, s, a: sum(m.x[d, t, s, a] for d in m.D) == k * m.y[t, s, a])
    m.R4 = Constraint(m.D, m.S, rule=lambda m, d, s: sum(m.x[d, t, s, a] for t in m.T for a in m.A) <= 1)

    def r5(m, d, t, s, a):
        return Constraint.Skip if (d, t) in eligible else m.x[d, t, s, a] == 0
    m.R5 = Constraint(m.D, m.T, m.S, m.A, rule=r5)

    def r6(m, d, t, s, a):
        return Constraint.Skip if s in avail_slots.get(d, ()) else m.x[d, t, s, a] == 0
    m.R6 = Constraint(m.D, m.T, m.S, m.A, rule=r6)

    m.R7 = Constraint(m.D, rule=lambda m, d: m.z[d] == sum(m.x[d, t, s, a] for t in m.T for s in m.S for a in m.A))
    m.R8 = Constraint(m.D, rule=lambda m, d: m.z[d] <= load_max[d])
    m.R9 = Constraint(m.D, rule=lambda m, d: m.Lmax >= m.z[d])
    m.R10 = Constraint(m.D, rule=lambda m, d: m.Lmin <= m.z[d])
    m.OBJ = Objective(expr=m.Lmax - m.Lmin, sense=minimize)
    m._x_vars = len(D) * len(T) * len(S) * len(A)
    return m

# Benchmark
def timed_mean(fn, n=N_REPEATS):
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return statistics.mean(times)


def timed_mean_solver(name, solver_name, n=N_REPEATS, **kwargs):
    """Como timed_mean pero salta el solver si no esta disponible en el entorno."""
    solver = SolverFactory(solver_name)
    if solver is None or not solver.available(exception_flag=False):
        return None
    times = []
    for _ in range(n):
        t0 = time.perf_counter()
        _model, result, _band = solve_balanced(solver_name=solver_name, **kwargs)
        assert is_solved(result), f"{name}/{solver_name}: sin solucion en {kwargs.get('time_limit')}s"
        times.append(time.perf_counter() - t0)
    return statistics.mean(times)


def main():
    print(f"{'Instancia':<10}{'TFG':>5}{'Doc':>5}{'Slots':>7}{'Aulas':>6}"
          f"{'x_denso':>10}{'x_disperso':>12}{'T.denso':>10}{'T.disperso':>12}{'Mejora':>9}")
    modelos_data = {}
    for name, spec in INSTANCE_SPECS.items():
        data = build_input_data(build_instance(**spec))
        md = data.as_model_data()
        modelos_data[name] = md
        sparse_x = sum(
            1 for t in md["T"] for d in md["D"] if (d, t) in md["eligible"]
            for s in md["S"] if s in md["avail_slots"][d]
        )

        t_sparse = timed_mean(lambda md=md: solve_balanced(md, time_limit=TIME_LIMIT_SPARSE))
        dense_x = [0]

        def _dense(md=md):
            dm = build_dense_model(md)
            dense_x[0] = dm._x_vars
            res = solve_model(dm, time_limit=TIME_LIMIT_DENSE)
            assert is_solved(res), f"{name}: el modelo denso no encontro solucion en {TIME_LIMIT_DENSE}s"

        t_dense = timed_mean(_dense)

        print(f"{name:<10}{len(md['T']):>5}{len(md['D']):>5}{len(md['S']):>7}{len(md['A']):>6}"
              f"{dense_x[0]:>10}{sparse_x:>12}{t_dense:>10.3f}{t_sparse:>12.3f}{t_dense / t_sparse:>8.1f}x")

    print()
    print("Comparativa de solvers (modelo disperso, solve_balanced):")
    header = f"{'Instancia':<10}{'TFG':>5}{'Doc':>5}{'Slots':>7}{'Aulas':>6}"
    header += "".join(f"{s:>14}" for s in SOLVER_NAMES)
    print(header)
    for name, md in modelos_data.items():
        row = f"{name:<10}{len(md['T']):>5}{len(md['D']):>5}{len(md['S']):>7}{len(md['A']):>6}"
        for solver_name in SOLVER_NAMES:
            t = timed_mean_solver(name, solver_name, data=md, time_limit=TIME_LIMIT_SPARSE)
            row += f"{'n/d':>14}" if t is None else f"{t:>14.3f}"
        print(row)


if __name__ == "__main__":
    main()
