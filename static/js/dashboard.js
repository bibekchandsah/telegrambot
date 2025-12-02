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
