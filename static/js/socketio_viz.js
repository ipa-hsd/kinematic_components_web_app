$( window ).on( "load", function() {
    socket = io.connect('http://' + document.domain + ':' + location.port + '/viz');

    socket.emit('component id', {data: window.location.href});

    // this is a callback that triggers when the "viz model" event is emitted by the server
    socket.on('viz model', function (msg) {
        // model, raw_file_url
        viewComponent(msg[0], msg[1], msg[2], msg[3], msg[4], msg[5], msg[6]);
    });
});