/**
 * 長安醫院 全站通用核心腳本 (site-main.js)
 * 整合：回到最上方、子頁側邊選單收合、PDF 原頁開啟、版權聲明自動年份更新
 */

// --- 0. 全域工具函式 ---
/**
 * 開啟 PDF 並解決歷史紀錄多出一筆的問題 (修正按上一頁需要點兩次的問題)
 * @param {string} url 
 */
window.openInFullScreenWin = function(url) {
    if (!url) return;
    // 改用 href 確保上一頁能回到原本的頁面，解決 replace 會導致跳過當前頁面的問題
    window.location.href = url;
};

// --- 1. 回到最上方 (Gotop) ---
window.topFunction = function() {
    window.scrollTo({ top: 0, behavior: 'smooth' });
};

document.addEventListener('DOMContentLoaded', function() {
    
    // --- 1.1 回到最上方按鈕顯示邏輯 ---
    const mybutton = document.getElementById('myBtn');
    if (mybutton) {
        function updateMyBtnVisibility() {
            // 如果畫面寬度小於 992px 且頁面上有 .bottom-nav，則隱藏預設的 #myBtn
            if (window.innerWidth < 992 && document.querySelector('.bottom-nav')) {
                mybutton.style.display = 'none';
                return;
            }
            
            if (window.scrollY > 20) {
                mybutton.style.display = 'block';
            } else {
                mybutton.style.display = 'none';
            }
        }

        window.addEventListener('scroll', updateMyBtnVisibility);
        window.addEventListener('resize', updateMyBtnVisibility);
        
        // 初始載入時檢查一次
        updateMyBtnVisibility();

        mybutton.addEventListener('click', () => {
            window.topFunction();
        });
    }

    // --- 2. 版權聲明-自動設定今年年份 ---
    const yearSpan = document.getElementById('currentYear');
    if (yearSpan) {
        yearSpan.textContent = new Date().getFullYear();
    }

    // --- 3. 子頁側邊選單收合 (Sidebar Menu) ---
    document.addEventListener('click', function(e) {
        const toggle = e.target.closest('.js-sidebar-toggle');
        if (!toggle) return;

        const sidebar = toggle.closest('.js-sidebar-wrapper');
        if (sidebar && window.innerWidth < 992) {
            sidebar.classList.toggle('is-open');
        }
    });

    window.addEventListener('resize', function() {
        if (window.innerWidth >= 992) {
            document.querySelectorAll('.js-sidebar-wrapper.is-open').forEach(el => {
                el.classList.remove('is-open');
            });
        }
    });

    // --- 4. PDF 開啟工具 ---
    document.addEventListener('click', function(e) {
        const pdfLink = e.target.closest('a[href$=".pdf"]');
        if (pdfLink) {
            // 為了解決「按上一頁需要點兩次」的瀏覽器 PDF 閱讀器歷史紀錄問題，
            // 最佳的作法是統一加上 target="_blank" 讓 PDF 在新分頁開啟。
            pdfLink.setAttribute('target', '_blank');
            // 不阻擋預設行為，讓瀏覽器自然開啟新分頁
        }
    });

    // --- 5. 側邊選單子項目切換 (Sidebar Submenu) ---
    document.addEventListener('click', function(e) {
        const subToggle = e.target.closest('.js-submenu-toggle');
        if (!subToggle) return;

        // 如果是 a 連結且沒有阻止預設行為，則不進行折疊切換（除非是想要點擊箭頭才切換）
        // 但這裡我們通常希望點擊整個項目都能切換
        const wrapper = subToggle.closest('.has-sub');
        if (wrapper) {
            e.preventDefault();
            e.stopPropagation(); // 阻止事件冒泡，避免觸發行動版選單關閉
            wrapper.classList.toggle('is-expanded');
        }
    });

    // --- 5.1 自動展開包含 active 子項目的父選單 ---
    const activeSubItem = document.querySelector('.c-sidebar-trust__sub-item.is-active');
    if (activeSubItem) {
        const parentWrapper = activeSubItem.closest('.has-sub');
        if (parentWrapper) {
            parentWrapper.classList.add('is-expanded');
        }
    }

    // --- 6. 桌機 Mega Menu 子項目折疊 (Mega Menu Sub-folding) ---
    document.addEventListener('click', function(e) {
        const megaToggle = e.target.closest('.js-mega-sub-toggle');
        if (!megaToggle) return;

        e.preventDefault();
        e.stopPropagation(); // 阻止事件冒泡，避免觸發行動版選單關閉
        const subList = megaToggle.nextElementSibling;
        if (subList && subList.classList.contains('m-mega__sub-list')) {
            megaToggle.classList.toggle('is-active');
            subList.classList.toggle('is-active');
        }
    });

});

(function() {
    const header = document.getElementById('m-header');
    const toggle = document.getElementById('m-toggle');
    const sidebar = document.getElementById('m-sidebar');
    const overlay = document.getElementById('m-overlay');
    const mobileContainer = document.getElementById('m-mobile-container');

    /**
     * 導航選單自動同步化邏輯 (Sync Navigation)
     * 從桌機版 (.m-nav) 自動生成行動版 (.m-mobile-container)
     */
    function syncNavigation() {
        const desktopNavList = document.querySelector('.m-nav__list');
        if (!desktopNavList || !mobileContainer) return;

        // --- 1. 建立主選單層 (Layer Main) ---
        const mainLayer = document.createElement('div');
        mainLayer.className = 'm-mobile-layer';
        mainLayer.id = 'm-layer-main';
        
        // 取得 Logo 連結與圖片 (從桌機版 Logo 複製)
        const desktopLogoA = document.querySelector('.m-header__logo a');
        const logoUrl = desktopLogoA ? desktopLogoA.getAttribute('href') : '/index/';
        const logoImg = desktopLogoA ? desktopLogoA.querySelector('img') : null;
        const logoImgSrc = logoImg ? logoImg.getAttribute('src') : '';

        mainLayer.innerHTML = `
            <div class="m-mobile-header">
                <a href="${logoUrl}" class="m-mobile-logo">
                    <img src="${logoImgSrc}" alt="回首頁" title="回首頁">
                </a>
                <button class="m-mobile-btn m-close-trigger">
                    <svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"></path></svg>
                </button>
            </div>
            <div class="m-mobile-body">
                <ul class="m-mobile-list" id="m-mobile-main-list"></ul>
            </div>
        `;

        const mobileMainList = mainLayer.querySelector('#m-mobile-main-list');
        const subLayersFragment = document.createDocumentFragment();

        // --- 2. 遍歷桌機選項 ---
        const navItems = desktopNavList.querySelectorAll(':scope > .m-nav__item');
        navItems.forEach((item, index) => {
            const link = item.querySelector('.m-nav__link');
            const mega = item.querySelector('.m-mega');
            if (!link) return;

            const title = link.textContent.trim();
            const href = link.getAttribute('href');
            const isMega = mega !== null;
            const subLayerId = `m-layer-sub-${index}`;

            // A. 加入主選單項目
            const li = document.createElement('li');
            li.className = 'm-mobile-item';
            
            if (isMega) {
                li.innerHTML = `
                    <a href="javascript:void(0)" class="m-mobile-link m-sub-trigger" data-target="${subLayerId}" title="${title}">
                        ${title}
                        <svg viewBox="0 0 24 24"><path d="M9 18l6-6-6-6"></path></svg>
                    </a>
                `;
                
                // B. 建立對應的子選單層 (Sub Layer)
                const subLayer = document.createElement('div');
                subLayer.className = 'm-mobile-layer m-sub-layer';
                subLayer.id = subLayerId;
                
                let subContent = '';
                
                // 判斷 mega 內部類型 (Grid 還是 List)
                const medicalGrid = mega.querySelector('.m-medical-grid');
                if (medicalGrid) {
                    // 重點醫療網格
                    subContent = `<div class="m-mobile-grid">`;
                    medicalGrid.querySelectorAll('.m-medical-card').forEach(card => {
                        const cardHref = card.getAttribute('href');
                        const cardTitleEl = card.querySelector('.m-medical-card__title');
                        const cardTitle = cardTitleEl ? cardTitleEl.textContent.trim() : '';
                        const cardImgEl = card.querySelector('.m-medical-card__img');
                        const cardImg = cardImgEl ? cardImgEl.getAttribute('src') : '';
                        subContent += `
                            <a href="${cardHref}" class="m-mobile-card" title="${cardTitle}">
                                <div class="m-mobile-card__img-box">
                                    <img src="${cardImg}" alt="${cardTitle}" class="m-mobile-card__img">
                                </div>
                                <div class="m-mobile-card__title">${cardTitle}</div>
                            </a>
                        `;
                    });
                    subContent += `</div>`;
                } else {
                    // 一般列表 (可能是多欄位或是單一列表)
                    const columns = mega.querySelectorAll('.m-mega__column');
                    if (columns.length > 0) {
                        columns.forEach(col => {
                            const colTitleEl = col.querySelector('.m-mega__title');
                            const colTitle = colTitleEl ? colTitleEl.textContent.trim() : '';
                            subContent += `
                                <div class="m-mobile-group">
                                    ${colTitle ? `<h5 class="m-mobile-group__title" title="${colTitle}">${colTitle}</h5>` : ''}
                                    <ul class="m-mobile-sub-list">
                            `;
                            
                            // 強化：支援所有嵌套層級的列表 (Nested Sub-lists)
                            const topLevelLis = col.querySelectorAll('.m-mega__list > li');
                            topLevelLis.forEach(li => {
                                const mainA = li.querySelector(':scope > a');
                                if (!mainA) return;
                                
                                const subUl = li.querySelector(':scope > ul');
                                if (subUl) {
                                    // 產生行動版折疊結構
                                    const title = mainA.textContent.trim();
                                    subContent += `
                                        <li class="m-mobile-sub-item-has-child">
                                            <a href="javascript:void(0)" class="m-mobile-sub-link js-mega-sub-toggle" title="${title}">
                                                ${title}
                                            </a>
                                            <ul class="m-mega__sub-list">
                                    `;
                                    subUl.querySelectorAll('li a').forEach(subA => {
                                        subContent += `<li><a href="${subA.getAttribute('href')}" class="m-mobile-sub-link" title="${subA.textContent.trim()}">${subA.textContent.trim()}</a></li>`;
                                    });
                                    subContent += `</ul></li>`;
                                } else {
                                    // 一般單層項目
                                    subContent += `<li><a href="${mainA.getAttribute('href')}" class="m-mobile-sub-link" title="${mainA.textContent.trim()}">${mainA.textContent.trim()}</a></li>`;
                                }
                            });
                            subContent += `</ul></div>`;
                        });
                    } else {
                        // 簡單單一列表 (沒有 .m-mega__column，例如 m-nav__item--dropdown)
                        const simpleList = mega.querySelector('.m-mega__list');
                        if (simpleList) {
                            subContent += `
                                <div class="m-mobile-group">
                                    <ul class="m-mobile-sub-list">
                            `;
                            const topLevelLis = simpleList.querySelectorAll(':scope > li');
                            topLevelLis.forEach(li => {
                                const mainA = li.querySelector(':scope > a');
                                if (!mainA) return;
                                
                                const subUl = li.querySelector(':scope > ul');
                                if (subUl) {
                                    const title = mainA.textContent.trim();
                                    subContent += `
                                        <li class="m-mobile-sub-item-has-child">
                                            <a href="javascript:void(0)" class="m-mobile-sub-link js-mega-sub-toggle" title="${title}">
                                                ${title}
                                            </a>
                                            <ul class="m-mega__sub-list">
                                    `;
                                    subUl.querySelectorAll('li a').forEach(subA => {
                                        subContent += `<li><a href="${subA.getAttribute('href')}" class="m-mobile-sub-link" title="${subA.textContent.trim()}">${subA.textContent.trim()}</a></li>`;
                                    });
                                    subContent += `</ul></li>`;
                                } else {
                                    subContent += `<li><a href="${mainA.getAttribute('href')}" class="m-mobile-sub-link" title="${mainA.textContent.trim()}">${mainA.textContent.trim()}</a></li>`;
                                }
                            });
                            subContent += `</ul></div>`;
                        }
                    }
                }

                subLayer.innerHTML = `
                    <div class="m-mobile-header">
                        <button class="m-mobile-btn m-back-trigger">
                            <svg viewBox="0 0 24 24"><path d="M15 18l-6-6 6-6"></path></svg>
                        </button>
                        <span class="m-mobile-header__title">${title}</span>
                        <button class="m-mobile-btn m-close-trigger">
                            <svg viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"></path></svg>
                        </button>
                    </div>
                    <div class="m-mobile-body">${subContent}</div>
                `;
                subLayersFragment.appendChild(subLayer);
            } else {
                // 沒有下拉選單的直接連結
                li.innerHTML = `
                    <a href="${href}" class="m-mobile-link" title="${title}">
                        ${title}
                    </a>
                `;
            }
            mobileMainList.appendChild(li);
        });

        // --- 3. 渲染到 DOM ---
        mobileContainer.innerHTML = '';
        mobileContainer.appendChild(mainLayer);
        mobileContainer.appendChild(subLayersFragment);
    }

    // 執行同步
    syncNavigation();

    // 5-1. 動態捲動陰影邏輯
    window.addEventListener('scroll', () => {
        if (window.scrollY > 20) {
            header.classList.add('is-scrolled');
        } else {
            header.classList.remove('is-scrolled');
        }
    });

    // 5-2. 行動版選單開關
    function openMobileMenu() {
        sidebar.classList.add('active');
        overlay.classList.add('active');
    }

    function closeMobileMenu() {
        sidebar.classList.remove('active');
        overlay.classList.remove('active');
        // 延遲重置，避免動畫中斷
        setTimeout(() => {
            mobileContainer.classList.remove('is-sub-active');
        }, 400);
    }

    if (toggle) toggle.addEventListener('click', openMobileMenu);
    if (overlay) overlay.addEventListener('click', closeMobileMenu);

    // 5-3. 鑽取式切換邏輯 (使用事件委派以支援動態生成內容)
    mobileContainer.addEventListener('click', function(e) {
        // A. 進入子層
        const subTrigger = e.target.closest('.m-sub-trigger');
        if (subTrigger) {
            const targetId = subTrigger.getAttribute('data-target');
            const targetLayer = document.getElementById(targetId);
            if (targetLayer) {
                // 隱藏所有子層
                document.querySelectorAll('.m-sub-layer').forEach(layer => layer.classList.remove('is-active'));
                targetLayer.classList.add('is-active');
                mobileContainer.classList.add('is-sub-active');
            }
            return;
        }

        // B. 返回上一層
        if (e.target.closest('.m-back-trigger')) {
            mobileContainer.classList.remove('is-sub-active');
            return;
        }

        // C. 關閉按鈕
        if (e.target.closest('.m-close-trigger')) {
            closeMobileMenu();
            return;
        }

        // D. 點擊子連結或卡片後自動關閉 (排除折疊觸發器)
        const isToggle = e.target.closest('.js-mega-sub-toggle');
        if (!isToggle && (e.target.closest('.m-mobile-sub-link') || e.target.closest('.m-mobile-card'))) {
            closeMobileMenu();
        }
    });

    // 5-4. 鍵盤 ESC 關閉支援
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && sidebar.classList.contains('active')) closeMobileMenu();
    });

    // 5-5. 桌機版點擊切換邏輯 (防止刷新並支援點擊展開)
    const desktopLinks = document.querySelectorAll('.m-nav__link[href^="javascript:void(0)"]');
    desktopLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const parent = link.parentElement;
            const isActive = parent.classList.contains('is-active');
                
            // 關閉其他已開啟的菜單
            document.querySelectorAll('.m-nav__item').forEach(item => {
                if (item !== parent) item.classList.remove('is-active');
            });
                
            // 切換當前菜單
            parent.classList.toggle('is-active');
        });
    });

    // 點擊空白處關閉桌機菜單
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.m-nav__item')) {
            document.querySelectorAll('.m-nav__item').forEach(item => item.classList.remove('is-active'));
        }
    });
})();


// ==========================================
// 長安醫院通用自適應 AJAX 分頁驅動器
// ==========================================
(function() {
    // 1. 監聽方向鍵與頁碼點擊
    document.addEventListener('click', function(e) {
        const link = e.target.closest('a[data-ajax-target]');
        if (!link) return;
        
        // 阻止預設換頁行為
        e.preventDefault();
        
        const url = link.getAttribute('href');
        const targetSelector = link.getAttribute('data-ajax-target');
        const scrollSelector = link.getAttribute('data-ajax-scroll');
        const pushState = link.getAttribute('data-ajax-pushstate') === 'true';
        
        if (!url || url === '#' || url === 'javascript:void(0);') return;
        
        // 檢查是否處於 disabled 或是 active 狀態
        const li = link.closest('.page-item');
        if (li && (li.classList.contains('disabled') || li.classList.contains('active'))) return;
        
        triggerGlobalAjaxPage(url, targetSelector, scrollSelector, pushState);
    });

    // 2. 監聽下拉選單變更
    document.addEventListener('change', function(e) {
        const select = e.target.closest('select[data-ajax-target]');
        if (!select) return;
        
        const targetSelector = select.getAttribute('data-ajax-target');
        const scrollSelector = select.getAttribute('data-ajax-scroll');
        const pushState = select.getAttribute('data-ajax-pushstate') === 'true';
        
        // 取得基礎網址與參數名稱
        const baseUrl = select.getAttribute('data-url-base') || window.location.pathname;
        const paramName = select.getAttribute('data-param-name') || 'page';
        const pageVal = select.value;
        
        // 組裝 URL
        let url;
        try {
            const urlObj = new URL(baseUrl, window.location.origin);
            urlObj.searchParams.set(paramName, pageVal);
            url = urlObj.pathname + urlObj.search;
        } catch(err) {
            const connector = baseUrl.includes('?') ? '&' : '?';
            url = baseUrl + connector + paramName + '=' + pageVal;
        }
        
        triggerGlobalAjaxPage(url, targetSelector, scrollSelector, pushState);
    });

    // 3. 處理瀏覽器上/下一頁歷史紀錄 (只對啟用 pushState 的容器起作用)
    window.addEventListener('popstate', function(e) {
        if (e.state && e.state.globalAjaxUrl && e.state.globalAjaxTarget) {
            triggerGlobalAjaxPage(e.state.globalAjaxUrl, e.state.globalAjaxTarget, e.state.globalAjaxScroll, false);
        }
    });

    // 4. 核心通用 AJAX 漸變切換與定位函式
    function triggerGlobalAjaxPage(url, targetSelector, scrollSelector, pushState) {
        const container = document.querySelector(targetSelector);
        if (!container) return;
        
        // 漸變淡出
        container.style.transition = 'opacity 0.3s cubic-bezier(0.4, 0, 0.2, 1)';
        container.style.opacity = '0';
        
        setTimeout(() => {
            fetch(url, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
            .then(response => {
                if (!response.ok) throw new Error('Network response was not ok');
                return response.text();
            })
            .then(html => {
                const parser = new DOMParser();
                const doc = parser.parseFromString(html, 'text/html');
                
                // 取得新內容：若後端回傳完整頁面，提取指定選擇器；若後端僅回傳局部範本，則直接取 body 內容
                const newContent = doc.querySelector(targetSelector);
                const updatedHTML = newContent ? newContent.innerHTML : (doc.body ? doc.body.innerHTML : html);
                
                if (updatedHTML) {
                    container.innerHTML = updatedHTML;
                    
                    // 支援 pushState 瀏覽器歷史紀錄
                    if (pushState) {
                        history.pushState({ 
                            globalAjaxUrl: url, 
                            globalAjaxTarget: targetSelector, 
                            globalAjaxScroll: scrollSelector 
                        }, '', url);
                    }
                    
                    // 平滑滾動到指定的定位點 (例如標題)
                    if (scrollSelector) {
                        const scrollEl = document.querySelector(scrollSelector);
                        if (scrollEl) {
                            if (window.jQuery) {
                                window.jQuery('html, body').animate({
                                    scrollTop: window.jQuery(scrollSelector).offset().top - 80
                                }, 200);
                            } else {
                                scrollEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            }
                        }
                    }
                }
                
                // 漸變淡入
                container.style.opacity = '1';
            })
            .catch(error => {
                console.error('AJAX分頁載入失敗:', error);
                container.style.opacity = '1';
                // 降級處理：若失敗則直接跳轉
                window.location.href = url;
            });
        }, 300);
    }
})();



