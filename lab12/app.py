from flask import Flask, render_template, request
from flask_socketio import SocketIO, emit, join_room
import random
from mental_poker_game import MentalPokerGame

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mental_poker_secret_key'
socketio = SocketIO(app, cors_allowed_origins="*")

# Одна игровая комната
mental_poker_game = None

@app.route('/')
def index():
    return render_template('index.html')

@socketio.on('connect')
def handle_connect():
    global mental_poker_game
    print(f"Client connected: {request.sid}")
    
    if mental_poker_game is None:
        # Передаем экземпляр socketio в игру при создании
        mental_poker_game = MentalPokerGame(socketio)
        print("A new mental poker game has been created.")
    
    player_name = f"Player_{random.randint(100, 999)}"
    player_id = request.sid
    
    success, message = mental_poker_game.add_player(player_id, player_name, request.sid)
    
    if success:
        join_room("main")
        emit('join_success', {'player_id': player_id, 'player_name': player_name, 'message': message})
        emit('player_joined', {'player_name': player_name}, room="main", include_self=False)
        mental_poker_game.emit_game_state()
        print(f"Player {player_name} has joined.")
    else:
        emit('join_error', {'message': message})
        print(f"Join error: {message}")

@socketio.on('disconnect')
def handle_disconnect():
    global mental_poker_game
    if mental_poker_game and request.sid in mental_poker_game.players:
        player_name = mental_poker_game.players[request.sid]['name']
        mental_poker_game.remove_player(request.sid)
        emit('player_left', {'player_name': player_name}, room="main")
        mental_poker_game.emit_game_state()
        print(f"Player {player_name} has disconnected.")

@socketio.on('next_phase')
def handle_next_phase(data):
    if mental_poker_game:
        player_id = data.get('player_id')
        mental_poker_game.next_game_phase(player_id)
        mental_poker_game.emit_game_state()

@socketio.on('encrypted_cards')
def handle_encrypted_cards(data):
    if mental_poker_game:
        player_id = data.get('player_id')
        cards = data.get('cards')
        success, _ = mental_poker_game.handle_encrypted_cards(player_id, cards)
        if success:
            mental_poker_game.emit_game_state()

@socketio.on('decrypted_cards')
def handle_decrypted_cards(data):
    if mental_poker_game:
        player_id = data.get('player_id')
        cards = data.get('cards')
        phase = data.get('phase')
        success, _ = mental_poker_game.handle_decrypted_cards(player_id, cards, phase)
        if success:
            mental_poker_game.emit_game_state()

@socketio.on('submit_keys')
def handle_submit_keys(data):
    if mental_poker_game:
        player_id = data.get('player_id')
        key_c = data.get('key_c')
        key_d = data.get('key_d')
        mental_poker_game.handle_player_keys(player_id, key_c, key_d)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)