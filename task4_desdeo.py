"""
TIES483 Exercise 3 – Task 4
============================
Multiobjective portfolio optimisation using the DESDEO framework.

Scientific application:
    Markowitz, H. (1952). Portfolio selection. Journal of Finance, 7(1), 77–91.
    The classic mean-variance (MV) portfolio selection problem is one of the
    most cited applications of multiobjective optimisation in finance.

Problem formulation
-------------------
Let w = (w1, w2, w3) be the allocation weights across three assets.

Objectives
    f1(w) = -(mu1*w1 + mu2*w2 + mu3*w3)   [minimise negative return  ⇔  maximise return]
    f2(w) =  w^T Σ w                        [minimise portfolio variance]

Constraints
    w1 + w2 + w3 = 1   (weights sum to one)
    0 ≤ wi ≤ 1         (no short-selling)

Data (artificial but realistic):
    expected returns  µ  = [0.10, 0.14, 0.08]
    covariance matrix Σ  = [[0.040, 0.006, 0.004],
                             [0.006, 0.090, 0.010],
                             [0.004, 0.010, 0.025]]
"""

import warnings
warnings.filterwarnings("ignore")

import numpy as np
from desdeo.problem.schema import (
    Constraint,
    ConstraintTypeEnum,
    Objective,
    Problem,
    Variable,
    VariableTypeEnum,
)
from desdeo.tools import payoff_table_method, ScipyMinimizeSolver
from desdeo.tools.scipy_solver_interfaces import ScipyMinimizeOptions
from desdeo.mcdm import rpm_solve_solutions

# ---------------------------------------------------------------------------
# 1. Define variables
# ---------------------------------------------------------------------------
w1 = Variable(
    name="Weight asset 1",
    symbol="w1",
    variable_type=VariableTypeEnum.real,
    lowerbound=0.0,
    upperbound=1.0,
    initial_value=1 / 3,
)
w2 = Variable(
    name="Weight asset 2",
    symbol="w2",
    variable_type=VariableTypeEnum.real,
    lowerbound=0.0,
    upperbound=1.0,
    initial_value=1 / 3,
)
w3 = Variable(
    name="Weight asset 3",
    symbol="w3",
    variable_type=VariableTypeEnum.real,
    lowerbound=0.0,
    upperbound=1.0,
    initial_value=1 / 3,
)

# ---------------------------------------------------------------------------
# 2. Define objectives as string expressions understood by DESDEO's parser
# ---------------------------------------------------------------------------
# f1: minimise negative expected return  ( = maximise expected return )
#     f1 = -(0.10*w1 + 0.14*w2 + 0.08*w3)
f1_expr = "-(0.10*w1 + 0.14*w2 + 0.08*w3)"

# f2: minimise portfolio variance
#     f2 = w^T Σ w
#        = 0.040*w1^2 + 0.090*w2^2 + 0.025*w3^2
#          + 2*0.006*w1*w2 + 2*0.004*w1*w3 + 2*0.010*w2*w3
f2_expr = (
    "0.040*w1**2 + 0.090*w2**2 + 0.025*w3**2"
    " + 2*0.006*w1*w2 + 2*0.004*w1*w3 + 2*0.010*w2*w3"
)

neg_return = Objective(
    name="Negative expected return",
    symbol="f1",
    func=f1_expr,
    maximize=False,
    is_linear=True,
    is_convex=True,
    is_twice_differentiable=True,
)

variance = Objective(
    name="Portfolio variance",
    symbol="f2",
    func=f2_expr,
    maximize=False,
    is_linear=False,
    is_convex=True,
    is_twice_differentiable=True,
)

# ---------------------------------------------------------------------------
# 3. Budget equality constraint:  w1 + w2 + w3 - 1 = 0
# ---------------------------------------------------------------------------
budget = Constraint(
    name="Budget constraint",
    symbol="g1",
    cons_type=ConstraintTypeEnum.EQ,   # equality  (=)
    func="w1 + w2 + w3 - 1",
    is_linear=True,
    is_convex=True,
    is_twice_differentiable=True,
)

# ---------------------------------------------------------------------------
# 4. Build the Problem object
# ---------------------------------------------------------------------------
problem = Problem(
    name="Mean-Variance Portfolio Optimisation",
    description=(
        "Two-objective portfolio problem from Markowitz (1952): "
        "maximise expected return and minimise variance."
    ),
    variables=[w1, w2, w3],
    objectives=[neg_return, variance],
    constraints=[budget],
    is_convex=True,
    is_twice_differentiable=True,
)

print("=" * 60)
print("Problem created successfully.")
print(f"  Variables  : {[v.symbol for v in problem.variables]}")
print(f"  Objectives : {[o.symbol for o in problem.objectives]}")
print(f"  Constraints: {[c.symbol for c in problem.constraints]}")

# ---------------------------------------------------------------------------
# 5. Compute the ideal and nadir vectors via the payoff-table method
# ---------------------------------------------------------------------------
print("\nComputing ideal and nadir vectors (payoff-table method)...")
# Pass the solver class (constructor), not an instance
ideal, nadir = payoff_table_method(problem, solver=ScipyMinimizeSolver)

print("\nIdeal vector:")
for key, val in ideal.items():
    print(f"  {key}: {val:.6f}")

print("\nNadir vector:")
for key, val in nadir.items():
    print(f"  {key}: {val:.6f}")

# Store ideal and nadir on the problem object (required for RPM)
problem = problem.update_ideal_and_nadir(new_ideal=ideal, new_nadir=nadir)

# ---------------------------------------------------------------------------
# 6. Solve the problem with the Reference Point Method (RPM)
# ---------------------------------------------------------------------------
# Set a reference point: aim for roughly 12 % return (f1 = -0.12) and
# variance below 0.03.
reference_point = {"f1": -0.12, "f2": 0.03}

print("\nSolving with the Reference Point Method...")
print(f"  Reference point: {reference_point}")

results = rpm_solve_solutions(
    problem,
    reference_point=reference_point,
    solver=ScipyMinimizeSolver,
    solver_options=ScipyMinimizeOptions(),
)

print("\nRPM solution(s):")
for i, res in enumerate(results, 1):
    print(f"\n  Solution {i}:")
    print(f"    Objectives : {res.optimal_objectives}")
    print(f"    Variables  : {res.optimal_variables}")

    # Interpret results
    obj = res.optimal_objectives
    w_opt = res.optimal_variables
    if obj and w_opt:
        ret = -obj.get("f1", float("nan"))
        var = obj.get("f2", float("nan"))
        print(f"\n    Expected return : {ret:.4f}  ({ret*100:.2f} %)")
        print(f"    Variance        : {var:.6f}")
        print(f"    Std. deviation  : {np.sqrt(var):.4f}  ({np.sqrt(var)*100:.2f} %)")
        if isinstance(w_opt, dict):
            print(f"    Weights         : w1={w_opt.get('w1',0):.4f}, "
                  f"w2={w_opt.get('w2',0):.4f}, "
                  f"w3={w_opt.get('w3',0):.4f}")

print("\nTask 4 completed successfully.")
