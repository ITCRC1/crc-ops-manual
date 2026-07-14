# Análisis de Brechas — Controles Financiero-Operativos

Compara la cobertura de los **76 SOPs ya cargados** de The Costa Rica Collection contra una taxonomía de **83 dominios de control** financiero-operativo estándar de la industria hotelera (15 categorías).

> **Nota legal.** La taxonomía se derivó de *conceptos genéricos* de control interno inspirados en la estructura de manuales financieros hoteleros de referencia (con copyright). **No se copió ni almacenó texto propietario**; los dominios son categorías factuales de control. Los SOPs para llenar las brechas deben redactarse con **contenido original de CRC**.

**Método:** un agente por categoría evaluó cobertura por significado (no por código) contra el inventario completo; un verificador adversarial reexaminó cada brecha y parcial para descartar falsos positivos.

## Resumen

| Cobertura | # | Qué significa |
|-----------|---|---------------|
| ✅ Cubierto | 28 | Existe un SOP de CRC que cubre el control |
| 🟡 Parcial | 30 | Hay un SOP relacionado, pero falta formalizar una pieza |
| 🔴 Brecha | 23 | CRC no tiene ningún SOP para el control |
| ⚪ No aplica | 2 | No relevante para un eco-lodge remoto de una propiedad |
| **Total** | **83** | |

## 🔴 Brechas — SOPs a crear (prioridad)

Controles sin ningún SOP en el inventario. Ordenados por categoría.

### Caja y Tesorería
- **Procedimientos bancarios y control de cuentas** — Confirmado tras re-escanear los 76 SOPs. Ninguno regula apertura/cierre de cuentas bancarias, firmantes autorizados ni acceso a banca electrónica. FIN-0017 (Segregación de Funciones & Matriz de Autorizaciones) cubre autorizaciones en general pero no administración bancaria. No hay tampoco un SOP de conciliación bancaria en el inventario (ese control pertenece a otra categoría). Brecha real.
- **Control y custodia de cheques (emisión y firmas)** — Confirmado. Ningún SOP cubre emisión, custodia, secuencia numérica ni firmas mancomunadas de cheques físicos. CT-0004 es pagos electrónicos/chargebacks y FIN-0025 es three-way match de AP; ninguno regula cheques. Brecha real (aun con bajo volumen esperado en un lodge remoto).
- **Desembolsos de caja (paid outs) con límites y aprobaciones** — Confirmado. Ningún SOP regula paid outs de caja con límites, aprobaciones y soporte. GE-0004 arquea la caja pero no define el procedimiento de paid outs; FIN-0017 da autorizaciones generales, no este control específico. Brecha real.
- **Caja chica (petty cash)** — Confirmado. No existe SOP de caja chica (constitución, custodio, vales, reembolso, arqueos, límites). Ningún documento del inventario aborda petty cash. Brecha real.
### Ingresos y Cuentas por Cobrar
- **Cortesías y consumos internos (meals & entertainment)** — Brecha confirmada tras re-escaneo completo. FBS-0008 (voids) y GE-0008 (ajustes OPERA) tratan correcciones/ajustes, no una política de complimentary/comps/consumos internos con autorización y registro. GOV-0004 es el catálogo de cuentas (incluye la cuenta USALI 7090 Complimentary F&B) pero un renglón de catálogo no es un control de autorización. No existe SOP dedicado. Brecha real de control frente a fuga de ingresos por cortesías.
- **Descuentos a empleados** — Brecha confirmada tras revisar HR-0001..HR-0007 y SM-0011. SM-0011 (Control de Descuentos y Overrides) trata descuentos comerciales/overrides de venta, no el beneficio a empleados; HR-0007 es disciplina. Ningún SOP regula tarifas preferenciales a empleados (rooms/F&B) con topes y aprobación. Brecha de bajo impacto dado el tamaño de la operación.
### Activos Fijos y Equipo Operativo
- **Altas y reemplazos de activos fijos** — Re-escaneados los 76 SOPs: ninguno gobierna capitalización, alta o reemplazo de activos fijos. FIN-0021 a FIN-0025 (PR/PO/proveedores/three-way match) cubren la adquisición y aprobación de la compra, pero no distinguen gasto vs. activo capitalizable, umbral de capitalización, ni el registro/etiquetado del activo en un registro de activos fijos. IT-0003 e IT-0006 solo inventarían equipo tecnológico, no mobiliario, embarcaciones ni equipo de cocina/operativo. Brecha confirmada.
- **Bajas y retiros de activos fijos** — No hay SOP que regule la baja, retiro, venta o disposición de activos fijos ni el registro de la ganancia/pérdida por disposición. HR-0005 e IT-0002 solo tratan desactivación de accesos y devolución de equipo tecnológico al terminar personal, no la baja contable de activos. Relevante para un lodge con embarcaciones y equipo operativo significativo. Brecha confirmada.
- **Arrendamientos (leases)** — CORRECCIÓN: el auditor marcó 'parcial' citando FIN-0024 y GOV-0002, pero esas citas no corresponden. FIN-0024 es alta/evaluación/control de PROVEEDORES (procurement), no contabilización de arrendamientos; GOV-0002 es solo el FORMATO estándar de políticas contables (una plantilla), no una política de leases. Ninguno aborda clasificación del arrendamiento, reconocimiento del activo por derecho de uso / pasivo, ni el tratamiento del gasto de renta. La taxonomía enlista 'Contratos, arrendamientos y otros acuerdos', 'Acuerdos con operadores terceros' y 'Firma de contratos comerciales', pero ningún SOP del inventario los cubre. Calificar 'parcial' sobre-estima la cobertura: es brecha real.
- **Reserva de FF&E (muebles y equipo)** — Ningún SOP establece la reserva de FF&E (cálculo como % de ingresos, acumulación ni uso). FIN-0020 (reconocimiento de ingresos USALI) y GOV-0004 (catálogo de cuentas) no la abordan. Control USALI típico para un lodge de lujo con inversión continua en mobiliario y equipo. Brecha confirmada.
### Compras / Cuentas por Pagar
- **Conciliación de estados de cuenta de proveedores** — Brecha confirmada tras re-escaneo de los 76 SOPs. Ningún SOP aborda la conciliación periódica de los estados de cuenta de proveedores contra el saldo de AP en libros para detectar facturas faltantes, notas de crédito no aplicadas o cobros indebidos. FIN-0024 evalúa proveedores pero no concilia sus estados de cuenta; FIN-0001 es del lado de ingresos; las conciliaciones documentadas (FIN-0018 journal entries) no incluyen statements de proveedor. No es falso positivo.
- **Reportes de gastos (expense reports)** — Brecha confirmada tras re-escaneo completo. No existe SOP que regule reportes de gastos de empleados (reembolsos, adelantos de viaje, tarjetas corporativas, liquidación con recibos, políticas de gastos elegibles y aprobación). CT-0003 (cajas fuertes), CT-0004 (pagos electrónicos/chargebacks) y HR-0006 (horas/turnos/HxE) no lo cubren; tampoco existe SOP de caja chica / petty cash / paid-outs. Aplica plenamente a un eco-lodge remoto donde el personal incurre en gastos de traslado y compras de emergencia. Brecha real.
### Pasivos Acumulados e Impuestos
- **Acumulaciones de nómina** — Re-escaneados los 76 SOPs: ninguno cubre el cálculo y registro de las acumulaciones de nómina (aguinaldo 1/12, cesantía/preaviso, salarios devengados no pagados, planilla acumulada al cierre). HR-0006 controla horas/turnos/horas extra y FIN-0011 el control financiero de headcount/contratación, pero ninguno aborda la PROVISIÓN CONTABLE de nómina. GOV-0005 (cierre) las presupone pero no las procedimenta. Los SOPs de HR (HR-0001/0003/0004/0005/0006/0007) son de gestión de personal, no de provisión contable. Brecha confirmada — material para un eco-lodge sujeto a Derecho Laboral CR.
- **Pasivo por vacaciones** — Re-escaneados los 76 SOPs: no existe SOP que documente el cálculo, registro y control del pasivo acumulado por vacaciones (devengo 2/52, saldo de días acumulados por empleado vs. tomados, valuación al cierre). HR-0006 (horas y turnos) no cubre la provisión contable de vacaciones y ningún otro SOP de HR o FIN lo aborda. Obligación laboral CR material — brecha confirmada.
- **Impuestos acumulados y su pago** — Re-escaneados los 76 SOPs: ninguno cubre la acumulación mensual del impuesto sobre la renta (provisión 30% sobre utilidad), su liquidación, calendario de pago ni retenciones fiscales. CT-0004 trata chargebacks de pagos electrónicos, GOV-0005 el cierre de EEFF y GOV-0004/FIN-0020/FIN-0027 clasificación/reconocimiento de ingresos, pero ninguno procedimenta el devengo ni la remisión de impuestos. Brecha confirmada.
- **IVA / impuesto sobre ventas y sobre compras** — Re-escaneados los 76 SOPs: no hay ningún SOP de IVA — ni el registro de IVA repercutido en ventas (habitaciones, A&B, tours, transporte), ni el IVA soportado en compras, ni la conciliación/declaración/remisión mensual del saldo neto. FIN-0027, FIN-0020 y GOV-0004 tratan reconocimiento/clasificación de ingresos y catálogo de cuentas pero no la mecánica del IVA. Brecha confirmada — relevante para operación en Costa Rica.
- **Acumulación y remisión de cargas de nómina (CCSS)** — Re-escaneados los 76 SOPs: ninguno cubre el cálculo, acumulación y remisión mensual de las cargas patronales de la CCSS (SEM, IVM, BP) e instituciones asociadas (INS Riesgos, IMAS, INA, ASFA, FONATEL). HR-0006 controla horas y FIN-0011 el costo de contratación/headcount, pero ninguno aborda la provisión ni el pago a la seguridad social. Obligación material en CR — brecha confirmada.
### Deuda y Patrimonio
- **Contabilidad de deuda de largo plazo** — CONFIRMADO tras re-escaneo de los 76 SOPs: ninguno trata contabilidad de deuda de largo plazo (registro del préstamo, clasificación corriente/no corriente, tabla de amortización, cálculo/devengo de intereses, covenants, conciliación del saldo con el acreedor). Se descartaron todos los candidatos plausibles: FIN-0018 (Journal Entries) solo registra asientos genéricos y no define política de deuda; GOV-0005 (Cierre Contable Mensual + estados financieros) presentaría el pasivo en el balance/notas pero no controla su contabilidad; GOV-0002 (Política Contable – Formato Estándar) es una plantilla de formato, no una política de deuda; GOV-0004 (Catálogo de Cuentas) solo clasificaría las cuentas de pasivo. No hay SOP de tesorería/financiamiento. FIN-0018 y GOV-0005 son a lo sumo tangenciales, no cobertura. Aplica porque un eco-lodge remoto financia CAPEX/infraestructura con deuda. Brecha real, no falso positivo.
### Nómina
- **Procesamiento y fondeo de nómina** — Brecha confirmada tras re-escanear los 76 SOPs. Ninguno describe el cálculo/procesamiento de la planilla ni el fondeo/pago (preparación del payroll, revisión, aprobación de la corrida, transferencia de fondos y distribución de pagos). Los candidatos de pago que existen son de otra naturaleza: CT-0004 (pagos electrónicos/chargebacks de tarjetas), FIN-0021/0022/0023/0025 (ciclo de compras PR/PO/three-way match a proveedores) y FBS-0018 (acumulación de facturas de mercadería); ninguno es nómina. HR-0006 solo captura horas y FIN-0011 solo aprueba headcount. No es falso positivo.
- **Anticipos y labor temporal/casual** — Brecha confirmada tras re-escanear los 76 SOPs. No hay ningún SOP que regule anticipos de salario a empleados ni la contratación/pago de labor temporal, ocasional o casual (jornaleros/contract labor). HR-0003 cubre reclutamiento formal permanente; HR-0001 es inducción; ninguno contempla personal casual ni anticipos. No es falso positivo.
### Conciliaciones
- **Conciliaciones bancarias** — Confirmada la brecha tras re-escanear los 76 SOPs (verificacion prioritaria por ser el error mas costoso). Ninguno formaliza la conciliacion bancaria: cotejo del estado de cuenta del banco vs. libro/mayor de caja, partidas en transito, cheques y depositos pendientes y ajustes. FIN-0001 concilia ingresos (POS/OPERA vs. cobros); FIN-0002 es cuadre de auditoria nocturna de postings diarios; CT-0004 maneja pagos electronicos/chargebacks; CT-0003 es custodia de cajas fuertes; GE-0004 es cierre de cajero (drawer); GOV-0005 presupone la conciliacion bancaria pero no la documenta como control con procedimiento, responsable ni evidencia. Es brecha relevante incluso para un eco-lodge remoto: maneja cuentas bancarias, tarjetas y moneda extranjera.
### Reporting y Estados Financieros
- **Reporte de gastos de capital (capex)** — Brecha CONFIRMADA tras re-escaneo adversarial de los 76 SOPs. IT-0003 'Inventario de Activos y Licencias' e IT-0006 'Inventario Crítico IT' son inventarios de activos de TI, no reporte de capex. Las compras (FIN-0021/0022/0023/0025) tratan requisiciones/PO/three-way match de gasto operativo. No existe SOP de altas/bajas de activos fijos, reserva FF&E, depreciación, autorización de capex ni reporte de avance vs presupuesto de capital. No es falso positivo: brecha real y material para un eco-lodge remoto (embarcaciones, equipo, infraestructura).
### Gestión de Costo Laboral
- **Estándares laborales fijos/variables y staffing guide** — Confirmado tras re-escaneo adversarial de los 76 SOPs. Ningún SOP define estándares laborales fijos vs. variables ni una staffing guide (posiciones/FTE requeridos por nivel de ocupación, cubiertos de A&B, tours vendidos o pasajeros de transporte marítimo). Candidatos descartados: FIN-0011 gobierna la aprobación financiera de plazas (no el estándar de dotación por unidad de negocio); HR-0006 cubre control de horas/turnos/OT (ejecución de scheduling, no el estándar de referencia); HR-0003 cubre reclutamiento; KIT-0001 estandariza recetas y su costeo (comida, no mano de obra). No hay ningún SOP cuyo nombre o alcance implícito establezca cuánta mano de obra por unidad de demanda. Brecha real y crítica para un eco-lodge remoto con demanda estacional variable. No es un falso positivo.

## 🟡 Cobertura parcial — reforzar

Controles tocados por un SOP existente, pero con una pieza formal pendiente.

| Categoría | Control | SOPs CRC relacionados | Qué falta |
|-----------|---------|----------------------|-----------|
| Caja y Tesorería | Fondos fijos / house funds | GE-0004 | Confirmado parcial. GE-0004 (Cierre de Cajero) cubre el manejo y arqueo del cajero, lo que implica un fondo de cambio (house fund). No existe un SOP que formalice asignación, custo… |
| Caja y Tesorería | Manejo de moneda extranjera y tipo de cambio | FIN-0001, GE-0004 | Confirmado parcial. FIN-0001 (Reconciliación Diaria de Ingresos) y GE-0004 (Cierre de Cajero) implican cierre en distintas divisas (USD/CRC), pero ningún SOP fija la política de ac… |
| Caja y Tesorería | Posición diaria de caja | FIN-0016, FIN-0001, FIN-0002, GE-0004 | Confirmado parcial, con GE-0004 añadido como soporte. FIN-0016 (Daily Revenue Report), FIN-0001 (Reconciliación Diaria de Ingresos) y FIN-0002 (Auditoría Nocturna) producen la posi… |
| Ingresos y Cuentas por Cobrar | Rentas y otros ingresos | FIN-0020, FIN-0027, FIN-0001, FIN-0016 | FIN-0020 y FIN-0027 dan el marco de reconocimiento por componente aplicable a tours, experiencias y transporte marítimo; FIN-0001 (Reconciliación Diaria) y FIN-0016 (Daily Revenue … |
| Inventarios | Corte y valuación de inventario | FBS-0018, FBS-0011, GOV-0005, KIT-0001, FBS-0009 | Confirmada la cobertura PARCIAL tras re-escaneo de los 76 SOPs. El componente de CORTE (cut-off) sí está soportado: FBS-0018 (Registro de Recibo & Acumulación de Facturas) fija el … |
| Activos Fijos y Equipo Operativo | Depreciación y amortización | GOV-0005, GOV-0004 | GOV-0005 (cierre contable mensual y emisión del paquete de estados financieros) implica que la depreciación se registra dentro del cierre, y GOV-0004 (catálogo de cuentas departame… |
| Activos Fijos y Equipo Operativo | Control y obsolescencia de equipo operativo | IT-0003, IT-0006, FBS-0013 | IT-0003 (inventario de activos y licencias) e IT-0006 (inventario crítico IT para hotel remoto) controlan el equipo tecnológico; FBS-0013 (manejo de bodegas y almacenes) cubre el r… |
| Compras / Cuentas por Pagar | Política de compras (purchasing) | FIN-0021, FIN-0022, FIN-0023, FIN-0024 | El ciclo de compras está fuertemente instrumentado: FIN-0021 (Requisiciones PR), FIN-0022 (Aprobación de Compras & Matriz de Autorizaciones), FIN-0023 (Órdenes de Compra PO) y FIN-… |
| Compras / Cuentas por Pagar | Cuentas por pagar | FBS-0018, FIN-0025 | Confirmado parcial. FBS-0018 (Registro de Recibo & Acumulación de Facturas) cubre el ingreso y acumulación de facturas de proveedor y FIN-0025 (Three-Way Match) la validación previ… |
| Compras / Cuentas por Pagar | Desembolsos y pagos electrónicos | CT-0004, FIN-0017 | Confirmado parcial. CT-0004 (Pagos Electrónicos & Chargebacks) trata el lado de COBRO a huéspedes/tarjetas y chargebacks, no el desembolso a proveedores; FIN-0017 (Segregación de F… |
| Compras / Cuentas por Pagar | Contratos, arrendamientos y otros acuerdos | SM-0005, FIN-0024 | Confirmado parcial. SM-0005 (Contratos de Grupos) cubre solo contratos comerciales del lado de ventas y FIN-0024 el alta/relación con proveedores. Falta un SOP transversal de gesti… |
| Pasivos Acumulados e Impuestos | Acumulación de pasivos (accruals) general | GOV-0005, FBS-0018, FIN-0018, GOV-0002 | GOV-0005 (Cierre Contable Mensual y emisión del paquete de EEFF) implica el registro de acumulaciones al cierre; FIN-0018 controla los journal entries/ajustes por los que se asient… |
| Deuda y Patrimonio | Patrimonio (equity) y aportes | GOV-0005 | CONFIRMADO. GOV-0005 (Cierre Contable Mensual y Emisión del Paquete de Estados Financieros — Resultado Integral, Cambios en el Patrimonio y Notas Explicativas) incluye explícitamen… |
| Nómina | Autorización de nómina y cambios de estatus | FIN-0017, FIN-0011, HR-0003, HR-0005 | Corrijo agregando FIN-0017 'Segregación de Funciones & Matriz de Autorizaciones', que el auditor omitió: define quién autoriza qué y la segregación de funciones, lo cual aplica dir… |
| Nómina | Cumplimiento de ley laboral (CR) | HR-0006, HR-0007, HR-0005 | Confirmado como parcial. HR-0006 (horas/horas extra), HR-0007 (régimen disciplinario/incidentes) y HR-0005 (terminación) tocan aspectos normados por el Código de Trabajo CR y las c… |
| Nómina | Sistemas de tiempo y asistencia | HR-0006 | Confirmado como parcial. HR-0006 controla horas, turnos y horas extra a nivel de proceso, tocando tangencialmente la captura de asistencia. Falta un SOP que gobierne específicament… |
| Conciliaciones | Conciliaciones del libro mayor (GL) | GOV-0005, FIN-0001, FIN-0002 | Re-escaneados los 76 SOPs: no existe ninguno dedicado a la conciliacion/sustanciacion de cuentas del mayor (cotejo de auxiliares vs. mayor, sustanciacion de cuentas de balance gene… |
| Reporting y Estados Financieros | Estado de flujo de caja | GOV-0005 | Corregido: se eliminó la cita a CT-0004 'Pagos Electrónicos & Chargebacks' del auditor, que no tiene relación alguna con un Estado de Flujo de Efectivo (era cita espuria). GOV-0005… |
| Reporting y Estados Financieros | Paquete de reporte de fin de año | GOV-0005, FIN-0006 | GOV-0005 define el paquete mensual de EEFF y notas, base reutilizable para el cierre anual, y FIN-0006 aporta cierre de variancias/forecast, pero no existe SOP dedicado al cierre/p… |
| Crédito y Cobranza | Aprobación de crédito (rooms / grupos) | SM-0005 | CONFIRMADO parcial. SM-0005 (Contratos de Grupos) fija los términos comerciales/contractuales de grupos, que es lo más cercano a otorgar crédito a un grupo/agencia. Sin embargo NIN… |
| Crédito y Cobranza | Facturación y cobranza / direct billing | FIN-0019, SM-0005 | CONFIRMADO parcial. FIN-0019 (Control de Cuentas por Cobrar Críticas) vigila y controla saldos por cobrar (seguimiento/gestión de cobro), y SM-0005 (Contratos de Grupos) fija térmi… |
| Crédito y Cobranza | Bad debt write-offs (incobrables) | FIN-0019 | CONFIRMADO parcial (borderline, pero NO brecha). FIN-0019 (Control de Cuentas por Cobrar Críticas) es el antecedente natural del castigo: da seguimiento a CxC problemáticas. No def… |
| Crédito y Cobranza | Aging / balance de comprobación de CxC | FIN-0019 | CONFIRMADO parcial. FIN-0019 (Control de Cuentas por Cobrar Críticas) es el hogar natural del monitoreo de saldos por cobrar e implica su revisión, pero no se identifica un SOP que… |
| Presupuesto | Proceso de presupuesto anual, forecast y plan multianual | FIN-0006, SM-0010, FIN-0011 | Verificado contra los 76 SOPs: no existe ningun SOP que gobierne el CICLO DE ARMADO del presupuesto anual (calendario, supuestos, quien construye cada linea, iteraciones, aprobacio… |
| Gestión de Costo Laboral | Filosofía y proceso de gestión de costo laboral | FIN-0011, FIN-0006, FIN-0026 | Verificado. FIN-0011 (Control Financiero para Contratación y Headcount) establece el control financiero sobre la autorización de plazas y la creación de headcount; FIN-0006 (Budget… |
| Gestión de Costo Laboral | Scheduling y variancias vs estándar | HR-0006 | Verificado. HR-0006 (Control de Horas, Turnos y Horas Extra) cubre efectivamente el lado de scheduling: elaboración/control de turnos y gestión de horas extra; la cita corresponde.… |
| Administración y Gobierno | Procedimientos de entrega de puesto (handover) | GE-0004, FIN-0002, HR-0006 | Se confirma la cobertura fragmentada. GE-0004 (Cierre de Cajero) cubre la entrega/cuadre del turno de caja y FIN-0002 (Auditoría Nocturna) es de hecho un traspaso formal del día co… |
| Administración y Gobierno | Retención de registros documentales | GOV-0001, GOV-0003, GOV-0005, IT-0008 | Se confirma. El marco de gobierno documental existe: GOV-0001 (creacion de SOPs), GOV-0003 (control de cambios/versionado del manual), GOV-0005 (cierre mensual y emision del paquet… |
| Administración y Gobierno | Acuerdos con operadores terceros | FIN-0024, SM-0005 | CORRECCION: el auditor marco brecha (sops vacios), pero eso es un falso positivo. FIN-0024 (Alta, Evaluacion y Control de Proveedores) SI brinda cobertura parcial de los operadores… |
| Administración y Gobierno | Firma de contratos comerciales | FIN-0017, FIN-0022, SM-0005 | Se confirma. Existen matrices de autorizacion que definen quien aprueba/firma en dominios especificos: FIN-0017 (segregacion de funciones y matriz de autorizaciones, directamente l… |

## ✅ Cubierto

| Categoría | Control | SOPs CRC |
|-----------|---------|----------|
| Caja y Tesorería | Depósitos anticipados y prepagos | GE-0011, FIN-0027, FIN-0020 |
| Caja y Tesorería | Control de cajas fuertes (safe control) | CT-0003 |
| Ingresos y Cuentas por Cobrar | Reconocimiento y control de ingresos (marco general) | FIN-0020, FIN-0027, FIN-0001, FIN-0016 |
| Ingresos y Cuentas por Cobrar | Control de ingresos de habitaciones | FIN-0001, FIN-0016, FIN-0002, GE-0004, GE-0005, GE-0008 |
| Ingresos y Cuentas por Cobrar | No-shows y cancelaciones protegidas | GE-0010 |
| Ingresos y Cuentas por Cobrar | Voids y ajustes de venta en POS (F&B) | FBS-0008 |
| Ingresos y Cuentas por Cobrar | Política de propinas y service charge | FBS-0007, FBS-0006, FIN-0027 |
| Ingresos y Cuentas por Cobrar | Allowances / ajustes de front office con límites y aprobaciones | GE-0008, FIN-0017 |
| Ingresos y Cuentas por Cobrar | Recibos de caja (cash receipts) | GE-0004, FIN-0001, CT-0003 |
| Ingresos y Cuentas por Cobrar | Integridad de saldos del ledger | GE-0009, FIN-0002, FIN-0019, FIN-0001 |
| Inventarios | Control general de inventarios | FBS-0011, FBS-0013, FBS-0014, FBS-0015 |
| Inventarios | Observación y conteo físico de inventario | FBS-0011, FBS-0014 |
| Inventarios | Gasto mensual de inventario | FBS-0009, FBS-0011 |
| Compras / Cuentas por Pagar | Requisiciones y órdenes de compra | FIN-0021, FIN-0023, FIN-0022 |
| Compras / Cuentas por Pagar | Recepción de mercancías y control de calidad | FIN-0025, FBS-0012, FBS-0016, FBS-0017 |
| Compras / Cuentas por Pagar | Almacenamiento y salidas de bodega (issues) | FBS-0013, FBS-0014, FBS-0015, FBS-0011 |
| Compras / Cuentas por Pagar | Comisión de agencias de viaje / OTAs | SM-0012, FIN-0027 |
| Nómina | Control de horas / time sheets | HR-0006 |
| Nómina | Reporte y asignación de propinas | FBS-0006, FBS-0007 |
| Conciliaciones | Control de asientos contables (journal entries) | FIN-0018, FIN-0017 |
| Sistemas / IT | Controles de cómputo y seguridad de sistemas | IT-0001, IT-0002, IT-0003, IT-0004, IT-0005, IT-0006, IT-0007, IT-0008, HR-0005 |
| Reporting y Estados Financieros | Reporte diario de ingresos | FIN-0016, FIN-0001, FBS-0010 |
| Reporting y Estados Financieros | Reporte de costo de F&B | FBS-0009, KIT-0001 |
| Reporting y Estados Financieros | Reporte de labor / FTE / headcount | FIN-0026, HR-0006, FIN-0011 |
| Reporting y Estados Financieros | Pronóstico de negocio (business forecast) | FIN-0006, SM-0010 |
| Reporting y Estados Financieros | Catálogo de cuentas y diccionario contable | GOV-0004, FIN-0020 |
| Reporting y Estados Financieros | Cierre mensual (month-end) | GOV-0005 |
| Crédito y Cobranza | Tarjetas de crédito y chargebacks | CT-0004 |

## ⚪ No aplica

- **Manejo de inversiones / excedentes de caja** (Caja y Tesorería) — Confirmado no_aplica. Un eco-lodge remoto de una sola propiedad no gestiona inversión de excedentes a nivel operativo; esa decisión es corporativa/de dueños. No es una brecha encubierta: es un control que no procede a nivel propiedad. Justificación correcta.
- **Ingresos de lavandería y valet** (Ingresos y Cuentas por Cobrar) — No_aplica justificado. Ningún SOP del inventario menciona ingreso de lavandería/valet. En un eco-lodge remoto de lujo la lavandería de huéspedes es cortesía/incluida y no es una línea de ingreso material; el servicio interno se gestiona como gasto operativo. No se usa no_aplica para esconder una brecha real.
