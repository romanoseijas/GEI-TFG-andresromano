from data_input import build_input_data, demo_payload
from model_milp import solve_balanced, print_solution

if __name__ == "__main__":
    data = build_input_data(demo_payload())
    for aviso in data.avisos:
        print("AVISO:", aviso)
    model, result, banda = solve_balanced(data.as_model_data(), time_limit=60)
    print_solution(model, result)
