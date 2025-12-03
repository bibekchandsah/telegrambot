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
        case 'reports':
            loadAllReports();
            loadReportStats();
            loadBlockedMedia();
            loadBadWords();
            loadModerationLogs();
            break;
        case 'bot-settings':
            loadBotSettings();
            break;
        case 'matching-control':
            loadMatchingSettings();
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
        html += '<div style="grid-column: 1 / -1; margin-bottom: 15px;"><h3 style="margin: 0;">👤 Basic Information</h3></div>';
        html += createDetailItem('User ID', user.user_id);
        html += createDetailItem('Username', user.username || 'N/A');
        html += createDetailItem('First Name', user.first_name || 'N/A');
        html += createDetailItem('Last Name', user.last_name || 'N/A');
        html += createDetailItem('Language Code', user.language_code || 'N/A');
        html += createDetailItem('Is Bot', user.is_bot !== null ? (user.is_bot ? 'Yes' : 'No') : 'N/A');
        html += createDetailItem('Is Premium', user.is_premium !== null ? (user.is_premium ? 'Yes ⭐' : 'No') : 'N/A');
        html += createDetailItem('Gender', user.gender || 'N/A');
        html += createDetailItem('Country', user.country || 'N/A');
        
        // Activity & Statistics
        html += '<div style="grid-column: 1 / -1; margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0;"><h3 style="margin: 0 0 15px 0;">📊 Activity & Statistics</h3></div>';
        
        // Format timestamps
        const formatDate = (timestamp) => {
            if (!timestamp) return 'N/A';
            const date = new Date(timestamp * 1000);
            return date.toLocaleString();
        };
        
        html += createDetailItem('Account Created', formatDate(user.account_created_at));
        html += createDetailItem('Last Activity', formatDate(user.last_activity_at));
        html += createDetailItem('Total Messages Sent', user.message_count !== undefined ? user.message_count : 'N/A');
        html += createDetailItem('Total Chats Completed', user.chat_count !== undefined ? user.chat_count : 'N/A');
        
        // Format rating with emoji
        let ratingDisplay = 'N/A';
        if (user.rating_score !== undefined) {
            const score = user.rating_score;
            let emoji = '😐';
            let status = 'Neutral';
            
            if (score >= 80) {
                emoji = '🌟';
                status = 'Excellent';
            } else if (score >= 60) {
                emoji = '😊';
                status = 'Good';
            } else if (score >= 40) {
                emoji = '😐';
                status = 'Neutral';
            } else {
                emoji = '😔';
                status = 'Needs Improvement';
            }
            
            ratingDisplay = `${emoji} ${status} - ${score.toFixed(1)}% (👍 ${user.positive_ratings} | 👎 ${user.negative_ratings} | Total Chats: ${user.total_chats})`;
        }
        
        html += createDetailItem('Rating', ratingDisplay);
        
        // Chat & Queue Statistics Section Header
        html += '<div style="grid-column: 1 / -1; margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0;"><h3 style="margin: 0 0 15px 0;">⏱️ Chat & Queue Statistics</h3></div>';
        
        // Format time durations
        const formatDuration = (seconds) => {
            if (!seconds) return '0s';
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const secs = seconds % 60;
            
            if (hours > 0) {
                return `${hours}h ${minutes}m ${secs}s`;
            } else if (minutes > 0) {
                return `${minutes}m ${secs}s`;
            } else {
                return `${secs}s`;
            }
        };
        
        html += createDetailItem('Average Chat Duration', formatDuration(user.avg_chat_duration || 0));
        html += createDetailItem('Total Time in Chat', formatDuration(user.total_chat_time || 0));
        html += createDetailItem('Average Queue Wait Time', formatDuration(user.avg_queue_time || 0));
        html += createDetailItem('Total Queue Time', formatDuration(user.total_queue_time || 0));
        
        // Skip Rate Section Header
        html += '<div style="grid-column: 1 / -1; margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0;"><h3 style="margin: 0 0 15px 0;">⏭️ Skip Rate</h3></div>';
        
        html += createDetailItem('Skip Count (/next)', user.skip_count !== undefined ? user.skip_count : 'N/A');
        
        // Calculate skip rate
        if (user.total_chats > 0 && user.skip_count !== undefined) {
            const skipRate = ((user.skip_count / user.total_chats) * 100).toFixed(1);
            html += createDetailItem('Skip Rate', `${skipRate}%`);
        } else {
            html += createDetailItem('Skip Rate', 'N/A');
        }
        
        html += createDetailItem('Times Reported', user.report_count !== undefined ? user.report_count : '0');
        
        // Status
        html += '<div style="grid-column: 1 / -1; margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0;"><h3 style="margin: 0 0 15px 0;">📍 Current Status</h3></div>';
        html += createDetailItem('Current State', user.state || 'unknown');
        html += createDetailItem('In Queue', user.in_queue ? 'Yes' : 'No');
        html += createDetailItem('In Chat', user.in_chat ? 'Yes' : 'No');
        
        if (user.partner_id) {
            html += createDetailItem('Chat Partner ID', user.partner_id);
        }
        
        // Preferences
        if (user.preferences && Object.keys(user.preferences).length > 0) {
            html += '<div style="grid-column: 1 / -1; margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0;"><h3 style="margin: 0 0 15px 0;">⚙️ Preferences</h3></div>';
            html += createDetailItem('Preferences', JSON.stringify(user.preferences, null, 2), true);
        }
        
        // Report History Section
        if (user.recent_reports && user.recent_reports.length > 0) {
            html += '<div style="grid-column: 1 / -1; margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0;"><h3 style="margin: 0 0 15px 0;">🚨 Recent Report History</h3></div>';
            
            user.recent_reports.forEach((report, index) => {
                const reportDate = new Date(report.timestamp * 1000).toLocaleString();
                html += `
                    <div style="grid-column: 1 / -1; background-color: #fff3cd; padding: 10px; margin-bottom: 8px; border-radius: 5px; border-left: 4px solid #ffc107;">
                        <strong>Report #${index + 1}</strong><br>
                        <small>Reported by User ID: ${report.reporter_id}</small><br>
                        <small>Time: ${reportDate}</small>
                    </div>
                `;
            });
        } else if (user.report_count > 0) {
            html += '<div style="grid-column: 1 / -1; margin-top: 20px; padding-top: 20px; border-top: 2px solid #e0e0e0;"><h3 style="margin: 0 0 15px 0;">🚨 Report History</h3></div>';
            html += `<div style="grid-column: 1 / -1;"><p>User has been reported ${user.report_count} time(s), but detailed history is not available.</p></div>`;
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

// ===== MODERATION FUNCTIONS =====

// Ban user
async function banUser() {
    const userId = document.getElementById('ban-user-id').value.trim();
    const reason = document.getElementById('ban-reason').value;
    const duration = document.getElementById('ban-duration').value;
    
    if (!userId) {
        alert('Please enter a user ID');
        return;
    }
    
    if (!reason) {
        alert('Please select a ban reason');
        return;
    }
    
    if (!duration) {
        alert('Please select a ban duration');
        return;
    }
    
    if (!confirm(`Are you sure you want to ban user ${userId} for ${duration}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/moderation/ban', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: parseInt(userId),
                reason: reason,
                duration: duration
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'User banned successfully');
            // Clear form
            document.getElementById('ban-user-id').value = '';
            document.getElementById('ban-reason').value = '';
            document.getElementById('ban-duration').value = '';
            // Refresh banned users list
            loadBannedUsers();
        } else {
            alert('Error: ' + (data.message || 'Failed to ban user'));
        }
    } catch (error) {
        console.error('Error banning user:', error);
        alert('Error banning user. Please try again.');
    }
}

// Unban user
async function unbanUser() {
    const userId = document.getElementById('unban-user-id').value.trim();
    
    if (!userId) {
        alert('Please enter a user ID');
        return;
    }
    
    if (!confirm(`Are you sure you want to unban user ${userId}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/moderation/unban', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: parseInt(userId)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'User unbanned successfully');
            // Clear form
            document.getElementById('unban-user-id').value = '';
            // Refresh banned users list
            loadBannedUsers();
        } else {
            alert('Error: ' + (data.message || 'Failed to unban user'));
        }
    } catch (error) {
        console.error('Error unbanning user:', error);
        alert('Error unbanning user. Please try again.');
    }
}

// Warn user
async function warnUser() {
    const userId = document.getElementById('warn-user-id').value.trim();
    const reason = document.getElementById('warn-reason').value.trim();
    
    if (!userId) {
        alert('Please enter a user ID');
        return;
    }
    
    if (!reason) {
        alert('Please enter a warning reason');
        return;
    }
    
    if (!confirm(`Are you sure you want to warn user ${userId}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/moderation/warn', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: parseInt(userId),
                reason: reason
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'Warning issued successfully');
            // Clear form
            document.getElementById('warn-user-id').value = '';
            document.getElementById('warn-reason').value = '';
            // Refresh warned users list
            loadWarnedUsers();
        } else {
            alert('Error: ' + (data.message || 'Failed to warn user'));
        }
    } catch (error) {
        console.error('Error warning user:', error);
        alert('Error warning user. Please try again.');
    }
}

// Check ban status
async function checkBanStatus() {
    const userId = document.getElementById('check-ban-user-id').value.trim();
    const resultDiv = document.getElementById('ban-status-result');
    
    if (!userId) {
        alert('Please enter a user ID');
        return;
    }
    
    resultDiv.innerHTML = '<p class="loading">Checking...</p>';
    
    try {
        const response = await fetch(`/api/moderation/check-ban/${userId}`);
        const data = await response.json();
        
        if (data.is_banned) {
            const expiresText = data.expires_at === 'permanent' 
                ? 'Permanent ban' 
                : `Expires: ${new Date(data.expires_at * 1000).toLocaleString()}`;
            
            resultDiv.innerHTML = `
                <div style="background-color: #f8d7da; padding: 15px; border-radius: 5px; border-left: 4px solid #dc3545;">
                    <h4 style="margin: 0 0 10px 0; color: #721c24;">🚫 User is Banned</h4>
                    <p><strong>User ID:</strong> ${data.user_id}</p>
                    <p><strong>Reason:</strong> ${data.reason}</p>
                    <p><strong>Duration:</strong> ${data.duration}</p>
                    <p><strong>Banned At:</strong> ${new Date(data.banned_at * 1000).toLocaleString()}</p>
                    <p><strong>${expiresText}</strong></p>
                    <p><strong>Banned By:</strong> ${data.banned_by}</p>
                    ${data.is_auto_ban ? '<p><strong>⚠️ Auto-banned due to reports</strong></p>' : ''}
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div style="background-color: #d4edda; padding: 15px; border-radius: 5px; border-left: 4px solid #28a745;">
                    <h4 style="margin: 0 0 10px 0; color: #155724;">✅ User is Not Banned</h4>
                    <p>User ID ${userId} is not currently banned.</p>
                </div>
            `;
        }
    } catch (error) {
        console.error('Error checking ban status:', error);
        resultDiv.innerHTML = `
            <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                <p>Error checking ban status. Please try again.</p>
            </div>
        `;
    }
}

// Load banned users
async function loadBannedUsers() {
    const tbody = document.getElementById('banned-users-table');
    tbody.innerHTML = '<tr><td colspan="7" class="loading">Loading...</td></tr>';
    
    try {
        const response = await fetch('/api/moderation/banned-users');
        const data = await response.json();
        
        if (data.banned_users && data.banned_users.length > 0) {
            tbody.innerHTML = data.banned_users.map(ban => {
                const bannedAt = new Date(ban.banned_at * 1000).toLocaleString();
                const expiresAt = ban.expires_at === 'permanent' 
                    ? 'Permanent' 
                    : new Date(ban.expires_at * 1000).toLocaleString();
                
                return `
                    <tr>
                        <td>${ban.user_id}</td>
                        <td>${ban.reason}</td>
                        <td>${ban.duration}</td>
                        <td>${bannedAt}</td>
                        <td>${expiresAt}</td>
                        <td>${ban.banned_by}</td>
                        <td>
                            <button class="btn btn-success btn-small" onclick="quickUnban(${ban.user_id})">
                                Unban
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="7" class="no-data">No banned users</td></tr>';
        }
    } catch (error) {
        console.error('Error loading banned users:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="no-data">Error loading banned users</td></tr>';
    }
}

// Load warned users
async function loadWarnedUsers() {
    const tbody = document.getElementById('warned-users-table');
    tbody.innerHTML = '<tr><td colspan="3" class="loading">Loading...</td></tr>';
    
    try {
        const response = await fetch('/api/moderation/warned-users');
        const data = await response.json();
        
        if (data.warned_users && data.warned_users.length > 0) {
            tbody.innerHTML = data.warned_users.map(user => {
                return `
                    <tr>
                        <td>${user.user_id}</td>
                        <td>${user.warning_count}</td>
                        <td>
                            <button class="btn btn-primary btn-small" onclick="viewUser(${user.user_id})">
                                View Details
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="3" class="no-data">No warned users</td></tr>';
        }
    } catch (error) {
        console.error('Error loading warned users:', error);
        tbody.innerHTML = '<tr><td colspan="3" class="no-data">Error loading warned users</td></tr>';
    }
}

// Quick unban from banned users list
async function quickUnban(userId) {
    if (!confirm(`Are you sure you want to unban user ${userId}?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/moderation/unban', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                user_id: userId
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'User unbanned successfully');
            loadBannedUsers();
        } else {
            alert('Error: ' + (data.message || 'Failed to unban user'));
        }
    } catch (error) {
        console.error('Error unbanning user:', error);
        alert('Error unbanning user. Please try again.');
    }
}

// ========== Reports & Safety Management Functions ==========

// Store all reports for filtering
let allReportsData = [];

// Load all reports
async function loadAllReports() {
    const tbody = document.getElementById('reports-table');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading reports...</td></tr>';
    
    try {
        const response = await fetch('/api/reports/all');
        const data = await response.json();
        
        if (data.success && data.reports) {
            // Flatten reports into individual rows
            allReportsData = [];
            
            data.reports.forEach(reportGroup => {
                if (reportGroup.reports && reportGroup.reports.length > 0) {
                    reportGroup.reports.forEach(individualReport => {
                        allReportsData.push({
                            reported_user_id: reportGroup.user_id,
                            reporter_id: individualReport.reporter_id,
                            flag: individualReport.flag,
                            timestamp: individualReport.timestamp,
                            status: 'pending', // Default to pending, will be updated below
                            report_count: reportGroup.report_count
                        });
                    });
                }
            });
            
            // Fetch all individual statuses in one call
            if (allReportsData.length > 0) {
                const statusResponse = await fetch('/api/reports/all-individual-statuses', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        reports: allReportsData.map(r => ({
                            reported_user_id: r.reported_user_id,
                            reporter_id: r.reporter_id,
                            timestamp: r.timestamp
                        }))
                    })
                });
                
                if (statusResponse.ok) {
                    const statusData = await statusResponse.json();
                    if (statusData.success && statusData.statuses) {
                        // Update statuses
                        statusData.statuses.forEach(statusInfo => {
                            const report = allReportsData.find(r =>
                                r.reported_user_id == statusInfo.reported_user_id &&
                                r.reporter_id == statusInfo.reporter_id &&
                                r.timestamp == statusInfo.timestamp
                            );
                            if (report) {
                                report.status = statusInfo.status;
                            }
                        });
                    }
                }
            }
            
            // Apply filters and display
            applyReportFilters();
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">Failed to load reports</td></tr>';
            allReportsData = [];
        }
        
        // Also load stats
        loadReportStats();
    } catch (error) {
        console.error('Error loading reports:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">Error loading reports</td></tr>';
        allReportsData = [];
    }
}

// Apply filters to reports
function applyReportFilters() {
    const tbody = document.getElementById('reports-table');
    const statusFilter = document.getElementById('filter-status').value;
    const flagFilter = document.getElementById('filter-flag').value;
    const userIdFilter = document.getElementById('filter-userid').value.trim().toLowerCase();
    
    // Filter reports
    let filteredReports = allReportsData.filter(report => {
        // Status filter
        if (statusFilter !== 'all' && report.status !== statusFilter) {
            return false;
        }
        
        // Flag type filter
        if (flagFilter !== 'all' && report.flag !== flagFilter) {
            return false;
        }
        
        // User ID filter
        if (userIdFilter && !report.reported_user_id.toString().includes(userIdFilter)) {
            return false;
        }
        
        return true;
    });
    
    // Sort by timestamp (newest first)
    filteredReports.sort((a, b) => b.timestamp - a.timestamp);
    
    if (filteredReports.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">No reports match the filters</td></tr>';
        return;
    }
    
    // Display filtered reports
    tbody.innerHTML = '';
    filteredReports.forEach(report => {
        const row = document.createElement('tr');
        
        // Format flag with badge
        const flagNames = {
            'nudity': '🔞 Nudity',
            'harassment': '😠 Harassment',
            'spam': '📢 Spam',
            'scam': '💰 Scam',
            'fake': '🎭 Fake Profile',
            'other': '❓ Other'
        };
        
        const flagBadgeClass = {
            'nudity': 'flag-nudity',
            'harassment': 'flag-harassment',
            'spam': 'flag-spam',
            'scam': 'flag-scam',
            'fake': 'flag-fake',
            'other': 'flag-other'
        };
        
        const flagDisplay = `<span class="flag-badge ${flagBadgeClass[report.flag]}">${flagNames[report.flag]}</span>`;
        const dateDisplay = new Date(report.timestamp * 1000).toLocaleString();
        
        row.innerHTML = `
            <td><strong>${report.reported_user_id}</strong></td>
            <td>${report.reporter_id}</td>
            <td>${flagDisplay}</td>
            <td>${dateDisplay}</td>
            <td><span class="status-badge ${report.status === 'approved' ? 'status-approved' : report.status === 'rejected' ? 'status-rejected' : 'status-pending'}">${report.status || 'pending'}</span></td>
            <td>
                <button class="btn-success" onclick="approveIndividualReport('${report.reported_user_id}', '${report.reporter_id}', ${report.timestamp})" ${report.status === 'approved' ? 'disabled' : ''}>✓ Approve</button>
                <button class="btn-danger" onclick="rejectIndividualReport('${report.reported_user_id}', '${report.reporter_id}', ${report.timestamp})" ${report.status === 'rejected' ? 'disabled' : ''}>✗ Reject</button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

// Clear all filters
function clearReportFilters() {
    document.getElementById('filter-status').value = 'pending';
    document.getElementById('filter-flag').value = 'all';
    document.getElementById('filter-userid').value = '';
    applyReportFilters();
}

// Approve individual report
async function approveIndividualReport(reportedUserId, reporterId, timestamp) {
    const report = allReportsData.find(r => 
        r.reported_user_id == reportedUserId && 
        r.reporter_id == reporterId && 
        r.timestamp == timestamp
    );
    
    let confirmMsg = `Approve this report?\n\nReported User: ${reportedUserId}\nReporter: ${reporterId}`;
    if (report && report.status === 'rejected') {
        confirmMsg = `Change status from REJECTED to APPROVED?\n\nReported User: ${reportedUserId}\nReporter: ${reporterId}`;
    }
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    try {
        const response = await fetch('/api/reports/approve-individual', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reported_user_id: reportedUserId,
                reporter_id: reporterId,
                timestamp: timestamp,
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update the specific report status in memory
            if (report) {
                report.status = 'approved';
            }
            
            // Reload stats to update counts
            loadReportStats();
            
            // Re-apply filters to update display
            applyReportFilters();
        } else {
            alert('Error: ' + (data.message || 'Failed to approve report'));
        }
    } catch (error) {
        console.error('Error approving report:', error);
        alert('Error approving report. Please try again.');
    }
}

// Reject individual report
async function rejectIndividualReport(reportedUserId, reporterId, timestamp) {
    const report = allReportsData.find(r => 
        r.reported_user_id == reportedUserId && 
        r.reporter_id == reporterId && 
        r.timestamp == timestamp
    );
    
    let confirmMsg = `Reject this report?\n\nReported User: ${reportedUserId}\nReporter: ${reporterId}`;
    if (report && report.status === 'approved') {
        confirmMsg = `Change status from APPROVED to REJECTED?\n\nReported User: ${reportedUserId}\nReporter: ${reporterId}`;
    }
    
    if (!confirm(confirmMsg)) {
        return;
    }
    
    try {
        const response = await fetch('/api/reports/reject-individual', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reported_user_id: reportedUserId,
                reporter_id: reporterId,
                timestamp: timestamp,
                admin_id: 'admin',
                reason: 'Invalid report'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update the specific report status in memory
            if (report) {
                report.status = 'rejected';
            }
            
            // Reload stats to update counts
            loadReportStats();
            
            // Re-apply filters to update display
            applyReportFilters();
        } else {
            alert('Error: ' + (data.message || 'Failed to reject report'));
        }
    } catch (error) {
        console.error('Error rejecting report:', error);
        alert('Error rejecting report. Please try again.');
    }
}

// Load report statistics
async function loadReportStats() {
    try {
        const response = await fetch('/api/reports/stats');
        const data = await response.json();
        
        if (data.success && data.stats) {
            document.getElementById('total-reports-count').textContent = data.stats.total_reports || 0;
            document.getElementById('reported-users-count').textContent = data.stats.reported_users || 0;
            document.getElementById('pending-reports-count').textContent = data.stats.pending_reports || 0;
            
            // Frozen users count will be updated by loadFrozenUsers
        }
    } catch (error) {
        console.error('Error loading report stats:', error);
    }
}

// Load blocked media types
async function loadBlockedMedia() {
    const tbody = document.getElementById('blocked-media-table');
    tbody.innerHTML = '<tr><td colspan="6" class="loading">Loading blocked media...</td></tr>';
    
    try {
        const response = await fetch('/api/safety/blocked-media');
        const data = await response.json();
        
        if (data.blocked_media) {
            if (data.blocked_media.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="no-data">No blocked media types</td></tr>';
                return;
            }
            
            tbody.innerHTML = '';
            data.blocked_media.forEach(media => {
                const row = document.createElement('tr');
                const blockedAt = new Date(media.blocked_at * 1000).toLocaleString();
                const expiresAt = media.expires_at ? new Date(media.expires_at * 1000).toLocaleString() : 'Never';
                
                // Calculate duration display
                let duration = 'Permanent';
                if (media.expires_at && media.blocked_at) {
                    const durationSeconds = media.expires_at - media.blocked_at;
                    if (durationSeconds === 3600) duration = '1 Hour';
                    else if (durationSeconds === 21600) duration = '6 Hours';
                    else if (durationSeconds === 86400) duration = '24 Hours';
                    else if (durationSeconds === 604800) duration = '7 Days';
                    else if (durationSeconds === 2592000) duration = '30 Days';
                    else {
                        // Format custom duration
                        const hours = Math.floor(durationSeconds / 3600);
                        const days = Math.floor(durationSeconds / 86400);
                        if (days > 0) duration = `${days} Day${days > 1 ? 's' : ''}`;
                        else if (hours > 0) duration = `${hours} Hour${hours > 1 ? 's' : ''}`;
                        else duration = `${durationSeconds} Seconds`;
                    }
                }
                
                // Media type icons
                const icons = {
                    photo: '📷',
                    video: '🎥',
                    voice: '🎤',
                    sticker: '😊',
                    gif: '🎞️',
                    document: '📄'
                };
                const icon = icons[media.media_type] || '📎';
                
                row.innerHTML = `
                    <td>${icon} ${media.media_type}</td>
                    <td>${blockedAt}</td>
                    <td>${media.reason || 'No reason provided'}</td>
                    <td>${duration}</td>
                    <td>${expiresAt}</td>
                    <td><button class="btn-primary" onclick="unblockMedia('${media.media_type}')">✓ Unblock</button></td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="6" class="no-data">Failed to load blocked media</td></tr>';
        }
    } catch (error) {
        console.error('Error loading blocked media:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="no-data">Error loading blocked media</td></tr>';
    }
}

// Block media type action
async function blockMediaAction() {
    const mediaTypeSelect = document.getElementById('block-media-type');
    const reasonInput = document.getElementById('block-media-reason');
    const durationSelect = document.getElementById('block-media-duration');
    
    const mediaType = mediaTypeSelect.value;
    const reason = reasonInput.value.trim();
    const duration = durationSelect.value;
    
    if (!mediaType) {
        alert('Please select a media type to block');
        return;
    }
    
    if (!reason) {
        alert('Please provide a reason for blocking');
        return;
    }
    
    if (!confirm(`Are you sure you want to BLOCK ${mediaType} media?\n\nReason: ${reason}\nDuration: ${duration || 'Permanent'}`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/safety/block-media', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                media_type: mediaType,
                reason: reason,
                duration: duration || 'permanent',
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'Media type blocked successfully');
            mediaTypeSelect.value = '';
            reasonInput.value = '';
            durationSelect.value = '';
            loadBlockedMedia();
        } else {
            alert('Error: ' + (data.message || 'Failed to block media'));
        }
    } catch (error) {
        console.error('Error blocking media:', error);
        alert('Error blocking media. Please try again.');
    }
}

// Unblock media type
async function unblockMedia(mediaType) {
    if (!confirm(`Are you sure you want to UNBLOCK ${mediaType} media?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/safety/unblock-media', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                media_type: mediaType,
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'Media type unblocked successfully');
            loadBlockedMedia();
        } else {
            alert('Error: ' + (data.message || 'Failed to unblock media'));
        }
    } catch (error) {
        console.error('Error unblocking media:', error);
        alert('Error unblocking media. Please try again.');
    }
}

// Load bad words
async function loadBadWords() {
    const container = document.getElementById('bad-words-container');
    container.innerHTML = '<p class="loading">Loading bad words...</p>';
    
    try {
        const response = await fetch('/api/safety/bad-words');
        const data = await response.json();
        
        if (data.bad_words) {
            if (data.bad_words.length === 0) {
                container.innerHTML = '<p class="no-data">No bad words in filter</p>';
                return;
            }
            
            container.innerHTML = '';
            data.bad_words.forEach(word => {
                const badge = document.createElement('div');
                badge.className = 'bad-word-badge';
                badge.innerHTML = `
                    ${word}
                    <button class="remove-btn" onclick="removeBadWord('${word.replace(/'/g, "\\'")}')">✕</button>
                `;
                container.appendChild(badge);
            });
        } else {
            container.innerHTML = '<p class="no-data">Failed to load bad words</p>';
        }
    } catch (error) {
        console.error('Error loading bad words:', error);
        container.innerHTML = '<p class="no-data">Error loading bad words</p>';
    }
}

// Add bad word action
async function addBadWordAction() {
    const input = document.getElementById('new-bad-word');
    const word = input.value.trim().toLowerCase();
    
    if (!word) {
        alert('Please enter a word or phrase to add');
        return;
    }
    
    if (!confirm(`Are you sure you want to add "${word}" to the bad word filter?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/safety/bad-words/add', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                word: word,
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'Bad word added successfully');
            input.value = '';
            loadBadWords();
        } else {
            alert('Error: ' + (data.message || 'Failed to add bad word'));
        }
    } catch (error) {
        console.error('Error adding bad word:', error);
        alert('Error adding bad word. Please try again.');
    }
}

// Remove bad word
async function removeBadWord(word) {
    if (!confirm(`Are you sure you want to remove "${word}" from the bad word filter?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/safety/bad-words/remove', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                word: word,
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert(data.message || 'Bad word removed successfully');
            loadBadWords();
        } else {
            alert('Error: ' + (data.message || 'Failed to remove bad word'));
        }
    } catch (error) {
        console.error('Error removing bad word:', error);
        alert('Error removing bad word. Please try again.');
    }
}

// Load moderation logs
async function loadModerationLogs() {
    const tbody = document.getElementById('moderation-logs-table');
    tbody.innerHTML = '<tr><td colspan="5" class="loading">Loading moderation logs...</td></tr>';
    
    try {
        const response = await fetch('/api/safety/moderation-logs');
        const data = await response.json();
        
        if (data.logs) {
            if (data.logs.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" class="no-data">No moderation logs</td></tr>';
                return;
            }
            
            tbody.innerHTML = '';
            // Show most recent logs first
            data.logs.reverse().forEach(log => {
                const row = document.createElement('tr');
                const timestamp = new Date(log.timestamp * 1000).toLocaleString();
                
                row.innerHTML = `
                    <td>${timestamp}</td>
                    <td>${log.admin_id}</td>
                    <td><span class="action-badge">${log.action}</span></td>
                    <td>${log.target_user || 'N/A'}</td>
                    <td style="font-size: 0.9em;">${log.details || 'No details'}</td>
                `;
                tbody.appendChild(row);
            });
        } else {
            tbody.innerHTML = '<tr><td colspan="5" class="no-data">Failed to load logs</td></tr>';
        }
    } catch (error) {
        console.error('Error loading moderation logs:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="no-data">Error loading logs</td></tr>';
    }
}

// ============================================
// BOT SETTINGS & CONFIGURATION
// ============================================

// Load bot settings
async function loadBotSettings() {
    try {
        const response = await fetch('/api/settings/bot');
        const data = await response.json();
        
        if (data.success && data.settings) {
            const settings = data.settings;
            
            // Populate message fields with current values or defaults
            document.getElementById('welcome-message').value = settings.welcome_message || settings.default_welcome || '';
            document.getElementById('match-found-message').value = settings.match_found_message || settings.default_match_found || '';
            document.getElementById('chat-end-message').value = settings.chat_end_message || settings.default_chat_end || '';
            document.getElementById('partner-left-message').value = settings.partner_left_message || settings.default_partner_left || '';
            document.getElementById('inactivity-duration').value = settings.inactivity_duration || 300;
            
            // Set mode checkboxes
            document.getElementById('maintenance-mode').checked = settings.maintenance_mode || false;
            document.getElementById('registrations-enabled').checked = settings.registrations_enabled !== false;
        }
    } catch (error) {
        console.error('Error loading bot settings:', error);
        alert('Error loading bot settings. Please try again.');
    }
}

// Save bot messages and inactivity duration
async function saveBotMessages() {
    const welcomeMessage = document.getElementById('welcome-message').value.trim();
    const matchFoundMessage = document.getElementById('match-found-message').value.trim();
    const chatEndMessage = document.getElementById('chat-end-message').value.trim();
    const partnerLeftMessage = document.getElementById('partner-left-message').value.trim();
    const inactivityDuration = parseInt(document.getElementById('inactivity-duration').value);
    
    if (inactivityDuration < 60) {
        alert('Inactivity duration must be at least 60 seconds');
        return;
    }
    
    if (!confirm('Are you sure you want to update the bot messages and inactivity duration?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/settings/bot/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                welcome_message: welcomeMessage || null,
                match_found_message: matchFoundMessage || null,
                chat_end_message: chatEndMessage || null,
                partner_left_message: partnerLeftMessage || null,
                inactivity_duration: inactivityDuration,
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Bot messages and settings updated successfully!\\n\\nUpdated: ' + data.updated.join(', '));
        } else {
            alert('Error: ' + (data.message || 'Failed to update settings'));
        }
    } catch (error) {
        console.error('Error saving bot messages:', error);
        alert('Error saving bot messages. Please try again.');
    }
}

// Save bot mode settings
async function saveBotModes() {
    const maintenanceMode = document.getElementById('maintenance-mode').checked;
    const registrationsEnabled = document.getElementById('registrations-enabled').checked;
    
    if (!confirm('Are you sure you want to update the bot mode settings?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/settings/bot/update', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                maintenance_mode: maintenanceMode,
                registrations_enabled: registrationsEnabled,
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ Bot mode settings updated successfully!\\n\\nUpdated: ' + data.updated.join(', '));
        } else {
            alert('Error: ' + (data.message || 'Failed to update settings'));
        }
    } catch (error) {
        console.error('Error saving bot modes:', error);
        alert('Error saving bot modes. Please try again.');
    }
}

// Force logout all users
async function forceLogoutAll() {
    if (!confirm('⚠️ WARNING: This will forcefully disconnect ALL active users and clear all chat sessions.\\n\\nAre you absolutely sure you want to do this?')) {
        return;
    }
    
    if (!confirm('This action cannot be undone. Confirm again to proceed.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/settings/actions/force-logout', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ ' + data.message);
            // Refresh statistics
            loadStatistics();
        } else {
            alert('Error: ' + (data.message || 'Failed to force logout users'));
        }
    } catch (error) {
        console.error('Error forcing logout:', error);
        alert('Error forcing logout. Please try again.');
    }
}

// Reset queue
async function resetQueue() {
    if (!confirm('⚠️ WARNING: This will remove ALL users from the matching queue.\\n\\nAre you absolutely sure you want to do this?')) {
        return;
    }
    
    if (!confirm('This action cannot be undone. Confirm again to proceed.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/settings/actions/reset-queue', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                admin_id: 'admin'
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ ' + data.message);
            // Refresh statistics
            loadStatistics();
        } else {
            alert('Error: ' + (data.message || 'Failed to reset queue'));
        }
    } catch (error) {
        console.error('Error resetting queue:', error);
        alert('Error resetting queue. Please try again.');
    }
}

// ============================================
// MATCHING CONTROL FUNCTIONS
// ============================================

async function loadMatchingSettings() {
    try {
        const response = await fetch('/api/matching/settings');
        const data = await response.json();
        
        if (data.success) {
            // Update toggles
            document.getElementById('gender-filter-enabled').checked = data.settings.gender_filter_enabled;
            document.getElementById('regional-filter-enabled').checked = data.settings.regional_filter_enabled;
            
            // Load queue size
            await loadQueueSize();
        } else {
            console.error('Failed to load matching settings:', data.error);
        }
    } catch (error) {
        console.error('Error loading matching settings:', error);
    }
}

async function updateMatchingFilters() {
    const genderEnabled = document.getElementById('gender-filter-enabled').checked;
    const regionalEnabled = document.getElementById('regional-filter-enabled').checked;
    
    try {
        const response = await fetch('/api/matching/settings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                admin_id: 'admin',
                gender_filter_enabled: genderEnabled,
                regional_filter_enabled: regionalEnabled
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showNotification('✅ Matching settings updated successfully', 'success');
        } else {
            alert('Error: ' + (data.message || 'Failed to update settings'));
            // Reload settings to revert UI
            loadMatchingSettings();
        }
    } catch (error) {
        console.error('Error updating matching filters:', error);
        alert('Error updating settings. Please try again.');
        loadMatchingSettings();
    }
}

async function loadQueueSize() {
    try {
        const response = await fetch('/api/matching/queue-size');
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('queue-size-display').textContent = data.queue_size;
            
            // Update timestamp
            const timestamp = new Date(data.timestamp);
            document.getElementById('queue-last-updated').textContent = timestamp.toLocaleTimeString();
        } else {
            document.getElementById('queue-size-display').textContent = 'Error';
            document.getElementById('queue-last-updated').textContent = '-';
        }
    } catch (error) {
        console.error('Error loading queue size:', error);
        document.getElementById('queue-size-display').textContent = 'Error';
        document.getElementById('queue-last-updated').textContent = '-';
    }
}

async function forceMatchUsers() {
    const user1 = document.getElementById('force-match-user1').value;
    const user2 = document.getElementById('force-match-user2').value;
    
    if (!user1 || !user2) {
        alert('Please enter both user IDs');
        return;
    }
    
    if (user1 === user2) {
        alert('Cannot match a user with themselves');
        return;
    }
    
    if (!confirm(`⚠️ WARNING: Force Match (Debug Feature)\\n\\nThis will forcefully match:\\nUser ${user1} ←→ User ${user2}\\n\\nThis bypasses all filters and queue logic.\\nAre you sure?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/matching/force-match', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                admin_id: 'admin',
                user1_id: parseInt(user1),
                user2_id: parseInt(user2)
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            alert('✅ ' + data.message);
            // Clear inputs
            document.getElementById('force-match-user1').value = '';
            document.getElementById('force-match-user2').value = '';
            // Refresh statistics
            loadStats();
            loadQueueSize();
        } else {
            alert('Error: ' + (data.error || data.message || 'Failed to force match'));
        }
    } catch (error) {
        console.error('Error forcing match:', error);
        alert('Error forcing match. Please try again.');
    }
}

function showNotification(message, type = 'info') {
    // Simple notification - you can enhance this with better UI
    const alertClass = type === 'success' ? 'success' : type === 'error' ? 'danger' : 'info';
    console.log(`[${type.toUpperCase()}] ${message}`);
}


