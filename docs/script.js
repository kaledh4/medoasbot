// Dashboard Configuration
const DASHBOARD_CONFIG = {
    apiEndpoint: 'https://api.medoasbot.com/v1',
    updateInterval: 30000, // 30 seconds
    chartColors: {
        primary: '#3498db',
        secondary: '#e74c3c',
        success: '#27ae60',
        warning: '#e67e22'
    }
};

// Initialize dashboard
document.addEventListener('DOMContentLoaded', function() {
    console.log('Dashboard initializing...');
    
    // Initialize all dashboard components
    initializeStats();
    initializeRealTimeData();
    initializeDailyReports();
    initializeCronJobs();
    initializeChart();
    
    // Set up automatic updates
    setInterval(updateDashboard, DASHBOARD_CONFIG.updateInterval);
    
    // Initial data load
    updateDashboard();
});

// Initialize statistics
function initializeStats() {
    updateStat('active-campaigns', 0);
    updateStat('total-sources', 0);
    updateStat('daily-findings', 0);
}

// Update a statistic
function updateStat(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        element.textContent = value.toLocaleString();
    }
}

// Initialize real-time data section
function initializeRealTimeData() {
    const dataCollectionList = document.getElementById('data-collection-status');
    const aiAnalysisList = document.getElementById('ai-analysis-status');
    
    if (dataCollectionList) {
        dataCollectionList.innerHTML = `
            <li>Loading social media data...</li>
            <li>Processing news sources...</li>
            <li>Analyzing dark web forums...</li>
        `;
    }
    
    if (aiAnalysisList) {
        aiAnalysisList.innerHTML = `
            <li>Natural language processing...</li>
            <li>Pattern recognition...</li>
            <li>Sentiment analysis...</li>
        `;
    }
}

// Initialize daily reports
function initializeDailyReports() {
    const dailySummary = document.getElementById('daily-summary');
    const criticalFindings = document.getElementById('critical-findings');
    const dataDistribution = document.getElementById('data-distribution');
    
    if (dailySummary) {
        dailySummary.innerHTML = `
            <div class='report-item'>
                <strong>Total Campaigns:</strong> 12 new campaigns detected</div>
            <div class='report-item'>
                <strong>Key Findings:</strong> Increased activity in Eastern Europe</div>
            <div class='report-item'>
                <strong>Top Source:</strong> Twitter (45% of activity)</div>
        `;
    }
    
    if (criticalFindings) {
        criticalFindings.innerHTML = `
            <div class='alert alert-danger'>
                <strong>URGENT:</strong> Coordinated disinformation campaign targeting election</div>
            <div class='alert alert-warning>
                <strong>HIGH PRIORITY:</strong> Bot network amplification detected</div>
        `;
    }
    
    if (dataDistribution) {
        dataDistribution.innerHTML = `
            <div class='chart-container'>
                <div class='chart-item'>
                    <strong>Social Media:</strong> 45%</div>
                <div class='chart-item'>
                    <strong>News Sources:</strong> 30%</div>
                <div class='chart-item'>
                    <strong>Dark Web:</strong> 15%</div>
                <div class='chart-item'>
                    <strong>Other:</strong> 10%</div>
            </div>
        `;
    }
}

// Initialize cron jobs
function initializeCronJobs() {
    updateJobStatus('job-data-collection', 'status-pending', 'Collecting data...');
    updateJobStatus('job-ai-analysis', 'status-pending', 'Analyzing data...');
    updateJobStatus('job-report-gen', 'status-pending', 'Generating report...');
}

// Update job status
function updateJobStatus(elementId, statusClass, message) {
    const element = document.getElementById(elementId);
    if (element) {
        element.className = statusClass;
        element.textContent = message;
    }
}

// Initialize chart
function initializeChart() {
    // Simple chart placeholder
    const chartContainer = document.getElementById('trend-chart');
    if (chartContainer) {
        chartContainer.innerHTML = `
            <canvas id='campaign-trends' width='300' height='150'></canvas>
        `;
        drawSimpleChart();
    }
}

// Draw simple chart
function drawSimpleChart() {
    const canvas = document.getElementById('campaign-trends');
    if (!canvas || !canvas.getContext) return;
    
    const ctx = canvas.getContext('2d');
    const width = canvas.width;
    const height = canvas.height;
    
    // Clear canvas
    ctx.clearRect(0, 0, width, height);
    
    // Draw simple line chart
    const data = [10, 15, 8, 20, 18, 25, 22];
    const max = Math.max(...data);
    const stepX = width / (data.length - 1);
    const stepY = height / max;
    
    ctx.strokeStyle = DASHBOARD_CONFIG.chartColors.primary;
    ctx.lineWidth = 2;
    ctx.beginPath();
    
    data.forEach((value, index) => {
        const x = index * stepX;
        const y = height - (value * stepY);
        
        if (index === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    
    ctx.stroke();
    
    // Draw points
    ctx.fillStyle = DASHBOARD_CONFIG.chartColors.primary;
    data.forEach((value, index) => {
        const x = index * stepX;
        const y = height - (value * stepY);
        
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, 2 * Math.PI);
        ctx.fill();
    });
}

// Update dashboard with new data
function updateDashboard() {
    console.log('Updating dashboard...');
    
    // Update statistics
    updateStat('active-campaigns', Math.floor(Math.random() * 20) + 5);
    updateStat('total-sources', Math.floor(Math.random() * 100) + 50);
    updateStat('daily-findings', Math.floor(Math.random() * 50) + 10);
    
    // Update real-time data
    updateRealTimeData();
    
    // Update cron jobs
    updateCronJobs();
    
    // Update last updated time
    updateLastUpdated();
    
    // Redraw chart
    drawSimpleChart();
}

// Update real-time data
function updateRealTimeData() {
    const dataCollectionList = document.getElementById('data-collection-status');
    const aiAnalysisList = document.getElementById('ai-analysis-status');
    
    if (dataCollectionList) {
        dataCollectionList.innerHTML = `
            <li>Social media: ${Math.floor(Math.random() * 1000) + 500} new posts</li>
            <li>News sources: ${Math.floor(Math.random() * 200) + 100} articles</li>
            <li>Dark web: ${Math.floor(Math.random() * 50) + 20} forum posts</li>
        `;
    }
    
    if (aiAnalysisList) {
        aiAnalysisList.innerHTML = `
            <li>NLP models: ${Math.floor(Math.random() * 1000) + 500} tokens processed</li>
            <li>Pattern matching: ${Math.floor(Math.random() * 100) + 50} patterns identified</li>
            <li>Sentiment: ${Math.floor(Math.random() * 100)}% negative sentiment detected</li>
        `;
    }
}

// Update cron jobs
function updateCronJobs() {
    const jobs = [
        {
            id: 'job-data-collection',
            name: 'Data Collection',
            status: Math.random() > 0.2 ? 'status-active' : 'status-error',
            message: Math.random() > 0.2 ? 'Completed successfully' : 'Error occurred'
        },
        {
            id: 'job-ai-analysis',
            name: 'AI Analysis',
            status: Math.random() > 0.2 ? 'status-active' : 'status-pending',
            message: Math.random() > 0.2 ? 'Analysis complete' : 'Analyzing...'
        },
        {
            id: 'job-report-gen',
            name: 'Report Generation',
            status: Math.random() > 0.3 ? 'status-active' : 'status-pending',
            message: Math.random() > 0.3 ? 'Report generated' : 'Generating...'
        }
    ];
    
    jobs.forEach(job > {
        updateJobStatus(job.id, job.status, job.message);
    });
}

// Update last updated time
function updateLastUpdated() {
    const element = document.getElementById('last-updated');
    if (element) {
        const now = new Date();
        element.textContent = now.toLocaleTimeString();
    }
}

// Handle refresh button click
function handleRefresh() {
    console.log('Manual refresh triggered...');
    updateDashboard();
}

// Export functions for external use
document.updateDashboard = updateDashboard;
document.handleRefresh = handleRefresh;
