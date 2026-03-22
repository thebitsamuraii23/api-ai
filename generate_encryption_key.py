#!/usr/bin/env python3
"""
Скрипт для генерации ключа шифрования Fernet.
Использование: python generate_encryption_key.py
"""

from cryptography.fernet import Fernet


def generate_encryption_key() -> str:
    """Генерирует новый ключ шифрования Fernet."""
    key = Fernet.generate_key()
    return key.decode('utf-8')


if __name__ == "__main__":
    encryption_key = generate_encryption_key()
    
    print("🔐 Сгенерирован новый ключ шифрования Fernet:\n")
    print(encryption_key)
    print("\n" + "="*80)
    print("📋 Инструкции:")
    print("="*80)
    print("\n1. Скопируйте ключ выше")
    print("2. Откройте файл .env в корневой папке проекта")
    print("3. Замените значение DATA_ENCRYPTION_KEY на скопированный ключ:")
    print("   DATA_ENCRYPTION_KEY=" + encryption_key)
    print("\n4. Сохраните файл .env")
    print("\n⚠️  ВАЖНО: Храните этот ключ в безопасном месте!")
    print("   Без этого ключа вы не сможете расшифровать сохраненные данные.")
