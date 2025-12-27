"""
Utilidades para manejo de media (descarga de URLs, subida a Telegram).
"""
import logging
from typing import Optional

import aiohttp
from aiogram import Bot
from aiogram.types import BufferedInputFile

logger = logging.getLogger(__name__)

# Tipos MIME soportados
SUPPORTED_MIME_TYPES = {
    "image/jpeg": "photo",
    "image/png": "photo",
    "image/gif": "photo",
    "image/webp": "photo",
    "video/mp4": "video",
    "video/quicktime": "video",
}

# Límite de tamaño (20MB para fotos, 50MB para videos en Telegram)
MAX_PHOTO_SIZE = 20 * 1024 * 1024  # 20MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50MB


async def download_and_upload_media(
    bot: Bot,
    url: str,
    chat_id: int,
    timeout: int = 30
) -> Optional[str]:
    """
    Descarga media desde URL y la sube a Telegram.

    Args:
        bot: Instancia del bot
        url: URL de la media a descargar
        chat_id: ID del chat para subir (se elimina después)
        timeout: Timeout para la descarga (segundos)

    Returns:
        file_id de Telegram o None si falla
    """
    try:
        # Descargar
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status != 200:
                    logger.error(f"Error descargando media: HTTP {response.status}")
                    return None

                content_type = response.headers.get("Content-Type", "").split(";")[0]

                if content_type not in SUPPORTED_MIME_TYPES:
                    logger.error(f"Tipo de media no soportado: {content_type}")
                    return None

                media_type = SUPPORTED_MIME_TYPES[content_type]

                # Leer contenido
                content = await response.read()

                # Validar tamaño
                max_size = MAX_VIDEO_SIZE if media_type == "video" else MAX_PHOTO_SIZE
                if len(content) > max_size:
                    logger.error(f"Media excede tamaño máximo: {len(content)} bytes")
                    return None

        # Obtener nombre de archivo de la URL
        filename = url.split("/")[-1].split("?")[0] or "media"

        # Crear input file
        input_file = BufferedInputFile(content, filename=filename)

        # Subir a Telegram
        if media_type == "photo":
            message = await bot.send_photo(
                chat_id=chat_id,
                photo=input_file
            )
            file_id = message.photo[-1].file_id
            # Eliminar mensaje
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        else:
            message = await bot.send_video(
                chat_id=chat_id,
                video=input_file
            )
            file_id = message.video.file_id
            # Eliminar mensaje
            await bot.delete_message(chat_id=chat_id, message_id=message.message_id)

        logger.info(f"Media subida exitosamente: {file_id[:20]}...")

        return file_id

    except aiohttp.ClientError as e:
        logger.error(f"Error de conexión descargando media: {e}")
        return None
    except Exception as e:
        logger.error(f"Error procesando media: {e}", exc_info=True)
        return None


def is_url(value: str) -> bool:
    """
    Verifica si un string es una URL HTTP/HTTPS.

    Args:
        value: String a verificar

    Returns:
        True si es URL, False si no
    """
    if not value:
        return False
    return value.startswith(("http://", "https://"))


def is_file_id(value: str) -> bool:
    """
    Verifica si un string parece ser un file_id de Telegram.

    Los file_ids de Telegram son strings alfanuméricos largos.

    Args:
        value: String a verificar

    Returns:
        True si parece file_id, False si no
    """
    if not value or len(value) < 20:
        return False

    # File IDs no contienen espacios ni caracteres especiales comunes de URLs
    if " " in value or "/" in value or ":" in value:
        return False

    return not is_url(value)
