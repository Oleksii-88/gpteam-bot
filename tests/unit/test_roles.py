"""Тесты для модуля roles."""
import pytest
from app.roles import UserRole, add_role, remove_role, has_role, get_user_roles, clear_roles

@pytest.fixture(autouse=True)
def cleanup():
    """Очищает роли после каждого теста."""
    yield
    clear_roles()

def test_add_role():
    """Тест добавления роли."""
    user_id = 123
    add_role(user_id, UserRole.USER)
    assert has_role(user_id, UserRole.USER)
    assert UserRole.USER in get_user_roles(user_id)

def test_add_multiple_roles():
    """Тест добавления нескольких ролей."""
    user_id = 123
    add_role(user_id, UserRole.USER)
    add_role(user_id, UserRole.ADMIN)
    assert has_role(user_id, UserRole.USER)
    assert has_role(user_id, UserRole.ADMIN)
    assert len(get_user_roles(user_id)) == 2

def test_remove_role():
    """Тест удаления роли."""
    user_id = 123
    add_role(user_id, UserRole.USER)
    add_role(user_id, UserRole.ADMIN)
    remove_role(user_id, UserRole.ADMIN)
    assert has_role(user_id, UserRole.USER)
    assert not has_role(user_id, UserRole.ADMIN)
    assert len(get_user_roles(user_id)) == 1

def test_get_roles_nonexistent_user():
    """Тест получения ролей несуществующего пользователя."""
    user_id = 999
    assert not get_user_roles(user_id)
    assert not has_role(user_id, UserRole.USER)

def test_remove_nonexistent_role():
    """Тест удаления несуществующей роли."""
    user_id = 123
    remove_role(user_id, UserRole.ADMIN)  # Не должно вызывать ошибок
    assert not has_role(user_id, UserRole.ADMIN)
