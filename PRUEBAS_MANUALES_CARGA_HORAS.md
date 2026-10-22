# Suite de pruebas manuales

Plan funcional ordenado para validar cargas, autorizaciones, conceptos automáticos y liquidación. Cada comportamiento común se prueba una sola vez. Un convenio vuelve a aparecer solamente cuando cambia la regla o el resultado esperado.

## Preparación

- Disponer de usuarios activos CISPREN, SAL, SAT, FC y MONOTRIBUTISTA.
- Contar al menos con una persona de Nómina y otra de Monotributo o Consultora.
- Asignar a FC la habilitación excepcional requerida.
- Asignar `switcher_nocturnidad` solamente a una persona incluida en la prueba.
- Configurar un feriado que devuelve y otro que no devuelve dentro del período vigente.
- Usar fechas sin cargas anteriores, excepto cuando el caso indique lo contrario.
- Toda carga manual debe incluir una observación.

Períodos vigentes:

- Nómina: del 16 de un mes al 15 del siguiente.
- Monotributo y Consultora: mes calendario.

## A. Validaciones generales

### 1. Datos obligatorios y pasos horarios

- [ ] Con un usuario SAL, intentar procesar horas extras sin observación.
- [ ] Intentar enviar un horario incompleto.
- [ ] Intentar enviar minutos distintos de `00` o `30` manipulando el formulario.

**Resultado esperado:** los tres intentos son rechazados y no generan borrador ni filas en la base.

### 2. Límite de fecha por contratación

- [ ] Con una persona de Nómina, intentar cargar fuera del período 16–15 vigente.
- [ ] Con una persona Monotributo o Consultora, intentar cargar fuera del mes vigente.

**Resultado esperado:** cada intento es rechazado con el rango permitido correspondiente.

### 3. Cantidad manual en pasos de 0,5

- [ ] Con un usuario SAT, cargar `METROS TORRE = 8,5`.
- [ ] Intentar `METROS TORRE = 8,2`.

**Resultado esperado:** 8,5 se guarda como registro independiente; 8,2 es rechazado por el servidor.

### 4. Estado, edición y eliminación

- [ ] Crear una carga pendiente y editarla desde el usuario.
- [ ] Autorizarla desde Jefatura.
- [ ] Intentar editarla y eliminarla nuevamente desde el usuario.

**Resultado esperado:** la pendiente puede modificarse; la autorizada ya no puede editarse ni eliminarse.

### 5. Acceso administrativo

- [ ] Ingresar con RRHH y luego con ADMIN.
- [ ] Abrir Carga administrativa, Autorizaciones, Seguimiento, Exportación y Precargas autorizadas.

**Resultado esperado:** ambos roles acceden a las funciones administrativas. ADMIN puede ver cargas de todas las personas y roles.

## B. Horas extras y nocturnidad

### 6. Horas hábiles al 50% — referencia SAL

- [ ] Cargar un día hábil de 18:00 a 20:30.

**Resultado esperado:** se generan 2,5 horas al 50%, sin reintegro ni conceptos automáticos.

> No repetir en SAT: la clasificación al 50% es la misma. SAT se prueba aparte por comida, merienda y domingo.

### 7. Horas hábiles CISPREN

- [ ] Cargar un día hábil de 18:00 a 19:30.

**Resultado esperado:** se generan 1,5 horas al 100%. Esta prueba existe porque CISPREN difiere del 50% general.

### 8. Jornada nocturna que cruza medianoche

- [ ] Con un usuario SAL, cargar de 23:00 a 02:00.

**Resultado esperado:** se crean tramos con sus fechas reales, suman 3 horas extras y calculan 3 horas nocturnas sin duplicarlas.

### 9. Nocturnidad dentro de jornada habitual

- [ ] Cargar `NOCTURNAS EN JORNADA` para una jornada habitual de 18:00 a 22:00.

**Resultado esperado:** se guarda 1 hora nocturna en `cantidad`, sin generar horas extras. En las vistas debe identificarse claramente como nocturnidad habitual.

### 10. Superposición de jornada habitual y horas extras

- [ ] Cargar horas extras de 22:00 a 01:00.
- [ ] Intentar cargar para la misma fecha una jornada habitual de 21:00 a 23:00.
- [ ] Repetir con jornada habitual de 18:00 a 22:00.

**Resultado esperado:** 21:00–23:00 es rechazado por superposición; 18:00–22:00 es aceptado porque los intervalos son contiguos.

### 11. Subtotal único de horas nocturnas

- [ ] Autorizar una carga extra con nocturnidad y otra de `NOCTURNAS EN JORNADA` en el mismo período.
- [ ] Exportar desde RRHH.

**Resultado esperado:** ambas cantidades se suman bajo `HORAS NOCTURNAS`; no aparecen subtotales duplicados.

### 12. Switcher de nocturnidad asignado

- [ ] Usar una persona con asignación vigente de `switcher_nocturnidad`.
- [ ] Generar 2 horas nocturnas desde horas extras y 1 hora desde jornada habitual.

**Resultado esperado:** se genera un único registro automático de 3 `switcher_nocturnidad`. Al editar o eliminar las fuentes, la cantidad se recalcula sin duplicarse.

### 13. Switcher no asignado o fuera de vigencia

- [ ] Repetir una carga nocturna con una persona sin asignación vigente.

**Resultado esperado:** se conservan las horas nocturnas, pero no se genera `switcher_nocturnidad`.

## C. Franco, feriado y reintegro

### 14. Umbral común de cuatro horas — referencia SAL

- [ ] Informar un franco de 08:00 a 11:30.
- [ ] En otra fecha, informar un franco de 08:00 a 12:00.

**Resultado esperado:** 3,5 horas generan horas reales al 100%; exactamente 4 horas generan 1 franco trabajado.

> No repetir en CISPREN ni SAT: usan el mismo umbral. Sus diferencias se cubren en reintegro y conceptos propios.

### 15. Reintegro CISPREN

- [ ] En un feriado que devuelve, informar al menos 4 horas.
- [ ] Probar medio reintegro y reintegro completo en fechas distintas.
- [ ] Agregar horas extras asociadas en uno de los casos.

**Resultado esperado:** el día trabajado, el reintegro de 0,5 o 1 y las horas al 100% quedan en registros separados.

### 16. Feriado que no devuelve — referencia SAL

- [ ] En el feriado `Devuelve = No`, informar una jornada de al menos 4 horas.

**Resultado esperado:** se guarda 1 feriado trabajado, pero no se ofrece ni guarda reintegro.

## D. Comportamientos específicos por convenio

### 17. Automáticos SAT: comida y merienda

- [ ] Cargar 4 horas extras SAT.
- [ ] Editar la carga pendiente hasta totalizar 6 horas.

**Resultado esperado:** con 4 horas se generan 2 meriendas y 1 comida; con 6 horas se actualizan a 3 meriendas y 2 comidas, sin duplicados.

### 18. Domingo SAT y cruce desde sábado

- [ ] Informar una jornada de sábado 23:30 a domingo 07:00.

**Resultado esperado:** se conservan las fechas, se calcula nocturnidad y se genera 1 DOMINGO para el domingo, sin franco adicional ni reintegro.

### 19. Domingo SAT duplicado

- [ ] Con un DOMINGO pendiente, intentar otro para la misma persona y fecha.
- [ ] Autorizar el primero y volver a intentar.

**Resultado esperado:** ambos intentos de duplicación son rechazados.

### 20. HS ARTICULO SAT

- [ ] Cargar horas extras hasta las 23:00.
- [ ] Informar que la jornada siguiente comienza a las 08:00.

**Resultado esperado:** calcula 9 horas de descanso y agrega 3 HS ARTICULO con observación automática. La cantidad no puede editarse manualmente.

### 21. EXTERIOR PRENSA CISPREN

- [ ] Cargar cantidades 3 y 6 en fechas distintas.
- [ ] Intentar cantidad 4 manipulando el formulario.
- [ ] Intentar cargar dos veces EXTERIOR PRENSA para la misma persona y fecha.

**Resultado esperado:** 3 y 6 son aceptadas en fechas distintas; 4 es rechazada. Sólo se admite una carga de EXTERIOR PRENSA por persona y fecha, aunque la anterior esté pendiente o autorizada.

### 22. FC

- [ ] Sin habilitación vigente, intentar ingresar a la carga.
- [ ] Con habilitación, cargar horas hábiles al 50%.
- [ ] Informar un franco de 2 horas y otro con horas extra asociadas.

**Resultado esperado:** sin permiso no puede cargar. Con permiso admite horas hábiles al 50%; el franco siempre genera 1 día y las extras asociadas quedan al 100%. No genera reintegro, nocturnidad, comida ni merienda.

### 23. MONOTRIBUTISTA

- [ ] Cargar horas hábiles.
- [ ] Informar un franco corto con 1 hora extra asociada.
- [ ] Informar un feriado sin horas extra.

**Resultado esperado:** las hábiles quedan al 50%; el franco corto genera 1 día y 1 hora al 100%; el feriado genera 1 día. No permite reintegro ni genera comida o merienda.

### 24. Concepto excepcional personal

- [ ] Asignar temporalmente un concepto manual a una persona.
- [ ] Verificar con otra persona del mismo convenio sin asignación.

**Resultado esperado:** sólo la persona asignada puede verlo y cargarlo durante la vigencia. Las vistas y la exportación muestran su nombre real.

## E. Precargas autorizadas

### 25. Conceptos disponibles según convenio

- [ ] Entrar como RRHH o ADMIN y elegir una persona.
- [ ] Revisar el selector de conceptos.
- [ ] Comparar un convenio con franja nocturna y otro sin franja nocturna.

**Resultado esperado:** sólo aparecen conceptos generales configurados para su convenio. Si el convenio tiene franja nocturna, también aparece HORAS NOCTURNAS; si no la tiene, no aparece. No existe una opción para crear conceptos desde esta pantalla.

### 26. Períodos disponibles y límite

- [ ] Elegir una persona de Nómina y otra de Monotributo o Consultora.
- [ ] Revisar los períodos inicial y final.
- [ ] Intentar enviar manualmente un período histórico o más de 12 períodos.

**Resultado esperado:** Nómina ofrece 16–15; Monotributo/Consultora, meses calendario. Se muestra primero el período actual, no hay históricos y el máximo es 12. El servidor rechaza valores inválidos.

### 27. Generación y visualización del pack

- [ ] Crear un pack de 3 períodos para un concepto al 50% o 100%.
- [ ] Consultar Precargas autorizadas, el historial del usuario y Seguimiento.

**Resultado esperado:** se crean 3 filas aprobadas en `horas_extras`, una por inicio de período, con `tipo_registro = PRECARGA_AUTORIZADA`, cantidad informada y horarios nulos. La pantalla administrativa las agrupa como un pack.

### 28. Exclusión de cálculos automáticos

- [ ] Crear un pack cuyo inicio coincida con domingo, franco o feriado.

**Resultado esperado:** la fecha es sólo representativa. No genera día trabajado, DOMINGO, reintegro, nocturnidad, comida, merienda ni `switcher_nocturnidad`.

### 29. Exportación de precarga

- [ ] Crear una precarga de 4 horas al 100% y una carga real de 2 horas al 100% en el mismo período.
- [ ] Exportar desde RRHH.

**Resultado esperado:** el subtotal de `Horas extras al 100%` es 6. La precarga no aparece como un concepto diferente.

### 30. Editar y eliminar packs

- [ ] Editar cantidad, concepto, período final y motivo de un pack.
- [ ] Comprobar sus filas en Seguimiento.
- [ ] Eliminar el pack.

**Resultado esperado:** la edición reemplaza sin duplicar solamente las filas del período actual y los futuros; las precargas de períodos anteriores conservan sus datos originales. La eliminación también quita únicamente el período actual y los futuros. Un grupo completamente histórico se muestra sólo para consulta, sin acciones de edición o eliminación.

## F. Autorización, seguimiento y exportación

### 31. Autorización agrupada

- [ ] Autorizar una jornada con carga principal y conceptos automáticos.

**Resultado esperado:** todos los registros vinculados cambian juntos a Autorizada. Los automáticos no se administran como cargas aisladas.

### 32. Seguimiento por persona

- [ ] Filtrar por período, usuario, convenio y contratación.

**Resultado esperado:** las cargas cumplen todos los filtros y el subtotal coincide con el detalle. Las precargas se identifican como `Precarga autorizada`.

### 33. Exportación consolidada

- [ ] Exportar un período con horas, nocturnidad, días, reintegros, otras cargas, excepcionales y precargas.

**Resultado esperado:** sólo se exportan autorizadas. La hoja resumen consolida por persona y concepto; el detalle conserva fecha y observación.

## Registro de ejecución

| Caso | Fecha | Usuario/convenio | Resultado real | Estado | Evidencia u observaciones |
|---:|---|---|---|---|---|
| 1 |  |  |  | Pendiente |  |
| 2 |  |  |  | Pendiente |  |
| 3 |  |  |  | Pendiente |  |
| 4 |  |  |  | Pendiente |  |
| 5 |  |  |  | Pendiente |  |
| 6 |  |  |  | Pendiente |  |
| 7 |  |  |  | Pendiente |  |
| 8 |  |  |  | Pendiente |  |
| 9 |  |  |  | Pendiente |  |
| 10 |  |  |  | Pendiente |  |
| 11 |  |  |  | Pendiente |  |
| 12 |  |  |  | Pendiente |  |
| 13 |  |  |  | Pendiente |  |
| 14 |  |  |  | Pendiente |  |
| 15 |  |  |  | Pendiente |  |
| 16 |  |  |  | Pendiente |  |
| 17 |  |  |  | Pendiente |  |
| 18 |  |  |  | Pendiente |  |
| 19 |  |  |  | Pendiente |  |
| 20 |  |  |  | Pendiente |  |
| 21 |  |  |  | Pendiente |  |
| 22 |  |  |  | Pendiente |  |
| 23 |  |  |  | Pendiente |  |
| 24 |  |  |  | Pendiente |  |
| 25 |  |  |  | Pendiente |  |
| 26 |  |  |  | Pendiente |  |
| 27 |  |  |  | Pendiente |  |
| 28 |  |  |  | Pendiente |  |
| 29 |  |  |  | Pendiente |  |
| 30 |  |  |  | Pendiente |  |
| 31 |  |  |  | Pendiente |  |
| 32 |  |  |  | Pendiente |  |
| 33 |  |  |  | Pendiente |  |

Estados sugeridos: **OK**, **Falló** o **No se pudo probar**.
