$(function() {
	$('#list').bind('load-visible',function() {
		$('.list-unprimed').each(function() {
			/* Default position for small screens */
			var x=-40;
			var y=30;
			/* Is there room for tooltips on the left? */
			if($(this).offset().left > 10) {
				x=-100;
				y=0;
			}
			/* Create tooltips */
			$('.list-image').each(function() {
				$(this).parents('li').find('.list-data').
					aqTip('<img src="'+$(this).attr('href')+'" height="120"/>',
						  { relativeX: 0, relativeY: 0, marginX: x, marginY: y});

			});
			$(this).removeClass('list-unprimed');
		});
	});
});
