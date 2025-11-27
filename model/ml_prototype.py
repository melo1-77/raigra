# model/ml_prototype.py

import numpy as np
import pandas as pd
from pathlib import Path

from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.ensemble import RandomForestRegressor
import matplotlib.pyplot as plt


def generate_synthetic_data(n_samples: int = 1000, random_state: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(random_state)

    data = {
        "governance": rng.integers(1, 6, size=n_samples),
        "privacy": rng.integers(1, 6, size=n_samples),
        "technical": rng.integers(1, 6, size=n_samples),
        "ethics": rng.integers(1, 6, size=n_samples),
        "org_capability": rng.integers(1, 6, size=n_samples),
        "org_size": rng.choice([0, 1, 2], size=n_samples),  # 0=small, 1=medium, 2=large
    }

    df = pd.DataFrame(data)

    base_score = (
        0.30 * df["governance"]
        + 0.25 * df["privacy"]
        + 0.20 * df["technical"]
        + 0.15 * df["ethics"]
        + 0.10 * df["org_capability"]
    )

    score = base_score / 5.0 * 100.0
    noise = rng.normal(0, 5, size=n_samples)
    df["readiness_score"] = np.clip(score + noise, 0, 100)

    return df


def train_model(df: pd.DataFrame):
    X = df.drop(columns=["readiness_score"])
    y = df["readiness_score"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(
        n_estimators=300,
        max_depth=5,
        random_state=42,
        n_jobs=-1,
    )

    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    rmse = mean_squared_error(y_test, y_pred) ** 0.5
    r2 = r2_score(y_test, y_pred)

    return model, X_test, y_test, y_pred, rmse, r2


def main():
    out_dir = Path("model")
    out_dir.mkdir(exist_ok=True, parents=True)

    df = generate_synthetic_data(n_samples=1500)
    csv_path = out_dir / "synthetic_readiness_data.csv"
    df.to_csv(csv_path, index=False)
    print(f"Saved synthetic dataset to {csv_path}")

    model, X_test, y_test, y_pred, rmse, r2 = train_model(df)
    print(f"RMSE: {rmse:.2f}")
    print(f"R²:   {r2:.3f}")

    plt.figure(figsize=(6, 6))
    plt.scatter(y_test, y_pred, alpha=0.6)
    plt.plot([0, 100], [0, 100], "r--")
    plt.xlabel("True readiness score")
    plt.ylabel("Predicted readiness score")
    plt.title("Random Forest readiness model – true vs predicted")
    plt.grid(True)

    plot_path = Path("docs") / "ml_scatter.png"
    plot_path.parent.mkdir(exist_ok=True, parents=True)
    plt.savefig(plot_path, bbox_inches="tight")
    print(f"Saved diagnostic plot to {plot_path}")


if __name__ == "__main__":
    main()
