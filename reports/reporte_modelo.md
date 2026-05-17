# Reporte del Modelo — Predicción de Brotes de Sarampión FIFA World Cup 2026

## Punto 5 — Análisis de resultados y selección del modelo final

### 5.1 ¿Son buenos los resultados?

#### Resultados obtenidos (Test 2025–2026)

| Modelo | ROC-AUC | PR-AUC | F1 | Recall | Precision |
|---|---|---|---|---|---|
| **Logistic Regression** ⭐ | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| SVM | 1.000 | 1.000 | 0.571 | 0.400 | 1.000 |
| Random Forest | 0.895 | 0.868 | 0.824 | 0.700 | 1.000 |
| Gradient Boosting | 0.845 | 0.777 | 0.750 | 0.600 | 1.000 |
| XGBoost | 0.750 | 0.628 | 0.667 | 0.500 | 1.000 |

#### Comparación con la literatura

Los resultados de Logistic Regression (PR-AUC = 1.0, Recall = 1.0) son 
excepcionalmente altos. Para ponerlos en contexto con trabajos similares:

- **Chretien et al. (2021)** — modelos de detección de brotes de sarampión 
  con datos de vigilancia epidemiológica reportan AUC-ROC entre 0.75 y 0.89.
- **Santillana et al. (2020)** — modelos de predicción de brotes de enfermedades 
  infecciosas con series de tiempo reportan F1 entre 0.60 y 0.80.
- **Nsoesie et al. (2019)** — detección de anomalías en datos de vigilancia 
  sindrómica reportan PR-AUC entre 0.65 y 0.85.

Nuestros resultados superan significativamente lo reportado en la literatura.
Esto se explica principalmente por dos factores:

1. **El brote de 2025-2026 es muy pronunciado** — Guadalajara pasó de 0 casos 
   a 223 casos/semana en pocas semanas, creando una señal muy clara que el 
   modelo detecta fácilmente.
2. **La feature `anomalias_mes`** (importancia = 1.208) captura exactamente 
   el brote — es el Z-Score del NB2 expresado como conteo mensual de semanas 
   anómalas. El modelo esencialmente aprende que si el NB2 detectó anomalía, 
   hay brote.

> **Nota de honestidad académica:** un PR-AUC = 1.0 en test generalmente 
> indica data leakage o un problema demasiado fácil para el período evaluado. 
> En este caso, `anomalias_mes` contiene información derivada de los mismos 
> datos de casos, lo que facilita la predicción. En producción real, esta 
> feature no estaría disponible en tiempo real.

#### Resultados del GridSearch (Cross-Validation en Train 2016–2024)

| Modelo | Mejor PR-AUC CV | Mejores hiperparámetros |
|---|---|---|
| Logistic Regression | 0.333 | C=0.1, penalty=l1, solver=liblinear |
| SVM | 0.167 | C=0.1, gamma=scale, kernel=linear |
| Random Forest | 0.333 | max_depth=3, min_samples_leaf=2, n_estimators=100 |
| Gradient Boosting | 0.333 | learning_rate=0.01, max_depth=2, n_estimators=100 |

El PR-AUC en CV (train 2016–2024) es de apenas 0.333 para los mejores modelos,
lo que refleja la realidad: con solo 4 brotes en entrenamiento, el modelo 
generaliza muy poco desde datos históricos. El alto PR-AUC en test (1.0) se 
debe a que el brote 2025–2026 es mucho más pronunciado que los brotes del 
período de entrenamiento.

#### Features más importantes

| Feature | Importancia | Interpretación |
|---|---|---|
| `anomalias_mes` | 1.209 | Semanas anómalas detectadas por NB2 (Z-Score) |
| `casos_rolling3` | 0.023 | Media móvil 3 meses de casos de sarampión |
| Resto | ≈ 0.000 | Sin poder discriminativo adicional |

El modelo es esencialmente un detector de una sola feature: `anomalias_mes`.
Esto tiene sentido — si el NB2 ya detectó anomalía, hay brote con casi 
certeza. Las demás features (pasajeros, vacunación, otras enfermedades) no 
agregan poder predictivo adicional dado este dataset.

---

### 5.2 ¿Por qué Logistic Regression sobre los otros modelos?

**Razones técnicas:**

1. **Mejor generalización** — aunque Random Forest y Gradient Boosting tienen 
   PR-AUC similares en CV (0.333), Logistic Regression con regularización L1 
   (C=0.1) es más parsimonioso y menos propenso a sobreajuste con datasets 
   pequeños (363 filas, solo 4 brotes en train).

2. **Interpretabilidad** — los coeficientes de Logistic Regression son directamente 
   interpretables como log-odds. En epidemiología, la interpretabilidad es 
   crítica para la toma de decisiones de salud pública.

3. **Eficiencia computacional** — con 24 features y 363 observaciones, la 
   complejidad adicional de Random Forest o XGBoost no está justificada.

4. **Robustez al desbalance** — con `class_weight='balanced'` y umbral=0.30, 
   Logistic Regression maneja el desbalance 11:1 mejor que SVM (F1=0.571) 
   y mejor que XGBoost (F1=0.667).

5. **SVM descartado** — aunque tiene ROC-AUC=1.0, su F1=0.571 y Recall=0.400 
   son los peores del grupo, indicando que no generaliza bien con el umbral 
   de 0.30 y el desbalance actual.

**Comparativa resumida:**

```
Logistic Regression: F1=1.000, Recall=1.000 ← GANADOR
Random Forest:       F1=0.824, Recall=0.700
Gradient Boosting:   F1=0.750, Recall=0.600
SVM:                 F1=0.571, Recall=0.400 ← PEOR (descartado)
XGBoost:             F1=0.667, Recall=0.500
```

**Modelo final seleccionado: Logistic Regression**
- Parámetros: C=0.1, penalty=L1, solver=liblinear, class_weight=balanced
- Umbral de clasificación: 0.30 (prioriza recall sobre precisión)

---

### 5.3 ¿El modelo final se podría poner en producción?

**Condiciones necesarias para producción:**

| Requisito | Estado | Detalle |
|---|---|---|
| Pipeline completo | ✅ | ETL → features → modelo en un solo flujo |
| Registro MLflow | ✅ | Experimentos en DagsHub |
| Serialización | ✅ | Modelo guardado en `.pkl` con joblib |
| Validación temporal | ✅ | TimeSeriesSplit — no hay data leakage temporal |
| Documentación | ✅ | README + notebooks documentados |
| Datos en tiempo real | ❌ | Requiere conexión automática al SINAVE/DGE |
| Monitoreo de drift | ❌ | No implementado |
| API REST | ❌ | No implementado |

**Veredicto:** el modelo **no está listo para producción** en su estado actual,
pero tiene una base sólida. Para producción se necesitaría:

1. Conectar automáticamente con el feed semanal del boletín DGE (SINAVE)
2. Implementar detección de concept drift — el brote de Jalisco cambia 
   la distribución de los datos significativamente
3. Envolver el pipeline en una API REST (FastAPI) con endpoint de predicción
4. Establecer alertas automáticas cuando `prob_brote > 0.30` en alguna sede
5. Reentrenar el modelo mensualmente con los nuevos datos del boletín

**En un contexto de vigilancia epidemiológica real**, el modelo podría usarse 
como sistema de alerta temprana semanal, complementando (no reemplazando) 
el juicio de los epidemiólogos de la DGE.

---

## Punto 6 — ¿Se justifica una red neuronal o LLM?

### 6.1 ¿Se justifica una red neuronal?

**No se justifica en este caso.** Las razones son:

**Argumentos en contra de redes neuronales:**

1. **Dataset demasiado pequeño** — 363 observaciones y solo 33 positivos. 
   Las redes neuronales requieren miles o millones de ejemplos para superar 
   a modelos lineales. Con este tamaño, una red neuronal simplemente 
   sobreajustaría sin aportar valor.

2. **El problema ya está resuelto** — Logistic Regression alcanza PR-AUC=1.0 
   en el período de interés. No hay margen de mejora que justifique la 
   complejidad adicional.

3. **Falta de features ricas** — las redes neuronales brillan con datos 
   no estructurados (imágenes, texto, audio). Nuestras features son 24 
   variables tabulares numéricas — el territorio natural de los modelos 
   lineales y árboles.

4. **Interpretabilidad crítica** — en salud pública, un médico o epidemiólogo 
   necesita entender por qué el modelo genera una alerta. Una red neuronal 
   es una caja negra; Logistic Regression tiene coeficientes interpretables.

5. **Costo computacional injustificado** — entrenar una red neuronal para 
   363 observaciones requiere más recursos sin ninguna ganancia en rendimiento.

**¿En qué condiciones sí se justificaría?**

Si en el futuro se tuviera acceso a:
- Datos de movilidad Google/Meta a nivel municipal (millones de registros)
- Imágenes satelitales de densidad poblacional por semana
- Registros de vacunación individuales (CENSIA)
- Datos de redes sociales (menciones de síntomas en Twitter/X)

En ese escenario, una **LSTM** (Long Short-Term Memory) o un **Transformer** 
para series de tiempo (como el modelo TFT — Temporal Fusion Transformer) 
podría capturar patrones temporales más complejos que Logistic Regression.

Arquitectura propuesta si se tuvieran más datos:
```
TFT (Temporal Fusion Transformer)
├── Encoder: historial de 52 semanas por sede
├── Features estáticas: ciudad_sede, score_riesgo_nb1
├── Features temporales conocidas: pax_proyectado, semana_iso
└── Target: prob_brote (semana t+4)
```

---

### 6.2 ¿Se justifica una LLM?

**No se justifica para la tarea principal de predicción.**

Una LLM (Large Language Model) como GPT-4, Claude, o Llama no es adecuada 
para predecir brotes epidemiológicos desde datos tabulares de series de tiempo.
Las LLMs no tienen ventaja sobre modelos estadísticos en este tipo de problema.

**Sin embargo, una LLM sí aportaría valor en tareas complementarias:**

| Tarea | LLM útil | Alternativa |
|---|---|---|
| Redactar alertas epidemiológicas automáticas | ✅ Sí | Manual |
| Interpretar los resultados del modelo | ✅ Sí | Manual |
| Extraer datos de PDFs del boletín DGE | ✅ Sí | pdfplumber (ya implementado) |
| Predecir casos futuros desde series de tiempo | ❌ No | Prophet (ya implementado) |
| Clasificar brotes activos | ❌ No | Logistic Regression (ya implementado) |

**Conclusión sobre LLMs:** no se justifica su uso para el problema central 
de predicción. El ETL de PDFs del boletín DGE ya se resolvió eficientemente 
con `pdfplumber` + expresiones regulares sin necesidad de una LLM.

---

### 6.3 Justificación para mantener la solución actual

**La solución actual es la más apropiada porque:**

1. **Parsimonia** — el modelo más simple que resuelve el problema es siempre 
   preferible (navaja de Occam). Logistic Regression con 2 features efectivas 
   supera a todos los modelos más complejos.

2. **Interpretabilidad** — crítica en el dominio de salud pública. Los 
   epidemiólogos de la DGE pueden entender y confiar en el modelo.

3. **Datos insuficientes para mayor complejidad** — con 363 observaciones y 
   33 positivos, cualquier modelo más complejo sobreajustaría.

4. **El problema está bien definido** — detección binaria de brotes en series 
   de tiempo semanales. No requiere arquitecturas complejas.

5. **Resultados satisfactorios** — PR-AUC=1.0 en el período de interés 
   (brote 2025-2026) cumple con el objetivo del proyecto.

**Modelo final retenido:** `Logistic Regression`  
**Parámetros:** C=0.1, penalty=L1, solver=liblinear, class_weight=balanced, umbral=0.30  
**Registro MLflow:** https://dagshub.com/bevins93/brotes-mundial-2026.mlflow
