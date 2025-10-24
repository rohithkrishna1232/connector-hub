// Global JavaScript functions for Data Integration Platform

// API helper functions
const API = {
    get: function(url, callback) {
        $.get(url)
            .done(callback)
            .fail(function(xhr) {
                const response = xhr.responseJSON || { error: 'Request failed' };
                showAlert('Error: ' + response.error, 'danger');
            });
    },
    
    post: function(url, data, callback) {
        $.ajax({
            url: url,
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify(data)
        })
        .done(callback)
        .fail(function(xhr) {
            const response = xhr.responseJSON || { error: 'Request failed' };
            showAlert('Error: ' + response.error, 'danger');
        });
    },
    
    put: function(url, data, callback) {
        $.ajax({
            url: url,
            method: 'PUT',
            contentType: 'application/json',
            data: JSON.stringify(data)
        })
        .done(callback)
        .fail(function(xhr) {
            const response = xhr.responseJSON || { error: 'Request failed' };
            showAlert('Error: ' + response.error, 'danger');
        });
    },
    
    delete: function(url, callback) {
        $.ajax({
            url: url,
            method: 'DELETE'
        })
        .done(callback)
        .fail(function(xhr) {
            const response = xhr.responseJSON || { error: 'Request failed' };
            showAlert('Error: ' + response.error, 'danger');
        });
    }
};

// Utility functions
function showAlert(message, type = 'info', duration = 5000) {
    const alertId = 'alert-' + Date.now();
    const alert = `
        <div id="${alertId}" class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;
    
    // Remove existing alerts
    $('.alert').alert('close');
    
    // Add new alert
    $('main .container').prepend(alert);
    
    // Auto-dismiss after duration
    if (duration > 0) {
        setTimeout(function() {
            $('#' + alertId).alert('close');
        }, duration);
    }
}

function showLoading(element) {
    const $element = $(element);
    $element.addClass('loading');
    
    if ($element.is('button')) {
        const originalText = $element.html();
        $element.data('original-text', originalText);
        $element.html('<span class="spinner-border spinner-border-sm me-2"></span>Loading...');
        $element.prop('disabled', true);
    }
}

function hideLoading(element) {
    const $element = $(element);
    $element.removeClass('loading');
    
    if ($element.is('button')) {
        const originalText = $element.data('original-text');
        if (originalText) {
            $element.html(originalText);
        }
        $element.prop('disabled', false);
    }
}

function formatDateTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleString();
}

function formatDate(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleDateString();
}

function formatTime(dateString) {
    if (!dateString) return '-';
    const date = new Date(dateString);
    return date.toLocaleTimeString();
}

function formatTimeAgo(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    if (diffInSeconds < 60) return 'Just now';
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)}d ago`;
    return date.toLocaleDateString();
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return new Intl.NumberFormat().format(num);
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function validateUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

function validateJSON(jsonString) {
    try {
        JSON.parse(jsonString);
        return true;
    } catch {
        return false;
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        showAlert('Copied to clipboard!', 'success', 2000);
    }).catch(function() {
        showAlert('Failed to copy to clipboard', 'warning');
    });
}

function downloadJSON(data, filename) {
    const jsonStr = JSON.stringify(data, null, 2);
    const blob = new Blob([jsonStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'data.json';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function downloadCSV(data, filename) {
    if (!data || data.length === 0) {
        showAlert('No data to download', 'warning');
        return;
    }
    
    const headers = Object.keys(data[0]);
    const csvContent = [
        headers.join(','),
        ...data.map(row => headers.map(header => {
            const value = row[header] || '';
            return typeof value === 'string' && value.includes(',') ? `"${value}"` : value;
        }).join(','))
    ].join('\n');
    
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = filename || 'data.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Status badge helper
function getStatusBadge(status) {
    const statusMap = {
        'active': 'bg-success',
        'inactive': 'bg-secondary',
        'pending': 'bg-warning',
        'running': 'bg-primary',
        'completed': 'bg-success',
        'failed': 'bg-danger',
        'cancelled': 'bg-secondary'
    };
    
    const badgeClass = statusMap[status] || 'bg-secondary';
    return `<span class="badge ${badgeClass}">${status.charAt(0).toUpperCase() + status.slice(1)}</span>`;
}

// Form validation helpers
function validateForm(formSelector) {
    const form = $(formSelector)[0];
    if (!form) return false;
    
    if (form.checkValidity()) {
        $(form).removeClass('was-validated');
        return true;
    } else {
        $(form).addClass('was-validated');
        return false;
    }
}

function clearForm(formSelector) {
    const form = $(formSelector);
    form[0].reset();
    form.removeClass('was-validated');
    form.find('.is-invalid').removeClass('is-invalid');
    form.find('.is-valid').removeClass('is-valid');
}

// Confirmation dialog
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// Initialize tooltips and popovers
$(document).ready(function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // Auto-dismiss alerts
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
});