"""Модуль для управления регистрацией пользователей."""
from enum import Enum
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

class RegistrationStatus(Enum):
    """Статус регистрации пользователя."""
    PENDING = "pending"  # Ожидает рассмотрения
    APPROVED = "approved"  # Одобрена
    REJECTED = "rejected"  # Отклонена

@dataclass
class RegistrationRequest:
    """Заявка на регистрацию."""
    user_id: int
    username: str
    first_name: str
    request_time: datetime
    status: RegistrationStatus
    processed_by: Optional[int] = None
    processed_time: Optional[datetime] = None

# Хранилище заявок на регистрацию (в реальном приложении должно быть в БД)
# user_id -> RegistrationRequest
_registration_requests: Dict[int, RegistrationRequest] = {
    # Администратор автоматически зарегистрирован
    229165573: RegistrationRequest(
        user_id=229165573,
        username="Oleksii",
        first_name="Oleksii 🇺🇦",
        request_time=datetime.now(),
        status=RegistrationStatus.APPROVED,
        processed_by=229165573,
        processed_time=datetime.now()
    )
}

def create_registration_request(user_id: int, username: str, first_name: str) -> bool:
    """Создает заявку на регистрацию."""
    # Проверяем, есть ли уже заявка и в каком она статусе
    if user_id in _registration_requests:
        request = _registration_requests[user_id]
        # Если заявка в статусе PENDING или APPROVED, не разрешаем повторную подачу
        if request.status in [RegistrationStatus.PENDING, RegistrationStatus.APPROVED]:
            return False
    
    _registration_requests[user_id] = RegistrationRequest(
        user_id=user_id,
        username=username,
        first_name=first_name,
        request_time=datetime.now(),
        status=RegistrationStatus.PENDING
    )
    return True

def get_registration_status(user_id: int) -> Optional[RegistrationStatus]:
    """Возвращает статус регистрации пользователя."""
    request = _registration_requests.get(user_id)
    return request.status if request else None

def is_registered(user_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь."""
    status = get_registration_status(user_id)
    return status == RegistrationStatus.APPROVED

def approve_registration(user_id: int, admin_id: int) -> bool:
    """Одобряет заявку на регистрацию."""
    request = _registration_requests.get(user_id)
    if not request or request.status != RegistrationStatus.PENDING:
        return False
    
    request.status = RegistrationStatus.APPROVED
    request.processed_by = admin_id
    request.processed_time = datetime.now()
    return True

def reject_registration(user_id: int, admin_id: int) -> bool:
    """Отклоняет заявку на регистрацию."""
    request = _registration_requests.get(user_id)
    if not request or request.status != RegistrationStatus.PENDING:
        return False
    
    request.status = RegistrationStatus.REJECTED
    request.processed_by = admin_id
    request.processed_time = datetime.now()
    return True

def get_pending_requests() -> Dict[int, RegistrationRequest]:
    """Возвращает список ожидающих заявок на регистрацию."""
    return {
        user_id: request 
        for user_id, request in _registration_requests.items() 
        if request.status == RegistrationStatus.PENDING
    }

def clear_requests() -> None:
    """Очищает все заявки (используется в тестах)."""
    _registration_requests.clear()
