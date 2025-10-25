import hashlib
import json
import time
from typing import List, Dict, Any


class Block:
    """
    Ein Block in der Blockchain.
    Enthält Transaktionen und ist mit dem vorherigen Block verkettet.
    """
    
    def __init__(self, index: int, transactions: List[Dict], previous_hash: str, timestamp: float = None):
        """
        Initialisiert einen neuen Block.
        
        Args:
            index: Position in der Blockchain (0 = Genesis Block)
            transactions: Liste von Transaktionen (Spenden)
            previous_hash: Hash des vorherigen Blocks
            timestamp: Zeitpunkt der Block-Erstellung (optional)
        """
        self.index = index
        self.transactions = transactions
        self.previous_hash = previous_hash
        self.timestamp = timestamp or time.time()
        self.nonce = 0  # Wird beim Mining verändert
        self.hash = ""  # Wird beim Mining berechnet
    
    def calculate_hash(self) -> str:
        """
        Berechnet den SHA-256 Hash dieses Blocks.
        Der Hash hängt von allen Block-Daten ab, inkl. Nonce.
        
        Returns:
            Hex-String des Hash-Werts
        """
        # Alle Block-Daten in einen String umwandeln
        block_string = json.dumps({
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce
        }, sort_keys=True)
        
        # SHA-256 Hash berechnen
        return hashlib.sha256(block_string.encode()).hexdigest()
    
    def mine_block(self, difficulty: int):
        """
        Proof-of-Work: Findet eine Nonce, sodass der Hash mit 'difficulty' Nullen beginnt.
        
        Args:
            difficulty: Anzahl führender Nullen (z.B. 4 = "0000...")
        """
        # Ziel: Hash muss mit dieser Anzahl Nullen beginnen
        target = "0" * difficulty
        
        print(f"⛏️  Mining Block {self.index}...")
        start_time = time.time()
        
        # Solange probieren, bis der Hash die Bedingung erfüllt
        while not self.hash.startswith(target):
            self.nonce += 1
            self.hash = self.calculate_hash()
        
        mining_time = time.time() - start_time
        print(f"✅ Block {self.index} gemined! Hash: {self.hash[:20]}... (Nonce: {self.nonce}, Zeit: {mining_time:.2f}s)")
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert den Block in ein Dictionary (für JSON)."""
        return {
            "index": self.index,
            "transactions": self.transactions,
            "previous_hash": self.previous_hash,
            "timestamp": self.timestamp,
            "nonce": self.nonce,
            "hash": self.hash
        }


class Blockchain:
    """
    Die Blockchain selbst.
    Verwaltet die Kette von Blöcken, den Mempool und das Mining.
    """
    
    def __init__(self, difficulty: int = 4):
        """
        Initialisiert eine neue Blockchain.
        
        Args:
            difficulty: Mining-Schwierigkeit (Anzahl führender Nullen)
        """
        self.chain: List[Block] = []
        self.difficulty = difficulty
        self.mempool: List[Dict] = []  # Noch nicht geminte Transaktionen
        self.max_transactions_per_block = 5  # Blöcke mit max. 5 Transaktionen
        
        # Genesis Block erstellen (der erste Block)
        self.create_genesis_block()
    
    def create_genesis_block(self):
        """Erstellt den ersten Block in der Chain."""
        genesis_block = Block(
            index=0,
            transactions=[{
                "sender": "System",
                "recipient": "Genesis",
                "amount": 0,
                "timestamp": time.time()
            }],
            previous_hash="0"
        )
        genesis_block.mine_block(self.difficulty)
        self.chain.append(genesis_block)
        print(f"🎉 Genesis Block erstellt!\n")
    
    def get_latest_block(self) -> Block:
        """Gibt den neuesten Block in der Chain zurück."""
        return self.chain[-1]
    
    def add_transaction(self, sender: str, recipient: str, amount: float) -> bool:
        """
        Fügt eine neue Transaktion zum Mempool hinzu.
        
        Args:
            sender: Name des Spenders (oder "Anonymous")
            recipient: Name der Organisation
            amount: Spendenbetrag
            
        Returns:
            True wenn erfolgreich
        """
        transaction = {
            "sender": sender,
            "recipient": recipient,
            "amount": amount,
            "timestamp": time.time()
        }
        
        self.mempool.append(transaction)
        print(f"📝 Transaktion hinzugefügt: {sender} → {recipient}: {amount}€")
        
        # Automatisch minen, wenn genug Transaktionen da sind
        if len(self.mempool) >= self.max_transactions_per_block:
            self.mine_pending_transactions()
        
        return True
    
    def mine_pending_transactions(self):
        """
        Mined alle Transaktionen im Mempool zu einem neuen Block.
        """
        if not self.mempool:
            print("⚠️  Keine Transaktionen zum Minen vorhanden.")
            return False
        
        # Neuen Block mit allen Transaktionen aus dem Mempool erstellen
        new_block = Block(
            index=len(self.chain),
            transactions=self.mempool.copy(),
            previous_hash=self.get_latest_block().hash
        )
        
        # Block minen (Proof-of-Work)
        new_block.mine_block(self.difficulty)
        
        # Block zur Chain hinzufügen
        self.chain.append(new_block)
        
        # Mempool leeren
        self.mempool = []
        
        return True
    
    def is_chain_valid(self) -> bool:
        """
        Überprüft, ob die Blockchain gültig ist.
        Checkt alle Hashes und die Verkettung.
        
        Returns:
            True wenn die Chain gültig ist, sonst False
        """
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]
            
            # 1. Check: Ist der gespeicherte Hash korrekt?
            if current_block.hash != current_block.calculate_hash():
                print(f"❌ Block {i}: Hash wurde manipuliert!")
                return False
            
            # 2. Check: Stimmt die Verkettung?
            if current_block.previous_hash != previous_block.hash:
                print(f"❌ Block {i}: Previous Hash stimmt nicht!")
                return False
            
            # 3. Check: Erfüllt der Hash die Schwierigkeit?
            if not current_block.hash.startswith("0" * self.difficulty):
                print(f"❌ Block {i}: Proof-of-Work ungültig!")
                return False
        
        return True
    
    def replace_chain(self, new_chain: List[Dict]) -> bool:
        """
        Ersetzt die aktuelle Chain, wenn die neue länger und gültig ist.
        (Konsens-Mechanismus: Longest Chain Rule)
        
        Args:
            new_chain: Die neue Chain als Liste von Dictionaries
            
        Returns:
            True wenn ersetzt wurde, sonst False
        """
        # Chain aus Dictionaries zurück in Block-Objekte umwandeln
        new_blockchain = Blockchain(difficulty=self.difficulty)
        new_blockchain.chain = []
        
        for block_data in new_chain:
            block = Block(
                index=block_data['index'],
                transactions=block_data['transactions'],
                previous_hash=block_data['previous_hash'],
                timestamp=block_data['timestamp']
            )
            block.nonce = block_data['nonce']
            block.hash = block_data['hash']
            new_blockchain.chain.append(block)
        
        # Prüfen: Ist die neue Chain länger und gültig?
        if len(new_blockchain.chain) > len(self.chain) and new_blockchain.is_chain_valid():
            print(f"🔄 Chain ersetzt! Neue Länge: {len(new_blockchain.chain)}")
            self.chain = new_blockchain.chain
            return True
        
        return False
    
    def get_chain_data(self) -> List[Dict]:
        """Gibt die gesamte Chain als Liste von Dictionaries zurück."""
        return [block.to_dict() for block in self.chain]
    
    def print_chain(self):
        """Gibt die gesamte Blockchain formatiert aus."""
        print("\n" + "="*60)
        print("📊 BLOCKCHAIN STATUS")
        print("="*60)
        print(f"Länge: {len(self.chain)} Blöcke")
        print(f"Schwierigkeit: {self.difficulty}")
        print(f"Mempool: {len(self.mempool)} ausstehende Transaktionen")
        print(f"Gültig: {'✅ Ja' if self.is_chain_valid() else '❌ Nein'}")
        print("="*60 + "\n")
        
        for block in self.chain:
            print(f"Block #{block.index}")
            print(f"  Hash: {block.hash[:40]}...")
            print(f"  Previous Hash: {block.previous_hash[:40]}...")
            print(f"  Transaktionen: {len(block.transactions)}")
            for tx in block.transactions:
                print(f"    - {tx['sender']} → {tx['recipient']}: {tx['amount']}€")
            print()


# Test-Code (wird nur ausgeführt, wenn diese Datei direkt gestartet wird)
if __name__ == "__main__":
    print("🚀 Blockchain-Test wird gestartet...\n")
    
    # Blockchain mit Schwierigkeit 4 erstellen
    blockchain = Blockchain(difficulty=4)
    
    # Ein paar Test-Transaktionen hinzufügen
    blockchain.add_transaction("Alice", "Rotes Kreuz", 50)
    blockchain.add_transaction("Bob", "WWF", 30)
    blockchain.add_transaction("Charlie", "Ärzte ohne Grenzen", 100)
    blockchain.add_transaction("Diana", "UNICEF", 75)
    blockchain.add_transaction("Eve", "Greenpeace", 25)
    
    # Weitere Transaktionen (wird automatisch einen zweiten Block erstellen)
    blockchain.add_transaction("Frank", "Rotes Kreuz", 60)
    
    # Blockchain ausgeben
    blockchain.print_chain()
    
    # Validierung testen
    print(f"Ist die Blockchain gültig? {blockchain.is_chain_valid()}")
    
    # Manipulation testen
    print("\n🔧 Manipuliere Block 1...")
    blockchain.chain[1].transactions[0]['amount'] = 999999
    print(f"Ist die Blockchain noch gültig? {blockchain.is_chain_valid()}")