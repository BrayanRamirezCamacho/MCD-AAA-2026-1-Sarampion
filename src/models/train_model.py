"""Train supervised outbreak prediction models.

This script trains baseline supervised models to predict monthly measles
outbreak risk in Mexico 2026 host cities using processed pipeline data.

Inputs
------
data/processed/panel_mensual_completo.csv

Outputs
-------
models/best_model.pkl
reports/metricas_modelos.csv
reports/reporte_modelo.md
data/processed/predicciones_modelo.csv
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import TimeSeriesSplit, cross_validate
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


CITY_CONFIG = {
    "CDMX": {
        "brote": "brote_CDMX",
        "brote_estricto": "brote_estricto_CDMX",
        "pax_lag": "pax_intl_lag4_CDMX",
        "vuelos_lag": "vuelos_intl_lag4_CDMX",
    },
    "Jalisco (Gdl)": {
        "brote": "brote_Jalisco (Gdl)",
        "brote_estricto": "brote_estricto_Jalisco (Gdl)",
        "pax_lag": "pax_intl_lag4_Jalisco (Gdl)",
        "vuelos_lag": "vuelos_intl_lag4_Jalisco (Gdl)",
    },
    "Nuevo León (Mty)": {
        "brote": "brote_Nuevo León (Mty)",
        "brote_estricto": "brote_estricto_Nuevo León (Mty)",
        "pax_lag": "pax_intl_lag0_Nuevo León (Mty)",
        "vuelos_lag": "vuelos_intl_lag0_Nuevo León (Mty)",
    },
}


GLOBAL_FEATURES = [
    "pasajeros_nacionales",
    "pasajeros_internacionales",
    "operaciones_vuelos_nacionales",
    "operaciones_vuelos_internacionales",
    "pax_intl_total",
    "casos_who_mexico",
    "score_riesgo_equipos",
    "mes_num",
    "es_ventana_mundial",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "processed_dir",
        type=Path,
        help="Directory containing processed datasets.",
    )
    parser.add_argument(
        "models_dir",
        type=Path,
        help="Directory where trained models will be saved.",
    )
    parser.add_argument(
        "reports_dir",
        type=Path,
        help="Directory where reports and metrics will be saved.",
    )
    parser.add_argument(
        "--target",
        choices=["brote", "brote_estricto"],
        default="brote",
        help="Target variable to train on.",
    )
    parser.add_argument(
        "--test-months",
        type=int,
        default=14,
        help="Number of final months used as temporal test set.",
    )
    return parser.parse_args()


def load_panel(processed_dir: Path) -> pd.DataFrame:
    panel_path = processed_dir / "panel_mensual_completo.csv"
    if not panel_path.exists():
        raise FileNotFoundError(
            f"No se encontró {panel_path}. Ejecuta primero: make data"
        )

    panel = pd.read_csv(panel_path)
    panel["fecha"] = pd.to_datetime(panel["fecha"], errors="coerce")

    if panel["fecha"].isna().any():
        raise ValueError("La columna fecha contiene valores no convertibles a fecha.")

    return panel.sort_values("fecha").reset_index(drop=True)


def build_city_month_dataset(panel: pd.DataFrame, target: str) -> pd.DataFrame:
    records = []

    for city, config in CITY_CONFIG.items():
        required_cols = GLOBAL_FEATURES + [
            config[target],
            config["pax_lag"],
            config["vuelos_lag"],
        ]

        missing_cols = [col for col in required_cols if col not in panel.columns]
        if missing_cols:
            raise ValueError(f"Faltan columnas para {city}: {missing_cols}")

        temp = panel[["fecha"] + required_cols].copy()
        temp["ciudad_sede"] = city
        temp["target_brote"] = temp[config[target]]
        temp["pax_intl_lag_ciudad"] = temp[config["pax_lag"]]
        temp["vuelos_intl_lag_ciudad"] = temp[config["vuelos_lag"]]

        drop_cols = [config[target], config["pax_lag"], config["vuelos_lag"]]
        temp = temp.drop(columns=drop_cols)

        records.append(temp)

    dataset = pd.concat(records, ignore_index=True)
    dataset = dataset.dropna(subset=["target_brote"]).copy()
    dataset["target_brote"] = dataset["target_brote"].astype(int)

    return dataset.sort_values(["fecha", "ciudad_sede"]).reset_index(drop=True)


def temporal_split(
    dataset: pd.DataFrame,
    test_months: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    unique_months = sorted(dataset["fecha"].dropna().unique())

    if len(unique_months) <= test_months:
        raise ValueError(
            f"No hay suficientes meses para usar test_months={test_months}."
        )

    cutoff = unique_months[-test_months]
    train_df = dataset[dataset["fecha"] < cutoff].copy()
    test_df = dataset[dataset["fecha"] >= cutoff].copy()

    if train_df["target_brote"].nunique() < 2:
        raise ValueError("El conjunto de entrenamiento tiene una sola clase.")

    if test_df["target_brote"].nunique() < 2:
        print(
            "ADVERTENCIA: el conjunto de prueba tiene una sola clase; "
            "algunas métricas no estarán disponibles."
        )

    return train_df, test_df


def build_preprocessor(
    numeric_features: List[str],
    categorical_features: List[str],
) -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_features),
            ("cat", categorical_pipeline, categorical_features),
        ]
    )


def get_models(random_state: int = 42) -> Dict[str, object]:
    return {
        "logistic_regression": LogisticRegression(
            max_iter=1000,
            class_weight="balanced",
            random_state=random_state,
        ),
        "random_forest": RandomForestClassifier(
            n_estimators=300,
            min_samples_leaf=2,
            class_weight="balanced",
            random_state=random_state,
        ),
        "gradient_boosting": GradientBoostingClassifier(
            random_state=random_state,
        ),
        "knn": KNeighborsClassifier(n_neighbors=5),
    }


def safe_roc_auc(y_true: pd.Series, y_score: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return np.nan
    return roc_auc_score(y_true, y_score)


def safe_average_precision(y_true: pd.Series, y_score: np.ndarray) -> float:
    if len(np.unique(y_true)) < 2:
        return np.nan
    return average_precision_score(y_true, y_score)


def evaluate_model(
    model_name: str,
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
) -> Dict[str, float]:
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)

    if hasattr(pipeline, "predict_proba"):
        y_score = pipeline.predict_proba(X_test)[:, 1]
    else:
        y_score = y_pred

    metrics = {
        "model": model_name,
        "accuracy": accuracy_score(y_test, y_pred),
        "balanced_accuracy": balanced_accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1": f1_score(y_test, y_pred, zero_division=0),
        "roc_auc": safe_roc_auc(y_test, y_score),
        "average_precision": safe_average_precision(y_test, y_score),
    }

    return metrics


def cross_validate_model(
    pipeline: Pipeline,
    X_train: pd.DataFrame,
    y_train: pd.Series,
) -> Dict[str, float]:
    n_splits = min(4, max(2, y_train.shape[0] // 30))
    cv = TimeSeriesSplit(n_splits=n_splits)

    scoring = {
        "f1": "f1",
        "balanced_accuracy": "balanced_accuracy",
        "recall": "recall",
    }

    try:
        scores = cross_validate(
            pipeline,
            X_train,
            y_train,
            cv=cv,
            scoring=scoring,
            error_score=np.nan,
        )
    except ValueError:
        return {
            "cv_f1_mean": np.nan,
            "cv_balanced_accuracy_mean": np.nan,
            "cv_recall_mean": np.nan,
        }

    return {
        "cv_f1_mean": np.nanmean(scores["test_f1"]),
        "cv_balanced_accuracy_mean": np.nanmean(scores["test_balanced_accuracy"]),
        "cv_recall_mean": np.nanmean(scores["test_recall"]),
    }


def write_markdown_report(
    report_path: Path,
    target: str,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    metrics_df: pd.DataFrame,
    best_model_name: str,
    y_test: pd.Series,
    y_pred: np.ndarray,
) -> None:
    cm = confusion_matrix(y_test, y_pred)
    class_report = classification_report(y_test, y_pred, zero_division=0)

    report = f"""# Reporte de modelo supervisado

## Objetivo

Entrenar modelos supervisados para predecir riesgo mensual de brote de sarampión
en ciudades sede de México 2026.

## Dataset

- Fuente: `data/processed/panel_mensual_completo.csv`
- Formato de entrenamiento: ciudad-mes
- Variable objetivo: `{target}`
- Filas de entrenamiento: {len(train_df)}
- Filas de prueba temporal: {len(test_df)}
- Periodo entrenamiento: {train_df["fecha"].min().date()} a {train_df["fecha"].max().date()}
- Periodo prueba: {test_df["fecha"].min().date()} a {test_df["fecha"].max().date()}

## Distribución de clases

### Entrenamiento

{train_df["target_brote"].value_counts().sort_index().to_markdown()}

### Prueba

{test_df["target_brote"].value_counts().sort_index().to_markdown()}

## Métricas comparativas

{metrics_df.to_markdown(index=False)}

## Mejor modelo seleccionado

`{best_model_name}`

El criterio automático de selección fue mayor `f1`; en caso de empate,
mayor `recall`.

## Matriz de confusión del mejor modelo

```text
{cm}
```

## Reporte de clasificación

```text
{class_report}
```
"""

    report_path.write_text(report, encoding="utf-8")

def main() -> None:
    args = parse_args()

    args.models_dir.mkdir(parents=True, exist_ok=True)
    args.reports_dir.mkdir(parents=True, exist_ok=True)

    panel = load_panel(args.processed_dir)
    dataset = build_city_month_dataset(panel, target=args.target)

    train_df, test_df = temporal_split(dataset, test_months=args.test_months)

    feature_cols = [
        "ciudad_sede",
        "pasajeros_nacionales",
        "pasajeros_internacionales",
        "operaciones_vuelos_nacionales",
        "operaciones_vuelos_internacionales",
        "pax_intl_total",
        "casos_who_mexico",
        "score_riesgo_equipos",
        "mes_num",
        "es_ventana_mundial",
        "pax_intl_lag_ciudad",
        "vuelos_intl_lag_ciudad",
    ]

    categorical_features = ["ciudad_sede"]
    numeric_features = [
        col for col in feature_cols if col not in categorical_features
    ]

    X_train = train_df[feature_cols]
    y_train = train_df["target_brote"]
    X_test = test_df[feature_cols]
    y_test = test_df["target_brote"]

    preprocessor = build_preprocessor(numeric_features, categorical_features)

    metrics = []
    fitted_pipelines = {}

    for model_name, model in get_models().items():
        pipeline = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", model),
            ]
        )

        metric_row = evaluate_model(
            model_name=model_name,
            pipeline=pipeline,
            X_train=X_train,
            y_train=y_train,
            X_test=X_test,
            y_test=y_test,
        )

        cv_metrics = cross_validate_model(pipeline, X_train, y_train)
        metric_row.update(cv_metrics)

        metrics.append(metric_row)
        fitted_pipelines[model_name] = pipeline

    metrics_df = pd.DataFrame(metrics)
    metrics_df = metrics_df.sort_values(
        by=["f1", "recall", "balanced_accuracy"],
        ascending=False,
    ).reset_index(drop=True)

    best_model_name = metrics_df.loc[0, "model"]
    best_pipeline = fitted_pipelines[best_model_name]

    best_predictions = best_pipeline.predict(X_test)

    if hasattr(best_pipeline, "predict_proba"):
        best_scores = best_pipeline.predict_proba(X_test)[:, 1]
    else:
        best_scores = best_predictions

    pred_df = test_df[["fecha", "ciudad_sede", "target_brote"]].copy()
    pred_df["pred_brote"] = best_predictions
    pred_df["score_brote"] = best_scores
    pred_df["modelo"] = best_model_name

    metrics_path = args.reports_dir / "metricas_modelos.csv"
    report_path = args.reports_dir / "reporte_modelo.md"
    model_path = args.models_dir / "best_model.pkl"
    predictions_path = args.processed_dir / "predicciones_modelo.csv"

    metrics_df.to_csv(metrics_path, index=False)
    pred_df.to_csv(predictions_path, index=False)
    joblib.dump(best_pipeline, model_path)

    write_markdown_report(
        report_path=report_path,
        target=args.target,
        train_df=train_df,
        test_df=test_df,
        metrics_df=metrics_df,
        best_model_name=best_model_name,
        y_test=y_test,
        y_pred=best_predictions,
    )

    print("Entrenamiento completado.")
    print(f"Mejor modelo: {best_model_name}")
    print("Archivos generados:")
    print(f" - {model_path}")
    print(f" - {metrics_path}")
    print(f" - {report_path}")
    print(f" - {predictions_path}")


if __name__ == "__main__":
    main()