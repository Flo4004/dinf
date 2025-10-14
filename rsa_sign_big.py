import crypt_lib as cl
import math
import os

import rsa

def rsa_sign(input_path, sign_path, n_big, private_key, public_key):
    """
    Подписывает файл по протоколу RSA, обрабатывая хэш как единое целое число.
    
    Args:
        input_path (str): Путь к входному файлу (файл для подписи).
        sign_path (str): Путь к выходному файлу (файл с вычисленной подписью).
        n_big (int): Большое специально сгенерированное число (модуль N).
        private_key (int): Приватный ключ (d).
        public_key (int): Публичный ключ (e).
    """
    try:
        file_hash = cl.calculate_file_hash(input_path)
        if file_hash is None: return False

        hash_as_int = int.from_bytes(file_hash, 'big')

        if hash_as_int >= n_big:
            print(f"Ошибка: Хэш как число ({hash_as_int}) больше или равен модулю N ({n_big}).")
            print("Подпись не может быть создана. Используйте большие p и q для генерации N.")
            return False
                
        signed_byte_len = (n_big.bit_length() + 7) // 8
        with open(sign_path, 'wb') as f_sign:
            
            n_bytes = n_big.to_bytes(signed_byte_len, 'big')
            f_sign.write(len(n_bytes).to_bytes(2, 'big'))
            f_sign.write(n_bytes)

            public_key_bytes = public_key.to_bytes((public_key.bit_length() + 7) // 8, 'big' )
            f_sign.write(len(public_key_bytes).to_bytes(2, 'big'))
            f_sign.write(public_key_bytes)

            signed_hash_int = cl.fast_exp_mod(hash_as_int, private_key, n_big)
            
            f_sign.write(signed_hash_int.to_bytes(signed_byte_len, 'big'))

        return True
    
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False



def rsa_check_sign(input_path, sign_path):
    """
    Проверяет подпись файла по протоколу RSA, работая с хэшем как с единым целым числом.
    
    Args:
        input_path (str): Путь к входному файлу.
        sign_path (str): Путь к файлу с подписью.
    """
    try:
        expected_hash = cl.calculate_file_hash(input_path)
        if expected_hash is None: return False

        expected_hash_int = int.from_bytes(expected_hash, 'big')

        with open(sign_path, 'rb') as f_sign:
            n_len = int.from_bytes(f_sign.read(2), 'big')
            n = int.from_bytes(f_sign.read(n_len), 'big')
            
            public_key_len = int.from_bytes(f_sign.read(2), 'big')
            public_key = int.from_bytes(f_sign.read(public_key_len), 'big')
            
            signed_byte_len = n_len

            signed_hash_chunk = f_sign.read(signed_byte_len)
            if not signed_hash_chunk:
                print("Ошибка: файл подписи пуст или поврежден.")
                return False
            
            signed_hash_int = int.from_bytes(signed_hash_chunk, 'big')
            
            decrypted_hash_int = cl.fast_exp_mod(signed_hash_int, public_key, n)

        if decrypted_hash_int == expected_hash_int:
            print("ПОДПИСЬ ВЕРНА")
            return True
        else:
            print("ПОДПИСЬ НЕВЕРНА!")
            print(f"Ожидаемый хэш: {expected_hash.hex()}")
            reconstructed_hash_bytes = decrypted_hash_int.to_bytes(len(expected_hash), 'big')
            print(f"Полученный хэш: {reconstructed_hash_bytes.hex()}")
            return False
    
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path} или {sign_path}")
        return False
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False


def demo_rsa_sign():
    """
    Единый процесс демонстрации подписи и проверки RSA.
    (Эта функция остается без изменений)
    """
    print("\n" + "=" * 50)
    print("Демонстрация подписи RSA")
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

        print("\nВыберите способ получения параметров:")
        print("1 - Ввести p и q с клавиатуры")
        print("2 - Сгенерировать параметры автоматически")
        param_choice = input("Ваш выбор: ")

        try:
            if param_choice == '1':
                p = int(input("Введите простое p (рекомендуется > 2^128): "))
                if not cl.fermat_primality_test(p):
                    print(f"Предупреждение: {p} не является вероятно простым числом.")

                q = int(input("Введите простое q (рекомендуется > 2^128): "))
                if not cl.fermat_primality_test(q):
                    print(f"Предупреждение: {q} не является вероятно простым числом.")
                
                n_big = p * q
                phi = (p - 1) * (q - 1)

                public_key = int(input("Введите публичный ключ e (например, 65537): "))
                if math.gcd(public_key, phi) != 1:
                    print(f"Предупреждение: {public_key} не является взаимно простым с phi.")

                private_key = cl.mod_inverse(public_key, phi)
            
            elif param_choice == '2':
                print("\nГенерация параметров (может занять время)...")
                n_big, public_key, private_key = rsa.rsa_generate_params(min_p=2**128, max_p=2**129)
            
            else:
                print("Неверный выбор!")
                return

            print("\n--- Сгенерированные параметры ---")
            print(f"N = {n_big}")
            print(f"Открытый ключ: {public_key}")
            print(f"Секретный ключ: {private_key}")

        except Exception as e:
            print(f"Ошибка при обработке параметров: {e}")
            return

        try:
            print("\n--- НАЧАЛО ПОДПИСИ ---")

            if rsa_sign(input_file, sign_file, n_big, private_key, public_key):
                print(f"Файл подписи '{sign_file}' успешно создан.")
            
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            return
        
    elif choice == '2':
        try:
            input_file = input("\nВведите путь к файлу для проверки: ")
            sign_file = input_file + ".sig"

            if not os.path.exists(input_file) or not os.path.exists(sign_file):
                print(f"Ошибка: один из файлов ('{input_file}', '{sign_file}') не найден.")
                return
        except Exception as e:
            print(f"Ошибка ввода: {e}")
            return
        
        print("\n--- НАЧАЛО ПРОВЕРКИ ---")
        rsa_check_sign(input_file, sign_file)