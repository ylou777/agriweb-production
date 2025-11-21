// Dashboard CRM - Statistiques et KPI
let charts = {};

document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
    
    // Refresh toutes les 30 secondes
    setInterval(loadDashboardData, 30000);
    
    // Event listener pour le filtre de période utilisateur
    document.getElementById('user-period')?.addEventListener('change', loadUserStats);
});

async function loadDashboardData() {
    try {
        const response = await fetch('/api/crm/dashboard/stats');
        const data = await response.json();
        
        if (data.success) {
            updateKPIs(data.kpis);
            updateCharts(data.charts);
            updateConversionFunnel(data.conversion);
            updateUserStats(data.users);
            updatePerformance(data.performance);
            updateDepartments(data.departments);
        }
    } catch (error) {
        console.error('Erreur chargement dashboard:', error);
    }
}

function updateKPIs(kpis) {
    // KPI Totaux
    document.getElementById('kpi-total').textContent = kpis.total || 0;
    document.getElementById('kpi-total-trend').textContent = kpis.nouveaux_mois || 0;
    
    document.getElementById('kpi-contactes').textContent = kpis.contactes || 0;
    document.getElementById('kpi-contactes-pct').textContent = 
        kpis.total > 0 ? ((kpis.contactes / kpis.total) * 100).toFixed(1) : 0;
    
    document.getElementById('kpi-qualifies').textContent = kpis.qualifies || 0;
    document.getElementById('kpi-qualifies-pct').textContent = 
        kpis.total > 0 ? ((kpis.qualifies / kpis.total) * 100).toFixed(1) : 0;
    
    document.getElementById('kpi-proposals').textContent = kpis.nb_proposals || 0;
    document.getElementById('kpi-proposals-value').textContent = 
        (kpis.total_proposals_value || 0).toLocaleString('fr-FR');
}

function updateCharts(chartData) {
    // Chart par Type
    const typeCtx = document.getElementById('typeChart');
    if (typeCtx) {
        if (charts.type) charts.type.destroy();
        charts.type = new Chart(typeCtx, {
            type: 'doughnut',
            data: {
                labels: Object.keys(chartData.by_type || {}),
                datasets: [{
                    data: Object.values(chartData.by_type || {}),
                    backgroundColor: ['#4CAF50', '#2196F3', '#FF9800', '#8BC34A']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
    
    // Chart par Statut
    const statutCtx = document.getElementById('statutChart');
    if (statutCtx) {
        if (charts.statut) charts.statut.destroy();
        charts.statut = new Chart(statutCtx, {
            type: 'pie',
            data: {
                labels: Object.keys(chartData.by_statut || {}),
                datasets: [{
                    data: Object.values(chartData.by_statut || {}),
                    backgroundColor: ['#9C27B0', '#2196F3', '#4CAF50', '#F44336']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'bottom' }
                }
            }
        });
    }
    
    // Timeline Chart
    const timelineCtx = document.getElementById('timelineChart');
    if (timelineCtx && chartData.timeline) {
        if (charts.timeline) charts.timeline.destroy();
        charts.timeline = new Chart(timelineCtx, {
            type: 'line',
            data: {
                labels: chartData.timeline.labels || [],
                datasets: [
                    {
                        label: 'Nouveaux',
                        data: chartData.timeline.nouveaux || [],
                        borderColor: '#9C27B0',
                        backgroundColor: 'rgba(156, 39, 176, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Contactés',
                        data: chartData.timeline.contactes || [],
                        borderColor: '#2196F3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        tension: 0.4
                    },
                    {
                        label: 'Qualifiés',
                        data: chartData.timeline.qualifies || [],
                        borderColor: '#4CAF50',
                        backgroundColor: 'rgba(76, 175, 80, 0.1)',
                        tension: 0.4
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}

function updateConversionFunnel(conversion) {
    const total = conversion.total || 1;
    
    // Nouveaux
    document.getElementById('funnel-nouveaux-count').textContent = `${conversion.nouveaux || 0} prospects`;
    document.getElementById('funnel-nouveaux-pct').textContent = '100%';
    document.getElementById('funnel-nouveaux-bar').style.width = '100%';
    
    // Contactés
    const contactesPct = total > 0 ? (conversion.contactes / total * 100) : 0;
    document.getElementById('funnel-contactes-count').textContent = `${conversion.contactes || 0} prospects`;
    document.getElementById('funnel-contactes-pct').textContent = contactesPct.toFixed(1) + '%';
    document.getElementById('funnel-contactes-bar').style.width = contactesPct + '%';
    
    // Qualifiés
    const qualifiesPct = total > 0 ? (conversion.qualifies / total * 100) : 0;
    document.getElementById('funnel-qualifies-count').textContent = `${conversion.qualifies || 0} prospects`;
    document.getElementById('funnel-qualifies-pct').textContent = qualifiesPct.toFixed(1) + '%';
    document.getElementById('funnel-qualifies-bar').style.width = qualifiesPct + '%';
    
    // Propositions
    const proposalsPct = total > 0 ? (conversion.proposals / total * 100) : 0;
    document.getElementById('funnel-proposals-count').textContent = `${conversion.proposals || 0} propositions`;
    document.getElementById('funnel-proposals-pct').textContent = proposalsPct.toFixed(1) + '%';
    document.getElementById('funnel-proposals-bar').style.width = proposalsPct + '%';
    
    // Métriques
    document.getElementById('metric-contact-rate').textContent = contactesPct.toFixed(1) + '%';
    document.getElementById('metric-qualification-rate').textContent = 
        (conversion.contactes > 0 ? (conversion.qualifies / conversion.contactes * 100) : 0).toFixed(1) + '%';
    document.getElementById('metric-proposal-rate').textContent = 
        (conversion.qualifies > 0 ? (conversion.proposals / conversion.qualifies * 100) : 0).toFixed(1) + '%';
    document.getElementById('metric-global-rate').textContent = proposalsPct.toFixed(1) + '%';
    document.getElementById('metric-avg-contact-delay').textContent = 
        `${conversion.avg_contact_delay || 0} jours`;
    document.getElementById('metric-avg-qualification-delay').textContent = 
        `${conversion.avg_qualification_delay || 0} jours`;
    
    // Chart conversion par type
    const conversionByTypeCtx = document.getElementById('conversionByTypeChart');
    if (conversionByTypeCtx && conversion.by_type) {
        if (charts.conversionByType) charts.conversionByType.destroy();
        charts.conversionByType = new Chart(conversionByTypeCtx, {
            type: 'bar',
            data: {
                labels: Object.keys(conversion.by_type),
                datasets: [{
                    label: 'Taux de Conversion (%)',
                    data: Object.values(conversion.by_type),
                    backgroundColor: ['#4CAF50', '#2196F3', '#FF9800', '#8BC34A']
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { 
                        beginAtZero: true,
                        max: 100,
                        ticks: {
                            callback: function(value) {
                                return value + '%';
                            }
                        }
                    }
                }
            }
        });
    }
}

function updateUserStats(users) {
    const tbody = document.getElementById('usersTableBody');
    if (!tbody || !users || users.length === 0) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Aucune donnée utilisateur</td></tr>';
        return;
    }
    
    let html = '';
    users.forEach((user, index) => {
        const tauxContact = user.total > 0 ? (user.contactes / user.total * 100) : 0;
        const tauxQualif = user.contactes > 0 ? (user.qualifies / user.contactes * 100) : 0;
        const tauxGlobal = user.total > 0 ? (user.qualifies / user.total * 100) : 0;
        
        html += `
            <tr>
                <td>
                    <div class="d-flex align-items-center">
                        <div class="rounded-circle bg-primary text-white d-flex align-items-center justify-content-center me-2" 
                             style="width: 35px; height: 35px; font-weight: bold;">
                            ${user.nom ? user.nom.charAt(0).toUpperCase() : 'U'}
                        </div>
                        <div>
                            <strong>${user.nom || 'Utilisateur ' + (index + 1)}</strong>
                            <div class="text-muted small">${user.email || '-'}</div>
                        </div>
                    </div>
                </td>
                <td class="text-center"><strong>${user.total}</strong></td>
                <td class="text-center">${user.contactes}</td>
                <td class="text-center">${user.qualifies}</td>
                <td class="text-center">${user.proposals}</td>
                <td class="text-center">
                    <span class="badge ${tauxContact >= 50 ? 'bg-success' : tauxContact >= 30 ? 'bg-warning' : 'bg-secondary'}">
                        ${tauxContact.toFixed(1)}%
                    </span>
                </td>
                <td class="text-center">
                    <span class="badge ${tauxQualif >= 40 ? 'bg-success' : tauxQualif >= 20 ? 'bg-warning' : 'bg-secondary'}">
                        ${tauxQualif.toFixed(1)}%
                    </span>
                </td>
                <td class="text-center">
                    <span class="badge ${tauxGlobal >= 30 ? 'bg-success' : tauxGlobal >= 15 ? 'bg-warning' : 'bg-secondary'}">
                        ${tauxGlobal.toFixed(1)}%
                    </span>
                </td>
                <td class="text-center">${user.total_actions || 0}</td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
    
    // Top Users Chart
    const topUsersCtx = document.getElementById('topUsersChart');
    if (topUsersCtx) {
        const topUsers = users.slice(0, 5);
        if (charts.topUsers) charts.topUsers.destroy();
        charts.topUsers = new Chart(topUsersCtx, {
            type: 'bar',
            data: {
                labels: topUsers.map(u => u.nom || 'Inconnu'),
                datasets: [{
                    label: 'Prospects Qualifiés',
                    data: topUsers.map(u => u.qualifies),
                    backgroundColor: '#4CAF50'
                }]
            },
            options: {
                responsive: true,
                indexAxis: 'y',
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
    
    // User Actions Chart
    const userActionsCtx = document.getElementById('userActionsChart');
    if (userActionsCtx) {
        if (charts.userActions) charts.userActions.destroy();
        charts.userActions = new Chart(userActionsCtx, {
            type: 'bar',
            data: {
                labels: users.slice(0, 5).map(u => u.nom || 'Inconnu'),
                datasets: [{
                    label: 'Actions Totales',
                    data: users.slice(0, 5).map(u => u.total_actions || 0),
                    backgroundColor: '#2196F3'
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { display: false }
                }
            }
        });
    }
}

function updatePerformance(perf) {
    if (!perf) return;
    
    // Meilleur taux
    document.getElementById('perf-best-rate').textContent = (perf.best_conversion_rate || 0).toFixed(1) + '%';
    document.getElementById('perf-best-user').textContent = perf.best_conversion_user || '-';
    
    // Plus rapide
    document.getElementById('perf-fastest').textContent = (perf.fastest_contact_delay || 0) + 'j';
    document.getElementById('perf-fastest-user').textContent = perf.fastest_contact_user || '-';
    
    // Plus productif
    document.getElementById('perf-most-productive').textContent = perf.most_productive_count || 0;
    document.getElementById('perf-productive-user').textContent = perf.most_productive_user || '-';
}

function updateDepartments(depts) {
    const tbody = document.getElementById('deptTableBody');
    if (!tbody || !depts || depts.length === 0) {
        if (tbody) tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted">Aucune donnée département</td></tr>';
        return;
    }
    
    let html = '';
    depts.forEach(dept => {
        const taux = dept.total > 0 ? (dept.qualifies / dept.total * 100) : 0;
        html += `
            <tr>
                <td><strong>${dept.departement}</strong></td>
                <td class="text-center">${dept.total}</td>
                <td class="text-center">${dept.qualifies}</td>
                <td class="text-center">
                    <span class="badge ${taux >= 30 ? 'bg-success' : taux >= 15 ? 'bg-warning' : 'bg-secondary'}">
                        ${taux.toFixed(1)}%
                    </span>
                </td>
                <td>
                    <div class="progress progress-thin">
                        <div class="progress-bar ${taux >= 30 ? 'bg-success' : taux >= 15 ? 'bg-warning' : 'bg-secondary'}" 
                             style="width: ${taux}%"></div>
                    </div>
                </td>
            </tr>
        `;
    });
    tbody.innerHTML = html;
    
    // Geo Chart
    const geoCtx = document.getElementById('geoChart');
    if (geoCtx) {
        if (charts.geo) charts.geo.destroy();
        charts.geo = new Chart(geoCtx, {
            type: 'bar',
            data: {
                labels: depts.map(d => d.departement),
                datasets: [
                    {
                        label: 'Total Prospects',
                        data: depts.map(d => d.total),
                        backgroundColor: '#2196F3'
                    },
                    {
                        label: 'Qualifiés',
                        data: depts.map(d => d.qualifies),
                        backgroundColor: '#4CAF50'
                    }
                ]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: { position: 'top' }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }
}

async function loadUserStats() {
    const period = document.getElementById('user-period')?.value || '30';
    try {
        const response = await fetch(`/api/crm/dashboard/users?period=${period}`);
        const data = await response.json();
        if (data.success) {
            updateUserStats(data.users);
        }
    } catch (error) {
        console.error('Erreur chargement stats utilisateurs:', error);
    }
}
