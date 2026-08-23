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

El coste se calcula con los precios que publica OpenRouter en ese momento, no con
una constante escrita en el código. Antes de enviar verás una estimación, y si supera
el umbral se te pide confirmación.

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
