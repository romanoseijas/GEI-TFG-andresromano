from data_input import build_input_data
from model_milp import build_model, solve_model, print_solution

if __name__ == "__main__":
    data = build_input_data()
    model = build_model(data)
    result = solve_model(model, tee=False)
    print_solution(model, result)
