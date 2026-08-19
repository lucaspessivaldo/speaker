/* Navbar unica das 3 paginas. Editar as abas SO aqui. */
(function () {
  var PAGES = [
    { label: 'Lista',   href: 'index.html' },
    { label: 'Fila',    href: 'practice.html' },
    { label: 'Revisão', href: 'review.html' }
  ];

  var host = document.getElementById('site-header');
  if (!host) return;

  var file = location.pathname.split('/').pop().toLowerCase();
  if (!file) file = 'index.html';

  var tabs = PAGES.map(function (p) {
    return p.href === file
      ? '<span class="current">' + p.label + '</span>'
      : '<a href="' + p.href + '">' + p.label + '</a>';
  }).join('');

  host.innerHTML =
    '<div class="head-inner">' +
      '<div class="brand">\u{1F3A7} 1000 English <em>Sentences</em></div>' +
      '<nav class="site-nav">' + tabs + '</nav>' +
    '</div>';
})();
