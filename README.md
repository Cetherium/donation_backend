# Blockchain-Spendenplattform

Eine dezentrale Spendenplattform basierend auf Blockchain-Technologie, implementiert mit Python und Flask für das W-Seminar.

## 📋 Projekt-Übersicht

Dieses Projekt simuliert eine dezentrale Blockchain-basierte Spendenplattform mit zwei Raspberry Pi Nodes. Nutzer können über ein Web-Frontend virtuelle Spenden an verschiedene Organisationen tätigen.

### Features

- ✅ **Blockchain-Implementierung** mit Proof-of-Work
- ✅ **Dezentrale Architektur** mit P2P-Kommunikation zwischen Nodes
- ✅ **REST API** für Frontend-Anbindung
- ✅ **Automatisches Mining** bei 5 Transaktionen oder nach 2 Minuten
- ✅ **Konsens-Mechanismus** (Longest Chain Rule)
- ✅ **5 vordefinierte Hilfsorganisationen**

## 🛠️ Technologie-Stack

- **Backend**: Python 3.x, Flask
- **Blockchain**: SHA-256 Hashing, Proof-of-Work
- **Frontend**: HTML, CSS, Vanilla JavaScript (coming soon)
- **Hardware**: 2x Raspberry Pi (Pi 4 & Pi 5)

## 📁 Projektstruktur

```
blockchain-donation/
├── blockchain.py          # Blockchain-Kern (Block, Chain, Mining)
├── node.py               # Flask API + P2P Kommunikation
├── requirements.txt      # Python Dependencies
├── test_api.py          # API Tests
├── test_p2p.py          # P2P Tests
├── frontend/            # Web-Frontend (coming soon)
│   ├── index.html
│   ├── style.css
│   └── script.js
└── README.md            # Diese Datei
```

## 🚀 Installation & Setup

### Voraussetzungen

- Python 3.7 oder höher
- pip (Python Package Manager)
- Git

### 1. Repository klonen

```bash
git clone <dein-repository-url>
cd blockchain-donation
```

### 2. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 3. Node starten

**Einzelner Node (zum Testen):**

```bash
python3 node.py 5000
```

**Zwei Nodes (P2P-Simulation):**

Terminal 1:

```bash
python3 node.py 5000
```

Terminal 2:

```bash
python3 node.py 5001
```

### 4. Nodes verbinden

Nodes müssen sich gegenseitig registrieren:

```bash
# Node 1 registriert Node 2
curl -X POST http://localhost:5000/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"node_address": "http://localhost:5001"}'

# Node 2 registriert Node 1
curl -X POST http://localhost:5001/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"node_address": "http://localhost:5000"}'
```

## 🧪 Tests ausführen

### API Tests

```bash
# Node muss laufen auf Port 5000
python3 test_api.py
```

### P2P Tests

```bash
# Beide Nodes müssen laufen (5000 und 5001)
python3 test_p2p.py
```

## 📡 API Endpoints

### Öffentliche Endpoints (für Frontend)

| Endpoint            | Methode | Beschreibung                      |
| ------------------- | ------- | --------------------------------- |
| `/health`           | GET     | Status des Nodes                  |
| `/chain`            | GET     | Komplette Blockchain abrufen      |
| `/transactions/new` | POST    | Neue Spende erstellen             |
| `/mine`             | POST    | Manuell einen Block minen         |
| `/organizations`    | GET     | Liste der Organisationen          |
| `/stats`            | GET     | Statistiken (Spendensummen, etc.) |

### P2P Endpoints (für Node-Kommunikation)

| Endpoint                | Methode | Beschreibung                     |
| ----------------------- | ------- | -------------------------------- |
| `/nodes/register`       | POST    | Anderen Node registrieren        |
| `/nodes/list`           | GET     | Alle bekannten Peers auflisten   |
| `/consensus`            | POST    | Chain synchronisieren            |
| `/transactions/receive` | POST    | Transaktion von Peer empfangen   |
| `/blocks/receive`       | POST    | Block-Benachrichtigung empfangen |

## 💡 Beispiel-Verwendung

### Transaktion erstellen

```bash
curl -X POST http://localhost:5000/transactions/new \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Alice",
    "recipient": "Rotes Kreuz",
    "amount": 50
  }'
```

### Blockchain abrufen

```bash
curl http://localhost:5000/chain
```

### Statistiken abrufen

```bash
curl http://localhost:5000/stats
```

## 🎯 Deployment auf Raspberry Pis

### 1. Code auf beide Pis kopieren

**Option A: Git Clone (empfohlen)**

```bash
git clone <dein-repository-url>
cd blockchain-donation
pip install -r requirements.txt
```

**Option B: SCP (direkter Transfer)**

```bash
scp -r blockchain-donation/ pi@192.168.1.100:/home/pi/
```

### 2. IP-Adressen notieren

Finde die IP-Adressen deiner Pis:

```bash
hostname -I
```

Beispiel:

- Pi 1: `192.168.1.100`
- Pi 2: `192.168.1.101`

### 3. Nodes starten

**Auf Pi 1:**

```bash
python3 node.py 5000
```

**Auf Pi 2:**

```bash
python3 node.py 5000
```

### 4. Nodes verbinden

**Von einem Pi oder vom Computer:**

```bash
# Pi 1 registriert Pi 2
curl -X POST http://192.168.1.100:5000/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"node_address": "http://192.168.1.101:5000"}'

# Pi 2 registriert Pi 1
curl -X POST http://192.168.1.101:5000/nodes/register \
  -H "Content-Type: application/json" \
  -d '{"node_address": "http://192.168.1.100:5000"}'
```

### 5. Frontend konfigurieren

Im Frontend (`script.js`) die IP-Adressen anpassen:

```javascript
const NODES = ['http://192.168.1.100:5000', 'http://192.168.1.101:5000'];
```

## 🔧 Konfiguration

### Blockchain-Parameter (in `blockchain.py`)

```python
difficulty = 4              # Mining-Schwierigkeit (Anzahl führender Nullen)
max_transactions_per_block = 5  # Transaktionen pro Block
```

### Auto-Mining Timer (in `node.py`)

```python
# Zeile ~280
if age > 120:  # 120 Sekunden = 2 Minuten
    blockchain.mine_pending_transactions()
```

## 📚 Technische Details

### Blockchain-Struktur

Jeder Block enthält:

- **Index**: Position in der Chain
- **Timestamp**: Erstellungszeitpunkt
- **Transactions**: Liste von Spenden
- **Previous Hash**: Hash des vorherigen Blocks
- **Nonce**: Proof-of-Work Lösung
- **Hash**: SHA-256 Hash des Blocks

### Proof-of-Work

Der Mining-Algorithmus sucht eine Nonce, sodass der Block-Hash mit `difficulty` Nullen beginnt:

```
Difficulty 4: 0000abc123...  ✅
Difficulty 5: 00000xyz456... ✅ (schwieriger)
```

### Konsens-Mechanismus

**Longest Chain Rule**: Bei unterschiedlichen Chains gewinnt die längste gültige Chain.

### P2P-Kommunikation

1. Transaktion wird an einen Node gesendet
2. Node broadcasted Transaktion an alle Peers
3. Bei Mining wird neuer Block an alle Peers gesendet
4. Peers starten Konsens-Algorithmus zur Synchronisierung

## 🐛 Troubleshooting

### "Connection refused" beim Verbinden

- Prüfe, ob der Node läuft: `curl http://localhost:5000/health`
- Prüfe die Firewall: `sudo ufw allow 5000`
- Prüfe die IP-Adresse: `hostname -I`

### Nodes synchronisieren nicht

- Prüfe, ob Nodes registriert sind: `curl http://localhost:5000/nodes/list`
- Manuell Konsens starten: `curl -X POST http://localhost:5000/consensus`

### Mining dauert zu lange

- Schwierigkeit reduzieren (z.B. von 4 auf 3)
- Weniger Transaktionen pro Block

## 📖 Hilfsorganisationen

Das System unterstützt folgende (fiktive) Organisationen:

1. Rotes Kreuz
2. WWF
3. Ärzte ohne Grenzen
4. UNICEF
5. Greenpeace

## 🎓 W-Seminar Kontext

Dieses Projekt wurde im Rahmen eines W-Seminars zum Thema "Modellierung und Implementierung einer dezentralen Spendenplatform" entwickelt.


