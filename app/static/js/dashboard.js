// dashboard.js logic


// =====================================================
// DASHBOARD SUMMARY COUNTS
// =====================================================
async function loadSummary() {
    try {
        const res = await authFetch("/reports/summary");
        const data = await res.json();

        let total = 0, normal = 0, abnormal = 0, critical = 0, unknown = 0;

        if (Array.isArray(data)) {
            data.forEach(row => {
                total += row.count;
                if (row.status === "NORMAL") normal = row.count;
                else if (row.status === "ABNORMAL") abnormal = row.count;
                else if (row.status === "CRITICAL") critical = row.count;
                else unknown += row.count;
            });
        }

        document.getElementById("totalLabs").innerText = total || 0;
        document.getElementById("normalCount").innerText = normal || 0;
        document.getElementById("abnormalCount").innerText = abnormal || 0;
        document.getElementById("criticalCount").innerText = critical || 0;
        document.getElementById("unknownCount").innerText = unknown || 0;
    } catch (error) {
        console.error("Error loading summary:", error);
        document.getElementById("totalLabs").innerText = "Error";
        document.getElementById("normalCount").innerText = "Error";
        document.getElementById("abnormalCount").innerText = "Error";
        document.getElementById("criticalCount").innerText = "Error";
        document.getElementById("unknownCount").innerText = "Error";
    }
}

// =====================================================
// BAR CHART – AFFECTED TESTS
// =====================================================
async function loadLabChart() {
    try {
        const res = await authFetch("/reports/by-lab");
        const data = await res.json();

        const labMap = {};
        if (Array.isArray(data)) {
            data.forEach(row => {
                labMap[row.test_name] = (labMap[row.test_name] || 0) + row.patient_count;
            });
        }

        new Chart(document.getElementById("labChart"), {
            type: "bar",
            data: {
                labels: Object.keys(labMap),
                datasets: [{
                    data: Object.values(labMap),
                    backgroundColor: "#1f3c88"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: { y: { beginAtZero: true } }
            }
        });
    } catch (error) {
        console.error("Error loading lab chart:", error);
    }
}

// =====================================================
// PIE CHART – GENDER DISTRIBUTION
// =====================================================
async function loadGenderChart() {
    try {
        const res = await authFetch("/reports/by-gender");
        const data = await res.json();

        const genderMap = {};
        if (Array.isArray(data)) {
            data.forEach(row => {
                genderMap[row.gender] = (genderMap[row.gender] || 0) + row.patient_count;
            });
        }

        new Chart(document.getElementById("genderChart"), {
            type: "pie",
            data: {
                labels: Object.keys(genderMap),
                datasets: [{
                    data: Object.values(genderMap),
                    backgroundColor: ["#36a2eb", "#ff6384", "#cfbebe"]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });
    } catch (error) {
        console.error("Error loading gender chart:", error);
    }
}

// =====================================================
// DOUGHNUT CHART – STATUS OVERVIEW
// =====================================================
async function loadStatusChart() {
    try {
        const res = await authFetch("/reports/summary");
        const data = await res.json();

        if (Array.isArray(data)) {
            new Chart(document.getElementById("statusChart"), {
                type: "doughnut",
                data: {
                    labels: data.map(r => r.status),
                    datasets: [{
                        data: data.map(r => r.count),
                        backgroundColor: ["#4caf50", "#ff9800", "#f44336", "#9e9e9e"]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { position: "bottom" } }
                }
            });
        }
    } catch (error) {
        console.error("Error loading status chart:", error);
    }
}

// =====================================================
// TABLE – TOP AFFECTED TESTS
// =====================================================
async function loadTopTestsTable() {
    try {
        const res = await authFetch("/reports/by-lab");
        const data = await res.json();

        const tbody = document.querySelector("#topTestsTable tbody");
        tbody.innerHTML = "";

        if (Array.isArray(data)) {
            data.slice(0, 10).forEach(row => {
                const tr = document.createElement("tr");
                tr.innerHTML = `
                    <td>${row.test_name}</td>
                    <td><span class="badge badge-${row.status.toLowerCase()}">${row.status}</span></td>
                    <td>${row.patient_count}</td>
                `;
                tbody.appendChild(tr);
            });
        }
    } catch (error) {
        console.error("Error loading top tests table:", error);
        document.querySelector("#topTestsTable tbody").innerHTML =
            "<tr><td colspan='3'>Error loading data</td></tr>";
    }
}

// =====================================================
// ALERT PANEL – UNREVIEWED CRITICAL
// =====================================================
async function loadCriticalAlerts() {
    try {
        const res = await authFetch("/reports/unreviewed-critical");
        const data = await res.json();

        const alertBox = document.getElementById("criticalAlerts");
        alertBox.innerHTML = "";

        if (data.length === 0) {
            alertBox.innerHTML = "<li>No pending critical alerts 🎉</li>";
            return;
        }

        if (Array.isArray(data)) {
            data.slice(0, 5).forEach(row => {
                const li = document.createElement("li");
                li.textContent = `Subject ${row.subject_id} | ${row.test_name}: ${row.value} ${row.unit}`;
                alertBox.appendChild(li);
            });
        }
    } catch (error) {
        console.error("Error loading critical alerts:", error);
        document.getElementById("criticalAlerts").innerHTML =
            "<li>Error loading alerts</li>";
    }
}

// =====================================================
// INITIAL DASHBOARD LOAD
// =====================================================
document.addEventListener("DOMContentLoaded", () => {
    loadSummary();
    loadLabChart();
    loadGenderChart();
    loadStatusChart();
    loadTopTestsTable();
    loadCriticalAlerts();
});
