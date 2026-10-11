# Cuarta ronda de mejora del 11 de octubre de 2026

## Decisión y alcance

Este repositorio es un template Django/DRF + Vue/Vite. Sus funcionalidades son
ejemplos: se corrigen comportamientos defectuosos que podrían heredarse, sin
añadir requisitos de un producto final. La base es
`f39b2eaa506be6d92d679829c70a866ba07d3410`.

Se aprobaron tres causas con evidencia concreta. El umbral fue impacto ALTO,
o MEDIO con esfuerzo BAJO y riesgo BAJO. Los estados siguientes describen el
alcance inspeccionado; no certifican madurez del repositorio completo.

| Frente | Estado | Decisión | PR |
|---|---|---|---|
| Seguridad | VALE LA PENA | Permitir el acceso de staff con el permiso real de Attachment | [#29](https://github.com/ProjectAppCore/base_django_vue_feature/pull/29) |
| Mantenibilidad | VALE LA PENA | Conservar relaciones compartidas y archivos al revertir un borrado | [#30](https://github.com/ProjectAppCore/base_django_vue_feature/pull/30) |
| Observabilidad | NO VALE LA PENA | No activar tareas cuyo contrato operacional es contradictorio | — |
| Rendimiento | NO VALE LA PENA | No optimizar sin beneficio nuevo medido | — |
| Responsividad | NO VALE LA PENA | No intervenir sin una rotura reproducible | — |
| QA | VALE LA PENA | Resolver la carrera real del setup de backoffice | [#31](https://github.com/ProjectAppCore/base_django_vue_feature/pull/31) |

Los agentes implementaron y commitearon sus archivos. El orquestador decidió
alcance y propietarios, preparó infraestructura desechable, revisó las entregas
y condujo Git e integración. No implementó ningún frente. Cada archivo tuvo un
dueño; dependencias, lockfiles, migraciones y configuración global quedaron sin
cambios. El toolkit se mantuvo de solo lectura, sin commit ni push.

## Cambios aprobados

### I-S-0484ba45f84b — permiso de las galerías del admin

**Impacto MEDIO / esfuerzo BAJO / riesgo BAJO.** La etiqueta `attachments`
del permiso no corresponde al app real `django_attachments`: el staff con el
permiso generado por Django recibía HTTP 403. Se corrigió únicamente la cadena
del permiso; se conservan login, staff y superuser. Es una falla de acceso de
usuarios autorizados; no se demostró una brecha de acceso ajeno.

Archivos: `backend/django_attachments/admin.py` y
`backend/base_feature_app/tests/admin/test_attachment_permissions.py`.
Head fuente: `a73d3ad846a36561ffc2caaf93e97d398e6503e6`.

Quince casos HTTP usan usuarios, permisos, sesiones y base de datos reales:
cinco actores por tres operaciones. Verifican creación persistida, payload de
adjuntos y conservación de inventarios ante el rechazo. Tres controles contra
la base reprodujeron el 403 incorrecto. Gate específico: 100/100, sin nuevas
excepciones. CI fuente verde: Tests `38098207508`, Gate `38098207514`.

### I-M-db2df79f69c5 — borrados con relaciones compartidas

**Impacto ALTO / esfuerzo MEDIO / riesgo MEDIO.** El esquema, admin y CRUD
permiten compartir líneas de venta y bibliotecas. Los borrados anteriores
asumían propiedad exclusiva y podían eliminar datos ajenos. Además, el
post_delete eliminaba archivos antes de que la transacción pudiera revertirse.

Sale limpia sólo las líneas capturadas que quedaron sin otra venta. Product y
Blog borran primero el objeto pedido y conservan su biblioteca mientras exista
otro propietario. Se respeta el alias de base de datos, ProtectedError, retorno
anterior y transacción. Los originales y miniaturas se limpian después del
commit, con nombres, storage y metadatos capturados.

Archivos de aplicación: `backend/base_feature_app/models/{sale,product,blog}.py`
y `backend/django_attachments/cleanup.py`. Pruebas: los tres archivos de esos
modelos, `tests/models/test_models_delete.py`, `tests/admin/test_admin.py`,
`tests/views/test_crud_endpoints_extended.py` y
`tests/integration/test_attachment_cleanup.py`, dentro de
`backend/base_feature_app/`. Head final fuente:
`09d27b1c09a7716a92d7df750677703e719a6db9`.

El autor ejecutó 54 casos positivos en lotes 10/16/12/16 y tres controles sobre
la base que reprodujeron pérdida de una relación ajena, de un producto
superviviente y de archivos tras rollback. Incluyen archivos y miniaturas
reales, fallo SQL por trigger, callback estable, segundo alias, admin y CRUD.

El primer CI detectó dos tests antiguos que fabricaban DoesNotExist mediante
un doble de Library.delete. Se autorizó un archivo adicional y se retiraron
sólo esos dos tests; las referencias ausentes tienen cobertura con datos reales.
El caso restante de Sale conserva su contenido. Tres regresiones enfocadas y
el gate de siete archivos pasaron. Los diez blobs originales son idénticos a
`3202867296f3d278f3aec2b24ecadf6da1f7eb82`: sus 54 ejecuciones previas mantienen
esa procedencia. La deduplicación adicional de Sale siguió descartada.
CI final fuente verde: Tests `38100181322`, Gate `38100181293`.

El pre_save y QuerySet.delete directo conservan su contrato anterior. La
aceptación SQLite no acredita concurrencia MySQL. Un fallo de storage después
del commit puede dejar archivos pendientes; no restaura SQL y no se añadió
retry, compensación ni nuevas tareas.

### I-M-8dc4c990e768 — preparación concurrente de QA

**Impacto MEDIO / esfuerzo BAJO / riesgo BAJO.** El setup de backoffice usaba
`exists() or create_user()`. La ronda anterior mostró un UNIQUE de email antes
del cuerpo del test. Se reemplaza únicamente el literal de Python por
get_or_create, con contraseña calculada sólo al crear y los mismos flags. Una
cuenta existente conserva todos sus campos; el modelo no tiene username.

Único archivo: `frontend/e2e/admin/backoffice.spec.js`. No se agregan tests
E2E, helpers, sleeps, timeouts, retries, serialización o excepciones del gate.
No cambia UX ni mapa de flujos.

Un artefacto ignorado extrae el literal del archivo real y del baseline. Tres
procesos con conexiones SQLite independientes se sincronizan antes del INSERT
real. El baseline registra dos UNIQUE; el arreglo termina en los tres procesos,
recupera dos IntegrityError con SELECT real y conserva una cuenta con contraseña
hasheada y flags correctos. Otro caso conserva íntegramente una cuenta existente.
No aparecieron OperationalError en esa aceptación.

El gate inicial falló por añadir --strict, que el CI no usa. El gate repetido
con los flags exactos del CI pasó: cero errores, un aviso antiguo de selector.
No se alteró ese selector ni se añadió una excepción. El primer lote E2E local
conserva cinco verdes y siete timeouts de navegación, sin retries; no demuestra
una falla de la creación concurrente. Se guarda separado de la validación final.

La ejecución final sobre build/preview pasó 12/12: los cuatro casos existentes
repetidos tres veces, workers 3, retries 0 y timeout 30000 intacto. Trazas y
capturas tienen rutas exclusivas. Head fuente final:
`ccfbbcbd0baad606eca2ba0591fae8f4a9235c78`. El build real produjo 28 archivos;
los 148 blobs frontend restantes coinciden con la base, de modo que cambiar el
literal E2E no altera los inputs del build. La mejora no se presenta como
solución para los timeouts del primer lote dev.

## Verificación e integración

Los manifiestos originales registran comandos, nodeids, resultados nativos y
hashes, incluidos los intentos rechazados. La validación combinada independiente
se vincula al SHA limpio de la cola; exige pruebas backend, E2E live y gate.
El motor canónico improvement-ledger mantiene el registro privado de las tres
causas. QA se registra como maintainability en su esquema de cinco frentes;
la responsabilidad del cambio sigue siendo del agente QA.

El tren draft de merge-queue valida la combinación final antes de drenar los
PR fuente. El draft no se mergea. El cierre compara el árbol de origin/master
con el del tren y comprueba los PR por número y head exactos. El helper de
worktrees confundió la rama reutilizada improve/seguridad con un PR viejo:
esa asociación no se usa para autorizar el retiro.

La evidencia se archiva en
`/tmp/base-django-vue-improvement-r4-2026-10-11/evidence/`, con hashes antes de
retirar los worktrees. Se excluyen secretos, credenciales, SQLite, media,
venv y node_modules. El clon principal y las seis referencias ajenas excluidas
se preservan. El cierre usa all-in-base --check-only.

## Descartes y pendientes

- Puente Huey: MEDIO/BAJO/MEDIO; documentación contradictoria, sin obligación
  operacional del scaffold. Activarlo podría habilitar backup/retención reales
  sin contrato explícito. Importarlo aislado no produjo efectos, pero eso no
  prueba seguridad de la ejecución de las tareas.
- Deduplicar cargas: se observaron 2, 3 o 4 GET en memoria según el orden, sin
  medición nueva de frecuencia o coste en runtime. No se añadió caché o índices.
- Unificar stores o normalizadores: sin divergencia ni fallo demostrado.
- Deduplicar el test antiguo de Sale: retorno bajo; no forma parte del ajuste
  requerido por CI.
- Cierre/foco del carrito y grids de checkout: necesitan operación y medición;
  las clases CSS por sí solas no demuestran una acción inaccesible.
- Recalcular tamaño de página al rotar: impacto BAJO, sin pérdida demostrada.
- APM, tracing o alertas nuevas: sin incidente ni tráfico propio que los justifique.

Reabrir estos puntos sólo con evidencia nueva. Los dos flakies de carrito de
rondas anteriores mantienen causa incierta; no se declaran corregidos por un
CI verde. Las alertas de dependencias requieren triage propio: los inventarios
de GitHub y npm tienen alcances distintos y no prueban explotabilidad. No se
hicieron upgrades sin evaluación. Las tareas Huey siguen sin activarse.

## Solicitudes al orquestador

No hubo solicitudes de cambios globales de aplicación. improve/compartido
contiene sólo este informe: MEDIO/BAJO/BAJO por trazabilidad de decisiones y
evidencia para proyectos derivados. Las dos ampliaciones de la lista de archivos
de mantenibilidad fueron autorizadas antes de editar: ubicación de integración
para los tests de archivos y retiro de los dos doubles obsoletos revelados por CI.
