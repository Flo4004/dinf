import random
import crypt_lib as cl
import os
import math

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
            params = cl.generate_diffie_hellman_strong_params()
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
            
            y_a, y_b, k_a, k_b = cl.diffie_hellman_exchange(p, g, x_a, x_b)
            
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
            n_big, public_key, private_key = cl.rsa_generate_params()
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
        
        cl.rsa_process_file(input_file, temp_encrypted_content, n_big, public_key, block_size_in, block_size_out)
        
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
        
        cl.rsa_process_file(temp_encrypted_content, decrypted_file, n_big, private_key, block_size_out, block_size_in, original_size_from_file)
        
        os.remove(temp_encrypted_content)
        print(f"Расшифрованный файл сохранен как {decrypted_file}")

    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return -1

def demo_vernam():
    """

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
            p, g, secret_a, secret_b = cl.generate_diffie_hellman_strong_params()
            public_a, public_b, k1, k2 = cl.diffie_hellman_exchange(p, g, secret_a, secret_b)

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
        
        cl.vernam_process_file(input_file, temp_encrypted_content, k1, block_size_in, block_size_out)
        
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

        cl.vernam_process_file(temp_encrypted_content, decrypted_file, k2, block_size_out, block_size_in, original_size_from_file)

        os.remove(temp_encrypted_content)
        print(f"Расшифрованный файл сохранен как '{decrypted_file}'")
    
    except Exception as e:
        print(f"Произошла непредвиденная ошибка: {e}")
        return -1

def demo_rsa_sign():
    """
    Единый процесс демонстрации подписи и проверки RSA.
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
                n_big, public_key, private_key = cl.rsa_generate_params()
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
        block_size_in = 1

        if block_size_in <= 0:
            print("Ошибка: сгенерированные p и q слишком малы. n должен быть > 255.")
            return

        try:
            print("\n--- НАЧАЛО ПОДПИСИ ---")

            cl.rsa_sign(input_file, sign_file, n_big, private_key, public_key)

            print(f"Файл подписи '{sign_file}' успешно создан.")
            
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")
            return -1
        
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
        cl.rsa_check_sign(input_file, sign_file)

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
            demo_diffie_hellman()
        elif choice == '3':
            demo_shamir()
        elif choice == '4':
            demo_elgamal()
        elif choice == '5':
            demo_rsa()
        elif choice == '6':
            demo_vernam()
        elif choice == '7':
            demo_rsa_sign()
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main()