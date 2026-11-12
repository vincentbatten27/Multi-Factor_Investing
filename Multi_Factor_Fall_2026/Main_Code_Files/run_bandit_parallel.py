"""
Runs the bandit for several months at the same time.

It does not contain a second copy of the bandit. It loads the functions from
"Sandbox Run Simulator.ipynb" and calls the notebook's own run_bandit() once per month,
each month in its own process. Same code, same results folder (RLM_DIR), same files, same seeds.
When it finishes, run_sp500_data() in the notebook finds nothing left to catch up on.

    python run_bandit_parallel.py        one process per CPU core, minus one
    python run_bandit_parallel.py 4      four processes

Which months run is decided by the notebook's get_unexplored_dates(): every month from
RLM_FIRST_MONTH on that has no finished results in RLM_DIR. Stop it any time; finished months are kept.
"""
import ast
import contextlib
import json
import os
import sys
import time
from multiprocessing import Pool
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTEBOOK = HERE / "Sandbox Run Simulator.ipynb"

# What run_sp500_data() loads; handed to every worker so the data is read and refreshed only once.
DATA_NAMES = [
    "indexgspc", "spy_yoy_tickers", "price_monthly_data", "new_monthly_data", "ff3_monthly",
    "months_after_this", "end1", "target_date", "OBJECTIVES", "OBJ_ORDER", "FACTORS",
]


def _calls_run_sp500_data(node):
    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
        return False
    return any(
        isinstance(n, ast.Call) and getattr(n.func, "id", "") == "run_sp500_data" for n in ast.walk(node)
    )


def _is_plain_value(node):
    """A top-level assignment of a literal: RLM_DIR = "...", MAX_WEIGHT = 0.02, _FF3_CACHE = {} ..."""
    if not isinstance(node, ast.Assign):
        return False
    try:
        ast.literal_eval(node.value)
        return True
    except (ValueError, SyntaxError):
        return False


def load_notebook_functions():
    """Everything the notebook defines before it first calls run_sp500_data():
    its imports, functions, classes and plain constants (RLM_DIR, MAX_WEIGHT, ...). Nothing is run."""
    cells = json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]
    bodies = []
    for cell in cells:
        if cell["cell_type"] != "code":
            continue
        try:
            body = ast.parse("".join(cell["source"])).body
        except SyntaxError:      # a cell with notebook-only commands
            continue
        if any(_calls_run_sp500_data(node) for node in body):
            break
        bodies.append(body)

    ns = {"__name__": "notebook"}

    def run(node):
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(NOTEBOOK), "exec"), ns)

    for body in bodies:          # imports first, wherever they sit in the notebook
        for node in body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                try:
                    run(node)
                except ImportError as e:
                    print(f"note: skipped an import the notebook lists ({e})")
    for body in bodies:          # then definitions and constants, in notebook order
        for node in body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) or _is_plain_value(node):
                run(node)
    return ns


def load_data(ns):
    """The notebook's own run_sp500_data(), data refresh included, with its bandit loop switched off."""
    real_run_bandit = ns["run_bandit"]
    ns["run_bandit"] = lambda *args, **kwargs: None
    try:
        ns["run_sp500_data"]()
    finally:
        ns["run_bandit"] = real_run_bandit
    return {name: ns[name] for name in DATA_NAMES}


_NS = None


def _start_worker(data):
    global _NS
    os.chdir(HERE)
    with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet):
        _NS = load_notebook_functions()
    _NS.update(data)


def _run_month(date):
    started = time.time()
    try:
        with open(os.devnull, "w") as quiet, contextlib.redirect_stdout(quiet):
            _NS["run_bandit"]({0: date}, _NS["target_date"])
        # run_bandit() skips evaluations that raise, so check that the month really produced a file
        first = _NS["OBJ_ORDER"][0]
        written = Path(_NS["RLM_DIR"]) / first / f"rebal_explored_{first}_{date.strftime('%Y-%m-%d')}.csv"
        error = None if written.exists() else "no results were written"
    except Exception as e:       # one bad month must not stop the others
        error = f"{type(e).__name__}: {e}"
    return date, (time.time() - started) / 60, error


def main():
    processes = int(sys.argv[1]) if len(sys.argv) > 1 else max(1, (os.cpu_count() or 2) - 1)
    os.chdir(HERE)
    ns = load_notebook_functions()
    data = load_data(ns)

    if len(data["new_monthly_data"].iloc[-1].dropna()) < 500:      # the same check run_bandit() makes
        print("Equity return data for the latest month is not yet available.")
        return
    months = ns["get_unexplored_dates"](data["months_after_this"], data["OBJECTIVES"], 100)
    if not months:
        print("No new months to process.")
        return

    print(f"Results folder: {ns['RLM_DIR']}")
    print(f"{len(months)} months to run ({months[0].date()} to {months[-1].date()}) on {processes} processes.")
    started = time.time()
    with Pool(processes, initializer=_start_worker, initargs=(data,)) as pool:
        for done, (date, minutes, error) in enumerate(pool.imap_unordered(_run_month, months), start=1):
            status = "done" if error is None else f"FAILED ({error})"
            print(f"[{done}/{len(months)}] {date.date()} {status} in {minutes:.1f} min", flush=True)
    print(f"Finished in {(time.time() - started) / 60:.1f} minutes.")


if __name__ == "__main__":
    main()
