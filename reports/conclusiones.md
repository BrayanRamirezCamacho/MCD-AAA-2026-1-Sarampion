# Conclusiones del Proyecto — Predicción de Brotes de Sarampión FIFA World Cup 2026

**Equipo:** bevins93 / BrayanRamirezCamacho  
**Repositorio:** https://github.com/BrayanRamirezCamacho/MCD-AAA-2026-1-Sarampion  
**MLflow:** https://dagshub.com/bevins93/brotes-mundial-2026.mlflow  
**Fecha:** Mayo 2026

---

## Resumen ejecutivo

Este proyecto analizó el riesgo de brotes de sarampión en las tres ciudades
sede mexicanas del FIFA World Cup 2026 (CDMX, Guadalajara, Monterrey) usando
datos reales del Boletín Epidemiológico DGE 2016–2026, datos de la OMS,
y flujos de pasajeros internacionales.

La principal conclusión es que **Guadalajara (Jalisco) representa el mayor
riesgo epidemiológico durante el Mundial**, con un brote activo de sarampión
iniciado en septiembre 2025 que proyecta 1,598 casos durante las semanas
del torneo (sem 23–27, junio–julio 2026).

---

## Hallazgos por notebook

### NB1 — Clustering de países por riesgo de importación

Se agruparon los 8 equipos visitantes en 3 clusters usando K-Means y
Clustering Jerárquico (k=3, Silhouette=0.206, ARI=1.000).

**Resultados clave:**
- **Cluster alto riesgo:** Ucrania (score 10.0/10) y Sudáfrica (8.99/10)
  por alta carga histórica de sarampión (111,326 y 2,475 casos WHO 2018–2024)
- **Guadalajara** obtuvo score 7.84/10 por el brote local activo
- La concordancia entre K-Means y Clustering Jerárquico fue perfecta (ARI=1.000)

**Implicación:** los equipos que juegan en Monterrey (Ucrania, Túnez, Japón)
traen la mayor carga histórica de sarampión, aunque Ucrania tiene cobertura
vacunal MCV1 del 87% que atenúa el riesgo de transmisión.

---

### NB2 — Detección de anomalías en series de tiempo

Se aplicaron tres métodos complementarios (Z-Score, IQR, Umbral Relativo)
sobre el Boletín DGE 2016–2026. Una semana se clasifica como anómala si
al menos 2 de 3 métodos la detectan.

**Resultados clave:**
- Concordancia IQR vs Umbral Relativo: ARI = 1.000 (perfecta)
- Semanas anómalas por sede: Guadalajara=27, CDMX=18, Monterrey=8
- Casos proyectados durante el Mundial (sem 23–27):

| Sede | Casos | Nivel |
|---|---|---|
| Guadalajara | 296 | 🔴 Alto |
| CDMX | 37 | 🟡 Moderado |
| Monterrey | 10 | 🟢 Bajo |

**Implicación:** el brote de Jalisco iniciado en sem 38/2025 ya estaba
activo durante las semanas del Mundial con 296 casos — la sede más crítica.

---

### NB3 — Series de tiempo y correlación pasajeros–casos

Se analizó la correlación de Pearson entre pasajeros internacionales y
casos de sarampión con lags de 0 a 6 meses.

**Resultados clave:**

| Sede | Lag óptimo | r | Significativo |
|---|---|---|---|
| CDMX | 0m | -0.212 | ✅ p=0.019 |
| Guadalajara | 4m | 0.156 | ⚠️ n.s. |
| Monterrey | — | — | Sin varianza |

- Proyección de pasajeros jun–jul 2026: **1.93M pax/mes** (+35% factor Mundial)
- Dataset exportado: `panel_mensual_completo.csv` (363 filas × 22 features)

**Implicación:** la correlación negativa en CDMX sugiere que el mayor flujo
turístico coincide con períodos de alta vigilancia y vacunación. El lag de
4 meses en Guadalajara es consistente con el inicio del brote (sep-2025)
cuatro meses después del pico turístico de mayo-2025.

---

### NB4 — Modelo supervisado de clasificación de brotes

Se entrenaron 5 modelos con validación temporal (TimeSeriesSplit, 3 folds)
y búsqueda de hiperparámetros con GridSearchCV.

**Resultados en test (2025–2026, umbral=0.30):**

| Modelo | ROC-AUC | PR-AUC | F1 | Recall |
|---|---|---|---|---|
| **Logistic Regression** ⭐ | 1.000 | 1.000 | 1.000 | 1.000 |
| SVM | 1.000 | 1.000 | 0.571 | 0.400 |
| Random Forest | 0.895 | 0.868 | 0.824 | 0.700 |
| Gradient Boosting | 0.845 | 0.777 | 0.750 | 0.600 |
| XGBoost | 0.750 | 0.628 | 0.667 | 0.500 |

**Mejores hiperparámetros (GridSearch):**
- Logistic Regression: C=0.1, penalty=L1, solver=liblinear
- Random Forest: max_depth=3, min_samples_leaf=2, n_estimators=100
- Gradient Boosting: learning_rate=0.01, max_depth=2, n_estimators=100

**Features más importantes:**
1. `anomalias_mes` (importancia=1.209) — señal del NB2
2. `casos_rolling3` (importancia=0.023) — media móvil de casos

**Predicción durante el Mundial:**
- Guadalajara: prob_brote = 0.77 → **Muy Alto** 🔴
- CDMX: prob_brote = 0.01 → **Bajo** 🟢
- Monterrey: prob_brote = 0.00 → **Bajo** 🟢

**Modelo seleccionado:** Logistic Regression (C=0.1, L1, umbral=0.30)

---

### NB5 — Forecasting prospectivo + R₀ + exportación

Se entrenó Prophet con datos reales hasta semana 10/2026 (9 marzo 2026)
para proyectar las semanas 11–53 de 2026.

**R₀ de las EFE analizadas:**

| Enfermedad | R₀ | Nivel |
|---|---|---|
| Sarampión | 15.0 | 🔴 Muy alto |
| Varicela | 10.0 | 🟠 Alto |
| Rubéola | 6.0 | 🟡 Moderado-alto |
| Escarlatina | 4.0 | 🟡 Moderado |
| Erisipela | 1.5 | 🟢 Bajo |

**Forecast durante el Mundial (sem 23–27):**

| Sede | Casos proyectados | Nivel |
|---|---|---|
| Guadalajara | 1,598 | 🔴 Alto |
| CDMX | 272 | 🟡 Medio |
| Monterrey | 80 | 🟡 Medio |

**Riesgo de exportación (R₀=15, 30% visitantes internacionales):**
- Mayor riesgo: **Sudáfrica** — 33.35 casos secundarios esperados
  (MCV1=83.5%, 272 casos en sede CDMX)
- Fórmula: `casos_sec = casos × 0.30 × (1-MCV1/100) × R₀ × (1-MCV1/100)`

---

## Respuesta a las preguntas del proyecto

### ¿Son buenos los resultados?

Sí, en el período de interés (brote 2025–2026). El PR-AUC=1.0 de Logistic
Regression supera lo reportado en la literatura (0.65–0.85). Sin embargo,
el PR-AUC en cross-validation sobre datos históricos es de apenas 0.333,
lo que refleja la limitación real: solo 4 brotes en entrenamiento (2016–2024).

### ¿Por qué Logistic Regression?

Es el modelo más simple que maximiza F1 y Recall en el período de interés,
con coeficientes interpretables — crítico en salud pública. SVM tiene peor
F1 (0.571), y los modelos de árbol (RF, GB, XGB) tienen peor Recall.

### ¿El modelo se podría poner en producción?

Con modificaciones: requiere conexión automática al SINAVE/DGE, monitoreo
de drift, y una API REST. La base técnica (pipeline, MLflow, serialización)
ya está lista.

### ¿Se justifica una red neuronal o LLM?

No. Con 363 observaciones y 33 positivos, cualquier modelo más complejo
sobreajustaría. El problema ya está resuelto con Logistic Regression.
Una LLM podría aportar valor solo en tareas complementarias como redactar
alertas epidemiológicas automáticas.

---

## Recomendaciones epidemiológicas

1. **Guadalajara:** activar vigilancia intensificada desde semana 20/2026
   — el brote ya está activo con tendencia creciente
2. **CDMX:** monitorear semanalmente el flujo del AICM durante el torneo
3. **Monterrey:** riesgo bajo pero mantener alerta por partidos de Ucrania
   (mayor carga histórica WHO)
4. **Exportación:** notificar a Sudáfrica y Ucrania como países con mayor
   riesgo de casos secundarios post-Mundial
5. **Vacunación:** reforzar campañas de MCV1 en Jalisco antes del torneo

---

## Limitaciones del proyecto

1. Solo 4 brotes en datos de entrenamiento (2016–2024) — baja capacidad
   de generalización histórica
2. El forecast del NB5 es prospectivo — el Mundial no ha ocurrido (mayo 2026)
3. La correlación pasajeros-casos no es significativa para GDL ni MTY
4. Prophet no modela transmisión dinámica — es un modelo estadístico,
   no epidemiológico (SIR/SEIR)
5. Los datos de exportación son estimaciones basadas en supuestos de
   proporción de aficionados internacionales (30% FIFA estimado)

---

## Infraestructura MLOps implementada

| Componente | Herramienta | Estado |
|---|---|---|
| Control de versiones | GitHub + DagsHub | ✅ |
| Registro de experimentos | MLflow vía DagsHub | ✅ |
| Versionado de datos | Git + DagsHub | ✅ |
| Serialización de modelos | joblib (.pkl) | ✅ |
| Pipelines reproducibles | sklearn Pipeline | ✅ |
| Documentación | README + notebooks | ✅ |
| API de predicción | — | ❌ Pendiente |
| Monitoreo de drift | — | ❌ Pendiente |
| Reentrenamiento automático | — | ❌ Pendiente |

---

## Calidad de los datos y limitaciones técnicas del ETL

Los resultados de este proyecto deben interpretarse con cautela debido a
problemas estructurales en las fuentes de datos que afectan directamente
la calidad del análisis. A continuación se describen los principales
problemas encontrados:

### Cambio de fuente y formato 2020–2026

El Boletín Epidemiológico DGE reportó sarampión en formato PDF estructurado
(tablas por entidad federativa) únicamente hasta 2019. A partir de 2020,
la DGE migró al sistema **SEFE (Sistema Especial de Vigilancia Epidemiológica)**
con archivos CSV caso a caso, lo que implicó construir dos ETLs completamente
distintos para el mismo período de análisis:

- **2016–2019:** extracción de tablas PDF con `pdfplumber` + expresiones regulares
- **2020–2026:** filtrado de registros individuales del SEFE por `ENTIDAD_RES`
  y reconstrucción de la serie temporal semanal

Este cambio de metodología introduce una discontinuidad en la serie que
**no refleja un cambio epidemiológico real**, sino un cambio administrativo
en la forma de reportar.

### Falta de segregación por entidad en el SEFE

Los datos del Boletín clásico (2016–2019) ya venían agregados por entidad
federativa y semana epidemiológica. Los datos SEFE (2020–2026) vienen
**caso a caso**, sin agregación previa, lo que requirió:

1. Filtrar por código de entidad (`ENTIDAD_RES`: 9=CDMX, 14=Jalisco, 19=NL)
2. Calcular la semana ISO de cada caso desde `FECHA_DIAGNOSTICO`
3. Reagrupar manualmente para reconstruir la serie semanal

Este proceso introduce posibles errores de clasificación cuando la fecha
de diagnóstico difiere de la fecha de inicio de síntomas o de notificación.

### Datos proyectados mezclados con datos reales

El archivo `2026_efes_abierto_090326.csv` (corte oficial: 9 marzo 2026)
contiene fechas de diagnóstico hasta **noviembre 2027**, muy por encima
del corte real. Esto generó confusión inicial — se asumió erróneamente
que había datos post-Mundial disponibles, cuando en realidad el Mundial
aún no ha ocurrido (mayo 2026).

Para el análisis se usaron **únicamente las semanas 1–10 de 2026** como
datos reales confirmados, descartando todo lo posterior al corte de marzo 2026.

### Impacto en la calidad del modelo

Estos problemas de datos se reflejan directamente en el rendimiento del modelo:

| Métrica | Valor | Interpretación |
|---|---|---|
| PR-AUC en cross-validation (train 2016–2024) | **0.333** | El modelo apenas supera el azar con datos históricos |
| PR-AUC en test (2025–2026) | **1.000** | El brote actual es tan pronunciado que cualquier modelo lo detecta |
| Brotes en train | **4** | Insuficientes para aprender patrones generalizables |
| Brotes en test | **29** | Concentrados en el brote de Jalisco 2025–2026 |

El PR-AUC=1.0 en el período de test **no debe interpretarse como un modelo
perfecto**, sino como un reflejo de que el brote de Jalisco 2025–2026 es
tan inusual en magnitud que es trivialmente detectable por cualquier modelo
que tenga acceso a `anomalias_mes` — la feature más importante derivada
del propio Z-Score del NB2.

### Advertencia general sobre los resultados

> ⚠️ **Los resultados de este proyecto deben interpretarse como un ejercicio
> académico de análisis epidemiológico con datos reales pero imperfectos.**
> La inconsistencia en las fuentes (boletín PDF vs SEFE CSV), la escasez de
> brotes históricos en el período de entrenamiento, y la mezcla de datos
> reales con proyecciones en los archivos de 2026 limitan significativamente
> la capacidad del modelo para generalizar a situaciones futuras distintas
> al brote actual de Jalisco.
>
> Para un sistema de vigilancia epidemiológica real, se recomendaría trabajar
> directamente con la DGE para obtener datos históricos consistentes en un
> único formato, idealmente desde el SINAVE con series semanales completas
> por entidad desde 2000 en adelante.
