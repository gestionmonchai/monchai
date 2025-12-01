/**
 * Recherche temps réel générique pour les référentiels
 * Compatible avec tous les types d'entités
 */

class RealtimeSearch {
    constructor(config) {
        this.config = {
            searchInputId: 'quick-search',
            resultsTableId: 'results-table',
            searchInfoId: 'search-info',
            paginationContainerId: 'pagination-container',
            searchIconId: 'search-icon',
            searchSpinnerId: 'search-spinner',
            debounceMs: 300,
            ajaxUrl: config.ajaxUrl,
            entityName: config.entityName,
            ...config
        };
        
        this.searchTimeout = null;
        this.currentController = null;
        
        this.init();
    }
    
    init() {
        this.setupElements();
        this.setupEventListeners();
        this.attachPaginationEvents();
        
        // Focus sur le champ de recherche
        if (this.searchInput) {
            this.searchInput.focus();
        }
        
        console.log(`Recherche temps réel initialisée pour ${this.config.entityName}`);
    }
    
    setupElements() {
        this.searchInput = document.getElementById(this.config.searchInputId);
        this.resultsTable = document.getElementById(this.config.resultsTableId);
        this.searchInfo = document.getElementById(this.config.searchInfoId);
        this.paginationContainer = document.getElementById(this.config.paginationContainerId);
        this.searchIcon = document.getElementById(this.config.searchIconId);
        this.searchSpinner = document.getElementById(this.config.searchSpinnerId);
    }
    
    setupEventListeners() {
        if (!this.searchInput) return;
        
        // Recherche avec debounce
        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(this.searchTimeout);
            
            // Si le champ est vide, recherche immédiate
            if (e.target.value.trim() === '') {
                this.performSearch();
            } else {
                // Debounce pour les autres cas
                this.searchTimeout = setTimeout(() => {
                    this.performSearch();
                }, this.config.debounceMs);
            }
        });
        
        // Recherche immédiate sur Entrée
        this.searchInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                clearTimeout(this.searchTimeout);
                this.performSearch();
            }
        });
    }
    
    performSearch(page = 1) {
        // Annuler la requête précédente
        if (this.currentController) {
            this.currentController.abort();
        }
        this.currentController = new AbortController();
        
        const searchTerm = this.searchInput ? this.searchInput.value.trim() : '';
        
        // Afficher le spinner
        this.showSpinner();
        
        // Construire l'URL
        const params = new URLSearchParams();
        if (searchTerm) {
            params.set('search', searchTerm);
        }
        if (page > 1) {
            params.set('page', page);
        }
        
        const ajaxUrl = `${this.config.ajaxUrl}?${params.toString()}`;
        
        // Faire la requête AJAX
        fetch(ajaxUrl, {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
            },
            signal: this.currentController.signal
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            this.updateResults(data, searchTerm);
            this.attachPaginationEvents();
        })
        .catch(error => {
            if (error.name !== 'AbortError') {
                console.error('Erreur de recherche:', error);
                if (this.searchInfo) {
                    this.searchInfo.innerHTML = '<span class="text-danger">Erreur lors de la recherche</span>';
                }
            }
        })
        .finally(() => {
            this.hideSpinner();
        });
    }
    
    updateResults(data, searchTerm) {
        // Mettre à jour le contenu du tableau
        if (data.html && this.resultsTable) {
            this.resultsTable.innerHTML = data.html;
        }
        
        // Mettre à jour la pagination
        if (data.pagination && this.paginationContainer) {
            this.paginationContainer.innerHTML = data.pagination;
        }
        
        // Mettre à jour les informations de recherche
        if (this.searchInfo) {
            const count = data.count || 0;
            if (searchTerm) {
                this.searchInfo.innerHTML = `${count} résultat${count > 1 ? 's' : ''} pour "${searchTerm}"`;
            } else {
                this.searchInfo.innerHTML = `${count} ${this.config.entityName}${count > 1 ? 's' : ''}`;
            }
        }
    }
    
    attachPaginationEvents() {
        const paginationLinks = document.querySelectorAll('.pagination-link');
        paginationLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const page = link.getAttribute('data-page');
                this.performSearch(parseInt(page));
            });
        });
    }
    
    showSpinner() {
        if (this.searchIcon && this.searchSpinner) {
            this.searchIcon.classList.add('d-none');
            this.searchSpinner.classList.remove('d-none');
        }
    }
    
    hideSpinner() {
        if (this.searchIcon && this.searchSpinner) {
            this.searchIcon.classList.remove('d-none');
            this.searchSpinner.classList.add('d-none');
        }
    }
}

// Export pour utilisation globale
window.RealtimeSearch = RealtimeSearch;
