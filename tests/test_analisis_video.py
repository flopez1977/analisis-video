#!/usr/bin/env python3
"""Pruebas de analisis-video. No hacen ninguna llamada a la API: son gratis.

    python3 tests/test_analisis_video.py

Requieren ffmpeg. El vídeo de prueba se genera al vuelo.
"""
import os
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import analisis_video as av  # noqa: E402


def video_de_prueba(destino, segundos=6, bitrate=None):
    ruta = os.path.join(destino, f"prueba_{segundos}_{bitrate}.mp4")
    subprocess.run(
        ["ffmpeg", "-y", "-f", "lavfi", "-i",
         f"testsrc=duration={segundos}:size=640x360:rate=25",
         "-f", "lavfi", "-i", f"sine=frequency=440:duration={segundos}",
         "-c:v", "libx264", *(["-b:v", bitrate] if bitrate else []),
         "-c:a", "aac", "-shortest",
         "-hide_banner", "-loglevel", "error", ruta],
        check=True,
    )
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


class DeteccionDeOrigen(unittest.TestCase):
    """Rutas locales y URLs http(s); cualquier otro esquema se rechaza."""

    def test_acepta_http_y_https(self):
        self.assertTrue(av.es_url("https://ejemplo.com/v.mp4"))
        self.assertTrue(av.es_url("http://ejemplo.com/v.mp4"))

    def test_ruta_local_no_es_url(self):
        self.assertFalse(av.es_url("/tmp/video.mp4"))
        self.assertFalse(av.es_url("clip 1:2 final.mp4"))  # ':' que no es esquema

    def test_rechaza_otros_esquemas(self):
        for mala in ("file:///etc/passwd", "gopher://x/1", "ftp://x/a.mp4"):
            with self.subTest(url=mala), self.assertRaises(SystemExit):
                av.es_url(mala)


class AntiSSRF(unittest.TestCase):
    """No debe poder usarse para alcanzar la red interna."""

    def test_rechaza_metadatos_de_nube(self):
        with self.assertRaises(SystemExit):
            av.validar_url("http://169.254.169.254/latest/meta-data/")

    def test_rechaza_loopback(self):
        with self.assertRaises(SystemExit):
            av.validar_url("http://localhost:8080/x")

    def test_rechaza_red_privada(self):
        with self.assertRaises(SystemExit):
            av.validar_url("http://192.168.1.1/")


class Ffmpeg(unittest.TestCase):
    """Comprimir y trocear, que es donde se rompió el análisis de vídeos largos."""

    @classmethod
    def setUpClass(cls):
        if not av.shutil.which("ffmpeg"):
            raise unittest.SkipTest("ffmpeg no está instalado")

    def test_comprimir_baja_del_limite(self):
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t, bitrate="3M")
            limite = av.MAX_BYTES_CRUDOS
            try:
                # Límite artificialmente bajo para recorrer la ruta de compresión
                # sin generar un vídeo de decenas de megas. 500 KB para 6 s deja
                # sitio de sobra por encima del suelo de calidad.
                av.MAX_BYTES_CRUDOS = 500_000
                salida = av.comprimir(ruta, t)
                self.assertLessEqual(os.path.getsize(salida), 500_000)
                self.assertLess(os.path.getsize(salida), os.path.getsize(ruta))
            finally:
                av.MAX_BYTES_CRUDOS = limite

    def test_comprimir_se_niega_antes_que_destrozar_el_video(self):
        """Si el objetivo obliga a bajar del suelo de calidad, aborta.

        Es preferible a enviar un vídeo ilegible del que no se puede sacar
        ningún análisis útil: quien lo ejecuta prefiere un error claro.
        """
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t)
            limite = av.MAX_BYTES_CRUDOS
            try:
                av.MAX_BYTES_CRUDOS = 20_000  # imposible para 6 s con audio
                with self.assertRaises(SystemExit):
                    av.comprimir(ruta, t)
            finally:
                av.MAX_BYTES_CRUDOS = limite

    def test_trocear_cubre_todo_el_video(self):
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t, segundos=10)
            trozos = av.trocear(ruta, t, 4)
            self.assertEqual([int(i) for i, _ in trozos], [0, 4, 8])
            for _, fragmento in trozos:
                self.assertGreater(os.path.getsize(fragmento), 0)

    def test_fotogramas_llevan_su_marca_de_tiempo(self):
        with tempfile.TemporaryDirectory() as t:
            ruta = video_de_prueba(t)
            duracion, fotogramas = av.extraer_fotogramas(ruta, os.path.join(t, "f"), 4)
            self.assertAlmostEqual(duracion, 6, delta=1)
            self.assertEqual(len(fotogramas), 4)
            for instante, archivo in fotogramas:
                self.assertIn(av.marca_tiempo(instante), os.path.basename(archivo))


class PromptDeFragmento(unittest.TestCase):
    """Las marcas de tiempo de un trozo deben referirse al vídeo completo."""

    def test_incluye_el_desfase(self):
        p = av.prompt_con_desfase(240, 600)
        self.assertIn("240", p)
        self.assertIn("04m00s", p)
        self.assertIn(av.PROMPT, p)


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


if __name__ == "__main__":
    unittest.main(verbosity=2)
