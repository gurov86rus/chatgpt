document.addEventListener('DOMContentLoaded', function() {
    // Load vehicles list first
    fetch('/api/vehicles')
        .then(response => response.json())
        .then(vehicles => {
            if (vehicles && vehicles.length > 0) {
                // Select the first vehicle by default
                loadVehicleData(vehicles[0].id);
                
                // Create vehicle selector if there are multiple vehicles
                if (vehicles.length > 1) {
                    createVehicleSelector(vehicles);
                }
            } else {
                // No vehicles found
                displayNoVehiclesMessage();
            }
        })
        .catch(error => {
            console.error('Error loading vehicles:', error);
            displayErrorMessage();
        });
});

function createVehicleSelector(vehicles) {
    // Create a dropdown for vehicle selection
    const navbarContainer = document.querySelector('.navbar .container');
    
    // Create a vehicle selector dropdown
    const selectorContainer = document.createElement('div');
    selectorContainer.className = 'dropdown ms-auto';
    
    const dropdownButton = document.createElement('button');
    dropdownButton.className = 'btn btn-outline-light dropdown-toggle';
    dropdownButton.type = 'button';
    dropdownButton.setAttribute('data-bs-toggle', 'dropdown');
    dropdownButton.textContent = 'Выбор автомобиля';
    
    const dropdownMenu = document.createElement('ul');
    dropdownMenu.className = 'dropdown-menu dropdown-menu-end';
    
    // Add vehicles to dropdown
    vehicles.forEach(vehicle => {
        const item = document.createElement('li');
        const link = document.createElement('a');
        link.className = 'dropdown-item';
        link.href = '#';
        link.textContent = `${vehicle.model} (${vehicle.reg_number})`;
        link.onclick = (e) => {
            e.preventDefault();
            loadVehicleData(vehicle.id);
        };
        item.appendChild(link);
        dropdownMenu.appendChild(item);
    });
    
    selectorContainer.appendChild(dropdownButton);
    selectorContainer.appendChild(dropdownMenu);
    navbarContainer.appendChild(selectorContainer);
}

function loadVehicleData(vehicleId) {
    // Load vehicle info
    fetch(`/api/vehicle/${vehicleId}`)
        .then(response => response.json())
        .then(data => {
            displayVehicleInfo(data);
            
            // Also load maintenance history
            return fetch(`/api/maintenance/${vehicleId}`);
        })
        .then(response => response.json())
        .then(data => {
            displayMaintenanceHistory(data);
            
            // Also load fuel history
            return fetch(`/api/fuel/${vehicleId}`);
        })
        .then(response => response.json())
        .then(data => {
            displayFuelStats(data);
        })
        .catch(error => {
            console.error('Error loading data:', error);
            displayErrorMessage();
        });
}

function displayVehicleInfo(vehicle) {
    // Update page title
    document.title = `${vehicle.model} (${vehicle.reg_number}) - Система учета обслуживания`;
    
    // Update vehicle info in the UI
    document.getElementById('vehicle-title').textContent = `${vehicle.model} (${vehicle.reg_number})`;
    document.getElementById('vin').textContent = vehicle.vin || 'Не указан';
    document.getElementById('mileage').textContent = `${vehicle.mileage} км`;
    document.getElementById('lastTo').textContent = vehicle.last_to_date || 'Не указано';
    
    // Format next maintenance info
    let nextToText = 'Не указано';
    if (vehicle.next_to_date && vehicle.next_to) {
        nextToText = `${vehicle.next_to_date} (${vehicle.next_to} км)`;
    }
    document.getElementById('nextTo').textContent = nextToText;
    
    // Other vehicle info
    document.getElementById('osago').textContent = vehicle.osago_valid || 'Не указано';
    document.getElementById('tachograph').textContent = vehicle.tachograph_required ? '✅ Требуется' : '❌ Не требуется';
    
    // Remaining km to next maintenance
    let remainingText = 'Не указано';
    if (vehicle.remaining_km !== null) {
        remainingText = `${vehicle.remaining_km} км`;
    }
    document.getElementById('remainingKm').textContent = remainingText;
    
    // Maintenance alert
    if (vehicle.remaining_km !== null && vehicle.remaining_km < 1000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning mt-3';
        alertDiv.innerHTML = `⚠️ <strong>Внимание!</strong> До следующего ТО осталось менее 1000 км.`;
        document.querySelector('.card-body').appendChild(alertDiv);
    }
}

function displayMaintenanceHistory(data) {
    const maintenanceTable = document.getElementById('toHistoryTable');
    const repairsTable = document.getElementById('repairsTable');
    
    // Clear tables
    maintenanceTable.innerHTML = '';
    repairsTable.innerHTML = '';
    
    // Display maintenance records
    if (data.maintenance && data.maintenance.length > 0) {
        data.maintenance.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.date}</td>
                <td>${record.mileage} км</td>
                <td>${record.works}</td>
            `;
            maintenanceTable.appendChild(row);
        });
    } else {
        // No maintenance records
        const row = document.createElement('tr');
        row.innerHTML = `<td colspan="3" class="text-center">Нет записей о техническом обслуживании.</td>`;
        maintenanceTable.appendChild(row);
    }
    
    // Display repair records
    if (data.repairs && data.repairs.length > 0) {
        data.repairs.forEach(repair => {
            const row = document.createElement('tr');
            const cost = repair.cost ? `${repair.cost} руб.` : 'Не указана';
            row.innerHTML = `
                <td>${repair.date}</td>
                <td>${repair.mileage} км</td>
                <td>${repair.description}</td>
                <td>${cost}</td>
            `;
            repairsTable.appendChild(row);
        });
    } else {
        // Show no repairs message
        document.getElementById('no-repairs').classList.remove('d-none');
    }
}

function displayFuelStats(data) {
    // We could add a section for fuel stats if needed
    // For now, just log them to console
    console.log('Fuel stats:', data);
}

function displayNoVehiclesMessage() {
    const container = document.querySelector('.container.mt-4');
    container.innerHTML = `
        <div class="alert alert-info" role="alert">
            <h4 class="alert-heading">Нет автомобилей в системе</h4>
            <p>Для начала работы добавьте автомобиль через Telegram бота: <a href="https://t.me/check_vin_avtobot" target="_blank">@check_vin_avtobot</a></p>
        </div>
    `;
}

function displayErrorMessage() {
    const container = document.querySelector('.container.mt-4');
    container.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <h4 class="alert-heading">Ошибка загрузки данных</h4>
            <p>Не удалось загрузить информацию об автомобилях. Пожалуйста, попробуйте позже или обратитесь к администратору.</p>
        </div>
    `;
}