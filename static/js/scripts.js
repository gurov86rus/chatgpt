document.addEventListener('DOMContentLoaded', function() {
    // Determine the base URL
    const baseUrl = location.hostname.includes('replit') ? 
                   location.origin : // If on replit, use the current origin
                   ''; // Otherwise use relative path (for local development)
    
    console.log('Using base URL:', baseUrl);
    
    // Store vehicles list globally to use it later
    let vehiclesList = [];
    
    // Load vehicles list first with proper error handling
    fetch(`${baseUrl}/api/vehicles`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(vehicles => {
            console.log('Vehicles loaded:', vehicles);
            vehiclesList = vehicles; // Store vehicles globally
            
            if (vehicles && vehicles.length > 0) {
                // Select the first vehicle by default
                loadVehicleData(vehicles[0].id);
                
                // Create vehicle selector if there are multiple vehicles
                if (vehicles.length > 1) {
                    createVehicleSelector(vehicles);
                }
                
                // Add event listener for "Show All Vehicles" button
                const showAllBtn = document.getElementById('showAllVehiclesBtn');
                if (showAllBtn) {
                    showAllBtn.addEventListener('click', function() {
                        displayVehiclesList(vehicles);
                    });
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
    // Get the base URL from the top level scope
    const baseUrl = location.hostname.includes('replit') ? 
                  location.origin : // If on replit, use the current origin
                  ''; // Otherwise use relative path (for local development)
    
    // Reset the main content to show vehicle details instead of list view
    const mainContent = document.querySelector('.container.mt-4');
    
    // Restore the original HTML structure for vehicle details
    mainContent.innerHTML = `
        <!-- Vehicle Info Card -->
        <div class="card mb-4">
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0" id="vehicle-title">Загрузка данных...</h5>
            </div>
            <div class="card-body">
                <div class="row">
                    <div class="col-md-6">
                        <h6 class="mb-3">Основная информация</h6>
                        <ul class="list-group mb-3">
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>VIN:</strong> <span id="vin">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>Категория:</strong> <span id="category">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>Квалификация:</strong> <span id="qualification">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>Пробег:</strong> <span id="mileage">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>Тахограф:</strong> <span id="tachograph">Загрузка...</span>
                            </li>
                        </ul>
                    </div>
                    <div class="col-md-6">
                        <h6 class="mb-3">Даты и документы</h6>
                        <ul class="list-group mb-3">
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>ОСАГО до:</strong> <span id="osago">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>Техосмотр до:</strong> <span id="techInspection">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>СКЗИ до:</strong> <span id="skzi">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>Последнее ТО:</strong> <span id="lastTo">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>Следующее ТО:</strong> <span id="nextTo">Загрузка...</span>
                            </li>
                            <li class="list-group-item d-flex justify-content-between">
                                <strong>Осталось до ТО:</strong> <span id="remainingKm">Загрузка...</span>
                            </li>
                        </ul>
                    </div>
                </div>
                
                <div class="mt-3">
                    <h6 class="mb-3">Информация о топливе</h6>
                    <div class="row">
                        <div class="col-md-6">
                            <ul class="list-group">
                                <li class="list-group-item d-flex justify-content-between">
                                    <strong>Тип топлива:</strong> <span id="fuelType">Загрузка...</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <strong>Объем бака:</strong> <span id="tankCapacity">Загрузка...</span>
                                </li>
                            </ul>
                        </div>
                        <div class="col-md-6">
                            <ul class="list-group">
                                <li class="list-group-item d-flex justify-content-between">
                                    <strong>Средний расход:</strong> <span id="avgConsumption">Загрузка...</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between">
                                    <strong>Примечания:</strong> <span id="notes">Загрузка...</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Maintenance History Card -->
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">История технического обслуживания</h5>
            </div>
            <div class="card-body">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Дата</th>
                            <th>Пробег</th>
                            <th>Выполненные работы</th>
                        </tr>
                    </thead>
                    <tbody id="toHistoryTable">
                        <tr>
                            <td colspan="3" class="text-center">Загрузка данных...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Repairs Card -->
        <div class="card mb-4">
            <div class="card-header bg-primary text-white">
                <h5 class="mb-0">История ремонтов</h5>
            </div>
            <div class="card-body">
                <div id="no-repairs" class="alert alert-info d-none">Нет записей о ремонтах</div>
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Дата</th>
                            <th>Пробег</th>
                            <th>Описание работ</th>
                            <th>Стоимость</th>
                        </tr>
                    </thead>
                    <tbody id="repairsTable">
                        <tr>
                            <td colspan="4" class="text-center">Загрузка данных...</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
        
        <!-- Vehicle List Button -->
        <div class="text-center mb-5" id="vehicleListButtonContainer">
            <button class="btn btn-primary" id="showAllVehiclesBtn">
                <i class="bi bi-list"></i> Показать список всех машин
            </button>
        </div>
    `;
    
    // Re-add event listener for the "Show All Vehicles" button
    const showAllBtn = document.getElementById('showAllVehiclesBtn');
    if (showAllBtn) {
        showAllBtn.addEventListener('click', function() {
            // Get the global vehicles list by making a new request
            fetch(`${baseUrl}/api/vehicles`)
                .then(response => response.json())
                .then(vehicles => {
                    displayVehiclesList(vehicles);
                })
                .catch(error => {
                    console.error('Error loading vehicles list:', error);
                });
        });
    }
    
    // Load vehicle info
    fetch(`${baseUrl}/api/vehicle/${vehicleId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Vehicle info loaded:', data);
            displayVehicleInfo(data);
            
            // Also load maintenance history
            return fetch(`${baseUrl}/api/maintenance/${vehicleId}`);
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Maintenance data loaded:', data);
            displayMaintenanceHistory(data);
            
            // Also load fuel history
            return fetch(`${baseUrl}/api/fuel/${vehicleId}`);
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Fuel data loaded:', data);
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
    document.getElementById('category').textContent = vehicle.category || 'Не указано';
    document.getElementById('qualification').textContent = vehicle.qualification || 'Не указано';
    document.getElementById('mileage').textContent = `${vehicle.mileage} км`;
    document.getElementById('lastTo').textContent = vehicle.last_to_date || 'Не указано';
    
    // Format next maintenance info
    let nextToText = 'Не указано';
    if (vehicle.next_to_date && vehicle.next_to) {
        nextToText = `${vehicle.next_to_date} (${vehicle.next_to} км)`;
    }
    document.getElementById('nextTo').textContent = nextToText;
    
    // Vehicle documents info
    document.getElementById('osago').textContent = vehicle.osago_valid || 'Не указано';
    document.getElementById('techInspection').textContent = vehicle.tech_inspection_valid || 'Не указано';
    document.getElementById('skzi').textContent = vehicle.skzi_valid_date || 'Не указано';
    document.getElementById('tachograph').textContent = vehicle.tachograph_required ? '✅ Требуется' : '❌ Не требуется';
    
    // Fuel info
    document.getElementById('fuelType').textContent = vehicle.fuel_type || 'Не указано';
    document.getElementById('tankCapacity').textContent = vehicle.fuel_tank_capacity ? `${vehicle.fuel_tank_capacity} л` : 'Не указано';
    document.getElementById('avgConsumption').textContent = vehicle.avg_fuel_consumption ? `${vehicle.avg_fuel_consumption} л/100 км` : 'Не указано';
    document.getElementById('notes').textContent = vehicle.notes || 'Нет';
    
    // Remaining km to next maintenance
    let remainingText = 'Не указано';
    if (vehicle.remaining_km !== null) {
        remainingText = `${vehicle.remaining_km} км`;
    }
    document.getElementById('remainingKm').textContent = remainingText;
    
    // Alerts container
    const alertsContainer = document.createElement('div');
    alertsContainer.className = 'alerts-container mt-3';
    document.querySelector('.card-body').appendChild(alertsContainer);
    
    // Maintenance alert
    if (vehicle.remaining_km !== null && vehicle.remaining_km < 1000) {
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-warning';
        alertDiv.innerHTML = `⚠️ <strong>Внимание!</strong> До следующего ТО осталось менее 1000 км.`;
        alertsContainer.appendChild(alertDiv);
    }
    
    // OSAGO alert
    if (vehicle.osago_valid) {
        const today = new Date();
        const osagoDate = parseDate(vehicle.osago_valid);
        const differenceInDays = Math.ceil((osagoDate - today) / (1000 * 60 * 60 * 24));
        
        if (differenceInDays <= 30 && differenceInDays > 0) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-warning';
            alertDiv.innerHTML = `⚠️ <strong>Внимание!</strong> Срок действия ОСАГО истекает через ${differenceInDays} дней.`;
            alertsContainer.appendChild(alertDiv);
        } else if (differenceInDays <= 0) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger';
            alertDiv.innerHTML = `⚠️ <strong>ВНИМАНИЕ!</strong> Срок действия ОСАГО истек!`;
            alertsContainer.appendChild(alertDiv);
        }
    }
    
    // Tech inspection alert
    if (vehicle.tech_inspection_valid) {
        const today = new Date();
        const techDate = parseDate(vehicle.tech_inspection_valid);
        const differenceInDays = Math.ceil((techDate - today) / (1000 * 60 * 60 * 24));
        
        if (differenceInDays <= 30 && differenceInDays > 0) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-warning';
            alertDiv.innerHTML = `⚠️ <strong>Внимание!</strong> Срок действия техосмотра истекает через ${differenceInDays} дней.`;
            alertsContainer.appendChild(alertDiv);
        } else if (differenceInDays <= 0) {
            const alertDiv = document.createElement('div');
            alertDiv.className = 'alert alert-danger';
            alertDiv.innerHTML = `⚠️ <strong>ВНИМАНИЕ!</strong> Срок действия техосмотра истек!`;
            alertsContainer.appendChild(alertDiv);
        }
    }
}

// Helper function to parse date in format DD.MM.YYYY
function parseDate(dateStr) {
    if (!dateStr) return null;
    
    // Check if format is DD.MM.YYYY
    if (dateStr.indexOf('.') !== -1) {
        const parts = dateStr.split('.');
        if (parts.length === 3) {
            return new Date(parts[2], parts[1] - 1, parts[0]);
        }
    }
    
    // Check if format is YYYY-MM-DD
    if (dateStr.indexOf('-') !== -1) {
        return new Date(dateStr);
    }
    
    return new Date(dateStr);
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

function displayVehiclesList(vehicles) {
    // Get the main content container
    const container = document.querySelector('.container.mt-4');
    
    // Clear current content
    container.innerHTML = '';
    
    // Create a card for the vehicle list
    const card = document.createElement('div');
    card.className = 'card mb-4';
    
    // Create card header
    const cardHeader = document.createElement('div');
    cardHeader.className = 'card-header bg-primary text-white';
    cardHeader.innerHTML = '<h5 class="mb-0">Список всех автомобилей</h5>';
    card.appendChild(cardHeader);
    
    // Create card body
    const cardBody = document.createElement('div');
    cardBody.className = 'card-body';
    
    // Create table
    const table = document.createElement('table');
    table.className = 'table table-striped table-hover';
    
    // Create table header
    const tableHeader = document.createElement('thead');
    tableHeader.innerHTML = `
        <tr>
            <th>Модель</th>
            <th>Гос. номер</th>
            <th>Категория</th>
            <th>Пробег</th>
            <th>Срок ОСАГО</th>
            <th>Действия</th>
        </tr>
    `;
    table.appendChild(tableHeader);
    
    // Create table body and add vehicle rows
    const tableBody = document.createElement('tbody');
    
    vehicles.forEach(vehicle => {
        const row = document.createElement('tr');
        
        // Calculate days until OSAGO expiration
        let osagoStatus = '';
        if (vehicle.osago_valid) {
            const today = new Date();
            const osagoDate = parseDate(vehicle.osago_valid);
            const differenceInDays = Math.ceil((osagoDate - today) / (1000 * 60 * 60 * 24));
            
            if (differenceInDays <= 0) {
                osagoStatus = `<span class="badge bg-danger">Просрочено</span>`;
            } else if (differenceInDays <= 30) {
                osagoStatus = `<span class="badge bg-warning text-dark">Осталось ${differenceInDays} дней</span>`;
            } else {
                osagoStatus = `<span class="badge bg-success">Действует</span>`;
            }
        } else {
            osagoStatus = '<span class="badge bg-secondary">Нет данных</span>';
        }
        
        row.innerHTML = `
            <td>${vehicle.model}</td>
            <td>${vehicle.reg_number}</td>
            <td>${vehicle.category || 'Не указана'}</td>
            <td>${vehicle.mileage} км</td>
            <td>${vehicle.osago_valid || 'Не указано'} ${osagoStatus}</td>
            <td>
                <button class="btn btn-sm btn-primary view-vehicle" data-id="${vehicle.id}">
                    <i class="bi bi-eye"></i> Просмотр
                </button>
            </td>
        `;
        tableBody.appendChild(row);
    });
    
    table.appendChild(tableBody);
    cardBody.appendChild(table);
    card.appendChild(cardBody);
    
    // Add a button to go back
    const backButton = document.createElement('div');
    backButton.className = 'text-center mb-4';
    backButton.innerHTML = `
        <button class="btn btn-secondary" id="backToVehicleBtn">
            <i class="bi bi-arrow-left"></i> Вернуться к детальной информации
        </button>
    `;
    
    // Add elements to container
    container.appendChild(card);
    container.appendChild(backButton);
    
    // Add event listeners for buttons
    document.querySelectorAll('.view-vehicle').forEach(button => {
        button.addEventListener('click', function() {
            const vehicleId = this.getAttribute('data-id');
            loadVehicleData(vehicleId);
        });
    });
    
    document.getElementById('backToVehicleBtn').addEventListener('click', function() {
        // Load the first vehicle
        if (vehicles.length > 0) {
            loadVehicleData(vehicles[0].id);
        }
    });
}