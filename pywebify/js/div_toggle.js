function div_toggle() {
    var origWidth = $('#sidebar').width();
    $('#toggle').toggle(function(){
    $('#sidebar').css({'overflow': 'hidden'});
    $('#sidebar li').css({'visibility': 'hidden'});
    $('#sidebar').animate({width:0});
    $('#viewer').animate({left:0});
    $('#toggle').html('>>');
    },function(){
    $('#sidebar').css({'overflow': 'auto'});
    $('#sidebar li').css({'visibility': 'visible'});
    $('#sidebar').animate({width:origWidth});
    $('#toggle').html('<<');
    });
};

$(document).ready( function() {
    div_toggle()
});