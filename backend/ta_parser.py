import pandas as pd


REQUIRED_COLUMNS = ["name", "mean", "tol_plus", "tol_minus"]


def parse_file(filepath: str) -> list[dict]:
    """
    Parse a CSV or Excel file into a list of step dicts.

    Expected columns: name, mean, tol_plus, tol_minus
    Returns: [{"name": "A", "distribution": "normal", "mean": 10.0, "tol_plus": 0.1, "tol_minus": 0.1}, ...]
    """
    if filepath.endswith(".csv"):
        df = pd.read_csv(filepath)
    else:
        df = pd.read_excel(filepath)

    missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    steps = []
    for _, row in df.iterrows():
        steps.append({
            "name": str(row["name"]),
            "distribution": "normal",
            "mean": float(row["mean"]),
            "tol_plus": float(row["tol_plus"]),
            "tol_minus": float(row["tol_minus"]),
        })

    return steps
