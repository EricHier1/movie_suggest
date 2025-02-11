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
            fetchCosineHeatmap(title);
            fetchGenreChart(title); // ✅ Now ensuring a valid title is passed
        } else {
            console.error("Movie title is empty! Not calling fetchGenreChart.");
        }
    });
    

    movieInput.addEventListener("keypress", function (event) {
        if (event.key === "Enter") {
            const title = movieInput.value.trim();
            if (title) {
                fetchRecommendations(title);
                fetchCosineHeatmap(title);
                fetchGenreChart(title); // ✅ Ensure a valid title is passed
            } else {
                console.error("Movie title is empty! Not calling fetchGenreChart.");
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
                        fetchCosineHeatmap(this.textContent); //
                        fetchGenreChart(this.textContent);
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

    function fetchGenreChart(title) {
        if (!title || title.trim() === "undefined") {
            console.error("Invalid movie title for genre chart:", title);
            return;
        }
    
        console.log("Fetching genre chart for:", title); // Debugging
    
        fetch(`http://127.0.0.1:5000/genre-distribution?title=${encodeURIComponent(title)}`)    
            .then(response => response.json())
            .then(data => {
                if (data.genre_chart) {
                    genreChartDiv.innerHTML = `
                        <h3>Genre Distribution for '${title}'</h3>
                        <img src="${data.genre_chart}" class="img-fluid" alt="Genre Distribution Chart">
                    `;
                } else if (data.error) {
                    genreChartDiv.innerHTML = `<p>${data.error}</p>`;
                } else {
                    genreChartDiv.innerHTML = `<p>No genre data available for '${title}'.</p>`;
                }
            })
            .catch(error => {
                genreChartDiv.innerHTML = `<p>Error loading genre distribution chart.</p>`;
                console.error("Error fetching genre distribution:", error);
            });
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
                    <div class="card mx-auto mb-3" style="max-width: 600px;">
                        <div class="card-body">
                            <h5 class="card-title"><strong>${movie.title}</strong></h5>
                            <h6 class="card-subtitle mb-2 text-muted">${movie.listed_in || "Genre not available"}</h6>
                            <p class="card-text">${movie.description || "No description available."}</p>
                        </div>
                    </div>
                `)
                .join("");            
    
                fetchCosineHeatmap(title);
                fetchFeatureImportance(title); // ✅ Fetch Feature Importance Chart
            })
            .catch(error => {
                loadingIndicator.style.display = "none";
                errorMessage.textContent = "An error occurred. Please try again.";
            });
    }    

    function fetchFeatureImportance(title) {
        fetch(`http://127.0.0.1:5000/feature-importance?title=${encodeURIComponent(title)}`)
            .then(response => response.json())
            .then(data => {
                if (data.feature_chart) {
                    document.getElementById("featureImportance").innerHTML = `
                        <h3>Key Words for Similarity</h3>
                        <img src="${data.feature_chart}" class="img-fluid" alt="Feature Importance Chart">
                    `;
                } else {
                    document.getElementById("featureImportance").innerHTML = `<p>No feature importance data available.</p>`;
                }
            })
            .catch(error => {
                document.getElementById("featureImportance").innerHTML = `<p>Error loading feature importance chart.</p>`;
                console.error("Error fetching feature importance:", error);
            });
    }    

    // ✅ Fetch genre distribution chart on page load
    fetchGenreChart();
});
