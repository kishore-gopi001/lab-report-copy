// =====================================================
// ML DASHBOARD - ALL RISK PREDICTION CHARTS
// =====================================================

let allRiskPatients = [];
let currentPage = 1;
let patientsPerPage = 20;
let currentRiskLevel = 2;

// =====================================================
// 1. LOAD RISK DISTRIBUTION (Cards: 0, 47, 53)
// =====================================================
async function loadRiskDistribution() {
    try {
        const res = await authFetch("/predict/risk-distribution");
        const data = await res.json();

        document.getElementById("riskNormalCount").innerText = data.NORMAL || 0;
        document.getElementById("riskAbnormalCount").innerText = data.ABNORMAL || 0;
        document.getElementById("riskCriticalCount").innerText = data.CRITICAL || 0;
    } catch (error) {
        console.error("Error loading risk distribution:", error);
        document.getElementById("riskNormalCount").innerText = "N/A";
        document.getElementById("riskAbnormalCount").innerText = "N/A";
        document.getElementById("riskCriticalCount").innerText = "N/A";
    }
}

// =====================================================
// 2. PATIENT RISK DISTRIBUTION CHART (Donut)
// =====================================================
async function loadPatientRiskChart() {
    try {
        const res = await authFetch("/reports/patient-risk");
        const data = await res.json();

        new Chart(document.getElementById("patientRiskChart"), {
            type: "doughnut",
            data: {
                labels: ['🟢 Normal', '🟡 Abnormal', '🔴 Critical'],
                datasets: [{
                    data: [data.NORMAL || 0, data.ABNORMAL || 0, data.CRITICAL || 0],
                    backgroundColor: [
                        '#4caf50',
                        '#ff9800',
                        '#f44336'
                    ],
                    borderColor: 'white',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom' },
                    tooltip: {
                        callbacks: {
                            label: function (context) {
                                return context.label + ': ' + context.parsed + ' patients';
                            }
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error("Error loading patient risk chart:", error);
    }
}

// =====================================================
// 3. RECENT CRITICAL ACTIVITY CHART (Horizontal Bar)
// =====================================================
async function loadRecentCriticalChart() {
    try {
        const res = await authFetch("/reports/recent-critical");
        const data = await res.json();

        // Get top 5 recent critical tests
        const topData = data.slice(0, 5);
        const testNames = topData.map(r => r.test_name);
        const counts = topData.map(r => r.count);

        new Chart(document.getElementById("recentCriticalChart"), {
            type: "bar",
            data: {
                labels: testNames,
                datasets: [{
                    label: 'Critical Cases (24h)',
                    data: counts,
                    backgroundColor: [
                        '#f44336',
                        '#e53935',
                        '#d32f2f',
                        '#c62828',
                        '#b71c1c'
                    ],
                    borderRadius: 6
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: true }
                },
                scales: {
                    x: { beginAtZero: true }
                }
            }
        });
    } catch (error) {
        console.error("Error loading recent critical chart:", error);
    }
}

// =====================================================
// 4. UNREVIEWED CRITICAL SUMMARY
// =====================================================
async function loadUnreviewedCriticalSummary() {
    try {
        const res = await authFetch("/reports/unreviewed-critical-summary");
        const data = await res.json();

        document.getElementById("totalUnreviewed").innerText = data.total_unreviewed || 0;
        document.getElementById("affectedPatients").innerText = data.affected_patients || 0;
    } catch (error) {
        console.error("Error loading unreviewed summary:", error);
        document.getElementById("totalUnreviewed").innerText = "N/A";
        document.getElementById("affectedPatients").innerText = "N/A";
    }
}

// =====================================================
// 5. HIGH-RISK PATIENT COUNT
// =====================================================
async function loadHighRiskPatientCount() {
    try {
        const res = await authFetch("/reports/high-risk-patients");
        const data = await res.json();

        document.getElementById("criticalPatientCount").innerText = data.critical_patients || 0;
    } catch (error) {
        console.error("Error loading high-risk count:", error);
        document.getElementById("criticalPatientCount").innerText = "N/A";
    }
}

// =====================================================
// HIGH RISK PATIENTS TABLE WITH PAGINATION
// =====================================================
async function loadHighRiskPatients(riskLevel = 2, limit = 100) {
    try {
        const res = await authFetch(`/predict/high-risk?risk_level=${riskLevel}&limit=${limit}`);
        const patients = await res.json();

        allRiskPatients = Array.isArray(patients) ? patients : [];
        currentRiskLevel = riskLevel;
        currentPage = 1;

        displayPaginatedPatients();
        updatePaginationControls();
    } catch (error) {
        console.error("Error loading high-risk patients:", error);
        document.querySelector("#riskPatientsTable tbody").innerHTML =
            "<tr><td colspan='6'>Error loading risk predictions</td></tr>";
    }
}

function displayPaginatedPatients() {
    const startIdx = (currentPage - 1) * patientsPerPage;
    const endIdx = startIdx + patientsPerPage;
    const paginatedPatients = allRiskPatients.slice(startIdx, endIdx);

    const tbody = document.querySelector("#riskPatientsTable tbody");
    tbody.innerHTML = "";

    if (paginatedPatients.length > 0) {
        paginatedPatients.forEach(patient => {
            if (!patient.error && patient.risk_label) {
                const row = `
                    <tr>
                        <td>${patient.subject_id}</td>
                        <td><span class="badge badge-${patient.risk_label.toLowerCase()}">${patient.risk_label}</span></td>
                        <td>${patient.confidence || 0}%</td>
                        <td>${patient.probabilities?.normal || 0}%</td>
                        <td>${patient.probabilities?.abnormal || 0}%</td>
                        <td>${patient.probabilities?.critical || 0}%</td>
                    </tr>
                `;
                tbody.innerHTML += row;
            }
        });
    } else {
        tbody.innerHTML = "<tr><td colspan='6'>No high-risk patients found</td></tr>";
    }
}

function updatePaginationControls() {
    const totalPages = Math.ceil(allRiskPatients.length / patientsPerPage);
    const pageInfo = document.getElementById("pageInfo");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");

    pageInfo.innerText = `Page ${currentPage} of ${totalPages || 1} (${allRiskPatients.length} total)`;
    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages || totalPages === 0;
}

// Pagination Event Listeners
document.getElementById("prevBtn").addEventListener("click", () => {
    if (currentPage > 1) {
        currentPage--;
        displayPaginatedPatients();
        updatePaginationControls();
        window.scrollTo(0, document.querySelector("#riskPatientsTable").offsetTop);
    }
});

document.getElementById("nextBtn").addEventListener("click", () => {
    const totalPages = Math.ceil(allRiskPatients.length / patientsPerPage);
    if (currentPage < totalPages) {
        currentPage++;
        displayPaginatedPatients();
        updatePaginationControls();
        window.scrollTo(0, document.querySelector("#riskPatientsTable").offsetTop);
    }
});

// =====================================================
// INITIAL PAGE LOAD
// =====================================================
async function initMLDashboard() {
    loadRiskDistribution();
    loadPatientRiskChart();
    loadRecentCriticalChart();
    loadUnreviewedCriticalSummary();
    loadHighRiskPatientCount();
    await loadHighRiskPatients(2, 100);
}

// Load on page init
document.addEventListener("DOMContentLoaded", () => {
    initMLDashboard();
});

// Auto-refresh risk stats every 30 seconds (not the table - user controls that)
setInterval(() => {
    loadRiskDistribution();
    loadUnreviewedCriticalSummary();
    loadHighRiskPatientCount();
}, 30000);
