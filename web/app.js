/**
 * STOCK BLINX - MAIN APPLICATION LOGIC
 * Includes Animated Stock Counters, Clean Main Catalog (SSS/SS/URUT), and S-Tier Bonus Modal
 * WhatsApp Admin: 62882003619577
 */

const ADMIN_WA = "62882003619577";

// Application State
let allStockItems = [];
let filteredItems = [];
let sTierStockItems = [];
let filteredSTierItems = [];

let selectedNumbers = new Set();
let favoriteNumbers = new Set(JSON.parse(localStorage.getItem('blinx_fav_numbers') || '[]'));

let currentCategory = 'ALL';
let currentSearchQuery = '';
let currentDigitFilter = '';
let currentSort = 'tier';
let currentPage = 1;
const ITEMS_PER_PAGE = 60;

// S-Tier Modal Pagination & Search State
let stierModalSearchQuery = '';
let stierModalPage = 1;
const STIER_PER_PAGE = 50;

const TIER_ORDER = {
    'SSS TIER (6x digit berulang)': 1,
    'SS TIER (5x digit berulang)': 2,
    '(URUT)': 3,
    'S TIER (4x digit berulang)': 4
};

// Helper: Strictly check if a category is S-TIER (and not SSS or SS)
function isSTierCategory(cat) {
    if (!cat) return false;
    return cat.includes('S TIER') && !cat.includes('SSS') && !cat.includes('SS');
}

// DOM Elements
const DOM = {
    headerStockCount: document.getElementById('header-stock-count'),
    totalHeroStock: document.getElementById('total-hero-stock'),
    countSSS: document.getElementById('count-sss'),
    countSS: document.getElementById('count-ss'),
    countUrut: document.getElementById('count-urut'),
    stierTotalCount: document.getElementById('stier-total-count'),
    modalSTierCount: document.getElementById('modal-stier-count'),

    btnWaNav: document.getElementById('btn-wa-nav'),
    btnWaFooter: document.getElementById('btn-wa-footer'),
    catalog: document.getElementById('catalog'),

    searchInput: document.getElementById('search-input'),
    btnClearSearch: document.getElementById('btn-clear-search'),
    categoryTabs: document.getElementById('category-tabs'),
    sortSelect: document.getElementById('sort-select'),
    
    tabCountAll: document.getElementById('tab-count-all'),
    tabCountSSS: document.getElementById('tab-count-sss'),
    tabCountSS: document.getElementById('tab-count-ss'),
    tabCountUrut: document.getElementById('tab-count-urut'),
    tabCountFav: document.getElementById('tab-count-fav'),

    showingCount: document.getElementById('showing-count'),
    activeFilterText: document.getElementById('active-filter-text'),

    stockGrid: document.getElementById('stock-grid'),
    loadingState: document.getElementById('loading-state'),
    emptyState: document.getElementById('empty-state'),
    paginationControls: document.getElementById('pagination-controls'),
    btnPrevPage: document.getElementById('btn-prev-page'),
    btnNextPage: document.getElementById('btn-next-page'),
    pageInfo: document.getElementById('page-info'),

    // Promo & S-Tier Modal DOM
    btnOpenSTierModal: document.getElementById('btn-open-stier-modal'),
    stierModal: document.getElementById('stier-modal'),
    btnCloseSTierModal: document.getElementById('btn-close-stier-modal'),
    btnDoneSTierModal: document.getElementById('btn-done-stier-modal'),
    stierModalSearch: document.getElementById('stier-modal-search'),
    stierModalGrid: document.getElementById('stier-modal-grid'),
    stierModalPagination: document.getElementById('stier-modal-pagination'),
    btnSTierPrev: document.getElementById('btn-stier-prev'),
    btnSTierNext: document.getElementById('btn-stier-next'),
    stierPageInfo: document.getElementById('stier-page-info'),
    stierModalDesc: document.getElementById('stier-modal-desc'),

    bulkBar: document.getElementById('bulk-bar'),
    bulkCount: document.getElementById('bulk-count'),
    promoBonusBadge: document.getElementById('promo-bonus-badge'),
    btnCopyBulk: document.getElementById('btn-copy-bulk'),
    btnOrderBulk: document.getElementById('btn-order-bulk'),

    toast: document.getElementById('toast'),
    toastMessage: document.getElementById('toast-message')
};

document.addEventListener('DOMContentLoaded', () => {
    initApp();
});

async function initApp() {
    setupEventListeners();
    await loadStockData();
    renderStats();
    applyFiltersAndSort();
}

async function loadStockData() {
    showLoading(true);
    let loadedSuccess = false;

    try {
        const response = await fetch('/api/stock');
        if (response.ok) {
            const data = await response.json();
            if (Array.isArray(data) && data.length > 0) {
                allStockItems = data;
                loadedSuccess = true;
                console.log('Loaded stock data via API:', allStockItems.length);
            }
        }
    } catch (e) {
        console.warn('API fetch error:', e);
    }

    if (!loadedSuccess) {
        try {
            const txtResponse = await fetch('/RAPI/all.txt');
            if (txtResponse.ok) {
                const text = await txtResponse.text();
                allStockItems = parseAllTxt(text);

                try {
                    const soldResponse = await fetch('/RAPI/sold.txt');
                    if (soldResponse.ok) {
                        const soldText = await soldResponse.text();
                        const soldItems = parseSoldTxt(soldText);
                        allStockItems = [...allStockItems, ...soldItems];
                    }
                } catch (errSold) {
                    console.warn('Fallback sold.txt fetch failed:', errSold);
                }

                if (allStockItems.length > 0) {
                    loadedSuccess = true;
                    console.log('Loaded stock data from all.txt & sold.txt:', allStockItems.length);
                }
            }
        } catch (err) {
            console.warn('Static file fetch error:', err);
        }
    }

    if (!loadedSuccess) {
        if (window.STOCK_DATA && Array.isArray(window.STOCK_DATA) && window.STOCK_DATA.length > 0) {
            allStockItems = window.STOCK_DATA;
            console.log('Loaded stock data via window.STOCK_DATA fallback:', allStockItems.length);
        }
    }

    // Separate S-Tier items from main stock
    sTierStockItems = allStockItems.filter(item => isSTierCategory(item.category) && item.status !== 'SOLD');

    showLoading(false);
}

function parseAllTxt(rawText) {
    const lines = rawText.split('\n');
    const items = [];
    let currentCat = 'S TIER (4x digit berulang)';

    lines.forEach(line => {
        line = line.trim();
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

// Smooth Ease-Out Animated Stock Counter Helper
function animateCounter(element, targetValue, options = {}) {
    if (!element) return;

    const duration = typeof options === 'number' ? options : (options.duration || 800);
    const prefix = typeof options === 'object' && options.prefix ? options.prefix : '';
    const suffix = typeof options === 'object' && options.suffix ? options.suffix : '';

    const prevValAttr = element.dataset.animVal;
    let startValue = prevValAttr !== undefined ? parseInt(prevValAttr, 10) : 0;
    if (isNaN(startValue)) startValue = 0;

    targetValue = parseInt(targetValue, 10) || 0;

    if (element._animId) {
        cancelAnimationFrame(element._animId);
    }

    element.dataset.animVal = targetValue;

    if (startValue === targetValue && element.textContent !== '') {
        element.textContent = `${prefix}${targetValue.toLocaleString()}${suffix}`;
        return;
    }

    const startTime = performance.now();

    function updateValue(currentTime) {
        const elapsedTime = currentTime - startTime;
        if (elapsedTime >= duration) {
            element.textContent = `${prefix}${targetValue.toLocaleString()}${suffix}`;
            delete element._animId;
        } else {
            const progress = elapsedTime / duration;
            const easeOut = 1 - Math.pow(1 - progress, 3);
            const current = Math.floor(startValue + (targetValue - startValue) * easeOut);
            element.textContent = `${prefix}${current.toLocaleString()}${suffix}`;
            element._animId = requestAnimationFrame(updateValue);
        }
    }

    element._animId = requestAnimationFrame(updateValue);
}

function renderStats() {
    const availableItems = allStockItems.filter(item => item.status !== 'SOLD');
    const mainAvailableItems = availableItems.filter(item => !isSTierCategory(item.category));
    const mainReady = mainAvailableItems.length;

    // Header & Hero stock counts
    animateCounter(DOM.headerStockCount, mainReady, { duration: 1000, suffix: ' Stock Utama Ready' });
    animateCounter(DOM.totalHeroStock, mainReady, 1000);

    const counts = { sss: 0, ss: 0, urut: 0, s: 0 };

    availableItems.forEach(item => {
        if (item.category.includes('SSS TIER')) counts.sss++;
        else if (item.category.includes('SS TIER')) counts.ss++;
        else if (item.category.includes('URUT')) counts.urut++;
        else if (isSTierCategory(item.category)) counts.s++;
    });

    // Stats cards
    animateCounter(DOM.countSSS, counts.sss, 900);
    animateCounter(DOM.countSS, counts.ss, 900);
    animateCounter(DOM.countUrut, counts.urut, 900);

    // Category tab badges
    animateCounter(DOM.tabCountAll, mainReady, 800);
    animateCounter(DOM.tabCountSSS, counts.sss, 800);
    animateCounter(DOM.tabCountSS, counts.ss, 800);
    animateCounter(DOM.tabCountUrut, counts.urut, 800);
    animateCounter(DOM.tabCountFav, favoriteNumbers.size, 500);

    // S-Tier promo counts
    if (DOM.stierTotalCount) animateCounter(DOM.stierTotalCount, counts.s, 1000);
    if (DOM.modalSTierCount) animateCounter(DOM.modalSTierCount, counts.s, 1000);
}

function setupEventListeners() {
    if (DOM.btnWaNav) {
        DOM.btnWaNav.addEventListener('click', () => openWaDirect("Halo Admin, saya ingin menanyakan Stock Blinx."));
    }
    if (DOM.btnWaFooter) {
        DOM.btnWaFooter.addEventListener('click', () => openWaDirect("Halo Admin, saya ingin menanyakan Stock Blinx."));
    }

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

    DOM.categoryTabs.addEventListener('click', (e) => {
        const btn = e.target.closest('.tab-btn');
        if (!btn) return;

        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        currentCategory = btn.dataset.category;
        currentPage = 1;
        applyFiltersAndSort();
    });

    document.querySelectorAll('.chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            currentDigitFilter = chip.dataset.digit;
            currentPage = 1;
            applyFiltersAndSort();
        });
    });

    DOM.sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        applyFiltersAndSort();
    });

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

    // Modal S-Tier Events
    if (DOM.btnOpenSTierModal) {
        DOM.btnOpenSTierModal.addEventListener('click', openSTierModal);
    }
    if (DOM.btnCloseSTierModal) {
        DOM.btnCloseSTierModal.addEventListener('click', closeSTierModal);
    }
    if (DOM.btnDoneSTierModal) {
        DOM.btnDoneSTierModal.addEventListener('click', closeSTierModal);
    }
    if (DOM.stierModal) {
        DOM.stierModal.addEventListener('click', (e) => {
            if (e.target === DOM.stierModal) closeSTierModal();
        });
    }

    if (DOM.stierModalSearch) {
        DOM.stierModalSearch.addEventListener('input', (e) => {
            stierModalSearchQuery = e.target.value.trim();
            stierModalPage = 1;
            renderSTierModalGrid();
        });
    }

    if (DOM.btnSTierPrev) {
        DOM.btnSTierPrev.addEventListener('click', () => {
            if (stierModalPage > 1) {
                stierModalPage--;
                renderSTierModalGrid();
            }
        });
    }

    if (DOM.btnSTierNext) {
        DOM.btnSTierNext.addEventListener('click', () => {
            const totalPages = Math.ceil(filteredSTierItems.length / STIER_PER_PAGE);
            if (stierModalPage < totalPages) {
                stierModalPage++;
                renderSTierModalGrid();
            }
        });
    }

    DOM.btnCopyBulk.addEventListener('click', copySelectedNumbers);
    DOM.btnOrderBulk.addEventListener('click', orderSelectedViaWA);
}

function applyFiltersAndSort() {
    filteredItems = allStockItems.filter(item => {
        // ALWAYS exclude S-Tier from the main catalog list!
        if (isSTierCategory(item.category)) return false;

        if (currentCategory === 'FAVORITE') {
            if (!favoriteNumbers.has(item.number)) return false;
        } else if (currentCategory !== 'ALL') {
            if (item.category !== currentCategory) return false;
        }

        if (currentSearchQuery) {
            const query = currentSearchQuery.toLowerCase();
            const matchNumber = item.number.toLowerCase().includes(query);
            const matchCategory = item.category.toLowerCase().includes(query);
            if (!matchNumber && !matchCategory) return false;
        }

        if (currentDigitFilter) {
            if (!item.number.includes(currentDigitFilter)) return false;
        }

        return true;
    });

    filteredItems.sort((a, b) => {
        if (currentSort === 'tier') {
            const tierA = TIER_ORDER[a.category] || 99;
            const tierB = TIER_ORDER[b.category] || 99;
            if (tierA !== tierB) return tierA - tierB;
            return a.number.localeCompare(b.number);
        } else if (currentSort === 'num-asc') {
            return a.number.localeCompare(a.number, undefined, { numeric: true });
        } else if (currentSort === 'num-desc') {
            return b.number.localeCompare(a.number, undefined, { numeric: true });
        }
        return 0;
    });

    animateCounter(DOM.showingCount, filteredItems.length, 500);
    DOM.activeFilterText.textContent = getFilterDescriptionText();

    renderGrid();
}

function getFilterDescriptionText() {
    let catText = currentCategory === 'ALL' ? 'Semua Kategori (SSS, SS, URUT)' : currentCategory;
    if (currentDigitFilter) catText += ` • Pattern '${currentDigitFilter}'`;
    if (currentSearchQuery) catText += ` • Cari: "${currentSearchQuery}"`;
    return catText;
}

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

// S-Tier Modal Logic
function openSTierModal() {
    DOM.stierModal.classList.remove('hidden');
    stierModalSearchQuery = '';
    if (DOM.stierModalSearch) DOM.stierModalSearch.value = '';
    stierModalPage = 1;
    renderSTierModalGrid();
}

function closeSTierModal() {
    DOM.stierModal.classList.add('hidden');
    renderGrid(); // Refresh main grid selection checkboxes
}

function renderSTierModalGrid() {
    const mainCount = getMainStockCount();
    const sTierCount = getSTierSelectedCount();
    const eligibleBonus = Math.floor(mainCount / 2);

    if (DOM.stierModalDesc) {
        if (mainCount < 2) {
            DOM.stierModalDesc.className = 'modal-desc modal-warning';
            DOM.stierModalDesc.innerHTML = `⚠️ <strong>Syarat Promo:</strong> Kamu baru memilih ${mainCount} Stok Utama. Minimal pilih <strong>2 Stok Utama (SSS/SS/URUT)</strong> terlebih dahulu untuk mengklaim Bonus S-Tier GRATIS.`;
        } else {
            DOM.stierModalDesc.className = 'modal-desc';
            DOM.stierModalDesc.innerHTML = `🎁 <strong>Promo Aktif:</strong> Kamu berhak memilih <strong>${eligibleBonus} Bonus S-Tier GRATIS</strong> (${sTierCount}/${eligibleBonus} telah dipilih).`;
        }
    }

    filteredSTierItems = sTierStockItems.filter(item => {
        if (stierModalSearchQuery) {
            return item.number.toLowerCase().includes(stierModalSearchQuery.toLowerCase());
        }
        return true;
    });

    DOM.stierModalGrid.innerHTML = '';

    if (filteredSTierItems.length === 0) {
        DOM.stierModalGrid.innerHTML = '<div style="text-align:center; padding: 2rem; color: #888;">Tidak ada stok S-Tier yang cocok dengan pencarian.</div>';
        DOM.stierModalPagination.classList.add('hidden');
        return;
    }

    const totalPages = Math.ceil(filteredSTierItems.length / STIER_PER_PAGE);
    if (stierModalPage > totalPages) stierModalPage = totalPages || 1;

    const startIndex = (stierModalPage - 1) * STIER_PER_PAGE;
    const pageItems = filteredSTierItems.slice(startIndex, startIndex + STIER_PER_PAGE);

    pageItems.forEach(item => {
        const card = createStockCard(item);
        DOM.stierModalGrid.appendChild(card);
    });

    if (totalPages > 1) {
        DOM.stierModalPagination.classList.remove('hidden');
        DOM.stierPageInfo.textContent = `Halaman ${stierModalPage} dari ${totalPages}`;
        DOM.btnSTierPrev.disabled = stierModalPage === 1;
        DOM.btnSTierNext.disabled = stierModalPage === totalPages;
    } else {
        DOM.stierModalPagination.classList.add('hidden');
    }
}

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

    const formattedNumber = formatNumberDisplay(item.number, currentSearchQuery || currentDigitFilter || stierModalSearchQuery);
    const patternTag = getPatternDescription(item.number, tierType);
    const isFav = favoriteNumbers.has(item.number);

    const statusBadgeHtml = isSold
        ? `<span class="badge-sold"><i class="fa-solid fa-lock"></i> TERJUAL</span>`
        : '';

    const promoBadgeHtml = (isSTierCategory(item.category) && !isSold)
        ? `<span class="badge-bonus-stier"><i class="fa-solid fa-gift"></i> BONUS BUY 2 GET 1</span>`
        : '';

    const checkboxHtml = isSold
        ? `<input type="checkbox" class="card-checkbox" disabled title="Nomor sudah terjual">`
        : `<input type="checkbox" class="card-checkbox" ${selectedNumbers.has(item.number) ? 'checked' : ''}>`;

    const isSTier = isSTierCategory(item.category);

    const favBtnHtml = isSTier
        ? ''
        : `<button class="btn-card-fav ${isFav ? 'active' : ''}" title="Tambah ke Favorit">
            <i class="fa-solid fa-heart"></i>
           </button>`;

    const orderBtnHtml = isSold
        ? `<button class="btn-card-order disabled" disabled title="Nomor ini sudah terjual">
            <i class="fa-solid fa-ban"></i> Terjual
           </button>`
        : (isSTier
            ? `<span class="badge-bonus-tag"><i class="fa-solid fa-gift"></i> Stock Bonus</span>`
            : `<button class="btn-card-order">
                <i class="fa-brands fa-whatsapp"></i> Beli
               </button>`);

    card.innerHTML = `
        <div class="card-top">
            ${checkboxHtml}
            <div class="card-badges">
                <span class="badge-tier ${tierBadgeClass}">
                    <i class="fa-solid ${tierIcon}"></i> ${tierLabel}
                </span>
                ${promoBadgeHtml}
                ${statusBadgeHtml}
            </div>
        </div>
        <div class="card-center">
            <div class="phone-number" title="Klik untuk salin">${formattedNumber}</div>
            <span class="pattern-tag">${patternTag}</span>
        </div>
        <div class="card-bottom">
            <button class="btn-card-copy" title="Salin Nomor">
                <i class="fa-solid fa-copy"></i>
            </button>
            ${favBtnHtml}
            ${orderBtnHtml}
        </div>
    `;

    const checkbox = card.querySelector('.card-checkbox');
    if (!isSold) {
        checkbox.addEventListener('change', () => {
            if (checkbox.checked) {
                if (isSTierCategory(item.category)) {
                    const mainCount = getMainStockCount();
                    if (mainCount < 2) {
                        checkbox.checked = false;
                        if (mainCount === 0) {
                            showToast(`⚠️ Pilih minimal 2 Stok Utama (SSS/SS/URUT) terlebih dahulu untuk memilih Bonus S-Tier!`);
                        } else {
                            showToast(`⚠️ Pilih 1 Stok Utama lagi untuk membuka 1 Bonus S-Tier GRATIS!`);
                        }
                        return;
                    }

                    const eligibleBonus = Math.floor(mainCount / 2);
                    const currentSTierCount = getSTierSelectedCount();
                    if (currentSTierCount >= eligibleBonus) {
                        checkbox.checked = false;
                        showToast(`⚠️ Kuota bonus tercapai (${eligibleBonus} S-Tier). Tambah 2 Stok Utama lagi untuk bonus berikutnya!`);
                        return;
                    }
                }
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
        copyToClipboard(item.number);
    });

    card.querySelector('.phone-number').addEventListener('click', () => {
        copyToClipboard(item.number);
    });

    const favBtn = card.querySelector('.btn-card-fav');
    if (favBtn) {
        favBtn.addEventListener('click', (e) => {
            e.stopPropagation();
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
            animateCounter(DOM.tabCountFav, favoriteNumbers.size, 400);
        });
    }

    const orderBtn = card.querySelector('.btn-card-order');
    if (orderBtn && !isSold) {
        orderBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            orderSingleViaWA(item);
        });
    }

    return card;
}

function formatNumberDisplay(numStr, highlightQuery) {
    if (!highlightQuery) return numStr;
    const regex = new RegExp(`(${highlightQuery})`, 'gi');
    return numStr.replace(regex, '<span class="phone-highlight">$1</span>');
}

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

function getMainStockCount() {
    let count = 0;
    selectedNumbers.forEach(num => {
        const found = allStockItems.find(i => i.number === num);
        if (found && !isSTierCategory(found.category)) count++;
    });
    return count;
}

function getSTierSelectedCount() {
    let count = 0;
    selectedNumbers.forEach(num => {
        const found = allStockItems.find(i => i.number === num);
        if (found && isSTierCategory(found.category)) count++;
    });
    return count;
}

function updateSelectionState() {
    const count = selectedNumbers.size;
    animateCounter(DOM.bulkCount, count, 400);

    let mainCount = 0;
    let sTierCount = 0;
    const sTierSelectedList = [];

    selectedNumbers.forEach(num => {
        const found = allStockItems.find(i => i.number === num);
        if (found) {
            if (isSTierCategory(found.category)) {
                sTierCount++;
                sTierSelectedList.push(found.number);
            } else {
                mainCount++;
            }
        }
    });

    const eligibleFreeBonus = Math.floor(mainCount / 2);

    // Auto-prune S-Tier items if main items were unselected and quota is exceeded
    if (sTierCount > eligibleFreeBonus) {
        const excessCount = sTierCount - eligibleFreeBonus;
        for (let i = 0; i < excessCount; i++) {
            const numToRemove = sTierSelectedList.pop();
            selectedNumbers.delete(numToRemove);
        }
        showToast(`⚠️ Kuota bonus disesuaikan. Membutuhkan minimal 2 Stok Utama per 1 Bonus S-Tier.`);
        renderGrid();
        if (DOM.stierModal && !DOM.stierModal.classList.contains('hidden')) {
            renderSTierModalGrid();
        }
        return;
    }

    if (DOM.promoBonusBadge) {
        if (eligibleFreeBonus > 0) {
            DOM.promoBonusBadge.classList.remove('hidden');
            DOM.promoBonusBadge.textContent = `🎁 ${sTierCount}/${eligibleFreeBonus} Bonus S-Tier Dipilih`;
        } else {
            DOM.promoBonusBadge.classList.add('hidden');
        }
    }

    if (count > 0) {
        DOM.bulkBar.classList.remove('hidden');
    } else {
        DOM.bulkBar.classList.add('hidden');
    }
}

function copyToClipboard(text) {
    navigator.clipboard.writeText(text);
    showToast(`Nomor ${text} berhasil disalin!`);
}

function copySelectedNumbers() {
    if (selectedNumbers.size === 0) return;
    const listText = Array.from(selectedNumbers).join('\n');
    navigator.clipboard.writeText(listText);
    showToast(`${selectedNumbers.size} nomor berhasil disalin!`);
}

function openWaDirect(textMessage) {
    const waUrl = `https://wa.me/${ADMIN_WA}?text=${encodeURIComponent(textMessage)}`;
    window.open(waUrl, '_blank');
}

function orderSingleViaWA(item) {
    const message = `Halo Admin, saya berminat membeli nomor Stock Blinx berikut:\n\n📱 *Nomor*: ${item.number}\n🏷️ *Category*: ${item.category}\n\nApakah nomor ini masih ready?`;
    openWaDirect(message);
}

function orderSelectedViaWA() {
    if (selectedNumbers.size === 0) return;

    const mainItems = [];
    const sTierBonusItems = [];

    selectedNumbers.forEach(num => {
        const found = allStockItems.find(i => i.number === num);
        if (found && isSTierCategory(found.category)) {
            sTierBonusItems.push(found);
        } else if (found) {
            mainItems.push(found);
        } else {
            mainItems.push({ number: num, category: 'Stock' });
        }
    });

    const eligibleFreeBonusCount = Math.floor(mainItems.length / 2);

    let message = `Halo Admin, saya berminat order via *PROMO BUY 2 GET 1 FREE*:\n\n`;

    if (mainItems.length > 0) {
        message += `🛒 *NOMOR UTAMA (${mainItems.length} nomor)*:\n`;
        mainItems.forEach((item, idx) => {
            message += `${idx + 1}. ${item.number} (${item.category})\n`;
        });
    }

    if (sTierBonusItems.length > 0) {
        message += `\n🎁 *BONUS S-TIER (${sTierBonusItems.length} nomor)*:\n`;
        sTierBonusItems.forEach((item, idx) => {
            message += `${idx + 1}. ${item.number}\n`;
        });
    }

    if (eligibleFreeBonusCount > 0 && sTierBonusItems.length === 0) {
        message += `\n💡 *Info Promo*: Pembelian ${mainItems.length} nomor utama berhak klaim ${eligibleFreeBonusCount} nomor S-Tier GRATIS!`;
    }

    message += `\nMohon info total harganya. Terima kasih Admin!`;
    openWaDirect(message);
}

function filterCategory(catName) {
    currentCategory = catName;
    document.querySelectorAll('.tab-btn').forEach(btn => {
        if (btn.dataset.category === catName) btn.classList.add('active');
        else btn.classList.remove('active');
    });
    currentPage = 1;
    applyFiltersAndSort();
    if (DOM.catalog) {
        window.scrollTo({ top: DOM.catalog.offsetTop - 80, behavior: 'smooth' });
    }
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
