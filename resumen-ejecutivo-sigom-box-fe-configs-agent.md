# NY_SCH — Configuración SIGOM de BOX FE · Resumen ejecutivo

El `sigom-box-fe-configs-agent` es responsable de la mitad **BOX FE** del paso CONFIGS del alta de sucursal; la configuración **BOX ACC** pertenece a otro agente. El agente es agnóstico de sucursal: la sucursal es un dato de entrada de cada ejecución, nunca está fijada en el charter.

Su objetivo, para cualquier sucursal, es producir el **SQL completo, ordenado y ejecutable** que crea todos los objetos de configuración SIGOM de BOX FE para esa sucursal. Cada valor debe estar trazado a evidencia, revisado por un SME nombrado, y ser ejecutable por entorno. El entregable es **un fichero que se ejecuta, no un análisis**: la corrección se mide porque la sucursal se comporta como su equivalente en GBO.

El agente **nunca tiene permisos de escritura sobre BOX**. Un humano ejecuta el SQL.

**Ejecución NY_SCH:** destino Tier 2 PRE, minado sobre GBO Tier 2, Tier 1 como `REFERENCE_ENV` para el diff de esquema, salida en `runs/NY_SCH/tier2-pre/`. `BRANCH_PK` debe resolverse con Q-G1 — el valor Tier 1 `20007.4` es una observación, no una entrada válida de Tier 2.

## Contrato de entrada y salida

**Entradas:** `BRANCH_CODE`, `TARGET_ENV`, `GBO_SOURCE`, `PRODUCT_BOOK_SCOPE`, `DB_ACCESS_MODE`, `RUN_FOLDER` y, para la puerta 0e, `REFERENCE_ENV`. Una entrada ausente es un arranque bloqueado. `PRODUCT_BOOK_SCOPE` debe venir de un SME nombrado **por escrito** y jamás inferirse.

**Salidas**, todas en la carpeta de ejecución: `00-inputs.md`, `01-evidence/`, `02-findings.md`, `03-sql/`, `04-provisioning/`, `99-open-items.md`.

**Se considera terminado** cuando todo objeto del walk tiene estado y evidencia, el walk se ejecutó en orden, ningún valor fue inventado, la firma del SME precedió a la generación de SQL, y el SQL ejecuta y verifica limpio. **Una ejecución que se detiene reportando los huecos con honestidad es un resultado correcto.**

## Etapa A — Puertas

No se escribe SQL de configuración durante la Etapa A. El fallo de una puerta es un estado final reportable: una ejecución parcialmente validada está **bloqueada**, no es algo que rodear.

| Paso | Puerta / acción | Salida | Bloquea |
|---|---|---|---|
| A0 | `00-inputs.md` — contrato de entrada cumplimentado antes de cualquier consulta | Entradas registradas | Sí |
| A1 | **0a / Q-G1** — resolver la sucursal en GBO: `BRANCH_PK`, entidad, divisa, calendario, `FK_LOCALGROUP` | Perfil de sucursal y `BRANCH_PK` | Sí — proponer handoff a GBO y esperar a `GBO-created` |
| A2 | **0b / Q-G2** — recorrer el árbol de configuración GBO tres niveles y registrar a qué resuelve `FK_MISCONFIG` | Nota de completitud del árbol | Sí |
| A3 | **0c** — obtener alcance de producto y book de un SME nombrado, por escrito; es una entrada, no una consulta | Declaración de alcance atribuida | Sí |
| A4 | **0d / Q-G3** — establecer el mecanismo de generación de PK **para cada tabla destino** | Mecanismo de PK por tabla | Sí — ningún `INSERT` sin esto |
| A5 | **0e / Q-G4** — comparar el esquema `BOX_FE` destino con el entorno de referencia, tabla por tabla | Lista de huecos de aprovisionamiento | Sí — ver Etapa B |

En esta ejecución se **espera** que 0d y 0e fallen sobre Tier 2 PRE. Que A4 no devuelva secuencia, trigger ni default es en sí un resultado significativo: apunta a asignación por parte de SIGOM, lo que significa que un `INSERT` en crudo **no es seguro**.

> **Ampliación de la puerta 0d (añadido a la versión de Devin).** Q-G3 contempla cuatro respuestas —secuencia, trigger, default de columna, asignación SIGOM—. El corpus documenta ya **dos mecanismos más, ambos evidenciados**: exportación/importación con *dynamic pk* (runbook de alta de Book) y **PK literales escritos a mano** en SQL versionado (`T_BOX_CROSS_REF_S`, repositorio `cib-box-cntdblite`). Una puerta que enumera cuatro respuestas puede darse por superada de forma incorrecta.
>
> Además, 0d debe responder una segunda pregunta que hoy no formula: **qué auth-code llevan las filas de NY_SCH**. El sufijo decimal del PK *es* el auth-code que muestra SIGOM en su barra de estado — `.21` = Madrid (confirmado), `.65` = BOX-DEV, `.4` = datos globales. Sin ese dato, ni siquiera un mecanismo de generación resuelto permite construir un literal correcto, y una fila escrita con el auth-code equivocado resulta invisible para los guardas de borrado del tipo `trunc(PK) = sign(PK)*(abs(PK)-.65)`.

## Etapa B — Aprovisionamiento

Sólo se ejecuta si Q-G4 encuentra huecos de esquema. El agente enumera cada objeto ausente y la consulta que lo prueba; localiza el DDL autoritativo de cada objeto en `cib-boxfin-dbboxfe` y **cita la ruta origen — nunca redacta DDL**; ordena los objetos por dependencia; determina si se trata de un entorno incompleto o de un módulo no desplegado; entrega la petición de aprovisionamiento al DBA/release owner nombrado y **bloquea**; y reejecuta A5 / Q-G4 tras el aprovisionamiento.

Para NY_SCH, el kickoff indica que GBO Tier 2 está vivo mientras BOX FE podría no estar desplegado en Tier 2. Esa distinción debe resolverse pronto: **un módulo no desplegado es un prerrequisito de Fase 0 del orquestador, no una tarea de configuración.** El agente no ejecuta DDL ni lo mezcla con el script de configuración.

## Etapa C — Minado (sólo lectura)

El agente trabaja **un objeto cada vez, en el orden del walk**. Para cada objeto lee el lado GBO (`Q-nn`, contra el objeto `T_PGT_*` correspondiente), lee el lado BOX (`Q-nnb`), clasifica el resultado, identifica el origen de cada valor ausente y registra la regla y procedencia de todo valor `DERIVED`.

| # | Objeto de configuración | Destino BOX FE | Origen GBO | Consulta | Bloqueado por |
|---|---|---|---|---|---|
| 1 | Asociación de configuración FE — **lectura**: ¿reutilizar o nueva? | `T_BOX_ENGCONF_X` | — | Q-01 | 0a, 0b |
| 2 | Cabecera MIS Generic | `T_BOX_ENGCONF_S` | `T_PGT_ENGCONF_S` | Q-02 | 1 |
| 3 | Cabecera Fixing Curve | `T_BOX_ENGFCURVE_S` | `T_PGT_ENGFCURVE_S` | Q-03 | 2 |
| 4 | Enlace curva → referencia de cotización | `T_BOX_ENGLKFC_X` | `T_PGT_ENGLKFC_X` | Q-04 | 3 |
| 5 | Fila de asociación de sucursal — **escritura** | `T_BOX_ENGCONF_X` | — (lado GBO es `T_PGT_BRANCH_S`) | — | 2, 3, 4 |
| 6 | Accrual defaults | `T_BOX_ENGACCRCONF_S` | `T_PGT_ENGACCRCONF_S` | Q-05 | 0c, 5 |
| 7 | Accrual Exceptions | `T_BOX_CONFIG_ACCRUAL_S` | `T_PGT_CONFIG_ACCRUAL_S` | Q-06 | 6 |
| 8 | Fixing Exceptions | `T_BOX_FIXING_BY_INSTR_S` + `V_BOX_PROC_INSTR_S` | `T_PGT_FIXING_BY_INSTR_S` + `V_PGT_PROC_INSTR_S` | Q-07 | 3, 6 |
| 9 | Yield Curve | `T_BOX_ENGZCCONF_S` | `T_PGT_ENGZCCONF_S` | Q-08 | 2 |
| 10 | Currency Basis | `T_BOX_ENGCURRENCYBASIS_S` | `T_PGT_ENGCURRENCYBASIS_S` | Q-09 | 2 |
| 11 | Book — registro de ejecución de batch | `T_BOX_CONF_BY_BOOK_S` | **ninguno — sin análogo GBO, confirmado** | Q-10 | 0c, 5, 6 |
| 12 | Derivado — **verificar, nunca INSERT** | `T_BOX_FIXING_ASSIGNMENT_S`, `T_BOX_BRPROCCAL_S` | — | Q-11 | 4, 11 |
| 13 | No scopeado por sucursal — descartar con evidencia | `T_BOX_ENGDAYS_MATURED_S`, `T_BOX_ENGSETUP_S` | — | Q-12 | — |

El orden del walk **es** el orden del script, porque sigue dependencias de FK, **no el orden de pestañas de SIGOM**. Las cabeceras (2–5) preceden a los hijos (6–11), y Book (11) va al final porque exige la asociación, el alcance de instrumentos y el alcance de books. El paso 1 es la bifurcación: determina si existe una asociación de configuración FE y, por tanto, si la ejecución adapta una configuración existente o construye una nueva.

> **Nota sobre el origen GBO (añadido).** La columna dice `DEVENG`, pero el lado GBO abarca más de un esquema: Q-G1 y Q-10 leen `PGT_STC.T_PGT_BRANCH_S`, `PGT_SYS.T_PGT_SUB_PRODUCT_S` y `PGT_SYS.PGT_DOMAINS`. Conviene no buscar `T_PGT_BRANCH_S` dentro de `DEVENG`.

En modo asistido, cada entrega contiene ID de consulta, propósito, base de datos destino, parámetros resueltos, SQL ejecutable, ruta exacta del CSV de salida y número de filas esperado; después el agente **se detiene y espera**. Las peticiones se hacen en lotes por dependencia, no todas a la vez. Un CSV que llega debe coincidir con la forma esperada: un desajuste es una petición de reejecución, **no datos que interpretar creativamente**.

Un resultado de cero filas **no es ausencia** cuando la consulta puede estar mal. Verificar el join antes de registrar `CONFIRMED_ABSENT`, especialmente en Q-08 y Q-09: el catálogo contiene joins asumidos, y un join incorrecto hace indistinguible una ausencia real de un defecto de consulta.

**Comprobación temprana específica de NY_SCH:** ejecutar `SELECT * FROM PGT_STC.T_PGT_BRANCH_S`. Si valores con forma de producto como `BOX CCS`, `BOX FX` o `BOX IRS` son reales y no una convención de desarrollo, **detenerse**: cambia la forma del walk.

El paso 11 es deliberadamente distinto: `T_BOX_CONF_BY_BOOK_S` no tiene fila GBO. Q-10 comprueba el hecho del lado BOX mediante el join canónico sucursal × instrumento Sub-Product × etiqueta de book en `PGT_DOMAINS`. La evidencia requerida es la enumeración de books Data-Lake/Murex de la sucursal más una decisión de SME nombrado sobre qué books necesitan registro de batch FE. Las filas existentes de Madrid/Londres son **referencia estructural, nunca valores que copiar**.

> **Trampa de la Fixing Curve, paso 3 (añadido).** `Fixing Curve` aparece en SIGOM bajo `Control > Configuration` **y** bajo `Control > Historical Data`. Ya está resuelto cuál es cuál: **Configuration es lo que el batch lee; Historical Data es lo que el batch escribe.** Se mina *Configuration*. Un *Historical Data* vacío en una sucursal nueva significa que el batch no ha corrido, no que falte configuración.

## Etapa D — Revisión de findings (puerta humana)

El agente compone `02-findings.md` con una fila con estado por cada objeto del walk, citando la evidencia correspondiente en `01-evidence/`. Las filas `DERIVED` se separan para firma individual y **no pueden ir dentro de una aprobación en bloque**. Los findings se dirigen al SME nombrado en A3, y el agente bloquea hasta que cada fila esté confirmada, rechazada o explícitamente diferida.

La traza de evidencia y la tabla de findings son entregables valiosos **aunque no pueda generarse SQL**. Una lista de huecos con evidencia es útil; unos `INSERT` sin esa traza son peores que nada.

## Etapa E — Generación de SQL

Arranca sólo con findings firmados y sólo tras superar 0d y 0e. El motor `generate-fe-config-sql` debe: generar sentencias en orden de dependencia FK (2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11); anotar cada sentencia con su fila GBO origen, la fila de findings que la autoriza y cualquier regla `DERIVED`; emparejar cada sentencia con un `SELECT` de verificación y un `DELETE` de rollback; declarar qué pantalla y acción de SIGOM reproduce el conjunto; limitar el fichero generado a **PRE**, generando PRO por separado sólo tras verificar PRE; y no emitir nada para el paso 1 (lectura), el 12 (derivado) ni el 13 (no scopeado).

El agente **no debe generar un `INSERT` en crudo** si Q-G3 establece asignación por parte de SIGOM o una vía de exportación/importación. Todo literal debe proceder de evidencia, de un SME nombrado, de una constante de plataforma documentada, o estar etiquetado `DERIVED` con su regla y firma independiente.

## Etapa F — Aplicación y verificación

Un humano ejecuta el script de PRE; el agente nunca tiene escritura sobre BOX. El humano ejecuta los `SELECT` de verificación emparejados y se detiene ante cualquier resultado inesperado. Cuando sea posible, se compara la fila creada con la fila equivalente creada por SIGOM en una sucursal existente, porque **un `INSERT` que ejecuta limpio no prueba que reproduzca la validación, las columnas de auditoría ni las escrituras multi-tabla de SIGOM**. La ejecución reporta qué se aplicó y verificó y qué no. Sólo tras verificar PRE se genera y entrega el script de PRO.

## Bloqueantes actuales

1. **0c** — el alcance de producto y book sigue necesitando una declaración escrita y conforme de un SME nombrado.
2. **0d** — la generación de PK está sin resolver para todas las tablas. **Es el mayor bloqueante para producir algo ejecutable**, y ahora incluye también la pregunta del auth-code de NY_SCH.
3. **0e** — Tier 2 PRE presenta huecos de esquema, como se esperaba; requiere el diff de Q-G4, el DDL localizado y el handoff al DBA/release owner.

`generate-fe-config-sql`, el motor de la Etapa E, **aún no está implementado**. Mientras tanto, la tabla del walk es la checklist y un humano escribe las sentencias una vez que las puertas y la revisión de findings lo permiten.
