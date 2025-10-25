#!/usr/bin/env python3
"""
Test-Script für P2P-Kommunikation zwischen zwei Nodes
Simuliert zwei Raspberry Pis
"""

import requests
import json
import time

NODE1 = "http://localhost:5001"
NODE2 = "http://localhost:5002"

def print_header(text):
    print("\n" + "="*60)
    print(f"  {text}")
    print("="*60)

def wait_for_nodes():
    """Wartet bis beide Nodes bereit sind"""
    print("⏳ Warte auf beide Nodes...")
    for i in range(10):
        try:
            r1 = requests.get(f"{NODE1}/health", timeout=1)
            r2 = requests.get(f"{NODE2}/health", timeout=1)
            if r1.status_code == 200 and r2.status_code == 200:
                print("✅ Beide Nodes sind bereit!")
                return True
        except:
            time.sleep(1)
    print("❌ Nodes sind nicht bereit!")
    return False

def test_p2p_registration():
    """Test: Nodes registrieren sich gegenseitig"""
    print_header("TEST 1: Node-Registrierung")
    
    # Node 1 registriert Node 2
    print(f"Node 1 registriert Node 2...")
    r = requests.post(f"{NODE1}/nodes/register", json={"node_address": NODE2})
    print(f"  Status: {r.status_code}")
    
    # Node 2 registriert Node 1
    print(f"Node 2 registriert Node 1...")
    r = requests.post(f"{NODE2}/nodes/register", json={"node_address": NODE1})
    print(f"  Status: {r.status_code}")
    
    # Peer-Listen prüfen
    peers1 = requests.get(f"{NODE1}/nodes/list").json()
    peers2 = requests.get(f"{NODE2}/nodes/list").json()
    
    print(f"\nNode 1 kennt {peers1['count']} Peer(s): {peers1['peers']}")
    print(f"Node 2 kennt {peers2['count']} Peer(s): {peers2['peers']}")
    
    return peers1['count'] == 1 and peers2['count'] == 1

def test_transaction_broadcast():
    """Test: Transaktion wird zwischen Nodes synchronisiert"""
    print_header("TEST 2: Transaction Broadcasting")
    
    # Transaktion an Node 1 senden
    print("Sende Transaktion an Node 1...")
    tx = {
        "sender": "Alice",
        "recipient": "Rotes Kreuz",
        "amount": 100
    }
    requests.post(f"{NODE1}/transactions/new", json=tx)
    
    time.sleep(1)  # Kurz warten für Broadcast
    
    # Mempools beider Nodes prüfen
    health1 = requests.get(f"{NODE1}/health").json()
    health2 = requests.get(f"{NODE2}/health").json()
    
    print(f"Node 1 Mempool: {health1['pending_transactions']} Transaktionen")
    print(f"Node 2 Mempool: {health2['pending_transactions']} Transaktionen")
    
    # Beide sollten die Transaktion haben
    return health1['pending_transactions'] >= 1 and health2['pending_transactions'] >= 1

def test_block_synchronization():
    """Test: Block-Synchronisierung zwischen Nodes"""
    print_header("TEST 3: Block-Synchronisierung")
    
    # 4 weitere Transaktionen an Node 1 → sollte Auto-Mining auslösen
    print("Füge 4 Transaktionen hinzu, um Mining auszulösen...")
    for i in range(4):
        tx = {
            "sender": f"Person{i}",
            "recipient": "WWF",
            "amount": 10 * (i + 1)
        }
        requests.post(f"{NODE1}/transactions/new", json=tx)
        time.sleep(0.3)
    
    print("⏳ Warte auf Mining und Synchronisierung...")
    time.sleep(5)
    
    # Chain-Längen prüfen
    chain1 = requests.get(f"{NODE1}/chain").json()
    chain2 = requests.get(f"{NODE2}/chain").json()
    
    print(f"Node 1 Chain-Länge: {chain1['length']} Blöcke")
    print(f"Node 2 Chain-Länge: {chain2['length']} Blöcke")
    
    # Beide sollten die gleiche Länge haben
    return chain1['length'] == chain2['length'] and chain1['length'] >= 2

def test_consensus():
    """Test: Konsens-Algorithmus (längste Chain gewinnt)"""
    print_header("TEST 4: Konsens-Algorithmus")
    
    # Node 2 manuell Konsens starten
    print("Starte Konsens auf Node 2...")
    r = requests.post(f"{NODE2}/consensus")
    result = r.json()
    
    print(f"Ergebnis: {result['message']}")
    
    # Beide Chains sollten gleich sein
    chain1 = requests.get(f"{NODE1}/chain").json()
    chain2 = requests.get(f"{NODE2}/chain").json()
    
    # Vergleiche die letzten Block-Hashes
    hash1 = chain1['chain'][-1]['hash']
    hash2 = chain2['chain'][-1]['hash']
    
    print(f"Node 1 letzter Hash: {hash1[:40]}...")
    print(f"Node 2 letzter Hash: {hash2[:40]}...")
    
    return hash1 == hash2

def test_statistics_sync():
    """Test: Statistiken sind auf beiden Nodes gleich"""
    print_header("TEST 5: Statistik-Synchronisierung")
    
    stats1 = requests.get(f"{NODE1}/stats").json()
    stats2 = requests.get(f"{NODE2}/stats").json()
    
    print(f"Node 1 Total Donations: {stats1['total_donations']}€")
    print(f"Node 2 Total Donations: {stats2['total_donations']}€")
    
    print(f"Node 1 Total Blocks: {stats1['total_blocks']}")
    print(f"Node 2 Total Blocks: {stats2['total_blocks']}")
    
    return (stats1['total_donations'] == stats2['total_donations'] and
            stats1['total_blocks'] == stats2['total_blocks'])

def run_all_tests():
    """Führt alle P2P-Tests aus"""
    print("\n" + "🌐"*30)
    print("  P2P BLOCKCHAIN TESTS")
    print("🌐"*30)
    
    if not wait_for_nodes():
        print("\n❌ Nodes sind nicht bereit. Breche ab.")
        return
    
    tests = [
        ("Node-Registrierung", test_p2p_registration),
        ("Transaction Broadcasting", test_transaction_broadcast),
        ("Block-Synchronisierung", test_block_synchronization),
        ("Konsens-Algorithmus", test_consensus),
        ("Statistik-Sync", test_statistics_sync),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            time.sleep(1)  # Kurze Pause zwischen Tests
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
    
    print(f"\nErgebnis: {passed}/{total} P2P-Tests bestanden")
    print("="*60 + "\n")

if __name__ == "__main__":
    run_all_tests()