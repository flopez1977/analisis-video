#!/usr/bin/env python3
"""Pruebas de analisis-video. No hacen ninguna llamada a la API: son gratis.

    python3 tests/test_analisis_video.py

Requieren ffmpeg. Los vídeos de prueba se generan al vuelo.
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from unittest import mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import analisis_video as av  # noqa: E402


def video_de_prueba(destino, segundos=6, bitrate=None, gop=None, nombre=None):
    ruta = os.path.join(destino, nombre or f"prueba_{segundos}_{bitrate}_{gop}.mp4")
    orden = [
        "ffmpeg", "-y", "-f", "lavfi", "-i",
        f"testsrc=duration={segundos}:size=320x180:rate=25",
        "-f", "lavfi", "-i", f"sine=frequency=440:duration={segundos}",
        "-c:v", "libx264",
    ]
    if bitrate:
        orden += ["-b:v", bitrate]
    if gop:
        orden += ["-g", str(gop), "-keyint_min", str(gop), "-sc_threshold", "0"]
    orden += ["-c:a", "aac", "-shortest", "-hide_banner", "-loglevel", "error", ruta]
    subprocess.run(orden, check=True)
    return ruta


class Saneado(unittest.TestCase):
    """La clave no debe poder aparecer en ningún mensaje."""

    def test_oculta_la_clave_cargada(self):
        clave = "sk-or-v1-" + "a" * 64
        self.assertNotIn(clave, av.sanear(f"Invalid key: {clave} rejected", clave))

    def test_oculta_cualquier_clave_con_ese_formato(self):
        otra = "sk-or-v1-" + "b" * 64
        self.assertNotIn(otra, av.sanear(f"error {otra}", "clave-distinta"))

    def test_no_rompe_con_texto_vacio(self):
        self.assertEqual(av.sanear("", "x"), "")
        self.assertIsNone(av.sanear(None, "x"))


class ClaveEnErroresHttp(unittest.TestCase):
    """OpenRouter devuelve la clave dentro del cuerpo de algunos errores 401.

    Es el camino por el que más fácilmente se filtraría, así que se prueba de
    extremo a extremo y no solo la función de saneado.
    """

    def test_un_401_con_la_clave_dentro_no_la_imprime(self):
        clave = "sk-or-v1-" + "c" * 64
        cuerpo = json.dumps({"error": {"message": f"Invalid key {clave}"}}).encode()
        error = urllib.error.HTTPError(av.API_URL, 401, "Unauthorized", {},
                                       io.BytesIO(cuerpo))
        with mock.patch("urllib.request.urlopen", side_effect=error), \
             mock.patch.object(av, "a_data_url", return_value="data:video/mp4;base64,AA"):
            capturado = io.StringIO()
            with mock.patch("sys.stderr", capturado), self.assertRaises(SystemExit):
                av.preguntar_al_modelo("x.mp4", "modelo", clave, "prompt")
            self.assertNotIn(clave, capturado.getvalue())
            self.assertIn("CLAVE-OCULTA", capturado.getvalue())


class DeteccionDeOrigen(unittest.TestCase):
    def test_acepta_http_y_https(self):
        self.assertTrue(av.es_url("https://ejemplo.com/v.mp4"))
        self.assertTrue(av.es_url("http://ejemplo.com/v.mp4"))

    def test_ruta_local_no_es_url(self):
        self.assertFalse(av.es_url("/tmp/video.mp4"))
        self.assertFalse(av.es_url("clip 1:2 final.mp4"))

    def test_rechaza_otros_esquemas(self):
        for mala in ("file:///etc/passwd", "gopher://x/1", "ftp://x/a.mp4"):
            with self.subTest(url=mala), self.assertRaises(SystemExit):
                av.es_url(mala)


class AntiSSRF(unittest.TestCase):
    """No debe poder usarse para alcanzar la red interna."""

    def _resolviendo_a(self, ip):
        familia = 10 if ":" in ip else 2
        return mock.patch("socket.getaddrinfo",
                          return_value=[(familia, 1, 6, "", (ip, 0))])

    def test_rechaza_destinos_no_publicos(self):
        internas = [
            "169.254.169.254",  # metadatos de nube
            "127.0.0.1",        # loopback
            "192.168.1.1",      # red doméstica
            "10.0.0.1",         # red privada
            "100.64.0.1",       # CGNAT, donde vive Tailscale
            "0.0.0.0",
            "::1",
        ]
        for ip in internas:
            with self.subTest(ip=ip), self._resolviendo_a(ip):
                with self.assertRaises(SystemExit):
                    av.validar_url("http://ejemplo-de-prueba.invalid/x")

    def test_acepta_una_ip_publica(self):
        with self._resolviendo_a("93.184.216.34"):
            self.assertTrue(av.validar_url("https://ejemplo-de-prueba.invalid/v.mp4"))


class BarreraDeCoste(unittest.TestCase):
    """Sin precio no se puede estimar, y entonces hay que preguntar.

    Continuar en silencio dejaría al usuario pagando envíos que no ha aprobado.
    """

    def test_si_no_hay_precio_pregunta(self):
        with mock.patch.object(av, "precios_del_modelo", return_value=(None, None)), \
             mock.patch("builtins.input", return_value="n") as preguntado, \
             mock.patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit):
                av.confirmar_coste(600, "modelo", 0.5, asumir_si=False)
            preguntado.assert_called_once()

    def test_con_si_no_pregunta(self):
        with mock.patch.object(av, "precios_del_modelo", return_value=(None, None)), \
             mock.patch("builtins.input") as preguntado, \
             mock.patch("sys.stderr", io.StringIO()):
            av.confirmar_coste(600, "modelo", 0.5, asumir_si=True)
            preguntado.assert_not_called()

    def test_por_encima_del_umbral_pregunta(self):
        with mock.patch.object(av, "precios_del_modelo", return_value=(1e-3, 1e-3)), \
             mock.patch("builtins.input", return_value="n") as preguntado, \
             mock.patch("sys.stderr", io.StringIO()):
            with self.assertRaises(SystemExit):
                av.confirmar_coste(600, "modelo", 0.01, asumir_si=False)
            preguntado.assert_called_once()


class PlanDeTrozos(unittest.TestCase):
    def test_cubre_la_duracion_entera_sin_perder_la_cola(self):
        tramos = av.plan_de_trozos(250.9, 120)
        self.assertEqual(len(tramos), 3)
        self.assertAlmostEqual(tramos[-1][0] + tramos[-1][1], 250.9, places=3)

    def test_no_genera_un_tramo_residual(self):
        self.assertEqual(len(av.plan_de_trozos(240.05, 120)), 2)

    def test_video_mas_corto_que_el_trozo(self):
        self.assertEqual(av.plan_de_trozos(30, 120), [(0.0, 30)])


class Ffmpeg(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not av.shutil.which("ffmpeg"):
            raise unittest.SkipTest("ffmpeg no está instalado")

    def test_comprimir_baja_del_limite(self):
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t, bitrate="3M")
            limite = av.MAX_BYTES_CRUDOS
            try:
                av.MAX_BYTES_CRUDOS = 500_000
                salida = av.comprimir(ruta, t)
                self.assertLessEqual(os.path.getsize(salida), 500_000)
            finally:
                av.MAX_BYTES_CRUDOS = limite

    def test_comprimir_se_niega_antes_que_destrozar_el_video(self):
        """Mejor un error claro que un vídeo ilegible del que no sale análisis."""
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t)
            limite = av.MAX_BYTES_CRUDOS
            try:
                av.MAX_BYTES_CRUDOS = 20_000
                with mock.patch("sys.stderr", io.StringIO()):
                    with self.assertRaises(SystemExit):
                        av.comprimir(ruta, t)
            finally:
                av.MAX_BYTES_CRUDOS = limite

    def test_el_fragmento_empieza_donde_dice_aunque_el_gop_sea_largo(self):
        """El corte tiene que ser exacto, no saltar al keyframe anterior.

        Con copia de flujo, un fragmento anunciado como "empieza en el segundo
        12" puede empezar en el 0 si el keyframe más cercano está ahí. Entonces
        el desfase que se le anuncia al modelo es falso y todas las marcas de
        tiempo del informe salen desplazadas.
        """
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t, segundos=20, gop=250)  # un solo keyframe
            fragmento = av.preparar_fragmento(ruta, t, inicio=12.0, segundos=6, indice=1)
            duracion = av.duracion_segundos(fragmento)
            self.assertAlmostEqual(duracion, 6, delta=0.7,
                                   msg="el fragmento no dura lo pedido: el corte "
                                       "no fue exacto y hay metraje solapado")

    def test_fotogramas_llevan_su_marca_de_tiempo(self):
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t)
            duracion, fotogramas = av.extraer_fotogramas(ruta, os.path.join(t, "f"), 4)
            self.assertAlmostEqual(duracion, 6, delta=1)
            self.assertEqual(len(fotogramas), 4)
            for instante, archivo in fotogramas:
                self.assertIn(av.marca_tiempo(instante), os.path.basename(archivo))

    def test_no_borra_archivos_ajenos_de_la_carpeta_de_fotogramas(self):
        """La carpeta se deriva del nombre de salida y puede ser del usuario."""
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t)
            carpeta = os.path.join(t, "frames")
            os.makedirs(carpeta)
            ajeno = os.path.join(carpeta, "documento-importante.txt")
            with open(ajeno, "w") as f:
                f.write("no me borres")
            viejo = os.path.join(carpeta, "frame_099_99m99s.jpg")
            open(viejo, "w").close()

            av.extraer_fotogramas(ruta, carpeta, 2)

            self.assertTrue(os.path.exists(ajeno), "borró un archivo del usuario")
            self.assertFalse(os.path.exists(viejo), "no limpió un fotograma antiguo")

    def test_duracion_ilegible_da_error_claro(self):
        with tempfile.TemporaryDirectory() as t:
            falso = os.path.join(t, "roto.mp4")
            with open(falso, "wb") as f:
                f.write(b"esto no es un video")
            with mock.patch("sys.stderr", io.StringIO()):
                with self.assertRaises(SystemExit):
                    av.duracion_segundos(falso)


class Subtitulos(unittest.TestCase):
    def test_prefiere_el_idioma_en_orden_de_preferencia(self):
        with tempfile.TemporaryDirectory() as t:
            for idioma, frase in (("en", "hello there"), ("es", "hola que tal")):
                with open(os.path.join(t, f"video.{idioma}.vtt"), "w",
                          encoding="utf-8") as f:
                    f.write(f"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n{frase}\n")
            lineas = av.subtitulos_a_texto(t)
            self.assertEqual(lineas[0][1], "hola que tal")

    def test_sin_subtitulos_devuelve_none(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertIsNone(av.subtitulos_a_texto(t))


class PromptDeFragmento(unittest.TestCase):
    def test_incluye_el_desfase(self):
        p = av.prompt_con_desfase(240, 600)
        self.assertIn("240", p)
        self.assertIn("04m00s", p)
        self.assertIn(av.PROMPT, p)


class Clave(unittest.TestCase):
    def test_la_variable_de_entorno_tiene_prioridad(self):
        with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": "desde-entorno"}):
            self.assertEqual(av.cargar_clave(), "desde-entorno")

    def test_lee_del_fichero_y_quita_comillas(self):
        with tempfile.TemporaryDirectory() as t:
            env = os.path.join(t, ".env")
            with open(env, "w") as f:
                f.write('# comentario\nOPENROUTER_API_KEY="secreto-entrecomillado"\n')
            with mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}), \
                 mock.patch.object(av, "ENV_PATH", env):
                self.assertEqual(av.cargar_clave(), "secreto-entrecomillado")


class NombreDeSalida(unittest.TestCase):
    def test_titulo_se_convierte_en_nombre_de_archivo(self):
        with tempfile.TemporaryDirectory() as t:
            with open(os.path.join(t, "video.info.json"), "w", encoding="utf-8") as f:
                f.write('{"title": "Un Título: con / caracteres raros"}')
            nombre = av.titulo_descargado(t)
            self.assertNotIn("/", nombre)
            self.assertNotIn(":", nombre)
            self.assertTrue(nombre)

    def test_sin_info_json_devuelve_video(self):
        with tempfile.TemporaryDirectory() as t:
            self.assertEqual(av.titulo_descargado(t), "video")


class ComprobacionDeEntorno(unittest.TestCase):
    """--comprobar informa de lo que falta y nunca revela la clave."""

    def test_detecta_lo_que_falta_y_no_instala(self):
        salida = io.StringIO()
        with mock.patch.object(av.shutil, "which", return_value=None), \
             mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}), \
             mock.patch.object(av, "ENV_PATH", "/no/existe/.env"), \
             mock.patch("sys.stdout", salida):
            codigo = av.comprobar_entorno()
        texto = salida.getvalue()
        self.assertEqual(codigo, 1)
        for binario in ("ffmpeg", "ffprobe", "yt-dlp"):
            self.assertIn(binario, texto)
        self.assertIn("No se instala nada automáticamente", texto)

    def test_no_imprime_el_valor_de_la_clave(self):
        clave = "sk-or-v1-" + "d" * 64
        salida = io.StringIO()
        with mock.patch.object(av.shutil, "which", return_value="/usr/bin/x"), \
             mock.patch.dict(os.environ, {"OPENROUTER_API_KEY": clave}), \
             mock.patch("sys.stdout", salida):
            codigo = av.comprobar_entorno()
        self.assertEqual(codigo, 0)
        self.assertNotIn(clave, salida.getvalue())
        self.assertIn("configurada", salida.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
