document.addEventListener('DOMContentLoaded', function() {
  function updateGradient() {
    const baseElement = document.querySelector('[data-theme]');
    const bgColor = window.getComputedStyle(baseElement).backgroundColor;
    
    const overlayElement = document.querySelector('.theme-gradient-overlay');
    if (overlayElement) {
      overlayElement.style.background = `linear-gradient(to bottom, rgba(0,0,0,0) 0%, ${bgColor} 100%)`;
    }
    
    document.documentElement.style.setProperty('--theme-background', bgColor);
  }

  // Run on page load
  updateGradient();

  // Watch for theme changes
  const observer = new MutationObserver(() => {
    setTimeout(updateGradient, 100);
  });

  observer.observe(document.documentElement, {
    attributes: true,
    attributeFilter: ['data-theme']
  });

  // Add slide content sync
  if (document.querySelector('.hero-slider')) {
    const swiper = document.querySelector('.swiper').swiper;
    const contents = document.querySelectorAll('.hero-content');
    
    // Show initial content
    contents[0].classList.add('active');
    
    // Update content on slide change
    swiper.on('slideChange', function () {
      contents.forEach(content => content.classList.remove('active'));
      const activeIndex = swiper.realIndex;
      contents[activeIndex]?.classList.add('active');
    });
  }
});
