"""
Servicio de desafíos narrativos.

Gestiona los acertijos, preguntas y desafíos interactivos
que el usuario debe superar para avanzar en la narrativa.
"""
import logging
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from bot.narrative.database.models_immersive import (
    FragmentChallenge,
    UserChallengeAttempt,
)
from bot.narrative.database.enums import ChallengeType

logger = logging.getLogger(__name__)


class ChallengeService:
    """
    Servicio para gestión de desafíos narrativos.

    Tipos de desafíos:
    - TEXT_INPUT: Usuario escribe respuesta
    - CHOICE_SEQUENCE: Secuencia correcta de opciones
    - TIMED_RESPONSE: Responder antes del timeout
    - MEMORY_RECALL: Recordar dato de fragmento anterior
    - OBSERVATION: Encontrar detalle oculto
    """

    def __init__(self, session: AsyncSession):
        """
        Inicializa el servicio.

        Args:
            session: Sesión async de SQLAlchemy
        """
        self._session = session

    # ========================================
    # OBTENCIÓN DE DESAFÍOS
    # ========================================

    async def get_challenge_for_fragment(
        self,
        fragment_key: str
    ) -> Optional[FragmentChallenge]:
        """
        Obtiene el desafío asociado a un fragmento.

        Args:
            fragment_key: Key del fragmento

        Returns:
            Desafío o None
        """
        stmt = select(FragmentChallenge).where(
            and_(
                FragmentChallenge.fragment_key == fragment_key,
                FragmentChallenge.is_active == True
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_challenge_by_id(
        self,
        challenge_id: int
    ) -> Optional[FragmentChallenge]:
        """
        Obtiene un desafío por su ID.

        Args:
            challenge_id: ID del desafío

        Returns:
            Desafío o None
        """
        stmt = select(FragmentChallenge).where(
            FragmentChallenge.id == challenge_id
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    # ========================================
    # VALIDACIÓN DE RESPUESTAS
    # ========================================

    async def validate_answer(
        self,
        challenge_id: int,
        user_answer: str
    ) -> tuple[bool, str]:
        """
        Valida una respuesta del usuario.

        Args:
            challenge_id: ID del desafío
            user_answer: Respuesta del usuario

        Returns:
            Tupla (es_correcta, mensaje)
        """
        challenge = await self.get_challenge_by_id(challenge_id)
        if challenge is None:
            return False, "Desafío no encontrado"

        try:
            correct_answers = json.loads(challenge.correct_answers)
        except json.JSONDecodeError:
            correct_answers = [challenge.correct_answers]

        # Normalizar respuestas para comparación
        user_normalized = self._normalize_answer(user_answer)
        correct_normalized = [self._normalize_answer(a) for a in correct_answers]

        is_correct = user_normalized in correct_normalized

        if is_correct:
            message = challenge.success_message or "¡Correcto!"
        else:
            message = challenge.failure_message or "Respuesta incorrecta. Intenta de nuevo."

        return is_correct, message

    def _normalize_answer(self, answer: str) -> str:
        """Normaliza una respuesta para comparación."""
        return answer.strip().lower()

    # ========================================
    # REGISTRO DE INTENTOS
    # ========================================

    async def record_attempt(
        self,
        user_id: int,
        challenge_id: int,
        answer_given: Optional[str],
        is_correct: bool,
        response_time_seconds: Optional[int] = None,
        hints_used: int = 0
    ) -> UserChallengeAttempt:
        """
        Registra un intento de desafío.

        Args:
            user_id: ID del usuario
            challenge_id: ID del desafío
            answer_given: Respuesta dada
            is_correct: Si fue correcta
            response_time_seconds: Tiempo de respuesta
            hints_used: Pistas usadas

        Returns:
            Registro del intento
        """
        # Obtener número de intento
        attempt_number = await self.get_attempt_count(user_id, challenge_id) + 1

        attempt = UserChallengeAttempt(
            user_id=user_id,
            challenge_id=challenge_id,
            attempt_number=attempt_number,
            answer_given=answer_given,
            is_correct=is_correct,
            hints_used=hints_used,
            attempted_at=datetime.utcnow(),
            response_time_seconds=response_time_seconds
        )
        self._session.add(attempt)
        await self._session.flush()

        logger.info(
            f"Intento registrado: user={user_id}, challenge={challenge_id}, "
            f"attempt={attempt_number}, correct={is_correct}"
        )
        return attempt

    async def get_attempt_count(
        self,
        user_id: int,
        challenge_id: int
    ) -> int:
        """
        Obtiene el número de intentos de un usuario en un desafío.

        Args:
            user_id: ID del usuario
            challenge_id: ID del desafío

        Returns:
            Número de intentos
        """
        stmt = select(func.count()).where(
            and_(
                UserChallengeAttempt.user_id == user_id,
                UserChallengeAttempt.challenge_id == challenge_id
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar() or 0

    async def has_completed_challenge(
        self,
        user_id: int,
        challenge_id: int
    ) -> bool:
        """
        Verifica si el usuario completó un desafío.

        Args:
            user_id: ID del usuario
            challenge_id: ID del desafío

        Returns:
            True si completó (al menos un intento correcto)
        """
        stmt = select(UserChallengeAttempt).where(
            and_(
                UserChallengeAttempt.user_id == user_id,
                UserChallengeAttempt.challenge_id == challenge_id,
                UserChallengeAttempt.is_correct == True
            )
        ).limit(1)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def can_attempt(
        self,
        user_id: int,
        challenge_id: int
    ) -> tuple[bool, str, int]:
        """
        Verifica si el usuario puede intentar un desafío.

        Args:
            user_id: ID del usuario
            challenge_id: ID del desafío

        Returns:
            Tupla (puede_intentar, mensaje, intentos_restantes)
        """
        challenge = await self.get_challenge_by_id(challenge_id)
        if challenge is None:
            return False, "Desafío no encontrado", 0

        # Ya completó?
        if await self.has_completed_challenge(user_id, challenge_id):
            return False, "Ya completaste este desafío", 0

        # Verificar límite de intentos
        attempts = await self.get_attempt_count(user_id, challenge_id)
        max_attempts = challenge.attempts_allowed

        if max_attempts == 0:
            # Sin límite
            return True, "", 999

        if attempts >= max_attempts:
            return False, "Has agotado tus intentos", 0

        remaining = max_attempts - attempts
        return True, "", remaining

    # ========================================
    # PISTAS (HINTS)
    # ========================================

    async def get_hint(
        self,
        challenge_id: int,
        hint_index: int
    ) -> Optional[str]:
        """
        Obtiene una pista específica de un desafío.

        Args:
            challenge_id: ID del desafío
            hint_index: Índice de la pista (0-based)

        Returns:
            Texto de la pista o None
        """
        challenge = await self.get_challenge_by_id(challenge_id)
        if challenge is None or not challenge.hints:
            return None

        try:
            hints = json.loads(challenge.hints)
            if 0 <= hint_index < len(hints):
                return hints[hint_index]
        except json.JSONDecodeError:
            pass

        return None

    async def get_available_hints(
        self,
        challenge_id: int
    ) -> List[str]:
        """
        Obtiene todas las pistas de un desafío.

        Args:
            challenge_id: ID del desafío

        Returns:
            Lista de pistas
        """
        challenge = await self.get_challenge_by_id(challenge_id)
        if challenge is None or not challenge.hints:
            return []

        try:
            return json.loads(challenge.hints)
        except json.JSONDecodeError:
            return []

    async def get_next_hint(
        self,
        user_id: int,
        challenge_id: int
    ) -> tuple[Optional[str], int, int]:
        """
        Obtiene la siguiente pista disponible para un usuario.

        Args:
            user_id: ID del usuario
            challenge_id: ID del desafío

        Returns:
            Tupla (pista, índice_actual, total_pistas)
        """
        # Obtener intentos para ver cuántas pistas ha usado
        stmt = select(func.max(UserChallengeAttempt.hints_used)).where(
            and_(
                UserChallengeAttempt.user_id == user_id,
                UserChallengeAttempt.challenge_id == challenge_id
            )
        )
        result = await self._session.execute(stmt)
        hints_used = result.scalar() or 0

        hints = await self.get_available_hints(challenge_id)
        total_hints = len(hints)

        if hints_used >= total_hints:
            return None, hints_used, total_hints

        hint = hints[hints_used]
        return hint, hints_used + 1, total_hints

    # ========================================
    # PROCESAMIENTO COMPLETO
    # ========================================

    async def process_challenge_attempt(
        self,
        user_id: int,
        challenge_id: int,
        user_answer: str,
        response_time_seconds: Optional[int] = None,
        hints_used: int = 0
    ) -> Dict[str, Any]:
        """
        Procesa un intento completo de desafío.

        Args:
            user_id: ID del usuario
            challenge_id: ID del desafío
            user_answer: Respuesta del usuario
            response_time_seconds: Tiempo de respuesta
            hints_used: Pistas usadas en este intento

        Returns:
            Diccionario con resultado completo
        """
        challenge = await self.get_challenge_by_id(challenge_id)
        if challenge is None:
            return {
                "success": False,
                "message": "Desafío no encontrado",
                "can_retry": False,
            }

        # Verificar si puede intentar
        can_attempt, block_message, remaining = await self.can_attempt(user_id, challenge_id)
        if not can_attempt:
            return {
                "success": False,
                "message": block_message,
                "can_retry": False,
                "redirect_key": challenge.failure_redirect_key,
            }

        # Validar respuesta
        is_correct, message = await self.validate_answer(challenge_id, user_answer)

        # Registrar intento
        await self.record_attempt(
            user_id=user_id,
            challenge_id=challenge_id,
            answer_given=user_answer,
            is_correct=is_correct,
            response_time_seconds=response_time_seconds,
            hints_used=hints_used
        )

        result = {
            "success": is_correct,
            "message": message,
            "answer_given": user_answer,
        }

        if is_correct:
            result["reward_clue_slug"] = challenge.success_clue_slug
            result["reward_besitos"] = challenge.success_besitos
            result["can_retry"] = False
        else:
            # Verificar si puede reintentar
            can_retry, _, remaining = await self.can_attempt(user_id, challenge_id)
            result["can_retry"] = can_retry
            result["attempts_remaining"] = remaining
            result["redirect_key"] = challenge.failure_redirect_key if not can_retry else None

        return result

    # ========================================
    # CRUD DE DESAFÍOS
    # ========================================

    async def create_challenge(
        self,
        fragment_key: str,
        challenge_type: ChallengeType,
        question: str,
        correct_answers: List[str],
        hints: Optional[List[str]] = None,
        attempts_allowed: int = 3,
        timeout_seconds: Optional[int] = None,
        failure_redirect_key: Optional[str] = None,
        failure_message: Optional[str] = None,
        success_clue_slug: Optional[str] = None,
        success_besitos: int = 0,
        success_message: Optional[str] = None
    ) -> FragmentChallenge:
        """
        Crea un nuevo desafío.

        Args:
            fragment_key: Key del fragmento
            challenge_type: Tipo de desafío
            question: Pregunta/instrucción
            correct_answers: Lista de respuestas correctas
            hints: Lista de pistas progresivas
            attempts_allowed: Intentos permitidos (0 = infinitos)
            timeout_seconds: Timeout para respuesta
            failure_redirect_key: Fragmento al fallar todos los intentos
            failure_message: Mensaje al fallar
            success_clue_slug: Pista a otorgar al completar
            success_besitos: Besitos a otorgar al completar
            success_message: Mensaje al completar

        Returns:
            Desafío creado
        """
        challenge = FragmentChallenge(
            fragment_key=fragment_key,
            challenge_type=challenge_type,
            question=question,
            correct_answers=json.dumps(correct_answers),
            hints=json.dumps(hints) if hints else None,
            attempts_allowed=attempts_allowed,
            timeout_seconds=timeout_seconds,
            failure_redirect_key=failure_redirect_key,
            failure_message=failure_message,
            success_clue_slug=success_clue_slug,
            success_besitos=success_besitos,
            success_message=success_message,
            is_active=True
        )
        self._session.add(challenge)
        await self._session.flush()

        logger.info(f"Desafío creado: id={challenge.id}, fragment={fragment_key}")
        return challenge

    async def update_challenge(
        self,
        challenge_id: int,
        **updates
    ) -> Optional[FragmentChallenge]:
        """
        Actualiza un desafío.

        Args:
            challenge_id: ID del desafío
            **updates: Campos a actualizar

        Returns:
            Desafío actualizado o None
        """
        challenge = await self.get_challenge_by_id(challenge_id)
        if challenge is None:
            return None

        for key, value in updates.items():
            if hasattr(challenge, key):
                if key in ("correct_answers", "hints") and isinstance(value, list):
                    value = json.dumps(value)
                setattr(challenge, key, value)

        await self._session.flush()
        return challenge

    async def delete_challenge(
        self,
        challenge_id: int
    ) -> bool:
        """
        Elimina (soft delete) un desafío.

        Args:
            challenge_id: ID del desafío

        Returns:
            True si se eliminó
        """
        challenge = await self.get_challenge_by_id(challenge_id)
        if challenge is None:
            return False

        challenge.is_active = False
        await self._session.flush()
        return True

    # ========================================
    # ESTADÍSTICAS
    # ========================================

    async def get_challenge_stats(
        self,
        challenge_id: int
    ) -> Dict[str, Any]:
        """
        Obtiene estadísticas de un desafío.

        Args:
            challenge_id: ID del desafío

        Returns:
            Diccionario con estadísticas
        """
        challenge = await self.get_challenge_by_id(challenge_id)
        if challenge is None:
            return {}

        # Total intentos
        stmt = select(func.count()).where(
            UserChallengeAttempt.challenge_id == challenge_id
        )
        result = await self._session.execute(stmt)
        total_attempts = result.scalar() or 0

        # Intentos correctos
        stmt = select(func.count()).where(
            and_(
                UserChallengeAttempt.challenge_id == challenge_id,
                UserChallengeAttempt.is_correct == True
            )
        )
        result = await self._session.execute(stmt)
        correct_attempts = result.scalar() or 0

        # Usuarios únicos
        stmt = select(func.count(func.distinct(UserChallengeAttempt.user_id))).where(
            UserChallengeAttempt.challenge_id == challenge_id
        )
        result = await self._session.execute(stmt)
        unique_users = result.scalar() or 0

        # Usuarios que completaron
        stmt = select(func.count(func.distinct(UserChallengeAttempt.user_id))).where(
            and_(
                UserChallengeAttempt.challenge_id == challenge_id,
                UserChallengeAttempt.is_correct == True
            )
        )
        result = await self._session.execute(stmt)
        users_completed = result.scalar() or 0

        return {
            "challenge_id": challenge_id,
            "fragment_key": challenge.fragment_key,
            "total_attempts": total_attempts,
            "correct_attempts": correct_attempts,
            "success_rate": round(correct_attempts / total_attempts * 100, 1) if total_attempts > 0 else 0,
            "unique_users": unique_users,
            "users_completed": users_completed,
            "completion_rate": round(users_completed / unique_users * 100, 1) if unique_users > 0 else 0,
        }
