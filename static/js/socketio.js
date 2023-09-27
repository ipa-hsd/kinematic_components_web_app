// Client Side Javascript to receive numbers.
$(document).ready(function () {
    // start up the SocketIO connection to the server - the namespace 'test' is also included here if necessary
    var socket = io.connect('http://' + document.domain + ':' + location.port + '/test');

    // this is a callback that triggers when the "add component" event is emitted by the server.
    socket.on('add component', function (msg) {
        $('#component_add').append(
            '<div class="ui segment">' +
            '<p class="ui big header"> ' + msg.name + ' | ' + msg.package + ' | ' + msg.category + '</p>' +
            '<a class="ui green button" href="/components/' + msg.category + '/' + msg.id + '">Details</a>' +
            '<a class="ui red button" href="/delete/' + msg.id + '">Delete</a>' +
            '</div>');
    });
});