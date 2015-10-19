/* Div content switcher
*/

function div_switch (name){
    // Check the file extension
    var re = /(?:\.([^.]+))?$/;
    var ext = re.exec(name)[1];
    var dv = document.getElementById('viewer');
    if( ext=="html"){
        // Check for an existing image and remove if found
        var image = document.getElementById('img0');
        if (typeof(image) != 'undefined' && image != null)
        {
            image.parentNode.removeChild(image);
        }
        
        var isHTML0 =  document.getElementById('html0');
        if (typeof(isHTML0) != 'undefined' && isHTML0 != null)
        {
            // HTML found, so replace with new
            var oldTHML = document.getElementById("html0");
            var newHTML = document.createElement("object");
            newHTML.data = name;
            newHTML.id = "html0";
            newHTML.width='100%';
            newHTML.height='100%';
            oldTHML.parentNode.replaceChild(newHTML, oldTHML);
        }
        else{
            // HTML not found, so create and add
            var summary = document.getElementById('summary');
            var newHTML = document.createElement("object");
            newHTML.data = name;
            newHTML.id = "html0";
            newHTML.width='100%';
            newHTML.height='100%';
            dv.insertBefore(newHTML, summary);
           
        }
       
    }
    else{
        // Check for an existing html remove if found
        var html = document.getElementById('html0');
        if (typeof(html) != 'undefined' && html != null)
        {
            html.parentNode.removeChild(html);
        }
        
        // Check for an existing image
        var image =  document.getElementById('img0');
        if (typeof(image) != 'undefined' && image != null)
        {
            // Image found, so replace with new
            image.removeAttribute('width');
            image.style.maxWidth='100%';
            // Center images
            // image.style.display = 'block';
            // image.style.marginLeft = 'auto';
            // image.style.marginRight = 'auto';
            image.src = name;
        }
        else{
            // Image not found, so create and add
            var image = document.createElement("img");
            var summary = document.getElementById('summary');
            image.src = name;
            image.id = "img0";
            image.removeAttribute('width');
            image.style.maxWidth='100%';
            // Center images
            // image.style.display = 'block';
            // image.style.marginLeft = 'auto';
            // image.style.marginRight = 'auto';
            dv.insertBefore(image, summary);
        }
        var width0 = 0;
        var zoom = 'in';
        var startWidth = image.width;
        
        image.onclick = function () {
            if (event.shiftKey) {
                var resize = 0.75; // resize amount in percentage
                if (zoom=='in') {
                    zoom = 'out';
                }
                else
                    zoom = 'in';
            } else {
                var resize = 1.25; // resize amount in percentage
                if (zoom=='out') {
                    zoom = 'in';
                }
                else
                    zoom = 'in';
            }
            if (event.ctrlKey) {
                viewer.scrollLeft=0;
                viewer.scrollTop=0;
                this.removeAttribute('width');
                this.style.maxWidth='800%';
            }
            else {
                
                //Set the new width and height
                var origW  = this.clientWidth; // original image width
                this.style.maxWidth='none';
                this.setAttribute('width', origW*resize);
                
                // Set the scroll bars
                var bbox = this.getBoundingClientRect();
                var mouseX = event.x - bbox.left;
                var mouseY = event.y - bbox.top;
                var imgWidth = bbox.right-bbox.left;
                var imgHeight = bbox.bottom-bbox.top;
                var xOffset = mouseX*resize - imgWidth/2;
                var yOffset = mouseY*resize - imgHeight/2;
                var scrollWidthMax = this.scrollWidth - dv.offsetWidth;
                var scrollHeightMax = this.scrollHeight - dv.offsetHeight;
                var ratioWidth = scrollWidthMax/imgWidth;
                
                viewer.scrollLeft = scrollWidthMax/2 + xOffset;
                viewer.scrollTop = scrollHeightMax/2 + yOffset;
            }
        }
    }
    viewer.scrollTop=0;
    viewer.scrollLeft=0;
}