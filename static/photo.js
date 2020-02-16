var results = $('.results');
var bestGuess = $('#best-guess');
var descriptions = $('#descriptions');
var links = $('#links');
var loaderWrapper = document.getElementById("loader-wrapper");
var fakeSearchButton = document.getElementById("fake-search-button");

function clearBox(elementID) {
    document.getElementById(elementID).innerHTML = "";
}


(function () {

    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();

            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    var video = document.getElementById('video'),
        canvas = document.getElementById('draw-canvas'),
        searchButton = document.getElementById('search-button'),
        context = canvas.getContext('2d'),
        photo = document.getElementById('photo'),
        secondBox = document.getElementById('second-box'),
        vendorUrl = window.URL || window.webkitURL;

    navigator.getMedia = navigator.getUserMedia ||
        navigator.webkitGetUserMedia ||
        navigator.mozGetUserMedia ||
        navigator.msGetUserMedia;

    navigator.getMedia({
        video: {
            width: {
                min: 300,
                max: 1920,
            },
            height: {
                min: 225,
                max: 1080
            },
            facingMode: "user"
        },
        audio: false
    }, function (stream) {
        video.srcObject = stream;
        //video.src = vendorUrl.createObjectURL(stream);
        video.play();
    }, function (error) {
        //error code
    });

    document.getElementById('capture').addEventListener('click', function () {
            fakeSearchButton.style.display = "none";


            var MAX_WIDTH = 300;
            var MAX_HEIGHT = 225;
            var width = video.videoWidth;
            var height = video.videoHeight;

            if (width > height) {
                if (width > MAX_WIDTH) {
                    height *= MAX_WIDTH / width;
                    width = MAX_WIDTH;
                }
                canvas.width = width;
                canvas.height = height;
                context.drawImage(video, 0, 0,  canvas.width, canvas.height);
            } else {
                if (height > MAX_HEIGHT) {
                    width *= MAX_HEIGHT / height;
                    width++;
                    height = MAX_HEIGHT;
                }
                canvas.width = width;
                canvas.height = height;
                context.drawImage(video, 0, 0, canvas.width, canvas.height);
            }

            var imgsrc = canvas.toDataURL('image/png');

            photo.setAttribute("width", canvas.width);
            photo.setAttribute("height", canvas.height);
            photo.setAttribute('src', imgsrc);
            $.ajax({
                type: "POST",
                url: "/save",
                data: imgsrc

            }).done(function () {
                console.log('sent');
            });


            photo.style.display = "block";

            searchButton.style.display = "block";
        },
    );

    document.getElementById('search-button').addEventListener('click', function () {

        loaderWrapper.style.display = "block";
        $.ajax({
            type: "GET",
            url: "https://192.168.0.101:5000/search_image",
            dataType: "json",
            success: function (data) {
                clearBox('best-guess');
                clearBox('descriptions');
                clearBox('links');
                $.each(data, function (key, value) {
                    if (key == "best_guess") {
                        key = "Best Guess";

                        var result = "<p><b>" + key + ":</b> " + value + "<hr></p>"
                        bestGuess.append(result);

                    } else if (key == "descriptions") {
                        key = "Descriptions";

                        value = "<ol>" + "<li>" + value[0] + "</li>" + "<li>" + value[1] + "</li>" + "</ol>";
                        var result = "<p class='text-center'><b>" + key + "</b></p>" + value;
                        descriptions.append(result);

                    } else if (key == "links") {
                        key = "Links";

                        value = "<ol>" + "<li>" + "<a href=\"" + value[0] + "\">" + value[0] + "</a>" + "</li>"
                            + "<li>" + "<a href=\"" + value[1] + "\">" + value[1] + "</a>" + "</li>" + "</ol>"
                        var result = "<p class='text-center'><b>" + key + ":</b></p>" + value;
                        links.append(result);
                    }

                });

            }

        }).done(function () {
            loaderWrapper.style.display = "none"
        });


    });


})();

function printOut() {
    console.log(JSON.stringify(info))
    $('body').append(info);
}
