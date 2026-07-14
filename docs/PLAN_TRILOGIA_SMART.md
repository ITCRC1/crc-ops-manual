# Plan de implementación — Trilogía SMART

> **Estado 2026-07-11**
> `SOP SMART ✅` (151 en prod) · `JD SMART ✅` (94/95, prod conciliado) ·
> `Training SMART ✅` **infraestructura montada y en vivo** ·
> `Training Records ⏳` **pendiente — gated por datos (roster) y sign-off legal.**
>
> Objetivo de la trilogía: un solo sistema documental integrado y auditable —
> `Persona → Puesto → JD SMART → Responsabilidad → SOP SMART → Capacitación → Registro → Evidencia → Vencimiento`.

Plan creado 2026-07-10 · **última actualización 2026-07-11** (JD SMART cerrado + Training SMART infra desplegada).

---

## 0. Estado verificado (dónde estamos hoy)

| Pieza | Estado |
|---|---|
| **SOP SMART** | ✅ En prod (151 SOPs, `SMART-1.0`). Columna `sop_master.smart` + `SopSmartView` + `PUT /api/sops/{id}/smart`. |
| **JD SMART** | ✅ **94/95** con capa `descriptor_puesto_master.smart`, en local y prod (conciliados por título; ver `jd_smart_backup/HANDOFF.md`). Falta 1 JD "flaco" (`JD-028 Gerente Residente`, sin prosa base). Vista + editor en vivo. |
| **Crosswalk JD↔SOP** | ✅ Existe **dentro de** `smart.sops_relacionados` + `smart.matriz_jd_sop` (JSON por JD). No hay tabla relacional rica separada — no hace falta para v1; la derivación (Fase 3) lee ese JSON. |
| **Training SMART (fichas)** | ✅ **Infra en vivo** (commit `9ec46cc`): columna `training_manual.smart` (`TRAIN-SMART-1.0`) + `PUT /api/capacitacion/manuales/{id}/smart` + `TrainingSmartView`/`TrainingSmartForm`. **Fichas vacías** — se redactan dentro del sistema (o se pueblan por IA a futuro). |
| **Training (contenido)** | `training_manual` (19 local / 12 prod) + `training_seccion` (163). Es CURRÍCULO. |
| **Training Records** | ❌ No construido: sin catálogo, requisitos, registros ni evidencias. |
| **Titulares (personas)** | `propiedad_puesto_ocupante` = **0 filas**. Sin roster no hay a quién capacitar. |
| **Organigrama** | ⚠️ `reporta_a` colgantes (apuntaban a puestos soft-deleted). **Re-verificar** tras la conciliación de roster de 2026-07-11. Bloquea RBAC por supervisor. |
| **Infra** | Subida de archivos SÍ (`intake.py`). **No** hay scheduler. **No** hay volumen persistente en `railway.toml`. Migraciones corren solas en cada deploy (Dockerfile). |

**Lo que resta de toda la trilogía = Training Records** (Fases T1–T5 abajo). Todo lo demás está hecho.

---

## 1. Decisiones de arquitectura (estado)

| # | Decisión | Resolución |
|---|---|---|
| **D1** | ¿SMART en BD o markdown? | ✅ **BD** (JSONB + vistas). Confirmado por SOP/JD/Training SMART. |
| **D2** | ¿Tabla `Employees` nueva o reutilizar? | **Extender `propiedad_puesto_ocupante` + `usuario`.** 1 persona ocupa 1 puesto EN 1 hotel. |
| **D3** | Alertas de vencimiento | **Compute-on-read** en v1 (no hay scheduler). Job programado = mejora posterior. |
| **D4** | Evidencias (archivos) | Reutilizar `intake`; **provisionar volumen persistente en Railway** antes de guardar adjuntos en prod. v1 puede ser metadatos + enlace. |
| **D5** | Requisitos vs cumplimiento | Requisitos = **maestro (JD/SOP)**; cumplimiento = **por titular en cada propiedad**. |
| **D6** | ¿Cómo se describe cada training? | ✅ **RESUELTO — "Training SMART" propio** (ficha estructurada `TRAIN-SMART-1.0` redactada en el sistema), NO solo enlazar manuales. Ya implementado. |

**Decisiones operativas aún pendientes del owner** (no bloquean arrancar T1):
- **Org-graph**: resolver los `reporta_a` colgantes → ¿reasignar a `JD-028` o restaurar los puestos borrados? (por caso). Prerequisito del RBAC por supervisor (T4).
- **Prod cleanup**: ¿alinear el set de manuales/JD de prod (12 vs 19 manuales; fixtures)? — cosmético, no bloquea.
- **Roster**: ¿cómo entran las personas — import de HR o carga manual en la UI? Define el esfuerzo de T2.
- **Sign-off legal**: quién firma las capacitaciones mandatorias (HR / Legal / Salud Ocupacional).

---

## 2. Plan restante — Training Records (5 etapas)

> Ingeniería ≈ **4.5 semanas** (camino crítico) + **1 sola corrida de IA** (la de JD SMART ya se hizo) + trabajo humano que **domina el calendario real** (roster + firma legal).
> Nada de esto muestra valor hasta que exista **roster** (personas) — por eso T2 arranca en paralelo desde el día 1.

### T1 — Prerrequisitos (≈0.5 sem eng)
- [ ] **Org-graph**: re-verificar y resolver los `reporta_a` colgantes (decisión por caso) y aplicar. *Prerequisito del RBAC por supervisor.*
- [ ] **Volumen persistente en Railway** para evidencias (si D4 = adjuntos en prod). El disco de Railway es efímero sin volumen.
- [ ] **Paridad de esquema local↔prod**: confirmar que las nuevas migraciones aplican igual en ambos (ya es el caso vía Dockerfile).

### T2 — Esqueleto de datos + API + UI (≈2 sem eng) · roster en paralelo (RH)
La etapa grande. No depende del contenido SMART, sí de las tablas base.
- [ ] **Modelo + migraciones**:
  - `training_catalog` — el ítem de capacitación (puede apuntar a un `training_manual` como material y/o a su ficha `TRAIN-SMART`).
  - `training_requirement` — qué training exige qué puesto/depto (origen: JD, SOP, o regla; `mandatoria`, `vigencia_meses`, `validation_status`).
  - `employee_training_record` — quién tomó qué, cuándo, resultado, vencimiento.
  - `training_evidence` — evidencia adjunta del registro (reutiliza `intake`).
  - Extender `propiedad_puesto_ocupante` con `hire_date`, `employment_status`, `contractor`, etc.
- [ ] **API CRUD**: titulares, catálogo, requisitos, registros, evidencias. **RBAC por rol con alcance por hotel + línea de reporte** (PII desde el día 1).
- [ ] **Frontend**: gestión de roster, ficha por persona (matriz de cumplimiento), subida de evidencias.
- [ ] **Roster (RH, no-eng, EN PARALELO)**: HR carga las personas de las 4 propiedades. **Sin esto el módulo es un cascarón.**

### T3 — Motor de derivación de requisitos + corrida IA (≈1 sem eng + 1 corrida)
- [ ] **Motor**: derivar `training_requirement` de **JD SMART × SOP SMART × crosswalk** + reglas por depto/riesgo. **Unión deduplicada** (misma capacitación exigida por JD y SOP = 1 requisito con múltiples orígenes).
- [ ] **Corrida IA (Opus, por tramos)**: proponer **catálogo + requisitos** desde 94 JDs × 151 SOPs. ~8–13M tokens. Verificación adversarial: **cero certificaciones legales inventadas** → todo `mandatoria = pendiente de validación` salvo confirmación. **Autorización del owner por tramo** ([[feedback_no_autolanzar_tramos]]). *Es la ÚNICA corrida de IA que queda.*
- [ ] **Gate legal**: validación HR/Legal/Salud Ocupacional de los flags mandatorios. **No comprimible.**

### T4 — Capa de cumplimiento (≈1 sem eng) · GATED por T2 (datos) + T3 (requisitos)
- [ ] Alertas **compute-on-read**: pendiente / próxima a vencer / vencida.
- [ ] Dashboard + reportes de cumplimiento por persona / puesto / propiedad / depto.
- [ ] Recálculo al cambiar de puesto (sin perder historial).

### T5 — Endurecimiento y deploy (≈0.5 sem eng)
- [ ] Auditoría RBAC/PII (datos personales de colaboradores).
- [ ] Verificación end-to-end + deploy (auto, por la norma del proyecto).

---

## 3. Calendario y camino crítico

```
T1 (prereq, 0.5s) ─ T2 (esqueleto, 2s) ──┬─ T3 (derivación, 1s + IA) ─┐
                                          │                            ├─ T4 (cumplimiento, 1s) ─ T5 (0.5s)
  Roster (RH) ───────── en paralelo ──────┘   Sign-off legal (gate) ───┘
```

**Camino crítico ≈ 4.5 semanas de ingeniería** + **1 corrida de IA** (~1 día en tramos) + trabajo humano en paralelo. El **cuello real no es el código**: es el roster (RH) y la firma legal.

## 4. Recursos NO-ingeniería (dominan el calendario real)

| Recurso | Quién | Qué |
|---|---|---|
| Org-graph + decisión de roster | Owner | Desbloquean T1/T2 |
| Autorización por tramo de la corrida IA | Owner | La de derivación (T3); no se autolanzan tramos |
| **Carga del roster (hoy 0 titulares)** | HR | Decenas–cientos de personas × 4 propiedades — *domina el calendario* |
| **Sign-off legal de mandatorias** | HR / Legal / Salud Ocupacional | Gate de responsabilidad — sin esto todo queda "pendiente de validación" |

## 5. Riesgos y gates

1. **Legal (mandatorias)** — gate duro. Nada se marca legalmente obligatorio sin firma.
2. **Roster vacío** — el módulo es cascarón hasta que HR cargue personas. Empezar T2/roster en paralelo.
3. **Organigrama** — re-verificar colgantes; bloquea RBAC por supervisor.
4. **PII** — RBAC + auditoría obligatorios desde el día 1 de T2.
5. **Costo de la corrida IA** — autorización explícita del owner por tramo (política del proyecto).
6. **Paridad local↔prod** — cuidar migraciones y datos en cada deploy.

## 6. Costos de IA (lo que resta)

| Corrida | Volumen | Tokens (Opus) | Estado |
|---|---|---|---|
| JD SMART + linkage | 94 JDs × 2 etapas | ~15.8M reales | ✅ Hecho |
| **Derivación de capacitaciones** (T3) | 94 JDs × 151 SOPs → catálogo + requisitos | ~8–13M | ⏳ Pendiente — **única que queda** |

Opus en las dos etapas (bajar a Sonnet perdió contenido normativo en SOP).

---

## 7. Arranque recomendado

Cuando el owner dé luz verde: **T1 + T2 en ingeniería** y, **en paralelo desde el día 1**, RH empieza a cargar el roster. T3 (derivación IA) sólo cuando el crosswalk JD↔SOP esté validado; T4 sólo con datos (roster + requisitos). Sin roster ni firma legal, T4 no tiene qué mostrar — no adelantarlo.
