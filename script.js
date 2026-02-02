/**
 * Holiday Destination Vote - Live Dashboard
 * Fetches voting data from ThingSpeak and displays real-time results
 */

// ========================================
// Configuration (READ-ONLY API - safe to expose)
// ========================================
const CONFIG = {
    channelId: '3247666',
    readApiKey: 'S1P2IM4XU8SG73CJ',
    refreshInterval: 5,
    apiBaseUrl: 'https://api.thingspeak.com'
};

// Candidate mapping (Field number -> Candidate info)
const CANDIDATES = [
    { field: 1, name: 'Japan', flag: '🇯🇵', class: 'japan' },
    { field: 2, name: 'Germany', flag: '🇩🇪', class: 'germany' },
    { field: 3, name: 'Switzerland', flag: '🇨🇭', class: 'switzerland' },
    { field: 4, name: 'Norway', flag: '🇳🇴', class: 'norway' }
];

// ========================================
// State
// ========================================
let votes = {};
let countdown = CONFIG.refreshInterval;
let refreshTimer = null;
let countdownTimer = null;

// ========================================
// DOM Elements
// ========================================
const elements = {
    statusBadge: document.getElementById('status-badge'),
    statusText: document.querySelector('.status-text'),
    totalVotes: document.getElementById('total-votes'),
    lastUpdate: document.getElementById('last-update'),
    refreshCountdown: document.getElementById('refresh-countdown'),
    candidatesGrid: document.getElementById('candidates-grid'),
    winnerBanner: document.getElementById('winner-banner'),
    winnerName: document.getElementById('winner-name')
};

// ========================================
// Initialize
// ========================================
function init() {
    renderCandidateCards();
    fetchVotes();
    startAutoRefresh();
}

// ========================================
// Render Candidate Cards (Initial)
// ========================================
function renderCandidateCards() {
    elements.candidatesGrid.innerHTML = CANDIDATES.map(candidate => `
        <article class="candidate-card ${candidate.class} loading" id="card-${candidate.field}">
            <div class="candidate-header">
                <span class="candidate-flag">${candidate.flag}</span>
                <div class="candidate-info">
                    <h2 class="candidate-name">${candidate.name}</h2>
                    <span class="candidate-rank" id="rank-${candidate.field}">Loading...</span>
                </div>
            </div>
            <div class="candidate-votes">
                <span class="vote-count" id="votes-${candidate.field}">--</span>
                <span class="vote-label">votes</span>
            </div>
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" id="progress-${candidate.field}"></div>
                </div>
                <div class="progress-percent" id="percent-${candidate.field}">0%</div>
            </div>
        </article>
    `).join('');
}

// ========================================
// Fetch Votes from ThingSpeak
// ========================================
async function fetchVotes() {
    updateStatus('loading', 'Fetching...');

    try {
        const url = `${CONFIG.apiBaseUrl}/channels/${CONFIG.channelId}/feeds/last.json?api_key=${CONFIG.readApiKey}`;
        const response = await fetch(url);

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (!data || Object.keys(data).length === 0) {
            showNoData();
            updateStatus('offline', 'No Data');
            return;
        }

        // Parse votes from fields
        CANDIDATES.forEach(candidate => {
            const fieldKey = `field${candidate.field}`;
            votes[candidate.field] = parseInt(data[fieldKey]) || 0;
        });

        updateDisplay();
        updateStatus('live', 'Live');

    } catch (error) {
        console.error('Error fetching votes:', error);
        updateStatus('offline', 'Offline');
    }
}

// ========================================
// Update Display
// ========================================
function updateDisplay() {
    const totalVotes = Object.values(votes).reduce((sum, v) => sum + v, 0);

    // Update total votes
    animateNumber(elements.totalVotes, totalVotes);

    // Update last update time
    const now = new Date();
    elements.lastUpdate.textContent = now.toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    });

    // Sort candidates by votes to determine ranking
    const sortedCandidates = [...CANDIDATES].sort((a, b) =>
        (votes[b.field] || 0) - (votes[a.field] || 0)
    );

    // Update each candidate card
    CANDIDATES.forEach(candidate => {
        const voteCount = votes[candidate.field] || 0;
        const percentage = totalVotes > 0 ? (voteCount / totalVotes) * 100 : 0;
        const rank = sortedCandidates.findIndex(c => c.field === candidate.field) + 1;

        const card = document.getElementById(`card-${candidate.field}`);
        const votesEl = document.getElementById(`votes-${candidate.field}`);
        const progressEl = document.getElementById(`progress-${candidate.field}`);
        const percentEl = document.getElementById(`percent-${candidate.field}`);
        const rankEl = document.getElementById(`rank-${candidate.field}`);

        // Remove loading state
        card.classList.remove('loading');

        // Update values
        animateNumber(votesEl, voteCount);
        progressEl.style.width = `${percentage}%`;
        percentEl.textContent = `${percentage.toFixed(1)}%`;
        rankEl.textContent = getRankLabel(rank);

        // Highlight leader
        if (rank === 1 && totalVotes > 0) {
            card.classList.add('leading');
        } else {
            card.classList.remove('leading');
        }
    });

    // Update winner banner
    if (totalVotes > 0) {
        const winner = sortedCandidates[0];
        elements.winnerName.textContent = `${winner.flag} ${winner.name}`;
        elements.winnerBanner.classList.add('visible');
    } else {
        elements.winnerBanner.classList.remove('visible');
    }
}

// ========================================
// Helper Functions
// ========================================
function getRankLabel(rank) {
    const labels = ['🥇 1st Place', '🥈 2nd Place', '🥉 3rd Place', '4th Place'];
    return labels[rank - 1] || `${rank}th Place`;
}

function animateNumber(element, targetValue) {
    const currentValue = parseInt(element.textContent) || 0;

    if (currentValue === targetValue) {
        element.textContent = targetValue;
        return;
    }

    const duration = 500;
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);

        // Ease out cubic
        const easeProgress = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(currentValue + (targetValue - currentValue) * easeProgress);

        element.textContent = value;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

function updateStatus(status, text) {
    elements.statusBadge.className = `status-badge ${status}`;
    elements.statusText.textContent = text;
}

function showNoData() {
    elements.candidatesGrid.innerHTML = `
        <div class="no-data-message" style="grid-column: 1 / -1;">
            <div class="no-data-icon">📊</div>
            <p class="no-data-text">No votes recorded yet</p>
            <p style="color: var(--text-muted); margin-top: 0.5rem;">
                Waiting for the first vote...
            </p>
        </div>
    `;
    elements.winnerBanner.classList.remove('visible');
}

// ========================================
// Auto Refresh
// ========================================
function startAutoRefresh() {
    // Clear existing timers
    if (refreshTimer) clearInterval(refreshTimer);
    if (countdownTimer) clearInterval(countdownTimer);

    // Reset countdown
    countdown = CONFIG.refreshInterval;
    elements.refreshCountdown.textContent = `${countdown}s`;

    // Countdown timer (every second)
    countdownTimer = setInterval(() => {
        countdown--;
        elements.refreshCountdown.textContent = `${countdown}s`;

        if (countdown <= 0) {
            countdown = CONFIG.refreshInterval;
        }
    }, 1000);

    // Refresh timer
    refreshTimer = setInterval(() => {
        fetchVotes();
        countdown = CONFIG.refreshInterval;
    }, CONFIG.refreshInterval * 1000);
}

// ========================================
// Start Application
// ========================================
document.addEventListener('DOMContentLoaded', init);
