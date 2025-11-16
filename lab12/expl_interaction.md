# Объяснения взаимодействие клиента и сервера.
---

Объясняет полное взаимодействие клиента с сервером. Рассказывает последовательный вызов функций

---
---
### Шаг 0: Запуск и Локальная Подготовка Клиента

**Цель:** Подготовить браузер к игре до того, как он даже подключится к серверу.

**Что происходит:** Пользователь открывает `index.html` в своем браузере. Прежде чем будет установлено соединение с сервером, JavaScript немедленно выполняется.

1.  **Вызов `init()`**: Это точка входа.
    ```javascript
    // script.js
    document.addEventListener('DOMContentLoaded', init);

    function init() {
        // 1. Вызывается генерация "шпаргалки"
        playerCardMap = generateCardIdentityMap();
        addLog('Локальный словарь карт сгенерирован.');
        // 2. Устанавливается соединение с сервером
        connectSocket();
        // 3. Навешиваются обработчики на кнопки
        setupEventListeners();
    }
    ```

2.  **Создание "Шпаргалки" - `generateCardIdentityMap()`**:
    Эта функция создает локальный словарь, который переводит числовые значения в "лица" карт. Это критически важно, так как именно этот словарь позволит клиенту в конце узнать свои карты, не спрашивая у сервера.
    ```javascript
    // script.js
    function generateCardIdentityMap() {
        const suits = ['♠', '♥', '♦', '♣'];
        const ranks = ['2', '3', /* ... */, 'K', 'A'];
        let card_id = 0;
        const newMap = {};
        for (const suit of suits) {
            for (const rank of ranks) {
                // Создается запись: 100 -> '2♠', 101 -> '3♠', ... 151 -> 'A♣'
                newMap[100 + card_id] = rank + suit;
                card_id++;
            }
        }
        return newMap; // Результат сохраняется в глобальную переменную playerCardMap
    }
    ```
    **Состояние:** У клиента теперь есть полный словарь `playerCardMap`. Сервер об этом не знает. Сетевого взаимодействия нет.

---

### Шаг 1: Подключение к Серверу и Формирование Игровой Комнаты

**Цель:** Установить соединение, зарегистрировать игрока на сервере и дождаться необходимого количества участников.

**Процесс:**
1.  Клиент устанавливает WebSocket-соединение.
2.  Сервер регистрирует нового игрока, дает ему имя и ID, и сообщает всем остальным о новом участнике.

**Технический путь:**

1.  `script.js` -> `connectSocket()`:
    ```javascript
    // script.js
    function connectSocket() {
        socket = io(); // Инициирует WebSocket-соединение с сервером
        // ...
    }
    ```
2.  `app.py` -> `@socketio.on('connect')`:
    Сервер ловит событие подключения.
    ```python
    # app.py
    @socketio.on('connect')
    def handle_connect():
        global mental_poker_game
        # ... (создает игру, если ее нет) ...
        player_name = f"Player_{random.randint(100, 999)}"
        player_id = request.sid // Уникальный ID сессии
        
        // Добавляет игрока в объект игры
        success, message = mental_poker_game.add_player(player_id, player_name, request.sid)
        
        if success:
            join_room("main")
            // Отправляет успешное сообщение ТОЛЬКО этому клиенту
            emit('join_success', {'player_id': player_id, 'player_name': player_name, ...})
            // Сообщает ВСЕМ ОСТАЛЬНЫМ о новом игроке
            emit('player_joined', {'player_name': player_name}, room="main", include_self=False)
            // Рассылает всем обновленное состояние игры
            mental_poker_game.emit_game_state()
    ```
3.  `script.js` -> `socket.on('join_success', ...)`:
    Клиент получает подтверждение, сохраняет свой `playerId` и `playerName`.

**Состояние:** Игроки подключены. Игра в фазе `waiting`. Каждый игрок знает состав комнаты.

---

### Шаг 2: Старт Игры и Криптографический "Рукопожатие"

**Цель:** Инициировать игру, сгенерировать общие криптографические параметры (`P`) и позволить каждому клиенту создать свои личные ключи.

**Процесс:**
1.  Первый подключившийся игрок нажимает кнопку "Начать игру".
2.  Сервер генерирует простое число `P`, создает эталонную колоду и рассылает `P` всем игрокам.
3.  Каждый игрок, получив `P`, генерирует свою пару ключей `(C, D)`.

**Технический путь:**

1.  Клиент нажимает кнопку -> `script.js` -> `nextPhase()` -> `socket.emit('next_phase', ...)`
2.  `app.py` -> `@socketio.on('next_phase')` -> `mental_poker_game.py` -> `next_game_phase()`:
    ```python
    # mental_poker_game.py
    def next_game_phase(self, player_id):
        if self.phase == "waiting" and self.can_start_game():
            self.start_game()
    ```
3.  `mental_poker_game.py` -> `start_game()`:
    ```python
    # mental_poker_game.py
    def start_game(self):
        // 1. Генерирует P
        self.p, self.q = self.generate_sophie_germain_prime()
        self._write_to_log(f"  Sophie Germain Prime generated: P={self.p}, Q={self.q}")
        
        // 2. Создает эталонную колоду и логирует ее
        self.initialize_deck() 
        
        self.phase = "key_exchange"
        
        // 3. Рассылает P всем игрокам
        for player in self.players.values():
            self.socketio.emit('receive_prime', {'p': self.p, 'q': self.q}, room=player['socket_id'])
    ```
    В этот момент в **лог-файл** записывается раздел `--- 1. INITIAL DECK STATE ---` с полным списком карт.

4.  `script.js` -> `socket.on('receive_prime', ...)`:
    ```javascript
    // script.js
    socket.on('receive_prime', (data) => {
        currentP = BigInt(data.p); // Сохраняет P
        generateKeys();             // Запускает генерацию ключей
    });
    ```
5.  `script.js` -> `generateKeys()`:
    Эта функция выполняет чисто математические операции для создания пары `(playerC, playerD)` таких, что `(playerC * playerD) % (P - 1) == 1`. **Эти ключи остаются в браузере.**

**Состояние:** Игра в фазе `key_exchange`. У сервера есть `P` и эталонная колода. У каждого клиента есть `P` и своя уникальная пара секретных ключей `(C, D)`.

---

### Шаг 3: Эстафета Шифрования и Перемешивания

**Цель:** Превратить отсортированную колоду в случайный набор зашифрованных данных.

**Процесс:**
1.  Лидер нажимает "Начать шифрование".
2.  Сервер запускает "эстафету", отправляя колоду первому игроку.
3.  Игрок 1 шифрует каждую карту ключом `C1`, перемешивает массив и возвращает серверу.
4.  Сервер получает результат, логирует его и передает Игроку 2, и так далее.

**Технический путь:**

1.  Лидер -> `next_phase` -> `mental_poker_game.py` -> `next_game_phase()` -> `start_encryption_phase()`:
    ```python
    # mental_poker_game.py
    def start_encryption_phase(self):
        self.phase = "encryption"
        self.processing_phase = "encryption"
        # ...
        self._write_to_log("--- 2. DECK ENCRYPTION PHASE ---")
        // Отправляет колоду первому игроку
        self.socketio.emit('encrypt_cards', {'cards': self.cards_to_process, ...})
    ```
2.  `script.js` (у Игрока 1) -> `socket.on('encrypt_cards', ...)` -> `encryptCards()`:
    ```javascript
    // script.js
    function encryptCards(cards) {
        // Шифрует каждое значение в массиве
        const encryptedCards = cards.map(card => ({
            ...card,
            encrypted_value: Number(modPow(BigInt(card.encrypted_value), playerC, currentP))
        }));
        // Перемешивает сам массив
        for (let i = encryptedCards.length - 1; i > 0; i--) { ... }
        // Отправляет результат обратно
        socket.emit('encrypted_cards', { player_id: playerId, cards: encryptedCards });
    }
    ```
3.  `mental_poker_game.py` -> `handle_encrypted_cards()`:
    ```python
    # mental_poker_game.py
    def handle_encrypted_cards(self, player_id, encrypted_cards):
        // ...
        self.cards_to_process = encrypted_cards // Сохраняет перемешанный порядок
        
        // Для лога создает временную отсортированную копию
        sorted_for_log = sorted(encrypted_cards, key=lambda x: x.get('id', -1))
        self._write_to_log(f"  Deck state after encryption by '{player_name}':")
        for card in sorted_for_log: // Пишет в лог
            self._write_to_log(f"    ID {card['id']:02d} -> Encrypted Value: {card['encrypted_value']}")
        
        // ... передает cards_to_process (перемешанную) следующему игроку
        // или завершает фазу.
    ```
**Состояние:** После завершения эстафеты на сервере в `self.deck` лежит массив из 52 карт, каждая из которых зашифрована ключами всех игроков, и порядок которых абсолютно случаен.

---

### Шаг 4: Раздача Карт и Начало Расшифровки

**Цель:** Раздать карты и запустить процесс их расшифровки.

**Процесс:**
1.  Сервер "снимает" по 2 карты с верха колоды (`.pop()`) для каждого игрока.
2.  Сервер запускает процесс круговой расшифровки для карт первого игрока.

**Технический путь:**

1.  `mental_poker_game.py` -> `start_card_dealing()`:
    *   Берет карты из `self.deck` и присваивает их игрокам.
    *   Пишет в **лог-файл** раздел `--- 3. DEALING CARDS TO PLAYERS ---`, указывая, какие ID и зашифрованные значения были розданы.
    *   Вызывает `start_private_cards_decryption()`.

2.  `mental_poker_game.py` -> `start_private_cards_decryption()`:
    *   Пишет в лог заголовок `--- 4. PRIVATE CARDS DECRYPTION ---`.
    *   Вызывает `_start_decryption_for_current_target()`.

3.  `mental_poker_game.py` -> `_start_decryption_for_current_target()`:
    *   Берет карты первого игрока (цели).
    *   Находит первого "помощника" (следующего по кругу).
    *   Отправляет ему карты цели через `socketio.emit('decrypt_cards', ...)`

---

### Шаг 5: Круговая Расшифровка (Сердце Протокола)

**Цель:** Позволить каждому игроку узнать свои карты, не раскрывая их другим.

**Процесс:**
Это сложная цепочка. Для карт Игрока 1: Сервер -> Игрок 2 -> Сервер -> Игрок 3 -> Сервер -> ... -> Игрок 1.

**Технический путь:**

1.  `script.js` (у "помощника") -> `socket.on('decrypt_cards', ...)` -> `decryptCards()`:
    *   Получает карты, применяет свой ключ `D` для снятия своего "замка" и отправляет результат обратно на сервер (`socket.emit('decrypted_cards', ...)`).

2.  `mental_poker_game.py` -> `handle_decrypted_cards()`:
    *   Получает частично расшифрованные карты.
    *   **Логирует** ID и новые `encrypted_value` после расшифровки "помощником".
    *   Если круг не закончен, передает карты следующему "помощнику".
    *   Если круг закончен, отправляет финальное событие `final_private_decryption` **только владельцу карт**.

3.  `script.js` (у "владельца") -> `socket.on('final_private_decryption', ...)`:
    *   Получает свои карты, зашифрованные только его ключом `C`.
    *   Применяет свой ключ `D`.
    *   Получает исходное числовое значение (например, `115`).
    *   Использует `playerCardMap` (`playerCardMap[115]`) чтобы узнать "лицо" карты (`'A♠'`).
    *   Сохраняет результат в `revealedHand` и обновляет свой интерфейс. **Ничего не отправляется на сервер.**

**Состояние:** Процесс повторяется для карт каждого игрока. В итоге каждый игрок знает свои карты, но никто другой (включая сервер) их не знает.

---

### Шаг 6: Общие Карты и Завершение Игры

**Процесс:**
*   **Флоп, Терн, Ривер:** Лидер нажимает кнопку "Далее". Сервер запускает `deal_table_cards()`. Процесс расшифровки общих карт аналогичен шагу 5, но в нем участвуют все игроки, и в конце сервер сам определяет "лица" карт и рассылает их всем в `game_state`. Промежуточные значения также **логируются** (`--- 5. DEALING FLOP ---` и т.д.).
*   **Завершение:** Лидер нажимает "Завершить игру".

---

### Шаг 7: Финальный Аудит

**Цель:** Собрать все ключи и завершить лог, чтобы сделать игру полностью проверяемой.

**Процесс:**
1.  Сервер запрашивает у всех ключи.
2.  Клиенты отправляют свои `C` и `D`.
3.  Сервер записывает их в лог.

**Технический путь:**

1.  `mental_poker_game.py` -> `complete_game()`:
    *   Отправляет всем `socketio.emit('game_completed', ...)` и затем `request_keys_from_players()`.

2.  `script.js` -> `socket.on('request_keys', ...)` -> `automaticallySubmitKeys()`:
    *   Отправляет `playerC` и `playerD` на сервер через `socket.emit('submit_keys', ...)`

3.  `app.py` -> `@socketio.on('submit_keys')` -> `mental_poker_game.py` -> `handle_player_keys()`:
    *   Получает ключи, записывает их в лог-файл в раздел **`--- 6. REQUESTING PLAYER KEYS FOR AUDIT ---`**.
    *   Когда все ключи получены, вызывает `_write_keys_to_log()` и `_write_final_summary()`, завершая лог-файл.

**Финальное состояние:** Игра окончена. На диске сервера лежит `mental_poker_YYYYMMDD_HHMMSS.log`, содержащий исчерпывающую информацию для математической проверки каждого шага раздачи.