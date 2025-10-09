import random
import crypt_lib as cl
import os
import math

import diffie_hellman
import shamir
import elgamal
import rsa
import vernam
import rsa_sign

def get_bsgs_input_from_keyboard():
    """
    Получение параметров a, y, p с клавиатуры.
    """
    try:
        p = int(input("Введите простой модуль p: "))
        if not cl.fermat_primality_test(p):
            print(f"Предупреждение: {p} не является вероятно простым числом.")
        a = int(input(f"Введите основание a (1 < a < {p-1}): "))
        y = int(input(f"Введите результат y (1 < y < {p-1}): "))
        return a, y, p
    except ValueError:
        print("Ошибка: введите целые числа!")
        return None, None, None

def generate_bsgs_parameters(min_p=100000, max_p=10000000):
    """
    Генерация параметров a, y, p для задачи дискретного логарифма.
    """
    print("Генерация параметров...")
    p = 0
    while True:
        num = random.randint(min_p, max_p)
        if cl.fermat_primality_test(num):
            p = num
            break
            
    a = random.randint(2, p - 2)
    x_true = random.randint(2, p - 2)
    y = cl.fast_exp_mod(a, x_true, p)
    
    print(f"Сгенерированы следующие параметры:")
    print(f"p = {p}")
    print(f"a = {a}")
    print(f"y = {y}")
    print(f"(Для проверки: секретный x был равен {x_true})")
    
    return a, y, p
    
def demo_bsgs():
    while True:
        print("\n" + "=" * 50)
        print("Алгоритм 'Шаг младенца, шаг великана'")
        print("Найти x в уравнении y = a^x mod p")
        print("=" * 50)
        print("1 - Ввод a, y, p с клавиатуры")
        print("2 - Сгенерировать a, y, p автоматически")
        print("0 - Вернуться в главное меню")
        
        choice = input("Ваш выбор: ")

        if choice == '0':
            break
        
        a, y, p = None, None, None
        
        if choice == '1':
            a, y, p = get_bsgs_input_from_keyboard()
        elif choice == '2':
            a, y, p = generate_bsgs_parameters()
        else:
            print("Неверный выбор!")
            continue

        if a is not None:
            print("\nВычисление x...")
            x = cl.baby_step_giant_step(a, y, p)
            
            if x is not None:
                print(f"\n>>> РЕШЕНИЕ НАЙДЕНО: x = {x}")
                check = cl.fast_exp_mod(a, x, p) 
                print(f"Проверка: {a}^{x} mod {p} = {check}")
                if check == y:
                    print("Проверка пройдена успешно!")
                else:
                    print("ВНИМАНИЕ: Проверка не пройдена!")
            else:
                print("\n>>> Решение не найдено.")



def main():
    """Главное меню программы."""
    while True:
        print("\n" + "#" * 50)
        print("Криптографическая библиотека: Главное меню")
        print("#" * 50)
        print("1 - Дискретный логарифм ('Шаг младенца, шаг великана')")
        print("2 - Обмен ключами Диффи-Хеллмана")
        print("3 - Шифр Шамира")
        print("4 - Шифр Эль-Гамаля")
        print("5 - Шифр RSA")
        print("6 - Шифр Вернама")
        print("7 - Подпись/Проверка RSA")
        print("0 - Выход")
        
        choice = input("Ваш выбор: ")
        
        if choice == '0':
            print("Выход из программы.")
            break
        elif choice == '1':
            demo_bsgs() 
        elif choice == '2':
            diffie_hellman.demo_diffie_hellman()
        elif choice == '3':
            shamir.demo_shamir()
        elif choice == '4':
            elgamal.demo_elgamal()
        elif choice == '5':
            rsa.demo_rsa()
        elif choice == '6':
            vernam.demo_vernam()
        elif choice == '7':
            rsa_sign.demo_rsa_sign()
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main()