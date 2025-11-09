import random
import sympy
from datetime import datetime
import os

class MentalPokerGame:
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

    def _write_to_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)

    def add_log(self, message, player_id=None):
        timestamp = datetime.now().strftime("%H:%M:%S")
        player_name = self.players[player_id]['name'] if player_id else "Система"
        log_entry = f"{timestamp} - {player_name}: {message}"
        self.game_log.append(log_entry)
        self.socketio.emit('log_update', {'log': log_entry}, room=self.room_id)

    def add_player(self, player_id, name, socket_id):
        if len(self.players) >= 5:
            return False, "Комната заполнена"
        self.players[player_id] = {'player_id': player_id, 'name': name, 'socket_id': socket_id, 'cards': [], 'active': False}
        self.player_order.append(player_id)
        self._write_to_log(f"[JOIN] Player '{name}' (ID: {player_id}) connected.")
        return True, f"Игрок {name} присоединился"

    def remove_player(self, player_id):
        if player_id in self.players:
            player_name = self.players[player_id]['name']
            if player_id in self.player_order: self.player_order.remove(player_id)
            del self.players[player_id]
            self._write_to_log(f"[LEAVE] Player '{player_name}' left.")

    def can_start_game(self):
        return len(self.players) >= 2

    def generate_sophie_germain_prime(self, bits=32):
        while True:
            q = sympy.randprime(2**(bits-1), 2**bits)
            p = 2 * q + 1
            if sympy.isprime(p): return p, q

    def initialize_deck(self):
        suits = ['♠', '♥', '♦', '♣']
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        temp_deck = []
        card_id = 0
        for suit in suits:
            for rank in ranks:
                numeric_value = 100 + card_id
                temp_deck.append({'id': card_id, 'value': rank + suit, 'numeric_value': numeric_value, 'encrypted_value': numeric_value})
                card_id += 1
        
        self._write_to_log("--- 1. INITIAL DECK STATE ---")
        for card in temp_deck:
            self._write_to_log(f"  ID {card['id']:02d}: {card['value']:<3} (Numeric Value: {card['numeric_value']})")
        
        self.card_identity_map = {card['id']: card['value'] for card in temp_deck}
        for card in temp_deck: del card['value']
        self.deck = temp_deck

    def start_game(self):
        if not self.can_start_game(): return False, "Нужно минимум 2 игрока"
        
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

    def start_encryption_phase(self):
        self.phase = "encryption"
        self.processing_phase = "encryption"
        self.current_player_index = 0
        self.cards_to_process = self.deck.copy()
        first_player_id = self.player_order[0]
        self.players[first_player_id]['active'] = True
        self.add_log("Начинается шифрование колоды")
        self._write_to_log("--- 2. DECK ENCRYPTION PHASE ---")
        self.socketio.emit('encrypt_cards', {'cards': self.cards_to_process, 'player_index': self.current_player_index}, room=self.players[first_player_id]['socket_id'])

    def handle_encrypted_cards(self, player_id, encrypted_cards):
        if self.processing_phase != "encryption" or player_id != self.player_order[self.current_player_index]: return False, "Invalid action"
            
        player_name = self.players[player_id]['name']
        
        # 1. Сохраняем перемешанный порядок, полученный от клиента. ЭТО КЛЮЧЕВОЕ ИЗМЕНЕНИЕ.
        self.cards_to_process = encrypted_cards
        
        # 2. Для удобства чтения логов, создаем ВРЕМЕННУЮ отсортированную копию.
        sorted_for_log = sorted(encrypted_cards, key=lambda x: x.get('id', -1))
        
        # 3. Пишем в лог отсортированную версию, но ИСПОЛЬЗУЕМ ДАЛЬШЕ перемешанную.
        self._write_to_log(f"  Deck state after encryption by '{player_name}':")
        for card in sorted_for_log:
            self._write_to_log(f"    ID {card['id']:02d} -> Encrypted Value: {card['encrypted_value']}")
        
        self.players[player_id]['active'] = False
        self.add_log("зашифровал колоду", player_id=player_id)
        
        self.current_player_index += 1
        if self.current_player_index < len(self.player_order):
            next_player_id = self.player_order[self.current_player_index]
            self.players[next_player_id]['active'] = True
            # Передаем следующему игроку ПЕРЕМЕШАННУЮ колоду
            self.socketio.emit('encrypt_cards', {'cards': self.cards_to_process, 'player_index': self.current_player_index}, room=self.players[next_player_id]['socket_id'])
        else:
            self.deck = self.cards_to_process
            self.cards_to_process = []
            self.processing_phase = None
            self._write_to_log("[ENCRYPTION] Final deck is fully encrypted and shuffled.")
            self.start_card_dealing()
        return True, "Encryption processed"

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

    def start_private_cards_decryption(self):
        self.processing_phase = 'decryption_private'
        self.decryption_target_player_index = 0
        self._write_to_log("--- 4. PRIVATE CARDS DECRYPTION ---")
        self._start_decryption_for_current_target()

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
        self.socketio.emit('decrypt_cards', {'cards': self.cards_to_process, 'phase': 'private'}, room=self.players[first_decryptor_id]['socket_id'])

    def handle_decrypted_cards(self, player_id, decrypted_cards, phase):
        if self.processing_phase != f"decryption_{phase}" or player_id != self.player_order[self.current_player_index]: return False, "Invalid action"

        current_player_name = self.players[player_id]['name']
        self.cards_to_process = decrypted_cards
        self.players[player_id]['active'] = False

        if phase == 'private':
            target_player_name = self.players[self.player_order[self.decryption_target_player_index]]['name']
            dec_vals = [c['encrypted_value'] for c in self.cards_to_process]
            card_ids_for_log = [c['id'] for c in self.cards_to_process]
            self._write_to_log(f"    '{current_player_name}' decrypted hand of '{target_player_name}' (IDs {card_ids_for_log}). New values: {dec_vals}")
            
            next_player_index = (self.current_player_index + 1) % len(self.player_order)
            if next_player_index == self.decryption_target_player_index:
                target_player_id = self.player_order[self.decryption_target_player_index]
                self.socketio.emit('final_private_decryption', {'cards': self.cards_to_process}, room=self.players[target_player_id]['socket_id'])
                self.decryption_target_player_index += 1
                self._start_decryption_for_current_target()
            else:
                self.current_player_index = next_player_index
                next_decryptor_id = self.player_order[self.current_player_index]
                self.players[next_decryptor_id]['active'] = True
                self.socketio.emit('decrypt_cards', {'cards': self.cards_to_process, 'phase': 'private'}, room=self.players[next_decryptor_id]['socket_id'])
            return True, "Private cards processed"

        if phase == 'table':
            dec_vals = [c['encrypted_value'] for c in self.cards_to_process]
            card_ids_for_log = [c['id'] for c in self.cards_to_process]
            self._write_to_log(f"    '{current_player_name}' decrypted table cards (IDs {card_ids_for_log}). New values: {dec_vals}")
            
            self.current_player_index += 1
            if self.current_player_index < len(self.player_order):
                next_player_id = self.player_order[self.current_player_index]
                self.players[next_player_id]['active'] = True
                self.socketio.emit('decrypt_cards', {'cards': self.cards_to_process, 'phase': 'table'}, room=self.players[next_player_id]['socket_id'])
            else:
                for card in self.cards_to_process:
                    card['value'] = self.card_identity_map[card['id']]
                decrypted_ids = {c['id'] for c in self.cards_to_process}
                updated_table = [c for c in self.table_cards if c['id'] not in decrypted_ids] + self.cards_to_process
                self.table_cards = sorted(updated_table, key=lambda c: c.get('id', -1))
                if self.phase == "flop": self.phase = "turn"
                elif self.phase == "turn": self.phase = "river"
                elif self.phase == "river": self.phase = "showdown"
                self.processing_phase = None
            return True, "Table cards processed"
        return False, "Unknown phase"

    def deal_table_cards(self, count):
        phase_name = {3: "FLOP", 1: "TURN" if len(self.table_cards) == 3 else "RIVER"}.get(count, "TABLE")
        new_cards = [self.deck.pop() for _ in range(count) if self.deck]
        self._write_to_log(f"--- 5. DEALING {phase_name} ({count} cards) ---")
        enc_vals = [c['encrypted_value'] for c in new_cards]
        card_ids_for_log = [c['id'] for c in new_cards]
        self._write_to_log(f"  Moving cards to table (IDs {card_ids_for_log}). Encrypted values: {enc_vals}")
        self.table_cards.extend(new_cards)
        self.start_table_cards_decryption(new_cards)

    def start_table_cards_decryption(self, cards_to_decrypt):
        self.processing_phase = 'decryption_table'
        self.current_player_index = 0
        self.cards_to_process = cards_to_decrypt
        if self.cards_to_process and self.player_order:
            first_player_id = self.player_order[0]
            self.players[first_player_id]['active'] = True
            self.socketio.emit('decrypt_cards', {'cards': self.cards_to_process, 'phase': 'table'}, room=self.players[first_player_id]['socket_id'])
            self.add_log("Расшифровка карт на столе...")

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

    def request_keys_from_players(self):
        self.keys_collection_phase = True
        self.add_log("Запрос ключей у игроков для аудита...")
        self._write_to_log("--- 6. REQUESTING PLAYER KEYS FOR AUDIT ---")
        self.socketio.emit('request_keys', {}, room=self.room_id)

    def handle_player_keys(self, player_id, key_c, key_d):
        if not self.keys_collection_phase or player_id in self.received_keys: return False, "Cannot receive keys now"
        try:
            p_name = self.players[player_id]['name']
            self.received_keys[player_id] = {'C': int(key_c), 'D': int(key_d), 'player_name': p_name}
            self.add_log("получил ключи", player_id=player_id)
            self._write_to_log(f"  Received keys from '{p_name}': C={key_c}, D={key_d}")
            if len(self.received_keys) == len(self.players): self._write_keys_to_log()
            return True, "Keys received"
        except (ValueError, TypeError): return False, "Invalid key format"

    def _write_keys_to_log(self):
        log_section = "\n--- PLAYER KEYS FOR AUDIT ---"
        for pid, data in self.received_keys.items():
            verification = "1" if self.p and (data['C'] * data['D']) % (self.p - 1) == 1 else "FAILED"
            log_section += f"\n  Player: {data['player_name']}\n    C = {data['C']}\n    D = {data['D']}\n    Verification (C*D mod P-1 == 1): {verification}"
        self._write_to_log(log_section)
        self._write_final_summary()

    def _write_final_summary(self):
        duration = (datetime.now() - self.game_start_time).total_seconds()
        summary = f"""\n--- FINAL SUMMARY ---
End Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Duration: {duration:.1f} seconds
Prime P: {self.p}
--- END OF LOG ---
"""
        self._write_to_log(summary)

    def next_game_phase(self, player_id):
        is_game_leader = self.player_order and player_id == self.player_order[0]
        if self.phase == "waiting" and self.can_start_game(): self.start_game()
        elif self.phase == "key_exchange": self.start_encryption_phase()
        elif is_game_leader:
            if self.phase == "flop": self.deal_table_cards(3)
            elif self.phase == "turn": self.deal_table_cards(1)
            elif self.phase == "river": self.deal_table_cards(1)
            elif self.phase == "showdown": self.complete_game()

    def emit_game_state(self):
        for player in self.players.values():
            if player['socket_id']:
                self.socketio.emit('game_state', self.get_game_state(player['player_id']), room=player['socket_id'])

    def get_game_state(self, for_player_id=None):
        state = {'phase': self.phase, 'table_cards': [], 'deck_size': len(self.deck), 'player_order': self.player_order, 'processing_phase': self.processing_phase, 'players': {}, 'your_player_id': for_player_id}
        
        for card in self.table_cards:
            safe_card = {k: v for k, v in card.items() if k != 'id'}
            state['table_cards'].append(safe_card)

        for pid, p_data in self.players.items():
            player_state = {'player_id': p_data['player_id'], 'name': p_data['name'], 'active': p_data['active'], 'cards': []}
            if pid == for_player_id:
                for card in p_data['cards']:
                    safe_card = {k: v for k, v in card.items() if k != 'id'}
                    player_state['cards'].append(safe_card)
            else:
                player_state['cards'] = [{'encrypted': True}] * len(p_data['cards'])
            state['players'][pid] = player_state
        return state