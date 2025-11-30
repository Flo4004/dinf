# server.py
import random
import math
import hashlib
import crypt_lib as cl

def rsa_generate_params(min_p=255, max_p=65535):
    """
    Генерирует полный набор параметров для протокола RSA.
    (Код предоставлен в условии)
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

class VotingServer:
    def __init__(self):
        # Генерация ключей при запуске сервера
        # Используем параметры побольше для надежности хеширования, 
        # но в рамках учебного примера можно оставить стандартные.
        # N - модуль, D - публичный ключ, C - приватный ключ
        self.N, self.D, self.C = rsa_generate_params(min_p=1000, max_p=50000)
        
        # База данных проголосовавших пользователей (для проверки прав)
        self.voters_who_received_ballots = set()
        
        # Открытая база данных принятых голосов
        self.ballot_box = [] 

    def get_public_key(self):
        """Возвращает открытые данные (N, D)."""
        return self.N, self.D

    def sign_blind_ballot(self, voter_id, blind_hash):
        """
        Этап 1: Сервер подписывает зашифрованный (слепой) хеш бюллетеня.
        Проверяет, имеет ли право voter_id голосовать.
        """
        if voter_id in self.voters_who_received_ballots:
            raise Exception(f"Пользователь {voter_id} уже получил бюллетень!")
        
        # Отмечаем, что бюллетень выдан
        self.voters_who_received_ballots.add(voter_id)
        
        # Подпись: s' = (h'^C) mod N
        # Используем pow(base, exp, mod) для эффективности
        s_prime = pow(blind_hash, self.C, self.N)
        
        return s_prime

    def receive_filled_ballot(self, n, s):
        """
        Этап 2: Анонимный канал. Сервер получает пару <n, s>.
        Проверяет подпись и учитывает голос.
        """
        # 1. Вычисляем хеш от n: h = SHA3(n)
        # В Python hashlib.sha3_256
        h_bytes = hashlib.sha3_256(str(n).encode('utf-8')).digest()
        h = int.from_bytes(h_bytes, byteorder='big')
        
        # Важно: В учебном примере с малыми ключами h может быть > N.
        # По алгоритму должно быть h < N. Приведем h по модулю N для корректности математики
        # в данном конкретном примере (в реальности N 2048 бит > SHA3 256 бит).
        h = h % self.N

        # 2. Проверяем подпись: SHA3(n) == (s^D) mod N
        # s^D mod N
        decrypted_signature = pow(s, self.D, self.N)
        
        if h == decrypted_signature:
            print(f"[Server] Бюллетень валиден. Голос принят.")
            self.ballot_box.append(n)
            return True
        else:
            print(f"[Server] ОШИБКА: Подпись недействительна!")
            return False

    def show_results(self):
        """Подсчет и вывод результатов (декодирование n)."""
        print("\n--- Результаты голосования ---")
        results = {"да": 0, "нет": 0, "воздержался": 0}
        
        for n in self.ballot_box:
            # Извлекаем данные из числа n
            # n = rnd | v. v - последние биты.
            # Допустим, мы кодировали v как простое число в конце
            # Для простоты декодирования в примере мы будем считать v последней цифрой 
            # (так как rnd сдвигался, см. клиент).
            
            # Извлекаем код голосования (последние 8 бит, например, или просто по значению)
            # В клиенте мы сделаем v: 1=да, 2=нет, 3=воздержался
            
            # Декодинг (обратный сдвиг)
            v = n & 0b11 # Берем последние 2 бита (достаточно для 0-3)
            
            if v == 1: results["да"] += 1
            elif v == 2: results["нет"] += 1
            elif v == 3: results["воздержался"] += 1
            
        print(results)