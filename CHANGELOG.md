# Changelog — CRC Operations Manual Hub

Todas las fechas en formato AAAA-MM-DD.

## [Sin publicar]

### SOPs operativos + reorganización (2026-07-04)
- **20 SOPs operativos nuevos** (contenido original CRC, generados con workflows adversariales): 7 de Cocina/Restaurante (mermas, pedidos, **forecast OPERA a 2 semanas**, gestión de recetas; **Simphony obligatorio + prohibición de ventas fuera del sistema + cobros correctos**, **house charges**, equipo), 12 de Mantenimiento preventivo (área nueva **MANT**: generadores, solar, marítimo, agua, cocina/frío, A/C + marco) y Entrenamiento (inducción, matriz, servicio, certificaciones, evaluación), y 1 de **Alimentación de Empleados** (menú aprobado + estimación de headcount + planeamiento semanal por ítem).
- **Bodegas → Finanzas**: 8 SOPs de bodega/recepción/inventario reclasificados de FBS a FIN (bodegas y compras son de Finanzas); `reclasificar_bodegas.py`.
- Loader genérico `cargar_sops_generados.py` + todos integrados a `run_all.py` (reproducible). `cargar_sops` ahora idempotente por código o nombre.
- Estado del master (rebuild limpio): **119 SOPs**, **27 descriptores**, CWL adopta los 119. Áreas: FIN 40, HR 14, SM 11, GE 8, IT 8, FBS 8, MANT 7, KIT 6, CR 6, CT 6, GOV 5.

### Etapa 4.4 — Motor de asignación por propiedad (2026-07-04)
- Asignar SOPs por propiedad en modo **adoptado** (hereda firma → `vigente`), **adaptado** (guarda solo deltas en `overrides`, arranca `borrador`) o **local** (`codigo_local` atómico tipo `CWL-LOC-0001`, sin master). §7.8-7.10.
- **Solo un master `firmado` es asignable** (§7.4); unicidad (propiedad, master) para no-locales.
- **Contenido efectivo** por merge: `merge(snapshot_master[version_fijada], overrides)` para adaptado, `campos_locales` para local (`app/services/merge.py`, A2).
- **Sincronización** (§7.11, A1): al firmarse una versión nueva del master, las asignaciones a versiones anteriores quedan marcadas `requiere_actualizacion`; endpoint `POST /propiedad-sops/{id}/actualizar` fija la versión y limpia la bandera (nunca automático).
- **Retiro** (§7.12, B3): al archivar un master, sus asignaciones quedan `vigente` pero marcadas `master_retirado`.
- **Sugerencias por sistemas** (§7.13): compara los sistemas que asume el master vs. los de la propiedad → sugiere adoptar / adaptar. Alcance por propiedad (`editor_propiedad`) o corporativo. 25 tests OK.

### Etapa 4.3 — Colaboración, firma electrónica y documento controlado (2026-07-04)
- **Máquina de estados** (§11) con transiciones validadas: enviar-revisión, volver-borrador, enviar-firma, retomar-revisión, archivar.
- **Firmantes** con validación de nivel ≤ `nivel_minimo_firmante` (B1), **segregación de funciones** (el autor no puede ser único firmante, §7.3), y **reasignación** de pendientes (B6, auditada).
- **Firma electrónica** en orden; al completar las firmas obligatorias → transición automática a `firmado`, generación del **PDF (ReportLab) + hash SHA-256**, archivado del PDF y creación del **documento controlado** (A5). Rate-limited.
- **Rechazo** con comentario obligatorio (B5): pasa a `rechazado` e **invalida las firmas parciales** de la versión.
- **Bitácora de controlados** (emisión, descarga) y **registro de auditoría** transversal; descarga del PDF firmado con traza.
- ReportLab en lugar de WeasyPrint (sin dependencias nativas). 19 tests OK (flujo completo, orden, nivel, segregación, rechazo, inmutabilidad).

### Etapa 4.2 — CRUD del master, numeración atómica, versionado y búsqueda (2026-07-04)
- `app/api/sops.py`: CRUD de `sop_master` con formato de 9 campos. Crear/editar/eliminar exigen rol `editor_corporativo`/`super_admin`; lectura, cualquier usuario autenticado.
- **Numeración atómica** por área con `SELECT ... FOR UPDATE` (`app/services/numeracion.py`, §7.2): dos creaciones concurrentes nunca colisionan; los números eliminados no se reutilizan (soft delete).
- **Versionado**: snapshot v1 al crear; endpoint `POST /{id}/nueva-version` para editar un documento firmado (inmutable, §7.6) reabriendo en `borrador`.
- **Búsqueda/filtros** (§8.5): por área, departamento, estado, tipo, sistema y texto, con paginación.
- 6 tests nuevos (numeración atómica, versionado, filtros, permisos, inmutabilidad, soft delete). 15 tests OK.

### Etapa 4.1 — Núcleo de autenticación y seguridad (2026-07-04)
- JWT access (20 min) + refresh (7 días) con validación de `type` (`app/core/seguridad.py`), Argon2 ya existente.
- Endpoints `/api/auth/login`, `/api/auth/refresh`, `/api/auth/me` (`app/api/auth.py`); dependencias `get_current_user` y `require_rol(...)` con alcance por propiedad (`app/api/deps.py`, §14).
- Rate limiting en login/firma (`app/core/rate_limit.py`), CORS allowlist (no `*`).
- Tests async (httpx + un solo event loop de sesión) para login/refresh/me/rate-limit; CI ahora provisiona Postgres + `alembic upgrade` + seed. 9 tests OK.

### Sistemas reales + enriquecimiento de SOPs de Guest Experience (2026-07-04)
- **Catálogo de sistemas** = stack real de CRC (13): OPERA Cloud (PMS), Simphony y **Skills4IT** (POS), **SiteMinder** (channel manager/tarifas), **SynXis** (CRS/central de reservas), **HubSpot** (CRM, a implementar), Integrity (back office), QuickBooks (algunas propiedades), Inventory Management (inventario), Starlink, paneles solares, generadores, operación marítima. Registrados para que los SOPs futuros los referencien.
- **5 SOPs de Guest Experience enriquecidos a v2** con procedimientos reales, detallados y probados (navegación paso a paso en OPERA Cloud), adaptados a CRC desde SOPs reales de un hotel CR comparable: GE-0001 Check-In, GE-0004 Cierre de Cajero, GE-0005 Check-Out, GE-0006 Llegada de Grupos, GE-0009 Posting Masters. Marca ajena/PII eliminada (verificado, 0 rastros); v1 preservado en `sop_master_versiones`.
- Pipeline `app/ingestion/enriquecer_ge_sops.py` (idempotente) integrado a `run_all.py`.

### Descriptores de Finanzas — 3 nuevos (2026-07-04)
- Cargados JD-025 (Contador/Analista Senior), JD-026 (Auxiliar Contable/CxP), JD-027 (Coordinador de Compras/Proveeduría), adaptados a CRC desde descriptores reales de un hotel CR comparable (contenido propio, sin marca ajena ni PII — verificado). Total descriptores: **27**.
- Jerarquía: Contador → Finance Controller; Auxiliar y Coordinador de Compras → Contador. `app/ingestion/cargar_descriptores_finanzas.py` (idempotente), integrado a `run_all.py`.

### Cierre de brechas de control — 23 SOPs nuevos (2026-07-04)
- Generados 23 borradores de SOP para las brechas del gap analysis (contenido original CRC), vía dos workflows adversariales: generación desde cero (46 agentes) y **re-fundamentación de 10 brechas en políticas REALES de un hotel CR comparable** (Cala Luna/Kona Pacífica, aportadas por el equipo de finanzas) adaptadas a CRC.
- **Datos sensibles:** el material real se usó solo como patrón; se eliminaron marca ajena, nombres de firmantes/empleados y números de cuenta/tarjeta/saldos. Escaneo automático post-carga: **0 rastros de PII/marca ajena** en los 23 SOPs.
- Cargados en `sop_master` (borrador, numeración atómica): CT-0005..0008, FIN-0028..0043, HR-0008..0010. Total ahora: **99 SOPs**, CWL adopta los 99.
- Pipeline: `app/ingestion/cargar_brechas.py` (idempotente), integrado a `run_all.py`. Fuentes congeladas en `seed/ingesta/gap_drafts.json` + `gap_topics.json`.

### Etapa 3 (completa) — Ingesta, reconciliación y carga (2026-07-03)
- **Aprobación otorgada** → cargados en la base (todo en estado `borrador`):
  - **76 SOPs** en `sop_master` (74 `sop` + 2 `politica`): 72 del índice curado con cuerpo emparejado (divisiones comparten cuerpo Word; la fusión FIN-0006 concatena 2) + 4 borradores del pack financiero USALI (FIN-0026/0027, GOV-0004/0005, contenido original CRC). CR-0007/CR-0008 omitidos (sin cuerpo en el manual).
  - **24 Descriptores de Puesto** con jerarquía `reporta_a` (niveles 1-4) y snapshots v1.
  - **CWL pre-asignado** en modo `adoptado` sobre los 76 SOPs (`estado=borrador` hasta la firma; las otras 3 propiedades sin asignaciones).
- Orquestador reproducible e idempotente: `python -m app.ingestion.run_all`.
- Pack financiero USALI generado por workflow LLM (4 redactores + 4 revisores adversariales), contenido 100% original CRC (sin copiar el PDF USALI).

### Etapa 3 (parcial) — Ingesta y reconciliación, hasta punto de aprobación (2026-07-03)
- Pipeline de ingesta en `app/ingestion/` (`parse_fuentes.py`, `construir_reporte.py`, `README.md`).
- Parseo determinístico: 74 SOPs del índice Excel curado; 150 SOPs del manual Word con cuerpo real (9 campos completos en todos); 2 títulos del Word (CR-0007, CR-0008) confirmados sin cuerpo desarrollado.
- Emparejamiento por NOMBRE (no por código): 52 exactos + 22 ambiguos resueltos con un workflow LLM (22 agentes de emparejamiento + 22 verificadores adversariales + 1 auditor de exactos). Decisiones congeladas en `seed/ingesta/reconciliation_matches.json`.
- `seed/reconciliation_report.csv` (155 filas): 34 emparejados, 27 conflicto, 10 división, 1 fusión, 2 solo_excel, 81 solo_word; 31 con colisión de código documentada.
- Artefactos derivados en `seed/ingesta/` para carga reproducible.
- **PENDIENTE (requiere aprobación):** cargar los cuerpos en `sop_master` (estado `borrador`); parsear 24 Descriptores de Puesto; borradores del pack financiero USALI; pre-asignar master a CWL en modo `adoptado`.

### Etapa 2 — Modelo de datos (2026-07-03)
- 27 modelos SQLAlchemy (§5) con PK UUID, `creado_en`/`actualizado_en`, soft delete en entidades de contenido, e índices en FKs y llaves de negocio. Organizados en `app/models/{base,config,catalogos,usuarios,puesto,sop,propiedad,auditoria}.py`.
- 6 tipos ENUM de PostgreSQL en español (`tipo_documento`, `estado_documento`, `modo_asignacion`, `estado_asignacion`, `frecuencia_revision`, `rol_usuario`), definidos como instancias compartidas para un solo CREATE TYPE.
- Migración Alembic inicial (`a042cced3322`): `alembic upgrade head` crea las 27 tablas + 6 enums; downgrade dropea tablas y tipos (ciclo down/up idempotente verificado).
- Hashing de contraseñas con Argon2 (`app/core/seguridad.py`).
- Seed idempotente (`app/seed.py`, `python -m app.seed`): 4 propiedades (CWL/AMA/OXI/OJO), 10 áreas del índice curado, 8 sistemas típicos, 13 departamentos estándar, `configuracion.nivel_minimo_firmante=3`, usuario admin `super_admin`, y marco institucional extraído fielmente de la Sección 0 del manual (visión, misión, 6 valores, 6 objetivos, declaración de valor, manifiesto).
- Diagrama ER del modelo generado en `docs/MODELO_DATOS.md` (Mermaid, desde el metadata real) vía `scripts/generar_diagrama.py`.
- Base de datos local `crc_ops_manual` (rol `crc_ops`) en la instancia PostgreSQL 16 del puerto 5433, aislada de `daily_ops`.

### Etapa 1 — Scaffold e infraestructura (2026-07-03)
- Estructura de monorepo (`backend/`, `frontend/`, `seed/`, `scripts/`, `docs/`) según §15 del spec.
- Backend: FastAPI + SQLAlchemy async + Alembic (scaffold vacío, sin modelos aún) + healthcheck `/api/salud`. Dockerfile. Test de humo con pytest.
- Frontend: Next.js 14 (App Router) + TypeScript + Tailwind, página de inicio en español con tokens de color del §9.
- Configs de infraestructura (sin crear recursos remotos): `backend/railway.toml` (proyecto `crc-ops-manual-api`), `frontend/vercel.json` (proyecto `crc-ops-manual-web`), `docker-compose.yml` para Postgres local.
- CI (GitHub Actions): lint + tests para backend y frontend.
- `.env.example` en backend y frontend; `.gitignore` raíz.
- Archivos fuente para la Etapa 3 copiados a `seed/source/`.

Pendiente: Etapa 2 (modelo de datos y migraciones Alembic).
