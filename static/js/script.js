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