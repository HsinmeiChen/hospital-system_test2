class AgentLinkHeaderMiddleware:
    """
    這個 Middleware 的作用是在每一個網頁的 HTTP 回應標頭 (Response Header) 中，
    偷偷塞入一個給 AI 爬蟲看的隱藏指路牌 (Link Header)。
    符合 RFC 8288 規範，這能大幅提升網站的 Agent Readiness 分數。
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # 只針對 HTML 網頁或是首頁發送，避免干擾圖片或靜態檔案的快取
        # 但為了簡單起見，直接加在標頭也無妨（因為它只是個提示）
        # 這裡我們將它指向我們剛才寫好的 /llms.txt
        response['Link'] = '</llms.txt>; rel="service-doc"'
        
        return response
