#!/usr/bin/env python3
"""
Утилита для работы с шифрованием данных.
Всё в одном месте: генерация ключей, шифрование/расшифровка данных.
"""

from cryptography.fernet import Fernet
import os
from dotenv import load_dotenv


def generate_key() -> str:
    """Генерирует новый Fernet ключ."""
    return Fernet.generate_key().decode('utf-8')


def encrypt_data(data: str, encryption_key: str) -> str:
    """
    Шифрует данные.
    
    Args:
        data: Строка для шифрования
        encryption_key: Fernet ключ из переменной окружения
        
    Returns:
        Зашифрованные данные в виде строки
    """
    if not encryption_key:
        raise ValueError("encryption_key не может быть пустым")
    
    cipher = Fernet(encryption_key.encode('utf-8'))
    encrypted = cipher.encrypt(data.encode('utf-8'))
    return encrypted.decode('utf-8')


def decrypt_data(encrypted_data: str, encryption_key: str) -> str:
    """
    Расшифровывает данные.
    
    Args:
        encrypted_data: Зашифрованные данные
        encryption_key: Fernet ключ из переменной окружения
        
    Returns:
        Расшифрованная строка
        
    Raises:
        cryptography.fernet.InvalidToken: Если данные повреждены или ключ неверный
    """
    if not encryption_key:
        raise ValueError("encryption_key не может быть пустым")
    
    cipher = Fernet(encryption_key.encode('utf-8'))
    decrypted = cipher.decrypt(encrypted_data.encode('utf-8'))
    return decrypted.decode('utf-8')


def validate_key(encryption_key: str) -> bool:
    """
    Проверяет валидность Fernet ключа.
    
    Args:
        encryption_key: Ключ для проверки
        
    Returns:
        True если ключ валиден, False иначе
    """
    try:
        Fernet(encryption_key.encode('utf-8'))
        return True
    except Exception:
        return False


def main():
    """Интерактивный режим утилиты."""
    load_dotenv()
    
    while True:
        print("\n" + "="*80)
        print("🔐 Утилита управления шифрованием")
        print("="*80)
        print("\nВыберите действие:")
        print("1. Сгенерировать новый ключ")
        print("2. Зашифровать текст")
        print("3. Расшифровать текст")
        print("4. Проверить ключ из .env")
        print("5. Выход")
        
        choice = input("\nВыбор (1-5): ").strip()
        
        if choice == "1":
            print("\n🔑 Генерирую новый ключ...")
            new_key = generate_key()
            print(f"\n✅ Новый ключ:\n{new_key}")
            print("\n💾 Добавьте следующую строку в ваш .env файл:")
            print(f"DATA_ENCRYPTION_KEY={new_key}")
            
        elif choice == "2":
            encryption_key = os.getenv('DATA_ENCRYPTION_KEY')
            if not encryption_key:
                print("❌ Ошибка: DATA_ENCRYPTION_KEY не найден в .env")
                continue
            
            text = input("\nВведите текст для шифрования: ")
            encrypted = encrypt_data(text, encryption_key)
            print(f"\n✅ Зашифрованный текст:\n{encrypted}")
            
        elif choice == "3":
            encryption_key = os.getenv('DATA_ENCRYPTION_KEY')
            if not encryption_key:
                print("❌ Ошибка: DATA_ENCRYPTION_KEY не найден в .env")
                continue
            
            encrypted_text = input("\nВведите зашифрованный текст: ")
            try:
                decrypted = decrypt_data(encrypted_text, encryption_key)
                print(f"\n✅ Расшифрованный текст:\n{decrypted}")
            except Exception as e:
                print(f"\n❌ Ошибка расшифровки: {e}")
                
        elif choice == "4":
            encryption_key = os.getenv('DATA_ENCRYPTION_KEY')
            if not encryption_key:
                print("❌ DATA_ENCRYPTION_KEY не найден в .env")
            elif validate_key(encryption_key):
                print("✅ Ключ из .env валиден и работает!")
                print(f"Ключ: {encryption_key}")
            else:
                print("❌ Ключ из .env невалиден! Проверьте .env файл.")
                
        elif choice == "5":
            print("\n👋 До свидания!")
            break
            
        else:
            print("❌ Неверный выбор. Пожалуйста, выберите 1-5.")


if __name__ == "__main__":
    main()
