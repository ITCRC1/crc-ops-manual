# Pendientes para cerrar — CRC Operations Manual

> Última actualización: **2026-07-11**.
> Estado global: **SMART implementado y desplegado en los 3 procesos** (SOP, JD, Training),
> adaptable y editable por propiedad, con cobertura total de campos (auditado).
> Frontend: `crc-ops-manual-web.vercel.app` · Backend: `backend-production-8977c.up.railway.app`.
> Rama de trabajo: `claude/jd-smart`.

Este archivo es la lista viva de lo que falta para dar por cerrado el sistema. Lo que resta
es, en su mayoría, **trabajo humano** (validación, firma, carga de datos) y **un módulo nuevo**
(Training Records), no arreglos de lo ya construido.

---

## 1. SMART adaptable por propiedad — cierres finos
- [ ] **Verificación visual** con login de los 3 editores SMART por propiedad en prod (SOP / JD / Training). Hasta hoy solo verificado por API.
- [ ] **Puestos adoptados**: agregar transición "Adaptar" en el organigrama (hoy solo SOPs y Training la tienen; un puesto adoptado no se puede personalizar hasta adaptarlo, y no hay botón).
- [ ] **Flujo de firma local**: las versiones adaptadas por propiedad quedan en `borrador` → falta correr su firma para que queden vigentes.

## 2. Validación humana de las capas SMART (no es código)
- [ ] **SOPs (151):** revisar los `pendiente_confirmar` de cada uno (deadlines, aprobadores, sistemas, retención) y validar `control_versiones` (dice "Reformateo SMART (IA) — validar").
- [ ] **JDs (94):** revisión HR de `pendiente_confirmar` (autoridad, línea de reporte, KPIs "recomendado").
- [ ] **JD-028 "Gerente Residente":** cargar su prosa base y reformatear a JD SMART (es el único de 95 sin ficha).
- [ ] **Training (12 fichas):** revisar `pendiente_confirmar` (obligatoriedad legal, certificaciones, vigencias, modalidad).
- [ ] Correr el flujo acordado: **firmar masters → adoptar por propiedad → adaptar**.

## 3. Training Records — última pata de la Trilogía (módulo NO construido)
Registro de quién tomó qué capacitación (asistencia, vencimientos, evidencia, cumplimiento).
Plan en `docs/PLAN_TRILOGIA_SMART.md` (Fases T1–T5).
- [ ] T1: resolver organigrama + volumen persistente para evidencias.
- [ ] T2: modelo + API + UI (catálogo, requisitos, registros, evidencias).
- [ ] T3: derivación de requisitos (JD × SOP) — corrida IA (autorización por tramo).
- [ ] T4: capa de cumplimiento (alertas, dashboard).
- [ ] T5: endurecimiento (RBAC/PII) + deploy.

## 4. Bloqueadores no-código (dependen de owner / HR / Legal)
- [ ] **Roster:** cargar las personas de cada hotel (`propiedad_puesto_ocupante` = 0 hoy). Sin roster, Training Records es un cascarón.
- [ ] **Organigrama roto:** 12 `reporta_a` colgantes (→ `JD-016` ×11, `JD-029` ×1, soft-deleted). Bloquea RBAC por supervisor. Decidir: reasignar / restaurar.
- [ ] **Sign-off legal** de las capacitaciones marcadas como obligatorias.
- [ ] **Limpiar prod:** ~49 fixtures de JD de prueba (`JD-099…154`) probablemente siguen en producción.

## 5. Operación del manual (armado gradual, por el owner)
- [ ] **Asignar cada usuario a su hotel** en `/usuarios` (los 11 del equipo quedaron sin hotel → no ven ninguna propiedad).
- [ ] Armar cada hotel poco a poco desde `/armador` y correr las firmas en `/firmas`.

## 6. Deuda técnica menor (opcional)
- [ ] `checklist.cumplido` en JD se edita como texto libre (tiene valores "Sí"/"Parcial") — se dejó así a propósito para no perder el "Parcial"; si se quiere, migrar a un desplegable Sí/Parcial/No/N/A (requiere soporte de select-con-opciones en `TablaEditable`).

---

## Notas de despliegue (para mantenerlo en vivo)
- **No hay auto-deploy desde GitHub.** El deploy es manual por CLI tras cada tanda:
  - Backend: `railway link --project 86e5e694-fbf7-49b4-9bcf-d3f30af2ed76 --environment production --service backend` + `railway up backend --path-as-root --service backend --detach` (migraciones corren solas en el build vía Dockerfile).
  - Frontend: `vercel --prod --yes` en `frontend/`.
- Ambos servicios (Railway + Vercel) **quedan sirviendo permanentemente**; el sitio está vivo mientras esos servicios estén arriba (no dependen de una sesión local).
- Verificación rápida de que sigue vivo: `GET crc-ops-manual-web.vercel.app` → 200 y login en el backend → 200.
