import crypt_lib as cl
import math
import os

import diffie_hellman

def vernam_process_file(input_path, output_path, key, block_size_in, block_size_out, original_size=None):
    """
    Шифрует файл шифром Вернама
    
    Args:
        input_path (str): Путь к входному файлу.
        output_path (str): Путь к выходному файлу.
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
                
                m = int.from_bytes(block, byteorder='big')

                e = m ^ key

                if original_size is not None:
                    remaining_bytes = original_size - bytes_written
                    bytes_to_write_count = min(block_size_out, remaining_bytes)
                else:
                    bytes_to_write_count = block_size_out

                processed_block = e.to_bytes(block_size_out, byteorder='big')

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



def demo_vernam():
    """
    Демонстрация шифра Вернама. Клюс шифрования получается методом Диффи-Хелмана
    """

    print("\n" + "=" * 50)
    print("Демонстрация шифра Вернама")
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
    print("1 - Ввести ключ K с клавиатуры")
    print("2 - Сгенерировать параметры автоматически")
    param_choice = input("Ваш выбор: ")

    
    try:
        if param_choice == '1':
            k1 = int(input(f"Введите ключ шифрования K: "))

        elif param_choice == '2':
            print("\nГенерация параметров протоколом Деффи-Хелмана...")
            p, g, secret_a, secret_b = diffie_hellman.generate_diffie_hellman_strong_params()
            public_a, public_b, k1, k2 = diffie_hellman.diffie_hellman_exchange(p, g, secret_a, secret_b)

            if k1 != k2:
                print(f"Сгенерированные параметры протоколом Деффи-Хелмана не совпадают k1 = {k1}, k2 = {k2}")
                return

        else:
            print("Неверный выбор!")
            return
            
        print("\n--- Сгенерированные параметры ---")
        print(f"key = {k1}")

    except Exception as e:
        print(f"Ошибка при обработке параметров: {e}")
        return

    encrypted_file = input_file + ".encrypted"
    temp_encrypted_content = encrypted_file + ".temp_content"
    
    block_size_in = (k1.bit_length() + 7) // 8
    block_size_out = block_size_in

    print(f"\nИсходный файл разобъется на блоки размером {block_size_in} байт.")

    try:
                
        print("\n--- НАЧАЛО ШИФРОВАНИЯ ---")
        print(f"Шифруем '{input_file}' с использованием ключа {k1}")

        original_size = os.path.getsize(input_file)
        
        vernam_process_file(input_file, temp_encrypted_content, k1, block_size_in, block_size_out)
        
        with open(encrypted_file, 'wb') as f_out, open(temp_encrypted_content, 'rb') as f_in_temp:
            f_out.write(original_size.to_bytes(8, byteorder='big'))
            f_out.write(f_in_temp.read())
        
        os.remove(temp_encrypted_content)
        print(f"Зашифрованный файл сохранен как {encrypted_file}")

        print("\n--- НАЧАЛО РАСШИФРОВАНИЯ ---")
        print(f"Расшифровываем '{encrypted_file}' с использованием приватного ключа X_b...")

        with open(encrypted_file, 'rb') as f_in:
            original_size_from_file = int.from_bytes(f_in.read(8), byteorder='big')
            with open(temp_encrypted_content, 'wb') as f_out_temp:
                f_out_temp.write(f_in.read())

        vernam_process_file(temp_encrypted_content, decrypted_file, k2, block_size_out, block_size_in, original_size_from_file)

        os.remove(temp_encrypted_content)
        print(f"Расшифрованный файл сохранен как '{decrypted_file}'")
    
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return -1
