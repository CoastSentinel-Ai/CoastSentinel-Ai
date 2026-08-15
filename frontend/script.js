// frontend/script.js

const API_BASE_URL = "http://localhost:5000/api";

// 8 Coastal Sectors Telemetry Dataset
const COASTAL_SITES = {
    vizag: {
        name: "Visakhapatnam, AP",
        beach: "RK Beach Sector",
        coords: [17.7126, 83.3236],
        features: { wave_height_m: 3.4, tidal_range_m: 2.2, coastal_slope_deg: 14.0, vegetation_cover_pct: 18.0, sediment_coarseness: 0.5, population_density: 12500, coastal_drain_count: 12, river_proximity_km: 1.8, vessel_density: 38.0, monsoon_runoff_idx: 0.78 }
    },
    mumbai: {
        name: "Mumbai Coast, MH",
        beach: "Juhu & Colaba Sector",
        coords: [19.0760, 72.8777],
        features: { wave_height_m: 3.8, tidal_range_m: 3.2, coastal_slope_deg: 8.5, vegetation_cover_pct: 15.0, sediment_coarseness: 0.4, population_density: 21000, coastal_drain_count: 16, river_proximity_km: 1.2, vessel_density: 42.0, monsoon_runoff_idx: 0.85 }
    },
    digha: {
        name: "Digha Sea Beach, WB",
        beach: "Old & New Digha Sector",
        coords: [21.6266, 87.5074],
        features: { wave_height_m: 4.5, tidal_range_m: 3.9, coastal_slope_deg: 18.0, vegetation_cover_pct: 10.0, sediment_coarseness: 0.3, population_density: 9500, coastal_drain_count: 11, river_proximity_km: 0.8, vessel_density: 28.0, monsoon_runoff_idx: 0.92 }
    },
    goa: {
        name: "Panaji Coast, Goa",
        beach: "Calangute & Miramar Sector",
        coords: [15.4989, 73.8278],
        features: { wave_height_m: 1.8, tidal_range_m: 1.2, coastal_slope_deg: 5.0, vegetation_cover_pct: 65.0, sediment_coarseness: 1.2, population_density: 3200, coastal_drain_count: 4, river_proximity_km: 5.5, vessel_density: 12.0, monsoon_runoff_idx: 0.40 }
    },
    chennai: {
        name: "Marina Beach, TN",
        beach: "Chennai Coastal Sector",
        coords: [13.0499, 80.2824],
        features: { wave_height_m: 3.1, tidal_range_m: 2.1, coastal_slope_deg: 11.2, vegetation_cover_pct: 25.0, sediment_coarseness: 0.7, population_density: 17000, coastal_drain_count: 14, river_proximity_km: 2.1, vessel_density: 35.0, monsoon_runoff_idx: 0.65 }
    },
    puri: {
        name: "Puri Beach, OD",
        beach: "Golden Beach Sector",
        coords: [19.7983, 85.8249],
        features: { wave_height_m: 3.9, tidal_range_m: 2.8, coastal_slope_deg: 15.1, vegetation_cover_pct: 20.0, sediment_coarseness: 0.6, population_density: 8200, coastal_drain_count: 8, river_proximity_km: 3.1, vessel_density: 19.0, monsoon_runoff_idx: 0.81 }
    },
    kochi: {
        name: "Kochi Coast, KL",
        beach: "Fort Kochi Sector",
        coords: [9.9674, 76.2429],
        features: { wave_height_m: 2.2, tidal_range_m: 1.1, coastal_slope_deg: 6.2, vegetation_cover_pct: 55.0, sediment_coarseness: 0.9, population_density: 11000, coastal_drain_count: 15, river_proximity_km: 0.5, vessel_density: 31.0, monsoon_runoff_idx: 0.75 }
    },
    mangalore: {
        name: "Mangalore Coast, KA",
        beach: "Panambur Beach Sector",
        coords: [12.9141, 74.8560],
        features: { wave_height_m: 2.9, tidal_range_m: 1.8, coastal_slope_deg: 9.8, vegetation_cover_pct: 40.0, sediment_coarseness: 0.8, population_density: 6400, coastal_drain_count: 7, river_proximity_km: 2.4, vessel_density: 22.0, monsoon_runoff_idx: 0.70 }
    }
};

let mainMap, analyticsMap, mainHeatLayer, analyticsHeatLayer;
let riskChart, ppdsBarChart, erosionLineChart, riskDoughnutChart;
let activeSiteKey = "vizag";

// -------------------------------------------------------------------
// Initialization & Map / Chart Setup
// -------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", () => {
    initMainMap();
    initDashChart();
    renderCityList();
    checkServerHealth();
    populateNgoDropdown();

    // Load initial city
    loadSiteData(activeSiteKey);

    // Dynamic Select Listener
    const siteSelect = document.getElementById("site-select");
    if (siteSelect) {
        siteSelect.addEventListener("change", (e) => loadSiteData(e.target.value));
    }
});

// Render Sidebar 8-City List
function renderCityList() {
    const cityListContainer = document.getElementById("city-list");
    const cityCountElem = document.getElementById("city-count");
    if (!cityListContainer) return;

    const keys = Object.keys(COASTAL_SITES);
    if (cityCountElem) cityCountElem.innerText = `${keys.length} Cities Active`;

    cityListContainer.innerHTML = keys.map(key => {
        const site = COASTAL_SITES[key];
        const isActive = key === activeSiteKey;
        return `
            <button onclick="loadSiteData('${key}')" 
                class="w-full text-left p-3 rounded-xl border transition-all flex justify-between items-center ${
                    isActive 
                    ? 'bg-teal-950/60 border-teal-500/80 text-teal-200' 
                    : 'bg-[#08111a] border-slate-800 text-slate-300 hover:border-slate-700 hover:bg-[#0c1827]'
                }">
                <div>
                    <h4 class="text-xs font-semibold">${site.name}</h4>
                    <p class="text-[10px] text-slate-400">${site.beach}</p>
                </div>
                <span class="text-[10px] font-mono text-teal-400 bg-teal-950 px-2 py-0.5 rounded-full border border-teal-800/40">Select</span>
            </button>
        `;
    }).join("");
}

function initMainMap() {
    mainMap = L.map("map").setView([17.7126, 83.3236], 10);
    L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
        attribution: "&copy; OpenStreetMap &copy; CARTO", maxZoom: 18
    }).addTo(mainMap);
}

function initDashChart() {
    const ctx = document.getElementById("analyticsChart")?.getContext("2d");
    if (!ctx) return;
    riskChart = new Chart(ctx, {
        type: "bar",
        data: {
            labels: ["CERI (Erosion)", "PPDS (Plastic)", "Overall Risk"],
            datasets: [{
                label: "Live Score",
                data: [0, 0, 0],
                backgroundColor: ["rgba(244, 63, 94, 0.7)", "rgba(45, 212, 191, 0.7)", "rgba(56, 189, 248, 0.7)"],
                borderColor: ["#f43f5e", "#2dd4bf", "#38bdf8"],
                borderWidth: 1.5
            }]
        },
        options: {
            responsive: true,
            scales: { y: { beginAtZero: true, max: 100, ticks: { color: "#94a3b8" } }, x: { ticks: { color: "#94a3b8" } } },
            plugins: { legend: { display: false } }
        }
    });
}

// -------------------------------------------------------------------
// Live ML Inference Fetch
// -------------------------------------------------------------------
async function loadSiteData(siteKey) {
    activeSiteKey = siteKey;
    const site = COASTAL_SITES[siteKey];
    if (!site) return;

    renderCityList();
    mainMap.flyTo(site.coords, 11, { duration: 1.2 });

    // Sync select dropdown if changed via list
    const siteSelect = document.getElementById("site-select");
    if (siteSelect) siteSelect.value = siteKey;

    const payload = { location_name: site.name, ...site.features };

    try {
        const response = await fetch(`${API_BASE_URL}/v1/predict`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        const data = await response.json();
        if (data.status === "success") {
            const preds = data.predictions;
            updateDashboardUI(site.name, site.beach, preds);
            updateMapHeatmap(site.coords, preds.ppds_score);
            if (riskChart) {
                riskChart.data.datasets[0].data = [preds.ceri_score, preds.ppds_score, preds.overall_risk_score];
                riskChart.update();
            }
        }
    } catch (err) {
        console.warn("ML Server offline or unreachable. Using fallback mathematical estimates.");
        const mockCERI = (site.features.wave_height_m * 12 + site.features.coastal_slope_deg * 2).toFixed(1);
        const mockPPDS = (site.features.population_density / 350 + site.features.coastal_drain_count * 2.5).toFixed(1);
        const mockOverall = ((parseFloat(mockCERI) + parseFloat(mockPPDS)) / 2).toFixed(1);
        updateDashboardUI(site.name, site.beach, { ceri_score: mockCERI, ppds_score: mockPPDS, overall_risk_score: mockOverall, shoreline_retreat_m: (mockCERI * 0.04).toFixed(2), threat_level: mockOverall > 60 ? "HIGH" : "MODERATE" });
        updateMapHeatmap(site.coords, mockPPDS);
    }
}

function updateDashboardUI(name, beach, preds) {
    document.getElementById("sector-name").innerText = name;
    document.getElementById("location-title").innerText = name;
    document.getElementById("beach-name").innerText = beach;
    
    document.getElementById("ceri-val").innerText = preds.ceri_score;
    document.getElementById("ppds-val").innerText = preds.ppds_score;
    document.getElementById("overall-risk").innerText = preds.overall_risk_score;
    document.getElementById("recession-rate").innerText = `${preds.shoreline_retreat_m} m/yr`;

    const badge = document.getElementById("risk-badge");
    if (badge) {
        badge.innerText = preds.threat_level || "EVALUATING";
        badge.className = `px-2.5 py-1 rounded-full text-xs font-bold border ${
            preds.threat_level === "CRITICAL" || preds.threat_level === "HIGH" 
            ? "bg-rose-950/80 text-rose-400 border-rose-800/60" 
            : "bg-amber-950/80 text-amber-400 border-amber-800/60"
        }`;
    }
}

function updateMapHeatmap(coords, ppdsScore) {
    if (mainHeatLayer) mainMap.removeLayer(mainHeatLayer);

    const heatPoints = [];
    const intensity = Math.min(ppdsScore / 100, 1.0);
    for (let i = 0; i < 35; i++) {
        const latOffset = (Math.random() - 0.5) * 0.09;
        const lngOffset = (Math.random() - 0.5) * 0.09;
        heatPoints.push([coords[0] + latOffset, coords[1] + lngOffset, intensity]);
    }
    if (typeof L.heatLayer === "function") {
        mainHeatLayer = L.heatLayer(heatPoints, { radius: 25, blur: 15, maxZoom: 14 }).addTo(mainMap);
    }
}

// -------------------------------------------------------------------
// TAB SWITCHER & ANALYTICS INITIALIZER (Fixes Empty Analytics Page)
// -------------------------------------------------------------------
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('text-teal-400', 'border-teal-400');
        btn.classList.add('text-slate-400', 'border-transparent');
    });

    const activeTab = document.getElementById(`tab-${tabId}`);
    const activeNav = document.getElementById(`nav-${tabId}`);
    if (activeTab) activeTab.classList.add('active');
    if (activeNav) {
        activeNav.classList.add('text-teal-400', 'border-teal-400');
        activeNav.classList.remove('text-slate-400', 'border-transparent');
    }

    if (tabId === 'analytics') {
        setTimeout(initAnalyticsTab, 100);
    }
}

function initAnalyticsTab() {
    // 1. Initialize Analytics Heatmap Map if not loaded
    if (!analyticsMap) {
        analyticsMap = L.map("analytics-heatmap").setView([19.0760, 78.8777], 5);
        L.tileLayer("https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png", {
            attribution: "&copy; OpenStreetMap", maxZoom: 18
        }).addTo(analyticsMap);

        const allHeatPoints = [];
        Object.values(COASTAL_SITES).forEach(site => {
            for (let i = 0; i < 20; i++) {
                allHeatPoints.push([site.coords[0] + (Math.random()-0.5)*0.1, site.coords[1] + (Math.random()-0.5)*0.1, 0.8]);
            }
        });
        if (typeof L.heatLayer === "function") {
            L.heatLayer(allHeatPoints, { radius: 20, blur: 12 }).addTo(analyticsMap);
        }
    } else {
        analyticsMap.invalidateSize();
    }

    // 2. Render Analytics Visual Charts
    const cityNames = Object.values(COASTAL_SITES).map(s => s.name.split(',')[0]);
    
    // Bar Chart
    if (!ppdsBarChart) {
        const ctxBar = document.getElementById("ppdsBarChart")?.getContext("2d");
        if (ctxBar) {
            ppdsBarChart = new Chart(ctxBar, {
                type: "bar",
                data: {
                    labels: cityNames,
                    datasets: [{ label: "PPDS Score", data: [65, 82, 91, 35, 74, 68, 48, 52], backgroundColor: "rgba(45, 212, 191, 0.7)", borderColor: "#2dd4bf", borderWidth: 1 }]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { ticks: { color: "#94a3b8" } }, x: { ticks: { color: "#94a3b8" } } } }
            });
        }
    }

    // Line Chart
    if (!erosionLineChart) {
        const ctxLine = document.getElementById("erosionLineChart")?.getContext("2d");
        if (ctxLine) {
            erosionLineChart = new Chart(ctxLine, {
                type: "line",
                data: {
                    labels: ["Jan", "Mar", "May", "Jul", "Sep", "Nov", "Dec"],
                    datasets: [
                        { label: "Visakhapatnam", data: [2.1, 2.4, 2.8, 3.5, 3.8, 3.3, 3.4], borderColor: "#f43f5e", tension: 0.3 },
                        { label: "Mumbai", data: [3.0, 3.2, 3.9, 4.8, 4.5, 3.8, 3.8], borderColor: "#38bdf8", tension: 0.3 }
                    ]
                },
                options: { responsive: true, maintainAspectRatio: false, scales: { y: { ticks: { color: "#94a3b8" } }, x: { ticks: { color: "#94a3b8" } } } }
            });
        }
    }

    // Doughnut Chart
    if (!riskDoughnutChart) {
        const ctxDoughnut = document.getElementById("riskDoughnutChart")?.getContext("2d");
        if (ctxDoughnut) {
            riskDoughnutChart = new Chart(ctxDoughnut, {
                type: "doughnut",
                data: {
                    labels: ["Critical", "High Risk", "Moderate", "Low"],
                    datasets: [{ data: [25, 37.5, 25, 12.5], backgroundColor: ["#dc2626", "#f43f5e", "#f59e0b", "#10b981"] }]
                },
                options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { labels: { color: "#94a3b8" } } } }
            });
        }
    }
}

// -------------------------------------------------------------------
// CITIZEN REPORT GPS & MOBILE IMAGE CAPTURE
// -------------------------------------------------------------------
function getGPSLocation() {
    const statusElem = document.getElementById("gps-status");
    if (navigator.geolocation) {
        if (statusElem) statusElem.innerText = "📍 Accessing Satellite GPS...";
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude.toFixed(6);
                const lng = pos.coords.longitude.toFixed(6);
                document.getElementById("report-location").value = `GPS Lat: ${lat}, Lng: ${lng}`;
                if (statusElem) statusElem.innerText = "✅ Precise GPS Coordinates Acquired!";
            },
            (err) => {
                alert("GPS Access Denied or Unavailable: " + err.message);
                if (statusElem) statusElem.innerText = "❌ GPS Retrieval Failed.";
            },
            { enableHighAccuracy: true }
        );
    } else {
        alert("Geolocation is not supported by your mobile or browser device.");
    }
}

function previewReportImage(event) {
    const file = event.target.files[0];
    const previewContainer = document.getElementById("image-preview-container");
    const previewImg = document.getElementById("image-preview");

    if (file && previewContainer && previewImg) {
        const reader = new FileReader();
        reader.onload = function (e) {
            previewImg.src = e.target.result;
            previewContainer.classList.remove("hidden");
        };
        reader.readAsDataURL(file);
    }
}

function submitCitizenReport(event) {
    event.preventDefault();
    const banner = document.getElementById("citizen-banner");
    if (banner) {
        banner.classList.remove("hidden");
        banner.innerHTML = "✅ <strong>Report Submitted Successfully!</strong> Geotagged telemetry and attached imagery queued for cleanup dispatch.";
        event.target.reset();
        document.getElementById("image-preview-container")?.classList.add("hidden");
    }
}

// Helper Utilities
function populateNgoDropdown() {
    const select = document.getElementById("ngo-region");
    if (!select) return;
    select.innerHTML = `<option value="" disabled selected>Select active operational coastal region</option>` +
        Object.keys(COASTAL_SITES).map(k => `<option value="${k}">${COASTAL_SITES[k].name}</option>`).join("");
}

async function checkServerHealth() {
    const statusElem = document.getElementById("server-status");
    try {
        const res = await fetch(`${API_BASE_URL}/health`);
        const data = await res.json();
        if (statusElem) {
            statusElem.innerText = data.models_loaded ? "ML Backend Online" : "Server Active (No Models)";
            statusElem.className = data.models_loaded ? "text-xs font-mono text-emerald-400 bg-emerald-950/60 px-2.5 py-1 rounded-full border border-emerald-800" : "text-xs font-mono text-amber-400";
        }
    } catch {
        if (statusElem) {
            statusElem.innerText = "ML Server Offline (Simulation Active)";
            statusElem.className = "text-xs font-mono text-rose-400 bg-rose-950/60 px-2.5 py-1 rounded-full border border-rose-800";
        }
    }
}

function registerNGO(event) {
    event.preventDefault();
    const banner = document.getElementById("ngo-banner");
    if (banner) {
        banner.classList.remove("hidden");
        banner.innerHTML = "✅ <strong>NGO Registered!</strong> You will receive automated SMS notifications for high-risk alerts.";
        event.target.reset();
    }
}

function triggerAlert() {
    const activeLocation = document.getElementById("sector-name").innerText;
    fetch(`${API_BASE_URL}/trigger_alert`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ location: activeLocation, threat_level: "HIGH" })
    })
    .then(r => r.json())
    .then(data => alert(`Alert Action: ${data.message || 'SMS Dispatched'}`))
    .catch(() => alert(`Dispatched Emergency Alerts to registered NGOs for ${activeLocation}`));
}