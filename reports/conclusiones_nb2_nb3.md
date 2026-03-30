# Conclusiones Notebook 2 — Detección de anomalías EFES

## Respuestas a las preguntas guía

### 1. ¿Qué meses históricos fueron detectados como anómalos por ambos métodos?

**CDMX** — 4 meses con brote_estricto=1:
- Mar-Apr 2020: 75 y 65 casos respectivamente. Coincide con el inicio
  de la pandemia COVID-19 cuando la vigilancia epidemiológica se intensificó
  masivamente y muchos casos febriles con exantema fueron notificados al
  sistema. Posiblemente sobrenotificación por el contexto pandémico.
- Sep-Oct 2025: 2 y 1 caso. Señal incipiente, marginal en número pero
  relevante porque rompe el patrón de cero casos que caracterizó 2021-2024.

**Jalisco (Guadalajara)** — 4 meses con brote_estricto=1:
- Sep–Dic 2025: 16, 129, 122, 148 casos. Este es el hallazgo más crítico
  del proyecto. El patrón muestra aceleración sostenida mes a mes, con
  148 casos confirmados en diciembre 2025. El brote está activo y creciendo
  antes del inicio del torneo.

**Nuevo León (Monterrey)** — 1 mes con brote_estricto=1:
- Jul 2025: 1 caso. Señal extremadamente débil. La baja Cohen Kappa (0.230)
  sugiere que este mes fue detectado por IF pero con poca convicción de DBSCAN.

### 2. ¿Qué sede muestra más meses anómalos?

Jalisco y CDMX empatan en 4 meses cada una, pero **Jalisco es la sede
más preocupante** por la magnitud y tendencia de los casos (148 en dic 2025
vs máximo de 2 en CDMX en el mismo período).

### 3. ¿Qué regla de brote se usará?

Se usa **brote_estricto** (IF y DBSCAN coinciden) como target del modelo
supervisado. Justificación: los umbrales basales son P75=0 en las tres
sedes, lo que significa que la regla laxa etiquetaría como brote cualquier
mes con 1 caso, generando demasiado ruido. La regla estricta (9 meses
positivos de 204) es más conservadora pero más confiable.

### 4. ¿El Cohen Kappa entre métodos es alto o bajo?

- CDMX: κ=0.705 — buena concordancia, los dos métodos ven lo mismo.
- Jalisco: κ=0.705 — ídem, los brotes son lo suficientemente pronunciados
  para que ambos algoritmos los detecten sin ambigüedad.
- Nuevo León: κ=0.230 — baja concordancia. Las anomalías en Monterrey
  son marginales y los métodos discrepan, lo que reduce la confianza
  en los labels de esa sede.

### 5. ¿La ventana del Mundial ya muestra señal?

Los datos EFES llegan hasta marzo 2026. La tendencia en Jalisco
(16→129→122→148 en sep-dic 2025) es una señal clara de que el brote
podría continuar hacia junio-julio 2026. CDMX muestra actividad incipiente.
Monterrey no muestra señal relevante.

---

# Conclusiones Notebook 3 — Series de tiempo y proyección

## Respuestas a las preguntas guía

### 1. ¿Existe correlación significativa entre pasajeros y casos?

Solo en CDMX y de forma inesperada: correlación **negativa** significativa
(r=-0.264, p=0.030) en lag=0. Jalisco muestra correlación positiva marginal
(r=0.237, p=0.059) en lag=4 pero no alcanza el umbral de significancia
convencional (p<0.05).

### 2. ¿La correlación es positiva o negativa?

En CDMX es negativa, contraria a la hipótesis original. Una explicación
plausible: los períodos de alta afluencia turística internacional en CDMX
(que elevan el conteo de pasajeros) son períodos en que la vigilancia
epidemiológica se orienta a otras prioridades, reduciendo la notificación
de casos EFES. Otra explicación: los brotes en CDMX (2020) ocurrieron
en período de baja movilidad internacional (pandemia).

En Jalisco la correlación positiva con lag=4 es más consistente con la
hipótesis, pero la muestra de 64 meses es insuficiente para confirmarla
con el nivel de significancia estándar.

### 3. ¿Qué sede tiene el índice de riesgo más alto?

CDMX y Jalisco empatan con índice=10.0, Monterrey=0.0. El empate se debe
a que el componente dominante (score de equipos × partidos) es igual
en ambas sedes (4 partidos, mismo score promedio de equipos = 2.66).
El baseline histórico de casos en jun-jul es cero en las tres sedes,
lo que no diferencia entre ellas.

### 4. ¿El factor Mundial de +35% es razonable?

El promedio post-COVID (2022-2025) de jun-jul es 1.43M pax/mes.
Con +35% la proyección es 1.93M pax/mes. Este factor es conservador:
FIFA estima 5 millones de visitantes totales para los 104 partidos,
y México recibirá aproximadamente 20 partidos (de los cuales 10 son
en las 3 sedes analizadas). Recomendación: verificar con estimaciones
oficiales de SECTUR o CPTM cuando estén disponibles.

### 5. ¿Qué features del panel son más prometedoras?

Basado en los resultados:
1. `casos_confirmados_Jalisco_lag1` — el mes anterior en Jalisco es el
   predictor más directo del mes actual dado el brote activo.
2. `pax_intl_lag4_Jalisco` — único lag con correlación positiva (p=0.059).
3. `mes_num` — la estacionalidad muestra que jun-jul no son meses de alta
   actividad basal, haciendo cualquier incremento más notable.
4. `score_riesgo_equipos` — constante en este dataset pero variará cuando
   se actualicen los clasificados definitivos al 2026.
5. `es_ventana_mundial` — feature binaria que captura el efecto del evento.
