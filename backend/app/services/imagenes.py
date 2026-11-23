"""Eliminación de metadatos de fotografías (RN-04 / LFPDPPP; auditoría final, A3).

Una foto de celular trae en EXIF/XMP/IPTC la ubicación GPS exacta, el modelo del dispositivo, la hora y a veces
el nombre de la persona. Las fotos se publican cuando el reporte se valida, así que esos datos no se guardan.

Se reescribe el archivo conservando sólo los segmentos necesarios para mostrar la imagen (sin decodificarla ni
recomprimirla, por lo que no se pierde calidad ni se agrega una dependencia):

* JPEG: se conservan las tablas y los datos de imagen, APP0 (JFIF), APP2 con perfil ICC y APP14 (Adobe, colores).
  Se descartan APP1 (EXIF/XMP), el resto de APPn y los comentarios. La orientación EXIF se reescribe en un
  APP1 mínimo (sólo la etiqueta 0x0112) para que las fotos verticales no aparezcan giradas.
* PNG: lista blanca de fragmentos de imagen y color; se descartan tEXt, zTXt, iTXt, eXIf, tIME y desconocidos.
* En ambos formatos se descarta cualquier byte después del fin de imagen (EOI / IEND), donde suelen ocultarse
  archivos «políglotas».

Un archivo con estructura inválida se rechaza (ValueError). También se rechazan dimensiones anómalas (más de
`MAX_LADO_PX` por lado o `MAX_PIXELES` en total): el servidor no decodifica la imagen, pero el navegador de quien la
abre sí, y un PNG/JPEG diminuto que declara 65 535 × 65 535 píxeles es una «bomba de descompresión».
"""

import struct

_FIRMA_PNG = b"\x89PNG\r\n\x1a\n"
_PNG_PERMITIDOS = {
    b"IHDR", b"PLTE", b"IDAT", b"IEND", b"tRNS", b"gAMA", b"cHRM", b"sRGB", b"iCCP", b"sBIT", b"pHYs", b"bKGD",
}

_SOI, _EOI, _SOS = 0xD8, 0xD9, 0xDA
_SIN_LONGITUD = {0x01, *range(0xD0, 0xD8)}  # TEM y RST0–RST7 no llevan longitud
_APP0, _APP1, _APP2, _APP14, _COM = 0xE0, 0xE1, 0xE2, 0xEE, 0xFE


MAX_LADO_PX = 16_384
MAX_PIXELES = 60_000_000  # cubre cámaras de 50 MP (8160 × 6120)
_SOF = {*range(0xC0, 0xD0)} - {0xC4, 0xC8, 0xCC}  # SOF0–SOF15 (excepto DHT, JPG y DAC)


class ImagenInvalida(ValueError):
    pass


def _validar_dimensiones(ancho: int, alto: int) -> None:
    if ancho < 1 or alto < 1 or ancho > MAX_LADO_PX or alto > MAX_LADO_PX or ancho * alto > MAX_PIXELES:
        raise ImagenInvalida("Dimensiones de imagen anómalas")


# ----------------------------------------------------------------------------------------------------- JPEG


def _orientacion_exif(datos: bytes) -> int | None:
    """Lee la etiqueta Orientation (0x0112) del IFD0 de un segmento APP1 Exif; None si no hay o es inválida."""
    if not datos.startswith(b"Exif\x00\x00"):
        return None
    tiff = datos[6:]
    if len(tiff) < 8:
        return None
    orden = {b"II": "<", b"MM": ">"}.get(tiff[:2])
    if orden is None:
        return None
    try:
        (ifd,) = struct.unpack_from(orden + "I", tiff, 4)
        (entradas,) = struct.unpack_from(orden + "H", tiff, ifd)
        for i in range(min(entradas, 512)):
            etiqueta, tipo, _cuenta = struct.unpack_from(orden + "HHI", tiff, ifd + 2 + i * 12)
            if etiqueta == 0x0112 and tipo == 3:  # SHORT
                (valor,) = struct.unpack_from(orden + "H", tiff, ifd + 2 + i * 12 + 8)
                return valor if 1 <= valor <= 8 else None
    except struct.error:
        return None
    return None


def _app1_solo_orientacion(valor: int) -> bytes:
    tiff = b"II*\x00" + struct.pack("<I", 8) + struct.pack("<H", 1)
    tiff += struct.pack("<HHIHH", 0x0112, 3, 1, valor, 0) + struct.pack("<I", 0)
    carga = b"Exif\x00\x00" + tiff
    return b"\xff" + bytes([_APP1]) + struct.pack(">H", len(carga) + 2) + carga


def _limpiar_jpeg(contenido: bytes) -> bytes:
    if not contenido.startswith(b"\xff\xd8"):
        raise ImagenInvalida("JPEG sin marcador de inicio")
    salida = bytearray(b"\xff\xd8")
    orientacion: int | None = None
    insercion = 2  # justo después de SOI, o después de APP0 (JFIF) si existe
    i, n = 2, len(contenido)
    while True:
        if i >= n or contenido[i] != 0xFF:
            raise ImagenInvalida("Estructura JPEG inválida")
        while i < n and contenido[i] == 0xFF:  # bytes de relleno entre marcadores
            i += 1
        if i >= n:
            raise ImagenInvalida("JPEG truncado")
        marcador = contenido[i]
        i += 1
        if marcador == _EOI:
            salida += b"\xff\xd9"
            return bytes(salida)  # se descarta todo lo que siga al fin de imagen
        if marcador in _SIN_LONGITUD or marcador == _SOI:
            salida += bytes([0xFF, marcador])
            continue
        if i + 2 > n:
            raise ImagenInvalida("JPEG truncado")
        (longitud,) = struct.unpack_from(">H", contenido, i)
        if longitud < 2 or i + longitud > n:
            raise ImagenInvalida("Longitud de segmento JPEG inválida")
        datos = contenido[i + 2 : i + longitud]
        segmento = bytes([0xFF, marcador]) + contenido[i : i + longitud]
        i += longitud

        if marcador in _SOF:
            if len(datos) < 5:
                raise ImagenInvalida("Segmento SOF inválido")
            alto, ancho = struct.unpack_from(">HH", datos, 1)
            # alto 0 en SOF es legal (se define con DNL), pero ningún navegador ni cámara lo usa: se rechaza.
            _validar_dimensiones(ancho, alto)
        if marcador == _APP1:
            orientacion = orientacion or _orientacion_exif(datos)
            continue
        if marcador == _COM or (0xE0 <= marcador <= 0xEF and marcador not in (_APP0, _APP2, _APP14)):
            continue
        if marcador == _APP2 and not datos.startswith(b"ICC_PROFILE\x00"):
            continue
        if marcador == _SOS and orientacion and orientacion != 1:
            salida[insercion:insercion] = _app1_solo_orientacion(orientacion)
            orientacion = None
        salida += segmento
        if marcador == _APP0 and insercion == 2:
            insercion = len(salida)
        if marcador == _SOS:
            # Datos comprimidos: terminan en el siguiente marcador que no sea relleno (FF00) ni RSTn.
            j = i
            while True:
                j = contenido.find(b"\xff", j)
                if j == -1 or j + 1 >= n:
                    raise ImagenInvalida("JPEG sin fin de imagen")
                siguiente = contenido[j + 1]
                if siguiente == 0x00 or 0xD0 <= siguiente <= 0xD7 or siguiente == 0xFF:
                    j += 1 if siguiente == 0xFF else 2
                    continue
                break
            salida += contenido[i:j]
            i = j


# ------------------------------------------------------------------------------------------------------ PNG


def _limpiar_png(contenido: bytes) -> bytes:
    if not contenido.startswith(_FIRMA_PNG):
        raise ImagenInvalida("PNG sin firma")
    salida = bytearray(_FIRMA_PNG)
    i, n, primero = len(_FIRMA_PNG), len(contenido), True
    while True:
        if i + 12 > n:
            raise ImagenInvalida("PNG truncado")
        (longitud,) = struct.unpack_from(">I", contenido, i)
        tipo = contenido[i + 4 : i + 8]
        fin = i + 12 + longitud
        if longitud > 0x7FFFFFFF or fin > n:
            raise ImagenInvalida("Longitud de fragmento PNG inválida")
        # El CRC no se valida: es integridad, no privacidad; el decodificador del navegador decide.
        if primero and tipo != b"IHDR":
            raise ImagenInvalida("PNG sin IHDR")
        if primero:
            if longitud != 13:
                raise ImagenInvalida("IHDR inválido")
            _validar_dimensiones(*struct.unpack_from(">II", contenido, i + 8))
        primero = False
        if tipo in _PNG_PERMITIDOS:
            salida += contenido[i:fin]
        elif not (tipo[0] & 0x20):  # fragmento crítico desconocido: no se puede omitir sin romper la imagen
            raise ImagenInvalida("Fragmento PNG crítico desconocido")
        i = fin
        if tipo == b"IEND":
            return bytes(salida)  # se descarta todo lo que siga a IEND


def limpiar_metadatos(contenido: bytes, mime: str) -> bytes:
    """Devuelve la imagen sin metadatos personales. Lanza ImagenInvalida si la estructura no es válida."""
    if mime == "image/jpeg":
        return _limpiar_jpeg(contenido)
    if mime == "image/png":
        return _limpiar_png(contenido)
    raise ImagenInvalida("Formato no soportado")
