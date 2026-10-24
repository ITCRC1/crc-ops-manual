# FIN-0034 — Estado de la revisión (pausada 2026-10-24)

**Archivo de trabajo:** [`FIN-0034.md`](FIN-0034.md) · rama `docs/fin-0034-gastos-viaje`

## Criterio acordado
- Se conserva el **texto original completo**, con su estructura (6 secciones, 10 pasos). No se borra ni se reescribe nada.
- Los puntos nuevos se agregan dentro de cada sección, marcados con ➕. Los ➕ se quitan al cargar el SOP en la app.
- No se borra nada en la app ni en la base: el contenido del borrador se reemplaza y el original queda en el historial de versiones.

## Ya incorporado
- Máximas a–i: viaje aprobado; liquidación en 2 días naturales; factura obligatoria; el hotel absorbe el gasto del negocio; alcohol; gastos ajenos al negocio; persona que originó el gasto y participantes en gastos de grupo; factura electrónica obligatoria en viajes locales; liquidación en la plataforma BTM.
- Tres tipos de viaje: International Sales Travel (tipo de cambio BCCR a la fecha de liquidación), Local Sales Travel (kilometraje a US$0.40/km), Local Hotel Travel (hospedaje y comida en hoteles del grupo como cortesía).
- Solicitud de adelanto de viaje, aprobada por el superior directo y el director del área.
- Directores de área: Gerente de Operaciones (Local Hotel) y Director de Ventas y Mercadeo (Sales).
- Sobrante del adelanto: se devuelve en 2 días hábiles, con recibo de dinero.

## Preguntas abiertas
1. ¿La solicitud de adelanto de viaje también se hace en BTM, o solo la liquidación?
2. ¿Las aprobaciones (superior directo + director del área) se dan dentro de BTM?
3. Formularios CT-EXP-01/02/03 del original: ¿se reemplazan por pantallas de BTM o se mantienen para gastos que no son de viaje?
4. Confirmar las decisiones que tomé sin consultar:
   - en viajes locales, sin factura electrónica no hay reembolso;
   - el kilometraje es la única excepción a la factura;
   - la prohibición explícita de liquidar en papel, correo o Excel.

## Siguientes pasos
1. Cerrar las preguntas abiertas.
2. Iniciar sesión en ops.thecostaricacollection.com y verificar el rol del usuario (`super_admin`).
3. Ver si FIN-0034 ya tiene capa SMART en producción. Si no la tiene, generarla a partir de este texto.
4. Cargar el texto (sin ➕) en FIN-0034. Sigue en borrador hasta firmarse.
