document.addEventListener('DOMContentLoaded', function () {
    // Your JavaScript code goes here
    console.log('Script loaded!');

    function zoomIn(img, event) {
        const container = img.closest('#image-container');
        const rect = img.getBoundingClientRect();
        const offsetX = (event.clientX || event.pageX)- rect.left;
        const offsetY = (event.clientY || event.pageY)- rect.top;

        img.style.transformOrigin = `${(offsetX / img.width) * 100}% ${(offsetY / img.height) * 100}%`;
        img.classList.add('zoomed');
    }

    function zoomOut(img) {
        img.style.transformOrigin = 'center center';
        img.classList.remove('zoomed');
    }
});