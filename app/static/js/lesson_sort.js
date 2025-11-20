(function() {
    document.addEventListener("DOMContentLoaded", function () {
        const rows = document.querySelectorAll("tr.form-row");
        rows.forEach(row => {
            row.style.cursor = "grab";
        });

        $("#lesson_set-group tbody").sortable({
            update: function () {
                $("#lesson_set-group tbody tr").each(function (index) {
                    $(this).find("input[name$='order']").val(index);
                });
            }
        });
    });
})();
