import crypt_lib as cl
import math
import os
import random

import elgamal

def elgamal_sign(input_path, sign_path, p, g, private_key, public_key):
    """
    Создает подпись для файла по схеме Эль-Гамаля.

        Args:
        input_path (str): Путь к входному файлу (файл для подписи).
        output_path (str): Путь к выходному файлу (файл с вычисленной подписью).
        p (int): Большое простое число.
        g (int): Первообразный корень p.
        private_key (int): Приватный ключ используемый только для подписи.
        public_key (int): Публичный ключ записывается в файл для дальнейшей проверки подписи
    """

    try:
        hash_bytes = cl.calculate_file_hash(input_path)
        if hash_bytes is None: return False

        p_len = (p.bit_length() + 7) // 8
        
        with open(sign_path, 'wb') as f_sign:
            p_bytes = p.to_bytes(p_len, 'big')
            f_sign.write(len(p_bytes).to_bytes(2, 'big'))
            f_sign.write(p_bytes)

            g_bytes = g.to_bytes((g.bit_length() + 7) // 8, 'big')
            f_sign.write(len(g_bytes).to_bytes(2, 'big'))
            f_sign.write(g_bytes)
            
            public_key_bytes = public_key.to_bytes(p_len, 'big')
            f_sign.write(len(public_key_bytes).to_bytes(2, 'big'))
            f_sign.write(public_key_bytes)

            for byte_of_hash in hash_bytes:
                
                k = 0
                while True:
                    k = random.randint(2, p - 2)
                    if math.gcd(k, p - 1) == 1:
                        break
                
                r = cl.fast_exp_mod(g, k, p)
                
                u = (byte_of_hash - private_key * r) % (p - 1)
                
                k_inv = cl.mod_inverse(k, p - 1)
                s = (k_inv * u) % (p - 1)
                
                f_sign.write(r.to_bytes(p_len, 'big'))
                f_sign.write(s.to_bytes(p_len, 'big'))

        return True
    except Exception as e:
        print(f"Ошибка при создании подписи Эль-Гамаля: {e}")
        return False

def elgamal_check_sign(input_path, sign_path):
    """
    Проверяет подпись файла по протоколу RSA.
    
    Args:
        input_path (str): Путь к входному файлу (файл для подписи).
        output_path (str): Путь к выходному файлу (файл с вычисленной подписью).
    """
    try:
        expected_hash = cl.calculate_file_hash(input_path)
        if expected_hash is None: return False

        with open(sign_path, 'rb') as f_sign:
            p_len = int.from_bytes(f_sign.read(2), 'big')
            p = int.from_bytes(f_sign.read(p_len), 'big')

            g_len = int.from_bytes(f_sign.read(2), 'big')
            g = int.from_bytes(f_sign.read(g_len), 'big')
            
            public_key_len = int.from_bytes(f_sign.read(2), 'big')
            public_key = int.from_bytes(f_sign.read(public_key_len), 'big')
            
            signed_byte_len = p_len

            is_valid = True
            for byte_of_hash in expected_hash:
                r_byte = f_sign.read(signed_byte_len)
                s_byte = f_sign.read(signed_byte_len)
                if not r_byte or not s_byte:
                    break
                
                r_byte_int = int.from_bytes(r_byte, 'big')
                s_byte_int = int.from_bytes(s_byte, 'big')
                
                left_part1 = cl.fast_exp_mod(public_key, r_byte_int, p)
                left_part2 = cl.fast_exp_mod(r_byte_int, s_byte_int, p)
                left = (left_part1 * left_part2) % p

                right = cl.fast_exp_mod(g, byte_of_hash, p)

                if left != right:
                    is_valid = False
                    # Отладка
                    print("\nНесовпадение")
                    print(f"left = {left}")
                    print(f"right = {right}")
                    break
                
        if is_valid:    
            print("\n--- ПОДПИСЬ ВЕРНА ---")
            return True
        else:
            print("\n--- ПОДПИСЬ НЕВЕРНА! ---")
            return False
    
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    except Exception as public_key:
        print(f"Произошла ошибка при обработке файла: {public_key}")
        return False



def demo_elgamal_sign():
    """
    Единый процесс демонстрации электронной подписи Эль-Гамаля.
    """
    print("\n" + "=" * 50)
    print("Демонстрация подписи Эль-Гамаля")
    print("=" * 50)

    print("\nЧто вы хотите сделать?")
    print("1. Подписать файл")
    print("2. Проверить подпись")
    choice = input("Ваш выбор: ")

    if choice == '1':
        try:
            input_file = input("\nВведите путь к подписываемому файлу: ")
            sign_file = input_file + ".sig"

            if not os.path.exists(input_file):
                print(f"Ошибка: Исходный файл '{input_file}' не найден.")
                return
        except Exception as e:
            print(f"Ошибка ввода: {e}")
            return


        print("\nГенерация параметров...")
        p, g, x, y = elgamal.elgamal_generate_params()
            
        print("\n--- Сгенерированные параметры ---")
        print(f"p = {p}")
        print(f"g = {g}")
        print(f"Открытый ключ (y): {y}")
        print(f"Секретный ключ (x): {x}")

        try:
            print("\n--- НАЧАЛО ПОДПИСИ ---")
            if elgamal_sign(input_file, sign_file, p, g, x, y):
                print(f"Файл подписи '{sign_file}' успешно создан.")
            
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            return
        
    elif choice == '2':
        try:
            input_file = input("\nВведите путь к подписываемому файлу: ")
            sign_file = input_file + ".sig"

            if not os.path.exists(input_file):
                print(f"Ошибка: Исходный файл '{input_file}' не найден.")
                return
        except Exception as e:
            print(f"Ошибка ввода: {e}")
            return
        
        print("\n--- НАЧАЛО ПРОВЕРКИ ---")
        elgamal_check_sign(input_file, sign_file)