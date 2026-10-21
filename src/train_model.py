import pandas as pd
import numpy as np
import matplotlib
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42

df = pd.read_csv("data/processed/abalone_clean.csv")
y = pd.read_csv("data/raw/rings.csv")


X_train, X_test, y_train, y_test = train_test_split(
    df, y, test_size=0.2, random_state=RANDOM_STATE)
y_train_arr = y_train.values.ravel()

# Ahora tenemos que ver que hacemos porque en el 4b predecimos la cantidad de anillos que es lo mismo que Age -1.5 entonces
# podemos borrar la variable Age para usar el mismo codigo que antes o podemos re hacer el forest para que busque Age

