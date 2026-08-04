def define_domains():
  T = ["T1", "T2", "T3", "T4", "T5", "T6", "T7", "T8", "T9", "T10"]
  D = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D10"]
  S = ["S1", "S2", "S3", "S4"]
  A = ["A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8"]
  R = ["R1", "R2", "R3"]
  return T, D, S, A, R

def teacher_available(D, S):
  teacher_available = {}
  for d in D:
    for s in S:
      teacher_available[(d, s)] = 1
  return teacher_available

def incompatibility_teacher_tfg(D, T):
  # 1 = el docente NO puede evaluar ese TFG (p.ej. es su tutor)
  # Por defecto no hay incompatibilidades; se marca el tutor D_i del TFG T_i.
  incompatibility_teacher_tfg = {}
  for i, d in enumerate(D):
    for j, t in enumerate(T):
      incompatibility_teacher_tfg[(d, t)] = 1 if i == j else 0
  return incompatibility_teacher_tfg

def language_compatibility(D, T):
  language_compatibility = {}
  for d in D:
    for t in T:
      language_compatibility[(d, t)] = 1
  return language_compatibility

def room_availability(S, A, T):
  room_availability = {}
  for s in S:
    for a in A:
      for t in T:
        room_availability[(s, a, t)] = 1
  return room_availability

def teacher_belongs_tribunal(D, R):
  teacher_belongs_tribunal = {}
  for d in D:
    for r in R:
      teacher_belongs_tribunal[(d, r)] = 1
  return teacher_belongs_tribunal

def teacher_belongs_tfg(D, T, S, A):
  teacher_belongs_tfg = {}
  for d in D:
    for t in T:
      for s in S:
        for a in A:
          teacher_belongs_tfg[(d, t, s, a)] = 1
  return teacher_belongs_tfg
    
def load_bounds(D, min_default, max_default):
    load_min = {d: min_default for d in D}
    load_max = {d: max_default for d in D}
    return load_min, load_max


def build_input_data():
    T, D, S, A, R = define_domains()

    data = {
        "T": T,
        "D": D,
        "S": S,
        "A": A,
        "R": R,
        "avail": teacher_available(D, S),
        "inc": incompatibility_teacher_tfg(D, T),
        "lang_ok": language_compatibility(D, T),
        "room_avail": room_availability(S, A, T),
        "tribunal_size": 3,
    }

    load_min, load_max = load_bounds(D, min_default=0, max_default=4)
    data["load_min"] = load_min
    data["load_max"] = load_max

    return data
