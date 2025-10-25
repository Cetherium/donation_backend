from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from blockchain import Blockchain
import threading
import time
from typing import Set


# Flask App initialisieren
app = Flask(__name__)
CORS(app)  # Erlaubt Frontend-Zugriff von anderen Domains

# Blockchain-Instanz erstellen
blockchain = Blockchain(difficulty=4)

# Set für bekannte Nodes (andere Raspberry Pis)
peer_nodes: Set[str] = set()

# Organisationen (fest vorgegeben)
ORGANIZATIONS = [
    "Rotes Kreuz",
    "WWF",
    "Ärzte ohne Grenzen",
    "UNICEF",
    "Greenpeace"
]


# ==================== REST API ENDPOINTS ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Prüft, ob der Node läuft."""
    return jsonify({
        "status": "running",
        "blocks": len(blockchain.chain),
        "pending_transactions": len(blockchain.mempool)
    }), 200


@app.route('/chain', methods=['GET'])
def get_chain():
    """Gibt die komplette Blockchain zurück."""
    return jsonify({
        "chain": blockchain.get_chain_data(),
        "length": len(blockchain.chain)
    }), 200


@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    """
    Erstellt eine neue Transaktion (Spende).
    
    Erwartet JSON:
    {
        "sender": "Alice",
        "recipient": "Rotes Kreuz",
        "amount": 50
    }
    """
    data = request.get_json()
    
    # Validierung
    required = ['sender', 'recipient', 'amount']
    if not all(key in data for key in required):
        return jsonify({"error": "Fehlende Felder"}), 400
    
    # Prüfen, ob die Organisation gültig ist
    if data['recipient'] not in ORGANIZATIONS:
        return jsonify({"error": "Ungültige Organisation"}), 400
    
    # Transaktion zur Blockchain hinzufügen
    blockchain.add_transaction(
        sender=data['sender'],
        recipient=data['recipient'],
        amount=data['amount']
    )
    
    # Transaktion an alle Peers broadcasten
    broadcast_transaction(data)
    
    return jsonify({
        "message": "Transaktion erfolgreich hinzugefügt",
        "mempool_size": len(blockchain.mempool)
    }), 201


@app.route('/mine', methods=['POST'])
def mine_block():
    """
    Mined manuell einen neuen Block mit allen ausstehenden Transaktionen.
    """
    if not blockchain.mempool:
        return jsonify({"error": "Keine Transaktionen zum Minen"}), 400
    
    # Block minen
    success = blockchain.mine_pending_transactions()
    
    if success:
        # Neuen Block an alle Peers broadcasten
        broadcast_new_block()
        
        return jsonify({
            "message": "Block erfolgreich gemined",
            "block": blockchain.get_latest_block().to_dict()
        }), 200
    else:
        return jsonify({"error": "Mining fehlgeschlagen"}), 500


@app.route('/organizations', methods=['GET'])
def get_organizations():
    """Gibt die Liste der verfügbaren Organisationen zurück."""
    return jsonify({"organizations": ORGANIZATIONS}), 200


@app.route('/stats', methods=['GET'])
def get_stats():
    """Gibt Statistiken über die Blockchain zurück."""
    total_donations = 0
    donations_per_org = {org: 0 for org in ORGANIZATIONS}
    
    # Alle Transaktionen durchgehen (außer Genesis)
    for block in blockchain.chain[1:]:  # Genesis Block überspringen
        for tx in block.transactions:
            if tx['recipient'] in ORGANIZATIONS:
                total_donations += tx['amount']
                donations_per_org[tx['recipient']] += tx['amount']
    
    return jsonify({
        "total_donations": total_donations,
        "donations_per_organization": donations_per_org,
        "total_blocks": len(blockchain.chain),
        "pending_transactions": len(blockchain.mempool),
        "chain_valid": blockchain.is_chain_valid()
    }), 200


# ==================== P2P ENDPOINTS ====================

@app.route('/nodes/register', methods=['POST'])
def register_node():
    """
    Registriert einen neuen Peer-Node.
    
    Erwartet JSON:
    {
        "node_address": "http://192.168.1.100:5000"
    }
    """
    data = request.get_json()
    node_address = data.get('node_address')
    
    if not node_address:
        return jsonify({"error": "Keine Node-Adresse angegeben"}), 400
    
    # Node zur Peer-Liste hinzufügen
    peer_nodes.add(node_address)
    
    print(f"🔗 Neuer Peer registriert: {node_address}")
    
    return jsonify({
        "message": "Node erfolgreich registriert",
        "total_peers": len(peer_nodes)
    }), 201


@app.route('/nodes/list', methods=['GET'])
def list_nodes():
    """Gibt alle bekannten Peer-Nodes zurück."""
    return jsonify({
        "peers": list(peer_nodes),
        "count": len(peer_nodes)
    }), 200


@app.route('/consensus', methods=['POST'])
def consensus():
    """
    Konsens-Algorithmus: Ersetzt die Chain durch die längste gültige Chain.
    """
    replaced = False
    
    for peer in peer_nodes:
        try:
            # Chain vom Peer holen
            response = requests.get(f"{peer}/chain", timeout=5)
            
            if response.status_code == 200:
                peer_chain = response.json()['chain']
                
                # Versuchen, unsere Chain zu ersetzen
                if blockchain.replace_chain(peer_chain):
                    replaced = True
                    print(f"🔄 Chain von {peer} übernommen!")
        
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Peer {peer} nicht erreichbar: {e}")
            continue
    
    if replaced:
        return jsonify({
            "message": "Chain wurde ersetzt",
            "new_length": len(blockchain.chain)
        }), 200
    else:
        return jsonify({
            "message": "Unsere Chain ist die längste",
            "length": len(blockchain.chain)
        }), 200


@app.route('/transactions/receive', methods=['POST'])
def receive_transaction():
    """
    Empfängt eine Transaktion von einem Peer-Node.
    Wird aufgerufen, wenn ein anderer Pi eine Transaktion broadcasted.
    """
    data = request.get_json()
    
    # Transaktion hinzufügen (ohne erneutes Broadcasting)
    blockchain.add_transaction(
        sender=data['sender'],
        recipient=data['recipient'],
        amount=data['amount']
    )
    
    print(f"📩 Transaktion von Peer empfangen: {data['sender']} → {data['recipient']}")
    
    return jsonify({"message": "Transaktion empfangen"}), 200


@app.route('/blocks/receive', methods=['POST'])
def receive_block():
    """
    Empfängt einen neuen Block von einem Peer-Node.
    Triggert automatisch Konsens, um die Chain zu synchronisieren.
    """
    print("📦 Neuer Block von Peer empfangen - starte Konsens...")
    
    # Konsens-Algorithmus ausführen
    consensus()
    
    return jsonify({"message": "Block empfangen, Konsens durchgeführt"}), 200


# ==================== HELPER FUNCTIONS ====================

def broadcast_transaction(transaction_data: dict):
    """
    Sendet eine neue Transaktion an alle Peer-Nodes.
    """
    for peer in peer_nodes:
        try:
            requests.post(
                f"{peer}/transactions/receive",
                json=transaction_data,
                timeout=2
            )
            print(f"📤 Transaktion an {peer} gesendet")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Konnte Transaktion nicht an {peer} senden: {e}")


def broadcast_new_block():
    """
    Informiert alle Peer-Nodes über einen neuen Block.
    """
    for peer in peer_nodes:
        try:
            requests.post(
                f"{peer}/blocks/receive",
                json={},
                timeout=2
            )
            print(f"📤 Block-Benachrichtigung an {peer} gesendet")
        except requests.exceptions.RequestException as e:
            print(f"⚠️  Konnte Block-Benachrichtigung nicht an {peer} senden: {e}")


def auto_mine_thread():
    """
    Hintergrund-Thread, der regelmäßig prüft, ob gemined werden soll.
    Mined automatisch, wenn Transaktionen älter als 2 Minuten sind.
    """
    while True:
        time.sleep(30)  # Alle 30 Sekunden prüfen
        
        if blockchain.mempool:
            # Prüfen, ob die älteste Transaktion älter als 2 Minuten ist
            oldest_tx = blockchain.mempool[0]
            age = time.time() - oldest_tx['timestamp']
            
            if age > 120:  # 2 Minuten
                print("⏰ Auto-Mining: Transaktionen sind älter als 2 Minuten")
                blockchain.mine_pending_transactions()
                broadcast_new_block()


def sync_with_peers_thread():
    """
    Hintergrund-Thread, der regelmäßig mit Peers synchronisiert.
    """
    while True:
        time.sleep(60)  # Jede Minute
        
        if peer_nodes:
            print("🔄 Starte automatische Synchronisierung mit Peers...")
            consensus()


# ==================== STARTUP ====================

if __name__ == '__main__':
    import sys
    
    # Port aus Kommandozeilen-Argument lesen (Standard: 5000)
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    
    print(f"""
    ╔══════════════════════════════════════════════╗
    ║  🚀 Blockchain Node gestartet               ║
    ║                                              ║
    ║  Port: {port}                                ║
    ║  Schwierigkeit: {blockchain.difficulty}                           ║
    ║                                              ║
    ║  API Endpoints:                              ║
    ║  • GET  /health                              ║
    ║  • GET  /chain                               ║
    ║  • POST /transactions/new                    ║
    ║  • POST /mine                                ║
    ║  • GET  /organizations                       ║
    ║  • GET  /stats                               ║
    ║  • POST /nodes/register                      ║
    ║  • POST /consensus                           ║
    ╚══════════════════════════════════════════════╝
    """)
    
    # Auto-Mining Thread starten
    mining_thread = threading.Thread(target=auto_mine_thread, daemon=True)
    mining_thread.start()
    
    # Sync Thread starten
    sync_thread = threading.Thread(target=sync_with_peers_thread, daemon=True)
    sync_thread.start()
    
    # Flask App starten
    app.run(host='0.0.0.0', port=port, debug=False)