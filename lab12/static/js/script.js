let playerId = null;
let playerName = null;
let socket = null;
let playerC = null;
let playerD = null;
let currentP = null;
let playerCardMap = {}; // {100: '2♠', ...}
let revealedHand = []; // [{face: 'A♠', num: 115}, {face: 'K♥', num: 130}]
let lastGameState = null;

const elements = {
    phaseInfo: document.getElementById('phaseInfo'),
    phaseName: document.getElementById('phaseName'),
    deckCount: document.getElementById('deckCount'),
    communityCards: document.getElementById('communityCards'),
    playerHand: document.getElementById('playerHand'),
    logContainer: document.getElementById('logContainer'),
    nextPhaseBtn: document.getElementById('nextPhaseBtn'),
    playerTop: document.getElementById('playerTop'),
    playerRight: document.getElementById('playerRight'),
    playerBottom: document.getElementById('playerBottom'),
    playerLeft: document.getElementById('playerLeft')
};

const suitSymbols = { '♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs' };

function generateCardIdentityMap() {
    const suits = ['♠', '♥', '♦', '♣'];
    const ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A'];
    let card_id = 0;
    const newMap = {};
    for (const suit of suits) {
        for (const rank of ranks) {
            newMap[100 + card_id] = rank + suit;
            card_id++;
        }
    }
    return newMap;
}

function init() {
    playerCardMap = generateCardIdentityMap();
    addLog('Локальный словарь карт сгенерирован.');
    connectSocket();
    setupEventListeners();
}

function connectSocket() {
    socket = io();
    socket.on('connect', () => addLog('Подключен к серверу'));
    socket.on('join_success', (data) => {
        playerId = data.player_id;
        playerName = data.player_name;
        addLog(data.message);
    });
    socket.on('game_state', (data) => {
        lastGameState = data;
        updateGameState(data);
    });
    socket.on('receive_prime', (data) => {
        currentP = BigInt(data.p);
        generateKeys();
    });
    socket.on('encrypt_cards', (data) => {
        encryptCards(data.cards);
    });
    socket.on('decrypt_cards', (data) => {
        decryptCards(data.cards, data.phase);
    });
    socket.on('player_joined', (data) => addLog(`${data.player_name} присоединился`));
    socket.on('player_left', (data) => addLog(`${data.player_name} покинул игру`));
    socket.on('log_update', (data) => addLog(data.log));

    socket.on('final_private_decryption', (data) => {
        if (!playerD || !currentP) return;
        addLog('🔑 Получены карты для финальной расшифровки. Раскрываю локально...');
        const handInfo = [];
        data.cards.forEach(card => {
            const decryptedValue = modPow(BigInt(card.encrypted_value), playerD, currentP);
            const numericValue = Number(decryptedValue);
            const cardFace = playerCardMap[numericValue];
            if (cardFace) {
                handInfo.push({ face: cardFace, num: numericValue });
                addLog(`Карта расшифрована: ${cardFace}`);
            }
        });
        revealedHand = handInfo;
        addLog('✅ Карты раскрыты локально.');
        if (lastGameState) updateGameState(lastGameState);
    });

    socket.on('game_completed', () => {
        addLog('🎮 Игра завершена! Отправка ключей для аудита...');
        automaticallySubmitKeys();
    });
    socket.on('request_keys', () => {
        addLog('🔑 Сервер запрашивает ключи для лога...');
        automaticallySubmitKeys();
    });

    function automaticallySubmitKeys() {
        if (playerId && playerC && playerD) {
            socket.emit('submit_keys', {
                player_id: playerId,
                key_c: playerC.toString(),
                key_d: playerD.toString()
            });
            addLog('✅ Ключи для аудита отправлены.');
        }
    }
}

function generateKeys() {
    const pMinusOne = currentP - 1n;
    while (true) {
        playerC = BigInt(Math.floor(Math.random() * Number(pMinusOne - 2n)) + 2);
        if (gcd(playerC, pMinusOne) === 1n) break;
    }
    playerD = modInverse(playerC, pMinusOne);
    addLog(`🔐 Ключи сгенерированы. Проверка (должна быть 1): ${(playerC * playerD) % pMinusOne}`);
}

function gcd(a, b) { while (b) { [a, b] = [b, a % b]; } return a; }
function modInverse(a, m) {
    let [old_r, r] = [a, m]; let [old_s, s] = [1n, 0n];
    while (r) {
        const quotient = old_r / r;
        [old_r, r] = [r, old_r - quotient * r];
        [old_s, s] = [s, old_s - quotient * s];
    }
    return old_s < 0n ? old_s + m : old_s;
}
function modPow(base, exp, mod) {
    let res = 1n; base %= mod;
    while (exp > 0n) {
        if (exp % 2n === 1n) res = (res * base) % mod;
        exp >>= 1n; base = (base * base) % mod;
    }
    return res;
}

function encryptCards(cards) {
    if (!playerC || !currentP) return;
    const encryptedCards = cards.map(card => ({
        ...card,
        encrypted_value: Number(modPow(BigInt(card.encrypted_value), playerC, currentP))
    }));
    for (let i = encryptedCards.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [encryptedCards[i], encryptedCards[j]] = [encryptedCards[j], encryptedCards[i]];
    }
    addLog(`🔀 Колода зашифрована и перемешана`);
    socket.emit('encrypted_cards', { player_id: playerId, cards: encryptedCards });
}

function decryptCards(cards, phase) {
    if (!playerD || !currentP) return;
    const decryptedCards = cards.map(card => ({
        ...card,
        encrypted_value: Number(modPow(BigInt(card.encrypted_value), playerD, currentP))
    }));
    socket.emit('decrypted_cards', { player_id: playerId, cards: decryptedCards, phase: phase });
}

function setupEventListeners() {
    elements.nextPhaseBtn.addEventListener('click', () => {
        if (playerId) socket.emit('next_phase', { player_id: playerId });
    });
}

function updateGameState(gameState) {
    updatePhaseInfo(gameState.phase, gameState.processing_phase);
    updatePlayerPositions(gameState.players, gameState.your_player_id);
    updateCommunityCards(gameState.table_cards);
    updateDeck(gameState.deck_size);
    updateControls(gameState);
    updatePlayerHand(gameState.players[gameState.your_player_id]);
}

function updatePhaseInfo(phase, processingPhase) {
    const phaseTexts = {
        'waiting': '⏳ Ожидание игроков...', 'key_exchange': '🔑 Обмен ключами...',
        'encryption': '🔒 Шифрование колоды...', 'dealing': '🃏 Раздача карт...',
        'flop': '🃏 Флоп', 'turn': '🃏 Тёрн', 'river': '🃏 Ривер',
        'showdown': '🎯 Вскрытие карт', 'completed': '✅ Игра завершена'
    };
    let phaseText = phaseTexts[phase] || phase;
    if (processingPhase) phaseText += ' (Идет процесс...)';
    elements.phaseInfo.textContent = phaseText;
    elements.phaseName.textContent = phase.toUpperCase();
}

function updatePlayerPositions(players, yourPlayerId) {
    const playerIds = Object.keys(players);
    const positions = ['bottom', 'left', 'top', 'right'];
    const yourIndex = playerIds.indexOf(yourPlayerId);
    const sortedIds = playerIds.slice(yourIndex).concat(playerIds.slice(0, yourIndex));

    ['top', 'right', 'bottom', 'left'].forEach(pos => {
        elements[`player${pos.charAt(0).toUpperCase() + pos.slice(1)}`].innerHTML = '<div class="seat-empty">-</div>';
    });
    
    sortedIds.forEach((pId, index) => {
        const pos = positions[index];
        if (!pos) return;
        const player = players[pId];
        const element = elements[`player${pos.charAt(0).toUpperCase() + pos.slice(1)}`];
        element.innerHTML = `
            <div class="player-seat-content ${player.active ? 'active' : ''}">
                <div class="player-info"><strong>${player.name}${pId === yourPlayerId ? ' (Вы)' : ''}</strong></div>
                <div class="player-cards">${ pId === yourPlayerId ? '' : '<div class="card encrypted">?</div>'.repeat(player.cards.length)}</div>
            </div>`;
    });
}

function updateCommunityCards(tableCards) {
    let html = (tableCards || []).map(card => createCardHTML(card)).join('');
    html += '<div class="card-placeholder">??</div>'.repeat(5 - (tableCards?.length || 0));
    elements.communityCards.innerHTML = html;
}

function updatePlayerHand(player) {
    if (!player || !player.cards) {
        elements.playerHand.innerHTML = `<div class="card-placeholder">??</div><div class="card-placeholder">??</div>`;
        return;
    }
    elements.playerHand.innerHTML = player.cards.map((card, index) => {
        const revealedCard = revealedHand[index];
        return createCardHTML(card, revealedCard ? revealedCard.face : null);
    }).join('');
}

function createCardHTML(card, revealedFace = null) {
    let cardFace = revealedFace || card.value;
    if (cardFace) {
        const value = cardFace.slice(0, -1);
        const suit = cardFace.slice(-1);
        const suitClass = suitSymbols[suit] || '';
        return `
            <div class="card ${suitClass}">
                <div class="card-value top">${value}</div>
                <div class="card-suit">${suit}</div>
                <div class="card-value bottom">${value}</div>
            </div>`;
    }
    return card ? `<div class="card encrypted">?</div>` : `<div class="card-placeholder">??</div>`;
}

function updateDeck(deckSize) { elements.deckCount.textContent = deckSize; }

function updateControls(gameState) {
    elements.nextPhaseBtn.disabled = !!gameState.processing_phase;
    let buttonText = "Начать / Далее";
    if (gameState.processing_phase) buttonText = "Идет процесс...";
    else if (gameState.phase === 'key_exchange') buttonText = "Начать шифрование";
    else if (gameState.phase === 'flop') buttonText = "Выложить флоп";
    else if (gameState.phase === 'turn') buttonText = "Выложить тёрн";
    else if (gameState.phase === 'river') buttonText = "Выложить ривер";
    else if (gameState.phase === 'showdown') buttonText = "Завершить игру";
    else if (gameState.phase === 'completed') {
        buttonText = "Игра завершена";
        elements.nextPhaseBtn.disabled = true;
    }
    elements.nextPhaseBtn.textContent = buttonText;
}

function addLog(message) {
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.textContent = message;
    elements.logContainer.appendChild(logEntry);
    elements.logContainer.scrollTop = elements.logContainer.scrollHeight;
}

document.addEventListener('DOMContentLoaded', init);