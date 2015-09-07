/* Div content switcher
*/

function div_switch (name){
    // Check the file extension
    var re = /(?:\.([^.]+))?$/;
    var ext = re.exec(name)[1];
    var dv = document.getElementById('view_div');
    if( ext=="html"){
        var isHTML0 =  document.getElementById('html0');
        if (typeof(isHTML0) != 'undefined' && isHTML0 != null)
        {
            // HTML found, so replace with new
            var oldTHML = document.getElementById("html0");
            var newHTML = document.createElement("object");
            newHTML.data = name;
            newHTML.id = "html0";
            newHTML.width='98%';
            newHTML.height='100%';
            oldTHML.parentNode.replaceChild(newHTML, oldTHML);
        }
        else{
            // HTML not found, so create and add
            var newDiv = document.createElement('div');
            newDiv.style.display = 'inline';
            dv.appendChild(newDiv);
            var newHTML = document.createElement("object");
            newHTML.data = name;
            newHTML.id = "html0";
            newHTML.width='98%';
            newHTML.height='100%';
            dv.appendChild(newHTML);
        }
       
    }
    else{
        // Check for an existing image
        var image =  document.getElementById('img0');
        if (typeof(image) != 'undefined' && image != null)
        {
            // Image found, so replace with new
            image.removeAttribute('width');
            image.style.maxWidth='98%';
            image.src = name;
        }
        else{
            // Image not found, so create and add
            var image = document.createElement("img");
            image.src = name;
            image.id = "img0";
            image.removeAttribute('width');
            image.style.maxWidth='98%';
            dv.appendChild(image);
        }
        var count = 0;
        var width0 = 0;
        image.onclick = function () {
            if( count < 5 ){
                var resize = 1.25; // resize amount in percentage
                var origW  = this.clientWidth; // original image width
                var mouseX = event.x - dv.offsetLeft;
                var mouseY = event.y;
                var divWidth = dv.offsetWidth;
                //Set the new width and height
                this.style.maxWidth='none';
                this.setAttribute('width', origW*resize);
                if( count == 0){
                    width0 = origW;
                }
                count += 1;
                
                // Set the new scroll bars
                view_div.scrollLeft=(mouseX-dv.offsetWidth/2)*count*resize;
                view_div.scrollTop=(mouseY-dv.offsetHeight/2)*count*resize;
            }
            else {
                this.style.maxWidth='98%';
                count = 0;
            }
        }
    }
    view_div.scrollTop=0;
    view_div.scrollLeft=0;
}