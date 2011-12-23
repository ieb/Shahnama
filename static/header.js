function limpetise(hover_sel,limpet_sel) {
	$(hover_sel).hover(function() {
		var $blob=$(limpet_sel);
		if($blob.css('display')=='none') {
			$blob.show('blind',{},200);
		}
	});
}

$(function() {
	limpetise('#nav-wb','#wb-blob');
		    
	$('.limpet-closer').click(function() {
		$(this).parents('.limpet').hide('blind',{},200);
	});
	
	$('#frame-title').click(function() {
	   window.location.href = $('#title-link').attr('href');
	});
});

// XXX general purpose, not really header. Should go somewhere better.
// XXX should be AJAX and not rely on erroneous returns.
    
$(function() {
    $('.optional-image').error(function() {
        $(this).data('real-src',$(this).attr('src'));
        $(this).attr('src',$('#transparent').attr('src'));
        return true;    
    });
});
