# Ronda de mejora del 10 de octubre de 2026

## Alcance y decisiones

Proyecto: `base_django_vue_feature`, plantilla Django/DRF + Vue/Vite sin
tráfico ni servicios activos. Base de diagnóstico:
`122c6fdb001faa33938a0ac5a8506d712d43723f` (`origin/master`).

Se diagnosticaron seis frentes mediante agentes independientes de lectura.
El operador confirmó un máximo de **tres causas globales** y eligió publicar
la evidencia en este proyecto. El toolkit se conserva en lectura, sin
modificar su ledger ni hacer push; la selección utilizó el preview canónico
de `improvement-ledger.sh --refresh --check`.

| Frente | Diagnóstico | Decisión de esta ronda |
|---|---|---|
| Seguridad | VALE LA PENA | Corregir identidad Google no verificada |
| Mantenibilidad | VALE LA PENA | Guía heredada incorrecta: pendiente por cupo |
| Observabilidad | VALE LA PENA | Corregir venta parcial y falso éxito del checkout |
| Rendimiento | VALE LA PENA | Peticiones simultáneas duplicadas: pendiente por cupo |
| Responsividad | VALE LA PENA | Acciones móviles, carruseles y galería: pendientes por cupo |
| QA | VALE LA PENA | Validar las tres causas, sin candidato discrecional adicional |

La suficiencia no se certifica para todo el proyecto. Los diagnósticos
delimitaron código inspeccionado y evidencia pendiente; en particular no se
validó visualmente la matriz responsive ni se completó una auditoría de
dependencias.

## Causas seleccionadas

### I-S-90444e54f0be: identidad Google no requerida

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.**

`backend/base_feature_app/services/auth_service.py:104` omitía la verificación
cuando faltaba credencial y seleccionaba una cuenta por el correo del body.
`backend/base_feature_app/views/auth.py:104` emitía sus tokens. Una reproducción
de la función real por AST, con usuario staff ficticio y almacenamiento en
memoria, devolvió la cuenta existente sin llamar al verificador.

La corrección exige token verificado contra la audiencia configurada y correo
verificado del payload; nunca usa el body para elegir identidad. Sin credencial
válida devuelve 401; sin Client ID, 503; cuenta inactiva, 403 antes de modificarla.
Mantiene el éxito 200, alias `id_token` y estructura de tokens/`created`.

QA requerida: casos de rechazo sin tokens ni mutaciones, audiencia/claims
inválidos, configuración ausente, cuenta inactiva y autenticación válida con
correo del body contradictorio. El mock se limita al verificador Google externo.

### I-O-52fee3da1120: creación de venta no atómica

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.**

`backend/base_feature_app/serializers/sale.py:20` guardaba cabecera y líneas
antes de descubrir un producto inexistente, sin transacción. Ejecutar el cuerpo
real con SQLite en memoria y referencias `[1, 999]` dejó una venta, una línea
y una relación tras fallar. La prueba vigente aceptaba `DoesNotExist` sin
comprobar residuos.

La corrección valida referencias y revierte toda la creación si falla. Una
referencia inválida o desaparecida produce 400; la venta válida conserva 201,
productos y cantidades. QA comprueba filas y relaciones, incluido un fallo
después de comenzar a guardar las líneas.

### I-O-8e037499c22c: checkout confirma antes de recibir respuesta

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.**

`frontend/src/views/product/Checkout.vue:227` no esperaba la creación y borraba
el carrito, anunciaba éxito y navegaba inmediatamente. El store silenciaba el
rechazo. Ejecutar los cuerpos reales con HTTP rechazado reprodujo esa pérdida.
El E2E sólo exigía salir de checkout y limpiaba almacenamiento durante la
navegación, por lo que tampoco demostraba un pedido con artículos.

La corrección espera la respuesta, impide envíos simultáneos y conserva carrito
y formulario ante fallos. Sólo tras creación confirmada limpia y navega. La demo
no cobra tarjetas: la confirmación describe el pedido, sin afirmar un cobro.

QA requerida: pendiente, segundo envío, HTTP 400/500, interrupción de red y
POST 201 real. Actualizar el flujo existente con `failure`, sin duplicar su
happy path.

## Pendientes por cupo, sin descartarlos por bajo retorno

- Guía canónica que prescribe Nuxt, app `content` y `build:django` inexistentes
  (`CLAUDE.md:254,571,641`): MEDIO / BAJO / BAJO.
- Dos consumidores concurrentes disparan dos GET antes de activar el cache
  (`frontend/src/stores/product.js:62`, `blog.js:28`): MEDIO / BAJO / BAJO.
- Header oculta los únicos accesos al carrito y búsqueda bajo `lg`, sin
  reemplazo móvil (`frontend/src/components/layouts/Header.vue:35`): ALTO / BAJO / MEDIO.
- Carruseles calculan desplazamiento/límite para cinco tarjetas aunque muestren
  una o dos (`ProductCarousel.vue:23`, `BlogCarousel.vue:24`): ALTO / MEDIO / MEDIO.
- Galería oculta su único selector bajo `sm`
  (`frontend/src/views/product/Detail.vue:12`): ALTO / BAJO / MEDIO.

## Descartes y condiciones para reevaluar

- Extraer normalización de URLs duplicada: beneficio bajo sin divergencia ni
  cambio pendiente; reevaluar si la regla comienza a divergir.
- Unificar estilos de stores o abstracciones CRUD por semejanza: sin fallo o
  operación bloqueada demostrados; no justificar por longitud o preferencias.
- Incorporar APM, tracing o monitoreo del scaffold: el registro excluye esta
  plantilla y no hay tráfico ni incidente que justifique el coste.
- Cambios estéticos responsive sin pérdida demostrada de utilidad: retorno
  insuficiente.
- Precarga de galerías, paginación, lazy loading o índices: sin medición SQL,
  tamaños o carga reales; mantener como evidencia pendiente, sin rediseñar APIs.

## Verificación y cierre

La autoría y pruebas pertenecen a seguridad y observabilidad. El orquestador
sólo coordina Git, dependencias de prueba, configuración scratch e informe.
Cada archivo tiene un único dueño. No se incluyen cambios de producto fuera
de las tres causas.

La QA final se ejecuta sobre un SHA combinado limpio: pytest por selecciones,
Jest acotado y Playwright con Django/Vite que sirven ese contenido. La base
SQLite es desechable, creada mediante las herramientas de bases de pruebas de
Django, sin `manage.py migrate` ni lectura de `.env`. Los artefactos de ejecución
se guardan en `test-results/improvement/2026-10-10-base-improvement/`, ignorado.
Se exige el gate con severidad CI y auditoría final de flujos.

Evidencia obtenida antes de incorporar este informe al tren:

| Capa | Resultado | Evidencia |
|---|---|---|
| Backend Google | 72 casos distintos pasan | Seis lotes pytest, máximo 16 por comando |
| Backend ventas | 12 casos pasan | Referencias inválidas, desaparición, rollback de segunda línea y contrato HTTP |
| Frontend unit | 10 casos ejecutados pasan | Componente con store real y frontera HTTP; 20 casos ajenos excluidos por selección |
| E2E checkout | 5 casos pasan con imagen real | POST 201 sin interceptar éxito; validación y fallos 400/500/red |
| Gate combinado | Cero errores; cuatro warnings | Siete archivos, lint externo activo, reglas strict y severidad CI |
| Flujos | 30 cubiertos y uno exento | Cero parciales, junk-only o missing; checkout success/error/failure; Google exento |

Las ejecuciones iniciales de backend/unit corresponden a
`d0ccf4f778706b82836551ea6cd3075e056d2f38`. La repetición E2E con imagen y
auditorías afectadas corresponde a `8b463cb4f00db976a8b23a6ed3c597a0368fa997`.
La incorporación del informe sólo añade Markdown; el Verifier vuelve a
comprobar lo afectado sobre el SHA final limpio. El manifest conserva el SHA
real de cada ejecución y demuestra qué entradas ejecutables permanecen
idénticas; no atribuye ejecuciones antiguas a un commit nuevo. Los PRs consignan
el SHA final y el resultado de CI antes de integrar.

La comprobación sobre `917a42e8908e02d1bff84729bc55c325621b705f` volvió a
pasar los 84 casos backend y los 10 unit, pero rechazó el checkout: los cinco
E2E combinados fallaron y el éxito aislado también. Los otros cuatro escenarios
aislados pasaron. Esos resultados se conservaron; el CI verde no los sustituyó.

Una traza posterior se agotó antes de añadir el producto: navegar al catálogo
costó 20,465 segundos y varios módulos locales tardaron 3,4–3,8 segundos.
El host tenía seis CPUs, carga de 30,30 y presión CPU de 77,77 %. La traza
demostró retrasos generales y agotamiento del presupuesto, sin demostrar un
fallo del cierre del carrito. Servir el build de producción del mismo código
tampoco bastó: el contexto volvió a cerrarse durante la preparación.

El Verifier confirmó en los resultados de Playwright un presupuesto total
efectivo de 30 segundos. El orquestador proporcionó un config temporal ignorado
que importa la configuración original y concede 90 segundos al escenario,
manteniendo 5 segundos por comprobación y límites globales de 30 segundos por
acción o navegación. El fixture original del spec conserva límites más
estrictos de 10 segundos por acción y 25 por navegación. Usa un worker y cero
reintentos. Conserva proyecto, viewport, acciones, animaciones y código
de pruebas. La primera ejecución pasó los cinco casos en 44,4 segundos; un
error de nombres de variables del reporter exigió repetir únicamente para
capturar JSON/JUnit reales, sin reconstruirlos a partir de la conclusión.
La captura posterior pasó **5/5 en 42,1 segundos**, sin reintentos, skips ni
flaky. El Verifier aprobó las tres causas sobre
`917a42e8908e02d1bff84729bc55c325621b705f`: 84 casos backend, 10 unit y cinco
E2E; gate sin errores y flujos sin brechas adicionales. Los JSON/JUnit reales
están en `917a42e/environment90/checkout.{json,xml}`, junto al manifest y el
veredicto. Esa ejecución usó el build de producción servido por Vite preview;
su procedencia y controles HTTP están en `917a42e/runtime-built.json`.
El PR consigna también la comprobación afectada tras este cambio documental.
No se aplicó un cambio de producto por esta limitación ambiental.

El CI de integración sobre ese SHA también acredita los cinco casos de
checkout en su primer intento, mediante el artefacto oficial de
[run 38059507034](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38059507034).
Un caso ajeno de `shopping-cart-add` necesitó un retry; queda registrado como
inestabilidad fuera del alcance, sin ampliar la ronda para corregirlo.

### Bloqueo posterior, conservado sin atribución especulativa

La actualización documental produjo el tren limpio
`463bd6a8b67bee0dad5574b818dbe212e69b0f94`. El Verifier comprobó que backend,
frontend, scripts y CI conservaban los mismos trees que `917a42e`; no atribuyó
los 84 backend ni los 10 unit previos a una ejecución nueva. La única repetición
E2E afectada pasó cuatro casos y falló uno en 52,556 segundos: antes de probar
HTTP 500, `cart-close` no desmontó `cart-overlay` dentro de la aserción de cinco
segundos (`shopping-checkout.spec.js:19-20`). El manifest local sigue
**REJECTED**. No se borraron ni sustituyeron sus JSON/JUnit y contexto de error.

El artefacto oficial del mismo SHA sí acredita **5/5 checkout en primer intento**
sobre Django/Vite reales y SQLite efímera, incluido POST 201 sin interceptar
éxito: [CI 38064120548](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38064120548).
La auditoría del Verifier confirmó su procedencia. Tres casos ajenos necesitaron
un retry: dos de carrito por enlaces ausentes y uno de backoffice por email
duplicado. Ninguno de esos fallos aporta evidencia sobre el cierre del overlay.

El dueño ejecutó una reproducción aislada HTTP 500: pasó sin retries en
18,682 segundos. La espera de cierre duró 2,797 segundos; era compatible con
retraso, pero no explicaba el fallo sin una traza de ese cierre fallido.
Se autorizaron después **dos capturas diagnósticas como máximo**, con hooks
pasivos ignorados y el spec original: clic real, estilos y muestras de frames
a cinco por segundo, sin alterar estado, acciones o límites de pruebas.
Ambas pasaron 5/5, sin retries, en 36,780 y 33,263 segundos; registraron el
desmontaje entre 1,088 y 1,253 segundos después de pulsar cerrar. No capturaron
la intermitencia ni hubo errores del navegador. La presión CPU de esas
ejecuciones verdes no prueba qué causó la anterior.

La causa sigue **INCONCLUSA**; no hay propuesta de cambio respaldada por esa
evidencia. No se modificaron `ShoppingCart.vue`, el helper ni las pruebas para
eludir el cierre. Los artefactos y hashes están en
`463bd6a/diagnostic-http500-owner/` y
`463bd6a/diagnostic-cart-frames-owner/diagnostic-summary.json`. Se agotó el
límite diagnóstico acordado, sin repetir hasta obtener verde. Al registrar
esta decisión, los tres PR y el tren tienen CI verde, pero **la integración
permanece detenida por el rechazo local de QA**. El cierre y cualquier decisión
posterior se consignan en los cuerpos de los PR.

El primer CI de observabilidad descubrió una diferencia que el fixture sin
imágenes no reproducía: el cursor del click en catálogo permanecía sobre la
imagen de detalle, activaba zoom y retiraba temporalmente el botón de compra.
La traza oficial mostraba zoom `scale(4)` en `/product/12`. El implementador
corrigió únicamente el helper E2E para comprobar navegación y sacar el cursor
de la imagen, sin sleeps ni aumentos de timeout
(`1a9f8fd865e4027eebeff447391d338f35dc26d2`). La repetición con un Attachment
real de 128×128 pasó los cinco escenarios. No se ocultó el fallo con el pase
previo del fixture vacío.

El gate de observabilidad también se detuvo tras dos ejecuciones fallidas por
lint. El orquestador informó la detención y delimitó el desbloqueo; el mismo
dueño corrigió tres líneas D204 dentro de sus archivos. El gate siguiente pasó.
Las advertencias restantes no justificaron una limpieza adicional.

Los cuerpos de los PRs consignan commits, comandos, resultados y referencias
de CI. `merge-queue` valida la combinación antes de integrar; su PR draft es
un banco de pruebas y no se mergea. El cierre usa `all-in-base --check-only`
y retira únicamente worktrees limpios con contenido confirmado en `master`.

PRs de implementación: [seguridad #16](https://github.com/ProjectAppCore/base_django_vue_feature/pull/16)
y [observabilidad #17](https://github.com/ProjectAppCore/base_django_vue_feature/pull/17).

## Solicitudes atendidas por el orquestador

- Documentar el contrato Google: incluido en este informe, sin ampliar la
  corrección de aplicación ni reescribir las guías heredadas pendientes.
- Proporcionar runtime y ejecución combinada: dependencias de prueba,
  configuración scratch sin `.env`, producto con imagen y servidores locales.
  Son recursos ignorados y desechables; no cambian manifests, lockfiles,
  migraciones ni configuración desplegada.
- Publicar decisiones/evidencia: único archivo rastreado de
  `improve/compartido`, este informe. No se escribieron ledger, memoria QA ni
  reportes en el toolkit.

El censo encontró cinco ramas históricas sin PR abierto con commits propios:
`chore/17052026-vuln-audit`, `docs/15052026-add-git-branch-protocol`,
`docs/16052026-claude-md-git-rules`, `docs/20082026-testing-standard` y
`double-check-30042026`. Se excluyeron porque no pertenecen a esta ronda;
no se integraron ni borraron. El checkout principal quedó intacto.

Riesgos abiertos: acciones/contenido móviles pendientes; auditoría de
dependencias incompleta; configuración de blacklist/renovación JWT que requiere
diagnóstico conjunto. El push mostró 62 avisos de dependencias en la base,
32 clasificados altos por GitHub; esta ronda no confirmó su alcanzabilidad ni
los remedió. SQLite no certifica concurrencia/locks MySQL. La ejecución E2E
local requiere el presupuesto ambiental documentado; el caso CI ajeno de
carrito y backoffice sigue necesitando diagnóstico de su inestabilidad. El
cierre intermitente del carrito conserva un rechazo local sin causa atribuida,
aunque CI y las capturas diagnósticas pasan. No se certifica
despliegue ni infraestructura.
