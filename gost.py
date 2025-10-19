import crypt_lib as cl
import math
import os
import random

def gost_generate_params(q_bits = 256, p_bits = 1024):
    """
    Генерирует параметры для электронной подписи ГОСТ Р 34.10-94.
    q = 256 бит, p = 1024 бит, p = b*q+1

    Returns:
        tuple: Кортеж, содержащий:
            - q (int): Простое число длинной 256 бит (или q_bits).
            - p (int): Простое число длинной 1024 бит (или p_bits).
            - a (int): a^q mod p == 1 (или a = g^b mod p).
            - public_key (int): Публичный ключ (y).
            - private_key (int): Секретный ключ (x).
    """
    
    q = cl.generate_prime_bits(q_bits)
    
    # Отладка
    # print(f"q = {q}")
    # print(f"Длина q: {q.bit_length()} бит\n")
    
    min_b = (2**(p_bits-1) - 1) // q
    max_b = (2**p_bits - 2) // q

    while True:
        b = random.randint(min_b, max_b)

        p = b * q + 1

        if cl.fermat_primality_test(p) and p.bit_length() == p_bits:
            # # Отладка
            # print(f"b = {b}")
            # print(f"Длина b: {b.bit_length()} бит\n")
            # print(f"p = {p}")
            # print(f"Длина p: {p.bit_length()} бит\n")
            break
    
    while True:
        g = random.randint(2, p-2)

        a = cl.fast_exp_mod(g, b, p)
        if a > 1:
            # Отладка
            # print(f"a = {a}")
            # print(f"Длина a: {a.bit_length()} бит\n")
            break
    
    private_key = random.randint(1, q-1)
    public_key = cl.fast_exp_mod(a, private_key, p)

    # print(f"public = {public_key}")
    # print(f"Длина: {public_key.bit_length()} бит\n")
    # print(f"private = {private_key}")
    # print(f"Длина: {private_key.bit_length()} бит\n")

    return q, p, a, public_key, private_key



def gost_sign(input_path, sign_path, q, p, a, public_key, private_key):
    """
    Создает подпись для файла по схеме ГОСТ Р 34.10-94.

    Args:
        input_path (str): Путь к входному файлу (файл для подписи).
        output_path (str): Путь к выходному файлу (файл с вычисленной подписью).
        q (int): Простое число (128 бит).
        p (int): Простое число (1024 бит).
        public_key (int): Публичный ключ записывается в файл для дальнейшей проверки подписи.
        private_key (int): Приватный ключ используемый только для подписи.
    """

    try:
        file_hash = cl.calculate_file_hash(input_path)
        if file_hash is None: return False

        hash_as_int = int.from_bytes(file_hash, 'big')

        if hash_as_int >= q:
            print(f"Ошибка: Хэш как число ({hash_as_int}) больше или равен q ({q}).")
            print("Подпись не может быть создана.")
            return False
                
        with open(sign_path, 'wb') as f_sign:
            
            signed_byte_len = (q.bit_length() + 7) // 8

            q_bytes = q.to_bytes(signed_byte_len, 'big')
            f_sign.write(len(q_bytes).to_bytes(2, 'big'))
            f_sign.write(q_bytes)

            p_bytes = p.to_bytes((p.bit_length() + 7) // 8, 'big')
            f_sign.write(len(p_bytes).to_bytes(4, 'big'))
            f_sign.write(p_bytes)

            a_bytes = a.to_bytes((a.bit_length() + 7) // 8, 'big')
            f_sign.write(len(a_bytes).to_bytes(4, 'big'))
            f_sign.write(a_bytes)

            public_key_bytes = public_key.to_bytes((public_key.bit_length() + 7) // 8, 'big' )
            f_sign.write(len(public_key_bytes).to_bytes(4, 'big'))
            f_sign.write(public_key_bytes)


            while True:
                k = random.randint(1, q - 1)
                r = cl.fast_exp_mod(a, k, p) % q
                if r != 0:
                    s = (k*hash_as_int + private_key*r) % q
                    if s != 0:
                        f_sign.write(r.to_bytes(signed_byte_len, 'big'))
                        f_sign.write(s.to_bytes(signed_byte_len, 'big'))
                        break

        return True
    
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False



def gost_check_sign(input_path, sign_path):
    """
    Проверяет подпись файла по протоколу  ГОСТ Р 34.10-94
    
    Args:
        input_path (str): Путь к входному файлу (файл для подписи).
        output_path (str): Путь к выходному файлу (файл с вычисленной подписью).
    """
    
    try:
        file_hash = cl.calculate_file_hash(input_path)
        if file_hash is None: return False

        hash_as_int = int.from_bytes(file_hash, 'big')

        with open(sign_path, 'rb') as f_sign:

            q_len = int.from_bytes(f_sign.read(2), 'big')
            q = int.from_bytes(f_sign.read(q_len), 'big')

            p_len = int.from_bytes(f_sign.read(4), 'big')
            p = int.from_bytes(f_sign.read(p_len), 'big')

            a_len = int.from_bytes(f_sign.read(4), 'big')
            a = int.from_bytes(f_sign.read(a_len), 'big')

            public_key_len = int.from_bytes(f_sign.read(4), 'big')
            public_key = int.from_bytes(f_sign.read(public_key_len), 'big')

            signed_byte_len = q_len

            r_byte = f_sign.read(signed_byte_len)
            s_byte = f_sign.read(signed_byte_len)

            if not r_byte or not s_byte:
                print("r_byte или s_byte = null")
                return False

            r_int = int.from_bytes(r_byte, 'big')
            s_int = int.from_bytes(s_byte, 'big')

            if r_int < 0 or r_int >= q:
                print("r_int < 0 или r_int > q")
                return False
            
            if s_int < 0 or s_int >= q:
                print("s_int < 0 или s_int > q")
                return False

            h_inv = cl.mod_inverse(hash_as_int, q)
            u1 = (s_int * h_inv) % q
            u2 = (-r_int * h_inv) % q

            # v = ((a**u1 * public_key**u2) % p) % q
            v = (cl.fast_exp_mod(a, u1, p) * cl.fast_exp_mod(public_key, u2, p) % p) % q

        if v == r_int:
            print("\n" + "=" * 50)
            print(" "*16 + "ПОДПИСЬ ВЕРНА")
            print("=" * 50)
            return True
        else:
            print("\n" + "=" * 50)
            print(" "*14 + "ПОДПИСЬ НЕВЕРНА!")
            print("=" * 50)
            return False



    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path} или {sign_path}")
        return False
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False



def demo_gost_sign():
    """
    Единый процесс демонстрации электронной подписи ГОСТ Р 34.10-94.
    """
    print("\n" + "=" * 50)
    print("Демонстрация подписи ГОСТ Р 34.10-94. ")
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
        q, p, a, public_key, private_key = gost_generate_params()
            
        print("\n--- Сгенерированные параметры ---")
        print(f"q = {q}")
        print(f"p = {p}")
        print(f"a = {a}")
        print(f"Открытый ключ (y): {public_key}")
        print(f"Секретный ключ (x): {private_key}")

        try:
            print("\n--- НАЧАЛО ПОДПИСИ ---")
            if gost_sign(input_file, sign_file, q, p, a, public_key, private_key,):
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
        gost_check_sign(input_file, sign_file)