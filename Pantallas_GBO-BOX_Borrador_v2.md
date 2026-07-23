# Plataformas Integrales de Back Office: GBO y BOX

## Descripción General

### GBO (Plataforma Integral de Back Office para Banca Mayorista)

Plataforma integral orientada a la gestión y procesamiento de operaciones de banca mayorista y clientes corporativos. Centraliza y automatiza transacciones financieras complejas, incluyendo créditos corporativos, operaciones de tesorería, registraciones contables y administración de instrumentos financieros del mercado local e internacional.

Gestiona productos como swaps, cross currency swaps, opciones OTC, operaciones FX deliverable (spot y forward), depósitos, instrumentos negociados en mercados organizados (ETD) y bonos.

Actúa como núcleo operativo, permitiendo:

- Procesamiento y liquidación de derivados y productos financieros
- Gestión de posiciones y valuaciones
- Registración contable automática y conciliaciones
- Trazabilidad completa de cada operación
- Control y mitigación de riesgos operativos
- Cumplimiento de normativas locales e internacionales
- Integración con múltiples sistemas y mercados

**Stack Tecnológico**

- PLSQL, sistemas tradicionales de back office
- Integración con front office y contabilidad mediante archivos y conectores estándar
- Servicios asociados: upgrades y actualizaciones de la plataforma, testing / QA, migraciones de datos, soporte y mantenimiento operativo

### BOX (Plataforma Integral de Back Office con Microservicios y Datalake)

Plataforma moderna basada en microservicios, conectada directamente a un datalake, eliminando la dependencia de ficheros. Diseñada para agilizar el back office, mejorar la trazabilidad de operaciones y soportar altos volúmenes transaccionales de manera escalable.

Gestiona los mismos productos que GBO, con el valor añadido de integración nativa con APIs y microservicios, optimizando flujos de datos y reporting.

**Stack Tecnológico**

- PLSQL + Java, Spring Boot
- Microservicios y APIs RESTful
- Conexión directa a datalake, eliminando uso de ficheros intermedios
- Servicios asociados: upgrades y actualizaciones de versiones y microservicios, testing / QA, migraciones hacia datalake, soporte y mantenimiento operativo

La plataforma de back office BOX, utilizada para la gestión de operaciones de banca mayorista, está actualmente implementada en Europa y América, con planes de expansión a nuevas áreas y geografías.

## BOX FINANCIAL ENGINE AND ACCOUNTING

El nuevo proceso de BOX describe el flujo de generación de datos financieros y contables a partir de la información de operaciones (deals). A grandes rasgos, el proceso sigue varias etapas:

1. **Lectura y preparación de datos iniciales**

   Se leen los datos de flujo (BOX Flow Data) y los datos de operaciones (Deal Data) para generar la información de entrada del motor financiero (Financial Engine).

   En esta etapa, los datos se preparan y organizan según distintos criterios como Branch, dirección (por ejemplo, compra/venta) y divisa (currency).

2. **Ejecución del motor financiero (Financial Engine)**

   A partir de los Deal Data, se ejecuta el Financial Engine, que es el encargado de calcular y generar los datos financieros necesarios (por ejemplo, flujos, valoraciones, etc.).

3. **Preparación para la contabilidad**

   Una vez obtenidos los datos financieros, se preparan para su uso contable. Esto incluye:

   - Portfolio properties
   - Cálculo de MTM (Mark to market)
   - Generación de documentos contables (Documents)

4. **Elementos adicionales de configuración**

   También intervienen otros componentes necesarios para la contabilidad, como:

   - Accounting Topics (descripciones contables)
   - Cuentas (Accounts)
   - Históricos estándar
   - Configuraciones generales

5. **Ejecución de la contabilidad por producto**

   Finalmente, se leen los datos financieros generados por BOX junto con la información de Trading para ejecutar la contabilidad, diferenciada por tipo de producto.

## PRINCIPALES PANTALLAS INVOLUCRADAS

### 1. BOX ACCOUNTING – CONFIG

#### a. BOX – Accounting\Config.\Assign Instrument Type

Esta pantalla permite asignar un Instrument Type alternativo a una operación según diferentes criterios como ser la Branch, el instrumento, código, valor y de forma opcional una contrapartida.

Dentro de esta pantalla se pueden crear, editar y eliminar configuraciones de este tipo.

#### b. BOX – Accounting\Config.\Condition Port Properties

En esta pantalla se definen las condiciones que posteriormente se aplicarán a los Portfolio Properties ('BOX – Accounting\Config.\Portfolio Properties')

Estas condiciones determinan qué configuración contable corresponde a cada operación (trade).

Existen dos tipos de condiciones (condition type):

- Campo (field): evalúan el valor de un campo específico.
- Función (function): se registran/agregan las funciones que pueden ser usadas como condición de los portfolios.

En resumen, es un repositorio de campos y funciones disponibles para construir las reglas de asignación.

No hay limitaciones para las condiciones de tipo función, es decir, se puede añadir cualquier función existente en la base de datos.

En cambio, cuando la configuración tiene como objetivo evaluar el valor de un campo específico, solo se permite añadir y, por ende, evaluar los siguientes campos de la boleta: Collateral, Counterparty, Deal Treat, Instrument Type, Portfolio, Strategy y Structure Indicator.

En esta pantalla se pueden crear, editar y eliminar condiciones, de acuerdo con los permisos o roles del usuario.

No se permite eliminar una condición que esté siendo utilizada por al menos un Portfolio en ese momento.

#### c. BOX – Accounting\Config.\Config. Local Properties

Aquí se configuran los tópicos globales, locales e internos, así como las condiciones (relacionado con la pantalla de 'BOX – Accounting\Config.\Condition Port.Properties') que tendrá cada tipo de Portfolio.

- Se define qué información tendrán, pero no sus valores.
- Se establece la lógica (funciones/condiciones), no el resultado final.

En esta pantalla es posible crear, modificar y eliminar configuraciones, de acuerdo con los permisos o roles asignados al usuario.

**Restricción importante:**

Solo puede existir una configuración por combinación de Instrument, Branch Group e Initial Date.

Ej: solo existe una configuración específica para los Portfolio Properties de Swaps en la Branch de Brasil con Initial Date 01/01/1900.

#### d. BOX – Accounting\Config.\FX Liquid Config

En esta pantalla se pueden definir que divisas se consideran liquidas en operaciones de FX. Existe una función llamada 'f_isFXLiquid' que revisa esta tabla para ambas divisas de un par y, si ambas se encuentran configuradas aquí como liquidas, devuelve 1.

#### e. BOX – Accounting\Config.\Cross Account Config

Se trata de una pantalla de mantenimiento (ABM) que permite configurar las cuentas contables cruzadas utilizadas durante el proceso de revaluación.

Al crear una nueva configurando es obligatorio completar la Branch y la Account. Además, se puede configurar según instrument, currency, entity, topic y account type.

Los tópicos disponibles para configurar son los existentes en la pantalla BOX – Accounting\Data\Accounting Topics.

Nota: No se utiliza en Brasil.

#### f. BOX – Accounting\Config.\Grouped Accounting Config

Esta pantalla permite definir configuraciones contables agrupadas, con el objetivo de facilitar su aplicación conjunta dentro de un mismo proceso.

Cada registro se asocia a una Branch, un Group ID (Dead o Live) y un Config Type, que puede ser de tipo Topic Group o Std. Hist Group.

En función del Config Type seleccionado, se asigna adicionalmente un 'Hist Group' o un 'Topic Group'. En el caso de 'Hist Group', las opciones disponibles corresponden a las definidas en la pantalla 'BOX – Accounting\Data\Standard Historic Group'. En el caso de 'Topic Group', las opciones disponibles provienen de la pantalla 'BOX – Accounting\Data\Topic Group'.

Nota: No se utiliza en Brasil.

#### g. BOX – Accounting\Config.\Net EOM to CCS

En resumen, esta pantalla permite configurar las cuentas que deben tener neteo al final de mes para el instrumento de CCS.

A través de esta funcionalidad se definen los parámetros que determinan cómo se calculan y registran las diferencias de valoración al cierre mensual, incluyendo revaluaciones, devaluaciones, así como los beneficios o pérdidas asociados.

El proceso en si verifica todos los componentes de la operación, realiza el neteo y se transfieren a una cuenta de ajuste mm de activos o pasivos. De esta manera, se evita tener saldos en ambos lados.

#### h. BOX – Accounting\Config.\Portfolio Properties

Es el núcleo de la lógica contable. Determina qué contabilidad se aplica a cada operación (trade) según sus carácterísticas.

Para que una operación (trade) utilice un Portfolio determinado, debe:

- Cumplir las condiciones configuradas dentro del mismo.
- Coincidir en instrumento y Branch.
- Estar en estado válido.

Además de las condiciones que deben cumplirse, dentro de cada Portfolio se incluyen los tópicos, que representan el tipo de movimiento contable y su motivo. Los tópicos pueden ser:

- Globales (Global Topics)
- Locales (Local Topics)
- Internos (Internal Topics)

Todo lo configurado en la pantalla 'BOX – Accounting\Config.\Config. Local Properties' se refleja aquí.

En otras palabras, aquí se materializa la configuración previa, permitiendo definir el resultado esperado de las funciones incluidas en las condiciones o la cuenta específica asociada a cada tópico dentro de cada Portfolio.

**Nota importante:**

Cada cambio realizado en 'BOX – Accounting\Config.\Config. Local Properties' requiere recargar la configuración del Portfolio en donde se desee ver ese cambio (utilizando Ctrl+3 o botón "Load Config Prop") para que tenga efecto.

En esta pantalla es posible crear, modificar y eliminar Portfolios, de acuerdo con los permisos o roles asignados al usuario.

### 2. BOX ACCOUNTING – DATA

#### a. BOX – Accounting\Data\Accounting Topics

Los Accounting Topics representan los nombres o descripciones de los asientos contables. En esta pantalla se pueden crear, editar y eliminar los tópicos que se utilizarán en la configuración de los Portfolios.

En particular, los tópicos definidos aquí quedan disponibles para su posterior configuración en la pantalla 'BOX – Accounting\Config.\Config. Local Properties'.

Al crear un nuevo Accounting Topic, es obligatorio completar los campos Code y Description.

No puede existir más de un tópico con el mismo Code.

Algunos ejemplos de Accounting Topics son:

- PREMPROFITCON: Premium Profit (Resultados consolidables)
- ASSETACCRUAL: Asset Accrual
- INTERNOTHPREM: Internal Other Premium
- ACCRUALINTPREST: Accrual prestado (periódica acumulada)
- EQCTADIVCOMMISS: EQS Commission Cta. Div.

La lista completa de Accounting Topics existentes en BOX puede exportarse directamente desde esta pantalla utilizando la herramienta 'Export To' (Tools → Export to → Excel).

#### b. BOX – Accounting\Data\Documents

En esta pantalla se almacenan los documentos contables generados por el sistema. Cada documento posee un código (CODE), descripción, indicador de cancelación (MC_CANCEL), evento de trade asociado (FK_TRADEEVENT), Branch, fechas de creación y cancelación, entre otros.

Es decir, cada trade lleva un documento asociado y esta pantalla puede utilizarse para consultar los asientos contables de cada documento.

#### c. BOX – Accounting\Data\Global Accounts

Esta pantalla permite dar de alta y mantener las cuentas contables que podrán vincularse con cada tópico dentro de un Portfolio determinado.

En otras palabras, se crean y gestionan las cuentas que posteriormente se asociarán a un tópico específico dentro de cada Portfolio, asegurando su correcta configuración y disponibilidad para su uso contable.

No puede haber más de un registro con el mismo 'code' (account code).

#### d. BOX – Accounting\Data\Net Contract

Esta pantalla permite realizar la parametrización de las relaciones entre divisas, portfolios e instrumento. Ç

La pantalla permite filtrar por Branch (obligatorio), instrument, portfolio, currency, contract, security y un rango de fechas.

#### e. BOX – Accounting\Data\Standard Historic

En esta pantalla se configuran y se encuentran los registros de datos estáticos que definen los estándares de contabilización. Los mismos son utilizados para identificar qué evento contable generó cada movimiento.

#### f. BOX – Accounting\Data\Standard Historic Group

En esta pantalla se pueden definir distintas agrupaciones de Standard Historics. Cada grupo posee una descripción y un fk_group. Esta pantalla se utiliza para agrupar varios Standard Historic (pantalla BOX – Accounting\Data\Standard Historic) en un mismo grupo y facilitar así la configuración de Grouped Accounting Config (pantalla BOX – Accounting\Config.\Grouped Accounting Config).

En otras palabras, se vinculan los eventos que deben procesarse en el proceso de netting.

#### g. BOX – Accounting\Data\Topic Group

Permite agrupar tópicos para su gestión y uso conjunto. Es decir, desde esta pantalla se pueden agrupar múltiples Accounting Topics (pantalla BOX – Accounting\Data\Accounting Topics) que luego son referenciados desde Grouped Accounting Config (pantalla BOX – Accounting\Config.\Grouped Accounting Config) para definir como se agrupan los movimientos contables por topic.

### 3. BOX ACCOUNTING – REPORTS

#### a. BOX – Accounting\Reports\Balance Deal Report

El reporte de balance a nivel de operación permite visualizar y analizar los saldos asociados a cada operación de forma individual.

Este reporte proporciona una vista detallada del impacto contable por transacción, facilitando el seguimiento y control de los movimientos financieros.

#### b. BOX – Accounting\Reports\Balance Report

Esta pantalla permite consultar los saldos de cuentas contables sin agrupar.

Adicionalmente, ofrece la posibilidad de filtrar la información mediante distintos parámetros, incluyendo Branch, Instrumento, Account, Divisa, Branch Entity, Portfolio, Cuenta de Liquidación, Registry, Portfolio, Tópico e intervalo de fechas, facilitando así un análisis detallado y segmentado de los saldos.

#### c. BOX – Accounting\Reports\Instrument Balance Report

El balance desglosado por instrumento permite visualizar la información de saldos agrupada y segmentada según cada instrumento financiero.

Se permite filtrar la información por branch (obligatorio), currency y account.

#### d. BOX – Accounting\Reports\Movements Report

Esta es la pantalla principal para la revisión de la contabilidad en GBO. En ella se puede consultar la contabilidad diaria generada para cada una de las operaciones, así como analizar movimientos de nominal, MTM y registros contables asociados a pagos y cobros.

Toda la información mostrada en esta pantalla es la que posteriormente se transfiere al Accounting Ledger (Equation Tier2).

Dentro de esta pantalla es posible realizar búsquedas por operación específica, por una fecha determinada o por un rango de fechas.

Adicionalmente, la pantalla ofrece diversas opciones de filtrado y agregación de la información mediante distintos parámetros, tales como: Branch, Instrument, Account, divisa, Branch Entity, Portfolio Property, cuenta de liquidación, Registry, Portfolio y Tópico, además del rango de fechas seleccionado.

Estas funcionalidades permiten realizar un análisis detallado y segmentado de los movimientos contables.

### 4. VARIOS – GBO

#### a. GBO\SYS\Process\Batch\Event Config

Se configuran los eventos ejecutables del sistema. Dentro de cada 'evento config' se configura.

- Qué proceso se ejecuta
- Qué parámetros recibe
- Si son 2 o más procedimientos, en que orden se ejecutan.

Dentro de cada 'Event Config' existen diferentes pestañas de configuración. Las principales son 'Table', 'Fields' y 'Conditions', que funcionan como las distintas partes de una consulta (SELECT, FROM y WHERE, respectivamente).

Adicionalmente, la pestaña 'Update/Calculate' permite configurar los procedimientos que se ejecutarán, definiendo los parámetros que reciben y el orden de ejecución de cada proceso. Estos eventos luego se agrupan en un Event Goruping (pantalla 'GBO\SYS\Process\Batch\Event Grouping') y pueden ejecutarse manualmente o vía procesos batch.

Para ejemplificar, utilizaremos el event config 44123.44 ("Generación de fichero/reporte de uso de SSI NY"). El objetivo de este evento es identificar las SSIs de la branch NY_SCH que podrían estar obsoletas, ya sea porque nunca se han utilizado o porque no se usan desde hace mucho tiempo.

Este event config revisa la última fecha de uso de cada SSI y genera un reporte en formato CSV en un directorio determinado.

Si analizamos la configuración, encontramos los siguientes elementos:

- Pestaña Tables: se requiere únicamente la tabla Branch y una tabla Dual.
- Pestaña Fields: se definen los siguientes campos:
  - FileDest (directorio de destino), con valor 'SSISREPORTS'.
  - FileName (nombre del reporte), con valor 'SSI_Log_Report_NY_'.
  - ProcessDate.
  - La PK de la branch.
- Pestaña Conditions: la única condición necesaria es Br.PK = #BRANCH#.
- Pestaña Update Calculate: aquí se encuentra el procedimiento encargado de generar el reporte: PGT_NY.PKG_REPORT_SSI.P_GENERATE_SSI_REPORT. En este caso, es el único procedimiento que se ejecuta dentro de este event config, aunque podrían añadirse más indicando su orden de ejecución (0, 1, 2, etc.).

Dentro del procedimiento, en la pestaña Parameters, se definen los parámetros que se le envían y el orden en que se pasan. Estos parámetros corresponden a los campos definidos previamente en la pestaña Fields.

Por último, el event config se añade a un event grouping, en este caso el número 21.674,44. Este event grouping es invocado desde un job y se ejecuta automáticamente con la periodicidad que se haya definido.

#### b. GBO\SYS\Process\Batch\Event Grouping

Esta pantalla permite crear grupos de eventos que posteriormente podrán ejecutarse a través de Jobs o ejecutarse manualmente desde la pantalla 'GBO\SYS\Process\Batch\Run Batch Process'.

Cada grupo de eventos puede incluir uno o más Event Configs (creados en la pantalla anterior 'GBO\SYS\Process\Batch\Event Config', y permite definir el orden de ejecución de estos dentro del flujo del proceso.

#### c. GBO\SYS\Process\Batch\Run Batch Process

Esta funcionalidad permite ejecutar un Event Grouping, proporcionando los parámetros necesarios para su procesamiento.

Entre los parámetros de ejecución se incluyen la fecha, la sucursal (Branch) y, cuando corresponda, el instrumento.

#### d. GBO\Process\Process Monitor

Esta pantalla permite monitorear la ejecución de procesos en función de una fecha, sucursal (Branch) e instrumento.

A través de esta pantalla es posible dar seguimiento al estado de los procesos ejecutados, identificando su resultado de forma clara.

En caso de errores, estos se visualizan resaltados en color rojo con el estado "ERR", facilitando su rápida detección.

#### e. GBO\SYS\Process\Batch\Event Log

Cuando un Event Grouping se ejecuta de forma incorrecta —es decir, cuando aparece en la pantalla 'GBO\Process\Process Monitor' en color rojo con estado "ERR"— se puede utilizar esta pantalla para obtener información detallada sobre el error ocurrido.

Esta funcionalidad proporciona una vista ampliada de los eventos fallidos, facilitando el análisis de su causa, contexto y trazabilidad dentro del sistema, con el objetivo de apoyar el diagnóstico y la resolución de incidencias.

#### f. GBO\Financial Engine\Control\Configuration\MIS

En esta pantalla es donde se realizan las configuraciones del Market Data. El Market Data hace referencia al conjunto de datos de mercado utilizados como input en los procesos de valoración y cálculo financiero. Incluye, entre otros, curvas de tipos de interés, tipos de cambio, índices, volatilidades y demás referencias necesarias para la correcta valoración de instrumentos financieros.

Esta pantalla permite definir los parámetros necesarios para la configuración de datos de mercado utilizados por el motor financiero, estructurados en diferentes pestañas funcionales:

- **Generic:** Define el nombre de la configuración, la divisa local de la curva, la curva de fixing asociada y los sistemas front y back office que la consumen.
- **Yield Curve:** Actualmente sin uso en tier2.
- **Carry:** Permite definir el índice utilizado para el cálculo de la tasa de carry en función de la divisa. Esta pestaña existe en GBO pero no en BOX.
- **Accrual:** Configura la periodicidad del devengo diario de intereses y comisiones por instrumento.
- **Fixing Exception:** Permite definir excepciones en la curva para un producto específico.
- **Accrual Exception:** Define excepciones para evitar el devengo diario en determinados productos. Adicionalmente, permite configurar el tipo de contabilidad asociado: Accrual (contabilidad estándar) o Market Value (contabilidad basada en alta y baja).
- **Carry Exception:** Define excepciones de carry por divisa, permitiendo operar sin necesidad de disponer de una tasa asociada. Esta pestaña existe en GBO, pero no en BOX.
- **Currency Basis:** Define la base utilizada para el cálculo del factor de descuento para la obtención del NPV por divisa, utilizando modelos lineales (short) o exponenciales (long) según corresponda.

Los datos disponibles para cada día se ven en la pantalla 'GBO\Financial Engine\Control\Historical Data\Market Data'.

Tanto la pantalla de configuración como la de datos las tenemos disponibles también en BOX: BOX - Financial Engine\Control\Configuration\MIS BOX - Financial Engine\Control\Historical Data\Market Data

#### g. GBO\Financial Engine\Control\Configuration\Fixing curve

La Fixing Curve es una curva de referencia utilizada para determinar los tipos de fijación (fixing) aplicables en instrumentos financieros. Su función principal es proporcionar una estructura de precios basada en pares de divisas, que sirve como input para procesos de valoración y cálculo dentro del motor financiero.

La configuración se realiza en la ruta 'GBO\Financial Engine\Control\Configuration\Fixing Curve' y los datos de cada día se ven en 'GBO\Financial Engine\Control\Historical Data\Fixing Curve'.

Esta pantalla permite definir y gestionar las curvas de fixing utilizadas en el sistema, estructuradas en diferentes pestañas funcionales:

- **Generic:** Define el nombre de la curva y la divisa local asociada. Únicamente se podrán incluir pares de divisa que contengan dicha moneda base.
- **Array of Quotes:** Permite seleccionar los pares de divisa (ubicados en GBO\Market Data\Quote References\Currency Pair) cuyos precios serán cargados en el sistema (GBO\Market Data\Quote Prices\Currency Pair).
- **Array of Yield Curve:** Actualmente sin uso en Tier2.

Estas pantallas también las encontramos en el módulo de BOX: BOX - Financial Engine\Control\Configuration\Fixing Curve y los datos se ven en BOX - Financial Engine\Control\Historical Data\Fixing Curve

#### h. GBO\SYS\Selectors\Market Data\Quote type

Un instrumento de cotización o Quote Type es aquel que proporciona precios de mercado (cotizaciones) con una frecuencia determinada. Se entiende por cotización el precio al que un instrumento financiero se valora o se negocia en el mercado en un momento dado.

Dentro de GBO, se consideran instrumentos de cotización los siguientes tipos:

- Referencias (Securities)
- Pares de divisas (Foreign Exchange)
- Índices (Indexes)

#### i. GBO\Market Data\Quote General\Quote Source

El Quote Source representa la fuente de origen de las cotizaciones y contiene la siguiente información:

- **Status:** estado del Quote Source, que puede ser Activo o Inactivo
- **Code:** código asignado al Quote Source dentro de GBO
- **Description:** descripción detallada del Quote Source
- **Entity:** entidad de referencia que respalda el dato publicado. Ej: Banco de Mexico.
- **Quote Market:** mercado o concepto asociado a la cotización (único campo opcional)
- **Reference Price:** condición o situación de mercado a la que hace referencia la cotización

#### j. GBO\Market Data\Quote references

Un Quote Reference representa la relación entre un instrumento de cotización (Quote Type – GBO\SYS\Selectors\Market Data\Quote type) y una fuente de cotización (Quote Source - GBO\Market Data\Quote General\Quote Source). Este elemento define cómo se obtiene un precio de mercado a partir de una fuente concreta.

El Quote Reference se configura en función de distintos elementos, como el tipo de instrumento (por ejemplo, índices), el instrumento específico (por ejemplo, un índice bursátil "X" o un índice de tipos de interés "Y"), un plazo de vencimiento (maturity) y la fuente de cotización (Quote Source).

**Tipos de Quote Reference**

**1. GBO\Market Data\Quote references\Currency Pair**

Gestión de Quote References para pares de divisas (Quote Type = Foreign Exchange).

Para dar de alta un Quote Reference de este tipo se requieren los siguientes campos:

*Pestaña Generic*

- **Quote Type:** valor fijo del sistema "Foreign Exchange"
- **Quote Source:** fuente de cotización utilizada para obtener precios
- **Currency Pair:** par de divisas asociado al Quote Reference
- **Direction:** sentido de la cotización (Loan, Borrower, Buy, Sell o Both)
- **Maturity:** plazo utilizado para la obtención del precio
- **Rounding Rule:** regla de redondeo aplicada al resultado (General Round o General Truncate) es decir, se redondean o se truncan los decimales indicandos en el campo 'Decimal Number'. Campo opcional
- **Decimal Number:** número de decimales sobre los que se aplica la regla de redondeo o truncado. Campo opcional

*Pestaña Search Proxy*

Permite almacenar un conjunto de Quote Sources similares, utilizados como respaldo cuando no es posible obtener el precio desde la configuración principal de la pestaña 'Generic'.

*Pestaña Alias*

Contiene la información de identificación del dato en otros sistemas mediante su alias.

**2. GBO\Market Data\Quote references\Index**

Gestión de Quote References para índices (Quote Type = Indexes).

Para este tipo de Quote Reference se requieren los siguientes campos:

*Pestaña Generic*

- **Quote Type:** valor fijo del sistema "Indexes"
- **Quote Source:** fuente de cotización utilizada para obtener precios
- **Index:** índice asociado al Quote Reference. Los índices disponibles se configuran en la pantalla GBO\Market Data\Static Data\Environment\Indexes
- **Maturity:** plazo utilizado para la obtención del precio. Los periodos disponibles se configuran en la pantalla GBO\Static Data\Environment\Standard Periods
- **Rounding Rule:** General Round o General Truncate. Campo opcional
- **Decimal Number:** número de decimales para redondeo o truncado. Campo opcional

*Pestaña Search Proxy*

Permite definir fuentes de cotización alternativas en caso de no poder obtener el precio desde la configuración principal.

**3. GBO\Market Data\Quote references\Security**

Gestión de Quote References para valores (Quote Type = Securities).

Para este tipo de Quote Reference se requieren los siguientes campos:

*Pestaña Generic*

- **Quote Type:** valor fijo del sistema "Securities"
- **Quote Source:** fuente de cotización utilizada para obtener precios
- **Security:** security asociada al Quote Reference. Las securities disponibles se configuran en la pantalla GBO\Static Data\Securities\Securities
- **Maturity:** plazo utilizado para la obtención del precio. Los periodos disponibles se configuran en la pantalla GBO\Static Data\Environment\Standard Periods
- **Rounding Rule:** General Round o General Truncate. Campo opcional
- **Decimal Number:** número de decimales para redondeo o truncado. Campo opcional

*Pestaña Search Proxy*

Permite definir fuentes de cotización alternativas en caso de no poder obtener el precio desde la configuración principal.

#### k. GBO\Market Data\Quote prices

En esta pantalla es posible visualizar los precios asociados a un determinado Currency Pair, Index o Security, para una fecha específica o un rango de fechas.

Asimismo, se pueden aplicar filtros por Quote Reference, Quote Source o por un elemento concreto como Currency Pair, Index o Security.
