// Konfiguration - PASSE DIESE IPS AN!
const NODES = [
    'http://192.168.178.95:5002',  // Pi 5
    'http://192.168.178.99:5002'   // Pi 4
];

// Globale Variablen
let currentNodeIndex = 0;
let organizations = [];
let updateInterval;

// ==================== HELPER FUNCTIONS ====================

// Aktuellen Node holen
function getCurrentNode() {
    return NODES[currentNodeIndex];
}

// Zum nächsten Node wechseln (Load Balancing)
function switchToNextNode() {
    currentNodeIndex = (currentNodeIndex + 1) % NODES.length;
}

// API Request mit Fallback zu anderem Node
async function apiRequest(endpoint, options = {}) {
    for (let attempt = 0; attempt < NODES.length; attempt++) {
        try {
            const node = getCurrentNode();
            const response = await fetch(`${node}${endpoint}`, {
                ...options,
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error(`Fehler bei ${getCurrentNode()}: ${error.message}`);
            switchToNextNode();
            
            if (attempt === NODES.length - 1) {
                throw new Error('Alle Nodes nicht erreichbar');
            }
        }
    }
}

// Toast Notification anzeigen
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// Datum formatieren
function formatDate(timestamp) {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString('de-DE');
}

// ==================== NODE STATUS ====================

async function updateNodeStatus() {
    for (let i = 0; i < NODES.length; i++) {
        const statusElement = document.getElementById(`node${i + 1}-status`);
        const indicator = statusElement.querySelector('.node-indicator');
        const blocksSpan = statusElement.querySelector('.node-blocks');
        
        try {
            const response = await fetch(`${NODES[i]}/health`, { timeout: 5000 });
            const data = await response.json();
            
            indicator.classList.remove('offline');
            indicator.classList.add('online');
            blocksSpan.textContent = `${data.blocks} Blöcke`;
        } catch (error) {
            indicator.classList.remove('online');
            indicator.classList.add('offline');
            blocksSpan.textContent = 'Offline';
        }
    }
}

// ==================== ORGANIZATIONS ====================

async function loadOrganizations() {
    try {
        const data = await apiRequest('/organizations');
        organizations = data.organizations;
        
        const select = document.getElementById('organization');
        select.innerHTML = '<option value="">-- Bitte wählen --</option>';
        
        organizations.forEach(org => {
            const option = document.createElement('option');
            option.value = org;
            option.textContent = org;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Fehler beim Laden der Organisationen:', error);
        showToast('Konnte Organisationen nicht laden', 'error');
    }
}

// ==================== DONATION FORM ====================

async function handleDonation(e) {
    e.preventDefault();
    
    const sender = document.getElementById('sender').value || 'Anonymer Spender';
    const recipient = document.getElementById('organization').value;
    const amount = parseFloat(document.getElementById('amount').value);
    
    if (!recipient) {
        showToast('Bitte wähle eine Organisation', 'error');
        return;
    }
    
    if (!amount || amount <= 0) {
        showToast('Bitte gib einen gültigen Betrag ein', 'error');
        return;
    }
    
    const btn = document.getElementById('donate-btn');
    btn.disabled = true;
    btn.innerHTML = '<span>⏳ Wird gesendet...</span>';
    
    try {
        await apiRequest('/transactions/new', {
            method: 'POST',
            body: JSON.stringify({
                sender: sender,
                recipient: recipient,
                amount: amount
            })
        });
        
        showToast(`✅ Spende von ${amount}€ an ${recipient} erfolgreich!`, 'success');
        
        // Formular zurücksetzen
        document.getElementById('amount').value = '';
        document.getElementById('organization').value = '';
        
        // Daten aktualisieren
        setTimeout(() => {
            loadStatistics();
            loadRecentTransactions();
        }, 1000);
        
    } catch (error) {
        console.error('Fehler beim Spenden:', error);
        showToast('Spende fehlgeschlagen. Versuche es erneut.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<span>💰 Spenden</span>';
    }
}

// ==================== STATISTICS ====================

async function loadStatistics() {
    try {
        const data = await apiRequest('/stats');
        
        document.getElementById('total-donations').textContent = `${data.total_donations} €`;
        document.getElementById('total-blocks').textContent = data.total_blocks;
        document.getElementById('pending-transactions').textContent = data.pending_transactions;
        
        const validBadge = document.getElementById('chain-valid');
        if (data.chain_valid) {
            validBadge.innerHTML = '<span class="status-badge valid">✓ Gültig</span>';
        } else {
            validBadge.innerHTML = '<span class="status-badge invalid">✗ Ungültig</span>';
        }
        
        // Spenden pro Organisation
        const orgList = document.getElementById('org-list');
        orgList.innerHTML = '';
        
        const sortedOrgs = Object.entries(data.donations_per_organization)
            .sort((a, b) => b[1] - a[1]);
        
        sortedOrgs.forEach(([org, amount]) => {
            const item = document.createElement('div');
            item.className = 'org-item';
            item.innerHTML = `
                <span class="org-name">${org}</span>
                <span class="org-amount">${amount} €</span>
            `;
            orgList.appendChild(item);
        });
        
    } catch (error) {
        console.error('Fehler beim Laden der Statistiken:', error);
    }
}

// ==================== RECENT TRANSACTIONS ====================

async function loadRecentTransactions() {
    try {
        const data = await apiRequest('/chain');
        const chain = data.chain;
        
        const container = document.getElementById('recent-transactions');
        
        // Alle Transaktionen sammeln (außer Genesis)
        let allTransactions = [];
        for (let i = 1; i < chain.length; i++) {
            const block = chain[i];
            block.transactions.forEach(tx => {
                allTransactions.push({
                    ...tx,
                    blockIndex: block.index
                });
            });
        }
        
        // Neueste zuerst
        allTransactions.reverse();
        
        // Nur die letzten 10 anzeigen
        const recentTransactions = allTransactions.slice(0, 10);
        
        if (recentTransactions.length === 0) {
            container.innerHTML = '<p class="loading">Noch keine Transaktionen</p>';
            return;
        }
        
        container.innerHTML = '<div class="transaction-list"></div>';
        const list = container.querySelector('.transaction-list');
        
        recentTransactions.forEach(tx => {
            const item = document.createElement('div');
            item.className = 'transaction-item';
            item.innerHTML = `
                <div class="transaction-info">
                    <span class="transaction-sender">${tx.sender}</span>
                    <span class="transaction-recipient">→ ${tx.recipient}</span>
                </div>
                <span class="transaction-amount">${tx.amount} €</span>
            `;
            list.appendChild(item);
        });
        
    } catch (error) {
        console.error('Fehler beim Laden der Transaktionen:', error);
    }
}

// ==================== BLOCKCHAIN VIEW ====================

async function loadBlockchain() {
    try {
        const data = await apiRequest('/chain');
        const chain = data.chain;
        
        const container = document.getElementById('blockchain-view');
        
        if (chain.length === 0) {
            container.innerHTML = '<p class="loading">Keine Blöcke vorhanden</p>';
            return;
        }
        
        container.innerHTML = '<div class="block-list"></div>';
        const list = container.querySelector('.block-list');
        
        // Neueste Blöcke zuerst
        const reversedChain = [...chain].reverse();
        
        reversedChain.forEach(block => {
            const item = document.createElement('div');
            item.className = 'block-item';
            
            const txCount = block.transactions.length;
            const time = formatDate(block.timestamp);
            
            item.innerHTML = `
                <div class="block-header">
                    <span class="block-index">Block #${block.index}</span>
                    <span class="block-time">${time}</span>
                </div>
                <div class="block-hash">
                    <strong>Hash:</strong> ${block.hash}
                </div>
                <div class="block-hash">
                    <strong>Previous:</strong> ${block.previous_hash}
                </div>
                <div class="block-transactions">
                    <strong>Transaktionen:</strong> ${txCount} | <strong>Nonce:</strong> ${block.nonce}
                </div>
            `;
            list.appendChild(item);
        });
        
    } catch (error) {
        console.error('Fehler beim Laden der Blockchain:', error);
        document.getElementById('blockchain-view').innerHTML = 
            '<p class="loading">Fehler beim Laden der Blockchain</p>';
    }
}

// ==================== ADMIN FUNCTIONS ====================

async function syncNodes() {
    const btn = document.getElementById('sync-nodes');
    const msg = document.getElementById('admin-message');
    
    btn.disabled = true;
    btn.textContent = '⏳ Synchronisiere...';
    
    try {
        // Registriere Nodes gegenseitig
        await fetch(`${NODES[0]}/nodes/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_address: NODES[1] })
        });
        
        await fetch(`${NODES[1]}/nodes/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ node_address: NODES[0] })
        });
        
        msg.className = 'message success';
        msg.textContent = '✅ Nodes erfolgreich synchronisiert!';
        showToast('Nodes synchronisiert', 'success');
        
    } catch (error) {
        msg.className = 'message error';
        msg.textContent = '❌ Synchronisierung fehlgeschlagen';
        showToast('Synchronisierung fehlgeschlagen', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔄 Nodes synchronisieren';
    }
}

async function manualMine() {
    const btn = document.getElementById('manual-mine');
    const msg = document.getElementById('admin-message');
    
    btn.disabled = true;
    btn.textContent = '⏳ Mining...';
    
    try {
        await apiRequest('/mine', { method: 'POST' });
        
        msg.className = 'message success';
        msg.textContent = '✅ Block erfolgreich gemined!';
        showToast('Block gemined!', 'success');
        
        // Daten aktualisieren
        setTimeout(() => {
            loadStatistics();
            loadBlockchain();
            loadRecentTransactions();
            updateNodeStatus();
        }, 2000);
        
    } catch (error) {
        msg.className = 'message error';
        msg.textContent = '❌ Mining fehlgeschlagen. Keine Transaktionen vorhanden?';
        showToast('Mining fehlgeschlagen', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '⛏️ Manuell minen';
    }
}

async function runConsensus() {
    const btn = document.getElementById('run-consensus');
    const msg = document.getElementById('admin-message');
    
    btn.disabled = true;
    btn.textContent = '⏳ Konsens läuft...';
    
    try {
        // Konsens auf beiden Nodes starten
        await Promise.all([
            fetch(`${NODES[0]}/consensus`, { method: 'POST' }),
            fetch(`${NODES[1]}/consensus`, { method: 'POST' })
        ]);
        
        msg.className = 'message success';
        msg.textContent = '✅ Konsens erfolgreich durchgeführt!';
        showToast('Konsens durchgeführt', 'success');
        
        // Daten aktualisieren
        setTimeout(() => {
            loadStatistics();
            loadBlockchain();
            updateNodeStatus();
        }, 1000);
        
    } catch (error) {
        msg.className = 'message error';
        msg.textContent = '❌ Konsens fehlgeschlagen';
        showToast('Konsens fehlgeschlagen', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🤝 Konsens starten';
    }
}

// ==================== INITIALIZATION ====================

async function initializeApp() {
    console.log('🚀 Blockchain Donation Platform wird gestartet...');
    console.log('Nodes:', NODES);
    
    // Event Listeners
    document.getElementById('donation-form').addEventListener('submit', handleDonation);
    document.getElementById('refresh-stats').addEventListener('click', loadStatistics);
    document.getElementById('refresh-chain').addEventListener('click', loadBlockchain);
    document.getElementById('sync-nodes').addEventListener('click', syncNodes);
    document.getElementById('manual-mine').addEventListener('click', manualMine);
    document.getElementById('run-consensus').addEventListener('click', runConsensus);
    
    // Initial laden
    await loadOrganizations();
    await updateNodeStatus();
    await loadStatistics();
    await loadRecentTransactions();
    await loadBlockchain();
    
    // Auto-Update alle 10 Sekunden
    updateInterval = setInterval(async () => {
        await updateNodeStatus();
        await loadStatistics();
        await loadRecentTransactions();
    }, 10000);
    
    console.log('✅ App erfolgreich initialisiert!');
}

// App starten wenn DOM geladen ist
document.addEventListener('DOMContentLoaded', initializeApp);

// Cleanup beim Verlassen der Seite
window.addEventListener('beforeunload', () => {
    if (updateInterval) {
        clearInterval(updateInterval);
    }
});