function loadHealthEdu(page = 1, type = 'all', containerId = 'edu-list', paginationId = 'pagination-list') {
	fetch(`${API_URL_EDU}?page=${page}&type=${type}`)
		.then(res => res.json())
		.then(data => {
			const container = document.getElementById(containerId);
			const section = container ? container.closest('div[id^="section-"]') : null;
			container.innerHTML = "";

			// （data.items 為空時）
			if (!data.items || data.items.length === 0) {
				if (section) {
					section.style.display = "none";
				} else {
					container.innerHTML = `<div class="col-12 text-center my-5"><p class="text-muted mb-0 h3">暫無資料</p></div>`;
					document.getElementById(paginationId).innerHTML = "";
				}
				return;
			}
			
			// 有資料時顯示
			if (section) section.style.display = "block";

			data.items.forEach((item, idx) => {
				// 若 API 已回傳 titleId，使用它；否則從第一張圖檔名取前綴
				const titleId = item.titleId || (item.images && item.images.length > 0 ? item.images[0].split('/').pop().split('_page')[0] : '');
				const detailUrl = URL_EDU_DETAIL.replace('PLACEHOLDER', titleId);
				const imageUrl = item.images && item.images.length > 0 ? item.images[0] : '/Public/common/img/everan2.webp';
				let webpUrl = imageUrl;
				if (imageUrl.includes('/media/health_edu/')) {
					webpUrl = imageUrl.replace(/([^\/]+)$/, 'webp/$1').replace(/\.(jpg|jpeg|png)$/i, '.webp');
				}

				const safeTitle = (item.title || '').replace(/"/g, '&quot;');

				container.innerHTML += `
					<div class="col-md-6 col-lg-3 mb-4 d-flex align-items-stretch">
						<a href="${detailUrl}" class="magazine-card">
							<figure class="magazine-img-wrapper m-0">
								<picture>
									<source srcset="${webpUrl}" type="image/webp">
									<img class="img-fluid w-100" src="${imageUrl}" alt="${safeTitle}" title="${safeTitle}" width="1200" height="630" loading="lazy" decoding="async">
								</picture>
								<figcaption class="d-none">${safeTitle}</figcaption>
							</figure>
							<div class="magazine-content">
								<div class="magazine-meta">Health Education</div>
								<h5 class="magazine-title">${item.title}</h5>
								<div class="magazine-read-more">READ MORE</div>
							</div>
						</a>
					</div>
				`;
			});

			// 動態生成 SEO ItemList Schema
			const itemList = {
				"@context": "https://schema.org",
				"@type": "ItemList",
				"itemListElement": data.items.map((item, idx) => {
					const titleId = item.titleId || (item.images && item.images.length > 0 ? item.images[0].split('/').pop().split('_page')[0] : '');
					return {
						"@type": "ListItem",
						"position": idx + 1,
						"url": window.location.origin + URL_EDU_DETAIL.replace('PLACEHOLDER', titleId)
					};
				})
			};

			// 移除舊的動態 Schema (切換分頁時)
			const oldSchema = document.getElementById(`dynamic-itemlist-schema-${type}`);
			if (oldSchema) oldSchema.remove();

			// 注入新的 Schema 到 <head>
			if (data.items.length > 0) {
				const script = document.createElement("script");
				script.id = `dynamic-itemlist-schema-${type}`;
				script.type = "application/ld+json";
				script.text = JSON.stringify(itemList);
				document.head.appendChild(script);
			}


			// 分頁控制
			const pagination = document.getElementById(paginationId);
			const nav = pagination ? pagination.closest('nav') : null;
			if (pagination) pagination.innerHTML = "";

			const total = data.num_pages;
			const current = data.current_page;

			if (total > 1) {
				if (nav) nav.style.display = "block";
				// 第一頁
				pagination.innerHTML += `
					<li class="page-item ${current === 1 ? 'disabled' : ''}">
						<a class="page-link" href="#" data-page="1">&laquo;</a>
					</li>
				`;
				// 上一頁
				pagination.innerHTML += `
					<li class="page-item ${current === 1 ? 'disabled' : ''}">
						<a class="page-link" href="#" data-page="${current - 1}">&lsaquo;</a>
					</li>
				`;
				// 下拉選單
				let selectHtml = `
					<li class="page-item">
						<select class="form-control form-control-sm h-100 edu-page-select" style="width:auto; display:inline-block;">
				`;
				for (let i = 1; i <= total; i++) {
					selectHtml += `<option value="${i}" ${i === current ? 'selected' : ''}>第 ${i} 頁</option>`;
				}
				selectHtml += `</select></li>`;
				pagination.innerHTML += selectHtml;
				// 下一頁
				pagination.innerHTML += `
					<li class="page-item ${current === total ? 'disabled' : ''}">
						<a class="page-link" href="#" data-page="${current + 1}">&rsaquo;</a>
					</li>
				`;
				// 最後頁
				pagination.innerHTML += `
					<li class="page-item ${current === total ? 'disabled' : ''}">
						<a class="page-link" href="#" data-page="${total}">&raquo;</a>
					</li>
				`;
				// 下拉事件 (改由下方委派事件處理)
			} else {
				if (nav) nav.style.display = "none";
			}
		})

		// （API 出錯時）
		.catch(err => {
			const container = document.getElementById(containerId);
			const section = container ? container.closest('div[id^="section-"]') : null;
			if (section) {
				section.style.display = "none";
			} else {
				if (container) container.innerHTML = `<div class="col-12 text-center my-5"><p class="text-danger mb-0 h3">資料載入失敗，請稍後再試。</p></div>`;
				const pagination = document.getElementById(paginationId);
				if (pagination) pagination.innerHTML = "";
			}
		});
}

// 點擊分頁
$(document).on("click", ".edu-pagination .page-link", function(e) {
	e.preventDefault();
	if ($(this).parent().hasClass("disabled")) return;
	let page = $(this).data("page");
	let $nav = $(this).closest('.edu-pagination');
	let type = $nav.data('type') || 'all';
	let listId = $nav.data('list-id') || 'edu-list';
	let paginationId = $nav.attr('id') || 'pagination-list';
	if (page) loadHealthEdu(page, type, listId, paginationId);
});

// 改變下拉選單
$(document).on("change", ".edu-pagination .edu-page-select", function(e) {
	let page = $(this).val();
	let $nav = $(this).closest('.edu-pagination');
	let type = $nav.data('type') || 'all';
	let listId = $nav.data('list-id') || 'edu-list';
	let paginationId = $nav.attr('id') || 'pagination-list';
	if (page) loadHealthEdu(page, type, listId, paginationId);
});

// 向下相容預設載入
document.addEventListener("DOMContentLoaded", () => {
	if (document.getElementById("edu-list")) {
		loadHealthEdu(1);
	}
});