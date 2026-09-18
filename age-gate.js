(function () {
  var gate = document.getElementById('age-gate');
  if (!gate) return;

  var acceptedPermanent = localStorage.getItem('horsesAreFoesAgeAccepted') === 'yes';
  var acceptedSession = sessionStorage.getItem('horsesAreFoesAgeAccepted') === 'yes';

  if (acceptedPermanent || acceptedSession) {
    gate.hidden = true;
    document.body.classList.remove('gate-open');
    return;
  }

  gate.hidden = false;
  document.body.classList.add('gate-open');

  var enter = document.getElementById('age-enter');
  var remember = document.getElementById('remember-age');

  if (enter) {
    enter.addEventListener('click', function () {
      if (remember.checked) {
        localStorage.setItem('horsesAreFoesAgeAccepted', 'yes');
      } else {
        sessionStorage.setItem('horsesAreFoesAgeAccepted', 'yes');
      }
      gate.hidden = true;
      document.body.classList.remove('gate-open');
    });
  }
})();
