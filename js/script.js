// Wait for the DOM to be fully loaded before executing code
document.addEventListener('DOMContentLoaded', function() {
    // Global variables
    let filmsData = [];
    let currentPage = 1;
    const ITEMS_PER_PAGE = 12;
    
    // DOM elements
    const visualizationContainer = document.getElementById('visualization-container');
    const filmsContainer = document.getElementById('films-container');
    const filmTemplate = document.getElementById('film-template');
    const loadingElement = document.getElementById('loading');
    const searchInput = document.getElementById('search');
    const searchBtn = document.getElementById('search-btn');
    const filterYear = document.getElementById('filter-year');
    const filterCountry = document.getElementById('filter-country');
    const sortBy = document.getElementById('sort-by');
    const prevPageBtn = document.getElementById('prev-page');
    const nextPageBtn = document.getElementById('next-page');
    const pageInfo = document.getElementById('page-info');
    
    // Fetch the film data from JSON file
    fetchFilmData();
    
    // Function to fetch film data
    async function fetchFilmData() {
        try {
            showLoading(true);
            
            const response = await fetch('data/films.json');
            if (!response.ok) {
                throw new Error('Failed to fetch data');
            }
            
            filmsData = await response.json();
            console.log('Films data loaded:', filmsData.length, 'films');
            
            // Process data after loading
            processData();
            
        } catch (error) {
            console.error('Error loading films data:', error);
            visualizationContainer.innerHTML = `
                <div class="error-message">
                    <h3>Error Loading Data</h3>
                    <p>Sorry, there was a problem loading the film data. Please try again later.</p>
                </div>
            `;
        } finally {
            showLoading(false);
        }
    }
    
    // Process data, populate filters, and initialize visualization
    function processData() {
        if (!filmsData || filmsData.length === 0) {
            return;
        }
        
        // Populate filters
        populateFilters();
        
        // Initialize visualization
        createVisualization();
        
        // Display films
        displayFilms(filmsData);
        
        // Set up event listeners
        setupEventListeners();
    }
    
    // Function to populate filters
    function populateFilters() {
        // Get unique years
        const years = [...new Set(filmsData.map(film => film.release_year))];
        years.sort((a, b) => b - a); // Sort years in descending order
        
        // Add years to filter
        years.forEach(year => {
            const option = document.createElement('option');
            option.value = year;
            option.textContent = year;
            filterYear.appendChild(option);
        });
        
        // Get unique countries
        const countries = [...new Set(filmsData
            .flatMap(film => film.country ? film.country.split(' ') : [])
            .filter(country => country && country.trim() !== '')
        )];
        countries.sort(); // Sort alphabetically
        
        // Add countries to filter
        countries.forEach(country => {
            const option = document.createElement('option');
            option.value = country;
            option.textContent = country;
            filterCountry.appendChild(option);
        });
    }
    
    // Function to create the data visualization
    function createVisualization() {
        // Clear any existing content
        visualizationContainer.innerHTML = '';
        
        const chartTitle = document.createElement('h2');
        chartTitle.textContent = 'Top 10 Highest Grossing Films';
        visualizationContainer.appendChild(chartTitle);
        
        // Get the top 10 films by box office
        const top10Films = [...filmsData]
            .sort((a, b) => b.box_office - a.box_office)
            .slice(0, 10);
        
        // Create a simple bar chart container
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        visualizationContainer.appendChild(chartContainer);
        
        // Find the maximum box office value for scaling
        const maxBoxOffice = Math.max(...top10Films.map(film => film.box_office));
        
        // Create bars for each film
        top10Films.forEach(film => {
            // Create bar container
            const barContainer = document.createElement('div');
            barContainer.className = 'bar-container';
            
            // Create film title label
            const titleLabel = document.createElement('div');
            titleLabel.className = 'bar-label';
            titleLabel.textContent = `${film.title} (${film.release_year})`;
            
            // Create the bar
            const bar = document.createElement('div');
            bar.className = 'bar';
            const barWidth = (film.box_office / maxBoxOffice * 100) + '%';
            bar.style.width = barWidth;
            
            // Create value label
            const valueLabel = document.createElement('div');
            valueLabel.className = 'bar-value';
            valueLabel.textContent = '$' + (film.box_office / 1000000000).toFixed(2) + 'B';
            
            // Add event listener to show film details
            barContainer.addEventListener('click', () => {
                displayFilmDetails(film);
            });
            
            // Assemble the bar
            barContainer.appendChild(titleLabel);
            barContainer.appendChild(bar);
            bar.appendChild(valueLabel);
            
            // Add to chart
            chartContainer.appendChild(barContainer);
        });
    }
    
    // Function to display films in the grid
    function displayFilms(films, page = 1) {
        currentPage = page;
        filmsContainer.innerHTML = '';
        
        // Calculate pagination
        const totalPages = Math.ceil(films.length / ITEMS_PER_PAGE);
        const start = (page - 1) * ITEMS_PER_PAGE;
        const end = start + ITEMS_PER_PAGE;
        const paginatedFilms = films.slice(start, end);
        
        // Update pagination UI
        pageInfo.textContent = `Page ${page} of ${totalPages || 1}`;
        prevPageBtn.disabled = page <= 1;
        nextPageBtn.disabled = page >= totalPages;
        
        if (paginatedFilms.length === 0) {
            filmsContainer.innerHTML = '<div class="no-results">No films match your search criteria</div>';
            return;
        }
        
        // Create film cards
        paginatedFilms.forEach(film => {
            const filmCard = filmTemplate.content.cloneNode(true);
            
            // Set film data
            filmCard.querySelector('.film-title').textContent = film.title;
            filmCard.querySelector('.film-year span').textContent = film.release_year;
            filmCard.querySelector('.film-director span').textContent = film.director || 'Unknown';
            filmCard.querySelector('.film-box-office span').textContent = formatCurrency(film.box_office);
            filmCard.querySelector('.film-country span').textContent = film.country || 'Unknown';
            
            // Add click event to show details
            const card = filmCard.querySelector('.film-card');
            card.addEventListener('click', () => {
                displayFilmDetails(film);
                
                // Remove active class from all cards
                document.querySelectorAll('.film-card').forEach(c => {
                    c.classList.remove('active');
                });
                
                // Add active class to this card
                card.classList.add('active');
            });
            
            filmsContainer.appendChild(filmCard);
        });
    }
    
    // Function to display film details
    function displayFilmDetails(film) {
        const filmDetailsSection = document.getElementById('film-details');
        filmDetailsSection.innerHTML = `
            <h3>${film.title}</h3>
            <div class="film-detail-content">
                <p><strong>Release Year:</strong> ${film.release_year}</p>
                <p><strong>Director:</strong> ${film.director || 'Unknown'}</p>
                <p><strong>Box Office:</strong> ${formatCurrency(film.box_office)}</p>
                <p><strong>Country:</strong> ${film.country || 'Unknown'}</p>
            </div>
        `;
    }
    
    // Helper function to format currency
    function formatCurrency(value) {
        if (value >= 1000000000) {
            return '$' + (value / 1000000000).toFixed(2) + ' billion';
        } else if (value >= 1000000) {
            return '$' + (value / 1000000).toFixed(2) + ' million';
        } else {
            return '$' + value.toLocaleString();
        }
    }
    
    // Set up event listeners for filters and controls
    function setupEventListeners() {
        // Search functionality
        searchBtn.addEventListener('click', applyFilters);
        searchInput.addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                applyFilters();
            }
        });
        
        // Filter changes
        filterYear.addEventListener('change', applyFilters);
        filterCountry.addEventListener('change', applyFilters);
        sortBy.addEventListener('change', applyFilters);
        
        // Pagination
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                const filteredFilms = getFilteredFilms();
                displayFilms(filteredFilms, currentPage - 1);
            }
        });
        
        nextPageBtn.addEventListener('click', () => {
            const filteredFilms = getFilteredFilms();
            const totalPages = Math.ceil(filteredFilms.length / ITEMS_PER_PAGE);
            if (currentPage < totalPages) {
                displayFilms(filteredFilms, currentPage + 1);
            }
        });
    }
    
    // Function to get filtered films based on current filters
    function getFilteredFilms() {
        const searchTerm = searchInput.value.toLowerCase().trim();
        const selectedYear = filterYear.value;
        const selectedCountry = filterCountry.value;
        const sortOption = sortBy.value;
        
        // Filter films
        let filtered = [...filmsData];
        
        if (searchTerm) {
            filtered = filtered.filter(film => 
                film.title.toLowerCase().includes(searchTerm) || 
                (film.director && film.director.toLowerCase().includes(searchTerm))
            );
        }
        
        if (selectedYear) {
            filtered = filtered.filter(film => film.release_year == selectedYear);
        }
        
        if (selectedCountry) {
            filtered = filtered.filter(film => 
                film.country && film.country.includes(selectedCountry)
            );
        }
        
        // Sort films
        switch(sortOption) {
            case 'box_office_desc':
                filtered.sort((a, b) => b.box_office - a.box_office);
                break;
            case 'box_office_asc':
                filtered.sort((a, b) => a.box_office - b.box_office);
                break;
            case 'year_desc':
                filtered.sort((a, b) => b.release_year - a.release_year);
                break;
            case 'year_asc':
                filtered.sort((a, b) => a.release_year - b.release_year);
                break;
            case 'title_asc':
                filtered.sort((a, b) => a.title.localeCompare(b.title));
                break;
            case 'title_desc':
                filtered.sort((a, b) => b.title.localeCompare(a.title));
                break;
        }
        
        return filtered;
    }
    
    // Apply all filters and update display
    function applyFilters() {
        const filteredFilms = getFilteredFilms();
        displayFilms(filteredFilms, 1); // Reset to first page when filters change
        
        // Update visualization based on filters if less than 20 results
        if (filteredFilms.length > 0 && filteredFilms.length <= 20) {
            updateVisualization(filteredFilms);
        } else {
            // Revert to default visualization
            createVisualization();
        }
    }
    
    // Function to update visualization based on filters
    function updateVisualization(filteredData) {
        // Clear existing visualization
        visualizationContainer.innerHTML = '';
        
        // Create a custom title
        const chartTitle = document.createElement('h2');
        chartTitle.textContent = 'Filtered Films Comparison';
        visualizationContainer.appendChild(chartTitle);
        
        // Create a simple bar chart container
        const chartContainer = document.createElement('div');
        chartContainer.className = 'chart-container';
        visualizationContainer.appendChild(chartContainer);
        
        // Find the maximum box office value for scaling
        const maxBoxOffice = Math.max(...filteredData.map(film => film.box_office));
        
        // Create bars for each film
        filteredData.forEach(film => {
            // Create bar container
            const barContainer = document.createElement('div');
            barContainer.className = 'bar-container';
            
            // Create film title label
            const titleLabel = document.createElement('div');
            titleLabel.className = 'bar-label';
            titleLabel.textContent = `${film.title} (${film.release_year})`;
            
            // Create the bar
            const bar = document.createElement('div');
            bar.className = 'bar';
            const barWidth = (film.box_office / maxBoxOffice * 100) + '%';
            bar.style.width = barWidth;
            
            // Create value label
            const valueLabel = document.createElement('div');
            valueLabel.className = 'bar-value';
            valueLabel.textContent = formatCurrency(film.box_office);
            
            // Add event listener to show film details
            barContainer.addEventListener('click', () => {
                displayFilmDetails(film);
            });
            
            // Assemble the bar
            barContainer.appendChild(titleLabel);
            barContainer.appendChild(bar);
            bar.appendChild(valueLabel);
            
            // Add to chart
            chartContainer.appendChild(barContainer);
        });
    }
    
    // Helper function to show/hide loading indicator
    function showLoading(show) {
        loadingElement.style.display = show ? 'flex' : 'none';
    }
}); 