/**
 * STOCK BLINX - MAIN APPLICATION LOGIC
 * WhatsApp Admin: 62882003619577
 */

const ADMIN_WA = "62882003619577";
const ITEMS_PER_PAGE = 60;

// Application State
let allStockItems = [];
let filteredItems = [];
let selectedNumbers = new Set();
let favoriteNumbers = new Set(JSON.parse(localStorage.getItem('blinx_fav_numbers') || '[]'));

let currentCategory = 'ALL';
let currentSearchQuery = '';
let currentDigitFilter = '';
let currentSort = 'tier';
let currentPage = 1;

// Category tier ranking for sorting
const TIER_ORDER = {
    'SSS TIER (6x digit berulang)': 1,
    'SS TIER (5x digit berulang)': 2,
    '(URUT)': 3,
    'S TIER (4x digit berulang)': 4
};

// DOM Elements
const DOM = {
    headerStockCount: document.getElementById('header-stock-count'),
    totalHeroStock: document.getElementById('total-hero-stock'),
    countSSS: document.getElementById('count-sss'),
    countSS: document.getElementById('count-ss'),
    countUrut: document.getElementById('count-urut'),
    countS: document.getElementById('count-s'),
    
    searchInput: document.getElementById('search-input'),
    btnClearSearch: document.getElementById('btn-clear-search'),
    categoryTabs: document.getElementById('category-tabs'),
    sortSelect: document.getElementById('sort-select'),
    
    tabCountAll: document.getElementById('tab-count-all'),
    tabCountSSS: document.getElementById('tab-count-sss'),
    tabCountSS: document.getElementById('tab-count-ss'),
    tabCountUrut: document.getElementById('tab-count-urut'),
    tabCountS: document.getElementById('tab-count-s'),
    tabCountFav: document.getElementById('tab-count-fav'),

    showingCount: document.getElementById('showing-count'),
    activeFilterText: document.getElementById('active-filter-text'),
    btnSelectAll: document.getElementById('btn-select-all'),
    btnUnselectAll: document.getElementById('btn-unselect-all'),

    stockGrid: document.getElementById('stock-grid'),
    loadingState: document.getElementById('loading-state'),
    emptyState: document.getElementById('empty-state'),
    paginationControls: document.getElementById('pagination-controls'),
    btnPrevPage: document.getElementById('btn-prev-page'),
    btnNextPage: document.getElementById('btn-next-page'),
    pageInfo: document.getElementById('page-info'),

    bulkBar: document.getElementById('bulk-bar'),
    bulkCount: document.getElementById('bulk-count'),
    btnCopyBulk: document.getElementById('btn-copy-bulk'),
    btnOrderBulk: document.getElementById('btn-order-bulk'),

    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message')
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await loadStockData();
    renderStats();
    applyFiltersAndSort();
}

/**
 * Fetch Stock Data from /api/stock or fallback to window.STOCK_DATA / all.txt
 */
async function loadStockData() {
    showLoading(true);
    try {
        // First attempt: API endpoint
        const response = await fetch('/api/stock');
        if (response.ok) {
            allStockItems = await response.json();
            console.log('Loaded stock data via API:', allStockItems.length);
        } else {
            throw new Error('API not available');
        }
    } catch (e) {
        console.warn('API fetch failed, trying static file fallback...', e);
        try {
            // Second attempt: parse /RAPI/all.txt directly
            const txtResponse = await fetch('../RAPI/all.txt');
            if (txtResponse.ok) {
                const text = await txtResponse.text();
                allStockItems = parseAllTxt(text);

                try {
                    const soldResponse = await fetch('../RAPI/sold.txt');
                    if (soldResponse.ok) {
                        const soldText = await soldResponse.text();
                        const soldItems = parseSoldTxt(soldText);
                        allStockItems = [...allStockItems, ...soldItems];
                    }
                } catch (errSold) {
                    console.warn('Fallback sold.txt fetch failed:', errSold);
                }

                console.log('Loaded stock data from all.txt & sold.txt:', allStockItems.length);
            } else {
                throw new Error('File fetch failed');
            }
        } catch (err) {
            console.warn('Static file fetch failed, using window.STOCK_DATA fallback.');
            if (window.STOCK_DATA && Array.isArray(window.STOCK_DATA)) {
                allStockItems = window.STOCK_DATA;
            }
        }
    }
    showLoading(false);
}

/**
 * Parse raw all.txt string into item objects
 */
function parseAllTxt(rawText) {
    const lines = rawText.split('\n');
    const items = [];
    let currentCat = 'S TIER (4x digit berulang)';

    lines.forEach(line => {
        line = line.strip ? line.strip() : line.trim();
        if (!line) return;

        if (line.startsWith('---')) {
            currentCat = line.replace(/^-+\s*/, '').replace(/\s*-+$/, '').trim();
        } else {
            items.push({
                number: line,
                category: currentCat,
                status: 'AVAILABLE'
            });
        }
    });

    return items;
}

/**
 * Parse raw sold.txt string into item objects
 */
function parseSoldTxt(rawText) {
    const lines = rawText.split('\n');
    const items = [];

    lines.forEach(line => {
        line = line.trim();
        if (!line || line.startsWith('#')) return;

        if (line.includes('|')) {
            const parts = line.split('|');
            items.push({
                number: parts[0].trim(),
                category: parts[1].trim(),
                status: 'SOLD'
            });
        } else if (!line.startsWith('---')) {
            items.push({
                number: line,
                category: determineTier(line),
                status: 'SOLD'
            });
        }
    });

    return items;
}

function determineTier(numStr) {
    for (let d = 0; d < 10; d++) {
        if (numStr.includes(String(d).repeat(6))) return 'SSS TIER (6x digit berulang)';
    }
    for (let d = 0; d < 10; d++) {
        if (numStr.includes(String(d).repeat(5))) return 'SS TIER (5x digit berulang)';
    }
    return 'S TIER (4x digit berulang)';
}

/**
 * Update stats and counts across header and tabs
 */
function renderStats() {
    const total = allStockItems.length;
    DOM.headerStockCount.textContent = `${total.toLocaleString()} Stock Ready`;
    DOM.totalHeroStock.textContent = `${total.toLocaleString()}+`;

    const counts = {
        sss: 0,
        ss: 0,
        urut: 0,
        s: 0
    };

    allStockItems.forEach(item => {
        if (item.category.includes('SSS TIER')) counts.sss++;
        else if (item.category.includes('SS TIER')) counts.ss++;
        else if (item.category.includes('URUT')) counts.urut++;
        else if (item.category.includes('S TIER')) counts.s++;
    });

    DOM.countSSS.textContent = counts.sss;
    DOM.countSS.textContent = counts.ss;
    DOM.countUrut.textContent = counts.urut;
    DOM.countS.textContent = counts.s;

    DOM.tabCountAll.textContent = total;
    DOM.tabCountSSS.textContent = counts.sss;
    DOM.tabCountSS.textContent = counts.ss;
    DOM.tabCountUrut.textContent = counts.urut;
    DOM.tabCountS.textContent = counts.s;
    DOM.tabCountFav.textContent = favoriteNumbers.size;
}

/**
 * Setup Event Listeners
 */
function setupEventListeners() {
    // Search input
    DOM.searchInput.addEventListener('input', (e) => {
        currentSearchQuery = e.target.value.trim();
        DOM.btnClearSearch.classList.toggle('hidden', currentSearchQuery === '');
        currentPage = 1;
        applyFiltersAndSort();
    });

    DOM.btnClearSearch.addEventListener('click', () => {
        DOM.searchInput.value = '';
        currentSearchQuery = '';
        DOM.btnClearSearch.classList.add('hidden');
        currentPage = 1;
        applyFiltersAndSort();
    });

    // Category Tabs
    DOM.categoryTabs.addEventListener('click', (e) => {
        const btn = e.target.closest('.tab-btn');
        if (!btn) return;

        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        currentCategory = btn.dataset.category;
        currentPage = 1;
        applyFiltersAndSort();
    });

    // Pattern Quick Chips
    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            currentDigitFilter = chip.dataset.digit;
            currentPage = 1;
            applyFiltersAndSort();
        });
    });

    // Sorting select
    DOM.sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        applyFiltersAndSort();
    });

    // Select all / Unselect all
    DOM.btnSelectAll.addEventListener('click', selectAllCurrentPage);
    DOM.btnUnselectAll.addEventListener('click', unselectAllCurrentPage);

    // Pagination
    DOM.btnPrevPage.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            renderGrid();
            window.scrollTo({ top: DOM.stockGrid.offsetTop - 150, behavior: 'smooth' });
        }
    });

    DOM.btnNextPage.addEventListener('click', () => {
        const totalPages = Math.ceil(filteredItems.length / ITEMS_PER_PAGE);
        if (currentPage < totalPages) {
            currentPage++;
            renderGrid();
            window.scrollTo({ top: DOM.stockGrid.offsetTop - 150, behavior: 'smooth' });
        }
    });

    // Bulk actions
    DOM.btnCopyBulk.addEventListener('click', copySelectedNumbers);
    DOM.btnOrderBulk.addEventListener('click', orderSelectedViaWA);
}

/**
 * Filter & Sort Logic
 */
function applyFiltersAndSort() {
    filteredItems = allStockItems.filter(item => {
        // Category filter
        if (currentCategory === 'FAVORITE') {
            if (!favoriteNumbers.has(item.number)) return false;
        } else if (currentCategory !== 'ALL') {
            if (item.category !== currentCategory) return false;
        }

        // Search query filter
        if (currentSearchQuery) {
            const query = currentSearchQuery.toLowerCase();
            const matchNumber = item.number.toLowerCase().includes(query);
            const matchCategory = item.category.toLowerCase().includes(query);
            if (!matchNumber && !matchCategory) return false;
        }

        // Digit pattern filter
        if (currentDigitFilter) {
            if (!item.number.includes(currentDigitFilter)) return false;
        }

        return true;
    });

    // Sort items
    filteredItems.sort((a, b) => {
        if (currentSort === 'tier') {
            const tierA = TIER_ORDER[a.category] || 99;
            const tierB = TIER_ORDER[b.category] || 99;
            if (tierA !== tierB) return tierA - tierB;
            return a.number.localeCompare(b.number);
        } else if (currentSort === 'num-asc') {
            return a.number.localeCompare(b.number, undefined, { numeric: true });
        } else if (currentSort === 'num-desc') {
            return b.number.localeCompare(a.number, undefined, { numeric: true });
        }
        return 0;
    });

    DOM.showingCount.textContent = filteredItems.length.toLocaleString();
    DOM.activeFilterText.textContent = getFilterDescriptionText();

    renderGrid();
}

function getFilterDescriptionText() {
    let catText = currentCategory === 'ALL' ? 'Semua Kategori' : currentCategory;
    if (currentDigitFilter) catText += ` • Pattern '${currentDigitFilter}'`;
    if (currentSearchQuery) catText += ` • Cari: "${currentSearchQuery}"`;
    return catText;
}

/**
 * Render Cards Grid & Pagination
 */
function renderGrid() {
    DOM.stockGrid.innerHTML = '';

    if (filteredItems.length === 0) {
        DOM.emptyState.classList.remove('hidden');
        DOM.paginationControls.classList.add('hidden');
        return;
    }

    DOM.emptyState.classList.add('hidden');

    const totalPages = Math.ceil(filteredItems.length / ITEMS_PER_PAGE);
    if (currentPage > totalPages) currentPage = totalPages || 1;

    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const pageItems = filteredItems.slice(startIndex, startIndex + ITEMS_PER_PAGE);

    pageItems.forEach(item => {
        const card = createStockCard(item);
        DOM.stockGrid.appendChild(card);
    });

    // Update Pagination
    if (totalPages > 1) {
        DOM.paginationControls.classList.remove('hidden');
        DOM.pageInfo.textContent = `Halaman ${currentPage} dari ${totalPages}`;
        DOM.btnPrevPage.disabled = currentPage === 1;
        DOM.btnNextPage.disabled = currentPage === totalPages;
    } else {
        DOM.paginationControls.classList.add('hidden');
    }

    updateSelectionState();
}

/**
 * Create DOM Card Element for a Stock Item
 */
function createStockCard(item) {
    const isSold = item.status === 'SOLD';
    const card = document.createElement('div');
    card.className = `stock-card ${isSold ? 'sold' : ''}`;
    if (selectedNumbers.has(item.number)) card.classList.add('selected');

    let tierType = 'S';
    let tierBadgeClass = 'badge-s';
    let tierIcon = 'fa-star';
    let tierLabel = 'S TIER';

    if (item.category.includes('SSS TIER')) {
        tierType = 'SSS';
        tierBadgeClass = 'badge-sss';
        tierIcon = 'fa-crown';
        tierLabel = 'SSS TIER';
    } else if (item.category.includes('SS TIER')) {
        tierType = 'SS';
        tierBadgeClass = 'badge-ss';
        tierIcon = 'fa-gem';
        tierLabel = 'SS TIER';
    } else if (item.category.includes('URUT')) {
        tierType = 'URUT';
        tierBadgeClass = 'badge-urut';
        tierIcon = 'fa-arrow-trend-up';
        tierLabel = 'URUT';
    }

    card.setAttribute('data-tier-type', tierType);

    // Pattern highlights
    const formattedNumber = formatNumberDisplay(item.number, currentSearchQuery || currentDigitFilter);
    const patternTag = getPatternDescription(item.number, tierType);
    const isFav = favoriteNumbers.has(item.number);

    const statusBadgeHtml = isSold
        ? `<span class="badge-status badge-sold"><i class="fa-solid fa-lock"></i> TERJUAL</span>`
        : '';

    const checkboxHtml = isSold
        ? `<input type="checkbox" class="card-checkbox" disabled title="Nomor sudah terjual">`
        : `<input type="checkbox" class="card-checkbox" ${selectedNumbers.has(item.number) ? 'checked' : ''}>`;

    const orderBtnHtml = isSold
        ? `<button class="btn-card-order disabled" disabled title="Nomor ini sudah terjual">
            <i class="fa-solid fa-ban"></i> Terjual
           </button>`
        : `<button class="btn-card-order">
            <i class="fa-brands fa-whatsapp"></i> Beli WA
           </button>`;

    card.innerHTML = `
        <div class="card-top">
            ${checkboxHtml}
            <div class="card-badges">
                <span class="badge-tier ${tierBadgeClass}">
                    <i class="fa-solid ${tierIcon}"></i> ${tierLabel}
                </span>
                ${statusBadgeHtml}
            </div>
        </div>
        <div class="card-center">
            <div class="phone-number">${formattedNumber}</div>
            <span class="pattern-tag">${patternTag}</span>
        </div>
        <div class="card-bottom">
            <button class="btn-card-copy" title="Salin Nomor">
                <i class="fa-solid fa-copy"></i>
            </button>
            <button class="btn-card-fav ${isFav ? 'active' : ''}" title="Tambah ke Favorit">
                <i class="fa-solid fa-heart"></i>
            </button>
            ${orderBtnHtml}
        </div>
    `;

    // Event Listeners for Card Controls
    const checkbox = card.querySelector('.card-checkbox');
    if (!isSold) {
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                selectedNumbers.add(item.number);
                card.classList.add('selected');
            } else {
                selectedNumbers.delete(item.number);
                card.classList.remove('selected');
            }
            updateSelectionState();
        });
    }

    card.querySelector('.btn-card-copy').addEventListener('click', (e) => {
        e.stopPropagation();
        navigator.clipboard.writeText(item.number);
        showToast(`Nomor ${item.number} berhasil disalin!`);
    });

    card.querySelector('.btn-card-fav').addEventListener('click', (e) => {
        e.stopPropagation();
        const favBtn = e.currentTarget;
        if (favoriteNumbers.has(item.number)) {
            favoriteNumbers.delete(item.number);
            favBtn.classList.remove('active');
            showToast(`Dihapus dari favorit`);
        } else {
            favoriteNumbers.add(item.number);
            favBtn.classList.add('active');
            showToast(`Ditambahkan ke favorit ❤️`);
        }
        localStorage.setItem('blinx_fav_numbers', JSON.stringify(Array.from(favoriteNumbers)));
        DOM.tabCountFav.textContent = favoriteNumbers.size;
    });

    if (!isSold) {
        card.querySelector('.btn-card-order').addEventListener('click', (e) => {
            e.stopPropagation();
            orderSingleViaWA(item);
        });
    }

    return card;
}

/**
 * Highlight search or pattern matches
 */
function formatNumberDisplay(numStr, highlightQuery) {
    if (!highlightQuery) return numStr;
    const regex = new RegExp(`(${highlightQuery})`, 'gi');
    return numStr.replace(regex, '<span class="phone-highlight">$1</span>');
}

/**
 * Get description tag for phone number pattern
 */
function getPatternDescription(numStr, tierType) {
    for (let d = 9; d >= 0; d--) {
        const seq6 = String(d).repeat(6);
        const seq5 = String(d).repeat(5);
        const seq4 = String(d).repeat(4);
        if (numStr.includes(seq6)) return `Super Repeat ${seq6}`;
        if (numStr.includes(seq5)) return `Rare Repeat ${seq5}`;
        if (numStr.includes(seq4)) return `Repeat ${seq4}`;
    }
    if (tierType === 'URUT') return `Urut Sequential`;
    return `Stock Blinx`;
}

/**
 * Update Floating Bulk Selection Bar
 */
function updateSelectionState() {
    const count = selectedNumbers.size;
    DOM.bulkCount.textContent = count;

    if (count > 0) {
        DOM.bulkBar.classList.remove('hidden');
        DOM.btnSelectAll.classList.add('hidden');
        DOM.btnUnselectAll.classList.remove('hidden');
    } else {
        DOM.bulkBar.classList.add('hidden');
        DOM.btnSelectAll.classList.remove('hidden');
        DOM.btnUnselectAll.classList.add('hidden');
    }
}

function selectAllCurrentPage() {
    const startIndex = (currentPage - 1) * ITEMS_PER_PAGE;
    const pageItems = filteredItems.slice(startIndex, startIndex + ITEMS_PER_PAGE);
    pageItems.forEach(item => {
        if (item.status !== 'SOLD') {
            selectedNumbers.add(item.number);
        }
    });
    renderGrid();
}

function unselectAllCurrentPage() {
    selectedNumbers.clear();
    renderGrid();
}

function copySelectedNumbers() {
    if (selectedNumbers.size === 0) return;
    const listText = Array.from(selectedNumbers).join('\n');
    navigator.clipboard.writeText(listText);
    showToast(`${selectedNumbers.size} nomor berhasil disalin!`);
}

/**
 * Order single item via WhatsApp
 */
function orderSingleViaWA(item) {
    const message = `Halo Admin, saya berminat membeli nomor Stock Blinx berikut:\n\n📱 *Nomor*: ${item.number}\n🏷️ *Category*: ${item.category}\n\nApakah nomor ini masih ready?`;
    const waUrl = `https://wa.me/${ADMIN_WA}?text=${encodeURIComponent(message)}`;
    window.open(waUrl, '_blank');
}

/**
 * Order multiple items via WhatsApp
 */
function orderSelectedViaWA() {
    if (selectedNumbers.size === 0) return;
    
    let listText = Array.from(selectedNumbers).map((num, idx) => `${idx + 1}. ${num}`).join('\n');
    const message = `Halo Admin, saya berminat membeli ${selectedNumbers.size} nomor Stock Blinx berikut:\n\n${listText}\n\nMohon info ketersediaan dan total harganya. Terima kasih!`;
    const waUrl = `https://wa.me/${ADMIN_WA}?text=${encodeURIComponent(message)}`;
    window.open(waUrl, '_blank');
}

/**
 * Filter category programmatically (e.g. from Hero stat cards)
 */
function filterCategory(catName) {
    currentCategory = catName;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.category === catName) btn.classList.add('active');
        else btn.classList.remove('active');
    });
    currentPage = 1;
    applyFiltersAndSort();
    window.scrollTo({ top: DOM.catalog.offsetTop - 100, behavior: 'smooth' });
}

function resetFilters() {
    currentCategory = 'ALL';
    currentSearchQuery = '';
    currentDigitFilter = '';
    DOM.searchInput.value = '';
    DOM.btnClearSearch.classList.add('hidden');
    document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', i === 0));
    currentPage = 1;
    applyFiltersAndSort();
}

/**
 * Helper UI functions
 */
function showLoading(isLoading) {
    if (isLoading) {
        DOM.loadingState.classList.remove('hidden');
        DOM.stockGrid.classList.add('hidden');
    } else {
        DOM.loadingState.classList.add('hidden');
        DOM.stockGrid.classList.remove('hidden');
    }
}

function showToast(msg) {
    DOM.toastMessage.textContent = msg;
    DOM.toast.classList.remove('hidden');
    setTimeout(() => {
        DOM.toast.classList.add('hidden');
    }, 3000);
}
