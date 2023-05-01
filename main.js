function populateYearSelection() {
    var inputs = document.getElementsByTagName('input');
    for (let i = 0; i < inputs.length; i++) {
        inputs[i].addEventListener('keypress', event => {
            if (event.key === 'Enter') {
                sendRequest();
            }
        });
    }
}

function sendRequest() {
    const searchField = document.getElementById('searchField');
    const minScore = document.getElementById('minScore');
    const maxScore = document.getElementById('maxScore');
    const minYear = document.getElementById('minYear');
    const maxYear = document.getElementById('maxYear');

    const results = document.getElementById('results');

    var url = `/search?query=${searchField.value}`
    url += `&minYear=${minYear.value}`;
    url += `&maxYear=${maxYear.value}`;
    url += `&minScore=${minScore.value}`;
    url += `&maxScore=${maxScore.value}`;

    results.innerHTML = "<p>Loading...</p>";

    fetch(url)
        .then(response => response.json())
        .then(data => {
            results.innerHTML = '';
            for (let i = 0; i < data.length; i++) {
                const container = document.createElement('div');
                container.style.width = "100%";
                container.style.display = "inline-block";
                container.style.padding = "10px";

                const img = new Image();
                const imgData = "data:image/jpeg;base64," + data[i].img_data;
                img.src = imgData;
                img.style.maxWidth = "100%";
                img.style.maxHeight = "200px";

                var img_container = document.createElement('div');
                img_container.style.width = "200px";
                img_container.style.float = "left";
                img_container.style.padding = "5px";

                img_container.appendChild(img);
                container.appendChild(img_container);

                var keys = ["title", "year", "score", "genres", "abstract"];
                var table = document.createElement('table');
                for (let j = 0; j < keys.length; j++) {
                    var row = document.createElement('tr');
                    var key = document.createElement('td');
                    key.innerText = keys[j];
                    var value = document.createElement('td');
                    value.innerText = data[i][keys[j]];
                    value.style.width = "100%";
                    row.appendChild(key);
                    row.appendChild(value);
                    table.appendChild(row);
                }
                // make the trailer row
                var trailer_row = document.createElement('tr');
                var trailer_key = document.createElement('td');
                trailer_key.innerText = "trailer";
                var trailer = document.createElement('td');
                var link = document.createElement('a');
                link_text = encodeURI("https://www.youtube.com/results?search_query=" + data[i].title + " " + data[i].year + " trailer");
                link.innerText = `Trailer Youtube`;
                link.href = link_text;
                link.target = "_blank";
                trailer.appendChild(link);
                trailer_row.appendChild(trailer_key);
                trailer_row.appendChild(trailer);
                table.appendChild(trailer_row);

                table.style.width = "calc(100% - 200px - 20px)";
                table.style.padding = "5px";
                container.appendChild(table);
                results.appendChild(container);

                fetch(`/image?title=${data[i].title}&year=${data[i].year}`)
                    .then(response => response.json())
                    .then(new_img_data => {
                        const imgData = "data:image/jpeg;base64," + new_img_data.img_data;
                        img.src = imgData;
                    });
            }
            if (data.length == 0) {
                results.innerHTML = "<p>No results found.</p>";
            }
        })
        .catch(error => {
            results.innerHTML = `<p>Error: ${error.message}</p>`;
        });
}

window.onload = populateYearSelection;
