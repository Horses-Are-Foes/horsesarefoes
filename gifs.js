(function() {
  var gifs = [
    'DANCETHEHORSESAWAY.gif', 'HERMAN.gif', 'ISHELLREAL.gif', 'MAN-HAPPY.gif',
    'USECOMPUTERFIGHTHORSES.gif', 'BRAINSOFT.gif', 'PROADAMERICAN.gif',
    'AUTISM.gif', 'WASHHANDS.gif', 'PROTECTYOURSELF.gif',
    'FREEONLINEBOOKS.gif', 'HAVEYOUSEENBIGBOY.gif', 'WIZARDFLUTES.gif',
    'YOU-DESERVE-IT-ALL-BBY.gif', 'BECOOL.gif',
    'ROMANCE.gif'
  ];

  // Skip barrage on the DANCETHEHORSESAWAY page itself
  if (window.location.pathname.indexOf('/dance-the-horses-away/') !== -1) {
    return;
  }

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

    // DANCETHEHORSESAWAY links to its dedicated page
    if (name === 'DANCETHEHORSESAWAY.gif') {
      var link = document.createElement('a');
      link.href = '/dance-the-horses-away/';
      link.style.pointerEvents = 'auto';
      link.appendChild(img);
      container.appendChild(link);
    } else {
      container.appendChild(img);
    }
  });

  document.body.appendChild(container);
})();
