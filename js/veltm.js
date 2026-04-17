/* VELTM shared JS — nav bg toggle + scroll-reveal observer */
(function () {
  'use strict';

  // Nav background toggle on scroll
  var nav = document.querySelector('.nav');
  if (nav) {
    window.addEventListener('scroll', function () {
      nav.classList.toggle('bg', window.scrollY > 32);
    }, { passive: true });
  }

  // Intersection Observer for reveal animations
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        io.unobserve(entry.target); // fire once
      }
    });
  }, { threshold: 0.15 });

  document.querySelectorAll('[data-reveal],[data-reveal-left],[data-reveal-right]').forEach(function (el) {
    io.observe(el);
  });
})();
