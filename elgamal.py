import crypt_lib as cl
import math
import os
import random

def elgamal_generate_params(min_p = 255, max_p=65535):
    """
    Генерирует полный набор параметров для протокола Эль-Гамаля:
    p выбирается > 256, чтобы любой байт (0-255) был меньше p.
    Returns:
        tuple: Кортеж, содержащий:
            - p (int): Большое простое число.
            - g (int): Первообразный корень p.
            - x (int): Секретный ключ Боба (c_b).
            - y (int): Публичный (открытый) ключ Боба (d_b).
    """

    p, q = cl.generate_safe_prime(min_p, max_p)
    g = cl.find_primitive_root(p, q)

    x = random.randint(2, p-1)
    y = cl.fast_exp_mod(g, x, p)

    return p, g, x, y

def elgamal_encrypt_file(input_path, output_path, p, g, public_key_y, block_size_out = 2):
    """
    Шифрует файл по протоколу Эль-Гамаля.
    
    Args:
        input_path (str): Путь к входному файлу.
        output_path (str): Путь к выходному файлу.
        p (int): Простое число.
        g (int): Первообразный корень p.
        public_key_y (int): Публичный ключ получателя (y)
        block_size_out (int): Размер блока для записи чисел a и b (в байтах).
    """
    try:
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            while True:
                block = f_in.read(1)
                if not block:
                    break
                
                m = int.from_bytes(block, byteorder='big')
                
                k = random.randint(2, p - 2)
                
                a = cl.fast_exp_mod(g, k, p)
                b = (cl.fast_exp_mod(public_key_y, k, p) * m) % p

                f_out.write(a.to_bytes(block_size_out, byteorder='big'))
                f_out.write(b.to_bytes(block_size_out, byteorder='big'))
        return True
    
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False
    
def elgamal_decrypt_file(input_path, output_path, p, private_key_x, block_size_in=2):
    """
    Расшифровывает файл с использованием приватного ключа получателя.
    
    Args:
        input_path (str): Путь к зашифрованному файлу.
        output_path (str): Путь для сохранения расшифрованного файла.
        p (int): Публичный параметр (простое число).
        private_key_x (int): Приватный ключ получателя (X).
        block_size_in (int): Размер блока для чтения чисел a и b (в байтах).
    """
    try:
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            while True:
                a_bytes = f_in.read(block_size_in)
                b_bytes = f_in.read(block_size_in)
                if not a_bytes or not b_bytes:
                    break
                    
                a = int.from_bytes(a_bytes, byteorder='big')
                b = int.from_bytes(b_bytes, byteorder='big')
                
                m = cl.fast_exp_mod(a, p - 1 - private_key_x, p) * b % p
                
                f_out.write(m.to_bytes(1, byteorder='big'))
        return True
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False



def demo_elgamal():
    """
    Единый процесс демонстрации шифра Эль-Гамаля:
    Генерация ключей -> Шифрование -> Расшифрование.
    """
    
    BLOCK_SIZE = 2

    print("\n" + "=" * 50)
    print("Демонстрация протокола Эль-Гамаля")
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

    
    try:
        if param_choice == '1':
            p = int(input(f"Введите простое p ({256**1} < p < {256**BLOCK_SIZE}): "))
            if p <= 255:
                print("Ошибка: p должно быть больше 255.")
                return
            if not cl.fermat_primality_test(p):
                print(f"Предупреждение: {p} не является вероятно простым числом.")

            g = int(input("Введите число g (первообразный корень p): "))
            if cl.fast_exp_mod(g, (p-1)/2, p) == 1:
                print(f"Предупреждение: {g} не является вероятно первообразным корнем.")
                
            x = int(input("Введите ключ Боба C_b: "))
            y = cl.fast_exp_mod(g, x, p)

        elif param_choice == '2':
            print("\nГенерация параметров...")
            p, g, x, y = cl.elgamal_generate_params()

        else:
            print("Неверный выбор!")
            return
            
        print("\n--- Сгенерированные параметры ---")
        print(f"p = {p}, g = {g}")
        print(f"Открытый ключ: y (d_b) = {y}")
        print(f"Секретный ключ: x (c_b) = {x}")

    except Exception as e:
        print(f"Ошибка при обработке параметров: {e}")
        return

    encrypted_file = input_file + ".encrypted"
    
    try:
                
        print("\n--- НАЧАЛО ШИФРОВАНИЯ ---")
        print(f"Шифруем '{input_file}' с использованием публичного ключа Y_b...")
        cl.elgamal_encrypt_file(input_file, encrypted_file, p, g , y, BLOCK_SIZE)
        print(f"Зашифрованный файл сохранен как {encrypted_file}")

        print("\n--- НАЧАЛО РАСШИФРОВАНИЯ ---")
        print(f"Расшифровываем '{encrypted_file}' с использованием приватного ключа X_b...")
        cl.elgamal_decrypt_file(encrypted_file, decrypted_file, p, x, BLOCK_SIZE)
        print(f"Расшифрованный файл сохранен как '{decrypted_file}'")
    
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return -1