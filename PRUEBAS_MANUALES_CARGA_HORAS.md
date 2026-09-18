# Pruebas manuales de carga de horas

Plan concreto de validación funcional para RRHH. Contiene **20 casos**, distribuidos entre los convenios CISPREN, SAL, SAT y FC.

## Preparación

Antes de comenzar:

- Crear o elegir un usuario activo de cada convenio: CISPREN, SAL, SAT y FC.
- Usar usuarios con perfil **USUARIO** y tipo de contratación que permita cargar las fechas elegidas.
  - Nómina: usar una fecha dentro del período vigente del 16 al 15.
  - Monotributo y Consultora: usar una fecha del mes calendario vigente.
- Confirmar que todos tengan las reglas indicadas en el documento de reglas vigente.
- Crear dentro del período permitido:
  - un feriado marcado **Devuelve = Sí**;
  - otro feriado marcado **Devuelve = No**;
  - un domingo para las pruebas SAT.
- Escribir una observación en todos los casos. Si se omite, el sistema debe impedir continuar.
- Para comprobar conceptos excepcionales, crear uno de prueba, por ejemplo **PLUS MÓVIL**, y asignarlo sólo a uno de los usuarios durante una vigencia que incluya la fecha de prueba.
- Usar fechas sin cargas previas, salvo cuando el caso indique lo contrario.

> En los ejemplos, “franco” significa una fecha que no figura como feriado y que se informa desde la opción **Franco o feriado trabajado**. El sistema no deduce automáticamente que un sábado sea franco.

## CISPREN

### 1. Horas extras hábiles comunes

- [ ] Elegir **Horas extras**, un día hábil, de 18:00 a 19:30.
- [ ] Agregar una observación, procesar y confirmar.

**Resultado esperado:** se genera una carga pendiente de **1,5 horas al 100%**. No genera reintegro, comida ni merienda.

### 2. Jornada hábil nocturna que cruza medianoche

- [ ] Cargar un día hábil de 23:00 a 02:00 del día siguiente.
- [ ] Procesar y confirmar.

**Resultado esperado:** la jornada se divide en las fechas correspondientes, totaliza **3 horas extra al 100%** y calcula **3 horas nocturnas**. No genera comida ni merienda.

### 3. Franco menor a cuatro horas

- [ ] Elegir **Franco o feriado trabajado** en una fecha no feriada.
- [ ] Informar 10:00 a 13:30, sin horas extras adicionales.

**Resultado esperado:** se generan **3,5 horas al 100%**. No se genera el concepto de día franco trabajado y no se ofrece ni guarda reintegro.

### 4. Feriado con medio reintegro y horas extra aparte

- [ ] Usar el feriado con **Devuelve = Sí**.
- [ ] Informar 09:00 a 17:00.
- [ ] Seleccionar **Medio reintegro** y agregar **1,5 horas extras**.

**Resultado esperado:** la vista previa muestra **1 feriado trabajado**, **0,5 reintegro** y **1,5 horas al 100%** en registros separados. No genera comida ni merienda.

### 5. EXTERIOR PRENSA: cantidades válidas e inválida

- [ ] En **Otras cargas**, seleccionar EXTERIOR PRENSA y verificar que permita guardar cantidad **3**.
- [ ] Repetir en otra fecha o carga con cantidad **6**.
- [ ] Intentar enviar cantidad **4**, incluso manipulando el campo desde el navegador si la interfaz no la ofrece.

**Resultado esperado:** 3 y 6 se guardan como registros separados de EXTERIOR PRENSA. La cantidad 4 es rechazada por el servidor.

## SAL

### 6. Horas extras hábiles comunes

- [ ] Cargar un día hábil de 18:00 a 20:30.

**Resultado esperado:** se genera una carga pendiente de **2,5 horas al 50%**, sin comida, merienda ni reintegro.

### 7. Franco de exactamente cuatro horas

- [ ] Elegir **Franco o feriado trabajado** en una fecha no feriada.
- [ ] Informar 08:00 a 12:00, sin horas extras adicionales y sin solicitar reintegro.

**Resultado esperado:** por alcanzar la cuarta hora se genera **1 franco trabajado**, no 4 horas al 100%. No genera comida ni merienda.

### 8. Franco largo con reintegro y extras

- [ ] Informar un franco de 10:00 a 18:00.
- [ ] Solicitar reintegro y declarar **2 horas extras**.

**Resultado esperado:** se generan por separado **1 franco trabajado**, **1 reintegro completo** y **2 horas al 100%**. Las horas extra corresponden al tramo final de la jornada. No se generan comida ni merienda porque SAL no tiene esos conceptos configurados.

### 9. Feriado que no devuelve

- [ ] Usar el feriado marcado **Devuelve = No** e informar una jornada de al menos 4 horas.
- [ ] Verificar la opción de reintegro antes de confirmar.

**Resultado esperado:** la opción de solicitar reintegro está deshabilitada o no aparece. Se guarda **1 feriado trabajado**, pero ningún reintegro.

### 10. Concepto excepcional asignado y no asignado

- [ ] Con el usuario SAL que tiene asignado **PLUS MÓVIL**, cargar 2,5 unidades y justificarlo.
- [ ] Ingresar luego con otro usuario SAL sin asignación y revisar sus opciones.

**Resultado esperado:** el primer usuario ve el nombre y la descripción, y guarda **2,5 PLUS MÓVIL** como registro independiente. El segundo usuario no puede verlo ni cargarlo. En seguimiento, autorización y exportación debe figurar **PLUS MÓVIL**, no “Excepcional”.

## SAT

### 11. Horas hábiles con nocturnidad y cálculos automáticos

- [ ] Cargar un día hábil de 18:00 a 22:00.

**Resultado esperado:** se generan **4 horas al 50%**, **1 hora nocturna**, **2 meriendas** y **1 comida**. Todos los conceptos aparecen como registros separados.

### 12. Actualización de comida y merienda al editar

- [ ] Tomar la carga pendiente del caso 11 y cambiarla de 4 a 6 horas extras en total.
- [ ] Revisar todos los registros de esa jornada.

**Resultado esperado:** la carga queda en **6 horas extra**, y los automáticos se actualizan a **3 meriendas** y **2 comidas** sin duplicar los registros anteriores. La edición sólo es posible mientras todo siga pendiente.

### 13. Jornada que pasa de sábado a domingo

- [ ] Desde **Franco o feriado trabajado**, informar sábado 23:30 a domingo 07:00.
- [ ] No declarar horas extras adicionales.

**Resultado esperado:** los tramos conservan sus fechas reales, se calcula la nocturnidad de 23:30 a 06:00 y se genera **1 DOMINGO** para el domingo. No se genera además un franco para ese domingo y no se permite reintegro por DOMINGO.

### 14. Domingo duplicado

- [ ] Confirmar una carga DOMINGO para el usuario y fecha del caso 13.
- [ ] Intentar generar otro DOMINGO para la misma persona y fecha mientras el primero está pendiente.

**Resultado esperado:** el segundo registro DOMINGO es rechazado. La misma validación debe mantenerse si el primero ya fue autorizado.

### 15. Otras cargas SAT y pasos de cantidad

- [ ] Agregar en una carga de horas extras **FRACCIONAMIENTO = 1** con su justificación.
- [ ] Agregar también **METROS TORRE = 8,5** con una justificación distinta.
- [ ] Intentar una cantidad con décimas distinta de 0,5, por ejemplo 8,2.

**Resultado esperado:** FRACCIONAMIENTO y METROS TORRE se guardan como registros independientes, con sus nombres, cantidades, fecha y observación. La cantidad 8,2 no debe admitirse; sólo se aceptan pasos de 0,5.

## FC

### 16. Horas extras hábiles

- [ ] Cargar un día hábil de 18:00 a 20:00.

**Resultado esperado:** se generan **2 horas al 50%**. No se calculan horas nocturnas, comida ni merienda.

### 17. Franco menor a cuatro horas

- [ ] Informar un franco de 08:00 a 11:00.

**Resultado esperado:** se generan **3 horas al 100%**, sin día franco trabajado y sin reintegro.

### 18. Feriado desde la cuarta hora sin reintegro

- [ ] En un feriado con **Devuelve = Sí**, informar 08:00 a 12:00.
- [ ] Revisar las opciones disponibles.

**Resultado esperado:** se genera **1 feriado trabajado**. Aunque el feriado devuelva, FC no muestra ni permite solicitar reintegro.

### 19. Jornada FC nocturna

- [ ] Cargar horas de un día hábil de 22:00 a 01:00.

**Resultado esperado:** se registran **3 horas al 50%**, divididas por fecha cuando corresponda, pero **sin horas nocturnas**, porque FC no tiene franja nocturna configurada.

### 20. Autorización, bloqueo de edición y exportación

- [ ] Autorizar como jefe una carga FC pendiente.
- [ ] Intentar editarla o eliminarla desde el usuario que la creó.
- [ ] Consultarla en Seguimiento y exportar el período a XLSX.

**Resultado esperado:** el usuario ya no puede editar ni eliminar la carga autorizada. Seguimiento la muestra agrupada bajo la persona con estado **Autorizada**. El Excel resume legajo, nombre y apellido, concepto y cantidad; la segunda hoja contiene legajo, nombre, concepto, cantidad, fecha y observación.

## HS ARTICULO — calculador de descanso entre jornadas

### 21. Cálculo desde una carga de horas extras

- [ ] Como usuario SAT, cargar horas extras el viernes de 18:00 a 23:00.
- [ ] Abrir **¿Querés calcular HS ARTICULO (descanso entre jornadas)?**.
- [ ] Verificar que el fin de jornada se complete con viernes a las 23:00.
- [ ] Informar como inicio de la jornada siguiente el sábado a las 08:00.

**Resultado esperado:** el sistema calcula un descanso real de **9 horas** sobre las **12 horas** requeridas y agrega a la vista previa un registro separado de **3 HS ARTICULO**, fechado el sábado. La cantidad no puede modificarse manualmente.

**Observación automática esperada:** `Fin de jornada anterior: [viernes] 23:00. Inicio de jornada siguiente: [sábado] 08:00. Descanso real: 9 horas. Descanso requerido: 12 horas. HS ARTICULO: 3 horas.`

## Control general de resultados

Completar al ejecutar cada caso:

| Caso | Fecha probada | Resultado real | Estado | Observaciones / evidencia |
|---:|---|---|---|---|
| 1 |  |  | Pendiente |  |
| 2 |  |  | Pendiente |  |
| 3 |  |  | Pendiente |  |
| 4 |  |  | Pendiente |  |
| 5 |  |  | Pendiente |  |
| 6 |  |  | Pendiente |  |
| 7 |  |  | Pendiente |  |
| 8 |  |  | Pendiente |  |
| 9 |  |  | Pendiente |  |
| 10 |  |  | Pendiente |  |
| 11 |  |  | Pendiente |  |
| 12 |  |  | Pendiente |  |
| 13 |  |  | Pendiente |  |
| 14 |  |  | Pendiente |  |
| 15 |  |  | Pendiente |  |
| 16 |  |  | Pendiente |  |
| 17 |  |  | Pendiente |  |
| 18 |  |  | Pendiente |  |
| 19 |  |  | Pendiente |  |
| 20 |  |  | Pendiente |  |
| 21 |  |  | Pendiente |  |

Estados sugeridos: **OK**, **Falló** o **No se pudo probar**.
