# Diccionario de datos — Datos procesados

Todos los archivos se generan en `content/data/processed/`
ejecutando `src/data/make_dataset.py`.

---

## 1. efes_mensual_sedes_target.csv
**Generado por:** Notebook 2 / `make_dataset.py` bloque 2-3
**Granularidad:** Sede × mes | **Shape:** 204 filas × 16 columnas
**Cobertura:** ene 2020 – mar 2026 | **Sedes:** CDMX, Jalisco (Gdl), Nuevo León (Mty)

| Columna | Tipo | Descripción |
|---|---|---|
| `anio_mes` | period | Período mensual (YYYY-MM) |
| `anio_mes_dt` | datetime | Primer día del mes (timestamp) |
| `ENTIDAD_RES` | int | Clave INEGI de la entidad (9, 14, 19) |
| `sede` | string | Nombre de la sede ('CDMX', 'Jalisco (Gdl)', 'Nuevo León (Mty)') |
| `casos_confirmados` | int | Casos EFES con DIAGNOSTICO=1 ese mes |
| `casos_sospechosos` | int | Casos EFES con DIAGNOSTICO=3 ese mes |
| `casos_descartados` | int | Casos EFES con DIAGNOSTICO=0 ese mes |
| `total_registros` | int | Total de registros EFES ese mes en la sede |
| `vacunados` | int | Casos con VACUNACION=1 |
| `con_complicaciones` | int | Casos con COMPLICACIONES=1 |
| `tasa_confirmacion` | float | casos_confirmados / total_registros |
| `anomalia_if` | bool | True si Isolation Forest lo clasifica como anómalo |
| `if_score` | float | Score de anomalía IF (más negativo = más anómalo) |
| `anomalia_db` | bool | True si DBSCAN lo clasifica como ruido (label=-1) |
| `db_label` | int | Etiqueta de cluster DBSCAN (-1=ruido, ≥0=cluster) |
| `brote` | int | **Target laxa:** 1 si IF o DBSCAN detectan anomalía |
| `brote_estricto` | int | **Target estricta:** 1 si IF y DBSCAN coinciden |

**Distribución del target:**

| Sede | brote_laxa | brote_estricto |
|---|---|---|
| CDMX | 7 | 4 |
| Jalisco (Gdl) | 7 | 4 |
| Nuevo León (Mty) | 7 | 1 |
| **Total** | **21** | **9** |

**Meses con brote_estricto=1:**

| Sede | Mes | Casos confirmados |
|---|---|---|
| CDMX | 2020-03 | 75 |
| CDMX | 2020-04 | 65 |
| CDMX | 2025-09 | 2 |
| CDMX | 2025-10 | 1 |
| Jalisco (Gdl) | 2025-09 | 16 |
| Jalisco (Gdl) | 2025-10 | 129 |
| Jalisco (Gdl) | 2025-11 | 122 |
| Jalisco (Gdl) | 2025-12 | 148 |
| Nuevo León (Mty) | 2025-07 | 1 |

---

## 2. paises_cluster_riesgo.csv
**Generado por:** Notebook 1 / `make_dataset.py` bloque 4
**Granularidad:** País (equipo confirmado para jugar en México)
**Shape:** 9 filas × 12 columnas

| Columna | Tipo | Descripción |
|---|---|---|
| `Country` | string | Nombre del país (nombre FIFA) |
| `Country_who` | string | Nombre del país en WHO (para joins) |
| `ciudad_sede` | string | Ciudad sede principal en México |
| `partidos_en_mexico` | int | Total de partidos que juega en México |
| `asistencia_promedio` | float | Asistencia promedio en Qatar 2022 (proxy hinchada) |
| `partidos_historicos` | int | Partidos jugados en Mundiales 1930–2018 |
| `clasificado_2026` | int | 1 para todos (confirmados en México) |
| `total_cases` | float | Total de casos de sarampión 2018–2024 (WHO) |
| `avg_monthly_cases` | float | Promedio mensual de casos 2018–2024 |
| `months_with_cases` | int | Meses con al menos 1 caso 2018–2024 |
| `mcv1_mean` | float | Cobertura MCV1 promedio 2018–2023 (%) |
| `mcv1_min` | float | Cobertura MCV1 mínima 2018–2023 (%) |
| `mcv1_tendencia` | float | Pendiente lineal de MCV1 (positivo=mejora) |
| `cluster` | int | Cluster K-Means asignado (k=4, Silhouette=0.385) |
| `score_riesgo_norm` | float | Score de riesgo compuesto normalizado (0–10) |

**Valores por país:**

| País | cluster | ciudad_sede | score_riesgo_norm |
|---|---|---|---|
| South Africa | 3 | Monterrey | 10.00 |
| Mexico | 0 | CDMX | 4.95 |
| Colombia | 0 | CDMX | 3.63 |
| Tunisia | 1 | Monterrey | 1.69 |
| Japan | 1 | Monterrey | 1.24 |
| Spain | 1 | Guadalajara | 1.06 |
| South Korea | 1 | Guadalajara | 1.00 |
| Uzbekistan | 1 | CDMX | 0.33 |
| Uruguay | 2 | Guadalajara | 0.00 |

---

## 3. panel_mensual_completo.csv
**Generado por:** Notebook 3 / `make_dataset.py` bloque 5
**Granularidad:** Mes | **Shape:** 70 filas × 35 columnas
**Cobertura:** ene 2020 – dic 2025
**Uso:** Input directo del modelo supervisado

### Columnas de target (variable a predecir)

| Columna | Tipo | Descripción |
|---|---|---|
| `brote_CDMX` | int | brote_estricto mensual en CDMX |
| `brote_Jalisco (Gdl)` | int | brote_estricto mensual en Jalisco |
| `brote_Nuevo León (Mty)` | int | brote_estricto mensual en Nuevo León |

### Columnas de features — casos EFES

| Columna | Tipo | Descripción |
|---|---|---|
| `casos_confirmados_CDMX` | float | Casos confirmados ese mes en CDMX |
| `casos_confirmados_Jalisco (Gdl)` | float | Casos confirmados ese mes en Jalisco |
| `casos_confirmados_Nuevo León (Mty)` | float | Casos confirmados ese mes en Nuevo León |
| `casos_sospechosos_{sede}` | float | Casos sospechosos por sede |
| `tasa_confirmacion_{sede}` | float | Proporción confirmados/total por sede |
| `total_registros_{sede}` | float | Total notificaciones por sede |

### Columnas de features — pasajeros

| Columna | Tipo | Descripción |
|---|---|---|
| `pasajeros_internacionales` | float | Pax internacionales AICM ese mes |
| `pasajeros_nacionales` | float | Pax nacionales AICM ese mes |
| `operaciones_vuelos_internacionales` | float | Operaciones de vuelos internacionales |
| `pax_intl_total` | float | Pax internacionales T1+T2 (terminal) |
| `pax_intl_lag1_CDMX` | float | Pax internacionales con lag=1 mes (CDMX) |
| `pax_intl_lag4_Jalisco (Gdl)` | float | Pax internacionales con lag=4 meses (Jalisco) |
| `pax_intl_lag1_Nuevo León (Mty)` | float | Pax internacionales con lag=1 mes (NL) |
| `vuelos_intl_lag1_{sede}` | float | Vuelos internacionales con lag óptimo |

### Columnas de features — contexto y calendario

| Columna | Tipo | Descripción |
|---|---|---|
| `score_riesgo_equipos` | float | Score promedio de riesgo de equipos en México (2.66) |
| `es_ventana_mundial` | int | 1 si el mes es jun o jul 2026 |
| `mes_num` | int | Número de mes 1–12 (estacionalidad) |

### Nulos

Los 2 nulos en columnas EFES corresponden a los primeros 2 meses del
dataset donde el lag introduce NaN por diseño.
Los 4 nulos en `pax_intl_lag4_Jalisco` corresponden a los primeros 4
meses por el lag=4.
