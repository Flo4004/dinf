# client.py
import random
import hashlib
import crypt_lib as cl
import server # Импортируем модуль сервера

class Voter:
    def __init__(self, name, voting_server):
        self.name = name
        self.server = voting_server

    def vote(self, choice):
        """
        Основной метод голосования.
        choice: "да", "нет", "воздержался"
        """
        # Кодирование выбора
        mapping = {"да": 1, "нет": 2, "воздержался": 3}
        if choice not in mapping:
            print("Некорректный выбор")
            return
        v = mapping[choice]

        # 1. Получаем открытые ключи сервера
        N, D = self.server.get_public_key()

        # 2. Формируем число n = rnd | v
        # rnd - 512 бит (в теории), здесь сделаем чуть меньше, чтобы влезло в N при генерации малых ключей
        rnd = random.getrandbits(32) 
        # Сдвигаем rnd влево на 2 бита и добавляем v
        n = (rnd << 2) | v
        
        # 3. Вычисляем хеш h = SHA3(n)
        h_bytes = hashlib.sha3_256(str(n).encode('utf-8')).digest()
        h = int.from_bytes(h_bytes, byteorder='big')
        h = h % N # Корректировка под размер N (см. комментарий в server.py)

        # 4. Формируем множитель r, взаимнопростой с N
        while True:
            r = random.randint(2, N - 1)
            if cl.mod_inverse(r, N) != 0: # Если обратный элемент существует, значит взаимнопросты
                break
        
        # 5. Ослепление (Blinding): h' = (h * r^D) mod N
        # D - это публичный ключ (по условию задачи D и C поменяны местами относительно классики RSA,
        # но мы следуем алгоритму: D - публичный, C - приватный).
        # Алгоритм: Алиса использует D для ослепления? 
        # В условии сказано: h'=(h*(r^d))mod N. Но D известен всем. Ок.
        h_prime = (h * pow(r, D, N)) % N

        print(f"[{self.name}] Отправляет слепой хеш на подпись...")
        
        # 6. Алиса отправляет h' на сервер (Защищенный канал)
        try:
            s_prime = self.server.sign_blind_ballot(self.name, h_prime)
        except Exception as e:
            print(f"[{self.name}] Ошибка сервера: {e}")
            return

        # 7. Алиса снимает ослепление: s = s' * r^(-1) mod N
        r_inv = cl.mod_inverse(r, N)
        s = (s_prime * r_inv) % N

        print(f"[{self.name}] Подпись получена и расшифрована. Отправка бюллетеня...")

        # 8. Алиса отправляет <n, s> на сервер (Анонимный канал)
        # Сервер не знает, какой именно h' соответствовал этому n, так как n был скрыт r.
        self.server.receive_filled_ballot(n, s)


# --- Демонстрация работы ---
if __name__ == "__main__":
    # 1. Запуск сервера
    srv = server.VotingServer()
    print("Сервер запущен. Параметры сгенерированы.")

    # 2. Создание участников
    alice = Voter("Alice", srv)
    bob = Voter("Bob", srv)
    leha = Voter("Leha", srv)
    lera = Voter("Lera", srv)

    # 3. Голосование
    alice.vote("да")
    bob.vote("нет")
    leha.vote("да")
    lera.vote("воздержался")
    
    # Попытка двойного голосования (должна быть ошибка на этапе получения подписи)
    alice.vote("воздержался")


    # 4. Подсчет результатов
    srv.show_results()