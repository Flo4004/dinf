import crypt_lib as cl
import math
import os
import random

def rsa_generate_params(min_p = 255, max_p=65535):
    """
    Генерирует полный набор параметров для протокола RSA.
    Returns:
        tuple: Кортеж, содержащий:
            - n_big (int): Большое простое число.
            - public_key (int): Публичный ключ Боба (d_b).
            - perivate_key (int): Секретный ключ Боба (c_b).
    """

    while True:
        p_candidate = random.randint(min_p, max_p)
        if cl.fermat_primality_test(p_candidate):
            p = p_candidate
            break

    while True:
        q_candidate = random.randint(min_p, max_p)
        if cl.fermat_primality_test(q_candidate) and q_candidate != p:
            q = q_candidate
            break
        
    n_big = p*q

    phi = (p-1)*(q-1)
    while True:
        d_candidate = random.randint(2, phi - 1)
        if math.gcd(d_candidate, phi) == 1:
            public_key = d_candidate
            break

    private_key = cl.mod_inverse(public_key, phi)

    return n_big, public_key, private_key

def rsa_process_file(input_path, output_path, n_big, key, block_size_in, block_size_out, original_size=None):
    """
    Шифрует файл по протоколу RSA.
    
    Args:
        input_path (str): Путь к входному файлу.
        output_path (str): Путь к выходному файлу.
        n_big (int): Большое специально сгенерированное число.
        key (int): Ключ.
        block_size_in (int): Размер блока для чтения (в байтах).
        block_size_out (int): Размер блока для записи (в байтах).
    """
    try:
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            
            bytes_written = 0
            
            while True:
                block = f_in.read(block_size_in)
                if not block:
                    break
                
                val = int.from_bytes(block, byteorder='big')
                
                process_val = cl.fast_exp_mod(val, key, n_big)
                
                if original_size is not None:
                    remaining_bytes = original_size - bytes_written
                    bytes_to_write_count = min(block_size_out, remaining_bytes)
                else:
                    bytes_to_write_count = block_size_out

                processed_block = process_val.to_bytes(block_size_out, byteorder='big')

                if original_size is not None:
                    f_out.write(processed_block[-bytes_to_write_count:])
                    bytes_written += bytes_to_write_count
                else:
                    f_out.write(processed_block)

        return True
    
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False



def demo_rsa():
    """
    Единый процесс демонстрации шифра RSA.
    """
    print("\n" + "=" * 50)
    print("Демонстрация протокола RSA")
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
    print("1 - Ввести p и q с клавиатуры")
    print("2 - Сгенерировать параметры автоматически")
    param_choice = input("Ваш выбор: ")

    try:
        if param_choice == '1':
            p = int(input("Введите простое p: "))
            if p <= 255:
                print("Ошибка: p должно быть больше 255.")
                return
            if not cl.fermat_primality_test(p):
                print(f"Предупреждение: {p} не является вероятно простым числом.")

            q = int(input("Введите простое q: "))
            if q <= 255:
                print("Ошибка: q должно быть больше 255.")
                return
            if not cl.fermat_primality_test(q):
                print(f"Предупреждение: {q} не является вероятно простым числом.")
            
            n_big = p * q
            phi = (p - 1) * (q - 1)

            public_key = int(input("Введите публичный ключ: "))
            if math.gcd(public_key, phi) != 1:
                print(f"Предупреждение: {public_key} не является взаимно простым с phi.")

            private_key = cl.mod_inverse(public_key, phi)
        elif param_choice == '2':
            print("\nГенерация параметров...")
            n_big, public_key, private_key = rsa_generate_params()
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

    block_size_out = (n_big.bit_length() + 7) // 8
    block_size_in = block_size_out - 1

    if block_size_in <= 0:
        print("Ошибка: сгенерированные p и q слишком малы. n должен быть > 255.")
        return

    print("\n--- Эффективность шифрования ---")
    print(f"Размер модуля n: {block_size_out} байт")
    print(f"Шифрование будет производиться блоками по {block_size_in} байт.")
    print(f"Каждые {block_size_in} байт исходного файла превратятся в {block_size_out} байт шифртекста.")

    encrypted_file = input_file + ".encrypted"
    temp_encrypted_content = encrypted_file + ".temp_content"

    try:
        print("\n--- НАЧАЛО ШИФРОВАНИЯ ---")
        print(f"Шифруем '{input_file}' с использованием публичного ключа...")

        original_size = os.path.getsize(input_file)
        
        rsa_process_file(input_file, temp_encrypted_content, n_big, public_key, block_size_in, block_size_out)
        
        with open(encrypted_file, 'wb') as f_out, open(temp_encrypted_content, 'rb') as f_in_temp:
            f_out.write(original_size.to_bytes(8, byteorder='big'))
            f_out.write(f_in_temp.read())
        
        os.remove(temp_encrypted_content)
        print(f"Зашифрованный файл сохранен как {encrypted_file}")

        print("\n--- НАЧАЛО РАСШИФРОВАНИЯ ---")
        print(f"Расшифровываем '{encrypted_file}' с использованием приватного ключа...")
        
        with open(encrypted_file, 'rb') as f_in:
            original_size_from_file = int.from_bytes(f_in.read(8), byteorder='big')
            with open(temp_encrypted_content, 'wb') as f_out_temp:
                f_out_temp.write(f_in.read())
        
        rsa_process_file(temp_encrypted_content, decrypted_file, n_big, private_key, block_size_out, block_size_in, original_size_from_file)
        
        os.remove(temp_encrypted_content)
        print(f"Расшифрованный файл сохранен как {decrypted_file}")

    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return -1