/* Modified to add option to display tooltip on left -- dan */

/* aqTip v1.1 - Pop up a box next to the object the mouse is currently pointing to.
   Copyright (C) 2008 Paul Pham <http://jquery.aquaron.com/aqTip>

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
*/
(function($){
$.fn.aqTip = function(html,options) {
   var opts = $.extend({}, $.fn.aqTip.defaults, options);

   return this.each(function() {
      var $obj = $(this);
      //alert($obj.);

      $('<div class="aqTip"><\/div>').appendTo($obj);

      var $layer = $('.aqTip',$obj);

      $layer.css({ display: 'none', position: 'absolute' }).css(opts.css);

      if (jQuery.isFunction(html)) html($layer);
      else $layer.html(html);

      var p = $obj.position();
      var ow = $obj.width() > $layer.width() 
         ? $obj.width() : $layer.width();
      var x = p.left + opts.relativeX * ow + opts.marginX;
      if (x > document.body.clientWidth)
         x = p.left - opts.relativeY * ow - opts.marginX;

      $layer.css({ left: x+'px', top: p.top+opts.marginY+'px' });
      $obj.hover(function(){$layer.show()}, function(){$layer.hide()});
   });
};

$.fn.aqTipOne = function(html,options) {
   var opts = $.extend({}, $.fn.aqTip.defaults, options);
   return this.each(function() {
      if (!$('#aqTip').length) {
         $('<div id="aqTip"><\/div>').appendTo(document.body);
         $('#aqTip').css({ display: 'none', position: 'absolute' })
            .css(opts.css);
      }

      var $obj = $(this);
      if (html) {
         $('#aqTip').html(html);

         var p = $obj.position();
         var ow = $obj.width() > $('#aqTip').width() 
            ? $obj.width():$('#aqTip').width();
         var x = p.left + ow + opts.marginX;
         if (x > document.body.clientWidth)
            x = p.left - ow - opts.marginX;

         $('#aqTip').show()
            .css({ left: x+'px', top: p.top+opts.marginY+'px' })
      } else
         $('#aqTip:visible').hide()

      return false;
   });
};

$.fn.aqTip.defaults = { 
   marginX: 10, marginY: 10,
   relativeX: 1.0, relativeY: 1.0,
   css: { 
      backgroundColor: '#fff', color: '#444',
      border: '1px solid #ddd', padding: '5px' }
};
})(jQuery);