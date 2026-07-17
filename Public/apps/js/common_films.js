// ■■■■■■■■■■■■■■■■■■■■■■■■■■ 影音專區 Health Films ■■■■■■■■■■■■■■■■■■■■■■■■■■

let allVideos = [];
let featuredVideo = null;
let remainingVideos = [];
let currentFilteredVideos = [];
let currentPage = 1;
const pageSize = 9;

// 預設團隊名稱 (可由外部 HTML 或其他 JS 設定 window.DEFAULT_TEAM_NAME 覆寫)
const DEFAULT_TEAM_NAME = window.DEFAULT_TEAM_NAME || '長安醫院醫療團隊';

const CATEGORIES = {
	1: { name: '長安的故事', class: 'cat-1' },
	2: { name: '長安保健室', class: 'cat-2' },
	4: { name: '醫師談健康', class: 'cat-4' }
};

function fetchAndInitVideos() {
	$.get(API_URL_FILM, { per_page: 'all' }, function(res) {
		if (!res.videos || res.videos.length === 0) {
			$('#video-list').html(`
				<div class="col-12 text-center my-5">
					<p class="text-muted">目前暫無影音文章</p>
				</div>
			`);
			$('#pagination').empty();
			return;
		}

		allVideos = res.videos;
		featuredVideo = allVideos[0];
		remainingVideos = allVideos.slice(1);

		// 1. 渲染推薦影片 (最新的一筆)
		renderFeaturedVideo(featuredVideo);

		// 2. 動態生成分類按鈕
		generateFilterButtons(allVideos);

		// 3. 渲染預設分類 (全部影片)
		renderCategory('all');
	}).fail(function() {
		$('#video-list').html(`
			<div class="col-12 text-center my-5">
				<p class="text-muted">載入影音資料失敗，請稍後再試。</p>
			</div>
		`);
	});
}

function renderFeaturedVideo(v) {
	if (!v) return;
	const container = $('#featured-video-container');
	const detailUrl = v.video_key ? URL_FILM_DETAIL.replace('PLACEHOLDER', v.video_key) : v.youtube_url;
	container.attr('href', detailUrl);
	container.attr('target', '_blank');
	container.attr('data-no-loading', 'true');
	container.attr('data-url', v.youtube_url);
	const featuredImg = document.getElementById('featured-video-img');
	if (featuredImg) {
		featuredImg.removeAttribute('onerror');
		featuredImg.onload = function() {
			if (this.naturalWidth <= 120) {
				this.onload = null;
				this.src = `https://img.youtube.com/vi/${v.youtube_id}/hqdefault.jpg`;
			}
		};
		featuredImg.src = v.youtube_image;
		featuredImg.alt = v.title;
	}
	$('#featured-video-title').text(v.title);
	
	// 自動使用切分出的醫師資訊作為副標題
	const desc = v.description ? `主講：${v.description}` : '了解日常預防與照護關鍵，由專業醫師親自為您解析。';
	$('#featured-video-desc').text(desc);
	
	// 動態顯示影片秒數資訊
	const durationText = v.duration ? ` (${v.duration})` : '';
	$('#featured-video-btn-text').text(`立即觀看${durationText}`);
	
	container.fadeIn(300);
}

function generateFilterButtons(videos) {
	const activeIndices = new Set();
	videos.forEach(v => {
		if (v.category_index !== null && CATEGORIES[v.category_index]) {
			activeIndices.add(v.category_index);
		}
	});

	const filterControls = $('#filter-controls');
	filterControls.html('<button class="filter-chip active" data-category="all">全部影片</button>');

	// 依索引值排序並動態生成按鈕
	const sortedIndices = Array.from(activeIndices).sort((a, b) => a - b);
	sortedIndices.forEach(idx => {
		filterControls.append(`
			<button class="filter-chip" data-category="${idx}">${CATEGORIES[idx].name}</button>
		`);
	});

	// 綁定點擊事件
	$('.filter-chip').off('click').on('click', function() {
		$('.filter-chip').removeClass('active');
		$(this).addClass('active');
		const cat = $(this).data('category');
		renderCategory(cat);
	});
}

// 隨機選取指定數量子陣列的輔助函式
function getRandomSubarray(arr, size) {
	let shuffled = arr.slice(0), i = arr.length, temp, index;
	while (i--) {
		index = Math.floor((i + 1) * Math.random());
		temp = shuffled[index];
		shuffled[index] = shuffled[i];
		shuffled[i] = temp;
	}
	return shuffled.slice(0, size);
}

function renderCategory(category) {
	currentPage = 1;
	
	if (category === 'all') {
		// 全部影片：將精選影片外的其餘影片進行一次性隨機打散，並支援分頁顯示
		currentFilteredVideos = getRandomSubarray(remainingVideos, remainingVideos.length);
	} else {
		// 依分類索引值篩選影片，支援分頁顯示
		const catIdx = parseInt(category);
		currentFilteredVideos = allVideos.filter(v => v.category_index === catIdx);
	}

	renderCurrentPage();
}

function renderCurrentPage() {
	const videoList = $('#video-list');
	
	// 清空並重新渲染卡片，瀏覽器會自動套用 CSS @keyframes staggered 動畫效果
	videoList.empty();
	
	const totalPages = Math.ceil(currentFilteredVideos.length / pageSize);
	const pageVideos = currentFilteredVideos.slice((currentPage - 1) * pageSize, currentPage * pageSize);

	if (pageVideos.length === 0) {
		videoList.html(`
			<div class="col-12 text-center my-5">
				<p class="text-muted">此分類目前暫無影音文章</p>
			</div>
		`);
		$('#pagination').empty();
		return;
	}

	pageVideos.forEach((v, index) => {
		const catObj = CATEGORIES[v.category_index] || { name: '衛教影音', class: 'cat-default' };
		const durationText = v.duration || '05:00';
		const doctorName = v.description || DEFAULT_TEAM_NAME;
		const delay = index * 50; // 卡片依序滑入延遲 (毫秒)
		const detailUrl = v.video_key ? URL_FILM_DETAIL.replace('PLACEHOLDER', v.video_key) : v.youtube_url;

		videoList.append(`
			<div style="animation-delay: ${delay}ms;">
				<a href="${detailUrl}" target="_blank" data-no-loading="true" class="video-card-wrapper" data-url="${v.youtube_url}">
					<figure class="video-card" data-url="${v.youtube_url}">
						<div class="video-thumb">
							<img src="${v.youtube_image}" class="card-img-top" alt="${v.filename_title}" onload="if(this.naturalWidth <= 120) { this.onload=null; this.src='https://img.youtube.com/vi/${v.youtube_id}/hqdefault.jpg'; }" onerror="this.onerror=null; this.src='https://img.youtube.com/vi/${v.youtube_id}/hqdefault.jpg';">
							<div class="play-btn-small-overlay">
								<div class="play-btn-small">
									<span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">play_arrow</span>
								</div>
							</div>
							<div class="video-duration">${durationText}</div>
						</div>
						<figcaption class="video-card-content">
							<div class="video-card-meta-row">
								<div class="video-category ${catObj.class}">${catObj.name}</div>
								<span class="video-card-meta">上架時間：${v.date}</span>
							</div>
							<h5 class="video-card-title">${v.filename_title}</h5>
							<span class="video-card-doctor">主講：${doctorName}</span>
						</figcaption>
					</figure>
				</a>
			</div>
		`);
	});

	// 渲染分頁控制器
	renderPaginationControls(currentPage, totalPages);
}

function renderPaginationControls(current, total) {
	const pagination = $('#pagination');
	pagination.empty();
	if (total <= 1) return;

	// 第一頁
	pagination.append(`
		<li class="page-item ${current === 1 ? 'disabled' : ''}">
			<a class="page-link" href="#" data-page="1">&laquo;</a>
		</li>
	`);

	// 上一頁
	pagination.append(`
		<li class="page-item ${current === 1 ? 'disabled' : ''}">
			<a class="page-link" href="#" data-page="${current - 1}">&lsaquo;</a>
		</li>
	`);

	// 下拉選單頁碼切換
	let selectHtml = `
		<li class="page-item">
			<select id="video-page-select" class="form-control form-control-sm h-100" style="width:auto; display:inline-block; border-color:#dee2e6;">
	`;
	for (let i = 1; i <= total; i++) {
		selectHtml += `<option value="${i}" ${i === current ? 'selected' : ''}>第 ${i} 頁 / 共 ${total} 頁</option>`;
	}
	selectHtml += `</select></li>`;
	pagination.append(selectHtml);

	// 下一頁
	pagination.append(`
		<li class="page-item ${current === total ? 'disabled' : ''}">
			<a class="page-link" href="#" data-page="${current + 1}">&rsaquo;</a>
		</li>
	`);

	// 最後頁
	pagination.append(`
		<li class="page-item ${current === total ? 'disabled' : ''}">
			<a class="page-link" href="#" data-page="${total}">&raquo;</a>
		</li>
	`);

	// 下拉選單值變動事件
	$('#video-page-select').off('change').on('change', function() {
		goToPage(parseInt($(this).val()));
	});
}

function goToPage(page) {
	currentPage = page;
	renderCurrentPage();
}

// 點擊分頁頁碼連結
$(document).on('click', '#pagination .page-link', function(e) {
	e.preventDefault();
	if ($(this).parent().hasClass('disabled')) return;
	const page = $(this).data('page');
	if (page) goToPage(page);
});



// 推薦影片點擊 Modal 播放（攔截預設 `<a>` 跳轉）
$(document).on('click', '#featured-video-container', function (e) {
	// 如果是按住 Ctrl, Shift, Meta (Mac Command) 鍵點擊，或是滑鼠中鍵點擊，則放行讓瀏覽器正常在新分頁打開詳情頁
	if (e.ctrlKey || e.shiftKey || e.metaKey || e.which === 2) {
		return;
	}
	e.preventDefault();
	const url = $(this).attr('data-url');
	const title = $(this).find('#featured-video-title').text();
	if (url) openVideoModal(url, title);
});

// 清單影片點擊 Modal 播放（攔截預設 `<a>` 跳轉）
$(document).on('click', '.video-card-wrapper', function (e) {
	// 如果是按住 Ctrl, Shift, Meta (Mac Command) 鍵點擊，或是滑鼠中鍵點擊，則放行讓瀏覽器正常在新分頁打開詳情頁
	if (e.ctrlKey || e.shiftKey || e.metaKey || e.which === 2) {
		return;
	}
	e.preventDefault();
	const url = $(this).attr('data-url');
	const title = $(this).find('.video-card-title').text();
	if (url) openVideoModal(url, title);
});

// Modal 關閉時清空影片 iframe src
$('#videoModal').on('hidden.bs.modal', function () {
	$('#videoFrame').attr('src', '');
});

// 頁面初始化
$(document).ready(() => {
	fetchAndInitVideos();
});