import random
import math
import hashlib

def fast_exp_mod(a, x, p):
    """
    Быстрое вычисление степени по модулю
    
    Args:
        a (int): Основание
        x (int): Показатель степени
        p (int): Модуль
    
    Returns:
        int: Результат вычисления a^x mod p
    """

    y = 1
    s = a % p
    while x > 0:
        if x % 2 == 1:
            y = (y * s) % p
        x = x // 2
        s = (s * s) % p
    return y

def fermat_primality_test(n, k=50):
    """
    Тест простоты Ферма
    
    Args:
        n (int): Число для проверки на простоту
        k (int): Количество тестов (по умолчанию 50)
    
    Returns:
        bool: True если число вероятно простое, False если составное
    """

    if n <= 1: return False
    if n <= 3: return True
    if n % 2 == 0: return False
    for _ in range(k):
        a = random.randint(2, n - 2)
        if fast_exp_mod(a, n - 1, n) != 1:
            return False
    return True

def extended_euclidean_algorithm(a, b):
    """
    Реализует обобщенный алгоритм Евклида.

    Находит наибольший общий делитель (НОД) двух чисел a и b, а также
    коэффициенты x и y, удовлетворяющие тождеству Безу:
    a*x + b*y = НОД(a, b).
    
    Args:
        a (int): Первое целое число.
        b (int): Второе целое число.
    
    Returns:
        tuple: Кортеж из трех целых чисел (gcd, x, y), где:
               gcd - наибольший общий делитель a и b.
               x, y - коэффициенты тождества Безу.
    """

    if a == 0:
        return b, 0, 1
    gcd, x1, y1 = extended_euclidean_algorithm(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return gcd, x, y

def mod_inverse(n, modulus):
    """
    Находит модульный мультипликативный обратный элемент.

    Вычисляет такое число x, что (n * x) % modulus = 1.
    Функция использует обобщенный алгоритм Евклида. Обратный элемент
    существует только в том случае, если n и modulus взаимно просты.
    
    Args:
        n (int): Число, для которого ищется обратный элемент.
        modulus (int): Модуль, по которому вычисляется обратный элемент.
    
    Returns:
        int: Модульный обратный элемент для n по модулю modulus.
        
    Raises:
        Exception: Вызывается, если обратный элемент не существует
                   (т.е. НОД(n, modulus) != 1).
    """
    
    gcd, x, y = extended_euclidean_algorithm(n, modulus)
    if gcd != 1:
        raise Exception('Модульный обратный элемент не существует')
    return x % modulus

def baby_step_giant_step(a, y, p):
    """
    Решает задачу дискретного логарифма методом "Шаг младенца, шаг великана".

    Находит такое значение x, что удовлетворяет уравнению y = a^x mod p.
    Алгоритм основан на идее "встречи посередине" и имеет временную
    сложность O(sqrt(p)), что значительно эффективнее полного перебора.
    
    Args:
        a (int): Основание степени.
        y (int): Результат возведения в степень по модулю.
        p (int): Простой модуль.
        
    Returns:
        int or None: Целое число x, являющееся решением уравнения.
                     Возвращает None, если решение не найдено.
    """

    m = int(math.sqrt(p)) + 1

    baby_steps = {}
    val = 1
    for j in range(m):
        baby_steps[val] = j
        val = (val * a) % p

    a_inv_m = mod_inverse(fast_exp_mod(a, m, p), p)

    giant_step_val = y
    for i in range(m):
        if giant_step_val in baby_steps:
            j = baby_steps[giant_step_val]
            return i * m + j
        giant_step_val = (giant_step_val * a_inv_m) % p

    return None

                            ######################
                            ### ЛАБАРАТОРНАЯ 3 ###
                            ######################

def generate_safe_prime(min_val, max_val):
    """
    Args:
        min_val (int): Минимальное значение для P.
        max_val (int): Максимальное значение для P.
        
    Returns:
        tuple: Кортеж (P, Q), где P - безопасное простое, Q - простое число Софи Жермен.
    """
    while True:
        q_candidate = random.randint(min_val // 2, max_val // 2)
        
        if fermat_primality_test(q_candidate):
            p_candidate = 2 * q_candidate + 1
            
            if fermat_primality_test(p_candidate):
                return p_candidate, q_candidate

def find_primitive_root(p, q):
    """
    Args:
        p (int): Безопасное простое число.
        q (int): Простое число Софи Жермен (q = (p-1)/2).
        
    Returns:
        int: Первообразный корень g.
    """
    for g in range(2, p):
        if fast_exp_mod(g, q, p) != 1:
            return g
    return None

def generate_diffie_hellman_strong_params(min_p=1000000, max_p=5000000):
    """
    
    Args:
        min_p (int): Минимальное значение для модуля P.
        max_p (int): Максимальное значение для модуля P.
    
    Returns:
        tuple: Кортеж (p, g, secret_a, secret_b).
    """
    p, q = generate_safe_prime(min_p, max_p)
    
    g = find_primitive_root(p, q)
    
    secret_a = random.randint(2, p - 2)
    secret_b = random.randint(2, p - 2)
    
    return p, g, secret_a, secret_b

def diffie_hellman_exchange(p, g, secret_a, secret_b):
    """
    Моделирует полный процесс обмена ключами по протоколу Диффи-Хеллмана.

    1. Алиса и Боб получают публичные параметры (p, g).
    2. Алиса генерирует свой публичный ключ Y_A = g^X_A mod p.
    3. Боб генерирует свой публичный ключ Y_B = g^X_B mod p.
    4. Алиса вычисляет общий секрет K_A = (Y_B)^X_A mod p.
    5. Боб вычисляет общий секрет K_B = (Y_A)^X_B mod p.
    В результате K_A должно быть равно K_B.
    
    Args:
        p (int): Большое простое число, публичный параметр.
        g (int): Генератор (первообразный корень), публичный параметр.
        secret_a (int): Секретный ключ абонента A (Алисы).
        secret_b (int): Секретный ключ абонента B (Боба).
    
    Returns:
        tuple: Кортеж, содержащий:
               - public_a (int): Публичный ключ Алисы (Y_A).
               - public_b (int): Публичный ключ Боба (Y_B).
               - shared_secret_a (int): Общий секрет, вычисленный Алисой.
               - shared_secret_b (int): Общий секрет, вычисленный Бобом.
    """
    public_a = fast_exp_mod(g, secret_a, p)
    
    public_b = fast_exp_mod(g, secret_b, p)
    
    shared_secret_a = fast_exp_mod(public_b, secret_a, p)
    
    shared_secret_b = fast_exp_mod(public_a, secret_b, p)
    
    return public_a, public_b, shared_secret_a, shared_secret_b

                            ######################
                            ### ЛАБАРАТОРНАЯ 4 ###
                            ######################

def shamir_generate_keys(p):
    """
    Генерирует пару ключей (шифрующий C, расшифровывающий D) для протокола Шамира.
    Ключ C должен быть взаимно простым с (p-1).
    """
    phi = p - 1
    while True:
        c = random.randint(2, phi - 1)
        if math.gcd(c, phi) == 1:
            d = mod_inverse(c, phi)
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
        if fermat_primality_test(candidate):
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
                
                processed_val = fast_exp_mod(val, key, p)
                
                f_out.write(processed_val.to_bytes(block_size_out, byteorder='big'))
        return True
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False
    
def calculate_file_hash(filepath):
    """
    Вычисляет хэш SHA-256 файла для проверки его целостности.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            # Читаем файл по частям для экономии памяти
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None
    
                            ######################
                            ### ЛАБАРАТОРНАЯ 5 ###
                            ######################

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

    p, q = generate_safe_prime(min_p, max_p)
    g = find_primitive_root(p, q)

    x = random.randint(2, p-1)
    y = fast_exp_mod(g, x, p)

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
                
                a = fast_exp_mod(g, k, p)
                b = (fast_exp_mod(public_key_y, k, p) * m) % p

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
                
                m = fast_exp_mod(a, p - 1 - private_key_x, p) * b % p
                
                f_out.write(m.to_bytes(1, byteorder='big'))
        return True
    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    
                            ######################
                            ### ЛАБАРАТОРНАЯ 6 ###
                            ######################

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
        if fermat_primality_test(p_candidate):
            p = p_candidate
            break

    while True:
        q_candidate = random.randint(min_p, max_p)
        if fermat_primality_test(q_candidate) and q_candidate != p:
            q = q_candidate
            break
        
    n_big = p*q

    phi = (p-1)*(q-1)
    while True:
        d_candidate = random.randint(2, phi - 1)
        if math.gcd(d_candidate, phi) == 1:
            public_key = d_candidate
            break

    private_key = mod_inverse(public_key, phi)

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
                
                process_val = fast_exp_mod(val, key, n_big)
                
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


                            ######################
                            ### ЛАБАРАТОРНАЯ 7 ###
                            ######################

def vernam_process_file(input_path, output_path, key, block_size_in, block_size_out):
    """
    
    """
    try:
        with open(input_path, 'rb') as f_in, open(output_path, 'wb') as f_out:
            while True:
                block = f_in.read(block_size_in)
                if not block:
                    break
                
                m = int.from_bytes(block, byteorder='big')

                e = m ^ key

                f_out.write(e.to_bytes(block_size_out, byteorder='big'))
        
        return True

    except FileNotFoundError:
        print(f"Ошибка: Файл не найден по пути {input_path}")
        return False
    
    except Exception as e:
        print(f"Произошла ошибка при обработке файла: {e}")
        return False