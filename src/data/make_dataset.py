
from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, Optional
import warnings

import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import DBSCAN, KMeans
from sklearn.ensemble import IsolationForest
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore", category=FutureWarning)

# ============================================================
# Configuración general
# ============================================================

SEDES: Dict[int, str] = {
    9: "CDMX",
    14: "Jalisco (Gdl)",
    19: "Nuevo León (Mty)",
}

MES_MAP = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}

EFES_FILES = {
    2020: "2020_efes_abierto_281220.csv",
    2021: "2021_efes_abierto_271221.csv",
    2022: "2022_efes_abierto_261222.csv",
    2023: "2023_efes_abierto_271223.csv",
    2024: "2024_efes_abierto_301024.xlsx",
    2025: "2025_efes_abierto_171225.csv",
    2026: "2026_efes_abierto_090326.csv",
}

DBSCAN_PARAMS = {
    9: {"eps": 1.2, "min_samples": 2},
    14: {"eps": 1.2, "min_samples": 2},
    19: {"eps": 1.2, "min_samples": 2},
}

REPECHAJES = ["Rep. UEFA D", "Rep. UEFA F", "Rep. Intercont. 2"]

NOMBRE_WHO = {
    "Mexico": "Mexico",
    "South Africa": "South Africa",
    "South Korea": "Republic of Korea",
    "Tunisia": "Tunisia",
    "Uzbekistan": "Uzbekistan",
    "Colombia": "Colombia",
    "Japan": "Japan",
    "Spain": "Spain",
    "Uruguay": "Uruguay",
}

PARTIDOS_MEXICO = [
    {"fecha": "2026-06-11", "ciudad": "CDMX", "home": "Mexico", "away": "South Africa"},
    {"fecha": "2026-06-11", "ciudad": "Guadalajara", "home": "South Korea", "away": "Rep. UEFA D"},
    {"fecha": "2026-06-14", "ciudad": "Monterrey", "home": "Tunisia", "away": "Rep. UEFA F"},
    {"fecha": "2026-06-17", "ciudad": "CDMX", "home": "Uzbekistan", "away": "Colombia"},
    {"fecha": "2026-06-18", "ciudad": "Guadalajara", "home": "Mexico", "away": "South Korea"},
    {"fecha": "2026-06-20", "ciudad": "Monterrey", "home": "Japan", "away": "Tunisia"},
    {"fecha": "2026-06-23", "ciudad": "Guadalajara", "home": "Colombia", "away": "Rep. Intercont. 2"},
    {"fecha": "2026-06-24", "ciudad": "CDMX", "home": "Rep. UEFA D", "away": "Mexico"},
    {"fecha": "2026-06-24", "ciudad": "Monterrey", "home": "South Africa", "away": "South Korea"},
    {"fecha": "2026-06-26", "ciudad": "Guadalajara", "home": "Spain", "away": "Uruguay"},
]


# ============================================================
# Utilidades
# ============================================================

def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def find_existing_file(raw_dir: Path, candidates: Iterable[str]) -> Path:
    for name in candidates:
        candidate = raw_dir / name
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"No se encontró ninguno de estos archivos en {raw_dir}: {list(candidates)}")


def month_to_date(df: pd.DataFrame, year_col: str = "anio", month_col: str = "mes") -> pd.Series:
    month_num = df[month_col].astype(str).str.strip().str.lower().map(MES_MAP)
    return pd.to_datetime(
        pd.DataFrame({"year": df[year_col], "month": month_num, "day": 1}),
        errors="coerce",
    )


def clean_who_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().replace("\n", " ").replace("  ", " ") for c in out.columns]
    return out


def safe_to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce")


# ============================================================
# Cargas base reutilizables
# ============================================================

def load_efes(raw_dir: Path) -> pd.DataFrame:
    dfs = []
    for year, filename in EFES_FILES.items():
        path = raw_dir / filename
        if not path.exists():
            raise FileNotFoundError(f"Falta el archivo EFES esperado: {path}")
        if path.suffix.lower() == ".xlsx":
            df = pd.read_excel(path)
        else:
            df = pd.read_csv(path)
        df["anio_fuente"] = year
        dfs.append(df)

    efes = pd.concat(dfs, ignore_index=True)

    efes["FECHA_DIAGNOSTICO"] = (
        efes["FECHA_DIAGNOSTICO"]
        .replace({"9999-99-99": np.nan, "9999/99/99": np.nan})
    )
    efes["FECHA_DIAGNOSTICO"] = pd.to_datetime(efes["FECHA_DIAGNOSTICO"], errors="coerce")

    fallback_dates = ["FECHA_ACTUALIZACION"]
    for col in fallback_dates:
        if col in efes.columns:
            efes[col] = pd.to_datetime(efes[col], errors="coerce")

    efes["fecha_base"] = efes["FECHA_DIAGNOSTICO"]
    if "FECHA_ACTUALIZACION" in efes.columns:
        efes["fecha_base"] = efes["fecha_base"].fillna(efes["FECHA_ACTUALIZACION"])

    efes["anio_mes_dt"] = efes["fecha_base"].dt.to_period("M").dt.to_timestamp()
    efes["anio_mes"] = efes["anio_mes_dt"].dt.to_period("M")

    return efes


def load_who_measles(raw_dir: Path) -> pd.DataFrame:
    path = find_existing_file(raw_dir, ["WHO_Provisional_measles_and_rubella_data.csv"])
    df = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    df = clean_who_columns(df)

    rename_map = {
        "Measles total": "measles_total",
        "Measles lab-confirmed": "measles_lab",
        "Measles epi-linked": "measles_epi",
        "Measles clinical": "measles_clinical",
        "Measles suspect": "measles_suspect",
    }
    df = df.rename(columns=rename_map)

    for col in ["Year", "Month", "measles_total", "measles_lab", "measles_epi", "measles_clinical", "measles_suspect"]:
        if col in df.columns:
            df[col] = safe_to_numeric(df[col])

    return df


def load_who_vaccination(raw_dir: Path) -> pd.DataFrame:
    path = find_existing_file(raw_dir, ["WHO_vaccination-coverage.csv"])
    df = pd.read_csv(path)
    df = df.rename(
        columns={
            "Entity": "Country",
            "Code": "ISO3",
            "Measles, first dose (MCV1)": "mcv1",
        }
    )[["Country", "ISO3", "Year", "mcv1"]].copy()
    df["Year"] = safe_to_numeric(df["Year"])
    df["mcv1"] = safe_to_numeric(df["mcv1"])
    return df


def load_qatar_attendance(raw_dir: Path) -> pd.DataFrame:
    local_candidates = [
        "Attendance Sheet.csv",
        "Qatar 2022 FIFA World Cup Attendance.csv",
    ]
    local_path = None
    for name in local_candidates:
        p = raw_dir / name
        if p.exists():
            local_path = p
            break

    if local_path is not None:
        df_qatar = pd.read_csv(local_path)
    else:
        try:
            import kagglehub
            from kagglehub import KaggleDatasetAdapter

            df_qatar = kagglehub.load_dataset(
                KaggleDatasetAdapter.PANDAS,
                "parasharmanas/qatar-2022-fifa-world-cup-attendance",
                "Attendance Sheet.csv",
            )
        except Exception as exc:  # pragma: no cover
            raise FileNotFoundError(
                "No se encontró Attendance Sheet.csv en data/raw y no fue posible descargarlo con kagglehub."
            ) from exc

    return df_qatar


def load_world_cup_matches(raw_dir: Path) -> pd.DataFrame:
    local_candidates = ["wcmatches.csv"]
    local_path = None
    for name in local_candidates:
        p = raw_dir / name
        if p.exists():
            local_path = p
            break

    if local_path is not None:
        wc_matches = pd.read_csv(local_path)
    else:
        try:
            import kagglehub

            path = kagglehub.dataset_download("evangower/fifa-world-cup")
            wc_matches = pd.read_csv(Path(path) / "wcmatches.csv")
        except Exception as exc:  # pragma: no cover
            raise FileNotFoundError(
                "No se encontró wcmatches.csv en data/raw y no fue posible descargarlo con kagglehub."
            ) from exc

    return wc_matches


def load_aicm_passengers(raw_dir: Path) -> pd.DataFrame:
    path = find_existing_file(raw_dir, ["Movimiento_operacional_de_pasajeros_de_AICM.csv"])
    aicm = pd.read_csv(path)
    aicm["fecha"] = month_to_date(aicm, "anio", "mes")
    return (
        aicm[["fecha", "pasajeros_nacionales", "pasajeros_internacionales"]]
        .sort_values("fecha")
        .reset_index(drop=True)
    )


def load_aicm_terminal(raw_dir: Path) -> pd.DataFrame:
    path = find_existing_file(raw_dir, ["Movimiento_operacional_de_pasajeros_por_terminal.csv"])
    terminal = pd.read_csv(path)
    terminal["fecha"] = month_to_date(terminal, "anio", "mes")
    terminal["pax_intl_total"] = (
        terminal["pasajeros_llegadas_internacionales_t1"].fillna(0)
        + terminal["pasajeros_llegadas_internacionales_t2"].fillna(0)
    )
    return (
        terminal[["fecha", "pax_intl_total"]]
        .sort_values("fecha")
        .reset_index(drop=True)
    )


def load_aicm_flights(raw_dir: Path) -> pd.DataFrame:
    path = find_existing_file(raw_dir, ["Movimiento_operacional_de_vuelos.csv"])
    vuelos = pd.read_csv(path)
    vuelos["fecha"] = month_to_date(vuelos, "anio", "mes")
    return (
        vuelos[["fecha", "operaciones_vuelos_nacionales", "operaciones_vuelos_internacionales"]]
        .sort_values("fecha")
        .reset_index(drop=True)
    )


def load_cdmx_arrivals(raw_dir: Path) -> pd.DataFrame:
    path = find_existing_file(raw_dir, ["Llegadas_internacionales_cdmx_mensual.csv"])
    cdmx = pd.read_csv(path)
    cdmx["fecha"] = pd.to_datetime(cdmx["fecha"], errors="coerce")
    return (
        cdmx[["fecha", "ciudad_de_mexico"]]
        .rename(columns={"ciudad_de_mexico": "intl_cdmx"})
        .sort_values("fecha")
        .reset_index(drop=True)
    )


def load_monterrey_proxy(raw_dir: Path, aicm: pd.DataFrame) -> pd.DataFrame:
    path = find_existing_file(raw_dir, ["Llegadas_aeropuerto_Extranjeros(Hoja3).csv"])
    mty_raw = pd.read_csv(path, sep=";", encoding="utf-8-sig")
    mty_raw.columns = ["anio", "pax_nacionales", "pax_internacionales", "pax_total"]

    for col in ["pax_nacionales", "pax_internacionales", "pax_total"]:
        mty_raw[col] = pd.to_numeric(
            mty_raw[col].astype(str).str.replace(".", "", regex=False).str.strip(),
            errors="coerce",
        )

    aicm_tmp = aicm.copy()
    aicm_tmp["mes_num"] = aicm_tmp["fecha"].dt.month
    estacional = aicm_tmp.groupby("mes_num")["pasajeros_internacionales"].mean()
    estacional = estacional / estacional.sum()

    rows = []
    for _, row in mty_raw.iterrows():
        for month_num, weight in estacional.items():
            rows.append(
                {
                    "fecha": pd.Timestamp(year=int(row["anio"]), month=int(month_num), day=1),
                    "pax_intl_mty": round(float(row["pax_internacionales"]) * float(weight)),
                }
            )

    return pd.DataFrame(rows).sort_values("fecha").reset_index(drop=True)


# ============================================================
# Notebook 2 — EFES mensual + anomalías
# ============================================================

def build_efes_mensual_sedes_target(efes: pd.DataFrame) -> pd.DataFrame:
    efes_sedes = efes[efes["ENTIDAD_RES"].isin(SEDES.keys())].copy()
    efes_sedes["sede"] = efes_sedes["ENTIDAD_RES"].map(SEDES)
    efes_sedes = efes_sedes[efes_sedes["anio_mes_dt"].notna()].copy()

    monthly = (
        efes_sedes.groupby(["anio_mes", "anio_mes_dt", "ENTIDAD_RES", "sede"])
        .agg(
            casos_confirmados=("DIAGNOSTICO", lambda x: (x == 1).sum()),
            casos_sospechosos=("DIAGNOSTICO", lambda x: (x == 3).sum()),
            casos_descartados=("DIAGNOSTICO", lambda x: (x == 0).sum()),
            total_registros=("DIAGNOSTICO", "count"),
            vacunados=("VACUNACION", lambda x: (x == 1).sum()),
            con_complicaciones=("COMPLICACIONES", lambda x: (x == 1).sum()),
        )
        .reset_index()
        .sort_values(["ENTIDAD_RES", "anio_mes_dt"])
        .reset_index(drop=True)
    )

    monthly["tasa_confirmacion"] = (
        monthly["casos_confirmados"] / monthly["total_registros"].replace({0: np.nan})
    ).fillna(0.0)

    # Isolation Forest por sede
    if_features = ["casos_confirmados", "casos_sospechosos", "tasa_confirmacion", "total_registros"]
    if_parts = []

    for entidad in SEDES:
        d = monthly[monthly["ENTIDAD_RES"] == entidad].copy()
        X = d[if_features].fillna(0)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)

        model = IsolationForest(contamination=0.10, random_state=42)
        d["if_pred"] = model.fit_predict(X_scaled)
        d["if_score"] = model.decision_function(X_scaled)
        d["anomalia_if"] = d["if_pred"] == -1
        if_parts.append(d)

    monthly_if = pd.concat(if_parts, ignore_index=True)

    # DBSCAN por sede
    db_parts = []
    for entidad, params in DBSCAN_PARAMS.items():
        d = monthly_if[monthly_if["ENTIDAD_RES"] == entidad].copy()
        X = d[["casos_confirmados"]].fillna(0).values
        model = DBSCAN(eps=params["eps"], min_samples=params["min_samples"])
        d["db_label"] = model.fit_predict(X)
        d["anomalia_db"] = d["db_label"] == -1
        db_parts.append(d)

    monthly_final = pd.concat(db_parts, ignore_index=True)
    monthly_final["brote"] = (monthly_final["anomalia_if"] | monthly_final["anomalia_db"]).astype(int)
    monthly_final["brote_estricto"] = (
        monthly_final["anomalia_if"] & monthly_final["anomalia_db"]
    ).astype(int)

    cols = [
        "anio_mes",
        "anio_mes_dt",
        "ENTIDAD_RES",
        "sede",
        "casos_confirmados",
        "casos_sospechosos",
        "casos_descartados",
        "total_registros",
        "vacunados",
        "con_complicaciones",
        "tasa_confirmacion",
        "anomalia_if",
        "if_score",
        "anomalia_db",
        "db_label",
        "brote",
        "brote_estricto",
    ]
    return monthly_final[cols].sort_values(["ENTIDAD_RES", "anio_mes_dt"]).reset_index(drop=True)


# ============================================================
# Notebook 1 — Clustering de países
# ============================================================

def build_match_tables() -> tuple[pd.DataFrame, list[str], pd.DataFrame, pd.DataFrame]:
    df_partidos_mexico = pd.DataFrame(PARTIDOS_MEXICO)
    df_partidos_mexico["fecha"] = pd.to_datetime(df_partidos_mexico["fecha"], errors="coerce")

    equipos_confirmados = list(NOMBRE_WHO.keys())

    equipos_por_ciudad = (
        pd.concat(
            [
                df_partidos_mexico[["ciudad", "home"]].rename(columns={"home": "Country"}),
                df_partidos_mexico[["ciudad", "away"]].rename(columns={"away": "Country"}),
            ],
            ignore_index=True,
        )
        .query("Country not in @REPECHAJES")
        .groupby(["Country", "ciudad"])
        .size()
        .reset_index(name="partidos_en_mexico")
    )

    ciudad_principal = (
        equipos_por_ciudad.sort_values("partidos_en_mexico", ascending=False)
        .groupby("Country")
        .first()
        .reset_index()[["Country", "ciudad"]]
        .rename(columns={"ciudad": "ciudad_sede"})
    )

    partidos_totales = (
        equipos_por_ciudad.groupby("Country")["partidos_en_mexico"].sum().reset_index()
    )

    return df_partidos_mexico, equipos_confirmados, equipos_por_ciudad, ciudad_principal.merge(
        partidos_totales, on="Country", how="left"
    )


def build_attendance_qatar(df_qatar: pd.DataFrame, equipos_confirmados: list[str]) -> pd.DataFrame:
    home_teams = df_qatar[["Home", "Attendance"]].rename(columns={"Home": "Country"})
    away_teams = df_qatar[["Away", "Attendance"]].rename(columns={"Away": "Country"})

    return (
        pd.concat([home_teams, away_teams], ignore_index=True)
        .assign(
            Attendance=lambda x: pd.to_numeric(
                x["Attendance"].astype(str).str.replace(",", "").str.strip(),
                errors="coerce",
            )
        )
        .groupby("Country")
        .agg(asistencia_promedio=("Attendance", "mean"))
        .reset_index()
        .query("Country in @equipos_confirmados")
    )


def build_world_cup_history(wc_matches: pd.DataFrame, equipos_confirmados: list[str]) -> pd.DataFrame:
    all_hist_teams = (
        pd.concat(
            [
                wc_matches[["home_team"]].rename(columns={"home_team": "Country"}),
                wc_matches[["away_team"]].rename(columns={"away_team": "Country"}),
            ],
            ignore_index=True,
        )
        .value_counts()
        .reset_index()
    )
    all_hist_teams.columns = ["Country", "partidos_historicos"]
    return all_hist_teams.query("Country in @equipos_confirmados").reset_index(drop=True)


def build_measles_country_features(measles: pd.DataFrame) -> pd.DataFrame:
    measles_recent = measles[measles["Year"].between(2018, 2024)].copy()
    return (
        measles_recent.groupby("Country")
        .agg(
            total_cases=("measles_total", "sum"),
            avg_monthly_cases=("measles_total", "mean"),
            months_with_cases=("measles_total", lambda x: (x > 0).sum()),
            peak_month=("measles_total", "max"),
        )
        .reset_index()
    )


def build_vax_country_features(vax: pd.DataFrame) -> pd.DataFrame:
    vax_recent = vax[vax["Year"].between(2018, 2023)].copy()

    vax_by_country = (
        vax_recent.groupby("Country")
        .agg(
            mcv1_mean=("mcv1", "mean"),
            mcv1_min=("mcv1", "min"),
            mcv1_std=("mcv1", "std"),
        )
        .reset_index()
    )

    def calc_slope(group: pd.DataFrame) -> float:
        g = group.dropna(subset=["mcv1"])
        if len(g) < 3:
            return np.nan
        slope, _, _, _, _ = stats.linregress(g["Year"], g["mcv1"])
        return slope

    vax_slope = vax_recent.groupby("Country").apply(calc_slope).reset_index(name="mcv1_tendencia")
    return vax_by_country.merge(vax_slope, on="Country", how="left")


def build_paises_cluster_riesgo(
    measles: pd.DataFrame,
    vax: pd.DataFrame,
    df_qatar: pd.DataFrame,
    wc_matches: pd.DataFrame,
) -> pd.DataFrame:
    _, equipos_confirmados, equipos_por_ciudad, city_matches = build_match_tables()
    ciudad_principal = city_matches[["Country", "ciudad_sede"]].copy()
    partidos_totales = city_matches[["Country", "partidos_en_mexico"]].copy()

    asistencia_qatar = build_attendance_qatar(df_qatar, equipos_confirmados)
    hist_wc = build_world_cup_history(wc_matches, equipos_confirmados)
    measles_by_country = build_measles_country_features(measles)
    vax_by_country = build_vax_country_features(vax)

    base = pd.DataFrame(
        {
            "Country": list(NOMBRE_WHO.keys()),
            "Country_who": list(NOMBRE_WHO.values()),
        }
    )
    base["clasificado_2026"] = 1

    cluster_df = (
        base.merge(ciudad_principal, on="Country", how="left")
        .merge(partidos_totales, on="Country", how="left")
        .merge(asistencia_qatar.rename(columns={"Country": "Country_who"}), on="Country_who", how="left")
        .merge(hist_wc.rename(columns={"Country": "Country_who"}), on="Country_who", how="left")
        .merge(
            measles_by_country.rename(columns={"Country": "Country_who"})[
                ["Country_who", "total_cases", "avg_monthly_cases", "months_with_cases", "peak_month"]
            ],
            on="Country_who",
            how="left",
        )
        .merge(
            vax_by_country.rename(columns={"Country": "Country_who"})[
                ["Country_who", "mcv1_mean", "mcv1_min", "mcv1_std", "mcv1_tendencia"]
            ],
            on="Country_who",
            how="left",
        )
    )

    fill_cols = [
        "total_cases",
        "avg_monthly_cases",
        "months_with_cases",
        "peak_month",
        "mcv1_mean",
        "mcv1_min",
        "mcv1_std",
        "mcv1_tendencia",
        "asistencia_promedio",
        "partidos_historicos",
        "partidos_en_mexico",
    ]
    for col in fill_cols:
        if col in cluster_df.columns:
            cluster_df[col] = cluster_df[col].fillna(cluster_df[col].median())

    cluster_df["partidos_historicos"] = cluster_df["partidos_historicos"].astype(int)
    cluster_df["partidos_en_mexico"] = cluster_df["partidos_en_mexico"].astype(int)

    cluster_features = [
        "total_cases",
        "months_with_cases",
        "mcv1_mean",
        "mcv1_min",
        "mcv1_tendencia",
    ]

    X = cluster_df[cluster_features].copy()
    X["total_cases"] = np.log1p(X["total_cases"])
    X["months_with_cases"] = np.log1p(X["months_with_cases"])

    imputer = SimpleImputer(strategy="median")
    X_imputed = imputer.fit_transform(X)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_imputed)

    # El notebook estima best_k_sil, pero el diccionario final documenta k=4.
    # Fijamos K_FINAL=4 para reproducir la entrega documentada.
    K_FINAL = 4
    km_final = KMeans(n_clusters=K_FINAL, random_state=42, n_init=30, max_iter=1000)
    cluster_df["cluster"] = km_final.fit_predict(X_scaled)

    cluster_df["score_riesgo"] = (
        np.log1p(cluster_df["total_cases"]) * (100 - cluster_df["mcv1_mean"]) / 100
    )
    min_r = cluster_df["score_riesgo"].min()
    max_r = cluster_df["score_riesgo"].max()
    if max_r == min_r:
        cluster_df["score_riesgo_norm"] = 0.0
    else:
        cluster_df["score_riesgo_norm"] = (
            (cluster_df["score_riesgo"] - min_r) / (max_r - min_r) * 10
        ).round(2)

    output_cols = [
        "Country",
        "Country_who",
        "ciudad_sede",
        "partidos_en_mexico",
        "asistencia_promedio",
        "partidos_historicos",
        "clasificado_2026",
        "total_cases",
        "avg_monthly_cases",
        "months_with_cases",
        "mcv1_mean",
        "mcv1_min",
        "mcv1_tendencia",
        "cluster",
        "score_riesgo_norm",
    ]
    return cluster_df[output_cols].sort_values(["score_riesgo_norm", "Country"], ascending=[False, True]).reset_index(drop=True)


# ============================================================
# Notebook 3 — Panel mensual completo
# ============================================================

def build_who_mexico_series(measles: pd.DataFrame) -> pd.DataFrame:
    who_mex = measles[measles["Country"] == "Mexico"].copy()
    who_mex["fecha"] = pd.to_datetime(
        pd.DataFrame(
            {
                "year": who_mex["Year"],
                "month": who_mex["Month"],
                "day": 1,
            }
        ),
        errors="coerce",
    )
    who_mex["casos_who_mexico"] = safe_to_numeric(who_mex["measles_total"])
    return who_mex[["fecha", "casos_who_mexico"]].sort_values("fecha").reset_index(drop=True)


def build_panel_mensual_completo(
    efes_monthly: pd.DataFrame,
    riesgo_paises: pd.DataFrame,
    aicm: pd.DataFrame,
    vuelos: pd.DataFrame,
    terminal: pd.DataFrame,
    who_mex: pd.DataFrame,
    cdmx_arrivals: pd.DataFrame,
    mty_proxy: pd.DataFrame,
) -> pd.DataFrame:
    efes_wide = (
        efes_monthly.pivot_table(
            index="anio_mes_dt",
            columns="sede",
            values=[
                "casos_confirmados",
                "casos_sospechosos",
                "total_registros",
                "tasa_confirmacion",
                "brote",
                "brote_estricto",
            ],
            aggfunc="first",
        )
        .reset_index()
    )

    efes_wide.columns = [
        f"{col[0]}_{col[1]}" if col[1] else col[0]
        for col in efes_wide.columns
    ]
    efes_wide = efes_wide.rename(columns={"anio_mes_dt": "fecha"})

    panel = (
        efes_wide.merge(aicm, on="fecha", how="left")
        .merge(vuelos, on="fecha", how="left")
        .merge(terminal, on="fecha", how="left")
        .merge(who_mex, on="fecha", how="left")
        .merge(cdmx_arrivals, on="fecha", how="left")
        .merge(mty_proxy, on="fecha", how="left")
        .sort_values("fecha")
        .reset_index(drop=True)
    )

    score_prom = float(riesgo_paises["score_riesgo_norm"].mean())
    panel["score_riesgo_equipos"] = score_prom
    panel["mes_num"] = panel["fecha"].dt.month
    panel["es_ventana_mundial"] = (
        (panel["fecha"].dt.year == 2026) & (panel["fecha"].dt.month.isin([6, 7]))
    ).astype(int)

    # Buscar lag óptimo por sede usando Pearson, como en notebook 3.
    LAGS = range(0, 7)
    lag_results: Dict[str, Dict[str, float]] = {}

    for _, nombre in SEDES.items():
        col_casos = f"casos_confirmados_{nombre}"
        if col_casos not in panel.columns:
            continue

        df_lag = panel[["fecha", "pasajeros_internacionales", col_casos]].dropna()
        if len(df_lag) < 8:
            lag_results[nombre] = {"mejor_lag": 1, "mejor_r": np.nan}
            continue

        correlaciones = []
        for lag in LAGS:
            if lag == 0:
                x = df_lag["pasajeros_internacionales"]
                y = df_lag[col_casos]
            else:
                x = df_lag["pasajeros_internacionales"].iloc[:-lag]
                y = df_lag[col_casos].iloc[lag:]

            if len(x) < 3 or len(y) < 3:
                correlaciones.append(np.nan)
                continue

            try:
                r, _ = stats.pearsonr(x, y)
            except Exception:
                r = np.nan
            correlaciones.append(r)

        corr_arr = np.array(correlaciones, dtype=float)
        if np.all(np.isnan(corr_arr)):
            best_lag = 1
            best_r = np.nan
        else:
            best_lag = int(list(LAGS)[np.nanargmax(np.abs(corr_arr))])
            best_r = float(corr_arr[np.nanargmax(np.abs(corr_arr))])

        lag_results[nombre] = {"mejor_lag": best_lag, "mejor_r": best_r}

    for _, nombre in SEDES.items():
        best_lag = int(lag_results.get(nombre, {}).get("mejor_lag", 1))
        panel[f"pax_intl_lag{best_lag}_{nombre}"] = panel["pasajeros_internacionales"].shift(best_lag)
        panel[f"vuelos_intl_lag{best_lag}_{nombre}"] = panel["operaciones_vuelos_internacionales"].shift(best_lag)

    # Para empatar con el diccionario final del proyecto, recortamos a 2020-01 .. 2025-12.
    panel = panel[(panel["fecha"] >= "2020-01-01") & (panel["fecha"] <= "2025-12-01")].copy()

    return panel.reset_index(drop=True)


# ============================================================
# Main
# ============================================================

def main() -> None:
    project_dir = Path(__file__).resolve().parents[2]
    raw_dir = project_dir / "data" / "raw"
    processed_dir = project_dir / "data" / "processed"
    ensure_dir(processed_dir)

    print("Cargando fuentes crudas...")
    efes = load_efes(raw_dir)
    measles = load_who_measles(raw_dir)
    vax = load_who_vaccination(raw_dir)
    df_qatar = load_qatar_attendance(raw_dir)
    wc_matches = load_world_cup_matches(raw_dir)

    aicm = load_aicm_passengers(raw_dir)
    terminal = load_aicm_terminal(raw_dir)
    vuelos = load_aicm_flights(raw_dir)
    who_mex = build_who_mexico_series(measles)
    cdmx_arrivals = load_cdmx_arrivals(raw_dir)
    mty_proxy = load_monterrey_proxy(raw_dir, aicm)

    print("Construyendo efes_mensual_sedes_target.csv ...")
    efes_target = build_efes_mensual_sedes_target(efes)
    efes_target.to_csv(processed_dir / "efes_mensual_sedes_target.csv", index=False)

    print("Construyendo paises_cluster_riesgo.csv ...")
    paises_riesgo = build_paises_cluster_riesgo(measles, vax, df_qatar, wc_matches)
    paises_riesgo.to_csv(processed_dir / "paises_cluster_riesgo.csv", index=False)

    print("Construyendo panel_mensual_completo.csv ...")
    panel = build_panel_mensual_completo(
        efes_monthly=efes_target,
        riesgo_paises=paises_riesgo,
        aicm=aicm,
        vuelos=vuelos,
        terminal=terminal,
        who_mex=who_mex,
        cdmx_arrivals=cdmx_arrivals,
        mty_proxy=mty_proxy,
    )
    panel.to_csv(processed_dir / "panel_mensual_completo.csv", index=False)

    print("\nArchivos generados:")
    print(f" - {processed_dir / 'efes_mensual_sedes_target.csv'}")
    print(f" - {processed_dir / 'paises_cluster_riesgo.csv'}")
    print(f" - {processed_dir / 'panel_mensual_completo.csv'}")


if __name__ == "__main__":
    main()
