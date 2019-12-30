// A couple of different backgrounds
var background1 = 'black';
var background2 = 'firebrick';

// Toggle the background state
var color = true;

// every 1 second, switch the background color, alternating between the two styles
setInterval(function () {
  document.body.style.backgroundColor = (color ? background1 : background2)
  color = !color;
}, 10000);