document.getElementById('pdfLink').addEventListener('click', function(e) {
    openInFullScreenWin(e.target.href);
    e.preventDefault();
});