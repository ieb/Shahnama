$(function() {
	$('.image-uploader').click(function() {
		var which = $(this).attr('name');
		$('#upload-dialog').data('which',which);
		$('#upload-dialog').dialog('open');
		// XXX parameterised here
		// Forces reload
		var base = $('#upload-root').attr('href')+which;
		// localise
		$('#upload-dialog iframe').attr('src',base+"/framed");
		$('#upload-dialog form').attr('action',base); // jQuery bug #3113
		return false;
	});
	$('#upload-dialog').dialog({ autoOpen: false, width: 700, height: 500, title: "Upload Image" });
	$('#upload-dialog .new-image').click(function() {
		var $d = $(this).parent('#upload-dialog');
		$('button',$d).css('display','none');
		$('form',$d).css('display','block');
	});
	$('#upload-dialog form').submit(function() {
		var $d = $(this).parent('#upload-dialog');
		$('button',$d).css('display','block');
		$('form',$d).css('display','none');
	});
	$('#upload-dialog .close').click(function() {
		// Save cropping
		var $d = $(this).parent('#upload-dialog');
		var $h = $('iframe',$d).contents().find('html');
		$('iframe',$d).get(0).contentWindow.save();
		$d.dialog('close');
		// Update anything on the screen
		$('img.'+$d.data('which')).each(function(i) {
            var src = $(this).data('real-src');
            if(!src) {
                src = $(this).attr('src');
            }
			$(this).attr('src',src+"?"+Math.random()); // Force reload
		});
	});
});
