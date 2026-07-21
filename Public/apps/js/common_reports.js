function loadMediaArticles(page = 1) {
	// 使用 HTML 傳過來的 API_URL_MEDIA 變數
	fetch(`${API_URL_MEDIA}?page=${page}`)
		// .then(res => res.json())
		.then(res => {
			if (!res.ok) throw new Error("API 錯誤：" + res.status);
			return res.json();
		})
		.then(data => {
			const container = document.getElementById('media-articles-container');
			container.innerHTML = '';

			// （data.articles 為空時）
			if (!data.articles || data.articles.length === 0) {
				container.innerHTML = `
					<div class="col-12 text-center my-5">
						<p class="text-muted mb-0 h3">暫無媒體報導</p>
					</div>
				`;
				document.getElementById("pagination-list").innerHTML = "";
				updateItemListSchema([]); // 清空可能存在的舊 Schema
				return;
			}

			// 更新 ItemList 結構化資料
			updateItemListSchema(data.articles);

			if (data.articles && data.articles.length > 0) {
				let html = '<div class="newspaper-grid">';
				let cellIndex = 0;
				
				for (let i = 0; i < data.articles.length; i++) {
					const article = data.articles[i];
					const pubDate = article.pub_date || '';
					const title = article.title || '';
					const summary = article.summary || '';
					const webpImg = `/media/${article.image}`;
					const img = webpImg.replace('/thumb_webp/', '/').replace('/img_webp_article/', '/').replace('/img_webp_news/', '/').replace(/\.webp$/i, '.jpg');
					const url = article.url || '#';

					// 採用 7 篇一循環的現代排版，剛好完美填滿 3 欄式網格（無空白）
					const patternIndex = cellIndex % 7;

					if (patternIndex === 0) {
						// 1. 頭條 (Hero) - 滿兩格寬，大圖
						html += `
							<a href="${url}" class="np-card np-hero">
								<figure class="m-0">
									<picture>
										<source srcset="${webpImg}" type="image/webp">
										<img src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
									</picture>
									<figcaption class="d-none">${title}</figcaption>
								</figure>
								<div class="np-content">
									<div class="np-meta">最新報導</div>
									<h2 class="np-title">${title}</h2>
									<p class="np-desc">${summary}</p>
									<div class="np-date">${pubDate}</div>
								</div>
							</a>
						`;
					} else if (patternIndex === 1 || patternIndex === 3) {
						// 2. 拆分為上下兩塊的暗黑快訊 (Stacked Brief Dark)
						html += `<div class="d-flex flex-column h-100" style="gap: 24px;">`;
						
						// 第一筆
						html += `
							<a href="${url}" class="np-card np-brief-dark flex-grow-1" style="--bg-img: url('${img}');">
								<div class="np-content" style="padding: 20px; z-index: 1;justify-content: end;">
									<div class="np-meta">編輯精選</div>
									<h3 class="np-title" style="-webkit-line-clamp: 2; font-size: 1.25rem;">${title}</h3>
									<!-- <p class="np-desc" style="-webkit-line-clamp: 2; margin-bottom: 12px;">${summary}</p> -->
									<div class="np-date" style="margin-top: 0;">${pubDate}</div>
								</div>
							</a>
						`;

						// 第二筆 (如果有)
						if (i + 1 < data.articles.length) {
							i++; // 消耗下一筆資料
							const article2 = data.articles[i];
							const pubDate2 = article2.pub_date || '';
							const title2 = article2.title || '';
							const summary2 = article2.summary || '';
							const webpImg2 = `/media/${article2.image}`;
							const img2 = webpImg2.replace('/thumb_webp/', '/').replace('/img_webp_article/', '/').replace('/img_webp_news/', '/').replace(/\.webp$/i, '.jpg');
							const url2 = article2.url || '#';
							
							html += `
								<a href="${url2}" class="np-card np-brief-dark flex-grow-1" style="--bg-img: url('${img2}');">
									<div class="np-content" style="padding: 20px; z-index: 1;justify-content: end;">
										<div class="np-meta">編輯精選</div>
										<h3 class="np-title" style="-webkit-line-clamp: 2; font-size: 1.25rem;">${title2}</h3>
										<!-- <p class="np-desc" style="-webkit-line-clamp: 2; margin-bottom: 12px;">${summary2}</p> -->
										<div class="np-date" style="margin-top: 0;">${pubDate2}</div>
									</div>
								</a>
							`;
						}
						
						html += `</div>`;
					} else if (patternIndex === 5) {
						// 3. 橫幅重點 (Highlight) - 橫向卡片，改為兩筆上下排列
						html += `<div class="np-highlight-wrapper d-flex flex-column h-100" style="gap: 24px;">`;
						
						// 第一筆
						html += `
							<a href="${url}" class="np-card np-highlight flex-grow-1">
								<figure class="m-0">
									<picture>
										<source srcset="${webpImg}" type="image/webp">
										<img src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
									</picture>
									<figcaption class="d-none">${title}</figcaption>
								</figure>
								<div class="np-content">
									<div class="np-meta">特別企劃</div>
									<h3 class="np-title">${title}</h3>
									<p class="np-desc">${summary}</p>
									<div class="np-date">${pubDate}</div>
								</div>
							</a>
						`;

						// 第二筆 (如果有)
						if (i + 1 < data.articles.length) {
							i++; // 消耗下一筆資料
							const article2 = data.articles[i];
							const pubDate2 = article2.pub_date || '';
							const title2 = article2.title || '';
							const summary2 = article2.summary || '';
							const webpImg2 = `/media/${article2.image}`;
							const img2 = webpImg2.replace('/thumb_webp/', '/').replace('/img_webp_article/', '/').replace('/img_webp_news/', '/').replace(/\.webp$/i, '.jpg');
							const url2 = article2.url || '#';
							
							html += `
								<a href="${url2}" class="np-card np-highlight flex-grow-1">
									<figure class="m-0">
										<picture>
											<source srcset="${webpImg2}" type="image/webp">
											<img src="${img2}" alt="${title2}" title="${title2}" loading="lazy" decoding="async">
										</picture>
										<figcaption class="d-none">${title2}</figcaption>
									</figure>
									<div class="np-content">
										<div class="np-meta">特別企劃</div>
										<h3 class="np-title">${title2}</h3>
										<p class="np-desc">${summary2}</p>
										<div class="np-date">${pubDate2}</div>
									</div>
								</a>
							`;
						}
						html += `</div>`;
					} else {
						// 4. 標準卡 (Standard)
						html += `
							<a href="${url}" class="np-card np-standard">
								<figure class="m-0">
									<picture>
										<source srcset="${webpImg}" type="image/webp">
										<img src="${img}" alt="${title}" title="${title}" loading="lazy" decoding="async">
									</picture>
									<figcaption class="d-none">${title}</figcaption>
								</figure>
								<div class="np-content">
									<div class="np-meta" style="color: var(--secondary);">媒體報導</div>
									<h4 class="np-title">${title}</h4>
									<!-- <p class="np-desc">${summary}</p> -->
									<div class="np-date">${pubDate}</div>
								</div>
							</a>
						`;
					}
					
					cellIndex++;
				}
				
				html += '</div>';
				container.innerHTML = html;
			}

			const pagination = document.getElementById('pagination-list');
			pagination.innerHTML = '';
			const total = data.total_pages;
			const current = data.current_page;

			if (total > 1) {
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
						<select id="report-page-select" class="form-control form-control-sm h-100" style="width:auto; display:inline-block;">
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
				// 綁定下拉事件
				document.getElementById("report-page-select").addEventListener("change", function() {
					loadMediaArticles(this.value);
				});
			}
		})
		
		// （API 出錯時）
		.catch(err => {
			console.error("[health-reports] API 載入失敗：", err);
			const container = document.getElementById("media-articles-container");
			container.innerHTML = `
				<div class="col-12 text-center my-5">
					<p class="text-danger mb-0 h3">資料載入失敗，請稍後再試。</p>
				</div>
			`;
			document.getElementById("pagination-list").innerHTML = "";
		});
}

// 點擊分頁
$(document).on("click", "#pagination-list .page-link", function(e) {
	e.preventDefault();
	if ($(this).parent().hasClass("disabled")) return; // disabled 的不觸發
	let page = $(this).data("page");
	if (page) loadMediaArticles(page);
});

// 初始載入
document.addEventListener("DOMContentLoaded", () => {
	loadMediaArticles(1);
});

// 動態產生並插入 ItemList 結構化資料
function updateItemListSchema(articles) {
	// 移除舊的 schema 以免切換分頁時重複添加
	const oldSchema = document.getElementById('dynamic-itemlist-schema');
	if (oldSchema) {
		oldSchema.remove();
	}

	if (!articles || articles.length === 0) return;

	// 將 API 拿到的文章陣列轉換成 ItemList 需要的格式
	const itemListElements = articles.map((article, index) => {
		// 確保網址是絕對路徑
		const absoluteUrl = new URL(article.url || '#', window.location.origin).href;
		
		return {
			"@type": "ListItem",
			"position": index + 1,
			"url": absoluteUrl,
			"name": article.title || '媒體報導'
		};
	});

	const schemaData = {
		"@context": "https://schema.org",
		"@type": "ItemList",
		"itemListElement": itemListElements
	};

	// 建立 <script> 標籤並塞入 <head>
	const script = document.createElement('script');
	script.id = 'dynamic-itemlist-schema';
	script.type = 'application/ld+json';
	script.text = JSON.stringify(schemaData);
	document.head.appendChild(script);
}