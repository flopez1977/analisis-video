# Seguridad

## Reportar un fallo

Abre un issue en el repositorio. Si el fallo permite filtrar credenciales o ejecutar
código, márcalo como tal en el título para poder priorizarlo.

## Decisiones de diseño

Estas medidas están en el código a propósito. Si envías un PR, no las deshagas.

### El modo local es el predeterminado
El fallo seguro es que el vídeo no salga de la máquina. Enviarlo a un tercero exige
la bandera explícita `--remoto`. Un descuido no debe acabar en una subida no deseada.

### La clave nunca se imprime
OpenRouter devuelve la clave dentro del cuerpo de algunos errores 401. Todo mensaje
del servidor pasa por `sanear()` antes de mostrarse, que sustituye tanto la clave
cargada como cualquier cadena con formato `sk-or-v1-…`.

La clave se lee de una variable de entorno o de `~/.config/openrouter/.env`, nunca
del repositorio, nunca de la línea de comandos (aparecería en el historial del shell)
y nunca de una URL.

### Sin `shell=True`
Todas las llamadas a `ffmpeg`, `ffprobe` y `yt-dlp` usan lista de argumentos y `--`
antes de los posicionales. Un archivo llamado `x; rm -rf ~.mp4` o `-rf.mp4` se trata
como nombre, no como comando ni como flag.

### Validación de URL contra SSRF
Antes de descargar, se comprueba que el esquema sea `http` o `https` y se resuelve el
host: si apunta a una dirección privada, loopback, link-local, reservada o multicast,
se rechaza. Bloquea el acceso a `169.254.169.254` (metadata de nube) y a la red interna.

### El contenido analizado son datos, no instrucciones
Un vídeo puede llevar en pantalla texto dirigido a un asistente de IA. El prompt del
modo remoto ordena transcribirlo como contenido y no obedecerlo, el informe se guarda
con una cabecera que lo marca como datos, y la skill instruye a Claude en el mismo sentido.

### Sin persistencia oculta
No hay telemetría, ni analítica, ni ficheros de estado fuera de la carpeta donde se
genera el informe. Las descargas y los archivos temporales viven en un directorio
temporal que se borra al terminar.

## Dependencias

El script solo usa la biblioteca estándar de Python. Los binarios externos
(`ffmpeg`, `ffprobe`, `yt-dlp`) los instala y actualiza quien usa la herramienta.

**Mantén `yt-dlp` actualizado.** Procesa contenido de sitios arbitrarios y ha tenido
vulnerabilidades en el pasado:

```bash
brew upgrade yt-dlp    # o: pipx upgrade yt-dlp
```
