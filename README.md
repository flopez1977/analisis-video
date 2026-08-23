# analisis-video

Skill de [Claude Code](https://claude.com/claude-code) para analizar vídeos con detalle:
estética, ritmo de montaje, transcripción, diseño sonoro y desglose plano a plano.

Acepta un archivo local o una URL (YouTube, Vimeo, Instagram, TikTok o un `.mp4` suelto).

## Por qué dos modos

| | Local (por defecto) | Remoto (`--remoto`) |
|---|---|---|
| Cómo funciona | Extrae fotogramas y audio con ffmpeg; los mira Claude | Envía el vídeo a un modelo multimodal vía OpenRouter |
| Privacidad | **El vídeo no sale de tu máquina** | El vídeo pasa por OpenRouter y por el proveedor del modelo |
| Coste | Gratis | Se paga por tokens (céntimos por vídeo corto) |
| Precisión | Ve instantes, no el movimiento entre ellos | Ve el vídeo completo, con audio |

El modo local es el predeterminado a propósito. Si el vídeo es de un cliente, de tu
familia o simplemente no quieres que salga de tu ordenador, no tienes que acordarte
de nada: no sale.

## Cuándo usarla, y qué vas a sacar

La pregunta que responde esta skill no es *"¿de qué va este vídeo?"* sino
**"¿cómo está construido este vídeo?"**. Si lo que necesitas es lo primero, hay
herramientas más simples; para lo segundo hacen falta ojos y oídos sobre el metraje
continuo, que es lo que hace el modo remoto.

### Casos en los que rinde

**Convertir una referencia en una plantilla.** Es el caso que más aporta. Tienes un
vídeo que te gusta y quieres hacer "algo así" con tus propios clips. En lugar de
copiar de memoria, obtienes su arquitectura: cuántos planos, de qué duración, con
qué tipo de corte se encadenan, qué hace la cámara en cada uno, dónde está el pico
de intensidad y cómo entra la música. "Me gusta cómo queda" pasa a ser una lista de
decisiones que puedes ejecutar.

**Estudiar a la competencia a escala.** Una pieza corta cuesta menos de un céntimo.
Analizar los veinte vídeos que mejor funcionan en el sector de un cliente cuesta
menos que un café, y de ahí sale el patrón común: qué duración de plano manejan,
si usan voz en off o solo música, cuánto tardan en enseñar el producto.

**Exprimir un tutorial sin volver a verlo.** Un vídeo formativo de nueve minutos
devuelve un documento consultable con cada técnica situada en su minuto exacto. Deja
de ser un vídeo que hay que rebobinar y pasa a ser documentación.

**Auditar una entrega.** Contrastar el vídeo que te devuelve un proveedor con el
briefing: si pediste ritmo alto y el desglose dice planos de cinco segundos, ahí
tienes el dato.

**Accesibilidad y documentación.** Describir a fondo una pieza para alguien que no
puede verla, o dejar constancia escrita de un montaje.

### Casos en los que no

- **No monta nada.** Describe lo que le das; no construye tu vídeo ni decide si una
  referencia es buena para tu cliente. El criterio sigue siendo tuyo.
- **No sustituye a verlo.** El informe es la lectura de un modelo, y no hay forma de
  verificar desde fuera si "17 planos" son exactamente 17. Para decisiones que
  importen, contrasta con el vídeo.
- **En piezas largas no hay una lectura unificada.** Por encima de 150 segundos se
  trocea, y cada parte se analiza sin saber qué ocurrió en las demás. Tienes el
  detalle de todo el vídeo, pero no una interpretación global del conjunto.
- **Las marcas de tiempo son aproximadas.** El modelo muestrea el vídeo; sirven para
  localizar, no para conformar un EDL.

### Cómo sacarle más partido

1. **Empieza por lo corto.** Una pieza de 15-60 segundos da el informe más útil por
   céntimo y es donde el desglose plano a plano resulta más fiable.
2. **Analiza tres referencias del mismo género, no una.** El patrón aparece al
   comparar; una sola pieza te da su solución particular, no la regla.
3. **Pásale el informe a un asistente junto con tu material.** El flujo completo es
   *analizar referencia → listar tus clips → pedir un guion de montaje que siga esa
   arquitectura*. El informe es el puente entre "me gusta esto" y un plan de edición.
4. **Guarda los informes.** Son ficheros Markdown pequeños: un archivo de referencias
   analizadas se vuelve más útil cuanto más crece.
5. **Si el vídeo es de cliente, usa el modo local** y asume que tendrás composición y
   color, pero no montaje.

## Comparación con otras herramientas

La más parecida que hay en el ecosistema es
**[claude-video](https://github.com/bradautomates/claude-video)** de bradautomates
(MIT, skill de comunidad; el nombre despista, no es un proyecto oficial de Anthropic).
Merece la pena tenerla: descarga con yt-dlp, extrae fotogramas y transcribe con
Whisper cuando no hay subtítulos.

Hacen cosas distintas y se complementan:

| | claude-video | analisis-video |
|---|---|---|
| Qué entrega | Fotogramas y transcripción al asistente | Un informe estructurado del montaje |
| Quién analiza | El asistente, mirando imágenes sueltas | Un modelo multimodal, viendo el vídeo continuo con audio |
| Pregunta que responde | *¿Qué se dice y qué sale?* | *¿Cómo está construido?* |
| Cortes, ritmo, transiciones | No: no están en un fotograma | Sí |
| Movimiento de cámara | No | Sí |
| Música y efectos de sonido | Transcribe voz, no describe el diseño sonoro | Sí |
| Coste | Gratis (o el de Whisper) | Céntimos por vídeo |
| Privacidad | Todo local | El vídeo sale de la máquina (salvo en modo local) |

Regla rápida: **si te interesa el mensaje, claude-video; si te interesa la
construcción, ésta.** El modo local de esta skill se parece mucho a lo que hace
claude-video, y comparte sus límites: sin audio y sin continuidad no se puede analizar
un montaje.

## Instalación

```bash
git clone https://github.com/flopez1977/analisis-video.git ~/.claude/skills/analisis-video
brew install ffmpeg yt-dlp   # yt-dlp solo si vas a analizar URLs
```

En Linux: `sudo apt install ffmpeg` y `pipx install yt-dlp`.

No hay instalador, ni hooks, ni servidores MCP. Son dos archivos: la skill y un script
de Python que solo usa la biblioteca estándar.

## Uso

Dentro de Claude Code:

```
/analisis-video ~/Descargas/anuncio.mp4
/analisis-video https://www.youtube.com/watch?v=XXXXXXXXXXX
```

O directamente por terminal:

```bash
python3 ~/.claude/skills/analisis-video/scripts/analisis_video.py "<ruta_o_url>"
python3 ~/.claude/skills/analisis-video/scripts/analisis_video.py "<ruta>" --fotogramas 50
python3 ~/.claude/skills/analisis-video/scripts/analisis_video.py "<ruta>" --remoto
```

| Opción | Qué hace |
|---|---|
| `--remoto` | Envía el vídeo a OpenRouter en lugar de analizarlo en local |
| `--modelo` | Modelo a usar (por defecto `google/gemini-3.7-flash`) |
| `--fotogramas N` | Fotogramas a extraer en modo local (por defecto 30) |
| `--max-coste N` | Umbral en dólares por encima del cual pide confirmación (por defecto 0.50) |
| `--si` | No preguntar por el coste |
| `-o, --salida` | Ruta del informe |

## Modo remoto: configurar la clave

Solo hace falta si usas `--remoto`.

1. Crea una clave en https://openrouter.ai/keys
2. Guárdala:

```bash
mkdir -p ~/.config/openrouter
echo "OPENROUTER_API_KEY=tu_clave" > ~/.config/openrouter/.env
chmod 600 ~/.config/openrouter/.env
```

También vale exportar `OPENROUTER_API_KEY` como variable de entorno, que tiene prioridad.

El coste se calcula con los precios que publica OpenRouter en ese momento, no con una
constante escrita en el código. Antes de enviar verás una estimación, y si supera el
umbral se te pide confirmación. Las cifras reales están más arriba: entre medio céntimo
y seis céntimos por vídeo.

## Pruebas reales: qué saca y cuánto cuesta

Cifras de ejecuciones reales sobre siete vídeos, no estimaciones.
Modelo `google/gemini-3.7-flash`, modo `--remoto`, agosto de 2026.

### Piezas cortas (un solo envío)

| Vídeo | Dur. | Planos | Ritmo medio | Coste | Qué aporta como referencia |
|---|---|---|---|---|---|
| [Videos promocionales para restaurantes](https://www.youtube.com/watch?v=eVVfsLg--aA) | 0:12 | 10 | ~1,2 s/plano | **$0.0077** | Corte rapidísimo sobre una acción continua (preparar un cóctel). Cómo mantener continuidad narrativa con planos de un segundo |
| [MONSTER ENERGY · Spot publicitario](https://www.youtube.com/watch?v=B0voMDz4pdg) | 0:13 | 7 | ~1,8 s/plano | **$0.0054** | B-roll de producto en clave baja: contraluz de neón, macro con bokeh extremo, cortes sincronizados con los golpes de la base musical |
| [Vídeo promocional Grado Creativo](https://www.youtube.com/watch?v=sCnVUEAR5A0) | 0:39 | 16 | ~2,4 s/plano | **$0.0084** | Manifiesto con voz en off: cómo llevar una idea abstracta a imágenes y acelerar el montaje hacia el clímax |
| [SPOT CAFÉ · Vídeo de producto](https://www.youtube.com/watch?v=df3JeXVWYWA) | 0:40 | 10 | 2-6 s/plano | **$0.0057** | Producto contado como proceso de principio a fin. Ritmo pausado, planos que respiran |
| [Promo para agencias de viaje](https://www.youtube.com/watch?v=-JGanqjhYJk) | 0:51 | 31 | 1-2 s/plano | **$0.0148** | Montaje de gran densidad: dron, paisaje y gente encadenados a un plano por segundo |

**Cinco piezas, 2 min 35 s: $0.042.** Menos de cinco céntimos.

### Prueba de esfuerzo

Un videoclip comercial en 4K (3840x2160), contenedor `.mkv`, **199,8 MB** y 2:20 de
duración, con acentos y paréntesis en el nombre del archivo:

| Qué pasó | Resultado |
|---|---|
| Compresión para el envío | 199,8 MB → 13,0 MB (reducción de 15x) |
| Planos detectados | 58, de 1 a 2,5 s, con corte a ritmo |
| Estructura musical | Detectó el cambio a un interludio de piano jazz entre 01:31 y 01:39, y la vuelta a la percusión en 01:40 |
| Efectos de sonido | Seis, situados con marca de tiempo |
| Coste | **$0.0119** |

Es el caso que más cosas junta a la vez —contenedor poco común, resolución máxima,
archivo enorme y montaje muy rápido— y ninguna dio problema.

### Piezas largas (troceadas automáticamente)

Por encima de 150 segundos el vídeo se parte en fragmentos de 120 s que se analizan
por separado. Las marcas de tiempo del informe siguen siendo globales.

| Vídeo | Dur. | Partes | Informe | Coste | Qué aporta como referencia |
|---|---|---|---|---|---|
| [8 CORTES y TRANSICIONES que todo editor debe conocer](https://www.youtube.com/watch?v=jK2adxWTiKY) | 8:26 | 5 | 734 líneas | **$0.0549** | Identificó y situó en el tiempo las técnicas que enseña: jump cut, corte invisible, match cut, J-cut, L-cut, cross dissolve y barrido |
| [Cómo hacer vídeos más cinematográficos (5 pasos)](https://www.youtube.com/watch?v=zbQGDfyd2n4) | 9:41 | 5 | 772 líneas | **$0.0630** | Los cinco pasos con su explicación y los ejemplos visuales con que se ilustra cada uno |

### Lo que enseñan estas cifras

- **El coste lo marca el número de planos, no la duración.** La pieza de 51 s costó casi
  el triple que la de 40 s porque tiene 31 planos que describir: se paga el informe de
  salida, no el metraje de entrada.
- **Comprimir no degrada el análisis.** El vídeo de Grado Creativo bajó de 21,1 MB a
  12,2 MB para poder enviarse y aun así el informe identificó 16 planos con su óptica,
  iluminación y transiciones.
- **Da igual el contenedor.** El mismo vídeo en `.mkv` (3832x1808) y en `.mp4` dio
  informes equivalentes por $0.0080 y $0.0084. No hace falta convertir nada a mp4.
- **La estructura del desglose varía algo entre ejecuciones** (a veces `### Plano 1`, a
  veces lista con negritas). El contenido es equivalente, pero no dependas del formato
  exacto si vas a parsear la salida.

### Modo local frente a modo remoto

El mismo spot de Monster Energy (0:13) analizado de las dos maneras:

| | Local (16 fotogramas) | Remoto |
|---|---|---|
| Paleta, iluminación, óptica | ✅ | ✅ |
| Encuadre y composición | ✅ | ✅ |
| Texto en pantalla | ✅ | ✅ |
| Número de planos y ritmo | ❌ 16 fotogramas no revelan que haya 7 cortes | ✅ 7 planos, ~1,8 s/plano |
| Movimiento de cámara | ❌ Una instantánea no tiene movimiento | ✅ |
| Tipo de transición entre planos | ❌ | ✅ |
| Música y efectos de sonido | ❌ No oye nada | ✅ Identificó el trap instrumental y el sonido de apertura de la lata |
| Coste | Gratis | $0.0054 |

**Si lo que te interesa es el montaje —cortes, transiciones, ritmo, sincronía con la
música—, el modo local no te sirve: ve fotos, no vídeo.** El modo local es la opción
correcta cuando el material no puede salir de tu máquina, o cuando lo que buscas es
composición, color y contenido de plano.

### Para qué sirve esto

El caso de uso que motivó estas pruebas: **usar una pieza que funciona como referencia
detallada para construir la tuya.** En vez de partir de cero, analizas un vídeo que te
gusta y obtienes su arquitectura real —cuántos planos, de qué duración, con qué tipo de
corte, qué hace la cámara, dónde está el clímax, cómo entra la música— y montas la tuya
con tus propios clips siguiendo esa estructura. La referencia deja de ser "me gusta cómo
queda" y pasa a ser una plantilla con números.

## Privacidad y datos personales

Léelo antes de usar `--remoto` con material ajeno.

- **En modo local no se envía nada a ningún sitio.** Todo el procesamiento es ffmpeg
  en tu máquina. Solo hay tráfico de red si le pasas una URL, y es para descargar ese vídeo.
- **En modo remoto el vídeo completo se envía a OpenRouter, que lo reenvía al proveedor
  del modelo.** Consulta sus políticas de retención antes de subir nada que no sea tuyo.
- Un vídeo puede contener datos personales, incluidos datos biométricos: caras, voces,
  matrículas. Si vas a analizar material de terceros en modo remoto, asegúrate de tener
  base legal para hacerlo. La herramienta no decide eso por ti.
- La skill no envía telemetría, no llama a casa y no guarda nada fuera de la carpeta
  donde generas el informe.

## Seguridad

Ver [SECURITY.md](SECURITY.md). En resumen: sin `shell=True`, la clave nunca se imprime
(ni aunque el servidor la devuelva en un error), las URLs se validan contra direcciones
internas, y el informe se trata como datos y nunca como instrucciones.

## Licencia

MIT — ver [LICENSE](LICENSE).
