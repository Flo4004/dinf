import crypt_lib as cl
import math
import os
import random

def generate_diffie_hellman_strong_params(min_p=1000000, max_p=5000000):
    """
    
    Args:
        min_p (int): Минимальное значение для модуля P.
        max_p (int): Максимальное значение для модуля P.
    
    Returns:
        tuple: Кортеж (p, g, secret_a, secret_b).
    """
    p, q = cl.generate_safe_prime(min_p, max_p)
    
    g = cl.find_primitive_root(p, q)
    
    secret_a = random.randint(2, p - 2)
    secret_b = random.randint(2, p - 2)
    
    return p, g, secret_a, secret_b



def diffie_hellman_exchange(p, g, secret_a, secret_b):
    """
    Моделирует полный процесс обмена ключами по протоколу Диффи-Хеллмана.

    1. Алиса и Боб получают публичные параметры (p, g).
    2. Алиса генерирует свой публичный ключ Y_A = g^X_A mod p.
    3. Боб генерирует свой публичный ключ Y_B = g^X_B mod p.
    4. Алиса вычисляет общий секрет K_A = (Y_B)^X_A mod p.
    5. Боб вычисляет общий секрет K_B = (Y_A)^X_B mod p.
    В результате K_A должно быть равно K_B.
    
    Args:
        p (int): Большое простое число, публичный параметр.
        g (int): Генератор (первообразный корень), публичный параметр.
        secret_a (int): Секретный ключ абонента A (Алисы).
        secret_b (int): Секретный ключ абонента B (Боба).
    
    Returns:
        tuple: Кортеж, содержащий:
               - public_a (int): Публичный ключ Алисы (Y_A).
               - public_b (int): Публичный ключ Боба (Y_B).
               - shared_secret_a (int): Общий секрет, вычисленный Алисой.
               - shared_secret_b (int): Общий секрет, вычисленный Бобом.
    """
    public_a = cl.fast_exp_mod(g, secret_a, p)
    
    public_b = cl.fast_exp_mod(g, secret_b, p)
    
    shared_secret_a = cl.fast_exp_mod(public_b, secret_a, p)
    
    shared_secret_b = cl.fast_exp_mod(public_a, secret_b, p)
    
    return public_a, public_b, shared_secret_a, shared_secret_b


def get_dh_input_from_keyboard():
    """Получение параметров p, g, X_A, X_B с клавиатуры."""
    try:
        p = int(input("Введите простое число p (модуль): "))
        if not cl.fermat_primality_test(p):
            print(f"Предупреждение: {p} не является вероятно простым числом.")
        
        g = int(input(f"Введите g (генератор, 1 < g < {p-1}): "))
        secret_a = int(input("Введите секретный ключ Алисы (X_A): "))
        secret_b = int(input("Введите секретный ключ Боба (X_B): "))
        
        return p, g, secret_a, secret_b
    except ValueError:
        print("Ошибка: введите целые числа!")
        return None, None, None, None
    

    
def demo_diffie_hellman():
    """Меню для демонстрации протокола Диффи-Хеллмана."""
    while True:
        print("\n" + "=" * 50)
        print("Протокол обмена ключами Диффи-Хеллмана")
        print("=" * 50)
        print("1 - Ввести параметры (p, g, X_A, X_B) с клавиатуры")
        print("2 - Сгенерировать параметры автоматически")
        print("0 - Вернуться в главное меню")
        
        choice = input("Ваш выбор: ")

        if choice == '0':
            break
        
        params = None
        if choice == '1':
            params = get_dh_input_from_keyboard()
        elif choice == '2':
            params = generate_diffie_hellman_strong_params()
        else:
            print("Неверный выбор!")
            continue

        if params and all(p is not None for p in params):
            p, g, x_a, x_b = params

            print("\n--- Начальные параметры ---")
            print(f"Публичные параметры: p = {p}, g = {g}")
            print(f"Секретный ключ Алисы (X_A): {x_a}")
            print(f"Секретный ключ Боба (X_B): {x_b}\n")
            
            print("--- Начало обмена ---")
            
            y_a, y_b, k_a, k_b = diffie_hellman_exchange(p, g, x_a, x_b)
            
            print(f"1. Алиса вычисляет публичный ключ Y_A = g^X_A mod p")
            print(f"   Y_A = {g}^{x_a} mod {p} = {y_a}")
            print("   Алиса отправляет Y_A Бобу.\n")
            
            print(f"2. Боб вычисляет публичный ключ Y_B = g^X_B mod p")
            print(f"   Y_B = {g}^{x_b} mod {p} = {y_b}")
            print("   Боб отправляет Y_B Алисе.\n")
            
            print("--- Вычисление общего секрета ---")
            
            print(f"3. Алиса получила Y_B и вычисляет общий ключ K_A:")
            print(f"   K_A = (Y_B)^X_A mod p = {y_b}^{x_a} mod {p} = {k_a}\n")

            print(f"4. Боб получил Y_A и вычисляет общий ключ K_B:")
            print(f"   K_B = (Y_A)^X_B mod p = {y_a}^{x_b} mod {p} = {k_b}\n")
            
            print("--- Результат ---")
            if k_a == k_b:
                print(f"УСПЕХ! Оба абонента получили одинаковый секретный ключ: {k_a}")
            else:
                print("ОШИБКА! Секретные ключи не совпадают.")
