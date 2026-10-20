import pandas as pd
from sklearn.preprocessing import OneHotEncoder

# COMPOROBACION 1 2 3

df = pd.read_csv("data/raw/abalone_raw.csv")
y = pd.read_csv("data/raw/rings.csv")

df['Age'] = y['Rings'] + 1.5

numericas = ["Length", "Diameter", "Height", "Whole_weight", "Shucked_weight",
             "Viscera_weight", "Shell_weight"]
categoricas = ["Sex"]


# onehotencoder para el sexo
ohe = OneHotEncoder(sparse_output=False)
ohe_arr = ohe.fit_transform(df[categoricas])
df_onehot = pd.DataFrame(
    ohe_arr,
    columns=ohe.get_feature_names_out(categoricas),
    index=df.index,
)
df = pd.concat([df.drop(columns=categoricas), df_onehot], axis=1)


df.to_csv("data/processed/abalone_clean.csv", index=False)
