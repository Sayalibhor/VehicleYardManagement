document.addEventListener("DOMContentLoaded", function() {
    loadVehicles();

    document.getElementById("entry-form").addEventListener("submit", function(e) {
        e.preventDefault();
        
        const data = {
            vehicle_no: document.getElementById("vehicle_no").value,
            model_type: document.getElementById("model_type").value,
            rfid_tag: document.getElementById("rfid_tag").value,
            qr_code: document.getElementById("qr_code").value,
            zone: document.getElementById("zone").value
        };

        fetch('/api/entry', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        })
        .then(res => res.json())
        .then(response => {
            alert(response.message);
            document.getElementById("entry-form").reset();
            loadVehicles();
        });
    });
});

function loadVehicles() {
    fetch('/api/vehicles')
    .then(res => res.json())
    .then(data => {
        const tbody = document.getElementById("vehicle-table-body");
        tbody.innerHTML = "";
        let activeCount = 0;

        data.forEach(v => {
            if (v.status === 'PARKED') activeCount++;
            
            const tr = document.createElement("tr");
            tr.innerHTML = `
                <td>${v.id}</td>
                <td>${v.vehicle_no}</td>
                <td>${v.model_type}</td>
                <td>${v.rfid_tag}</td>
                <td>${v.zone}</td>
                <td><b>${v.status}</b></td>
                <td>${v.entry_time}</td>
                <td><span style="color: green;">${v.sap_status}</span></td>
                <td>${v.status === 'PARKED' ? `<button class="exit-btn" onclick="processExit(${v.id})">Exit</button>` : '-'}</td>
            `;
            tbody.appendChild(tr);
        });

        document.getElementById("active-count").innerText = activeCount;
    });
}

function processExit(id) {
    fetch(`/api/exit/${id}`, { method: 'POST' })
    .then(res => res.json())
    .then(response => {
        alert(response.message);
        loadVehicles();
    });
}