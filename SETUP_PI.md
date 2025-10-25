# 🚀 Schnellstart für Raspberry Pis

## Schritt 1: Repository auf beide Pis klonen

**Auf Pi 1 und Pi 2:**

```bash
cd ~
git clone <DEINE-GITHUB-URL> blockchain-donation
cd blockchain-donation
```

## Schritt 2: Dependencies installieren

```bash
pip3 install -r requirements.txt --break-system-packages
```

## Schritt 3: IP-Adressen herausfinden

**Auf Pi 1:**

```bash
hostname -I
```

Notiere die IP (z.B. `192.168.1.100`)

**Auf Pi 2:**

```bash
hostname -I
```

Notiere die IP (z.B. `192.168.1.101`)

## Schritt 4: Nodes starten

**Auf Pi 1:**

```bash
python3 node.py 5000
```

**Auf Pi 2:**

```bash
python3 node.py 5000
```

## Schritt 5: Nodes verbinden

**Von deinem Computer (oder einem der Pis):**

Ersetze die IP-Adressen mit deinen echten IPs!

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

## Schritt 6: Testen

**Prüfe, ob beide Nodes laufen:**

```bash
curl http://192.168.1.100:5000/health
curl http://192.168.1.101:5000/health
```

**Prüfe, ob Nodes verbunden sind:**

```bash
curl http://192.168.1.100:5000/nodes/list
```

**Erstelle eine Test-Transaktion:**

```bash
curl -X POST http://192.168.1.100:5000/transactions/new \
  -H "Content-Type: application/json" \
  -d '{
    "sender": "Test User",
    "recipient": "Rotes Kreuz",
    "amount": 100
  }'
```

**Prüfe die Blockchain:**

```bash
curl http://192.168.1.100:5000/chain
```

## ✅ Erfolgreich, wenn:

- ✅ Beide Nodes laufen (Health Check gibt 200 zurück)
- ✅ Beide Nodes kennen sich (`/nodes/list` zeigt 1 Peer)
- ✅ Transaktionen werden synchronisiert
- ✅ Blocks werden auf beiden Nodes gemined

## 🐛 Probleme?

**Node startet nicht:**

```bash
# Prüfe Python-Version (muss 3.7+ sein)
python3 --version

# Prüfe, ob Port frei ist
sudo netstat -tlnp | grep 5000
```

**Nodes verbinden nicht:**

```bash
# Prüfe Firewall
sudo ufw status
sudo ufw allow 5000

# Prüfe, ob IPs erreichbar sind
ping 192.168.1.101
```

**Frontend verbindet nicht:**

- Prüfe CORS in `node.py` (sollte aktiviert sein)
- Aktualisiere IPs in `frontend/script.js`

## 📱 Frontend später hinzufügen

Wenn das Frontend fertig ist:

1. Kopiere den `frontend/` Ordner auf einen der Pis
2. Öffne `frontend/script.js` und passe die IP-Adressen an
3. Öffne `frontend/index.html` im Browser

Oder verwende einen einfachen Web-Server:

```bash
cd frontend
python3 -m http.server 8080
```

Dann im Browser: `http://192.168.1.100:8080`

## 🎓 Für die Präsentation

**Zeige diese Dinge:**

1. Zwei Pis laufen parallel
2. Transaktion über Frontend eingeben
3. Zeige, dass beide Pis die Transaktion haben
4. Warte auf Mining (oder starte manuell)
5. Zeige, dass beide Pis den Block haben
6. Zeige Statistiken

**Coole Demo-Ideen:**

- Einen Pi ausschalten → der andere läuft weiter
- Pi wieder einschalten → synchronisiert automatisch
- Gleichzeitig Transaktionen an beide Pis senden
