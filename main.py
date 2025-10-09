import random
import crypt_lib as cl
import os
import math

import diffie_hellman
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






def demo_shamir():
    """
    Единый процесс демонстрации протокола Шамира
    """
    BLOCK_SIZE = 2

    print("\n" + "=" * 50)
    print("Демонстрация протокола Шамира (полный цикл)")
    print("=" * 50)
    
    try:
        input_file = input("Введите путь к исходному файлу: ")
        decrypted_file = input("Введите путь для сохранения конечного (расшифрованного) файла: ")
        
        if not os.path.exists(input_file):
            print(f"Ошибка: Исходный файл '{input_file}' не найден.")
            return
    except Exception as e:
        print(f"Ошибка ввода: {e}")
        return

    print("\nВыберите способ получения параметров:")
    print("1 - Ввести p, C_a, C_b с клавиатуры")
    print("2 - Сгенерировать параметры автоматически")
    param_choice = input("Ваш выбор: ")

    p, c_a, d_a, c_b, d_b = 0, 0, 0, 0, 0
    
    try:
        if param_choice == '1':
            p = int(input(f"Введите простое p ({256**1} < p < {256**BLOCK_SIZE}): "))
            if p <= 255:
                print("Ошибка: p должно быть больше 255.")
                return
            c_a = int(input("Введите ключ Алисы C_a: "))
            c_b = int(input("Введите ключ Боба C_b: "))
            phi = p - 1
            d_a = cl.mod_inverse(c_a, phi)
            d_b = cl.mod_inverse(c_b, phi)
        elif param_choice == '2':
            print("\nГенерация параметров...")
            p, c_a, d_a, c_b, d_b = cl.shamir_generate_params(max_p=(256**BLOCK_SIZE - 1))
        else:
            print("Неверный выбор!")
            return
            
        print("\n--- Сгенерированные параметры ---")
        print(f"p = {p}")
        print(f"Ключи Алисы: C_a={c_a}, D_a={d_a}")
        print(f"Ключи Боба: C_b={c_b}, D_b={d_b}")

    except Exception as e:
        print(f"Ошибка при обработке параметров: {e}")
        return

    temp_file1 = decrypted_file + ".temp1"
    temp_file2 = decrypted_file + ".temp2"
    encrypted_file = decrypted_file + ".encrypted"
    
    # try:
    
    print("\n--- НАЧАЛО ШИФРОВАНИЯ/РАСШИФРОВАНИЯ ---")
    print(f"1. Алиса шифрует '{input_file}' ключом C_a...")
    cl.shamir_process_file(input_file, temp_file1, p, c_a, 1, BLOCK_SIZE)
    
    print(f"2. Боб шифрует полученный файл ключом C_b...")
    cl.shamir_process_file(temp_file1, temp_file2, p, c_b, BLOCK_SIZE, BLOCK_SIZE)

    print(f"3. Алиса расшифровывает своим ключом D_a...")
    cl.shamir_process_file(temp_file2, encrypted_file, p, d_a, BLOCK_SIZE, BLOCK_SIZE)

    print(f"4. Боб расшифровывает '{encrypted_file}' своим ключом D_b...")
    cl.shamir_process_file(encrypted_file, decrypted_file, p, d_b, BLOCK_SIZE, 1)

    print(f"\nПроцесс завершен. Финальный файл сохранен как '{decrypted_file}'")

    # print("\n--- ПРОВЕРКА РЕЗУЛЬТАТА ---")
    # hash_original = cl.calculate_file_hash(input_file)
    # hash_decrypted = cl.calculate_file_hash(decrypted_file)

    # print(f"Хэш исходного файла:    {hash_original}")
    # print(f"Хэш расшифрованного файла: {hash_decrypted}")

    # if hash_original and hash_original == hash_decrypted:
    #     print("\nУСПЕХ! Файлы полностью совпадают.")
    # else:
    #     print("\nОШИБКА! Файлы не совпадают. Что-то пошло не так.")

    # finally:
    #     # --- Очистка временных файлов ---
    #     print("\nОчистка временных файлов...")
    #     for f in [temp_file1, temp_file2, encrypted_file]:
    #         if os.path.exists(f):
    #             os.remove(f)





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
            demo_shamir()
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