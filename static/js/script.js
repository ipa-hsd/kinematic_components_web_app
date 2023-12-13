document.addEventListener('DOMContentLoaded', function () {

    function filterComponents() {
        var input = document.getElementById('searchInput').value.toLowerCase();
        var components = document.querySelectorAll('.ui.segment');

        components.forEach(function (component) {
            var componentName = component.querySelector('.ui.big.header').textContent.toLowerCase();
            if (componentName.includes(input)) {
                component.style.display = 'block';
            } else {
                component.style.display = 'none';
            }
        });
    }
    document.getElementById('searchInput').addEventListener('input', filterComponents);
});

function clearSearch() {
    var input = document.getElementById('searchInput');

    var components = document.querySelectorAll('.ui.segment');
    components.forEach(function (component) {
        component.style.display = 'block';
    });
}

function zoom(e){
    var zoomer = e.currentTarget;
    e.offsetX ? offsetX = e.offsetX : offsetX = e.touches[0].pageX
    e.offsetY ? offsetY = e.offsetY : offsetX = e.touches[0].pageX
    x = offsetX/zoomer.offsetWidth*100
    y = offsetY/zoomer.offsetHeight*100
    zoomer.style.backgroundPosition = x + '% ' + y + '%';
  }