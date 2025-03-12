// JavaScript для системы управления автопарком

document.addEventListener('DOMContentLoaded', function() {
    console.log("Using base URL:", window.location.origin);
    
    // Загружаем список транспортных средств при загрузке страницы
    fetch('/api/vehicles')
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log("Vehicles loaded:", data);
            displayVehiclesList(data);
        })
        .catch(error => {
            console.error('Error loading vehicles:', error);
            displayErrorMessage('Ошибка загрузки данных. Пожалуйста, обновите страницу.');
        });
});

function createVehicleSelector(vehicles) {
    if (!vehicles || vehicles.length === 0) {
        return '<p class="text-center">Транспортные средства не найдены</p>';
    }
    
    let html = '<div class="list-group">';
    
    vehicles.forEach(vehicle => {
        html += `<a href="#" class="list-group-item list-group-item-action vehicle-item" 
                    data-id="${vehicle.id}" onclick="loadVehicleData(${vehicle.id})">
                    ${vehicle.model} (${vehicle.reg_number})
                </a>`;
    });
    
    html += '</div>';
    return html;
}

function loadVehicleData(vehicleId) {
    // Подсвечиваем выбранное ТС
    document.querySelectorAll('.vehicle-item').forEach(item => {
        item.classList.remove('active');
    });
    document.querySelector(`.vehicle-item[data-id="${vehicleId}"]`).classList.add('active');
    
    // Загружаем данные о ТС
    fetch(`/api/vehicle/${vehicleId}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            console.log("Vehicle info loaded:", data);
            displayVehicleInfo(data);
        })
        .catch(error => {
            console.error('Error loading vehicle info:', error);
            document.getElementById('vehicle-info').innerHTML = 
                '<div class="alert alert-danger">Ошибка загрузки данных ТС</div>';
        });
    
    // Загружаем историю обслуживания
    fetch(`/api/maintenance/${vehicleId}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            console.log("Maintenance data loaded:", data);
            displayMaintenanceHistory(data);
        })
        .catch(error => {
            console.error('Error loading maintenance history:', error);
            document.getElementById('maintenance-history').innerHTML = 
                '<div class="alert alert-danger">Ошибка загрузки истории обслуживания</div>';
        });
    
    // Загружаем статистику по топливу
    fetch(`/api/fuel/${vehicleId}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            console.log("Fuel data loaded:", data);
            displayFuelStats(data);
        })
        .catch(error => {
            console.error('Error loading fuel stats:', error);
            document.getElementById('fuel-stats').innerHTML = 
                '<div class="alert alert-danger">Ошибка загрузки данных по топливу</div>';
        });
}

function displayVehicleInfo(vehicle) {
    let infoHtml = `
        <div class="vehicle-card">
            <h4>${vehicle.model} <span class="badge bg-secondary">${vehicle.reg_number}</span></h4>
            <div class="row">
                <div class="col-md-6">
                    <p><strong>VIN:</strong> ${vehicle.vin || 'Не указан'}</p>
                    <p><strong>Категория:</strong> ${vehicle.category || 'Не указана'}</p>
                    <p><strong>Тип:</strong> ${vehicle.qualification || 'Не указан'}</p>
                    <p><strong>Год выпуска:</strong> ${vehicle.year || 'Не указан'}</p>
                    <p><strong>Текущий пробег:</strong> ${vehicle.mileage || 0} км</p>
                </div>
                <div class="col-md-6">
                    <p><strong>Тахограф:</strong> ${vehicle.tachograph_required ? 'Требуется' : 'Не требуется'}</p>
                    <p><strong>ОСАГО до:</strong> ${vehicle.osago_valid || 'Не указано'}</p>
                    <p><strong>Тех. осмотр до:</strong> ${vehicle.tech_inspection_valid || 'Не указано'}</p>
                    <p><strong>СКЗИ до:</strong> ${vehicle.skzi_valid_date || 'Не требуется'}</p>
                    <p><strong>Следующее ТО:</strong> ${vehicle.next_to_date || 'Не указано'}</p>
                </div>
            </div>
        </div>`;
    
    document.getElementById('vehicle-info').innerHTML = infoHtml;
}

function parseDate(dateStr) {
    if (!dateStr) return null;
    
    // Парсинг даты в формате DD.MM.YYYY
    const parts = dateStr.split('.');
    if (parts.length !== 3) return null;
    
    return new Date(parts[2], parts[1] - 1, parts[0]);
}

function displayMaintenanceHistory(data) {
    const maintenance = data.maintenance || [];
    const repairs = data.repairs || [];
    
    let historyHtml = '';
    
    if (maintenance.length === 0 && repairs.length === 0) {
        historyHtml = '<p class="text-center">История обслуживания отсутствует</p>';
    } else {
        if (maintenance.length > 0) {
            historyHtml += `
                <h5>Техническое обслуживание</h5>
                <div class="table-responsive">
                    <table class="table table-sm table-hover">
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Пробег</th>
                                <th>Выполненные работы</th>
                            </tr>
                        </thead>
                        <tbody>`;
            
            maintenance.forEach(item => {
                historyHtml += `
                    <tr>
                        <td>${item.date}</td>
                        <td>${item.mileage} км</td>
                        <td>${item.works}</td>
                    </tr>`;
            });
            
            historyHtml += `
                        </tbody>
                    </table>
                </div>`;
        }
        
        if (repairs.length > 0) {
            historyHtml += `
                <h5 class="mt-3">Ремонты</h5>
                <div class="table-responsive">
                    <table class="table table-sm table-hover">
                        <thead>
                            <tr>
                                <th>Дата</th>
                                <th>Пробег</th>
                                <th>Описание</th>
                                <th>Стоимость</th>
                            </tr>
                        </thead>
                        <tbody>`;
            
            repairs.forEach(item => {
                historyHtml += `
                    <tr>
                        <td>${item.date}</td>
                        <td>${item.mileage} км</td>
                        <td>${item.description}</td>
                        <td>${item.cost ? item.cost.toLocaleString() + ' ₽' : 'Не указана'}</td>
                    </tr>`;
            });
            
            historyHtml += `
                        </tbody>
                    </table>
                </div>`;
        }
    }
    
    document.getElementById('maintenance-history').innerHTML = historyHtml;
}

function displayFuelStats(data) {
    console.log("Fuel stats:", data);
    const refueling = data.refueling || [];
    const stats = data.stats || {};
    
    let fuelHtml = '';
    
    if (refueling.length === 0) {
        fuelHtml = '<p class="text-center">Данные о заправках отсутствуют</p>';
    } else {
        // Показываем общую статистику
        fuelHtml += `
            <div class="row mb-3">
                <div class="col-md-4">
                    <div class="stats-box text-center">
                        <h5>Общий расход</h5>
                        <h4>${stats.total_fuel_liters?.toFixed(1) || 0} л</h4>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-box text-center">
                        <h5>Средний расход</h5>
                        <h4>${stats.avg_consumption?.toFixed(1) || 'Н/Д'} л/100км</h4>
                    </div>
                </div>
                <div class="col-md-4">
                    <div class="stats-box text-center">
                        <h5>Средняя цена</h5>
                        <h4>${stats.avg_cost_per_liter?.toFixed(1) || 0} ₽/л</h4>
                    </div>
                </div>
            </div>`;
        
        // Показываем историю заправок
        fuelHtml += `
            <h5>История заправок</h5>
            <div class="table-responsive">
                <table class="table table-sm table-hover">
                    <thead>
                        <tr>
                            <th>Дата</th>
                            <th>Пробег</th>
                            <th>Литры</th>
                            <th>Цена за литр</th>
                            <th>Сумма</th>
                        </tr>
                    </thead>
                    <tbody>`;
        
        refueling.forEach(item => {
            const total = (item.liters * item.cost_per_liter).toFixed(1);
            fuelHtml += `
                <tr>
                    <td>${item.date}</td>
                    <td>${item.mileage} км</td>
                    <td>${item.liters} л</td>
                    <td>${item.cost_per_liter} ₽</td>
                    <td>${total} ₽</td>
                </tr>`;
        });
        
        fuelHtml += `
                    </tbody>
                </table>
            </div>`;
    }
    
    document.getElementById('fuel-stats').innerHTML = fuelHtml;
}

function displayNoVehiclesMessage() {
    document.getElementById('vehicle-list').innerHTML = 
        '<p class="text-center">Транспортные средства не найдены</p>';
    
    document.getElementById('vehicle-info').innerHTML = 
        '<p class="text-center">Нет данных для отображения</p>';
    
    document.getElementById('maintenance-history').innerHTML = 
        '<p class="text-center">Нет данных для отображения</p>';
    
    document.getElementById('fuel-stats').innerHTML = 
        '<p class="text-center">Нет данных для отображения</p>';
}

function displayErrorMessage(message) {
    document.getElementById('vehicle-list').innerHTML = 
        `<div class="alert alert-danger">${message}</div>`;
}

function displayVehiclesList(vehicles) {
    if (!vehicles || vehicles.length === 0) {
        displayNoVehiclesMessage();
        return;
    }
    
    document.getElementById('vehicle-list').innerHTML = createVehicleSelector(vehicles);
    
    // Автоматически загружаем данные первого ТС
    if (vehicles.length > 0) {
        loadVehicleData(vehicles[0].id);
    }
}