"""Модуль для управления ролями пользователей в Telegram боте.

Этот модуль предоставляет функционал для управления ролями пользователей,
включая добавление, удаление и проверку ролей. В текущей реализации роли
хранятся в памяти, но в production-окружении должны храниться в базе данных.

Роли:
    - ADMIN: Администратор с полным доступом к функциям бота
    - USER: Обычный пользователь с базовым доступом

Примечание:
    В текущей реализации данные о ролях хранятся в памяти и будут сброшены
    при перезапуске бота. Для production использования рекомендуется
    реализовать хранение в постоянной базе данных.
"""
from enum import Enum
from typing import Set

class UserRole(Enum):
    """Перечисление доступных ролей пользователей.
    
    Attributes:
        ADMIN: Роль администратора, имеет полный доступ к функциям бота
        USER: Роль обычного пользователя, имеет базовый доступ к функциям бота
    """
    ADMIN = "admin"
    USER = "user"

# Хранилище ролей пользователей (в реальном приложении это должно быть в БД)
# Формат: user_id -> set of roles
_user_roles: dict[int, Set[UserRole]] = {
    # Предустановленный администратор
    229165573: {UserRole.ADMIN, UserRole.USER}
}

def add_role(user_id: int, role: UserRole) -> None:
    """Добавляет роль пользователю.
    
    Args:
        user_id: Telegram ID пользователя
        role: Роль для добавления из перечисления UserRole
    """
    if user_id not in _user_roles:
        _user_roles[user_id] = set()
    _user_roles[user_id].add(role)

def remove_role(user_id: int, role: UserRole) -> None:
    """Удаляет роль у пользователя.
    
    Args:
        user_id: Telegram ID пользователя
        role: Роль для удаления из перечисления UserRole
    
    Note:
        Если у пользователя нет указанной роли, операция игнорируется.
    """
    if user_id in _user_roles:
        _user_roles[user_id].discard(role)

def get_user_roles(user_id: int) -> Set[UserRole]:
    """Возвращает все роли пользователя.
    
    Args:
        user_id: Telegram ID пользователя
    
    Returns:
        Множество ролей пользователя. Если у пользователя нет ролей,
        возвращается пустое множество.
    """
    return _user_roles.get(user_id, set())

def has_role(user_id: int, role: UserRole) -> bool:
    """Проверяет, есть ли у пользователя указанная роль.
    
    Args:
        user_id: Telegram ID пользователя
        role: Роль для проверки из перечисления UserRole
    
    Returns:
        True если у пользователя есть указанная роль, иначе False
    """
    return role in get_user_roles(user_id)

def clear_roles() -> None:
    """Очищает все роли из хранилища.
    
    Эта функция используется в тестах для сброса состояния хранилища ролей
    перед каждым тестом.
    
    Warning:
        Не использовать в production-коде!
    """
    _user_roles.clear()
