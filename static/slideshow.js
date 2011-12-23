$(function() {
  $('#slideshow').bind('load-visible',function(){ layout() });

	/* XXX move, not just slideshow */
  	var spare=84-$('#frame-main-top').outerHeight();
	if(spare>0) {
		$('#slideshow').css('top',180-spare);
		$('#list').css('top',180-spare);
	}
	
	/* XXX not slideshow */
	$('#main-ill img').each(function() {
  	  var h = jQuery(window).height();
  	  $(this).css('max-height',h-150);
	});
	
});

function layout() {
	if(!$('#photos').hasClass('unloaded'))
		return;
	$('#photos').removeClass('unloaded');
	// populate the gallery
	
	/* Shift up if there's only one button row */
	
	var w = jQuery(window).width();
	var h = jQuery(window).height();
			
	var a = 1.6; /* Aspect ratio. */
			
	h = h - 140; /* Pixels in header. */
	h = h - $('#frame-main-top').outerHeight(true);

	w = w / 2;

	var hew = h / a; /* height-equivalent width */
			
	if(w>hew) w=hew;
	h = w * a;


  function centre($what) {
    if($what.hasClass('resized'))
    	return;
    if(!$what.width() || !$what.height()) {
    	$(this).oneTime('0.2s',function() { centre($what); });
    	return;
    }
	var img_w=$what.width();
	var img_h=$what.height();
    $what.parents('.panel-content-image').css('margin-top',(h-img_h)/2);
	$what.parents('.panel-content-image').css('margin-left',(w-img_w)/2);
	$what.addClass('resized');
  }

  function resize(what) {
    if(what.hasClass('resized'))
    	return;
    if(!what.width() || !what.height()) {
    	$(this).oneTime('0.2s',function() { resize(what); });
    	return;
    }
		var img_w=what.width();
		var img_h=what.height();
		var img_ws=img_w/w;
		var img_hs=img_h/h;
		var img_s=img_hs;
		if(img_ws>img_hs)
		  img_s=img_ws;
		what.attr('width',img_w/img_s);
		what.attr('height',img_h/img_s);
		what.parents('.panel-content-image').css('margin-top',(h-img_h/img_s)/2);
		what.parents('.panel-content-image').css('margin-left',(w-img_w/img_s)/2);
		what.addClass('resized');
	}
	
	window_loaded=true;
	jQuery('#photos').galleryView({
		panel_width: w,
		panel_height: h,
		frame_width: 60,
		frame_height: 80,
		filmstrip_position: 'right',
		overlay_position: 'bottom',
		nav_theme: 'light',
		panel_scale: 'crop',
		frame_scale: 'crop',
		pause_on_hover: true,
		transition_interval: '0'
	});
	
	/* We only load big images on demand to avoid breaking the server.
	 * First, we don't start until the page is fully loaded. Then we
	 * look every two seconds at the current image and load that if not
	 * loaded. It would be nice to have an event to avoid the timer.
	 */
	
	function load_image(what) {
		var $p=what.parent();
		var href=what.attr('href');
		what.remove();
		$('a.panel-insert',$p).append('<img src="'+href+'" style="display: none"/>');
		$img=$p.find('img');
		if(what.hasClass('no-resize'))
		  centre($img);
		else
		  resize($img);
		$img.css('display','block');
	}
	
		$('#photos .panel-content').bind('visible',function() {
		    $pi=$('a.panel-image',this);
		    if($pi.length)
			  load_image($pi);
			$pm=$('.panel-message',this);
			if($pm.length)
			  centre($pm);
		});
	
	$('#photos .panel-thumb').each(function() {
	    if($(this).hasClass('resized'))
    	  return;
		var h=$(this).height();
		var ph=$(this).parent().height();
		$(this).css('margin-top',(ph-h)/2);
		$(this).addClass('resized');
	});
}
