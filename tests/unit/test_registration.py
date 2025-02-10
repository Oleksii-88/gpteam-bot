"""Тесты для модуля регистрации."""
import pytest
from datetime import datetime
from app.registration import (
    RegistrationRequest, RegistrationStatus,
    create_registration_request, get_registration_status,
    approve_registration, reject_registration,
    get_pending_requests, _registration_requests, clear_requests
)

@pytest.fixture(autouse=True)
def clean_requests():
    """Очищает список заявок перед каждым тестом."""
    clear_requests()
    yield

def test_create_registration_request():
    """Тест создания заявки на регистрацию."""
    # Создаем заявку
    assert create_registration_request(123, "test_user", "Test User") == True
    
    # Проверяем, что заявка создана с правильными данными
    request = _registration_requests[123]
    assert request.user_id == 123
    assert request.username == "test_user"
    assert request.first_name == "Test User"
    assert request.status == RegistrationStatus.PENDING
    assert request.processed_by is None
    assert request.processed_time is None

def test_create_duplicate_request():
    """Тест создания дублирующей заявки."""
    # Создаем первую заявку
    assert create_registration_request(123, "test_user", "Test User") == True
    
    # Пытаемся создать дублирующую заявку
    assert create_registration_request(123, "test_user", "Test User") == False

def test_create_request_after_rejection():
    """Тест создания заявки после отклонения."""
    # Создаем и отклоняем заявку
    create_registration_request(123, "test_user", "Test User")
    reject_registration(123, 456)
    
    # Пытаемся создать новую заявку
    assert create_registration_request(123, "test_user", "Test User") == True

def test_get_registration_status():
    """Тест получения статуса регистрации."""
    # Проверяем несуществующую заявку
    assert get_registration_status(123) == None
    
    # Создаем заявку и проверяем статус
    create_registration_request(123, "test_user", "Test User")
    assert get_registration_status(123) == RegistrationStatus.PENDING
    
    # Одобряем заявку и проверяем статус
    approve_registration(123, 456)
    assert get_registration_status(123) == RegistrationStatus.APPROVED
    
    # Отклоняем другую заявку и проверяем статус
    create_registration_request(789, "test_user2", "Test User 2")
    reject_registration(789, 456)
    assert get_registration_status(789) == RegistrationStatus.REJECTED

def test_approve_registration():
    """Тест одобрения заявки."""
    # Пытаемся одобрить несуществующую заявку
    assert approve_registration(123, 456) == False
    
    # Создаем и одобряем заявку
    create_registration_request(123, "test_user", "Test User")
    assert approve_registration(123, 456) == True
    
    # Проверяем данные одобренной заявки
    request = _registration_requests[123]
    assert request.status == RegistrationStatus.APPROVED
    assert request.processed_by == 456
    assert isinstance(request.processed_time, datetime)

def test_reject_registration():
    """Тест отклонения заявки."""
    # Пытаемся отклонить несуществующую заявку
    assert reject_registration(123, 456) == False
    
    # Создаем и отклоняем заявку
    create_registration_request(123, "test_user", "Test User")
    assert reject_registration(123, 456) == True
    
    # Проверяем данные отклоненной заявки
    request = _registration_requests[123]
    assert request.status == RegistrationStatus.REJECTED
    assert request.processed_by == 456
    assert isinstance(request.processed_time, datetime)

def test_get_pending_requests():
    """Тест получения списка ожидающих заявок."""
    # Проверяем пустой список
    assert len(get_pending_requests()) == 0
    
    # Создаем несколько заявок
    create_registration_request(123, "user1", "User 1")  # PENDING
    create_registration_request(456, "user2", "User 2")  # PENDING
    create_registration_request(789, "user3", "User 3")  # будет APPROVED
    
    # Одобряем одну заявку
    approve_registration(789, 999)
    
    # Проверяем список ожидающих заявок
    pending = get_pending_requests()
    assert len(pending) == 2
    assert 123 in pending
    assert 456 in pending
    assert 789 not in pending

def test_registration_workflow():
    """Тест полного процесса регистрации."""
    # 1. Создаем заявку
    create_registration_request(123, "test_user", "Test User")
    assert get_registration_status(123) == RegistrationStatus.PENDING
    
    # 2. Проверяем, что заявка в списке ожидающих
    pending = get_pending_requests()
    assert 123 in pending
    
    # 3. Отклоняем заявку
    reject_registration(123, 456)
    assert get_registration_status(123) == RegistrationStatus.REJECTED
    
    # 4. Создаем новую заявку после отклонения
    create_registration_request(123, "test_user", "Test User")
    assert get_registration_status(123) == RegistrationStatus.PENDING
    
    # 5. Одобряем заявку
    approve_registration(123, 456)
    assert get_registration_status(123) == RegistrationStatus.APPROVED
    
    # 6. Проверяем, что заявки нет в списке ожидающих
    pending = get_pending_requests()
    assert 123 not in pending
