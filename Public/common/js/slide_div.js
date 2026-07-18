document.addEventListener("DOMContentLoaded", () => {
    // ==========================================
    // 1. Native Fade Slider (主視覺 Banner)
    // ==========================================
    class NativeFadeSlider {
        constructor(container) {
            this.container = container;
            this.slides = container.querySelectorAll('.slide-item');
            this.dots = container.querySelectorAll('.banner-dots .dot');
            this.btnPrev = container.querySelector('.banner_arrow_left');
            this.btnNext = container.querySelector('.banner_arrow_right');
            this.currentIndex = 0;
            this.timer = null;
            this.interval = 5000;

            if (this.slides.length === 0) return;

            this.init();
        }

        init() {
            this.updateView();

            if (this.btnPrev) this.btnPrev.addEventListener('click', (e) => { e.preventDefault(); this.prev(); this.resetTimer(); });
            if (this.btnNext) this.btnNext.addEventListener('click', (e) => { e.preventDefault(); this.next(); this.resetTimer(); });
            
            this.dots.forEach((dot, index) => {
                dot.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.goTo(index);
                    this.resetTimer();
                });
            });

            // 加入觸控滑動 (Swipe) 支援
            let touchStartX = 0;
            let touchEndX = 0;
            
            this.container.addEventListener('touchstart', e => {
                touchStartX = e.changedTouches[0].screenX;
            }, { passive: true });
            
            this.container.addEventListener('touchend', e => {
                touchEndX = e.changedTouches[0].screenX;
                this.handleSwipe();
            }, { passive: true });

            this.handleSwipe = () => {
                const threshold = 50; // 最小滑動距離
                if (touchEndX < touchStartX - threshold) {
                    this.next();
                    this.resetTimer();
                }
                if (touchEndX > touchStartX + threshold) {
                    this.prev();
                    this.resetTimer();
                }
            };

            this.startTimer();
        }

        updateView() {
            this.slides.forEach((slide, idx) => {
                slide.classList.toggle('active', idx === this.currentIndex);
            });
            this.dots.forEach((dot, idx) => {
                dot.classList.toggle('active', idx === this.currentIndex);
            });
        }

        next() {
            this.currentIndex = (this.currentIndex + 1) % this.slides.length;
            this.updateView();
        }

        prev() {
            this.currentIndex = (this.currentIndex - 1 + this.slides.length) % this.slides.length;
            this.updateView();
        }

        goTo(index) {
            this.currentIndex = index;
            this.updateView();
        }

        startTimer() {
            this.timer = setInterval(() => this.next(), this.interval);
        }

        resetTimer() {
            clearInterval(this.timer);
            this.startTimer();
        }
    }

    document.querySelectorAll('.native-banner-container').forEach(container => {
        new NativeFadeSlider(container);
    });

    // ==========================================
    // 2. Native Scroll Slider (重點醫療)
    // ==========================================
    class NativeScrollSlider {
        constructor(wrapper) {
            this.slider = wrapper.querySelector('.native-scroll-slider');
            this.btnPrev = wrapper.querySelector('.arrow_btleft');
            this.btnNext = wrapper.querySelector('.arrow_btright');
            this.timer = null;
            this.interval = 2000;

            if (!this.slider) return;
            this.init();
        }

        init() {
            if (this.btnPrev) this.btnPrev.addEventListener('click', () => { this.scroll(-1); this.resetTimer(); });
            if (this.btnNext) this.btnNext.addEventListener('click', () => { this.scroll(1); this.resetTimer(); });
            
            // 當使用者手動滑動時，重置計時器避免干擾
            this.slider.addEventListener('scroll', () => {
                clearInterval(this.timer);
                // 停止滑動後 3 秒再恢復自動播放
                clearTimeout(this.scrollTimeout);
                this.scrollTimeout = setTimeout(() => this.startTimer(), 3000);
            }, { passive: true });

            this.startTimer();
        }

        scroll(direction) {
            const firstItem = this.slider.querySelector('.slide-item');
            if (!firstItem) return;
            const scrollAmount = firstItem.offsetWidth * direction;
            
            // 判斷是否到底部，如果到底則跳回第一張，反之亦然
            if (direction === 1 && this.slider.scrollLeft + this.slider.clientWidth >= this.slider.scrollWidth - 10) {
                this.slider.scrollTo({ left: 0, behavior: 'smooth' });
            } else if (direction === -1 && this.slider.scrollLeft <= 10) {
                this.slider.scrollTo({ left: this.slider.scrollWidth, behavior: 'smooth' });
            } else {
                this.slider.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            }
        }

        startTimer() {
            clearInterval(this.timer);
            this.timer = setInterval(() => this.scroll(1), this.interval);
        }

        resetTimer() {
            clearInterval(this.timer);
            this.startTimer();
        }
    }

    document.querySelectorAll('.slider-wrapper').forEach(wrapper => {
        new NativeScrollSlider(wrapper);
    });
});