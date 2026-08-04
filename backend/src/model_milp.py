from pyomo.environ import (
    ConcreteModel, Set, Param, Var, Constraint, Objective,
    Binary, NonNegativeIntegers, NonNegativeReals, minimize,
    SolverFactory, value
)

def build_model(data):
    m = ConcreteModel("TFG_Tribunal_Assignment")

    # 1) Conjuntos
    m.T = Set(initialize=data["T"])
    m.D = Set(initialize=data["D"])
    m.S = Set(initialize=data["S"])
    m.A = Set(initialize=data["A"])
    m.R = Set(initialize=data["R"])
    k = data.get("tribunal_size", 3)


    # 2) Parámetros
    # Disponibilidad docente-slot
    m.avail = Param(m.D, m.S, within=Binary, initialize=data["avail"], default=0)

    # Incompatibilidad docente-TFG (1 = incompatible)
    m.inc = Param(m.D, m.T, within=Binary, initialize=data["inc"], default=0)

    # Compatibilidad idioma docente-TFG (1 = compatible)
    m.lang_ok = Param(m.D, m.T, within=Binary, initialize=data["lang_ok"], default=1)

    # Disponibilidad aula-slot-tfg (como viene en tus datos)
    m.room_avail = Param(m.S, m.A, m.T, within=Binary, initialize=data["room_avail"], default=0)

    # Límites de carga
    m.load_min = Param(m.D, within=NonNegativeIntegers, initialize=data["load_min"], default=0)
    m.load_max = Param(m.D, within=NonNegativeIntegers, initialize=data["load_max"], default=len(data["T"]))


    # 3) Variables de decisión
    m.y = Var(m.T, m.S, m.A, domain=Binary)
    m.x = Var(m.D, m.T, m.S, m.A, domain=Binary)
    m.z = Var(m.D, domain=NonNegativeIntegers)

    # Variables de la función objetivo
    m.Lmax = Var(domain=NonNegativeReals)
    m.Lmin = Var(domain=NonNegativeReals)


    # 4) Restricciones
    # R1) Cada TFG se programa exactamente una vez
    def one_schedule_rule(m, t):
        return sum(m.y[t, s, a] for s in m.S for a in m.A) == 1
    m.OneSchedule = Constraint(m.T, rule=one_schedule_rule)

    # R2) Un TFG por aula y slot
    def room_capacity_rule(m, s, a):
        return sum(m.y[t, s, a] for t in m.T) <= 1
    m.RoomCapacity = Constraint(m.S, m.A, rule=room_capacity_rule)

    # R3) Disponibilidad de aula
    def room_availability_rule(m, t, s, a):
        return m.y[t, s, a] <= m.room_avail[s, a, t]
    m.RoomAvailability = Constraint(m.T, m.S, m.A, rule=room_availability_rule)

    # R4) Tribunal exactamente k docentes
    def tribunal_size_rule(m, t, s, a):
        return sum(m.x[d, t, s, a] for d in m.D) == k * m.y[t, s, a]
    m.TribunalSize = Constraint(m.T, m.S, m.A, rule=tribunal_size_rule)

    # R5) Enlace evaluación-programación
    def link_x_y_rule(m, d, t, s, a):
        return m.x[d, t, s, a] <= m.y[t, s, a]
    m.LinkXY = Constraint(m.D, m.T, m.S, m.A, rule=link_x_y_rule)

    # R6) Un docente no puede evaluar dos TFG simultáneamente
    def one_tfg_per_slot_rule(m, d, s):
        return sum(m.x[d, t, s, a] for t in m.T for a in m.A) <= 1
    m.OneTFGPerSlot = Constraint(m.D, m.S, rule=one_tfg_per_slot_rule)

    # R7) Disponibilidad docente
    def teacher_availability_rule(m, d, t, s, a):
        return m.x[d, t, s, a] <= m.avail[d, s]
    m.TeacherAvailability = Constraint(m.D, m.T, m.S, m.A, rule=teacher_availability_rule)

    # R8) Incompatibilidad tutor/supervisor
    def incompatibility_rule(m, d, t, s, a):
        return m.x[d, t, s, a] <= 1 - m.inc[d, t]
    m.Incompatibility = Constraint(m.D, m.T, m.S, m.A, rule=incompatibility_rule)

    # R9) Compatibilidad idioma
    def language_rule(m, d, t, s, a):
        return m.x[d, t, s, a] <= m.lang_ok[d, t]
    m.LanguageCompatibility = Constraint(m.D, m.T, m.S, m.A, rule=language_rule)

    # R10) Definición de carga
    def load_definition_rule(m, d):
        return m.z[d] == sum(m.x[d, t, s, a] for t in m.T for s in m.S for a in m.A)
    m.LoadDefinition = Constraint(m.D, rule=load_definition_rule)

    # R11) Límites de carga
    def load_min_rule(m, d):
        return m.z[d] >= m.load_min[d]
    def load_max_rule(m, d):
        return m.z[d] <= m.load_max[d]
    m.LoadMin = Constraint(m.D, rule=load_min_rule)
    m.LoadMax = Constraint(m.D, rule=load_max_rule)

    # R12) Vinculación para equidad
    def lmax_rule(m, d):
        return m.z[d] <= m.Lmax
    def lmin_rule(m, d):
        return m.z[d] >= m.Lmin
    m.LmaxLink = Constraint(m.D, rule=lmax_rule)
    m.LminLink = Constraint(m.D, rule=lmin_rule)


    # 5) Objetivo
    m.OBJ = Objective(expr=m.Lmax - m.Lmin, sense=minimize)

    return m

def solve_model(m, tee=False):
    last_error = None
    for name in ("appsi_highs", "highs", "cbc", "glpk"):
        try:
            solver = SolverFactory(name)
            if solver is None or not solver.available(exception_flag=False):
                continue
            return solver.solve(m, tee=tee)
        except Exception as exc:
            last_error = exc
    raise RuntimeError(
        "No hay ningun solver MILP disponible (probados: appsi_highs, highs, cbc, glpk). "
        "Instala uno, por ejemplo: pip install highspy"
    ) from last_error


def print_solution(m, res):
    print("Status:", res.solver.status)
    print("Termination:", res.solver.termination_condition)

    if str(res.solver.termination_condition).lower() not in ("optimal", "feasible"):
        print("No hay solución factible con los datos actuales.")
        return

    print(f"Lmax={value(m.Lmax):.2f}, Lmin={value(m.Lmin):.2f}, gap={value(m.Lmax)-value(m.Lmin):.2f}")

    for t in m.T:
        for s in m.S:
            for a in m.A:
                if value(m.y[t, s, a]) > 0.5:
                    evaluadores = [d for d in m.D if value(m.x[d, t, s, a]) > 0.5]
                    print(f"{t} -> slot={s}, aula={a}, evals={evaluadores}")
