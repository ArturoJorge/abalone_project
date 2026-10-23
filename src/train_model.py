import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import optuna
import joblib
import hashlib
from pathlib import Path
from datetime import date
import json
import shutil

RANDOM_STATE = 42


# ---------------------------------------------------------------- rutas
MODEL_PATH = Path("models/model_v1.pkl")
REGISTRY_PATH = Path("results/metrics_v1.json")
SNAPSHOT_DIR = Path("models")
# poner en True si tenes ganas de guardar copias de cada abalone_clean que se creo
SAVE_SNAPSHOTS = False

# Versionado -----------------------------------------------------------------
def sha256_file(path: Path) -> str:
    """Hash SHA-256 del contenido del archivo (leído en bloques)."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def load_registry() -> list:
    if REGISTRY_PATH.exists():
        with open(REGISTRY_PATH, encoding="utf-8") as f:
            return json.load(f)
    return []


def save_registry(registry: list) -> None:
    with open(REGISTRY_PATH, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


def register_version(hiperparametros: list, metrics: list) -> None:
    """Registra una nueva versión solo si abalone_clean.csv cambió."""
    registry = load_registry()
    new_hash = sha256_file(MODEL_PATH)

    # Si el hash es igual al de la última versión, no hubo cambios reales
    if registry and registry[-1]["sha256"] == new_hash:
        print(
            f"Sin cambios (hash {new_hash[:12]}...): no se crea nueva versión.")
        return

    entry = {
        "version": f"v{len(registry) + 1}",
        "created_at": date.today().isoformat(),
        "output": str(MODEL_PATH).replace("\\", "/"),
        "sha256": new_hash,
        "metrics": metrics,
        "hiperparámetros": hiperparametros,
    }
    registry.append(entry)
    save_registry(registry)

    if SAVE_SNAPSHOTS:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(MODEL_PATH, SNAPSHOT_DIR /
                    f"abalone_clean_{entry['version']}_{new_hash[:8]}.csv")

    print(f"Nueva versión registrada: {entry['version']} ({new_hash[:12]}...)")
# ----------------------------------------------------------------------------------

def main():
    metrics = []
    hiperparametros = []
    
    df = pd.read_csv("data/processed/abalone_clean.csv")
    y = pd.read_csv("data/raw/rings.csv")


    X_train, X_test, y_train, y_test = train_test_split(
        df, y, test_size=0.2, random_state=RANDOM_STATE)
    y_train_arr = y_train.values.ravel()

    # Ahora tenemos que ver que hacemos porque en el 4b predecimos la cantidad de anillos que es lo mismo que Age -1.5 entonces
    # podemos borrar la variable Age para usar el mismo codigo que antes o podemos re hacer el forest para que busque Age
    # ---------------------
    variables = df.columns
    i = 0
    for var in variables:
        if var == 'Age':
            variables = variables.delete(i)
            break
        else:
            i += 1
    # ---------------------

    df = df[variables]

    cv = KFold(n_splits=5, shuffle=True, random_state=42)


    def objective(trial):
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 100, 500, step=50),
            "max_depth": trial.suggest_int("max_depth", 4, 24),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 5, 15),
            "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", 0.5, 1.0]),
        }
        model = RandomForestRegressor(**params, random_state=42, n_jobs=-1)
        scores = cross_val_score(model, X_train, y_train_arr, cv=cv,
                                scoring="neg_mean_absolute_error")
        return -scores.mean()   # MAE de CV, a minimizar


    train = input("Do you want to train the model? (y/n)")
    if train == "y":
        study = optuna.create_study(
            direction="minimize",
            sampler=optuna.samplers.TPESampler(seed=42),
        )
        study.optimize(objective, n_trials=10, show_progress_bar=True)

        best_params = study.best_params
        print("Mejores hiperparámetros:", best_params)
        print("MAE CV:", study.best_value)

        # Modelo final con los mejores hiperparámetros
        rf = RandomForestRegressor(**best_params, random_state=42, n_jobs=-1)
        rf.fit(X_train, y_train_arr)

        joblib.dump(rf, "models/model_v1.pkl", compress=3)
        
        y_pred = rf.predict(X_test)
        mae = mean_absolute_error(y_test, y_pred)
        mse = mean_squared_error(y_test, y_pred)
        r2 = r2_score(y_test, y_pred)
        
        print("Métricas en test:")
        print(f"MAE: {mae}, MSE: {mse}, RMSE: {np.sqrt(mse)}, R2: {r2}")
        print(f"Mejores hiperparámetros: {best_params}")
        
        metrics.append(
        f"MAE: {mae}, MSE: {mse}, RMSE: {np.sqrt(mse)}, R2: {r2}"
    )   
        hiperparametros.append(
        f"Mejores hiperparámetros: {best_params}"
    )   

    else:
        rf = joblib.load("models/model_v1.pkl")
        print("Random forest cargado con exito")
        

    register_version(hiperparametros, metrics)


if __name__ == "__main__":
    main()
