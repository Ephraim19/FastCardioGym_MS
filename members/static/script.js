const collapseBtn = document.querySelector('.collapse-btn');
const sidebar = document.querySelector('.sidebar');

collapseBtn.addEventListener('click', () => {
  sidebar.classList.toggle('collapsed');
});