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
from datetime import date, datetime
import json
import shutil
import csv, os
from sklearn.pipeline import Pipeline, make_pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import RobustScaler, PowerTransformer
from sklearn.base import clone

RANDOM_STATE = 42


# ---------------------------------------------------------------- rutas
MODEL_VERSION = "v2"
MODEL_PATH = Path(f"models/model_{MODEL_VERSION}.pkl")
REGISTRY_PATH = Path(f"results/metrics_{MODEL_VERSION}.json")
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
        return len(registry)

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
    
    return (len(registry) + 1)
# ----------------------------------------------------------------------------------
numericas = ["Length", "Diameter", "Height", "Whole_weight", "Shucked_weight",
             "Viscera_weight", "Shell_weight"]
categoricas = ["Sex_M", "Sex_I", "Sex_F"]

#---------------------------------------------------------------------------------------------------------------------------#
def main():
    metrics = []
    hiperparametros = []
    
    df = pd.read_csv("data/processed/abalone_clean.csv")
    X = df.drop(columns=["Age"])
    y = df["Age"]


    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE)
    y_train_arr = y_train.values.ravel()


    cv = KFold(n_splits=5, shuffle=True, random_state=42)


    def objective(trial):
        pipeline_numericas = Pipeline(steps=[
            ('scaler', RobustScaler()),
            ('power', PowerTransformer(method='yeo-johnson', standardize=False))
        ])


        preprocesador_final = ColumnTransformer(
            transformers=[
                ('numericas', pipeline_numericas, numericas),
                ('categoricas', 'passthrough', categoricas)
            ],
            verbose_feature_names_out=False
        ).set_output(transform="pandas")

        
        params = {
            "n_estimators": trial.suggest_int("n_estimators", 150, 1000, step=50),
            "max_depth": trial.suggest_int("max_depth", 2, 24),
            "min_samples_leaf": trial.suggest_int("min_samples_leaf", 1, 20),
            "max_features": trial.suggest_categorical("max_features", ["sqrt", "log2", 0.3, 0.5, 0.7, 1.0]),
        }
        final_pipeline = Pipeline(steps=[
                    ('preprocessor', preprocesador_final),
                    ('regressor', (RandomForestRegressor(**params)))
                ])
        scores = cross_val_score(final_pipeline, X_train, y_train_arr, cv=cv,
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

        pipeline_numericas = Pipeline(steps=[
                    ('scaler', RobustScaler()),
                    ('power', PowerTransformer(method='yeo-johnson', standardize=False))
                ])
        
        
        preprocesador_final = ColumnTransformer(
            transformers=[
                ('numericas', pipeline_numericas, numericas),
                ('categoricas', 'passthrough', categoricas)
                ],
            verbose_feature_names_out=False
         ).set_output(transform="pandas")
        # Modelo final con los mejores hiperparámetros
        modelof =  Pipeline(steps=[
            ('preprocessor', preprocesador_final),
            ('regressor', (RandomForestRegressor(**best_params)))
        ])
        modelof.fit(X_train, y_train_arr)

        joblib.dump(modelof, MODEL_PATH, compress=3)
        
        y_pred = modelof.predict(X_test)
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
        version = register_version(hiperparametros, metrics)

        log_path = "results/experiments_log.csv"
        
        def siguiente_id(log_path):
            if not os.path.exists(log_path):
                return "exp_001"
            with open(log_path, newline="") as f:
                ids = [int(r["experiment_id"].split("_")[1]) for r in csv.DictReader(f)]
            return f"exp_{max(ids, default=0) + 1:03d}"

        fila = {
            "experiment_id": siguiente_id(log_path),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "model_version": version,
            "hyperparameters": json.dumps(best_params),
            "mae": mae,
            "rmse": np.sqrt(mse),
            "r2": r2,
    }   
        existe = os.path.exists(log_path)
        with open(log_path, "a", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fila.keys())
            if not existe:
                writer.writeheader()   # encabezado solo la primera vez
            writer.writerow(fila)
        
    else:
        modelof = joblib.load(MODEL_PATH)
        print("Modelo cargado con exito")
        




if __name__ == "__main__":
    main()


