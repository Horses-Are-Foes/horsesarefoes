(function() {
  var gifs = [
    'YOU-DESERVE-IT-ALL-BBY.gif', 'HERMAN.gif', 'ISHELLREAL.gif', 'MAN-HAPPY.gif',
    'USECOMPUTERFIGHTHORSES.gif', 'BECOOL.gif', 'PROADAMERICAN.gif',
    'AUTISM.gif', 'WASHHANDS.gif', 'PROTECTYOURSELF.gif',
    'FREEONLINEBOOKS.gif', 'HAVEYOUSEENBIGBOY.gif', 'WIZARDFLUTES.gif',
    'DANCETHEHORSESAWAY.gif', 'BRAINSOFT.gif',
    'ROMANCE.gif'
  ];

  var container = document.createElement('div');
  container.className = 'gif-barrage';

  var path = window.location.pathname;
  var isSubpage = path.indexOf('/reports/') !== -1 || path.indexOf('/mission/') !== -1 || path.indexOf('/contact/') !== -1 || path.indexOf('/wiki/') !== -1;
  var prefix = isSubpage ? '../assets/' : '/assets/';

  gifs.forEach(function(name) {
    var img = document.createElement('img');
    img.src = prefix + name;
    img.className = 'gif-item';
    img.alt = '';
    container.appendChild(img);
  });

  document.body.appendChild(container);
})();
