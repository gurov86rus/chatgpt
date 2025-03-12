document.addEventListener('DOMContentLoaded', function() {
    // Load vehicle information
    fetch('/api/vehicle-info')
        .then(response => response.json())
        .then(data => {
            document.getElementById('vehicle-title').textContent = `${data.model} (${data.number})`;
            document.getElementById('vin').textContent = data.vin;
            document.getElementById('mileage').textContent = `${data.mileage} км`;
            document.getElementById('lastTo').textContent = `${data.last_to} (${data.next_to - 10000} км)`;
            document.getElementById('nextTo').textContent = `${data.next_to_date} (через ${data.remaining_km} км)`;
            document.getElementById('osago').textContent = data.osago_valid;
            document.getElementById('tachograph').textContent = data.tachograph_required ? '✔ Требуется' : '❌ Не требуется';
            document.getElementById('remainingKm').textContent = `${data.remaining_km} км`;
        })
        .catch(error => console.error('Error fetching vehicle data:', error));

    // Load maintenance history
    fetch('/api/maintenance-history')
        .then(response => response.json())
        .then(data => {
            // Populate maintenance history table
            const toHistoryTable = document.getElementById('toHistoryTable');
            toHistoryTable.innerHTML = '';
            
            data.to_history.forEach(record => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${record.date}</td>
                    <td>${record.mileage} км</td>
                    <td>${record.works}</td>
                `;
                toHistoryTable.appendChild(row);
            });
            
            // Populate repairs table
            const repairsTable = document.getElementById('repairsTable');
            repairsTable.innerHTML = '';
            
            if (data.repairs && data.repairs.length > 0) {
                data.repairs.forEach(repair => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${repair.date}</td>
                        <td>${repair.mileage} км</td>
                        <td>${repair.repair}</td>
                        <td>${repair.cost} руб.</td>
                    `;
                    repairsTable.appendChild(row);
                });
                document.getElementById('no-repairs').classList.add('d-none');
            } else {
                document.getElementById('no-repairs').classList.remove('d-none');
            }
        })
        .catch(error => console.error('Error fetching maintenance history:', error));
});