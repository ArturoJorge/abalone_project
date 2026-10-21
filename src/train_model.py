import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import KFold, cross_val_score
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import optuna
import pickle

RANDOM_STATE = 42

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


train = input("Do you want to train the model again? (y/n)")
if train == "y":
    study = optuna.create_study(
        direction="minimize",
        sampler=optuna.samplers.TPESampler(seed=42),
    )
    study.optimize(objective, n_trials=50, show_progress_bar=True)

    best_params = study.best_params
    print("Mejores hiperparámetros:", best_params)
    print("MAE CV:", study.best_value)

    # Modelo final con los mejores hiperparámetros
    rf = RandomForestRegressor(**best_params, random_state=42, n_jobs=-1)
    rf.fit(X_train, y_train_arr)

    with open("results/random_forest.pkl", "wb") as file:
        pickle.dump(rf, file)

else:
    with open("results/random_forest.pkl", "rb") as file:
        rf = pickle.load(file)
        print("Random forest cargado con exito")

# TODO: CAMBIAR LOS PICKLE POR EL JOBLIB COMPRIMIENDO EL MODELO.
