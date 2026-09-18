# Reglas de carga para validación de RRHH

Resumen del funcionamiento actual del sistema al **16/09/2026**.

## Reglas generales

- Cada usuario carga únicamente sus propias horas.
- Toda carga debe tener una observación.
- Los horarios se ingresan cada 30 minutos.
- Si una jornada pasa la medianoche, el sistema separa los tramos por fecha, pero los considera parte de una misma jornada para calcular comida y merienda.
- Una fecha registrada en el calendario de feriados se considera feriado. Los sábados y domingos no se consideran francos automáticamente, salvo el tratamiento especial de domingo para SAT.
- Las cargas quedan pendientes hasta que un jefe o administrador las autorice o rechace.
- Sólo pueden editarse o eliminarse cargas pendientes.

## Comida y merienda

Se calculan únicamente sobre las horas extras de una misma jornada:

- **Merienda:** una cada 2 horas extras, si el convenio tiene configurado el concepto MERIENDA.
- **Comida:** una cada 3 horas extras, si el convenio tiene configurado el concepto COMIDA.
- Se calculan ambas al mismo tiempo.
- Un franco o feriado trabajado sin horas extras no genera comida ni merienda.

Ejemplo: 6 horas extras generan 3 meriendas y 2 comidas.

Actualmente COMIDA y MERIENDA sólo están configuradas para SAT. Los demás convenios no las calculan ni generan errores. Si RRHH configura uno de estos conceptos para otro convenio, su cálculo se activa automáticamente.

## Convenio CISPREN

### Día hábil

- Las horas extras se cargan al **100%**.
- La franja nocturna es de **21:00 a 06:00**.
- No permite reintegro.

Ejemplo: lunes de 18:00 a 19:30 → 1,5 horas al 100%.

### Franco trabajado

- Menos de 4 horas: se pagan solamente las horas efectivamente trabajadas al 100%.
- Desde la cuarta hora: se registra 1 franco trabajado.
- Desde las 4 horas permite elegir: no solicitar, medio reintegro (`0,5`) o reintegro completo (`1`).
- Si se informan horas extras adicionales, se guardan aparte al 100%.

Ejemplos:

- Franco de 10:00 a 11:30 → 1,5 horas al 100%; no genera día trabajado ni reintegro.
- Franco de 10:00 a 14:00 → 1 franco trabajado; puede solicitar medio reintegro o reintegro completo.

### Feriado trabajado

- Menos de 4 horas: se pagan solamente las horas efectivamente trabajadas al 100%.
- Desde la cuarta hora: se registra 1 feriado trabajado.
- Las horas extras adicionales se cargan al 100%.
- Permite elegir medio reintegro o reintegro completo si el feriado está marcado como “Devuelve”.
- Si el feriado está marcado como “No devuelve”, no permite reintegro.

### Otras cargas

- **EXTERIOR PRENSA:** sólo admite cantidad 3 o 6.

> CISPREN no tiene configuradas COMIDA y MERIENDA; por lo tanto, no se calculan para este convenio.

## Convenio SAL

### Día hábil

- Las horas extras se cargan al **50%**.
- La franja nocturna es de **21:00 a 06:00**.
- No permite reintegro.

Ejemplo: miércoles de 18:00 a 19:30 → 1,5 horas al 50%.

### Franco trabajado

- Menos de 4 horas: se pagan solamente las horas efectivamente trabajadas al 100%.
- Desde la cuarta hora: se registra 1 franco trabajado.
- Permite solicitar reintegro.
- Las horas extras adicionales se guardan aparte al 100%.

### Feriado trabajado

- Menos de 4 horas: se pagan solamente las horas efectivamente trabajadas al 100%.
- Desde la cuarta hora: se registra 1 feriado trabajado.
- Las horas extras adicionales se cargan al 100%.
- Permite reintegro únicamente si el feriado está marcado como “Devuelve”.

Ejemplo: feriado de 09:00 a 17:00 y 2 horas extras informadas → 1 feriado trabajado y 2 horas al 100%.

### Otras cargas

No hay otras cargas configuradas actualmente para SAL.

> SAL no tiene configuradas COMIDA y MERIENDA; por lo tanto, no se calculan para este convenio.

## Convenio SAT

### Día hábil

- Las horas extras se cargan al **50%**.
- La franja nocturna es de **21:00 a 06:00**.
- No permite reintegro.

Ejemplo: martes de 18:00 a 22:00 → 4 horas al 50% y 1 hora nocturna.

### Franco trabajado

- Menos de 4 horas: se pagan solamente las horas efectivamente trabajadas al 100%.
- Desde la cuarta hora: se registra 1 franco trabajado.
- Permite solicitar reintegro.
- Las horas extras adicionales se guardan aparte al 100%.

Ejemplos:

- Franco de 22:00 a 01:00 → 3 horas al 100% y 3 horas nocturnas; no genera día trabajado ni reintegro.
- Franco de 10:00 a 18:00, indicando 2 horas extras → 1 franco trabajado y 2 horas al 100% correspondientes al tramo de 16:00 a 18:00.

### Feriado trabajado

- Menos de 4 horas: se pagan solamente las horas efectivamente trabajadas al 100%.
- Desde la cuarta hora: se registra 1 feriado trabajado.
- Las horas extras adicionales se cargan al 100%.
- Permite reintegro únicamente si el feriado está marcado como “Devuelve”.
- El feriado pagado sin horas extras no genera comida ni merienda.

### Domingo

- En domingo se genera el concepto **DOMINGO**, con cantidad 1.
- Puede guardar horario y calcular nocturnidad.
- No se registra también como franco trabajado.
- No permite reintegro.
- No puede haber dos registros DOMINGO pendientes o autorizados para la misma persona y fecha.
- Si una jornada cruza hacia un domingo, se agrega el concepto DOMINGO para esa fecha.

Ejemplo: sábado de 23:30 a domingo 07:00 → se divide por fecha, se calcula la nocturnidad y se agrega 1 DOMINGO para el domingo.

### Otras cargas

- **EXTERIOR COMUN:** tareas realizadas fuera de la planta transmisora.
- **FRACCIONAMIENTO:** jornada con horario dividido.
- **HS ARTICULO:** horas faltantes para completar 12 horas de descanso entre jornadas; se calcula con el fin de la jornada anterior y el inicio de la siguiente.
- **METROS TORRE:** cantidad de metros subidos para realizar una tarea.
- Las cantidades se ingresan de a 0,5.
- Cada concepto requiere una justificación propia y se guarda como registro separado.

## Convenio FC

- **Día hábil:** las horas extras se cargan al 50%.
- **Franco:** menos de 4 horas se pagan como horas reales al 100%; desde la cuarta hora se registra 1 franco trabajado.
- **Feriado:** menos de 4 horas se pagan como horas reales al 100%; desde la cuarta hora se registra 1 feriado trabajado.
- FC nunca permite solicitar reintegro. La opción no se muestra en la carga.
- No tiene franja nocturna configurada.
- No tiene configuradas COMIDA ni MERIENDA, por lo que esos conceptos no se calculan.

Ejemplos:

- Día hábil de 18:00 a 20:00 → 2 horas al 50%.
- Franco de 08:00 a 11:00 → 3 horas al 100%, sin día trabajado ni reintegro.
- Feriado de 08:00 a 12:00 → 1 feriado trabajado, sin reintegro.

Actualmente FC no tiene una regla de día hábil al 100%. Si también debe permitir esa carga, se necesita incorporar la selección entre 50% y 100% junto con el parámetro correspondiente.

## Conceptos excepcionales

- Pueden utilizarse con cualquier convenio.
- RRHH o el jefe debe asignar previamente el concepto a la persona y definir su vigencia.
- El usuario sólo ve los conceptos que tiene activos para la fecha elegida.
- La cantidad se carga de a l o 0,5 y exige justificación.
- Se guarda como registro separado con el nombre real del concepto.

## Períodos permitidos para cargar

Esta regla depende del tipo de contratación, no del convenio:

- **Nómina:** período vigente del día 16 de un mes al día 15 del siguiente.
- **Monotributo y Consultora:** mes calendario vigente.

## Puntos concretos que RRHH debería validar

1. Si CISPREN realmente debe pagar las horas de día hábil al 100%.
2. Si la regla “franco o feriado trabajado desde la cuarta hora” corresponde igual para CISPREN, SAL, SAT y FC.
3. Si comida y merienda deben calcularse simultáneamente cada 2 y 3 horas, respectivamente.
4. Si CISPREN, SAL y FC también necesitan reglas de comida y merienda.
5. Si los sábados después de las 13:00 para SAT deben detectarse automáticamente como franco. Hoy no se detectan automáticamente.
6. Si FC también debe permitir elegir horas hábiles al 100%, además de las actuales al 50%.
7. Si un domingo SAT que también es feriado debe continuar tratándose sólo como DOMINGO y sin reintegro.
