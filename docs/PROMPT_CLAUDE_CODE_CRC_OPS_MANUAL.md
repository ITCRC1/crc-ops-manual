# CRC Operations Manual Hub — Prompt de Construcción para Claude Code (FINAL)

**Cliente:** The Costa Rica Collection (CRC)
**Repositorio:** `crc-ops-manual`
**Versión del prompt:** 3.0 — documento final para construcción
**Idioma del sistema:** español en su totalidad (interfaz, contenido, estados, exportaciones, etiquetas y nomenclatura del modelo de datos).

---

## 0. Cómo usar este documento

1. Entorno de desarrollo: **Windows**. Claude Code debe dar comandos y scripts cross-platform; si necesita scripts, proveer variante **PowerShell (.ps1)**.
2. Abrí Claude Code en una carpeta vacía y ejecutá `/model opus`.
3. Colocá los archivos fuente en `seed/source/` (§10) **antes** de la Etapa 3.
4. Pegá el "Comando de arranque" (§16) como primer mensaje, junto con este documento.
5. Claude Code trabaja **etapa por etapa** (§12) y se **detiene en cada PUNTO DE APROBACIÓN**. No avanzar sin confirmación.
6. **Verificación antes de toda acción remota** (crear repo, proyecto Railway/Vercel, base de datos, `git push`, `link`, `deploy`): confirmar si el recurso **ya existe**, distinguir "crear por primera vez" de "reconectar", y **nunca** tocar ni sobrescribir el stack existente `crc-coordination-hub`.
7. Mantener `CHANGELOG.md` desde el inicio y escribir pruebas para las reglas de negocio críticas (§7).

**Regla legal innegociable:** el documento USALI (`seed/source/usali-*.pdf`) tiene copyright. Se usa **solo como referencia conceptual**. Prohibido copiar, almacenar en base de datos o redistribuir su texto. Todo procedimiento derivado se redacta con contenido original de CRC alineado al estándar.

---

## 1. Objetivo y visión del producto

Sistema web multipropiedad, **enteramente en español**, para administrar **Procedimientos Operativos Estándar (SOP)**, **Descriptores de Puesto (Job Descriptions)** y **Políticas** del grupo hotelero.

El modelo central es una **librería maestra aprobada** de la que cada hotel **adopta**, **adapta** o **crea localmente** procedimientos, ajustándose a los **sistemas** que tiene y a sus situaciones especiales. Debe permitir **agregar propiedades, departamentos, áreas y sistemas** sin cambios de esquema, y garantizar que solo se asigne contenido del **set aprobado**.

Cada SOP **nace, vive y reside en la base de datos** (fuente única de verdad). Se finaliza con **firma electrónica**, se **imprime y archiva la versión firmada en PDF**, y esa versión queda **controlada** (inmutable, con bitácora y custodio).

El **marco institucional** (visión, misión, objetivos estratégicos, valores, declaración de valor y manifiesto) es **editable** desde el sistema por el rol corporativo, y queda versionado.

Propiedades iniciales: **Corcovado Wilderness Lodge (CWL)**, **Amarena**, **Oxigen**, **Ojochal Garden Villas**.

---

## 2. Glosario del dominio

- **Marco institucional:** contenido corporativo editable (visión, misión, objetivos, valores, declaración de valor, manifiesto). Prevalece sobre cualquier SOP.
- **Master (librería maestra):** catálogo central y aprobado de SOPs, Descriptores de Puesto y políticas estándar.
- **Propiedad:** un hotel del grupo. Es el "inquilino" del modelo.
- **Área:** clasificación funcional con **prefijo de código** (FIN, GE, SM, KIT, FBS, HR, IT, CT, GOV, CR, …). Es catálogo editable, **distinto del departamento** (un área puede repartirse entre varios departamentos).
- **Formato único:** estructura obligatoria de 9 campos que **todo SOP** cumple, sin importar naturaleza ni departamento.
- **Modo de asignación:** `adoptado` (usa el master tal cual), `adaptado` (parte del master y guarda solo lo que cambió), `local` (creado por la propiedad), `no_aplica`.
- **Sistema:** herramienta operativa/financiera de una propiedad (OPERA Cloud, Simphony POS, QuickBooks, Integrity, Starlink, paneles solares, generadores, botes/operación marítima…). Un SOP master puede declarar los sistemas que asume.
- **Colaborador:** usuario invitado a completar/redactar un SOP durante su creación.
- **Firmante:** usuario **designado al inicio** de la creación del SOP para firmarlo al final. Debe cumplir el nivel mínimo configurado (§3, decisión B1).
- **Firma electrónica:** acto que **constituye la aprobación**. Se registra usuario, fecha/hora, método, IP y hash del PDF.
- **Documento controlado:** versión firmada en PDF, **inmutable**. Todo cambio posterior exige versión nueva y queda en bitácora.
- **Custodio documental:** rol que controla acceso y cambios de los documentos controlados.
- **Versión fijada (`version_fijada`):** versión del master que una propiedad adoptó; no cambia sola.

---

## 3. Decisiones (tomadas — implementar así)

### Arquitectura
- **A1. Sincronización master → propiedad = fijada + notificación.** Al firmarse una versión nueva de un master, las propiedades quedan en su `version_fijada` y se marca `requiere_actualizacion = true` con alerta. Nunca automático.
- **A2. Override por campos, no copia total.** La adaptación guarda solo secciones modificadas (JSONB de deltas); render = `merge(master.snapshot[version_fijada], overrides)`.
- **A3. Formato único de SOP (sin excepciones).** Todo SOP usa los 9 campos: Código, Departamento/Área, Propósito, Evaluación de Riesgos, Controles Existentes, Procedimiento Detallado, Responsables, Evidencia/Reportes, Frecuencia de Revisión.
- **A4. Políticas = mismo mecanismo que SOPs** con `tipo = sop | politica`. Los Descriptores de Puesto van en tablas propias por la jerarquía (`reporta_a`).
- **A5. Firma electrónica y control documental.** El SOP se finaliza con firmas electrónicas de los firmantes designados; al completarse, se genera el PDF firmado (con hash), se archiva y pasa a **controlado** (inmutable, bitácora, custodio).
- **A6. PK = UUID** en todas las tablas (habrá integración con otros sistemas). `codigo`/`numero` son llaves de negocio, no la PK.
- **A7. Parámetros de negocio en configuración, no hardcodeados** (tabla `configuracion`). Áreas, sistemas, departamentos y propiedades son catálogos editables.

### Negocio (resueltas por defecto — **ajustables**; cambiá el valor si tu operación difiere)
- **B1. Nivel mínimo de firmante = 3** (jefatura/gerencia de departamento). Elegibles: niveles 1, 2 y 3. Vive en `configuracion.nivel_minimo_firmante`.
- **B2. Aprobar = firmar.** No hay paso de aprobación separado: la firma electrónica de los firmantes designados **es** la aprobación. Por eso no existen roles "aprobador"; la autoridad de finalizar la da la designación como firmante (más el nivel B1).
- **B3. Retiro/archivado de un master:** no archiva automáticamente las instancias de propiedad. Las propiedades que lo adoptaron/adaptaron mantienen su versión controlada **vigente pero marcada** (`master_retirado = true` + alerta); el master deja de ser asignable; cada propiedad decide archivar o conservar su instancia con justificación.
- **B4. Transiciones del ciclo:** `borrador → en_revision → en_firma` las dispara el `editor_corporativo` (master) o el `editor_propiedad` (propiedad). `en_firma → firmado` es **automático** al completarse las firmas obligatorias. Archivar lo hace `super_admin` o el editor del ámbito, con registro.
- **B5. Rechazo en firma:** cualquier firmante puede **rechazar con comentario obligatorio**; el documento vuelve a `en_revision` y **se invalidan las firmas parciales** de esa versión (queda en auditoría).
- **B6. Reasignación de firmante:** si un firmante pendiente se desactiva o no está disponible, el `editor` del ámbito puede reasignarlo (solo firmantes que aún no firmaron); queda en `registro_auditoria`.

---

## 4. Stack tecnológico y nombres de infraestructura

- **Backend:** Python 3.11, **FastAPI**, **SQLAlchemy 2.x**, **Alembic**, Pydantic v2.
- **Base de datos:** **PostgreSQL** (JSONB para snapshots, overrides y estructuras editables).
- **Frontend:** **Next.js 14** (App Router) + **TypeScript** + **Tailwind CSS**; TanStack Query; react-hook-form + zod. Todo el texto en español.
- **Autenticación:** JWT con **access token corto (15–30 min) + refresh token**; roles (§14). Passwords con **argon2/bcrypt**.
- **Firma electrónica:** flujo interno con registro de firma (usuario, fecha/hora, método, IP, **hash SHA-256 del PDF**). Capa desacoplada para integrar un proveedor externo (DocuSign u otro) más adelante sin rehacer el modelo.
- **Generación PDF:** WeasyPrint o ReportLab; el PDF firmado se almacena con su hash y **no se regenera** (inmutable).
- **Infra/deploy — nombres explícitos y únicos:**
  - Repo GitHub: `crc-ops-manual`
  - Railway (API + Postgres): proyecto `crc-ops-manual-api`, base `crc_ops_manual`
  - Vercel (frontend): proyecto `crc-ops-manual-web`
  - **No reutilizar ni tocar** el stack `crc-coordination-hub`. Verificar existencia antes de crear (§0.6).
- **Estructura:** monorepo (§15). Dockerfile para el backend y CI mínima (lint + tests).

---

## 5. Modelo de datos

SQLAlchemy + Alembic. **PK = UUID** en todas las tablas. Todas con `creado_en`, `actualizado_en`. Soft delete (`eliminado_en`) en entidades de contenido. Nomenclatura en español. Los campos de estado son **NOT NULL con DEFAULT `borrador`** y validados.

### Enums (valores en español)
- `tipo_documento`: `sop | politica`
- `estado_documento` (master): `borrador | en_revision | en_firma | firmado | rechazado | archivado` (`firmado` = aprobado y controlado)
- `modo_asignacion`: `adoptado | adaptado | local | no_aplica`
- `estado_asignacion` (propiedad): `borrador | en_revision | en_firma | vigente | rechazado | archivado`
- `frecuencia_revision`: `mensual | trimestral | semestral | anual | por_cambio`
- `rol_usuario`: `super_admin | editor_corporativo | editor_propiedad | custodio_documental | lector`
- `nivel_jerarquico`: `1 | 2 | 3 | 4` (1 alta dirección · 2 dirección funcional · 3 jefatura/gerencia de departamento · 4 operativo)

### Configuración y parámetros
- **configuracion** — `clave` (única), `valor`, `tipo` (int/text/bool), `descripcion`, `editable` (bool). Semilla obligatoria: `nivel_minimo_firmante = 3`.

### Marco institucional (editable)
- **marco_institucional** — `vision`, `mision`, `objetivos_estrategicos` (JSONB, lista editable), `valores` (JSONB, lista editable), `declaracion_valor`, `manifiesto`, `version` (int), `activo` (bool), `editado_por`, `editado_en`. Un registro activo + historial. Editable solo por rol corporativo.

### Master data de usuarios
- **usuarios** — `nombre`, `email` (único), `password_hash`, `departamento_id` FK, `puesto_id` FK→descriptor_puesto_master (nullable), `nivel_jerarquico`, `activo`.
- **roles_usuario** — `usuario_id` FK, `rol` (`rol_usuario`), `propiedad_id` FK **nullable** (`NULL` = alcance corporativo; con valor = alcance a esa propiedad). Varios roles/propiedades por usuario.

### Catálogos (editables — extensibilidad sin migración)
- **propiedades** — `codigo` (único, ej. `CWL`), `nombre`, `razon_social`, `zona_horaria`, `activo`.
- **areas** — `codigo` (prefijo único, ej. `FIN`), `nombre`, `activo`. **Base del `codigo` de los SOP; distinto de departamento.**
- **sistemas** — `codigo`, `nombre`, `categoria` (PMS, POS, contable, conectividad, energía, transporte…), `descripcion`.
- **propiedad_sistemas** — (`propiedad_id`, `sistema_id`), `notas`.
- **departamentos** — `codigo`, `nombre`, `propiedad_propietaria_id` FK→propiedades **nullable** (`NULL` = estándar; con valor = local), `activo`.
- **propiedad_departamentos** — (`propiedad_id`, `departamento_id`).
- **contador_area** — (`area_id`) `ultimo_numero` (int). Secuencia por área para numeración atómica (§7.2).
- **contador_local** — (`propiedad_id`) `ultimo_numero` (int). Secuencia por propiedad para códigos locales.

### Master: SOPs y políticas (formato único)
- **sop_master** — `numero` (int, asignado automáticamente al crear, §7.2), `area_id` FK→areas, `codigo` (único, = `area.codigo + '-' + numero` a 4 dígitos, ej. `FIN-0001`), `tipo` (`tipo_documento`), `nombre`, `departamento_id` FK, y los **9 campos**:
  `proposito`, `evaluacion_riesgos`, `controles_existentes`, `procedimiento` (texto estructurado por secciones), `responsables` (puede referenciar Descriptores de Puesto), `evidencia`, `frecuencia_revision`.
  Más: `estado` (`estado_documento`, DEFAULT `borrador`), `version_actual` (int), `creado_por`, `firmado_en`.
  (Para `tipo=politica`, riesgo/controles opcionales; la estructura de 9 campos se mantiene.)
- **sop_master_versiones** — `sop_master_id` FK, `version`, `snapshot` (JSONB con todos los campos), `nota_cambio`, `estado_en_version`, `creado_por`, `creado_en`.
- **sop_master_sistemas** — (`sop_master_id`, `sistema_id`). Sistemas que el SOP asume (sugerencias, §7).

### Colaboración y firma
- **colaboradores_sop** — `sop_master_id` FK, `usuario_id` FK, `rol_colaboracion` (redactor/revisor), `seccion_asignada` (nullable), `estado` (invitado/en_progreso/completado).
- **firmantes_sop** — `sop_master_id` FK, `usuario_id` FK, `orden` (int), `obligatorio` (bool). Designados al crear. **Restricción:** `usuario.nivel_jerarquico <= configuracion.nivel_minimo_firmante`.
- **firmas_electronicas** — `sop_master_id` FK, `version` (int), `usuario_id` FK, `fecha_hora`, `metodo`, `ip`, `hash_pdf`. Registro inmutable.
- **documento_controlado** — `sop_master_id` FK, `version` (int), `pdf_storage_key`, `hash_pdf`, `fecha_firma`, `custodio_id` FK→usuarios, `es_vigente` (bool). Versión firmada en PDF, inmutable.

### Capa de propiedad
- **propiedad_sop** — `propiedad_id` FK, `sop_master_id` FK **nullable** (`NULL` = local), `modo` (`modo_asignacion`), `version_fijada` (int nullable), `overrides` (JSONB, solo deltas), `codigo_local` (nullable, ej. `CWL-LOC-0001`), `campos_locales` (JSONB), `estado` (`estado_asignacion`, DEFAULT `borrador`), `fecha_vigencia`, `requiere_actualizacion` (bool), `master_retirado` (bool). Índice único (`propiedad_id`, `sop_master_id`) cuando no es local.
- **propiedad_puesto** — `propiedad_id` FK, `descriptor_puesto_master_id` FK nullable, `modo`, `version_fijada`, `overrides` (JSONB), `reporta_a_id` FK→propiedad_puesto nullable, `dotacion` (int nullable), `estado`, `requiere_actualizacion`.
- **propiedad_sop_bitacora** — `propiedad_sop_id` FK, `accion`, `campo`, `valor_anterior`, `valor_nuevo`, `usuario_id`, `creado_en`.

### Descriptores de Puesto (Job Descriptions)
- **descriptor_puesto_master** — `codigo` (único), `titulo`, `reporta_a_id` FK→self **nullable**, `departamento_id` FK, `nivel_jerarquico` (1–4), `proposito`, `responsabilidades` (JSONB), `nivel_autoridad`, `kpis` (JSONB), `requisitos`, `estado` (`estado_documento`, DEFAULT `borrador`), `version_actual`.
- **descriptor_puesto_versiones** — historial (igual que `sop_master_versiones`).

### Control, auditoría y adjuntos
- **bitacora_control** — `documento_controlado_id` FK, `accion`, `detalle` (JSONB), `usuario_id`, `creado_en`. Log de accesos/cambios a documentos controlados.
- **registro_auditoria** — `usuario_id`, `entidad`, `entidad_id`, `accion`, `detalle` (JSONB), `ip`, `creado_en`. Trazabilidad transversal.
- **adjuntos** — `entidad`, `entidad_id`, `nombre`, `mime`, `tamano`, `storage_key`, `subido_por`. (No almacenar el PDF de USALI.)

**Índices:** en todas las FK, y en (`propiedad_id`, `sop_master_id`), (`codigo`), (`estado`), (`area_id`, `numero`).

---

## 6. Ciclo de vida del SOP

1. **Creación en base de datos.** Se elige el **área**; el sistema asigna el `numero` atómico por área y arma el `codigo`. Estado `borrador`. Se **designan los firmantes** (nivel ≥ configurado) desde el master data de usuarios.
2. **Colaboración.** Se invita a colaboradores a completar el SOP bajo el formato único (opcionalmente por secciones). El SOP vive en la base de datos.
3. **Revisión.** Estado `en_revision` (lo envía el editor). Se consolida contenido y se verifica el formato.
4. **Firma electrónica.** Estado `en_firma` (lo envía el editor). Los firmantes firman en orden; cada firma queda registrada. Un firmante puede **rechazar con comentario** → vuelve a `en_revision`, se invalidan firmas parciales (B5).
5. **Documento controlado.** Al completarse las firmas obligatorias: se genera el **PDF firmado**, se calcula su **hash**, se archiva en `documento_controlado` y el estado pasa a `firmado` (automático, B4). Versión inmutable y controlada.
6. **Control de cambios post-firma.** Todo cambio exige **versión nueva** (reinicia revisión/firma). Cambios y accesos a la versión controlada quedan en `bitacora_control`, bajo el **custodio documental**.

El mismo ciclo aplica, en menor escala, a **adaptaciones y políticas locales** (firmantes locales, PDF firmado local, custodia).

---

## 7. Reglas de negocio (implementar con pruebas)

1. **Formato único.** El editor impone los 9 campos para todo `tipo` y todo departamento; sin plantillas alternativas.
2. **Numeración automática y atómica.** Al crear un SOP se toma el siguiente número de `contador_area` (del área elegida) bajo bloqueo transaccional; el `codigo` se deriva. Los números de SOP eliminados **no se reutilizan** (trazabilidad). Igual para `codigo_local` con `contador_local`.
3. **Firmantes.** `firmantes_sop` solo admite usuarios con `nivel_jerarquico <= configuracion.nivel_minimo_firmante`. Se designan al inicio. Quien redacta en solitario no puede ser el único firmante que lo finaliza (segregación de funciones).
4. **Set aprobado.** Solo `sop_master`/`descriptor_puesto_master` en estado `firmado` son asignables.
5. **Firma = aprobación.** `firmado` se alcanza solo con todas las firmas obligatorias registradas; recién ahí se genera el `documento_controlado`.
6. **Inmutabilidad del controlado.** La versión firmada no se edita; editar obliga a nueva versión; la anterior permanece íntegra (verificable por hash).
7. **Custodia.** Toda acción sobre documentos controlados (ver, exportar, iniciar nueva versión) queda en `bitacora_control`; el `custodio_documental` administra el acceso.
8. **Adopción.** `adoptado`: `version_fijada = master.version_actual`; contenido del snapshot; hereda la aprobación (firma) corporativa; registrado en auditoría.
9. **Adaptación.** `adaptado`: `overrides` solo secciones cambiadas; render = merge; requiere firma local.
10. **Local.** `local`: `sop_master_id = NULL`; contenido en `campos_locales`; `codigo_local` generado; flujo de firma local.
11. **Sincronización controlada.** Al firmarse versión nueva de un master, marcar `requiere_actualizacion=true` en las `propiedad_sop` con `version_fijada < version_actual` y alertar. "Revisar y actualizar" muestra diff, permite re-fusionar overrides y, al confirmar, actualiza `version_fijada`. Prohibido actualizar sin acción humana.
12. **Retiro de master (B3).** Al archivar un master: marcar `master_retirado=true` en sus `propiedad_sop`, mantenerlas `vigente` pero alertadas; bloquear nuevas asignaciones; cada propiedad decide archivar o conservar con justificación.
13. **Sugerencias por sistemas.** Comparar `sop_master_sistemas` vs `propiedad_sistemas`: faltan sistemas → sugerir `no_aplica`/"requiere adaptación"; están todos → sugerir `adoptado`. Siempre editable; nunca automático.
14. **Transiciones (B4).** Solo el editor del ámbito dispara `borrador→en_revision→en_firma`; `en_firma→firmado` es automático; archivar por `super_admin`/editor con registro.
15. **Rechazo (B5) y reasignación (B6).** Rechazo → `rechazado`/`en_revision` + invalida firmas parciales. Firmante pendiente desactivado → el editor reasigna (solo pendientes), con auditoría.
16. **Marco institucional.** Editable solo por rol corporativo; cada guardado crea versión; prevalece sobre cualquier SOP.
17. **Extensibilidad sin migración.** Agregar propiedad, área, departamento o sistema son operaciones de datos. Umbrales en `configuracion`.
18. **Versionado y auditoría.** Toda edición firmada crea fila en `*_versiones`; toda acción sensible queda en `registro_auditoria`.

---

## 8. Módulos y funcionalidades

1. **Marco institucional:** edición versionada de visión, misión, objetivos, valores, declaración, manifiesto (solo corporativo).
2. **Master data de usuarios:** alta/edición con departamento, puesto y nivel; roles y alcance por propiedad.
3. **Configuración:** parámetros editables (incluye `nivel_minimo_firmante`).
4. **Catálogos:** áreas, sistemas, departamentos, propiedades.
5. **Librería maestra:** CRUD de SOPs/políticas/Descriptores con **formato único**; numeración automática; versionado; búsqueda y filtros por área/departamento/estado/sistema/tipo.
6. **Creación colaborativa:** crear SOP (con número), designar firmantes, invitar colaboradores, completar por secciones, enviar a revisión y a firma.
7. **Firma electrónica:** firma en orden; rechazo con comentario; generación y archivo del PDF firmado; paso a controlado.
8. **Gestión documental (custodio):** documentos controlados, bitácora de accesos/cambios, control de acceso, inicio de nueva versión.
9. **Gestión de propiedades:** alta/edición; `propiedad_sistemas` y `propiedad_departamentos`.
10. **Asistente de asignación:** por propiedad, lista los master `firmado` con sugerencia por sistemas; confirma modo.
11. **Editor de override:** master vs. local lado a lado; toggle por sección "heredar / sobrescribir"; guarda deltas.
12. **Colas de firma:** corporativa y por propiedad, con historial y comentarios.
13. **Alertas:** versiones nuevas disponibles y masters retirados, por propiedad, con diff.
14. **Organigrama por propiedad:** derivado de `reporta_a`; árbol por niveles 1–4.
15. **Tablero:** cobertura por propiedad (adoptados/adaptados/locales/pendientes), estado de firmas, SOPs vencidos, alertas de sincronización y retiro.
16. **Búsqueda global** con filtros combinables.
17. **Exportación:** PDF por documento (encabezado CRC), manual completo por propiedad (contenido efectivo fusionado), catálogo del master, y descarga de la versión firmada controlada.
18. **Auditoría:** trazabilidad completa para roles corporativos y custodio.

---

## 9. Diseño / UX

Estilo **enterprise tipo OPERA Cloud**: limpio, denso pero ordenado, navegación por pestañas, **todo en español**.

**Tokens de color:** primario petrol `#1F7A8C`, petrol oscuro `#155E6D`, tint `#E6F0F2`; texto/carbón `#3D3D3D`, suave `#4A5A62`; fondo `#F2F4F1`, superficie `#FFFFFF`, línea `#DEE5E2`; estados: firmado/vigente `#2F7D57`, en revisión/en firma `#B97514`, borrador `#5B6A72`, rechazado `#B23A48`, archivado `#8A979D`, controlado `#155E6D`. Color por propiedad: CWL `#2F6B4F`, Amarena `#8A4F5E`, Oxigen `#3B8EA5`, Ojochal `#6E7F3A`.

**Componentes:** badges de estado y de "documento controlado"; chips de modo; badges de propiedad con su color; vista diff; árbol de organigrama; editor de 9 secciones; panel de firmas con orden/estado y opción de rechazo; sello/registro de firma en el PDF.

**Piso de calidad:** responsive, foco de teclado visible, `prefers-reduced-motion` respetado, textos de estado/vacío/error en la voz del producto y en español.

---

## 10. Datos semilla y reconciliación (detalle de Etapa 3)

Colocar en `seed/source/`:
- `Manual_Sop___Hotel_Corcovado_FINAL__SOP_.docx` — manual desarrollado (~150 SOPs, 9 campos).
- `SOP_MASTER_Corcovado_74_FIXED.xlsx` — índice curado de 74 SOPs con `codigo` + `Área`.
- `Job_Descriptions.docx` y `JOB_DESCRIPTIONS_CONSECUTIVO_001.zip` — 24 Descriptores de Puesto.
- `Organizational_Chart.docx` — organigrama (validación de jerarquía y niveles 1–4).
- `usali-*.pdf` — **solo referencia conceptual** (no almacenar/copiar).

**Pipeline de reconciliación (crítico):**
1. Parsear el Excel `SOP_INDEX` → 74 códigos + Área. Sembrar el catálogo `areas` a partir de los prefijos. Esta es la taxonomía del master.
2. Parsear el manual Word → extraer el cuerpo de cada SOP (9 campos).
3. **Emparejar Excel ↔ Word por NOMBRE (semántico), NO por código.** De 57 códigos comunes, **34 apuntan a un SOP distinto**; unir por código corrompería ~60%. Contemplar divisiones (ej. "Reconciliación Diaria & Auditoría Nocturna" que el Excel separó en dos), fusiones y renombres.
4. Generar `seed/reconciliation_report.csv`: `codigo_excel, nombre_excel, area, nombre_word_emparejado, confianza, estado (emparejado | conflicto | division | fusion | solo_excel | solo_word)`.
5. **PUNTO DE APROBACIÓN:** presentar el reporte. Solo tras aprobación, cargar los cuerpos en `sop_master` (estado inicial `borrador`).
6. Parsear los 24 Descriptores → `descriptor_puesto_master`, con `reporta_a_id` desde "Reporta a"; validar niveles con el organigrama.
7. **Generar borradores del pack financiero USALI** (contenido original de CRC, alineado al estándar, estado `borrador`): (a) métricas e indicadores estándar (ADR, RevPAR, GOPPAR, ocupación, flow-through, productividad); (b) reporte **bruto vs neto** (paquetes por componente, comisiones OTA, tours/transporte de terceros, service charge); (c) guía de clasificación de ingresos y gastos base USALI (COA y posting); (d) estados financieros mensuales (incluye resultado integral, patrimonio y notas). Áreas `FIN`/`GOV`.
8. **Semilla:** crear las 4 propiedades, el marco institucional inicial (desde la Sección 0 del manual) y la configuración (`nivel_minimo_firmante = 3`). Como el contenido proviene de CWL, pre-asignar el master a **CWL en modo `adoptado`** (pendiente de confirmación); las otras tres arrancan sin asignaciones.

---

## 11. Máquina de estados y transiciones

Implementar exactamente estas transiciones (base de las reglas §7.14–15 y B4–B5).

**Documento master (`estado_documento`):**
- `borrador → en_revision` — editor del ámbito.
- `en_revision → en_firma` — editor; también `en_revision → borrador` para seguir editando.
- `en_firma → firmado` — **automático** al registrarse todas las firmas obligatorias (genera el PDF firmado y el `documento_controlado`).
- `en_firma → rechazado` — un firmante rechaza con comentario; **invalida las firmas parciales** de esa versión.
- `rechazado → en_revision` — el editor retoma.
- `firmado → archivado` — `super_admin` o editor, con registro.
- Editar un `firmado` NO lo modifica: se **crea una versión nueva** (arranca en `borrador`/`en_revision`); la versión firmada permanece controlada e íntegra.

**Asignación de propiedad (`estado_asignacion`), para `adaptado`/`local`:**
- `borrador → en_revision → en_firma → vigente` (`vigente` automático al completar firmas locales); `en_firma → rechazado → en_revision` igual que el master.
- `vigente → archivado` — editor de propiedad o `super_admin`.
- **`adoptado`:** al asignarse pasa directo a `vigente` (hereda la firma del master). `requiere_actualizacion` y `master_retirado` son banderas, no estados: se muestran como alertas sobre una asignación `vigente`.

---

## 12. Plan de entrega por etapas (con puntos de aprobación)

Detenerse en cada PUNTO DE APROBACIÓN. Antes de cualquier recurso remoto, aplicar la verificación de §0.6.

- **Etapa 1 — Scaffold e infra.** Monorepo, Dockerfile backend, configs Railway/Vercel con los nombres de §4, CI (lint+tests), variables de entorno, `.env` en `.gitignore`, healthcheck. → PUNTO DE APROBACIÓN
- **Etapa 2 — Modelo de datos.** Migraciones Alembic (UUID, DEFAULTs, índices); seed de catálogos (propiedades, áreas, sistemas típicos, departamentos estándar), `configuracion`, master data de usuarios inicial y marco institucional. → PUNTO DE APROBACIÓN
- **Etapa 3 — Ingesta y reconciliación.** Pipeline §10; `reconciliation_report.csv`; carga del master tras aprobación; Descriptores + organigrama; borradores USALI. → PUNTO DE APROBACIÓN
- **Etapa 4 — Backend API.** Auth (JWT access+refresh, rate limiting), CORS allowlist, roles; CRUD master con formato único + numeración atómica + versionado; creación colaborativa; firma electrónica + rechazo + reasignación + PDF firmado + documento controlado + bitácora + custodio; motor de asignación + overrides + sincronización/retiro/alertas; Descriptores + organigrama; búsqueda; auditoría. Pruebas de §7. → PUNTO DE APROBACIÓN
- **Etapa 5 — Frontend.** Marco institucional, usuarios, configuración, catálogos, librería maestra (9 campos), creación colaborativa + designación de firmantes, panel de firma (con rechazo), gestión documental del custodio, workspace por propiedad, asistente de asignación, editor de override con diff, colas, organigrama, tablero, búsqueda/filtros, exportación PDF/manual. Estilo §9. → PUNTO DE APROBACIÓN
- **Etapa 6 — Hardening y deploy.** Auditoría y bitácora completas, verificación de integridad por hash, exportaciones finales, respaldos, seed de producción, documentación (`README`, guía de operación, manual del custodio). Verificar recursos remotos (§0.6) y desplegar a Railway + Vercel. → PUNTO DE APROBACIÓN

---

## 13. Criterios de aceptación por etapa

- **E1:** levanta local; healthcheck OK; CI en verde; `.env` ignorado por git.
- **E2:** `alembic upgrade head` crea todo (UUID, DEFAULTs, índices); catálogos, `configuracion`, usuarios y marco institucional sembrados; diagrama del modelo generado.
- **E3:** `reconciliation_report.csv` marca los 34 conflictos; tras aprobación, los 74 SOP con cuerpo; catálogo `areas` sembrado; 24 Descriptores con `reporta_a`; 4 borradores USALI; 4 propiedades; CWL pre-asignado en `adoptado`.
- **E4:** número atómico al crear (sin reutilizar eliminados); el editor impone los 9 campos; solo elegibles por nivel son designables; master en `borrador` no asignable; `firmado` solo con todas las firmas; PDF firmado con hash; controlado inmutable con accesos/cambios en bitácora; rechazo invalida firmas parciales; reasignación auditada; adoptar fija versión; adaptar guarda deltas; versión nueva marca `requiere_actualizacion`; retiro marca `master_retirado`; sugerencias por sistemas correctas; CORS allowlist y rate limiting activos. Cubierto por tests.
- **E5:** flujos en español; marco/usuarios/configuración editables; creación colaborativa + firma + rechazo; custodio ve bitácora y controla acceso; diff visible; organigrama por propiedad; exporta manual por propiedad y descarga la versión firmada.
- **E6:** trazabilidad completa; integridad por hash verificable; despliegue accesible sin colisión con `crc-coordination-hub`; respaldos configurados; documentación presente.

---

## 14. No-funcionales

- **Roles y segregación de funciones:** `super_admin`, `editor_corporativo`, `editor_propiedad`, `custodio_documental`, `lector`. Alcance por propiedad vía `roles_usuario.propiedad_id`. La aprobación se materializa por firma (B2); quien redacta en solitario no finaliza como único firmante.
- **Seguridad:** JWT access corto + refresh; **CORS allowlist** al origen del frontend (nunca `*`); **rate limiting** en login y firma; validación de input en servidor (Pydantic); `.env` en `.gitignore`; secretos solo en variables de entorno.
- **Firma e integridad:** hash SHA-256 del PDF firmado; el controlado no se regenera; verificación de integridad disponible.
- **Auditoría:** acciones sensibles en `registro_auditoria`; accesos/cambios de controlados en `bitacora_control`.
- **Integridad de datos:** soft delete; FKs con `ON DELETE RESTRICT` donde corresponda; validaciones Pydantic/zod.
- **i18n:** UI y contenido en español; textos externalizados.
- **Rendimiento:** índices en FKs y en (`propiedad_id`, `sop_master_id`), (`codigo`), (`estado`), (`area_id`, `numero`).

---

## 15. Estructura de repositorio esperada

```
crc-ops-manual/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy (español, PK UUID)
│   │   ├── schemas/         # Pydantic
│   │   ├── api/             # routers FastAPI
│   │   ├── services/        # reglas de negocio (numeración, asignación, sync, retiro, firma, custodia)
│   │   ├── firma/           # firma electrónica + PDF + hash
│   │   ├── ingestion/       # pipeline de reconciliación (§10)
│   │   └── core/            # auth, config, db, seguridad (CORS, rate limit)
│   ├── alembic/
│   ├── tests/
│   └── Dockerfile
├── frontend/                # Next.js 14 + TS + Tailwind (español)
│   ├── app/
│   ├── components/
│   └── lib/
├── seed/
│   ├── source/              # archivos fuente (§10)
│   └── reconciliation_report.csv   # generado en E3
├── scripts/                 # utilidades (incluye variantes .ps1 para Windows)
├── docs/
├── CHANGELOG.md
└── README.md
```

---

## 16. Comando de arranque (pegar como primer mensaje a Claude Code)

> Vas a construir **CRC Operations Manual Hub** siguiendo el documento `PROMPT_CLAUDE_CODE_CRC_OPS_MANUAL.md` que te adjunto. Todo el sistema debe ser **en español** (interfaz, contenido, estados y modelo de datos). Entorno de desarrollo: **Windows**. Trabajá **etapa por etapa** (§12) y **detenete en cada PUNTO DE APROBACIÓN** hasta que yo apruebe. Antes de crear cualquier recurso remoto, aplicá la verificación de §0.6 y **no toques** el stack `crc-coordination-hub`. Empezá por la **Etapa 1 (scaffold e infra)**: proponé la estructura de repositorio (§15), el stack y los nombres de infraestructura (§4) y la configuración base, y esperá mi confirmación antes de la Etapa 2. Respetá la regla legal sobre USALI (§0) y las decisiones (§3). Mantené `CHANGELOG.md` desde el inicio.

---

### Anexo — Notas de contexto

- El contenido semilla proviene de **Corcovado Wilderness Lodge**; por eso CWL entra casi todo como `adoptado` y las demás propiedades asignan desde el master.
- Áreas/prefijos presentes en el material (sembrar en `areas`): `FIN, GE, SM, KIT, FBS, HR, IT, CT, GOV, CR` (índice curado de 74). El manual amplio incluye además `PR, RD, TT, EN, FB`; durante la reconciliación se decide cuáles incorporar.
- **Formato único de SOP (9 campos):** Código, Departamento/Área, Propósito, Evaluación de Riesgos, Controles Existentes, Procedimiento Detallado, Responsables, Evidencia/Reportes, Frecuencia de Revisión.
- **Descriptor de Puesto:** código, título, reporta a, nivel jerárquico (1–4), propósito, responsabilidades, nivel de autoridad, KPIs, requisitos.
- **Niveles jerárquicos:** 1 alta dirección · 2 dirección funcional · 3 jefatura/gerencia de departamento · 4 operativo. Firmantes = nivel `configuracion.nivel_minimo_firmante` o superior (por defecto 3).
- **Decisiones de negocio B1–B6 (§3):** son valores por defecto **ajustables**; cambialos ahí si tu operación difiere.
