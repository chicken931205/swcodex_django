$(document).ready(function() {
    $('#dataTable').DataTable({
        "processing": true,
        "serverSide": true,
        "ajax": {
            "url": window.location.href,
            "type": "GET"
        },
        "columns": [
            {% for column in columns %}
                { "data": "{{ column }}" },
            {% endfor %}
        ],
        "dom": '<"dt-buttons"Bf><"clear">lirtp',
        "buttons": [
            'colvis',
            'copyHtml5',
            'csvHtml5',
            'excelHtml5',
            'pdfHtml5',
            'print'
        ]
    });
});