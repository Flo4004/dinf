# Объяснение серверной части программа


### **1. `__init__(self, socketio)` - Конструктор класса**

```python
def __init__(self, socketio):
    self.socketio = socketio
    self.room_id = "main"
    self.players = {}
    self.player_order = []
    self.deck = []
    self.table_cards = []
    self.phase = 'waiting'
    self.p = None
    self.q = None
    self.current_player_index = 0
    self.game_log = []
    self.cards_to_process = []
    self.processing_phase = None
    self.game_start_time = datetime.now()
    self.log_file = None
    self._init_log_file()
    self.received_keys = {}
    self.keys_collection_phase = False
    self.card_identity_map = {}
    self.decryption_target_player_index = 0
```

**Что делает:**
- **Инициализирует ВСЕ переменные игры**
- `socketio` - объект для связи с клиентами через WebSocket
- `players` - словарь вида `{player_id: {данные игрока}}`
- `player_order` - список порядка ходов игроков
- `deck` - колода карт (список словарей)
- `table_cards` - карты на столе
- `phase` - текущая фаза игры: 'waiting', 'key_exchange', 'encryption', 'dealing', 'flop', 'turn', 'river', 'showdown', 'completed'
- `p, q` - простые числа для криптографии
- `current_player_index` - индекс текущего активного игрока
- `game_log` - список сообщений игрового лога
- `cards_to_process` - временный список карт для обработки
- `processing_phase` - текущая фаза обработки: 'encryption', 'decryption_private', 'decryption_table'
- `card_identity_map` - словарь сопоставления ID карт с их названиями
- `decryption_target_player_index` - индекс игрока, чьи карты сейчас расшифровываются

---

### **2. `_init_log_file(self)` - Инициализация файла логов**

```python
def _init_log_file(self):
    logs_dir = "game_logs"
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)
    timestamp = self.game_start_time.strftime("%Y%m%d_%H%M%S")
    self.log_file = os.path.join(logs_dir, f"mental_poker_{timestamp}.log")
    header = f"""--- MENTAL POKER GAME LOG ---
Game Start: {self.game_start_time.strftime("%Y-%m-%d %H:%M:%S")}
"""
    with open(self.log_file, 'w', encoding='utf-8') as f:
        f.write(header)
```

**Что делает:**
- Создает папку `game_logs` если она не существует
- Генерирует уникальное имя файла с временной меткой
- Записывает заголовок с временем начала игры
- **Цель:** Создать структурированную систему логирования для отладки и аудита

---

### **3. `_write_to_log(self, message)` - Запись в лог-файл**

```python
def _write_to_log(self, message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    with open(self.log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
```

**Что делает:**
- Добавляет временную метку к сообщению
- Открывает файл в режиме дозаписи ('a')
- Записывает форматированную строку в файл
- **Цель:** Детальное протоколирование всех событий игры

---

### **4. `add_log(self, message, player_id=None)` - Добавление в игровой лог**

```python
def add_log(self, message, player_id=None):
    timestamp = datetime.now().strftime("%H:%M:%S")
    player_name = self.players[player_id]['name'] if player_id else "Система"
    log_entry = f"{timestamp} - {player_name}: {message}"
    self.game_log.append(log_entry)
    self.socketio.emit('log_update', {'log': log_entry}, room=self.room_id)
```

**Что делает:**
- Форматирует сообщение для отображения игрокам
- Если `player_id=None` - сообщение от системы
- Добавляет запись в `self.game_log`
- Рассылает сообщение всем клиентам через WebSocket
- **Цель:** Информирование игроков о событиях в реальном времени

---

### **5. `add_player(self, player_id, name, socket_id)` - Добавление игрока**

```python
def add_player(self, player_id, name, socket_id):
    if len(self.players) >= 5:
        return False, "Комната заполнена"
    self.players[player_id] = {
        'player_id': player_id, 
        'name': name, 
        'socket_id': socket_id, 
        'cards': [], 
        'active': False
    }
    self.player_order.append(player_id)
    self._write_to_log(f"[JOIN] Player '{name}' (ID: {player_id}) connected.")
    return True, f"Игрок {name} присоединился"
```

**Что делает:**
- Проверяет что в комнате меньше 5 игроков
- Создает запись игрока в словаре `players`
- Добавляет ID игрока в порядок ходов
- Логирует присоединение
- Возвращает статус успеха/ошибки
- **Цель:** Управление подключением новых игроков

---

### **6. `remove_player(self, player_id)` - Удаление игрока**

```python
def remove_player(self, player_id):
    if player_id in self.players:
        player_name = self.players[player_id]['name']
        if player_id in self.player_order: 
            self.player_order.remove(player_id)
        del self.players[player_id]
        self._write_to_log(f"[LEAVE] Player '{player_name}' left.")
```

**Что делает:**
- Удаляет игрока из всех структур данных
- Убирает из `player_order` и `players`
- Логирует выход игрока
- **Цель:** Корректная обработка отключения игроков

---

### **7. `can_start_game(self)` - Проверка возможности старта**

```python
def can_start_game(self):
    return len(self.players) >= 2
```

**Что делает:**
- Простая проверка что игроков достаточно для начала
- **Цель:** Предотвратить начало игры с одним игроком

---

### **8. `generate_sophie_germain_prime(self, bits=32)` - Генерация простых чисел**

```python
def generate_sophie_germain_prime(self, bits=32):
    while True:
        q = sympy.randprime(2**(bits-1), 2**bits)
        p = 2 * q + 1
        if sympy.isprime(p): 
            return p, q
```

**Что делает:**
- В бесконечном цикле генерирует простое число `q`
- Вычисляет `p = 2*q + 1` (простое число Софи Жермен)
- Проверяет что `p` тоже простое
- Возвращает пару `(p, q)`
- **Цель:** Создать криптографически стойкие параметры для шифрования

---

### **9. `initialize_deck(self)` - Инициализация колоды**

```python
def initialize_deck(self):
    suits = ['♠', '♥', '♦', '♣']
    ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
    temp_deck = []
    card_id = 0
    for suit in suits:
        for rank in ranks:
            numeric_value = 100 + card_id
            temp_deck.append({
                'id': card_id, 
                'value': rank + suit, 
                'numeric_value': numeric_value, 
                'encrypted_value': numeric_value
            })
            card_id += 1
    
    self._write_to_log("--- 1. INITIAL DECK STATE ---")
    for card in temp_deck:
        self._write_to_log(f"  ID {card['id']:02d}: {card['value']:<3} (Numeric Value: {card['numeric_value']})")
    
    self.card_identity_map = {card['id']: card['value'] for card in temp_deck}
    for card in temp_deck: 
        del card['value']
    self.deck = temp_deck
```

**Что делает:**
- Создает стандартную колоду из 52 карт
- Каждой карте присваивает уникальный ID и числовое значение
- Создает `card_identity_map` для связи ID с читаемыми названиями
- **УДАЛЯЕТ** поле `value` из карт для безопасности
- Логирует исходное состояние колоды
- **Цель:** Подготовить колоду для безопасного шифрования

---

### **10. `start_game(self)` - Начало игры**

```python
def start_game(self):
    if not self.can_start_game(): 
        return False, "Нужно минимум 2 игрока"
    
    player_names = [p['name'] for p in self.players.values()]
    self._write_to_log(f"--- GAME STARTED with {len(player_names)} players: {', '.join(player_names)} ---")
    
    self.p, self.q = self.generate_sophie_germain_prime()
    self._write_to_log(f"  Sophie Germain Prime generated: P={self.p}, Q={self.q}")
    
    self.initialize_deck()
    self.phase = "key_exchange"
    self.add_log("Игра началась! Сервер сгенерировал P и Q")
    for player in self.players.values():
        self.socketio.emit('receive_prime', {'p': self.p, 'q': self.q}, room=player['socket_id'])
    return True, "Игра началась"
```

**Что делает:**
- Проверяет возможность старта
- Логирует начало игры и список игроков
- Генерирует простые числа `p` и `q`
- Инициализирует колоду
- Устанавливает фазу `key_exchange`
- Рассылает простые числа всем игрокам
- **Цель:** Запустить игровой процесс и подготовить криптографические параметры

---

### **11. `start_encryption_phase(self)` - Начало фазы шифрования**

```python
def start_encryption_phase(self):
    self.phase = "encryption"
    self.processing_phase = "encryption"
    self.current_player_index = 0
    self.cards_to_process = self.deck.copy()
    first_player_id = self.player_order[0]
    self.players[first_player_id]['active'] = True
    self.add_log("Начинается шифрование колоды")
    self._write_to_log("--- 2. DECK ENCRYPTION PHASE ---")
    self.socketio.emit('encrypt_cards', {
        'cards': self.cards_to_process, 
        'player_index': self.current_player_index
    }, room=self.players[first_player_id]['socket_id'])
```

**Что делает:**
- Устанавливает фазу шифрования
- Копирует колоду во временный буфер `cards_to_process`
- Активирует первого игрока
- Логирует начало фазы
- Отправляет колоду первому игроку для шифрования
- **Цель:** Запустить процесс последовательного шифрования колоды

---

### **12. `handle_encrypted_cards(self, player_id, encrypted_cards)` - Обработка зашифрованных карт**

```python
def handle_encrypted_cards(self, player_id, encrypted_cards):
    if self.processing_phase != "encryption" or player_id != self.player_order[self.current_player_index]: 
        return False, "Invalid action"
        
    player_name = self.players[player_id]['name']
    
    # Ключевое изменение: сохраняем перемешанный порядок
    self.cards_to_process = encrypted_cards
    
    # Для логов создаем отсортированную копию
    sorted_for_log = sorted(encrypted_cards, key=lambda x: x.get('id', -1))
    
    # Логируем отсортированную версию
    self._write_to_log(f"  Deck state after encryption by '{player_name}':")
    for card in sorted_for_log:
        self._write_to_log(f"    ID {card['id']:02d} -> Encrypted Value: {card['encrypted_value']}")
    
    self.players[player_id]['active'] = False
    self.add_log("зашифровал колоду", player_id=player_id)
    
    self.current_player_index += 1
    if self.current_player_index < len(self.player_order):
        # Передаем следующему игроку ПЕРЕМЕШАННУЮ колоду
        next_player_id = self.player_order[self.current_player_index]
        self.players[next_player_id]['active'] = True
        self.socketio.emit('encrypt_cards', {
            'cards': self.cards_to_process, 
            'player_index': self.current_player_index
        }, room=self.players[next_player_id]['socket_id'])
    else:
        # Все игроки зашифровали
        self.deck = self.cards_to_process
        self.cards_to_process = []
        self.processing_phase = None
        self._write_to_log("[ENCRYPTION] Final deck is fully encrypted and shuffled.")
        self.start_card_dealing()
    return True, "Encryption processed"
```

**Что делает:**
- Проверяет что действие валидно
- **Сохраняет перемешанный порядок карт** (важное изменение!)
- Логирует результат шифрования
- Передает колоду следующему игроку
- Когда все игроки зашифровали - сохраняет финальную колоду и начинает раздачу
- **Цель:** Координация процесса последовательного шифрования

---

### **13. `start_card_dealing(self)` - Раздача карт**

```python
def start_card_dealing(self):
    self.phase = "dealing"
    self.add_log("Раздача карт...")
    self._write_to_log("--- 3. DEALING CARDS TO PLAYERS ---")
    for player_id in self.player_order:
        player_cards = [self.deck.pop() for _ in range(2) if self.deck]
        self.players[player_id]['cards'] = player_cards
        player_name = self.players[player_id]['name']
        
        card_values = [c['encrypted_value'] for c in player_cards]
        card_ids_for_log = [c['id'] for c in player_cards]
        self._write_to_log(f"  Dealt to '{player_name}': Card IDs {card_ids_for_log} with Encrypted Values {card_values}")
        
    self.start_private_cards_decryption()
```

**Что делает:**
- Устанавливает фазу раздачи
- Каждому игроку раздает по 2 карты с вершины колоды
- Сохраняет карты в данные игрока
- Логирует какие карты кому розданы
- Запускает процесс расшифровки личных карт
- **Цель:** Распределение зашифрованных карт между игроками

---

### **14. `start_private_cards_decryption(self)` - Начало расшифровки личных карт**

```python
def start_private_cards_decryption(self):
    self.processing_phase = 'decryption_private'
    self.decryption_target_player_index = 0
    self._write_to_log("--- 4. PRIVATE CARDS DECRYPTION ---")
    self._start_decryption_for_current_target()
```

**Что делает:**
- Устанавливает фазу расшифровки личных карт
- Сбрасывает индекс целевого игрока на 0 (первый игрок)
- Логирует начало фазы
- Запускает процесс для первого игрока
- **Цель:** Координация расшифровки карт игроков

---

### **15. `_start_decryption_for_current_target(self)` - Запуск расшифровки для текущего цели**

```python
def _start_decryption_for_current_target(self):
    if self.decryption_target_player_index >= len(self.player_order):
        self.processing_phase = None
        self.phase = "flop"
        self.add_log("Карты игроков расшифрованы. Начинается игра.")
        self._write_to_log("[DECRYPTION-PRIVATE] All player hands processed.")
        self.emit_game_state()
        return

    target_player_id = self.player_order[self.decryption_target_player_index]
    target_player_name = self.players[target_player_id]['name']
    self.add_log(f"Начинается расшифровка карт для {target_player_name}...", player_id=target_player_id)
    self._write_to_log(f"  Starting decryption circle for {target_player_name}'s hand.")

    self.cards_to_process = self.players[target_player_id]['cards']
    self.current_player_index = (self.decryption_target_player_index + 1) % len(self.player_order)
    
    first_decryptor_id = self.player_order[self.current_player_index]
    self.players[first_decryptor_id]['active'] = True
    self.socketio.emit('decrypt_cards', {
        'cards': self.cards_to_process, 
        'phase': 'private'
    }, room=self.players[first_decryptor_id]['socket_id'])
```

**Что делает:**
- Проверяет все ли игроки обработаны
- Определяет чьи карты сейчас расшифровываются
- Устанавливает следующего игрока в цепочке расшифровки (не самого владельца!)
- Активирует первого расшифровщика и отправляет ему карты
- **Цель:** Организация циклической расшифровки карт каждого игрока

---

### **16. `handle_decrypted_cards(self, player_id, decrypted_cards, phase)` - Обработка расшифрованных карт**

```python
def handle_decrypted_cards(self, player_id, decrypted_cards, phase):
    if self.processing_phase != f"decryption_{phase}" or player_id != self.player_order[self.current_player_index]: 
        return False, "Invalid action"

    current_player_name = self.players[player_id]['name']
    self.cards_to_process = decrypted_cards
    self.players[player_id]['active'] = False

    if phase == 'private':
        # Обработка личных карт
        target_player_name = self.players[self.player_order[self.decryption_target_player_index]]['name']
        dec_vals = [c['encrypted_value'] for c in self.cards_to_process]
        card_ids_for_log = [c['id'] for c in self.cards_to_process]
        self._write_to_log(f"    '{current_player_name}' decrypted hand of '{target_player_name}' (IDs {card_ids_for_log}). New values: {dec_vals}")
        
        next_player_index = (self.current_player_index + 1) % len(self.player_order)
        if next_player_index == self.decryption_target_player_index:
            # Все расшифровали, передаем владельцу
            target_player_id = self.player_order[self.decryption_target_player_index]
            self.socketio.emit('final_private_decryption', {
                'cards': self.cards_to_process
            }, room=self.players[target_player_id]['socket_id'])
            self.decryption_target_player_index += 1
            self._start_decryption_for_current_target()
        else:
            # Передаем следующему расшифровщику
            self.current_player_index = next_player_index
            next_decryptor_id = self.player_order[self.current_player_index]
            self.players[next_decryptor_id]['active'] = True
            self.socketio.emit('decrypt_cards', {
                'cards': self.cards_to_process, 
                'phase': 'private'
            }, room=self.players[next_decryptor_id]['socket_id'])
        return True, "Private cards processed"

    if phase == 'table':
        # Обработка карт на столе
        dec_vals = [c['encrypted_value'] for c in self.cards_to_process]
        card_ids_for_log = [c['id'] for c in self.cards_to_process]
        self._write_to_log(f"    '{current_player_name}' decrypted table cards (IDs {card_ids_for_log}). New values: {dec_vals}")
        
        self.current_player_index += 1
        if self.current_player_index < len(self.player_order):
            # Передаем следующему игроку
            next_player_id = self.player_order[self.current_player_index]
            self.players[next_player_id]['active'] = True
            self.socketio.emit('decrypt_cards', {
                'cards': self.cards_to_process, 
                'phase': 'table'
            }, room=self.players[next_player_id]['socket_id'])
        else:
            # Все игроки расшифровали
            for card in self.cards_to_process:
                card['value'] = self.card_identity_map[card['id']]
            decrypted_ids = {c['id'] for c in self.cards_to_process}
            updated_table = [c for c in self.table_cards if c['id'] not in decrypted_ids] + self.cards_to_process
            self.table_cards = sorted(updated_table, key=lambda c: c.get('id', -1))
            # Переход к следующей фазе игры
            if self.phase == "flop": self.phase = "turn"
            elif self.phase == "turn": self.phase = "river"
            elif self.phase == "river": self.phase = "showdown"
            self.processing_phase = None
        return True, "Table cards processed"
    return False, "Unknown phase"
```

**Что делает:**
- **Для личных карт:** Организует циклическую расшифровку пока все игроки не обработают карты
- **Для карт стола:** Последовательная расшифровка всеми игроками
- Обновляет состояние карт после каждого шага расшифровки
- Управляет переходами между фазами игры
- **Цель:** Координация процесса расшифровки для разных типов карт

---

### **17. `deal_table_cards(self, count)` - Выкладывание карт на стол**

```python
def deal_table_cards(self, count):
    phase_name = {3: "FLOP", 1: "TURN" if len(self.table_cards) == 3 else "RIVER"}.get(count, "TABLE")
    new_cards = [self.deck.pop() for _ in range(count) if self.deck]
    self._write_to_log(f"--- 5. DEALING {phase_name} ({count} cards) ---")
    enc_vals = [c['encrypted_value'] for c in new_cards]
    card_ids_for_log = [c['id'] for c in new_cards]
    self._write_to_log(f"  Moving cards to table (IDs {card_ids_for_log}). Encrypted values: {enc_vals}")
    self.table_cards.extend(new_cards)
    self.start_table_cards_decryption(new_cards)
```

**Что делает:**
- Определяет название фазы (FLOP-3 карты, TURN-1 карта, RIVER-1 карта)
- Берет карты с вершины колоды
- Логирует выложенные карты
- Добавляет карты на стол
- Запускает процесс их расшифровки
- **Цель:** Выкладывание общих карт на стол

---

### **18. `start_table_cards_decryption(self, cards_to_decrypt)` - Начало расшифровки карт стола**

```python
def start_table_cards_decryption(self, cards_to_decrypt):
    self.processing_phase = 'decryption_table'
    self.current_player_index = 0
    self.cards_to_process = cards_to_decrypt
    if self.cards_to_process and self.player_order:
        first_player_id = self.player_order[0]
        self.players[first_player_id]['active'] = True
        self.socketio.emit('decrypt_cards', {
            'cards': self.cards_to_process, 
            'phase': 'table'
        }, room=self.players[first_player_id]['socket_id'])
        self.add_log("Расшифровка карт на столе...")
```

**Что делает:**
- Устанавливает фазу расшифровки карт стола
- Сбрасывает индекс текущего игрока
- Активирует первого игрока для расшифровки
- Отправляет карты на расшифровку
- **Цель:** Запуск процесса расшифровки общих карт

---

### **19. `complete_game(self)` - Завершение игры**

```python
def complete_game(self):
    self.phase = "completed"
    self._write_to_log("--- GAME COMPLETED: REVEALING ALL CARDS FOR LOG ---")
    table_log = ", ".join([self.card_identity_map.get(c['id'], '??') for c in self.table_cards])
    self._write_to_log(f"  Final Table: [{table_log}]")
    for pid in self.player_order:
        p_name = self.players[pid]['name']
        p_cards = ", ".join([self.card_identity_map.get(c['id'], '??') for c in self.players[pid]['cards']])
        self._write_to_log(f"  Player '{p_name}' had: [{p_cards}]")
    self.add_log("Игра завершена! Все карты открыты в логе.")
    self.socketio.emit('game_completed', {}, room=self.room_id)
    self.request_keys_from_players()
```

**Что делает:**
- Устанавливает фазу завершения
- Логирует ВСЕ карты (стол и руки игроков) для отладки
- Рассылает уведомление о завершении
- Запрашивает ключи у игроков для аудита
- **Цель:** Завершение игры и сбор данных для проверки

---

### **20. `request_keys_from_players(self)` - Запрос ключей**

```python
def request_keys_from_players(self):
    self.keys_collection_phase = True
    self.add_log("Запрос ключей у игроков для аудита...")
    self._write_to_log("--- 6. REQUESTING PLAYER KEYS FOR AUDIT ---")
    self.socketio.emit('request_keys', {}, room=self.room_id)
```

**Что делает:**
- Включает фазу сбора ключей
- Рассылает запрос ключей всем игрокам
- **Цель:** Собрать криптографические ключи для проверки честности

---

### **21. `handle_player_keys(self, player_id, key_c, key_d)` - Обработка ключей игроков**

```python
def handle_player_keys(self, player_id, key_c, key_d):
    if not self.keys_collection_phase or player_id in self.received_keys: 
        return False, "Cannot receive keys now"
    try:
        p_name = self.players[player_id]['name']
        self.received_keys[player_id] = {
            'C': int(key_c), 
            'D': int(key_d), 
            'player_name': p_name
        }
        self.add_log("получил ключи", player_id=player_id)
        self._write_to_log(f"  Received keys from '{p_name}': C={key_c}, D={key_d}")
        if len(self.received_keys) == len(self.players): 
            self._write_keys_to_log()
        return True, "Keys received"
    except (ValueError, TypeError): 
        return False, "Invalid key format"
```

**Что делает:**
- Проверяет что фаза сбора ключей активна
- Конвертирует ключи в числа
- Сохраняет ключи в `received_keys`
- Логирует получение
- Когда все ключи получены - записывает их в лог
- **Цель:** Сбор и валидация криптографических ключей

---

### **22. `_write_keys_to_log(self)` - Запись ключей в лог**

```python
def _write_keys_to_log(self):
    log_section = "\n--- PLAYER KEYS FOR AUDIT ---"
    for pid, data in self.received_keys.items():
        verification = "1" if self.p and (data['C'] * data['D']) % (self.p - 1) == 1 else "FAILED"
        log_section += f"\n  Player: {data['player_name']}\n    C = {data['C']}\n    D = {data['D']}\n    Verification (C*D mod P-1 == 1): {verification}"
    self._write_to_log(log_section)
    self._write_final_summary()
```

**Что делает:**
- Форматирует все полученные ключи
- **Проверяет валидность ключей:** `(C * D) mod (P-1) == 1`
- Записывает результат проверки
- Вызывает запись финального резюме
- **Цель:** Аудит криптографической корректности игры

---

### **23. `_write_final_summary(self)` - Финальное резюме**

```python
def _write_final_summary(self):
    duration = (datetime.now() - self.game_start_time).total_seconds()
    summary = f"""\n--- FINAL SUMMARY ---
End Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Duration: {duration:.1f} seconds
Prime P: {self.p}
--- END OF LOG ---
"""
    self._write_to_log(summary)
```

**Что делает:**
- Вычисляет длительность игры
- Форматирует итоговую информацию
- Записывает завершающую секцию лога
- **Цель:** Подведение итогов игры

---

### **24. `next_game_phase(self, player_id)` - Переход к следующей фазе**

```python
def next_game_phase(self, player_id):
    is_game_leader = self.player_order and player_id == self.player_order[0]
    if self.phase == "waiting" and self.can_start_game(): 
        self.start_game()
    elif self.phase == "key_exchange": 
        self.start_encryption_phase()
    elif is_game_leader:
        if self.phase == "flop": self.deal_table_cards(3)
        elif self.phase == "turn": self.deal_table_cards(1)
        elif self.phase == "river": self.deal_table_cards(1)
        elif self.phase == "showdown": self.complete_game()
```

**Что делает:**
- Определяет является ли игрок лидером (первым в порядке)
- Обрабатывает переходы между фазами по командам игроков
- Только лидер может управлять прогрессом игры после начала
- **Цель:** Управление прогрессом игры через пользовательский интерфейс

---

### **25. `get_game_state(self, for_player_id=None)` - Получение состояния игры** и  
## **26.`emit_game_state(self)` - Рассылка состояния игры**


### Как работает `get_game_state()` (детальный разбор кода)

Вот эта функция:
```python
# mental_poker_game.py
def get_game_state(self, for_player_id=None):
    # 1. Создает базовый "скелет" ответа с публичной информацией
    state = {'phase': self.phase, 'table_cards': [], 'deck_size': len(self.deck), 
             'player_order': self.player_order, 'processing_phase': self.processing_phase, 
             'players': {}, 'your_player_id': for_player_id}
    
    # 2. Безопасно обрабатывает карты стола, удаляя секретный 'id'
    for card in self.table_cards:
        safe_card = {k: v for k, v in card.items() if k != 'id'}
        state['table_cards'].append(safe_card)

    # 3. Самая важная часть: готовит данные о каждом игроке ИНДИВИДУАЛЬНО
    for pid, p_data in self.players.items():
        player_state = {'player_id': p_data['player_id'], 'name': p_data['name'], 
                        'active': p_data['active'], 'cards': []}
        
        # 3a. ЕСЛИ это игрок, для которого мы готовим ответ...
        if pid == for_player_id:
            # ...мы берем его карты, но тоже удаляем секретный 'id' из каждой!
            for card in p_data['cards']:
                safe_card = {k: v for k, v in card.items() if k != 'id'}
                player_state['cards'].append(safe_card)
        # 3b. ЕСЛИ это любой другой игрок...
        else:
            # ...мы не показываем его карты. Мы просто создаем "заглушки",
            # чтобы клиент знал, что у игрока есть 2 карты, но не знал какие.
            player_state['cards'] = [{'encrypted': True}] * len(p_data['cards'])
            
        state['players'][pid] = player_state
        
    return state
```
**Что она делает по пунктам:**
1.  Собирает общую информацию, которая не является секретной (фаза, размер колоды и т.д.).
2.  **Защита №1:** Удаляет `id` из карт на столе перед отправкой.
3.  **Защита №2 (ключевая):**
    *   **Для вас:** Она отдает вам ваши карты, но без `id`. Вы получаете `encrypted_value`, которое можете расшифровать, но не получаете внутренний идентификатор сервера.
    *   **Для всех остальных:** Она полностью скрывает их карты, заменяя их на простые объекты-заглушки. Вы знаете, что у вашего оппонента 2 карты, но не имеете никакой информации о них.

### Кто же ее вызывает? Функция `emit_game_state()`

Эта функция является "рассыльщиком". Ее задача — отправить обновленное состояние игры всем участникам. И она делает это очень хитро: она не отправляет всем одно и то же, а готовит для каждого персональное сообщение с помощью `get_game_state()`.

```python
# mental_poker_game.py
def emit_game_state(self):
    # Проходим по каждому игроку в игре
    for player in self.players.values():
        if player['socket_id']:
            # 1. Вызываем get_game_state, передавая ID ТЕКУЩЕГО игрока в цикле
            state = self.get_game_state(player['player_id'])
            
            # 2. Отправляем сгенерированное, персональное состояние
            #    только этому игроку (в его личную "комнату")
            self.socketio.emit('game_state', state, room=player['socket_id'])
```
**Аналогия:**
Представьте, что `emit_game_state` — это официант на банкете. Он не раздает всем одинаковые тарелки. Он подходит к каждому гостю (`for player in...`), спрашивает у повара (`get_game_state(player_id)`), какое блюдо приготовить для этого конкретного гостя (с его аллергиями и предпочтениями), и приносит ему персональный заказ.

### Когда все это происходит?

Функция `emit_game_state()` (и, следовательно, `get_game_state()`) вызывается в конце **любого действия, которое меняет состояние игры**. Например, в `app.py`:

*   `handle_connect()`: игрок присоединился, всем нужно обновить список игроков.
*   `handle_disconnect()`: игрок ушел, всем нужно обновить список.
*   `handle_next_phase()`: игра перешла в новую фазу.
*   `handle_encrypted_cards()`: игрок закончил шифровать, нужно показать, что он больше не "активен".
*   `handle_decrypted_cards()`: игрок закончил расшифровывать, то же самое.

---