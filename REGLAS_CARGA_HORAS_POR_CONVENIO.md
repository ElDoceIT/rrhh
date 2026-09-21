# Reglas de carga de horas por convenio

Estado relevado del código y de los parámetros vigentes al **16/09/2026**.

## Reglas comunes

- Sólo una persona con perfil **USUARIO** puede cargar sus propias horas. Un jefe no puede agregar ni editar cargas.
- Toda carga requiere **observaciones**.
- Las horas de inicio y fin se ingresan en intervalos de **30 minutos**.
- Si el horario cruza medianoche, se divide en dos registros con sus fechas reales, pero ambos tramos se consideran una misma jornada para COMIDA y MERIENDA.
- Un feriado configurado tiene prioridad. Un sábado o domingo no se considera franco automáticamente.
- Las horas comunes se resuelven buscando una única regla para la combinación **convenio + tipo de día** (`HABIL`, `FERIADO` o `FRANCO`).
- Las horas nocturnas se calculan con la franja configurada en esa regla.
- En la carga normal de horas extras sólo se admiten días hábiles, salvo el tratamiento especial de domingo para SAT. Los feriados y francos se cargan desde **Franco o feriado trabajado**.
- Como regla general, si un franco o feriado se trabajó menos de 4 horas, se cargan las horas reales trabajadas al 100%. FC y MONOTRIBUTISTA son excepciones: siempre registran 1 día trabajado, cualquiera sea la duración.
- En un franco o feriado trabajado se pueden indicar horas extras adicionales. La cantidad debe ser múltiplo de `0,5`, no puede superar la jornada y se toma desde el final del horario informado.
- El reintegro sólo se permite si la regla del convenio y tipo de día lo habilita. Además, un feriado marcado con `devuelve = NO` no admite reintegro.
- Los registros pendientes pueden modificarse o eliminarse; los autorizados o rechazados no pueden modificarse.

## Cálculos automáticos por jornada

- **MERIENDA:** `cantidad = parte entera de horas extras / 2`, sólo si el convenio tiene la regla `TODOS / MERIENDA`.
- **COMIDA:** `cantidad = parte entera de horas extras / 3`, sólo si el convenio tiene la regla `TODOS / COMIDA`.
- Ambos conceptos se calculan simultáneamente sólo sobre registros de horas extras pendientes de la misma jornada.
- Si cambian las horas pendientes, se actualizan o eliminan los registros automáticos de COMIDA y MERIENDA de esa jornada.
- Un día trabajado o reintegro sin horas extras no genera COMIDA ni MERIENDA.

## CISPREN

| Tipo de día/carga | Tipo resultante | Nocturnidad | Reintegro | Observación vigente |
|---|---:|---|---|---|
| HABIL | 100 | 21:00 a 06:00 | No | — |
| FERIADO | 100 | 21:00 a 06:00 | Medio o completo | Permite elegir 0,5 o 1 reintegro si se trabajaron al menos 4 horas |
| FRANCO | 100 | 21:00 a 06:00 | Medio o completo | Permite elegir 0,5 o 1 reintegro si se trabajaron al menos 4 horas |
| EXTERIOR PRENSA | Cantidad manual | — | No | Sólo admite cantidad 3 o 6 |

## SAL

| Tipo de día | Tipo resultante | Nocturnidad | Reintegro | Observación vigente |
|---|---:|---|---|---|
| HABIL | 50 | 21:00 a 06:00 | No | — |
| FERIADO | 100 | 21:00 a 06:00 | Sí | Permite solicitar reintegro del día completo |
| FRANCO | 100 | 21:00 a 06:00 | Sí | Permite solicitar reintegro del día completo |

## SAT

| Tipo de día/carga | Tipo resultante | Nocturnidad | Reintegro | Observación vigente |
|---|---:|---|---|---|
| HABIL (se muestra “HÁBIL”) | 50 | 21:00 a 06:00 | No | Horas extras de lunes a viernes |
| FERIADO | 100 | 21:00 a 06:00 | Sí | Días feriados; permite solicitar reintegro |
| FRANCO | 100 | 21:00 a 06:00 | Sí | Sábados después de las 13:00, domingos o francos trabajados |
| DOMINGO | 1 por día | 21:00 a 06:00 | No | Exclusivo de SAT y de fechas domingo |
| COMIDA | Automática | — | No | Una cada 3 horas extras |
| MERIENDA | Automática | — | No | Una cada 2 horas extras |
| EXTERIOR COMUN | Cantidad manual | — | No | Tareas fuera de la planta transmisora |
| FRACCIONAMIENTO | Cantidad manual | — | No | Jornada con horario dividido |
| HS ARTICULO | Cálculo automático | — | No | Horas faltantes para completar 12 horas de descanso entre jornadas |
| METROS TORRE | Cantidad manual | — | No | Metros subidos para realizar una tarea |

Reglas especiales de domingo SAT:

- En una fecha domingo se genera el concepto **DOMINGO** si existe su regla activa.
- Si se informa una jornada iniciada en domingo, se registra DOMINGO con su horario y nocturnidad, en lugar de franco o feriado trabajado.
- DOMINGO no permite reintegro.
- Si una jornada cruza hacia un domingo, se agrega también el concepto DOMINGO para esa fecha.
- No puede existir más de un registro DOMINGO pendiente o aprobado para la misma persona y fecha.

## FC

| Tipo de día | Tipo resultante | Nocturnidad | Reintegro | Observación vigente |
|---|---:|---|---|---|
| FERIADO | DIA TRABAJADO | No | No | Informa 1 feriado trabajado, sin mínimo de horas |
| FRANCO | DIA TRABAJADO | No | No | Informa 1 franco trabajado, sin mínimo de horas |

FC sólo permite informar un franco o feriado trabajado. No permite horas extras, reintegros, otras cargas, conceptos asociados, COMIDA ni MERIENDA. Si la jornada cruza medianoche conserva el horario completo sin exigir una regla HABIL ni calcular nocturnidad.

## MONOTRIBUTISTA

| Tipo de día | Tipo resultante | Nocturnidad | Reintegro | Observación vigente |
|---|---:|---|---|---|
| HABIL | 50 | Sin configurar | No | Horas extras de día hábil |
| FERIADO | 100 | Sin configurar | No | Horas extras asociadas a un feriado trabajado |
| FRANCO | 100 | Sin configurar | No | Horas extras asociadas a un franco trabajado |

MONOTRIBUTISTA registra 1 franco o feriado trabajado cualquiera sea la duración. Puede agregar horas extras dentro de esa carga, que se clasifican automáticamente según el tipo de día. No permite reintegro y no tiene configuradas COMIDA ni MERIENDA.

## Otras cargas y conceptos excepcionales

- Las otras cargas comunes sólo están disponibles si existe una regla `TODOS` para el convenio del usuario.
- COMIDA, MERIENDA y DOMINGO no se pueden cargar manualmente desde “Otras cargas”.
- Las cantidades manuales deben ser mayores que cero y múltiplos de `0,5`.
- EXTERIOR PRENSA es la excepción: sólo admite `3` o `6`.
- Una carga adicional puede agregarse junto con horas extras o con un franco/feriado trabajado. Se guarda como registro independiente para la misma fecha y exige justificación propia.
- HS ARTICULO se calcula únicamente desde una carga de horas extras, informando el fin de la jornada anterior y el inicio de la siguiente. No está disponible en Otras cargas ni dentro de Franco o feriado trabajado.
- Los conceptos excepcionales no dependen del convenio: deben estar activos y asignados al usuario para la fecha cargada. También usan cantidades en pasos de `0,5`.

## Límites de fecha según contratación

- **Nómina:** sólo puede cargar dentro del período vigente del día 16 de un mes al día 15 del siguiente.
- **Monotributo y Consultora:** sólo pueden cargar fechas del mes calendario vigente.
- Otros tipos de contratación no tienen un límite específico implementado.

## Observaciones técnicas detectadas

1. Los nombres y parámetros de cada convenio no están fijados en el código: pueden modificarse desde Configuración. Este documento refleja la combinación del comportamiento programado y los parámetros vigentes al momento del relevamiento.
