# Segunda ronda de mejora del 10 de octubre de 2026

## Decisión y alcance

Este es un template Django/DRF + Vue/Vite. Se prioriza que sus derivados
hereden instrucciones correctas, ejemplos utilizables y pruebas de resultados
reales. El operador eligió simplificar los carruseles a grillas.

Base: `7888269f67f0bd47ed0743350b8131f1de99df2d`. Se mantuvo el máximo aprobado
de **tres causas globales**. Sólo se admitió impacto ALTO, o MEDIO con esfuerzo
BAJO y riesgo BAJO. La selección se contrastó con el preview canónico de
`improvement-ledger.sh --refresh --check`, sin escribir archivos del toolkit.

Cada archivo tuvo un único dueño. Los autores implementaron los frentes; el
orquestador coordinó decisiones, Git, infraestructura desechable e informe.
No hubo cambios de dependencias, lockfiles ni migraciones.

| Frente | Estado del diagnóstico | Decisión de esta ronda | PR |
|---|---|---|---|
| Seguridad | VALE LA PENA | Cantidades no positivas: pendiente por cupo | — |
| Mantenibilidad | VALE LA PENA | Corregir la guía de un runtime inexistente | [#20](https://github.com/ProjectAppCore/base_django_vue_feature/pull/20) |
| Observabilidad | VALE LA PENA | Errores inesperados de autenticación: pendiente por cupo | — |
| Rendimiento | VALE LA PENA | GET concurrentes duplicados: pendiente por cupo | — |
| Responsividad | VALE LA PENA | Acciones universales del header y grillas completas | [#21](https://github.com/ProjectAppCore/base_django_vue_feature/pull/21) |
| QA | VALE LA PENA | Pruebas observables y validación de las tres causas | [#21](https://github.com/ProjectAppCore/base_django_vue_feature/pull/21) |

Son estados del alcance inspeccionado; no certifican todo el template. Los
pendientes por cupo se distinguen de los descartes por retorno insuficiente.

## Tres causas implementadas

### I-M-50776dfd6375: instrucciones de otro runtime

**Impacto MEDIO / esfuerzo BAJO / riesgo BAJO.** La guía describía Nuxt,
`content`, propuestas/correos de otro proyecto y `build:django`. El código
utiliza Vue/Vite, `base_feature_app`, router explícito y build `dist`.

El autor corrigió exactamente `CLAUDE.md`, `AGENTS.md`, `frontend/CLAUDE.md`,
`docs/methodology/technical.md` y `docs/methodology/lessons-learned.md`.
Conservó byte por byte los bloques fleet, la guía general de seguridad y los
overrides Codex. AGENTS se regeneró desde la fuente del proyecto.

Commit `96d663d381c5a083e8fda7e2b244adf0db79f1c4`. Verificación: manifiestos,
21 rutas reales, 17 comprobaciones estáticas, renderer `CASE=NOOP` y
`git diff --check`. Sin tests nuevos de Markdown. Cinco checks CI verdes.

### I-R-c00269d38436: acciones únicas ocultas en anchos compactos

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.** `hidden lg:flex` ocultaba los
únicos controles de búsqueda, carrito y tema; los E2E omitían esos tamaños.
La compra no era alcanzable por ese recorrido en celular/tableta.

El header conserva una instancia de cada acción, disponible a todos los
anchos con controles de 44 px. El logo puede encogerse/truncarse. Se mantienen
el menú de autenticación y los contratos de carrito/tema. Cambios de aplicación
limitados a `Header.vue` y `ThemeToggle.vue`; SearchBar, ShoppingCart y Checkout
permanecen intactos.

### I-R-7c715614b757: artículos inalcanzables en carruseles

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.** La aritmética fija para cinco
tarjetas dejaba accesibles seis de diez registros, incluso en escritorio.
Las grillas de una, dos o cinco columnas muestran todos los datos, con
`ul > li > router-link`, orden y URLs conservados. Se retiraron flechas,
índices, transformaciones y temporizadores. Se mantuvieron nombres/imports.

Autor de ambas causas: responsividad. Commit inicial
`37f45ec2402d8fa9e656600c82de33a5c25fa919`; corrección de selectores
`289385591fef44e2786ca940d4d4b516a2ecdf10`. Exactamente doce archivos:
cuatro componentes, dos unitarios, cuatro E2E y los dos archivos existentes
del mapa. Se conservan los 31 IDs de flujos. QA no añadió una cuarta causa.

## Verificación y procedencia

QA de contenido y ejecución independiente: **APPROVED** en la combinación
limpia `44bfe90ef0c2087a315a083c1248c8d576239bcb`, árbol
`0d33b531d55983cc83bee7876f884d6130a4b4a9`.

| Capa | Resultado | Procedencia |
|---|---|---|
| Unitarios | 40/40: grillas 14, carrito 18, checkout 8 | SHA `5b560e0`, heredados por identidad de entradas |
| Matriz E2E | 38/38, cero retries/skips/flaky | SHA `44bfe90`; JSON/JUnit reales de diez lotes |
| Checkout E2E | 10/10: cinco en 835 y cinco en 412 | Venta real 201; campos requeridos; conservación ante 400/500/red |
| Gate específico | Seis archivos, 22 definiciones, cero errores/avisos | Reglas strict, lint externo y junk severity error |
| Flujos | 31: 30 cubiertos y uno exento; cero faltantes/junk | Freshness real en stdout y auditoría JSON |
| Inspección visual | Cinco tamaños, sin overflow horizontal | Home/grillas, búsqueda, carrito y tema operados; capturas reales |
| Autenticación UI | Accesos visibles y navegación/cierre comprobados | Invitados y cuenta scratch real; no certifica revocación servidor |

Matriz: 835×1194 y 412×915, siete casos cada uno; 1195×835, 1440×900 y
2560×1440, ocho cada uno. Manifest/veredicto:
`test-results/improvement/ronda-2/verification-44bfe90/`. Los artefactos se
archivan fuera de los worktrees antes de retirarlos, bajo
`/tmp/base-django-vue-improvement-r2-2026-10-10/evidence/`, excluyendo secretos,
credenciales, SQLite, media scratch, venv y node_modules.

El build se ejecutó realmente en `5b560e0a183e3467e1f61de4b5f1bccea4eaa1b7`.
La combinación nueva sólo cambia tres selectores de dos specs: aplicación,
backend, unitarios, dependencias y configuración permanecen idénticos.
Se verificaron los hashes de los 28 archivos `dist`. Los manifests conservan
los SHA reales; no atribuyen comandos anteriores a un commit posterior.

Unitarios independientes en `5b560e0`: grillas 14, carrito 18 y checkout 8,
en tres comandos de archivos específicos. Se heredan por identidad de entradas,
sin repetirlos. El runtime usa SQLite scratch, diez productos y diez blogs
con títulos únicos e imágenes WEBP reales 640×480. Backend 8001 y preview 5174
sirven API e imágenes desde el mismo origen del navegador. No se leyó `.env`,
no se corrió `manage.py migrate` ni se tocó el checkout principal.

E2E: un worker, cero retries, orden 835×1194, 412×915, 1195×835, 1440×900 y
2560×1440; máximo dos specs por comando. Se conserva el presupuesto ambiental
previo de 90 segundos por caso, 5 por aserción y los límites del fixture:
10 por acción y 25 por navegación. No se elevaron para resolver estos fallos.

### Rechazos conservados

El gate inicial rechazó tres casos débiles: dos aserciones de ausencia y un
cierre de búsqueda sin consulta. El autor añadió resultados positivos reales.

El primer CI falló quince casos por un selector coincidente con H1 del detalle
y H3 de tarjetas relacionadas. Tableta local reprodujo tres fallos y un caso
válido; la matriz se detuvo sin retries. Se informó al operador del segundo
rechazo de verificación. El autor añadió sólo `level: 1` a tres aserciones,
preservando título exacto, `toHaveText` y URL/ID. Sin `.first()`, sleeps ni
retries. El CI posterior de `2893855` tiene cinco checks verdes.

El CI rechazado registró dos casos ajenos que pasaron con retry. El CI posterior
verde informa **75 passed y tres flaky**: creación del usuario de backoffice,
agregar al carrito y persistencia del carrito. QA demostró la carrera de
`exists() or create_user` en setup paralelo de backoffice. Los otros dos sólo
acreditan ausencia del botón durante cinco segundos; no hay snapshot/red/cursor
para atribuir causa. El detalle admite ausencia por carga o por hover, pero no
se eligió una hipótesis sin evidencia. No se declaran corregidos ni plenamente
exonerados por esta ronda. Son distintos de los 48 casos locales con retry 0.

Los ocho lotes de 412–2560 pasaron inicialmente, pero una variable incorrecta
de reporter no creó sus JSON/JUnit. Se conservó la brecha y se autorizó una
ejecución adicional de cada lote sólo para recuperar evidencia automática,
con el mismo SHA, límites, specs y cero retries. Los ocho nuevos lotes pasaron
y produjeron los archivos `reporter-capture-*`. No se repitieron 835, checkout,
unitarios ni capturas ya válidos para buscar verde. Freshness se registra como
stdout porque su modo de comprobación no creó un archivo; no se inventó uno.

El resumen inicial del seed scratch usó una relación de imágenes inexistente
después de crear los datos. El orquestador corrigió sólo ese script ignorado,
conservó la misma base y no volvió a sembrar ni cambió aplicación.

## Pendientes elegibles por cupo

- Cantidades `0` y `-1` se validan/persisten
  (`backend/base_feature_app/serializers/sale.py:6`): MEDIO/BAJO/BAJO.
  Experimento con versiones distintas de los pins y referencia de producto
  sustituida; no acredita HTTP ni pagos negativos. Retomar con los pins.
- Errores inesperados de registro/Google devuelven 400 y texto de excepción
  (`backend/base_feature_app/views/auth.py:45,96`), sin diagnóstico específico:
  MEDIO/BAJO/BAJO. Propuesta: 500 genérico y log saneado.
- Cargas concurrentes realizan cuatro GET donde bastan dos
  (`frontend/src/stores/product.js:62`, `blog.js:28`): MEDIO/BAJO/BAJO.
  Experimento con promesas HTTP controladas; sin medir SQL, latencia ni
  frecuencia real en navegador.
- Galería oculta el único selector bajo `sm`
  (`frontend/src/views/product/Detail.vue:12`): ALTO/BAJO/BAJO.

## Descartes por retorno o evidencia insuficientes

- Rotación JWT completa: MEDIO/MEDIO/MEDIO; requiere blacklist, tablas y
  persistir refresh, cambiando la duración efectiva de sesión.
- Desactivar flags JWT inconsistentes: beneficio BAJO; limpieza de
  configuración sin resolver un contrato suficiente.
- Extraer normalización, unificar stores o abstraer CRUD: sin divergencia,
  fallo ni operación bloqueada que justifique complejidad nueva.
- APM/tracing o caché persistente: sin incidente/tráfico que justifique
  infraestructura para el scaffold.
- Paginación, precarga, índices o bundle: sin medición nueva de SQL, tamaño
  o carga; las rutas ya tienen importación dinámica.
- Retoques estéticos: sin pérdida demostrada de utilidad.

## Solicitudes al orquestador y límites

Sin solicitudes de archivos globales de aplicación. `improve/compartido`
contiene sólo este informe, MEDIO/BAJO/BAJO. Los recursos de prueba son
privados, ignorados y desechables; credenciales scratch fuera del archivado.

Toolkit sólo lectura, sin push. Ramas ajenas excluidas de la cola. El clon
principal conserva limpio su HEAD previo; no se actualiza el checkout del
servicio para resolver su retraso respecto de `origin/master`.

Siguen abiertos los pendientes anteriores. JWT mantiene flags de
rotación/blacklist sin app de blacklist y el cliente descarta refresh nuevo;
no hay contrato de revocación servidor en logout ni se demostró robo de tokens.
Dependencias sin certificar: GitHub anuncia 62 alertas, sin validar alcance
explotable ni recomendar upgrades indiscriminados. Los tres casos intermitentes
del último CI requieren su propio tratamiento; la carrera de backoffice tiene
causa demostrada y los dos de carrito conservan incertidumbre.

## Integración

Este informe registra la preparación aprobada antes de integrar. CI fuente:
cinco checks verdes en ambos PR;
[#20, Tests 38078392358](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38078392358)
y [#21, Tests 38079365317](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38079365317).
El verde del CI con retries se distingue de la matriz local sin retries.

Orden autorizado de `merge-queue`: mantenibilidad → responsividad → informe.
La combinación más este Markdown se valida en un tren draft, que se cierra
sin merge; aterrizan únicamente los squashes de los tres PR. Se comprobará
identidad del árbol final con `origin/master`, se retirarán recursos propios y
se ejecutará `all-in-base --check-only`. El cierre y sus SHA/PR se consignan en
la evidencia de integración y el reporte final al operador; no se anticipa aquí
un resultado que todavía no ocurrió.
