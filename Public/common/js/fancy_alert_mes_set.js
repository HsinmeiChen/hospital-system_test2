// ▼▼▼ Fancybox 效果 ▼▼▼
Fancybox.bind('[data-fancybox]', {
    // Custom options for all galleries
});

// ▼▼▼ Sweet alert2 效果 ▼▼▼

// 登入成功
const login_success = () => {
    let timerInterval;
    Swal.fire({
        title: "登入中...",
        timer: 2000,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {
        Swal.fire({
            title: "登入成功！",
            icon: "success",
            showConfirmButton: false,
            timer: 1500,
        }).then(function(){
            window.location = "Patient_Guide_2_3.html";
        });  
        Fancybox.close();
    });
};	
// 初診單建立結果
const First_data_ok = () => {
    let timerInterval;
    Swal.fire({
        title: "初診資料建立中...",
        timer: 2000,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {
        Swal.fire({
            title: "初診資料建立成功!",
            text: "為您轉到首頁。",
            icon: "success",
            showConfirmButton: false,
            timer: 2000,
        }).then(function(){
            window.location = "/A006_Online_Booking_0_0/";
        });
        // console.log(result)
        // if (result.isConfirmed) {
        //  Swal.fire({
        //      title: "初診資料建立成功!",
        //      icon: "success"
        //  }).then(function(){
        //        window.location = "Patient_Guide_2_4.html";
        //    });
        // }
        // else if (result.isDenied) {
        //  Swal.fire({
        //      title: "初診資料建立失敗！",
        //      text: "請聯繫本院客服人員協助處理，謝謝。",
        //      icon: "error"
        //  });
        // }
        Fancybox.close();
    });
};
// 初診單建立結果
const First_data_error = () => {
    let timerInterval;
    Swal.fire({
        title: "初診資料建立中...",
        timer: 2000,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {
        Swal.fire({
            title: "已有您的看診資料!",
            text: "請重新登入，謝謝。",
            icon: "error",
            showConfirmButton: false,
            timer: 2000,
        }).then(function(){
            window.location = "/A006_Online_Booking_login/";
        });
        // console.log(result)
        // if (result.isConfirmed) {
        //  Swal.fire({
        //      title: "初診資料建立成功!",
        //      icon: "success"
        //  }).then(function(){
        //        window.location = "Patient_Guide_2_4.html";
        //    });
        // }
        // else if (result.isDenied) {
        //  Swal.fire({
        //      title: "初診資料建立失敗！",
        //      text: "請聯繫本院客服人員協助處理，謝謝。",
        //      icon: "error"
        //  });
        // }
        Fancybox.close();
    });
};
// 預約作業結果
const sure_ok = () => {
    // 觸發掛號API
    $( function () {
        $.get("/A006_register/",function(result){
        });
    });


    let timerInterval;
    Swal.fire({
        title: "預約處理中...",
        timer: 7000,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {

        // 觸發掛號API
        $( function () {
            $.get("/A006_find_register/",function(result){
                // alert(result);
                // Swal.fire({
                //     title: "預約成功！!",
                //     icon: "success",
                //     text: "自動為您跳轉到查詢頁面。",
                //     showConfirmButton: false,
                //     timer: 1000,
                // }).then(function(){
                //     window.location = "/A006_Online_Booking_data?visitno=" + result;
                // });
                // Fancybox.close();

                if (result > -1){
                    // Swal.fire({
                    //     title: "預約成功！!",
                    //     icon: "success",
                    //     text: "自動為您跳轉到查詢頁面。",
                    //     showConfirmButton: false,
                    //     timer: 1000,
                    // }).then(function(){
                    window.location = "/A006_Online_Booking_data?visitno=" + result;
                    // });
                    Fancybox.close();
                }
                else if (result < -1000){
                    // Swal.fire({
                    //     title: "預約失敗！!",
                    //     icon: "error",
                    //     text: "請聯繫本院客服人員進行預約作業，謝謝。",
                    //     showConfirmButton: false,
                    //     timer: 1000,
                    // }).then(function(){
                    window.location = "/A006_Online_Booking_data/";
                    // });
                    Fancybox.close();
                }
                else{
                    // Swal.fire({
                    //     title: "等待預約！!",
                    //     icon: "loading",
                    //     text: "自動為您跳轉到查詢頁面。",
                    //     showConfirmButton: false,
                    //     timer: 1000,
                    // }).then(function(){
                    window.location = "/A006_Online_Booking_data/";
                    // });
                    Fancybox.close();
                }
            });
        });

        // console.log(result)
        // if (result.isConfirmed) {
        // 	Swal.fire({
        // 		title: "預約成功!",
        // 		icon: "success"
        // 	});
        // }
        // else if (result.isDenied) {
        // 	Swal.fire({
        // 		title: "預約失敗！",
        // 		text: "請聯繫本院客服人員進行預約作業，謝謝。",
        // 		icon: "error"
        // 	});
        // }
        Fancybox.close();
    });
};
// 退掛處理結果
function sure_cancel_ok(visitdt, recno) {
    let timerInterval;
    // alert(visitdt);
    // alert(recno);

    $.get("/A006_out_register?A006_user_visitdt=" + visitdt + "&A006_user_recno=" + recno,function(result){
        // alert(result);
      });
    Swal.fire({
        title: "取消掛號中...",
        timer: 7000,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {
        $.get("/A006_find_register/",function(result){
            // alert(result);
          });

        Swal.fire({
            title: "已完成退掛！",
            icon: "success",
            // text: "自動為您跳轉到查詢頁面。",
            showConfirmButton: false,
            timer: 1000,
        }).then(function(){
            window.location = "/A006_Online_Booking_data/";
        });

        // console.log(result)
        // if (result.isConfirmed) {
        // 	Swal.fire({
        // 		title: "已完成退掛！",
        // 		icon: "success",
        //      showConfirmButton: false,
        //      timer: 1500,
        // 	});
        // }
        // else if (result.isDenied) {
        // 	Swal.fire({
        // 		title: "退掛失敗！",
        // 		text: "請聯繫本院客服人員進行退掛作業，謝謝。",
        // 		icon: "error"
        // 	});
        // }
        Fancybox.close();
    });    
};
// 登出
const logout_ok = () => {
    let timerInterval;

    $.get("/A006_sign_out/",function(result){
        // alert(result);
      });

    Swal.fire({
        title: "登出中...",
        timer: 1000,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {					
        Swal.fire({						
            title: "已登出成功!",
            // text: "若要請重新登入，謝謝。",
            icon: "success",
            showConfirmButton: false,
            timer: 1000,
        }).then(function(){
            window.location = "/A006_Online_Booking_0/";
        });
        // console.log(result)
        // if (result.isConfirmed) {
        // 	Swal.fire({
        // 		title: "初診資料建立成功!",
        // 		icon: "success"
        // 	}).then(function(){
        //        window.location = "Patient_Guide_2_4.html";
        //    });
        // }
        // else if (result.isDenied) {
        // 	Swal.fire({
        // 		title: "初診資料建立失敗！",
        // 		text: "請聯繫本院客服人員協助處理，謝謝。",
        // 		icon: "error"
        // 	});
        // }
        Fancybox.close();
    });
};
// 彈出預約號碼
function show_visitno(visitno) {
    Swal.fire({
      title: "您的預約號是",
      text: visitno,
      // icon: "success"
    });
};
// 轉兒科
function sectno_to_04() {
    Swal.fire({
      title: "18歲以下不開放掛號內科。\n12歲以下不開放掛號耳鼻喉科。",
      text: "為您轉到兒科介面。",
      icon: "error"
    }).then((result) => {
        window.location = "/A006_Online_Booking_1_part/?A006_sename=兒科";

        Swal.fire({
            title: "請稍等!",
            // text: "若要請重新登入，謝謝。",
            // icon: "success",
            showConfirmButton: false,
            timer: 3000,
        })
    });
};
// 已有掛號資料轉預約紀錄
function repeat_to_data() {
    Swal.fire({
      title: "您已重複預約。",
      text: "為您轉到預約紀錄。",
      icon: "error"
    }).then((result) => {
        window.location = "/A006_Online_Booking_data/";

        Swal.fire({
            title: "請稍等!",
            // text: "若要請重新登入，謝謝。",
            // icon: "success",
            showConfirmButton: false,
            timer: 3000,
        })
    });
};
// 停機公告
function show_stop_text() {
    Swal.fire({
      title: "網路掛號停機公告",
      html:"您好，為提供更好的網路掛號服務，<br> 本院預計5/4（六）下午3點到4點，<br> 暫停服務一小時，進行系統優化作業，<br>期間內若您有掛號需求，<br> 請撥(04)-36113611 #9 由總機為您服務，<br> 造成您的不便，請見諒，謝謝。",
      // icon: "success"
      confirmButtonText: "我知道了",
    });
};
// 錯誤題是訊息
function error_message(message) {
    Swal.fire({
      title: "錯誤",
      text:message,
    });
};

// ╠════ 慢箋預約區塊 ════╣
// 慢箋-登入
function drug_login() {
    let timerInterval;
    Swal.fire({
        title: "登入中...",
        timer: 7000,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {
       Swal.fire({
        title: "登入失敗！",
        icon: "error",
        text: "請確認「身分證字號」與「出生年月日」是否輸入正確",
    });
        Fancybox.close();
    });   
};

// 慢箋-登入失敗
function login_error(alert) {
    let timerInterval;
    Swal.fire({
        title: "登入失敗！",
        icon: "error",
        // text: "請確認「身分證字號」與「出生年月日」是否輸入正確",
        text: alert,
    });
};

// 慢箋-確定預約
function Drugs_sure_ok(chrocard) {
    const selectedDate = document.querySelector(`input[name^="radio-${chrocard}"]:checked`)?.value;

    let timerInterval;
    Swal.fire({
        title: "預約中...",
        timer: 300,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {
         $.get("/A007_Reserve_pre/reserve?A007_chroarddata="+'預約'+'$'+selectedDate+'$'+chrocard,function(result){
            if ((result === '不可預約') || (result === '請重新登入')){
                // 執行登出
                alert('請重新登入')
                // $.get("/A007_Reserve_pre/logout/",function(result){
                //     // alert(result);
                // });

                window.location = "/A007_Reserve_pre/login/"
            }else{
                Swal.fire({
                    title: "已成功預約！",
                    icon: "success",
                    showConfirmButton: false,
                    timer: 1500,
                }).then(function(){
                    window.location = "/A007_Reserve_pre/data/"
                });

                Fancybox.close();  // 關閉 Fancybox
            }
      });
    }); 
};
// 慢箋-取消預約
// function Drugs_cancel_ok(chrocard,number,original) {
//     let timerInterval;

//     $.get("/A007_Reserve_pre/reserve?A007_chroarddata="+'取消預約'+'$'+chrocard+'$'+number+'$'+original,function(result){
//         // alert(result)
//         if (result === '不可取消'){
//             // 執行登出
//             $.get("/A007_Reserve_pre/logout/",function(result){
//                 // alert(result);
//             });

//             window.location = "/A007_Reserve_pre/login/"
//         }
//       });

//     Swal.fire({
//         title: "取消預約中...",
//         timer: 5000,
//         timerProgressBar: true,
//         allowEscapeKey: false,
//         allowOutsideClick: false,
//         didOpen: () => {
//             Swal.showLoading();
//             const timer = Swal.getPopup().querySelector("b");
//             timerInterval = setInterval(() => {
//                 timer.textContent = `${Swal.getTimerLeft()}`;
//             }, 100);
//         },
//         willClose: () => {
//             clearInterval(timerInterval);
//         }
//     }).then((result) => {
//         Swal.fire({
//             title: "已取消預約！",
//             icon: "success",
//             showConfirmButton: false,
//             timer: 1500,
//         }).then(function(){
//             window.location = "/A007_Reserve_pre/data/"
//         });

//         Fancybox.close();

        
        
//     });    
// };

function Drugs_cancel_ok(chrocard,number,original) {
    let timerInterval;

    // 顯示 "取消預約中..."，但不設定計時器
    Swal.fire({
        title: "取消預約中...",
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
        }
    });

    $.get("/A007_Reserve_pre/reserve?A007_chroarddata="+'取消預約'+'$'+chrocard+'$'+number+'$'+original,function(result){
        // alert(result)
        if ((result === '不可取消') || (result === '請重新登入')){
            // 執行登出
            alert('請重新登入')
            // $.get("/A007_Reserve_pre/logout/",function(result){
            //     // alert(result);
            // });

            window.location = "/A007_Reserve_pre/login/"
        }else{
             Swal.fire({
                title: "已取消預約！",
                icon: "success",
                showConfirmButton: false,
                timer: 1500,
            }).then(function(){
                window.location = "/A007_Reserve_pre/data/"
            });

             Fancybox.close();

        }

      });

};



// 慢箋-登出
const Drugs_logout_ok = () => {
    let timerInterval;
    $.get("/A007_Reserve_pre/logout/",function(result){
        // alert(result);
      });


    Swal.fire({
        title: "登出中...",
        timer: 1000,
        timerProgressBar: true,
        allowEscapeKey: false,
        allowOutsideClick: false,
        didOpen: () => {
            Swal.showLoading();
            const timer = Swal.getPopup().querySelector("b");
            timerInterval = setInterval(() => {
                timer.textContent = `${Swal.getTimerLeft()}`;
            }, 100);
        },
        willClose: () => {
            clearInterval(timerInterval);
        }
    }).then((result) => {                   
        Swal.fire({                     
            title: "已登出成功!",
            // text: "若要請重新登入，謝謝。",
            icon: "success",
            showConfirmButton: false,
            timer: 1000,
        }).then(function(){
            window.location = "/A007_Reserve_pre/login/"
        });
        Fancybox.close();
    });
};



// 慢箋-選擇慢箋預約日期後，判斷是否請求成功 (等待文檔完全加載後再綁定事件)(暫時沒用到)
document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('loadingButton');
    const successBlock = document.getElementById('successBlock');
    const errorBlock = document.getElementById('errorBlock');

    button.addEventListener('click', () => {
        // 啟動 loading 狀態
        button.classList.add('Date_loading');
        
        // 隱藏結果區塊
        successBlock.style.display = 'none';
        
        // 隱藏按鈕文字並顯示 loading 圖標
        button.querySelector('.Date_text').style.display = 'none';
        button.querySelector('.Date_spinner').style.display = 'inline-block';

        // 發送 AJAX 請求（這裡使用 fetch）
        fetch("https://jsonplaceholder.typicode.com/posts/1")  // 假設的 API 請求
        .then(response => {
            if (!response.ok) {  // 如果 HTTP 狀態不是 200，則拋出錯誤
            throw new Error('Network response was not ok');
            }
            return response.json();  // 解析 JSON 響應
        })
        .then(data => {
            // 請求成功後顯示成功區塊 A
            successBlock.style.display = 'block';
            
            // 顯示返回的數據
            console.log(data);

            // 還原按鈕狀態
            button.classList.remove('Date_loading');
            button.querySelector('.Date_spinner').style.display = 'none';
            button.querySelector('.Date_text').style.display = 'inline-block';
        })
        .catch(error => {
            // 請求失敗後顯示錯誤區塊 B
            Swal.fire({
                title: "慢箋預約失敗！",
                text: "請聯繫本院藥局 (電話 04-3611-3600) 進行預約，謝謝。",
                icon: "error"
            });
            Fancybox.close();

            // 顯示錯誤信息
            console.error('Fetch error:', error);

            // 還原按鈕狀態
            button.classList.remove('Date_loading');
            button.querySelector('.Date_spinner').style.display = 'none';
            button.querySelector('.Date_text').style.display = 'inline-block';
        });
    });
});

// 慢箋-選擇慢箋預約日期後，才會啟用「確定預約」按鈕
document.addEventListener('DOMContentLoaded', function () {
    const radios = document.querySelectorAll('.c-radio-table__radio');

    // 更新按鈕狀態
    function updateButtonState() {
        // 創建一個 Map 來存儲每組按鈕的啟用狀態
        const buttonStates = {};

        radios.forEach(radio => {
            const group = radio.id.split('-')[1];

            // 如果該組已經啟用，直接跳過（已經有一個選中）
            if (buttonStates[group]) return;

            // 如果該組的按鈕應該啟用
            if (radio.checked) {
                buttonStates[group] = true;
            }
        });

        // 遍歷按鈕，根據狀態更新
        Object.keys(buttonStates).forEach(group => {
            const button = document.getElementById(`checkButton-${group}`);
            if (button) {
                button.disabled = !buttonStates[group];
            }
        });
    }

    // 為所有單選框綁定事件監聽器
    radios.forEach(radio => {
        radio.addEventListener('change', updateButtonState);
    });

    // 初始時更新按鈕狀態
    updateButtonState();
});