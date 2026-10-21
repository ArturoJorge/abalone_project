import hashlib
import json
import shutil
from datetime import date
from pathlib import Path
import pandas as pd
from sklearn.preprocessing import OneHotEncoder

# ---------------------------------------------------------------- rutas
RAW_PATH = Path("data/raw/abalone_raw.csv")
RINGS_PATH = Path("data/raw/rings.csv")
CLEAN_PATH = Path("data/processed/abalone_clean.csv")
REGISTRY_PATH = Path("data/processed/data_log.json")
SNAPSHOT_DIR = Path("data/processed")
# poner en True si tenes ganas de guardar copias de cada abalone_clean que se creo
SAVE_SNAPSHOTS = False


# ---------------------------------------------------------------- esto es todo lo del hash (´･ω･`)?
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


def register_version(transformations: list) -> None:
    """Registra una nueva versión solo si abalone_clean.csv cambió."""
    registry = load_registry()
    new_hash = sha256_file(CLEAN_PATH)

    # Si el hash es igual al de la última versión, no hubo cambios reales
    if registry and registry[-1]["sha256"] == new_hash:
        print(
            f"Sin cambios (hash {new_hash[:12]}...): no se crea nueva versión.")
        return

    entry = {
        "version": f"v{len(registry) + 1}",
        "created_at": date.today().isoformat(),
        "source": str(RAW_PATH).replace("\\", "/"),
        "source_sha256": sha256_file(RAW_PATH),
        "output": str(CLEAN_PATH).replace("\\", "/"),
        "sha256": new_hash,
        "parent_sha256": registry[-1]["sha256"] if registry else None,
        "transformations": transformations,
    }
    registry.append(entry)
    save_registry(registry)

    if SAVE_SNAPSHOTS:
        SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy(CLEAN_PATH, SNAPSHOT_DIR /
                    f"abalone_clean_{entry['version']}_{new_hash[:8]}.csv")

    print(f"Nueva versión registrada: {entry['version']} ({new_hash[:12]}...)")


# ----------------------------------------------------------------
def main() -> None:
    transformations = []  # para llevar registro de los pasos que se hacen

    df = pd.read_csv(RAW_PATH)
    y = pd.read_csv(RINGS_PATH)

    df["Age"] = y["Rings"] + 1.5
    transformations.append("added derived feature 'Age = Rings + 1.5'")

    numericas = ["Length", "Diameter", "Height", "Whole_weight", "Shucked_weight",
                 "Viscera_weight", "Shell_weight"]
    categoricas = ["Sex"]

    ohe = OneHotEncoder(sparse_output=False)
    ohe_arr = ohe.fit_transform(df[categoricas])
    nuevas_cols = list(ohe.get_feature_names_out(categoricas))
    df_onehot = pd.DataFrame(ohe_arr, columns=nuevas_cols, index=df.index)
    df = pd.concat([df.drop(columns=categoricas), df_onehot], axis=1)
    transformations.append(
        f"encoded {', '.join(categoricas)} with one-hot encoding ({', '.join(nuevas_cols)})"
    )

    # guardar y registrar

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(CLEAN_PATH, index=False)
    register_version(transformations)


if __name__ == "__main__":
    main()
