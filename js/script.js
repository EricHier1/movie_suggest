document.addEventListener("DOMContentLoaded", function () {
    const movieInput = document.getElementById("movieTitle");
    const getBtn = document.getElementById("getRecommendations");
    const results = document.getElementById("results");
    const loadingIndicator = document.getElementById("loading");
    const errorMessage = document.getElementById("errorMessage");
    const autocompleteBox = document.getElementById("autocompleteBox");
    const heatmapDiv = document.getElementById("heatmap");
    const genreChartDiv = document.getElementById("genreChart");

    getBtn.addEventListener("click", () => {
        const title = movieInput.value.trim();
        if (title) {
            fetchRecommendations(title);
            fetchCosineHeatmap(title); // ✅ Now calling heatmap function
        }
    });

    movieInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            const title = movieInput.value.trim();
            if (title) {
                fetchRecommendations(title);
                fetchCosineHeatmap(title); // ✅ Now calling heatmap function
            }
        }
    });

    // Fetch autocomplete suggestions
    movieInput.addEventListener("input", function () {
        const query = movieInput.value.trim();
        if (query.length < 2) {
            autocompleteBox.style.display = "none";
            return;
        }

        fetch(`http://127.0.0.1:5000/autocomplete?query=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(suggestions => {
                if (suggestions.length === 0) {
                    autocompleteBox.style.display = "none";
                    return;
                }

                autocompleteBox.innerHTML = suggestions
                    .map(title => `<div class="autocomplete-item">${title}</div>`)
                    .join("");
                autocompleteBox.style.display = "block";

                // Handle click on suggestion
                document.querySelectorAll(".autocomplete-item").forEach(item => {
                    item.addEventListener("click", function () {
                        movieInput.value = this.textContent;
                        autocompleteBox.style.display = "none";
                        fetchRecommendations(this.textContent);
                        fetchCosineHeatmap(this.textContent); // ✅ Also fetch heatmap on autocomplete selection
                    });
                });
            })
            .catch(() => autocompleteBox.style.display = "none");
    });

    // Hide autocomplete when clicking outside
    document.addEventListener("click", function (event) {
        if (!autocompleteBox.contains(event.target) && event.target !== movieInput) {
            autocompleteBox.style.display = "none";
        }
    });

    function fetchGenreChart() {
        fetch("http://127.0.0.1:5000/genre-distribution")
            .then(response => response.json())
            .then(data => {
                if (data.genre_chart) {
                    genreChartDiv.innerHTML = `
                        <h3>Top Movie Genres</h3>
                        <img src="${data.genre_chart}" class="img-fluid" alt="Genre Distribution Chart">
                    `;
                }
            })
            .catch(error => console.error("Error fetching genre distribution:", error));
    }
    
    function fetchCosineHeatmap(title) {
        fetch(`http://127.0.0.1:5000/cosine-heatmap?title=${encodeURIComponent(title)}`)
            .then(response => response.json())
            .then(data => {
                if (data.heatmap) {
                    heatmapDiv.innerHTML = `
                        <h3>Similarity Heatmap</h3>
                        <img src="${data.heatmap}" class="img-fluid" alt="Cosine Similarity Heatmap">
                    `;
                } else {
                    heatmapDiv.innerHTML = `<p>No heatmap available.</p>`;
                }
            })
            .catch(error => {
                heatmapDiv.innerHTML = `<p>Error loading heatmap.</p>`;
                console.error("Error fetching heatmap:", error);
            });
    }

    function fetchRecommendations(title) {
        if (!title.trim()) {
            errorMessage.textContent = "Please enter a movie title.";
            return;
        }

        errorMessage.textContent = "";
        results.innerHTML = "";
        loadingIndicator.style.display = "block";
        autocompleteBox.style.display = "none";

        fetch(`http://127.0.0.1:5000/recommend?title=${encodeURIComponent(title)}`)
            .then(response => response.json())
            .then(data => {
                loadingIndicator.style.display = "none";

                if (!data.recommendations || data.recommendations.length === 0) {
                    errorMessage.textContent = "No recommendations found.";
                    return;
                }

                results.innerHTML = data.recommendations
                    .map(movie => `
                        <div class="movie-card">
                            <div class="movie-title"><strong>${movie.title}</strong></div>
                            <div class="movie-genre"><em>${movie.listed_in || "Genre not available"}</em></div>
                            <div class="movie-description">${movie.description || "No description available."}</div>
                        </div>
                    `)
                    .join("");
            })
            .catch(error => {
                loadingIndicator.style.display = "none";
                errorMessage.textContent = "An error occurred. Please try again.";
            });
    }

    // ✅ Fetch genre distribution chart on page load
    fetchGenreChart();
});
