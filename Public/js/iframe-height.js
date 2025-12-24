function iframeLoad() {						
    var iframe = document.getElementById("myiframe");						
    var iframeWin = iframe.contentWindow || iframe.contentDocument.parentWindow;						
        if(iframe) {						
            iframe.height = iframeWin.document.body.scroll;
            if(iframeWin.document.body)						
            iframe.height = iframeWin.document.documentElement.scrollHeight;						
        }						
    }						
    //window.setInterval("iframeLoad()", 20);