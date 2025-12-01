// Dashboard JavaScript
let currentPage = 1;
const perPage = 20;

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    // Update time
    updateTime();
    setInterval(updateTime, 1000);
    
    // Load initial data
    loadStats();
    loadAllUsers();
    
    // Setup tab navigation
    setupTabs();
    
    // Auto-refresh stats every 30 seconds
    setInterval(loadStats, 30000);
});

// Update current time
function updateTime() {
    const now = new Date();
    document.getElementById('current-time').textContent = now.toLocaleString();
}

// Setup tab navigation
function setupTabs() {
    const tabButtons = document.querySelectorAll('.tab-button');
    
    tabButtons.forEach(button => {
        button.addEventListener('click', function() {
            const targetTab = this.getAttribute('data-tab');
            
            // Remove active class from all buttons and panes
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
            
            // Add active class to clicked button and target pane
            this.classList.add('active');
            document.getElementById(targetTab).classList.add('active');
            
            // Load data for the tab
            loadTabData(targetTab);
        });
    });
}

// Load data for specific tab
function loadTabData(tab) {
    switch(tab) {
        case 'all-users':
            loadAllUsers();
            break;
        case 'online-users':
            loadOnlineUsers();
            break;
        case 'in-chat':
            loadUsersInChat();
            break;
        case 'in-queue':
            loadUsersInQueue();
            break;
    }
}

// Load statistics
async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const data = await response.json();
        
        document.getElementById('total-users').textContent = data.total_users || 0;
        document.getElementById('users-with-profiles').textContent = data.users_with_profiles || 0;
        document.getElementById('active-users').textContent = data.active_users || 0;
        document.getElementById('users-in-queue').textContent = data.users_in_queue || 0;
        document.getElementById('users-in-chat').textContent = data.users_in_chat || 0;
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

// Load all users
async function loadAllUsers(page = 1) {
    currentPage = page;
    const tbody = document.getElementById('all-users-table');
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Loading...</td></tr>';
    
    try {
        const response = await fetch(`/api/users?page=${page}&per_page=${perPage}`);
        const data = await response.json();
        
        if (data.users && data.users.length > 0) {
            tbody.innerHTML = data.users.map(user => createUserRow(user)).join('');
            
            // Update pagination info
            document.getElementById('pagination-info').textContent = 
                `Showing ${((page - 1) * perPage) + 1}-${Math.min(page * perPage, data.total)} of ${data.total} users`;
            
            // Create pagination
            createPagination(data.page, data.total_pages);
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No users found</td></tr>';
            document.getElementById('pagination-info').textContent = '';
            document.getElementById('pagination').innerHTML = '';
        }
    } catch (error) {
        console.error('Error loading users:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">Error loading users</td></tr>';
    }
}

// Load online users
async function loadOnlineUsers() {
    const tbody = document.getElementById('online-users-table');
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Loading...</td></tr>';
    
    try {
        const response = await fetch('/api/users/online');
        const users = await response.json();
        
        if (users && users.length > 0) {
            tbody.innerHTML = users.map(user => createUserRow(user)).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="no-data">No online users</td></tr>';
        }
    } catch (error) {
        console.error('Error loading online users:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">Error loading users</td></tr>';
    }
}

// Load users in chat
async function loadUsersInChat() {
    const tbody = document.getElementById('in-chat-table');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading...</td></tr>';
    
    try {
        const response = await fetch('/api/users/in-chat');
        const users = await response.json();
        
        if (users && users.length > 0) {
            tbody.innerHTML = users.map(user => createUserRowWithPartner(user)).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">No users in chat</td></tr>';
        }
    } catch (error) {
        console.error('Error loading users in chat:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">Error loading users</td></tr>';
    }
}

// Load users in queue
async function loadUsersInQueue() {
    const tbody = document.getElementById('in-queue-table');
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Loading...</td></tr>';
    
    try {
        const response = await fetch('/api/users/in-queue');
        const users = await response.json();
        
        if (users && users.length > 0) {
            tbody.innerHTML = users.map(user => createUserRow(user)).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="no-data">No users in queue</td></tr>';
        }
    } catch (error) {
        console.error('Error loading users in queue:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">Error loading users</td></tr>';
    }
}

// Search users
async function searchUsers() {
    const tbody = document.getElementById('search-results-table');
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Searching...</td></tr>';
    
    const userId = document.getElementById('search-user-id').value;
    const username = document.getElementById('search-username').value;
    const gender = document.getElementById('search-gender').value;
    const country = document.getElementById('search-country').value;
    
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (username) params.append('username', username);
    if (gender) params.append('gender', gender);
    if (country) params.append('country', country);
    
    try {
        const response = await fetch(`/api/users/search?${params}`);
        const users = await response.json();
        
        if (users && users.length > 0) {
            tbody.innerHTML = users.map(user => createUserRow(user)).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="no-data">No users found</td></tr>';
        }
    } catch (error) {
        console.error('Error searching users:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">Error searching users</td></tr>';
    }
}

// Clear search
function clearSearch() {
    document.getElementById('search-user-id').value = '';
    document.getElementById('search-username').value = '';
    document.getElementById('search-gender').value = '';
    document.getElementById('search-country').value = '';
    document.getElementById('search-results-table').innerHTML = 
        '<tr><td colspan="5" class="no-data">Enter search criteria above</td></tr>';
}

// Create user table row
function createUserRow(user) {
    return `
        <tr>
            <td>${user.user_id}</td>
            <td>${user.username || 'N/A'}</td>
            <td>${user.gender || 'N/A'}</td>
            <td>${user.country || 'N/A'}</td>
            <td>
                <button class="btn btn-primary btn-small" onclick="viewUser(${user.user_id})">
                    View Details
                </button>
            </td>
        </tr>
    `;
}

// Create user table row with partner
function createUserRowWithPartner(user) {
    return `
        <tr>
            <td>${user.user_id}</td>
            <td>${user.username || 'N/A'}</td>
            <td>${user.gender || 'N/A'}</td>
            <td>${user.country || 'N/A'}</td>
            <td>${user.partner_id || 'N/A'}</td>
            <td>
                <button class="btn btn-primary btn-small" onclick="viewUser(${user.user_id})">
                    View Details
                </button>
            </td>
        </tr>
    `;
}

// Create pagination
function createPagination(currentPage, totalPages) {
    const paginationDiv = document.getElementById('pagination');
    
    if (totalPages <= 1) {
        paginationDiv.innerHTML = '';
        return;
    }
    
    let html = '';
    
    // Previous button
    html += `<button class="page-btn" ${currentPage === 1 ? 'disabled' : ''} 
             onclick="loadAllUsers(${currentPage - 1})">Previous</button>`;
    
    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === 1 || i === totalPages || (i >= currentPage - 2 && i <= currentPage + 2)) {
            html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" 
                     onclick="loadAllUsers(${i})">${i}</button>`;
        } else if (i === currentPage - 3 || i === currentPage + 3) {
            html += '<span>...</span>';
        }
    }
    
    // Next button
    html += `<button class="page-btn" ${currentPage === totalPages ? 'disabled' : ''} 
             onclick="loadAllUsers(${currentPage + 1})">Next</button>`;
    
    paginationDiv.innerHTML = html;
}

// View user details
async function viewUser(userId) {
    const modal = document.getElementById('user-modal');
    const detailsDiv = document.getElementById('user-details');
    
    modal.classList.add('show');
    detailsDiv.innerHTML = '<p class="loading">Loading...</p>';
    
    try {
        const response = await fetch(`/api/users/${userId}`);
        const user = await response.json();
        
        if (user.error) {
            detailsDiv.innerHTML = `<p class="no-data">${user.error}</p>`;
            return;
        }
        
        let html = '<div class="user-detail-grid">';
        
        // Basic info
        html += createDetailItem('User ID', user.user_id);
        html += createDetailItem('Username', user.username || 'N/A');
        html += createDetailItem('First Name', user.first_name || 'N/A');
        html += createDetailItem('Last Name', user.last_name || 'N/A');
        html += createDetailItem('Language Code', user.language_code || 'N/A');
        html += createDetailItem('Is Bot', user.is_bot !== null ? (user.is_bot ? 'Yes' : 'No') : 'N/A');
        html += createDetailItem('Is Premium', user.is_premium !== null ? (user.is_premium ? 'Yes ⭐' : 'No') : 'N/A');
        html += createDetailItem('Gender', user.gender || 'N/A');
        html += createDetailItem('Country', user.country || 'N/A');
        
        // Status
        html += createDetailItem('Current State', user.state || 'unknown');
        html += createDetailItem('In Queue', user.in_queue ? 'Yes' : 'No');
        html += createDetailItem('In Chat', user.in_chat ? 'Yes' : 'No');
        
        if (user.partner_id) {
            html += createDetailItem('Chat Partner ID', user.partner_id);
        }
        
        // Preferences
        if (user.preferences && Object.keys(user.preferences).length > 0) {
            html += createDetailItem('Preferences', JSON.stringify(user.preferences, null, 2), true);
        }
        
        html += '</div>';
        detailsDiv.innerHTML = html;
    } catch (error) {
        console.error('Error loading user details:', error);
        detailsDiv.innerHTML = '<p class="no-data">Error loading user details</p>';
    }
}

// Create detail item
function createDetailItem(label, value, isCode = false) {
    return `
        <div class="detail-item">
            <div class="detail-label">${label}</div>
            <div class="detail-value" ${isCode ? 'style="white-space: pre-wrap; font-family: monospace;"' : ''}>
                ${value}
            </div>
        </div>
    `;
}

// Close user modal
function closeUserModal() {
    document.getElementById('user-modal').classList.remove('show');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('user-modal');
    if (event.target === modal) {
        closeUserModal();
    }
}
