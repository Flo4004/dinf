import crypt_lib as cl
import math
import os
import random

def shamir_generate_keys(p):
    """
    Генерирует пару ключей (шифрующий C, расшифровывающий D) для протокола Шамира.
    Ключ C должен быть взаимно простым с (p-1).
    """
    phi = p - 1
    while True:
        c = random.randint(2, phi - 1)
        if math.gcd(c, phi) == 1:
            d = cl.mod_inverse(c, phi)
            return c, d

def shamir_generate_params(min_p=257, max_p=65535):
    """
    Генерирует полный набор параметров для протокола Шамира:
    p выбирается > 256, чтобы любой байт (0-255) был меньше p.
    p, C_a, D_a, C_b, D_b.
    """

    p = 0
    while True:
        candidate = random.randint(min_p, max_p)
        if cl.fermat_primality_test(candidate):
            p = candidate
            break
            
    c_a, d_a = shamir_generate_keys(p)
    
    c_b, d_b = shamir_generate_keys(p)
    
    return p, c_a, d_a, c_b, d_b

def shamir_process_file(input_path, output_path, p, key, block_size_in, block_size_out):
    """
    Обрабатывает файл (шифрует/расшифровывает) по протоколу Шамира.
    
    Args:
        input_path (str): Путь к входному файлу.
        output_path (str): Путь к выходному файлу.
        p (int): Простое число (модуль).
        key (int): Ключ (C или D) для операции.
        block_size_in (int): Размер блока для чтения (в байтах, 1 для исходного файла).
        block_size_out (int): Размер блока для записи (в байтах, 2 или 4).
    """
    try:
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            while True:
                block = f_in.read(block_size_in)
                if not block:
                    break
                
                val = int.from_bytes(block, byteorder='big')
                
                processed_val = cl.fast_exp_mod(val, key, p)
                
                f_out.write(processed_val.to_bytes(block_size_out, byteorder='big'))
        return True
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False



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
            p, c_a, d_a, c_b, d_b = shamir_generate_params(max_p=(256**BLOCK_SIZE - 1))
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
    shamir_process_file(input_file, temp_file1, p, c_a, 1, BLOCK_SIZE)
    
    print(f"2. Боб шифрует полученный файл ключом C_b...")
    shamir_process_file(temp_file1, temp_file2, p, c_b, BLOCK_SIZE, BLOCK_SIZE)

    print(f"3. Алиса расшифровывает своим ключом D_a...")
    shamir_process_file(temp_file2, encrypted_file, p, d_a, BLOCK_SIZE, BLOCK_SIZE)

    print(f"4. Боб расшифровывает '{encrypted_file}' своим ключом D_b...")
    shamir_process_file(encrypted_file, decrypted_file, p, d_b, BLOCK_SIZE, 1)

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
