# Kit de Triaje de Phishing

**▶ Pruébalo aquí:** https://d-gomez-sec.github.io/kit-triaje-phishing/

Cuatro herramientas de análisis para decidir, en minutos y sin depender de servicios externos, si un correo sospechoso es un fraude.

**Qué resuelve:** acorta el tiempo de triaje de un correo sospechoso reuniendo en un solo sitio las cuatro comprobaciones que normalmente exigen cuatro webs distintas.
**Por qué importa:** todo el análisis ocurre en el dispositivo, así que un correo que puede contener datos sensibles nunca se sube a un servicio de terceros.

---

## Las herramientas

| Herramienta | Pregunta que responde |
|---|---|
| **Analizador de cabeceras** | ¿Quién envió realmente este correo? |
| **Detector de homógrafos** | ¿El dominio imita a una marca con caracteres falsos? |
| **Expansor de enlaces** | ¿A dónde lleva de verdad este enlace corto? |
| **Verificador de archivos** | ¿El adjunto es lo que su extensión dice ser? |

Se encadenan en ese orden: el sobre, el dominio, el enlace y el adjunto.

### Analizador de cabeceras
Interpreta las cabeceras completas de un correo. Muestra semáforos de **SPF, DKIM, DMARC y ARC**, enfrenta `From` contra `Return-Path` y `Reply-To`, y dibuja la línea de tiempo de los saltos separando la zona verificable de la que no lo es. Reconoce reenviadores y servicios de alias (SimpleLogin, addy.io, Apple Private Relay y otros) para no marcar como fraude un correo legítimamente redirigido, apoyándose en `ARC-Authentication-Results` cuando existe.

### Detector de homógrafos
Detecta dominios que suplantan marcas mediante caracteres visualmente idénticos. Implementa el **algoritmo de esqueleto de Unicode TR39** con una tabla de ~180 confundibles, detecta caracteres invisibles, y compara contra un catálogo de marcas (globales y de España) con **distancia Damerau-Levenshtein**, combosquatting y vecindad de teclado QWERTY. Distingue un ataque real de un dominio internacionalizado legítimo, como `почта.рф`, donde el alfabeto es coherente y no hay engaño.

### Expansor de enlaces
Sigue la cadena de redirecciones de un enlace corto hasta su destino final y marca las señales de riesgo: acortador dentro de acortador, degradación a `http://`, IP cruda como destino, y distingue un bloqueo antibot (403) de una página caducada o retirada.

> **Nota de arquitectura:** el navegador no permite leer las redirecciones intermedias de una petición (*opaque redirects*), así que esta herramienta es híbrida: genera el comando `curl` que debes ejecutar y analiza la salida que le pegues. La red la hace la terminal; la interpretación, la herramienta.

### Verificador de archivos
Comprueba si un adjunto es lo que aparenta ser, en cuatro frentes:

- **Magic bytes vs extensión.** Compara la firma real del archivo con lo que promete su nombre. Caso principal: un `factura.pdf` que en realidad empieza por `MZ` no es un PDF, es un ejecutable de Windows. Muestra un careo explícito entre la firma esperada y los bytes encontrados, más un volcado hexadecimal con la firma resaltada.
- **Doble extensión.** Detecta el patrón `nomina.pdf.exe` por el nombre, sin depender de los bytes. Windows oculta por defecto las extensiones conocidas, así que la víctima solo ve `nomina.pdf`; la herramienta muestra qué vería el explorador y cuál es la extensión real.
- **Extensiones que ejecutan código.** Los scripts (`.bat`, `.vbs`, `.ps1`, `.hta`, `.js`, `.lnk`) no tienen firma binaria porque son texto, pero al abrirlos se ejecutan. Se avisa igualmente.
- **Contenido activo y macros.** Una coincidencia entre extensión y contenido significa que no hay disfraz, no que el archivo sea inofensivo: un PDF admite scripts, un XLSX puede consultar fuentes externas y un `.xlsm` está hecho para llevar macros. También detecta comprimidos protegidos con contraseña, que impiden el análisis por parte de los filtros de seguridad.

---

## Uso

Abre `index.html` en cualquier navegador. Es un único archivo autocontenido: incluye las cuatro herramientas y funciona sin conexión y sin instalar nada.

---

## Estructura del repositorio

```
index.html                ← el kit listo para usar (archivo generado)
construir_kit.py          ← script que genera el kit
herramientas/             ← código fuente de cada herramienta
    analizador-cabeceras.html
    expansor-acortados.html
    detector-homografos-v4.html
    verificador-archivos.html
```

**El kit es un archivo generado, no se edita a mano.** Su CSS lleva los ámbitos reescritos y su JavaScript va encapsulado: es funcional pero ilegible. Las herramientas de `herramientas/` son la fuente, y cada una funciona también por separado.

### Modificar una herramienta

1. Edita el archivo correspondiente en `herramientas/`
2. Ejecuta `python3 construir_kit.py` desde la raíz del repositorio
3. El script regenera `index.html` con el cambio incorporado

El script es determinista —partiendo de las mismas herramientas produce siempre un kit idéntico— y no necesita dependencias, solo Python 3.

---

## Decisiones técnicas

**Todo en local, sin dependencias.** Ninguna herramienta envía datos a ningún servidor. No hay librerías externas ni proceso de compilación: HTML, CSS y JavaScript en un archivo.

**Fusión sin iframes.** El lanzador une las cuatro herramientas en un documento. Como cada una traía sus propias variables, IDs y clases CSS repetidas, hacía falta aislarlas: el CSS de cada herramienta se reescribe con su ámbito (`#app0 .panel` en lugar de `.panel`) y cada bloque de JavaScript se envuelve en una función autoejecutable con un objeto `document` acotado a su contenedor. Así conviven ocho IDs duplicados sin colisión y **sin modificar el código original de ninguna herramienta**.

Se descartó la solución con `iframe`, más simple, porque los navegadores móviles bloquean la carga de archivos locales vecinos cuando la página se abre desde `file://` o `content://`.

---

## Limitaciones conocidas

- Las restricciones del navegador impiden seguir redirecciones sin ayuda de `curl` (ver nota de arquitectura).
- El detector de homógrafos compara contra un catálogo de marcas: una suplantación de una marca no incluida no se detecta. El catálogo es ampliable desde la propia interfaz.
- El verificador de archivos cubre las firmas más habituales, no todas las variantes de todos los formatos.
- Abierto desde `file://`, el almacenamiento local del navegador puede no persistir entre sesiones.

Estas herramientas son apoyo al análisis, no un veredicto automático. Ninguna sustituye el criterio del analista.

---

## Qué aprendí construyéndolo

- El **modelo de seguridad del navegador** deja de ser abstracto cuando te bloquea: opaque redirects, CORS y las restricciones de `file://` marcaron la arquitectura de tres de las cuatro herramientas.
- Un **falso positivo puede ser peor que un falso negativo** para la utilidad de una herramienta: la primera versión del detector marcaba como ataque cualquier dominio no latino, incluidos los legítimos. Distinguir "alfabeto distinto" de "alfabetos mezclados con intención de engañar" fue el cambio que la hizo usable.
- **Confirmar el tipo de archivo no es confirmar que sea seguro.** El verificador daba un verde tranquilizador cuando extensión y magic bytes coincidían, hasta que quedó claro que un PDF auténtico admite scripts y un XLSX legítimo puede conectarse al exterior. Un mensaje que induce a confiar de más es un fallo de la herramienta, aunque el análisis técnico sea correcto.
- **El aislamiento de componentes** (ámbito de CSS, encapsulado de JavaScript) resuelve el mismo problema que atacan el Shadow DOM y los frameworks modernos, y entenderlo a mano aclara por qué existen.
- **La verificación tiene que ser específica.** Al fundir las herramientas, todo parecía correcto hasta que comprobé una cosa concreta: si cada una conservaba sus variables de color. Un comentario pegado a un selector estaba generando `#app0 :root`, que no coincide con nada, y habría dejado una herramienta sin estilos.
- **Un artefacto generado necesita que su generador viva con él.** El kit se creaba con un script que quedaba fuera del proyecto, así que actualizar una herramienta habría obligado a rehacer la fusión a mano. Versionar el script junto al resultado es lo que hace el proyecto mantenible.

---

## Licencia

MIT — ver [LICENSE](LICENSE).
