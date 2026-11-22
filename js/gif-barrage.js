(function () {
  "use strict";

  if (document.getElementById("gif-barrage")) return;

  var scriptUrl = document.currentScript ? document.currentScript.src : null;
  var assetsBase = scriptUrl
    ? new URL("../assets/", scriptUrl).href
    : "/assets/";

  var images = [
    "BECOOL.gif",
    "BRAINSOFT.gif",
    "CLICK-FOR-COMET.gif",
    "DANCETHEHORSESAWAY.gif",
    "EASYTOREAD.gif",
    "EVILAWAITS.gif",
    "FREEONLINEBOOKS.gif",
    "GET100OFF.gif",
    "GOUF.gif",
    "GRLNO.gif",
    "HAVEYOUSEENBIGBOY.gif",
    "HERMAN.gif",
    "ISHELLREAL.gif",
    "LearnAboutThis.gif",
    "MAN-HAPPY.gif",
    "pinkfoot.gif",
    "PROADAMERICAN.gif",
    "PROTECTYOURSELF.gif",
    "RAINBOWBABY.gif",
    "ROMANCE.gif",
    "SHADOWPEOPLE.gif",
    "SPACEAPES.gif",
    "TOP100.gif",
    "WASHHANDS.gif",
    "WIZARDEMPORIUM.gif",
    "WIZARDFLUTES.gif",
    "YOU-DESERVE-IT-ALL-BBY.gif",
    "AUTISM.gif",
    "discoveryourself.gif"
  ];

  var barrage = document.createElement("div");
  barrage.id = "gif-barrage";
  barrage.setAttribute("aria-hidden", "true");

  images.forEach(function (name, index) {
    var link = document.createElement("a");
    link.href = index % 7 === 0 ? "/dance-the-horses-away/index.html" : "/";
    link.tabIndex = -1;

    var image = document.createElement("img");
    image.src = assetsBase + name;
    image.alt = "";
    image.loading = "eager";
    link.appendChild(image);

    var side = index % 2 === 0 ? "left" : "right";
    var row = Math.floor(index / 2);
    link.style[side] = side === "left" ? "10px" : "10px";
    link.style.top = (30 + row * 82) + "px";

    barrage.appendChild(link);
  });

  document.body.appendChild(barrage);
})();
