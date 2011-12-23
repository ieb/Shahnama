
	  $(function() {

		console.log("hello");
	
	  	
	  	$( "#views" ).buttonset();
	    $( "#orders" ).buttonset();
	  		 
	  	$('#list-select').click(function() {
	  		$(document).scrollTop(0);
	  		$('#grid').css('display','none');
	  		$('#slideshow').css('display','none');
	  		$('#list').css('display','block');
	  		$('#list').trigger('load-visible');
	  	});
	  	
	  	$('#slides-select').click(function() {
	  		$(document).scrollTop(0);
	  		$('#grid').css('display','none');
	  		$('#slideshow').css('display','block');
	  		$('#list').css('display','none');
	  		$('#slideshow').trigger('load-visible');
	  	});

	  	$('#grid-select').click(function() {
	  		$(document).scrollTop(0);
	  		$('#grid').css('display','block');
	  		$('#slideshow').css('display','none');
	  		$('#list').css('display','none');
	  		$('#grid').trigger('load-visible');
	  	});


	  $(window).load(function(){
	  	$('#views input:radio:checked').click();
	  });
	  

	  
});
