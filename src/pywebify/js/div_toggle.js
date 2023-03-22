/*******************************************************************************/
/* Div size toggler                                                            */
/*   Designed for the PyWebify project                                         */
/*   https://github.com/endangeredoxen/pywebify                                */
/*******************************************************************************/

function div_toggle() {
    var origWidth = $('#sidebar').width();
    var status = 0;
    $('#toggle').html('<<');
    $('#toggle').on('click', function() {
        if (status == 0) {
            $('#sidebar').css({'overflow': 'hidden'});
            $('#sidebar li').css({'visibility': 'hidden'});
            $('#sidebar').animate({width:0});
            $('#viewer').animate({left:0});
            $('#toggle').html('>>');
            status = 1;
        } else {
            $('#sidebar').css({'overflow': 'auto'});
            $('#sidebar li').css({'visibility': 'visible'});
            $('#sidebar').animate({width:origWidth});
            $('#toggle').html('<<');
            status = 0;
        }
    }
    );
};

$(document).ready( function() {
    div_toggle()
});
