#!/usr/bin/env python3
"""
Test-Script für die Blockchain API
Testet alle wichtigen Endpoints
"""

import requests
import json
import time

# Base URL für den Node
BASE_URL = "http://localhost:5001"

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def test_health():
    """Test: Health Check"""
    print_header("TEST 1: Health Check")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 200

def test_get_chain():
    """Test: Blockchain abrufen"""
    print_header("TEST 2: Blockchain abrufen")
    response = requests.get(f"{BASE_URL}/chain")
    print(f"Status Code: {response.status_code}")
    data = response.json()
    print(f"Anzahl Blöcke: {data['length']}")
    print(f"Genesis Block Hash: {data['chain'][0]['hash'][:40]}...")
    return response.status_code == 200

def test_get_organizations():
    """Test: Organisationen abrufen"""
    print_header("TEST 3: Organisationen abrufen")
    response = requests.get(f"{BASE_URL}/organizations")
    print(f"Status Code: {response.status_code}")
    orgs = response.json()['organizations']
    print(f"Verfügbare Organisationen:")
    for org in orgs:
        print(f"  • {org}")
    return response.status_code == 200

def test_create_transaction():
    """Test: Transaktion erstellen"""
    print_header("TEST 4: Transaktion erstellen")
    
    transaction = {
        "sender": "Alice",
        "recipient": "Rotes Kreuz",
        "amount": 50
    }
    
    print(f"Sende Transaktion: {transaction}")
    response = requests.post(
        f"{BASE_URL}/transactions/new",
        json=transaction
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response.status_code == 201

def test_multiple_transactions():
    """Test: Mehrere Transaktionen (sollte Auto-Mining auslösen)"""
    print_header("TEST 5: Mehrere Transaktionen (Auto-Mining)")
    
    transactions = [
        {"sender": "Bob", "recipient": "WWF", "amount": 30},
        {"sender": "Charlie", "recipient": "Ärzte ohne Grenzen", "amount": 100},
        {"sender": "Diana", "recipient": "UNICEF", "amount": 75},
        {"sender": "Eve", "recipient": "Greenpeace", "amount": 25},
    ]
    
    for tx in transactions:
        print(f"  → Sende: {tx['sender']} → {tx['recipient']}: {tx['amount']}€")
        response = requests.post(f"{BASE_URL}/transactions/new", json=tx)
        if response.status_code != 201:
            print(f"  ❌ Fehler: {response.status_code}")
            return False
        time.sleep(0.5)  # Kurz warten
    
    print("\n⏳ Warte 3 Sekunden auf Auto-Mining...")
    time.sleep(3)
    
    # Chain prüfen
    response = requests.get(f"{BASE_URL}/chain")
    length = response.json()['length']
    print(f"✅ Blockchain-Länge: {length} Blöcke")
    
    return length >= 2  # Genesis + mindestens 1 gemineter Block

def test_stats():
    """Test: Statistiken abrufen"""
    print_header("TEST 6: Statistiken")
    response = requests.get(f"{BASE_URL}/stats")
    print(f"Status Code: {response.status_code}")
    stats = response.json()
    print(f"Total Donations: {stats['total_donations']}€")
    print(f"Total Blocks: {stats['total_blocks']}")
    print(f"Pending Transactions: {stats['pending_transactions']}")
    print(f"Chain Valid: {stats['chain_valid']}")
    print(f"\nDonations per Organization:")
    for org, amount in stats['donations_per_organization'].items():
        print(f"  • {org}: {amount}€")
    return response.status_code == 200

def test_manual_mine():
    """Test: Manuelles Mining"""
    print_header("TEST 7: Manuelles Mining")
    
    # Erst eine Transaktion hinzufügen
    tx = {"sender": "Frank", "recipient": "Rotes Kreuz", "amount": 60}
    requests.post(f"{BASE_URL}/transactions/new", json=tx)
    
    print("⛏️  Starte manuelles Mining...")
    response = requests.post(f"{BASE_URL}/mine")
    print(f"Status Code: {response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Block gemined!")
        print(f"Block Index: {data['block']['index']}")
        print(f"Block Hash: {data['block']['hash'][:40]}...")
        return True
    else:
        print(f"Response: {response.json()}")
        return False

def run_all_tests():
    """Führt alle Tests aus"""
    print("\n" + "🚀"*30)
    print("  BLOCKCHAIN API TESTS")
    print("🚀"*30)
    
    tests = [
        ("Health Check", test_health),
        ("Get Chain", test_get_chain),
        ("Get Organizations", test_get_organizations),
        ("Create Transaction", test_create_transaction),
        ("Multiple Transactions", test_multiple_transactions),
        ("Statistics", test_stats),
        ("Manual Mining", test_manual_mine),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ Fehler bei {test_name}: {e}")
            results.append((test_name, False))
    
    # Zusammenfassung
    print_header("ZUSAMMENFASSUNG")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
    
    print(f"\nErgebnis: {passed}/{total} Tests bestanden")
    print("="*60 + "\n")

if __name__ == "__main__":
    print("⏳ Warte 2 Sekunden, damit der Node vollständig startet...")
    time.sleep(2)
    
    try:
        run_all_tests()
    except requests.exceptions.ConnectionError:
        print("\n❌ Fehler: Konnte keine Verbindung zum Node herstellen!")
        print("Stelle sicher, dass der Node läuft: python3 node.py 5000")