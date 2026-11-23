// Year and category archives: keep one group open at a time, and open the
// group named in the URL hash (posts link to /archives/categories.html#slug).
(function () {
    var groups = document.querySelectorAll('.category-group, .archive-year-group');

    function openFromHash() {
        var id = decodeURIComponent(window.location.hash.slice(1));
        var target = id && document.getElementById(id);
        if (target && target.tagName === 'DETAILS') {
            target.open = true;
            target.scrollIntoView({ block: 'start' });
        }
    }

    for (var i = 0; i < groups.length; i += 1) {
        groups[i].addEventListener('toggle', function () {
            if (!this.open) {
                return;
            }
            for (var j = 0; j < groups.length; j += 1) {
                if (groups[j] !== this && groups[j].open) {
                    groups[j].removeAttribute('open');
                }
            }
        });
    }

    window.addEventListener('hashchange', openFromHash);
    openFromHash();
}());
