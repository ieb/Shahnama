$(function() {
  $('#notes-tab').click(function() {
    $('#notes-slider').show('slide',{ direction: 'right' },100);
  });
  $('#notes-active-tab').click(function() {
    $('#notes-slider').hide('slide',{ direction: 'right' },100);
  });
  $('#notes-closer a').click(function() {
    $('#notes-slider').hide('slide',{ direction: 'right' },100);
  });
});