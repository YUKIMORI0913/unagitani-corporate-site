document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.card').forEach((card) => {
    const link = card.querySelector('a[href*="unagitanibass.wixsite.com"]');
    if (link) card.remove();
  });
});
