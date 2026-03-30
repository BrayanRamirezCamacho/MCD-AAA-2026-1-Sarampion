# Predicción de brotes de sarampión en ciudades sede del Mundial 2026

## Hallazgos del EDA

### Notebook 1 — Perfil de riesgo de los equipos que juegan en México

El análisis de clustering K-Means (k=4, Silhouette=0.385) sobre los 9 equipos
confirmados para jugar en México identificó cuatro grupos de riesgo con
perfiles claramente diferenciados. El clustering jerárquico (Ward) produjo
exactamente la misma partición (ARI=1.000), lo que da máxima solidez a los
grupos encontrados.

Los loadings de PCA muestran que **PC1 está dominado por `mcv1_min` y
`mcv1_tendencia`** (cobertura en el peor año y tendencia de vacunación), y
**PC2 por `total_cases` vs `mcv1_mean`** — es decir, el eje de mayor
variación entre países es la estabilidad de su programa de vacunación,
no solo el nivel promedio.

Hallazgos por cluster:

- **Cluster 3 — Riesgo muy alto:** Solo Sudáfrica (2,475 casos, MCV1=83.5%,
  score=10.0). Es el equipo de mayor riesgo de importación entre los que
  juegan en México, con cobertura vacunal significativamente por debajo
  del umbral OMS del 95% y alta carga histórica de casos.

- **Cluster 0 — Riesgo moderado:** México (score=4.95) y Colombia (score=3.63).
  México presenta cobertura variable (MCV1 promedio=87.2%) y ya registra
  un brote activo en Jalisco en 2026. Colombia supera apenas el 91%.

- **Cluster 2 — Riesgo bajo:** Uruguay (score=0.0, solo 11 casos históricos,
  MCV1=95.5%). Mínimo riesgo de importación.

- **Cluster 1 — Riesgo muy bajo:** Corea del Sur, Túnez, Uzbekistán, Japón
  y España, todos con MCV1 promedio >96% y scores entre 0.33 y 1.69.
  Paradójicamente, Túnez y Uzbekistán tienen alta incidencia histórica
  (4,756 y 8,480 casos respectivamente) pero su cobertura vacunal reciente
  los coloca en riesgo bajo de exportar el virus.

### Notebook 2 — Anomalías en datos EFES por ciudad sede

La detección de anomalías sobre 68 meses por sede (2020–2026) reveló
patrones distintos en cada ciudad:

**Jalisco (Guadalajara)** es la sede de mayor preocupación. Los cuatro
meses con `brote_estricto=1` son todos recientes (sep-dic 2025), con casos
confirmados escalando de 16 a 148 en solo 4 meses. Esto indica un **brote
en curso y acelerándose** antes de que inicie el torneo. Cohen Kappa=0.705
entre IF y DBSCAN confirma alta concordancia entre métodos.

**CDMX** muestra dos episodios separados: uno en marzo-abril 2020
(75 y 65 casos respectivamente, coincidiendo con el inicio de la pandemia
y posible subnotificación posterior) y otro incipiente en sep-oct 2025
(1-2 casos). Cohen Kappa=0.705.

**Nuevo León (Monterrey)** es la sede con menor actividad. Solo 1 mes con
`brote_estricto=1` (jul-2025, 1 caso). Cohen Kappa=0.230 — baja concordancia
entre métodos, lo que sugiere que las anomalías detectadas en Monterrey son
marginales y poco robustas.

Los umbrales basales son extremadamente bajos en las tres sedes (P75=0,
P90<2 en CDMX, P95<11 en Jalisco), lo que confirma que el sarampión es
un evento raro en condiciones normales — cualquier incremento durante el
Mundial será fácilmente detectable.

### Notebook 3 — Correlación pasajeros-casos y proyección de riesgo

La correlación entre pasajeros internacionales al AICM y casos EFES
confirmados no mostró el patrón esperado de manera uniforme:

- **CDMX**: correlación negativa significativa en lag=0 (r=-0.264, p=0.030).
  Contraintuitivo: más pasajeros se asocia con menos casos notificados,
  posiblemente por un efecto de dilución en la vigilancia epidemiológica
  durante períodos de alta actividad turística.
- **Jalisco**: correlación positiva en lag=4 meses (r=0.237, p=0.059),
  marginalmente no significativa. El flujo de hace 4 meses es el mejor
  predictor de casos actuales — consistente con el período de incubación
  y propagación comunitaria.
- **Nuevo León**: sin correlación significativa en ningún lag (r=0.146,
  p=0.234 en lag=0).

La proyección estima **1.93 millones de pasajeros internacionales por mes**
durante junio-julio 2026 (+35% sobre el promedio post-COVID de 1.43M),
nivel sin precedente histórico en el AICM.

El índice de riesgo compuesto posiciona a **CDMX y Jalisco empatadas**
como las sedes de mayor riesgo (índice=10.0), seguidas de Monterrey (0.0),
principalmente por el número de partidos y el score de riesgo de los equipos
visitantes. El baseline histórico de casos en jun-jul es cero en todas las
sedes, lo que amplifica la incertidumbre de la proyección.

---

## Definición del problema supervisado

### ¿Qué problema se plantea resolver?

Predecir si en una ciudad sede del Mundial 2026 en México ocurrirá un
**brote de sarampión** durante los meses del torneo (junio–julio 2026),
con suficiente anticipación para que las autoridades de salud puedan
activar medidas preventivas.

### ¿Por qué es un problema importante?

El sarampión es altamente contagioso (R0 entre 12 y 18). México ya registra
un brote activo y acelerándose en Jalisco desde septiembre 2025, con 148
casos confirmados en diciembre. La concentración de aficionados de países
como Sudáfrica (MCV1=83.5%) en estadios con alta densidad, sumada a la
proyección de 1.93M de pasajeros internacionales mensuales durante el torneo,
crea condiciones para amplificación y dispersión nacional. Una alerta
temprana permite reforzar vacunación, intensificar vigilancia y preparar
respuesta hospitalaria antes de que el brote escale.

### ¿Qué problema de aprendizaje implica?

**Clasificación binaria** a nivel ciudad-sede × mes:

| Clase | Definición |
|---|---|
| `brote = 0` | Mes sin actividad anómala de sarampión en esa sede |
| `brote = 1` | Mes detectado como anómalo por IF y DBSCAN simultáneamente (`brote_estricto`) |

Se usa `brote_estricto` como target principal dado que los umbrales basales
son muy bajos (P75=0 en las tres sedes) — la regla laxa generaría demasiados
falsos positivos. El dataset tiene fuerte desbalance de clases: 9 meses
positivos de 204 totales (~4.4%), por lo que se aplicará SMOTE o
`class_weight='balanced'` en el modelo.

### Features del modelo

| Feature | Fuente | Tipo |
|---|---|---|
| `pax_intl_lag4_Jalisco` | AICM | Numérica continua |
| `pax_intl_lag1_CDMX` | AICM | Numérica continua |
| `operaciones_vuelos_intl_lag1` | AICM vuelos | Numérica continua |
| `score_riesgo_equipos` | Notebook 1 | Numérica continua (2.66 promedio) |
| `casos_confirmados_mes_anterior` | EFES | Numérica discreta |
| `tasa_confirmacion_lag1` | EFES | Numérica continua |
| `mcv1_mean_equipos_sede` | WHO vaccination | Numérica continua |
| `mes_num` | Calendario | Numérica (estacionalidad) |
| `es_ventana_mundial` | FIFA 2026 | Binaria |

### Métricas de evaluación

Dado que el costo de un **falso negativo** es mucho mayor que el de un
falso positivo, las métricas prioritarias son:

| Métrica | Valor deseable | Justificación |
|---|---|---|
| **Recall** | ≥ 0.80 | No perderse brotes reales |
| **F1-score** | ≥ 0.70 | Balance precisión-recall |
| **AUC-ROC** | ≥ 0.75 | Capacidad discriminativa general |
| Precisión | Secundaria | Falsas alarmas son tolerables |

### Alineación métricas–objetivos institucionales

Un modelo con **alto recall** garantiza que las autoridades de salud reciban
alertas en todos los meses de riesgo real. El costo de una alerta falsa
(campaña de vacunación o refuerzo de vigilancia innecesaria) es órdenes de
magnitud menor que el de un brote no detectado durante un evento con millones
de espectadores. La correlación de lag=4 encontrada en Jalisco es
especialmente valiosa: permite emitir alertas con 4 meses de anticipación
basadas en el flujo de pasajeros del mes actual.
