$(document).ready(function() {
    // 首頁-文宣輪播
    $('.banner').slick({
        dots: true,
        infinite: true,
        nextArrow: '<button type="button" class="banner_arrow_right slick-arrow-btn"><i class="fas fa-angle-right"></i></button>',
        prevArrow: '<button type="button" class="banner_arrow_left slick-arrow-btn"><i class="fas fa-angle-left fa-1x"></i></button>',                
        slidesToShow: 1,
        autoplay: true,
        autoplaySpeed: 5000,
        adaptiveHeight: true,
        speed: 500,
        fade: true,
        cssEase: 'linear',
        lazyLoad: 'ondemand' // 啟用 lazyLoad 懶載入
    });
    // 首頁-媒體報導區
    $('.media_reports').slick({
        // dots: true,
        infinite: true,
        nextArrow: '<button type="button" class="arrow_btright slick-arrow-btn btn btn-outline-warning"><i class="fas fa-angle-right"></i></button>',
        prevArrow: '<button type="button" class="arrow_btleft slick-arrow-btn btn btn-outline-warning"><i class="fas fa-angle-left fa-1x"></i></button>',
        speed: 300,
        slidesToShow: 4,
        slidesToScroll: 1,
        responsive: [
            {
                breakpoint: 1024,
                settings: {
                    slidesToShow: 2,
                    slidesToScroll: 2,
                    infinite: true,
                    dots: true
                }
            },
            {
                breakpoint: 600,
                settings: {
                    slidesToShow: 2,
                    slidesToScroll: 2
                }
            },
            {
                breakpoint: 480,
                settings: {
                    slidesToShow: 1,
                    slidesToScroll: 1
                }
            }
        ]
    });
    // 首頁-醫療資訊區
    $('.medical_info').slick({
        // dots: true,
        infinite: true,
        nextArrow: '<button type="button" class="arrow_btright slick-arrow-btn btn btn-outline-warning"><i class="fas fa-angle-right"></i></button>',
        prevArrow: '<button type="button" class="arrow_btleft slick-arrow-btn btn btn-outline-warning"><i class="fas fa-angle-left fa-1x"></i></button>',
        speed: 300,
        slidesToShow: 4,
        slidesToScroll: 1,
        responsive: [
            {
                breakpoint: 1024,
                settings: {
                    slidesToShow: 4,
                    slidesToScroll: 4,
                    infinite: true,
                    dots: true
                }
            },
            {
                breakpoint: 600,
                settings: {
                    slidesToShow: 2,
                    slidesToScroll: 2
                }
            },
            {
                breakpoint: 480,
                settings: {
                    slidesToShow: 1,
                    slidesToScroll: 1
                }
            }
        ]
    });
    // 首頁-重點醫療
    $('.slider').slick({
        infinite: true,
        nextArrow: '<button type="button" class="arrow_btright slick-arrow-btn btn btn-outline-warning"><i class="fas fa-angle-right"></i></button>',
        prevArrow: '<button type="button" class="arrow_btleft slick-arrow-btn btn btn-outline-warning"><i class="fas fa-angle-left fa-1x"></i></button>',
        // arrows: true,
        slidesToShow: 3,
        slidesToScroll: 1,
        autoplay: true,
        autoplaySpeed: 2000,
        responsive: [
            {
            breakpoint: 1024,
                settings: {
                slidesToShow: 2,
                slidesToScroll: 2,
                infinite: true,
                dots: true
                }
            },
            {
            breakpoint: 600,
            settings: {
                slidesToShow: 2,
                slidesToScroll: 2
                }
            },
            {
            breakpoint: 480,
            settings: {
                slidesToShow: 1,
                slidesToScroll: 1
                }
            }
        ]
    });
});    