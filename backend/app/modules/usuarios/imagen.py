"""Validación y normalización de la foto de perfil.

No se confía en el nombre, la extensión ni el Content-Type que declara el cliente: se abre el archivo con
Pillow, se comprueba el formato real y se RE-CODIFICA a un JPEG cuadrado de 512 px. Re-codificar elimina
metadatos (EXIF/GPS) y cualquier contenido extra que alguien hubiera escondido dentro del archivo.
"""
import io
import warnings

from PIL import Image, ImageOps, UnidentifiedImageError

from app.core.errors import ErrorDominio, ErrorValidacion

TAMANO_MAX_BYTES = 5 * 1024 * 1024  # archivo subido
LADO_SALIDA = 512
MAX_PIXELES = 40_000_000  # protección contra "bombas de descompresión"
FORMATOS_PERMITIDOS = {"JPEG", "PNG", "WEBP"}
TIPO_SALIDA = "image/jpeg"


class ArchivoDemasiadoGrande(ErrorDominio):
    status_code = 413
    codigo_defecto = "FOTO_DEMASIADO_GRANDE"


def procesar_foto(datos: bytes) -> bytes:
    if not datos:
        raise ErrorValidacion("El archivo está vacío.", "FOTO_INVALIDA")
    if len(datos) > TAMANO_MAX_BYTES:
        raise ArchivoDemasiadoGrande("La imagen supera el máximo de 5 MB.")
    Image.MAX_IMAGE_PIXELS = MAX_PIXELES
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(datos)) as img:
                if img.format not in FORMATOS_PERMITIDOS:
                    raise ErrorValidacion(
                        "Formato no permitido. Usa una imagen JPG, PNG o WebP.", "FOTO_FORMATO_INVALIDO"
                    )
                img.load()  # decodifica por completo: detecta archivos truncados o corruptos
                img = ImageOps.exif_transpose(img)  # respeta la orientación antes de quitar EXIF
                img = img.convert("RGBA")
                fondo = Image.new("RGB", img.size, (255, 255, 255))  # PNG/WebP transparentes -> fondo blanco
                fondo.paste(img, mask=img.getchannel("A"))
                img = ImageOps.fit(fondo, (LADO_SALIDA, LADO_SALIDA), Image.Resampling.LANCZOS)
    except ErrorDominio:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise ErrorValidacion("El archivo no es una imagen válida.", "FOTO_INVALIDA")
    salida = io.BytesIO()
    img.save(salida, format="JPEG", quality=85, optimize=True)  # sin exif: Pillow no lo copia por defecto
    return salida.getvalue()
