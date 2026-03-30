# Diccionario de datos — Fuentes crudas

## 1. WHO_Provisional_measles_and_rubella_data.csv
**Fuente:** Organización Mundial de la Salud (WHO)
**URL:** https://www.who.int/teams/immunization-vaccines-and-biologicals/immunization-analysis-and-insights/surveillance/monitoring/provisional-data
**Separador:** punto y coma (;) | **Encoding:** UTF-8 con BOM
**Granularidad:** País × mes × año | **Cobertura:** 2012–2026

| Columna | Tipo | Descripción |
|---|---|---|
| `Region` | string | Región WHO (AMR, EUR, AFR, etc.) |
| `Country` | string | Nombre del país en inglés |
| `ISO3` | string | Código ISO 3166-1 alpha-3 |
| `Year` | int | Año del reporte |
| `Month` | int | Mes del reporte (1–12) |
| `Measles suspect` | float | Casos sospechosos de sarampión |
| `Measles clinical` | float | Casos con diagnóstico clínico |
| `Measles epi-linked` | float | Casos confirmados por nexo epidemiológico |
| `Measles lab-confirmed` | float | Casos confirmados por laboratorio |
| `Measles total` | float | Total de casos de sarampión |
| `Rubella clinical` | float | Casos clínicos de rubéola |
| `Rubella epi-linked` | float | Casos de rubéola por nexo epi |
| `Rubella lab-confirmed` | float | Casos de rubéola por laboratorio |
| `Rubella Total` | float | Total de casos de rubéola |
| `Discarded` | float | Casos descartados |

**Nota de carga:** Los nombres de columna contienen `\n` literal.
Aplicar `.str.replace('\n', ' ')` al cargar.

---

## 2. WHO_vaccination-coverage.csv
**Fuente:** Our World in Data / WHO
**URL:** https://ourworldindata.org/vaccination
**Separador:** coma | **Encoding:** UTF-8
**Granularidad:** País × año | **Cobertura:** 1980–2023

| Columna | Tipo | Descripción |
|---|---|---|
| `Entity` | string | Nombre del país |
| `Code` | string | Código ISO3 |
| `Year` | int | Año |
| `Measles, first dose (MCV1)` | float | Cobertura primera dosis sarampión (%) |
| `Hepatitis B (HepB3)` | float | Cobertura Hepatitis B tercera dosis (%) |
| `H. influenza type b (Hib3)` | float | Cobertura Hib tercera dosis (%) |
| `Inactivated polio vaccine (IPV)` | float | Cobertura polio inactivada (%) |
| `Pneumococcal vaccine (PCV3)` | float | Cobertura neumococo tercera dosis (%) |
| `Polio (Pol3)` | float | Cobertura polio tercera dosis (%) |
| `Rubella (RCV1)` | float | Cobertura rubéola primera dosis (%) |
| `Rotavirus (RotaC)` | float | Cobertura rotavirus (%) |
| `Yellow fever (YFV)` | float | Cobertura fiebre amarilla (%) |
| `Diptheria/tetanus/pertussis (DTP3)` | float | Cobertura DTP tercera dosis (%) |

---

## 3. EFES 2020–2026 (7 archivos)
**Fuente:** Dirección General de Epidemiología (DGE) — Secretaría de Salud México
**URL:** https://www.gob.mx/salud/acciones-y-programas/informacion-epidemiologica
**Separador:** coma | **Encoding:** UTF-8 | **2024:** formato .xlsx
**Granularidad:** Caso individual | **Cobertura:** Un archivo por año

| Columna | Tipo | Descripción |
|---|---|---|
| `FECHA_ACTUALIZACION` | date | Fecha de última actualización del registro |
| `ID_REGISTRO` | int | Identificador único del caso |
| `EDAD_ANOS` | int | Edad en años del paciente |
| `EDAD_MESES` | int | Edad en meses (complemento) |
| `EDAD_DIAS` | int | Edad en días (complemento) |
| `SEXO` | int | 1=Masculino, 2=Femenino |
| `HABLA_LENGUA_INDIG` | int | 1=Sí, 2=No |
| `INDIGENA` | int | 1=Sí, 2=No |
| `ENTIDAD_UM_NOTIF` | int | Clave INEGI de entidad de la unidad médica notificante |
| `MUNICIPIO_UM_NOTIF` | int | Clave de municipio de la unidad médica notificante |
| `ENTIDAD_RES` | int | Clave INEGI de entidad de residencia del paciente |
| `MUNICIPIO_RES` | int | Clave de municipio de residencia |
| `INSTITUCION_NOTIF` | int | Institución que notifica (IMSS=1, ISSSTE=2, etc.) |
| `VACUNACION` | int | 1=Vacunado, 2=No vacunado, 9=Se ignora |
| `EXANTEMA` | int | 1=Sí presenta exantema, 2=No |
| `FIEBRE` | int | 1=Sí presenta fiebre, 2=No |
| `COMPLICACIONES` | int | 1=Con complicaciones, 2=Sin complicaciones |
| `DEFUNCION` | int | 1=Defunción, 2=No defunción |
| `DIAGNOSTICO` | int | **0=Descartado, 1=Sarampión confirmado, 3=Otro diagnóstico** |
| `CRITERIO_DIAGNOSTICO` | int | 0=En estudio, 1=Lab, 2=Nexo epidemiológico |
| `FECHA_DIAGNOSTICO` | date | Fecha del diagnóstico final (9999-99-99 = pendiente) |
| `ORIGEN_CASO` | float | 1=Importado, 2=Relacionado importado, 4=Endémico, 5=Desconocido |

**Entidades sede del Mundial 2026:**
- `09` = Ciudad de México (Estadio Azteca)
- `14` = Jalisco (Estadio Akron, Guadalajara)
- `19` = Nuevo León (Estadio BBVA, Monterrey)

---

## 4. Movimiento_operacional_de_pasajeros_de_AICM.csv
**Fuente:** Aeropuerto Internacional de la Ciudad de México (AICM)
**Separador:** coma | **Encoding:** UTF-8
**Granularidad:** Mes × año | **Cobertura:** 2015–2026

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | int | Año |
| `mes` | string | Mes en español (enero, febrero, …) |
| `pasajeros_nacionales` | int | Total de pasajeros en vuelos nacionales |
| `pasajeros_internacionales` | int | Total de pasajeros en vuelos internacionales |

---

## 5. Movimiento_operacional_de_pasajeros_por_terminal.csv
**Fuente:** AICM
**Separador:** coma | **Encoding:** UTF-8
**Granularidad:** Mes × año × terminal | **Cobertura:** 2016–2026

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | int | Año |
| `mes` | string | Mes en español |
| `pasajeros_llegadas_nacionales_t1` | int | Llegadas nacionales Terminal 1 |
| `pasajeros_salidas_nacionales_t1` | int | Salidas nacionales Terminal 1 |
| `pasajeros_llegadas_internacionales_t1` | int | Llegadas internacionales Terminal 1 |
| `pasajeros_salidas_internacionales_t1` | int | Salidas internacionales Terminal 1 |
| `pasajeros_llegadas_nacionales_t2` | int | Llegadas nacionales Terminal 2 |
| `pasajeros_salidas_nacionales_t2` | int | Salidas nacionales Terminal 2 |
| `pasajeros_llegadas_internacionales_t2` | int | Llegadas internacionales Terminal 2 |
| `pasajeros_salidas_internacionales_t2` | int | Salidas internacionales Terminal 2 |

---

## 6. Movimiento_operacional_de_vuelos.csv
**Fuente:** AICM
**Separador:** coma | **Encoding:** UTF-8
**Granularidad:** Mes × año | **Cobertura:** 2015–2026

| Columna | Tipo | Descripción |
|---|---|---|
| `anio` | int | Año |
| `mes` | string | Mes en español |
| `operaciones_vuelos_nacionales` | int | Número de operaciones en vuelos nacionales |
| `operaciones_vuelos_internacionales` | int | Número de operaciones en vuelos internacionales |

---

## 7. Llegadas_aeropuerto_Extranjeros(Hoja3).csv
**Fuente:** AICM / Secretaría de Turismo
**Separador:** punto y coma (;) | **Encoding:** UTF-8 con BOM
**Granularidad:** Año | **Cobertura:** 2012–2024
**Uso en el proyecto:** Proxy de flujo internacional hacia Monterrey

| Columna | Tipo | Descripción |
|---|---|---|
| `Periodo` | int | Año |
| `Llegadas de Pasajeros Nacionales` | string | Total anual nacionales (formato: 1.234.567) |
| `Llegada de Pasajeros Internacionales` | string | Total anual internacionales |
| `Llegada Total de Pasajeros` | string | Total anual combinado |

**Nota de carga:** Los números usan punto como separador de miles.
Aplicar `.str.replace('.', '')` antes de convertir a numérico.

---

## 8. Llegadas_internacionales_cdmx_mensual.csv
**Fuente:** SEDETUR / INEGI
**Separador:** coma | **Encoding:** UTF-8
**Granularidad:** Mes | **Cobertura:** sep 2018 – jun 2024

| Columna | Tipo | Descripción |
|---|---|---|
| `fecha` | date | Último día del mes (formato YYYY-MM-DD) |
| `ciudad_de_mexico` | int | Llegadas internacionales a CDMX ese mes |
| `temporal_fecha` | string | Período en formato YYYY-MM |
| `..anio_fecha` | int | Año (columna auxiliar) |

---

## 9. Qatar 2022 FIFA World Cup Attendance
**Fuente:** Kaggle — parasharmanas/qatar-2022-fifa-world-cup-attendance
**Carga:** `kagglehub.load_dataset(..., "Attendance Sheet.csv")`
**Granularidad:** Partido | **Cobertura:** Qatar 2022 (64 partidos)

| Columna | Tipo | Descripción |
|---|---|---|
| `Date` | string | Fecha del partido |
| `Time` | string | Hora local y hora Qatar |
| `Home` | string | Equipo local |
| `Away` | string | Equipo visitante |
| `Attendance` | string | Asistencia al partido (formato: 67,372) |
| `Venue` | string | Estadio |

---

## 10. FIFA World Cup 1930–2018 (wcmatches.csv)
**Fuente:** Kaggle — evangower/fifa-world-cup
**Carga:** `kagglehub.dataset_download("evangower/fifa-world-cup")`
**Granularidad:** Partido | **Cobertura:** 1930–2018

| Columna | Tipo | Descripción |
|---|---|---|
| `year` | int | Año del Mundial |
| `country` | string | País anfitrión |
| `city` | string | Ciudad del partido |
| `stage` | string | Fase (Group, Quarter-final, Final, etc.) |
| `home_team` | string | Equipo local |
| `away_team` | string | Equipo visitante |
| `home_score` | int | Goles equipo local |
| `away_score` | int | Goles equipo visitante |
| `outcome` | string | H=Local, A=Visitante, D=Empate |
| `win_conditions` | string | Condición especial (penales, prórroga) |
| `winning_team` | string | Equipo ganador |
| `losing_team` | string | Equipo perdedor |
| `date` | date | Fecha del partido |
| `month` | string | Mes abreviado |
| `dayofweek` | string | Día de la semana |
