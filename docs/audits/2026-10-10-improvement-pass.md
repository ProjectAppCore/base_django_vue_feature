# Ronda de mejora del 10 de octubre de 2026

## Alcance y criterio

Proyecto `base_django_vue_feature`: template Django/DRF + Vue/Vite. Los
comportamientos son ejemplos para nuevos proyectos. Se priorizaron identidad
verificada, consistencia de datos y confirmaciones verdaderas; se simplificó
la decoración del carrito para que no condicione su uso.

Base de diagnóstico: `122c6fdb001faa33938a0ac5a8506d712d43723f`
(`origin/master`). Las referencias de línea de los hallazgos corresponden a
esa base. Se diagnosticaron seis frentes mediante agentes independientes de
lectura. El operador confirmó un máximo de **tres causas globales**. Cada
archivo tuvo un único dueño; el orquestador coordinó decisiones, Git,
infraestructura de prueba e informe, sin implementar los frentes.

Sólo se admitieron impacto ALTO, o MEDIO con esfuerzo BAJO y riesgo BAJO.
No modificar el template era un resultado válido. El toolkit se mantuvo en
lectura: sin ledger, memoria, reportes ni push. La selección utilizó el preview
canónico de `improvement-ledger.sh --refresh --check`.

| Frente | Estado del diagnóstico | Decisión y trabajo |
|---|---|---|
| Seguridad | VALE LA PENA | Identidad Google verificada; PR #16 |
| Mantenibilidad | VALE LA PENA | Guía operativa incorrecta: pendiente por cupo |
| Observabilidad | VALE LA PENA | Venta atómica y checkout que conserva datos ante fallos; PR #17 |
| Rendimiento | VALE LA PENA | GET concurrentes duplicados: pendiente por cupo |
| Responsividad | VALE LA PENA | Acciones móviles, carruseles y galería: pendientes por cupo |
| QA | VALE LA PENA | Regresiones de las tres causas y contratos observables del carrito; soporte sin cuarta causa |

Estos estados no certifican todo el frente ni todo el template. No hubo
validación visual de la matriz responsive ni auditoría completa de dependencias.

## Tres causas implementadas

### I-S-90444e54f0be: identidad Google no requerida

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.**

`backend/base_feature_app/services/auth_service.py:104` seleccionaba una cuenta
por el correo del body cuando faltaba credencial;
`backend/base_feature_app/views/auth.py:104` emitía sus tokens. Ejecutar la
función real extraída por AST con una cuenta ficticia reprodujo el bypass sin
llamar al verificador.

Se exige credencial verificada contra la audiencia configurada y correo
verificado del payload. El body no elige identidad. Credencial inválida produce
401; ausencia de Client ID, 503; cuenta inactiva, 403 antes de modificarla.
Se conserva HTTP 200, alias `id_token` y estructura `user/access/refresh/created`.
El mock se limita a la frontera externa de Google, sin sustituir la lógica
que resuelve el payload.

Autor: seguridad. Commit `c070a58e57064d56e8a5a88bd01d5132611afebe`.
PR: [#16](https://github.com/ProjectAppCore/base_django_vue_feature/pull/16).
Cuatro archivos aprobados, sin cambios de configuración ni dependencias.

### I-O-52fee3da1120: creación de venta no atómica

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.**

`backend/base_feature_app/serializers/sale.py:20` persistía cabecera y líneas
antes de detectar un producto inexistente. Ejecutar el cuerpo real con SQLite
scratch y referencias `[1, 999]` dejó residuos tras fallar. La prueba anterior
aceptaba la excepción sin comprobar esos residuos.

La creación ahora valida referencias y usa una transacción. Una referencia
inválida o desaparecida produce 400; una venta válida conserva 201, productos,
cantidades y orden. Un fallo inesperado después de iniciar las líneas se
propaga y revierte cabecera, líneas y relaciones. Las filas se bloquean en
orden; SQLite no acredita la concurrencia ni los locks de MySQL.

### I-O-8e037499c22c: éxito de checkout anterior a la respuesta

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.**

`frontend/src/views/product/Checkout.vue:227` no esperaba la creación: borraba
el carrito y anunciaba éxito inmediatamente. El store silenciaba el rechazo.
Ejecutar los cuerpos reales con HTTP rechazado reprodujo la pérdida; el E2E
anterior sólo exigía salir de la página.

Ahora la interfaz espera creación confirmada, impide envíos simultáneos y
conserva carrito y formulario ante 400/500/interrupción de red. Sólo después
limpia y navega. La demo no procesa tarjetas; su mensaje confirma un pedido,
sin afirmar un cobro. El E2E exige POST 201 real y artículos agregados por la
interfaz; no intercepta el éxito ni limpia datos durante la navegación.

Autor de ambas causas: observabilidad. Head final de implementación
`a281f15da0e92822691171e6f5a0faa326b33901`.
PR: [#17](https://github.com/ProjectAppCore/base_django_vue_feature/pull/17).
Trece archivos aprobados, incluidos pruebas y mapa de flujos existente.

## Simplificación conservadora del carrito

**Soporte QA de checkout: MEDIO / BAJO / BAJO; no cuarta causa.**

El cierre dependía del callback de salida decorativa. Se simplificó para que
el padre actualice inmediatamente la visibilidad y Vue retire panel/backdrop.
Pruebas con padre real y callbacks sin completar demostraron el contrato:
tres casos fallaban con el cierre anterior y pasan con el cierre inmediato
(commit `035a2808d32cd3d280cf2a55a83616d3e5fd6f16`). El escenario existente
comprueba cierre por backdrop, reapertura con datos preservados y cierre por botón.

La comprobación posterior sobre `638bd28c49cf06eeb6ef3c64998274a920fdfded`
pasó seis de siete E2E. La traza restante mostró el panel desplazándose mientras
el clic en Checkout agotaba sus 10 segundos, antes de instalar `route.abort`.
El mismo ancestro animado cambiaba de `translate3d(511.859px,0,0)` a su posición
final. Esto acredita la dependencia decorativa; no explica por qué la animación
nominal duró más ni atribuye causalidad a la CPU.
Traza SHA256: `5ee7096dccfa0b7f1b9b14d9e7ada08259393259401b63b11efca84d9f8e74ac`.

Con el criterio template autorizado se retiró también la entrada GSAP
(`a281f15`). Apertura y cierre son declarativos; se conservan scroll lock,
productos, cantidades, subtotal y almacenamiento al reabrir. La prueba de
llamadas a GSAP fue sustituida por apertura y navegación a Checkout mediante
router real. QA aprobó el contenido y el alcance; el Verifier aprobó después la ejecución combinada. Los dos E2E quedaron
byte-idénticos respecto de `5f8f2a4`; sin sleeps, retries, nuevos timers ni
aserciones debilitadas. Sólo se precisó el flujo `header-cart-overlay`, sin
inventar otro flujo.

## Verificación y procedencia

La verificación usa SHA combinado limpio, SQLite desechable, producto con
Attachment PNG real 128×128 y build de producción servido por Vite preview.
No se leyó `.env`, ejecutó `manage.py migrate` ni tocó el checkout principal.
Backend y frontend sirvieron los inputs consignados en los manifests.

**QA independiente APPROVED** sobre
`aa7f3a3993a38d5d285a55c16415e4e114035031` / tree
`20f3fc1cf32151b5422dd4d4e24fa86754a03e06`, con árbol limpio.
Manifest y veredicto: `aa7f3a3/verification/{manifest.json,qa-verdict.md}`.
Los siete E2E pasaron en una ejecución, sin retries, skips ni flaky, incluidos
POST 201 real, fallos 400/500/red y reapertura del carrito.

| Capa | Resultado acreditado | Procedencia |
|---|---|---|
| Google backend | 72 casos distintos pasan | Seis lotes pytest, máximo 16 por comando |
| Ventas backend | 12 casos pasan | Referencias inválidas, desaparición, rollback y contratos 400/201 |
| Checkout/store unit | 10 casos pasan | Componente/store reales, mock HTTP en frontera |
| Carrito unit | 18 casos pasan | Apertura/navegación, cierre y reapertura/conservación |
| E2E | 7/7 pasan en 63,783 segundos | Dos specs, siete casos, sin retries |
| Gate combinado | Cero errores, nueve avisos; nueve archivos/102 definiciones | Lint externo, reglas strict y severidad CI |
| Flujos | 30 cubiertos, uno exento | Cero faltantes/junk; Google exento |

Los 84 backend y 10 unit de checkout/store corresponden a ejecución real sobre
`917a42e8908e02d1bff84729bc55c325621b705f`. Sus inputs se conservaron idénticos;
no se reasignó una ejecución previa a un SHA nuevo. El carrito y E2E afectados
se verificaron en la combinación nueva
`aa7f3a3993a38d5d285a55c16415e4e114035031`. Build, hashes servidos y controles
HTTP están en `aa7f3a3/{build.json,runtime-live.json}`. El backend fue iniciado
desde `c209207`, con tree de backend idéntico al actual; el preview fue
reconstruido desde el SHA nuevo. El documento final sólo modifica Markdown; su incorporación se comprueba
por equivalencia de inputs, conservando el SHA real de las pruebas.
El CI fuente de observabilidad también tiene sus cinco checks verdes sobre
`a281f15`: [Tests 38073884581](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38073884581)
y [Gate 38073884612](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38073884612).

Los artefactos reales se guardan bajo
`test-results/improvement/2026-10-10-base-improvement/`, ignorado, y se archivan
fuera de los worktrees antes de retirarlos. Cada manifest conserva el SHA real,
comandos, límites, resultados y evidencia heredada explícitamente.

### Fallos previos conservados y metodología

Los rechazos locales permanecen documentados; el CI verde no los sustituyó.
La preparación inicial E2E en servidor de desarrollo agotó el presupuesto
total de 30 segundos bajo retrasos generales del host. Se utilizó un config
ambiental ignorado con 90 segundos por escenario, manteniendo 5 por aserción,
30 globales por acción/navegación y los límites más estrictos del fixture
original: 10 por acción y 25 por navegación. Un worker, retries 0 y trazas de fallo.
Esos mismos límites se conservaron al simplificar el carrito.

El cierre intermitente histórico sobre `463bd6a` quedó sin causa atribuida:
CI pasó; un replay aislado y dos capturas pasivas pasaron, sin reproducirlo.
No se dedujo causalidad de presión CPU ni se repitió indefinidamente hasta verde.
La simplificación posterior se justifica por el contrato observable y por la
traza concreta del movimiento de entrada, bajo la autorización para simplificar
los ejemplos del template.

Una primera ejecución de `638bd28` sólo pasó 1/7 porque el orquestador omitió
`VITE_BACKEND_URL` al iniciar preview: `/api/products/` fue enviado al puerto 8000
sin backend y devolvió 500. Se corrigió exclusivamente el inicio del runtime,
se comprobó el API 200 desde el mismo origen del navegador y la ejecución
posterior pasó 6/7, exponiendo el movimiento de entrada. Se preservan ambas
ejecuciones y su causa; no se cambió aplicación/configuración por ese error.

El fixture con imagen real también reveló que el cursor activaba zoom de la
imagen de detalle y ocultaba el botón de compra. El autor corrigió el helper
para comprobar la navegación y sacar el cursor de la imagen (`1a9f8fd`),
sin sleeps ni aumento de límites. El gate previo descubrió tres errores de
lint; tras informar la detención, su dueño los corrigió en archivos autorizados.

## Pendientes por cupo

Son elegibles y quedan fuera por el máximo de tres causas, no por bajo retorno:

- Guía canónica Nuxt/`content`/`build:django` inexistentes
  (`CLAUDE.md:254,571,641`): MEDIO/BAJO/BAJO.
- GET simultáneos duplicados antes de activar cache (`product.js:62`,
  `blog.js:28`): MEDIO/BAJO/BAJO.
- Header oculta los únicos accesos a carrito y búsqueda bajo `lg`
  (`Header.vue:35`): ALTO/BAJO/MEDIO.
- Carruseles usan desplazamiento/límite para cinco tarjetas aunque muestren
  una o dos (`ProductCarousel.vue:23`, `BlogCarousel.vue:24`): ALTO/MEDIO/MEDIO.
- Galería oculta su único selector bajo `sm` (`Detail.vue:12`): ALTO/BAJO/MEDIO.

## Descartes por retorno o evidencia insuficientes

- Extraer normalización de URL: beneficio bajo sin divergencia; reevaluar sólo si diverge.
- Unificar estilos de stores o abstraer CRUD: sin fallo ni operación bloqueada demostrados.
- APM/tracing para el scaffold: sin tráfico ni incidente que justifique su coste.
- Retoques estéticos responsive: sin pérdida demostrada de utilidad.
- Precarga/paginación/lazy loading/índices: sin medición de SQL, tamaño o carga reales.

## Solicitudes atendidas e integración

- Documentar contrato Google y decisiones/evidencia: únicamente este informe,
  en `improve/compartido`; MEDIO/BAJO/BAJO. Sin reescribir las guías pendientes.
- Proporcionar dependencias/runtime de prueba, base scratch e imagen real:
  recursos ignorados y desechables. Sin manifests, lockfiles, migraciones ni
  cambios de configuración desplegada.
- Ninguna solicitud de implementación fuera de alcance tras el ajuste final.

PR de informe: [#18](https://github.com/ProjectAppCore/base_django_vue_feature/pull/18).
`merge-queue` valida la combinación final en el PR draft
[#19](https://github.com/ProjectAppCore/base_django_vue_feature/pull/19), que
jamás se mergea. Sólo después de QA aprobada y CI verde se integran 16 → 17 → 18.
`all-in-base --check-only` comprueba entrega y contenido en `origin/master`;
se retiran únicamente worktrees propios limpios después del aterrizaje.

Cinco ramas históricas sin PR abierto se excluyeron, sin integrar ni borrar:
`chore/17052026-vuln-audit`, `docs/15052026-add-git-branch-protocol`,
`docs/16052026-claude-md-git-rules`, `docs/20082026-testing-standard` y
`double-check-30042026`. El checkout principal y el toolkit quedaron intactos.

## Límites y riesgos abiertos

Las acciones/contenidos móviles elegibles siguen pendientes. No se completaron
la auditoría de dependencias ni el diagnóstico conjunto de blacklist/renovación
JWT. GitHub reportó 62 avisos (32 altos, 26 moderados, 4 bajos); no se confirmó
alcanzabilidad ni remedio en esta ronda. SQLite no certifica locks MySQL.
CI histórico mostró retries en casos ajenos de carrito/backoffice: necesitan
diagnóstico propio, sin atribuirlos a estos cambios. No se certifica todo el
template, despliegue ni infraestructura.
