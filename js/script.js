document.addEventListener("DOMContentLoaded", function () {
    const movieInput = document.getElementById("movieTitle");
    const getBtn = document.getElementById("getRecommendations");
    const results = document.getElementById("results");
    const loadingIndicator = document.getElementById("loading");
    const errorMessage = document.getElementById("errorMessage");
    const autocompleteBox = document.getElementById("autocompleteBox");
    const heatmapDiv = document.getElementById("heatmap");
    const genreChartDiv = document.getElementById("genreChart");
    const featureImportanceDiv = document.getElementById("featureImportance");

    // Get slider elements
    const genreSlider = document.getElementById("genreWeight");
    const descSlider = document.getElementById("descWeight");
    const directorSlider = document.getElementById("directorWeight");
    const castSlider = document.getElementById("castWeight");

    getBtn.addEventListener("click", () => handleMovieSearch());
    movieInput.addEventListener("keypress", (event) => {
        if (event.key === "Enter") handleMovieSearch();
    });

    function handleMovieSearch() {
        const title = movieInput.value.trim();
        if (!title) {
            console.error("Movie title is empty! Not fetching data.");
            return;
        }

        fetchRecommendations(title);
        fetchCosineHeatmap(title);
        fetchGenreChart(title);
        fetchFeatureImportance(title);
    }

    // ✅ Fetch autocomplete suggestions
    movieInput.addEventListener("input", async function () {
        const query = movieInput.value.trim();
        if (query.length < 2) {
            autocompleteBox.style.display = "none";
            return;
        }

        try {
            const response = await fetch(`http://127.0.0.1:5000/autocomplete?query=${encodeURIComponent(query)}`);
            const suggestions = await response.json();

            if (!suggestions.length) {
                autocompleteBox.style.display = "none";
                return;
            }

            autocompleteBox.innerHTML = suggestions
                .map(title => `<div class="autocomplete-item">${title}</div>`)
                .join("");
            autocompleteBox.style.display = "block";

            document.querySelectorAll(".autocomplete-item").forEach(item => {
                item.addEventListener("click", function () {
                    movieInput.value = this.textContent;
                    autocompleteBox.style.display = "none";
                    handleMovieSearch();
                });
            });
        } catch (error) {
            console.error("Error fetching autocomplete suggestions:", error);
            autocompleteBox.style.display = "none";
        }
    });

    // ✅ Hide autocomplete when clicking outside
    document.addEventListener("click", (event) => {
        if (!autocompleteBox.contains(event.target) && event.target !== movieInput) {
            autocompleteBox.style.display = "none";
        }
    });

    async function fetchGenreChart(title) {
        if (!title) return;
        console.log("Fetching genre chart for:", title);
    
        try {
            const response = await fetch(`http://127.0.0.1:5000/genre-distribution?title=${encodeURIComponent(title)}`);
    
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
    
            const data = await response.json();
            genreChartDiv.innerHTML = data.genre_chart
                ? `<h3>Genre Distribution for '${title}'</h3><img src="${data.genre_chart}" class="img-fluid" alt="Genre Distribution Chart">`
                : `<p>${data.error || "No genre data available."}</p>`;
        } catch (error) {
            console.error("Error fetching genre distribution:", error);
            genreChartDiv.innerHTML = `<p>Error loading genre distribution chart.</p>`;
        }
    }
    

    // ✅ Fetch Cosine Similarity Heatmap
    async function fetchCosineHeatmap(title) {
        if (!title) return;
        console.log("Fetching heatmap for:", title);

        try {
            const response = await fetch(`http://127.0.0.1:5000/cosine-heatmap?title=${encodeURIComponent(title)}`);
            const data = await response.json();

            heatmapDiv.innerHTML = data.heatmap
                ? `<h3>Similarity Heatmap</h3><img src="${data.heatmap}" class="img-fluid" alt="Cosine Similarity Heatmap">`
                : `<p>${data.error || "No heatmap available."}</p>`;
        } catch (error) {
            console.error("Error fetching heatmap:", error);
            heatmapDiv.innerHTML = `<p>Error loading heatmap.</p>`;
        }
    }

    // ✅ Fetch Movie Recommendations (with similarity percentages)
    async function fetchRecommendations(title) {
        if (!title) return;
        console.log("Fetching recommendations for:", title);

        errorMessage.textContent = "";
        results.innerHTML = "";
        loadingIndicator.style.display = "block";
        autocompleteBox.style.display = "none";

        // ✅ Get slider values
        const genreWeight = genreSlider.value;
        const descWeight = descSlider.value;
        const directorWeight = directorSlider.value;
        const castWeight = castSlider.value;

        try {
            const response = await fetch(`http://127.0.0.1:5000/recommend?title=${encodeURIComponent(title)}&genreWeight=${genreWeight}&descWeight=${descWeight}&directorWeight=${directorWeight}&castWeight=${castWeight}`);
            const data = await response.json();
            loadingIndicator.style.display = "none";

            if (!data.recommendations || data.recommendations.length === 0) {
                errorMessage.textContent = "No recommendations found.";
                return;
            }

            results.innerHTML = data.recommendations.map(movie => `
                <div class="card mx-auto mb-3" style="max-width: 600px;">
                    <div class="card-body">
                        <h5 class="card-title"><strong>${movie.title}</strong> 
                            <span class="badge bg-success">${movie.similarity}% Similar</span> 
                        </h5>
                        <h6 class="card-subtitle mb-2 text-muted">${movie.listed_in || "Genre not available"}</h6>
                        <p class="card-text">${movie.description || "No description available."}</p>
                    </div>
                </div>
            `).join("");

            fetchCosineHeatmap(title);
            fetchFeatureImportance(title);
        } catch (error) {
            console.error("Error fetching recommendations:", error);
            loadingIndicator.style.display = "none";
            errorMessage.textContent = "An error occurred. Please try again.";
        }
    }

    // ✅ Fetch Feature Importance Chart
    async function fetchFeatureImportance(title) {
        if (!title) return;
        console.log("Fetching feature importance for:", title);

        try {
            const response = await fetch(`http://127.0.0.1:5000/feature-importance?title=${encodeURIComponent(title)}`);
            const data = await response.json();

            featureImportanceDiv.innerHTML = data.feature_chart
                ? `<h3>Key Words for Similarity</h3><img src="${data.feature_chart}" class="img-fluid" alt="Feature Importance Chart">`
                : `<p>${data.error || "No feature importance data available."}</p>`;
        } catch (error) {
            console.error("Error fetching feature importance:", error);
            featureImportanceDiv.innerHTML = `<p>Error loading feature importance chart.</p>`;
        }
    }

    // ✅ Initial fetch when the page loads
    fetchGenreChart();
});
