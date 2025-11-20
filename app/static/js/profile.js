// === Profile Page JS ===

// Добавляем классы оценки результата
document.querySelectorAll('.result-tag.score').forEach(tag => {
    const value = parseInt(tag.textContent);
    if (value >= 85) {
        tag.classList.add('high');
    } else if (value >= 50) {
        tag.classList.add('medium');
    } else {
        tag.classList.add('low');
    }
});

// Фильтры по тегам
document.querySelectorAll('.section-tags .tag').forEach(tag => {
    tag.addEventListener('click', () => {
        const siblings = tag.parentElement.querySelectorAll('.tag');
        siblings.forEach(s => s.classList.remove('active'));
        tag.classList.add('active');

        const filter = tag.textContent.toLowerCase();
        const section = tag.closest('.section');
        const items = section.querySelectorAll('.course-card, .result-card');

        items.forEach(item => {
            if (filter === 'все') {
                item.style.display = 'block';
            } else if (item.textContent.toLowerCase().includes(filter)) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    });
});
