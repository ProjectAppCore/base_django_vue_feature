# Tercera ronda de mejora del 10 de octubre de 2026

## Decisión y alcance

Template Django/DRF + Vue/Vite, sin tráfico de producción propio. Se prioriza
corregir ejemplos defectuosos que podrían heredarse, con cambios pequeños y
beneficio demostrado. No se añadió funcionalidad para un producto final.

Base: `afb736c65a3e39807a18f1d9e615e5a10a31da6f`. Se aprobaron tres causas:
impacto ALTO, o MEDIO con esfuerzo BAJO y riesgo BAJO. El motor canónico de
`improvement-ledger.sh` contrastó la selección y registra ejecución/QA en un
ledger privado e ignorado. El toolkit se mantuvo de solo lectura, sin push.

Cada archivo tuvo un dueño. Los autores implementaron y commitearon sus
frentes; el orquestador coordinó decisiones, Git, infraestructura desechable e
informe. No cambiaron dependencias, lockfiles, modelos ni migraciones.

| Frente | Estado | Decisión | PR |
|---|---|---|---|
| Seguridad | VALE LA PENA | Rechazar cantidades no positivas sin persistencia parcial | [#24](https://github.com/ProjectAppCore/base_django_vue_feature/pull/24) |
| Mantenibilidad | MADURO | Sin problema concreto en el alcance revisado | — |
| Observabilidad | VALE LA PENA | HTTP 500 genérico y diagnóstico saneado de autenticación | [#25](https://github.com/ProjectAppCore/base_django_vue_feature/pull/25) |
| Rendimiento | NO VALE LA PENA | No intervenir sin beneficio medido en runtime real | — |
| Responsividad | VALE LA PENA | Hacer alcanzable la segunda imagen en celular | [#26](https://github.com/ProjectAppCore/base_django_vue_feature/pull/26) |
| QA | VALE LA PENA | Pruebas de resultados reales y verificación independiente de las tres causas | #24, #25 y #26 |

Los estados describen el alcance inspeccionado. No certifican el repositorio
completo: el ledger no declara una auditoría exhaustiva de cada frente.

## Cambios aprobados

### I-S-8d86a56a9e4b — cantidad de una línea de pedido

**Impacto MEDIO / esfuerzo BAJO / riesgo BAJO.** El serializer aceptaba y
persistía cantidades `0` y negativas. Ahora rechaza valores menores que uno,
conservando el campo inferido del modelo y sus límites.

Archivos exactos: `backend/base_feature_app/serializers/sale.py` y
`backend/base_feature_app/tests/views/test_public_endpoints.py`. Head fuente
`43fe511c9a66479d1d24f9ea7ca7c20606a07fb3`.

Ocho casos HTTP comprueban cantidades positivas `1/2` en respuesta y base de
datos, y rechazo completo de un pedido cuya segunda línea tiene `0/-1`.
Conservan una venta previa, su línea cantidad `7` y todas sus relaciones.
Se verificaron también siete casos existentes de serializer, sin editarlos.

### I-O-74aaa05fb0ea — excepciones inesperadas de autenticación

**Impacto MEDIO / esfuerzo BAJO / riesgo BAJO.** Dos ramas inesperadas de
registro/Google devolvían HTTP 400 con texto interno de la excepción. Ahora
devuelven HTTP 500 con JSON genérico y un evento ERROR con operación fija y
tipo de excepción, sin mensaje interno, traceback ni datos de la petición.

Archivos exactos: `backend/base_feature_app/views/auth.py` y
`backend/base_feature_app/tests/views/test_auth_endpoints.py`. Head fuente
`0e2aaf20d368d383e937108072c75b327354ca46`.

Las pruebas provocan un fallo real de INSERT mediante triggers temporales de
SQLite, aislados y retirados al terminar. Comprueban respuesta, diagnóstico
exacto, ausencia de marcadores privados y conservación íntegra de una cuenta
previa. Los dobles se limitan a los proveedores externos CAPTCHA/Google.
Los once casos seleccionados conservan los resultados esperados 400,
401/403, configuración 503 y éxito 201/200, incluido el alias `id_token`.

### I-R-1622ac507e6c — selector de galería oculto en celular

**Impacto ALTO / esfuerzo BAJO / riesgo BAJO.** El único selector de imágenes
estaba oculto bajo `sm`. Se retiró esa ocultación y se añadieron nombres
accesibles `View image N` a las pestañas. Se conservan HeadlessUI, orden,
URLs, zoom y compra; no se añadió infraestructura.

Archivos exactos: `frontend/src/views/product/Detail.vue`,
`frontend/e2e/shopping/shopping-product-detail.spec.js`,
`frontend/e2e/flow-definitions.json` y `docs/USER_FLOW_MAP.md`. Head fuente
`3cc2d2f1343f04c83b3279c7352313c02d8d5843`.

Cinco casos operan la galería con tap en 835×1194 y 412×915, teclado en
1195×835 y 2560×1440, y click en 1440×900. Comparan rutas de imágenes reales
del API, selección ARIA, carga y dimensiones naturales, controles de al menos
44×44 y ausencia de overflow horizontal. Se conservan el caso de cantidad
`1→2→1` y el de producto inexistente. IDs y clases de resultado del mapa se
mantienen; cambia la descripción del mismo flujo.

## Verificación y procedencia

QA independiente **APPROVED**; registrada por el motor canónico en la
combinación limpia `325c442b4ea22d3b68720f65ffdec1fe25ca667f`, árbol
`90ec22cedbebdbbca2f964a8b49cf3bf6cfb04a5`.

| Capa | Resultado | Ejecución real |
|---|---|---|
| Backend | 26/26: pedidos 15, autenticación 11 | SHA `52a9226`; heredados por identidad de entradas |
| Unitarios frontend | 2/2 seleccionados; 21 exclusiones por filtro | SHA `52a9226`; JSON original y JUnit fiel |
| E2E live | 8/8: galería/cantidad/ID inexistente 7, registro 500 uno | SHA `325c442`; cero retries/skips/flaky |
| Gate específico | Tres archivos, 32 definiciones; cero errores/avisos/infra | SHA `325c442`; strict, junk-error, Ruff y ESLint |
| Flujos | Freshness pasa; 30 cubiertos, uno exento, cero faltantes/junk | SHA `325c442`; stdout y JSON reales |

Manifest y reporte: `test-results/improvement/ronda-3/verifier-325c442b/`.
`equivalence-corrected.json` acredita que el único archivo distinto contra
`52a9226` es el spec E2E: los otros 528 blobs permanecen idénticos. Los 28
casos backend/unit conservan `execution_commit=52a9226...`, `inherited=true`;
no se atribuyen al SHA posterior como ejecuciones nuevas. Los ocho E2E se
volvieron a ejecutar por la corrección de ese spec, con outputs exclusivos.


Los backend usan los pins Django 6.0.5 / DRF 3.17.1 y SQLite aislada. No
acreditan equivalencia con MySQL ni recepción de logs en un despliegue real.
El E2E heredado de registro simula HTTP 500 sin JSON y verifica aviso y
permanencia en el formulario; el JSON nuevo se verifica en backend. No
certifica recuperación de CAPTCHA.

La matriz ejecuta 835×1194 primero, un worker y retries 0. El build real se
ejecutó en `52a9226b9e834cd389d2885e6fe05f253f05807a`; los 28 archivos de
`dist`, las imágenes WEBP físicas y las respuestas del proxy/API quedan
registrados. Scratch: diez productos y diez blogs, sin leer `.env` ni correr
`manage.py migrate`. Los servicios de prueba son propios y desechables.

### Rechazos y correcciones conservados

QA rechazó inicialmente un exceso de aserciones/longitud en las pruebas de
autenticación. El autor agrupó contratos relacionados sin retirar resultados,
añadir helpers opacos o debilitar el gate. Se corrigieron también duplicación
de casos E2E, un selector ambiguo y la comparación de URL absoluta del API
contra ruta relativa del DOM, por el mismo autor de responsividad.

La primera QA combinada produjo 35/36 verdes, sin retries: falló el caso
existente de cantidad por ausencia de controles. El comando posterior de
auth reemplazó su carpeta de output y se perdió la primera traza/captura.
Los JSON/JUnit y el rechazo canónico se conservan; no se atribuye una causa
a la URL `/product/1` referida inicialmente sin aquella traza.

El autor reprodujo el fallo con output exclusivo y traza: en `/product/10`,
API e imágenes 200, el puntero del clic quedó sobre la imagen y activó zoom
`scale(4)`. Ese estado oculta los controles de compra. El arreglo modifica
sólo dos líneas del test: URL exacta y movimiento físico del puntero fuera
de la imagen. Mantiene visibilidad y cantidad `1→2→1`, sin cambiar zoom,
timeouts, retries o aplicación. La reproducción corregida pasó; la evidencia
antes/después y la verificación independiente se preservan por separado.

El primer gate independiente no encontró Ruff en PATH. Se conservó ese
warning y se repitió sólo el gate con el venv que ya contenía Ruff 0.15.13,
sin reinstalar ni modificar dependencias.

## Descartes por retorno o evidencia insuficientes

- Compartir promesas de carga: BAJO/BAJO/BAJO; el experimento en memoria
  demuestra **2, 3 o 4 GET** según el orden, no cuatro siempre. Después de
  cargar, la caché añade cero GET. Sin frecuencia o coste real observados,
  no se mantiene como mejora elegible de impacto MEDIO.
- Extraer los dos normalizadores multimedia: sin divergencia ni fallo.
- Unificar stores o abstraer CRUD: sin cambio bloqueado que justifique la
  nueva abstracción; beneficio BAJO y mayor esfuerzo/riesgo.
- Consolidar tema/idioma o retirar aliases vigentes: sin problema demostrado.
- Caché persistente, índices, paginación, precarga o bundle: sin medición
  que justifique añadir complejidad al scaffold.
- APM/tracing/alertas nuevas: sin incidente o tráfico propio que lo justifique.
- Retoques estéticos: sin pérdida de utilidad demostrada.

Reabrir estos puntos sólo con un fallo, divergencia, frecuencia o coste
observado nuevos; no repetir recomendaciones de estilo.

## Pendientes y solicitudes al orquestador

Sin solicitudes de aplicación o archivos globales de los implementadores.
`improve/compartido` contiene únicamente este informe: MEDIO/BAJO/BAJO por
trazabilidad de decisiones, descartes y evidencia para futuros derivados.

La carrera demostrada en el setup paralelo de usuario de backoffice
(`exists() or create_user`) sigue pendiente por el cupo de tres causas;
MEDIO/BAJO/BAJO. No es un descarte por bajo retorno. Los dos fallos
intermitentes de carrito de la ronda anterior conservan causa incierta;
esta ronda no los declara corregidos ni exonerados por un CI verde.

Las dependencias requieren un triage propio. GitHub anunció 62 alertas
(32 altas, 26 moderadas y cuatro bajas); el inventario de instalación npm
informó 49 (43 altas, cuatro moderadas y dos bajas), incluido desarrollo.
Son fuentes/alcances distintos, no se suman ni prueban explotabilidad en el
template. No se hicieron upgrades sin evaluación. Quedan sin cambiar el
tratamiento de fallos de transporte del proveedor Google y el contrato de
rotación/revocación JWT, que no superaron el umbral de riesgo de esta ronda.

## Integración y cierre

Este informe se publica después de QA y antes del drenaje. La combinación
final añade sólo este documento, manteniendo idénticos todos los archivos
verificados. El tren draft de `$merge-queue` valida ese árbol final antes de
los squashes por PR; nunca se mergea el draft. El cierre contrasta el árbol
de `origin/master` contra el del tren, comprueba cada PR y ejecuta
`$all-in-base --check-only` para las ramas propias.

La evidencia privada se archiva en
`/tmp/base-django-vue-improvement-r3-2026-10-10/evidence/`, con hashes antes
de retirar worktrees. Se excluyen secretos, credenciales, SQLite, media
scratch, venv y node_modules. Ramas ajenas expresamente excluidas, sin tocar.
El clon principal permanece limpio en su HEAD previo; no se actualiza el
checkout del servicio para eliminar el retraso frente a `origin/master`.

CI fuente: cinco checks verdes por PR, en sus heads finales:
[#24, Tests 38091434657](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38091434657),
[#25, Tests 38091766092](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38091766092) y
[#26, Tests 38093028677](https://github.com/ProjectAppCore/base_django_vue_feature/actions/runs/38093028677).
El CI del tren y los squashes definitivos se registran en el archivo de cierre,
sin atribuirlos a comandos anteriores ni modificar evidencia ya verificada.
