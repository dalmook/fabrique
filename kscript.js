// 문의 폼 제출 처리
document.getElementById('contact-form').addEventListener('submit', function(e) {
    e.preventDefault();
    alert('문의해 주셔서 감사합니다! 곧 연락드리겠습니다.');
    this.reset();
});

// 간단한 스크롤 애니메이션 (옵션)
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            window.scrollTo({
                top: target.offsetTop - 70, // 헤더 높이 보정
                behavior: 'smooth'
            });
        }
    });
});
