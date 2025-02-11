import matplotlib
matplotlib.use('Agg')  # Non-GUI mode to prevent macOS errors

from flask import Flask, request, jsonify
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from flask_cors import CORS
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO
import base64
from data_cleaning import clean_data

# Initialize Flask App
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load Dataset
df = clean_data()

# ✅ Ensure all fields are properly filled to avoid errors
df["genre"] = df["listed_in"].fillna("")
df["description"] = df["description"].fillna("")
df["director"] = df["director"].fillna("")
df["cast"] = df["cast"].fillna("")

# ✅ Apply TF-IDF per field for independent weighting
tfidf_genre = TfidfVectorizer(stop_words="english")
tfidf_desc = TfidfVectorizer(stop_words="english")
tfidf_director = TfidfVectorizer(stop_words="english")
tfidf_cast = TfidfVectorizer(stop_words="english")

tfidf_matrix_genre = tfidf_genre.fit_transform(df["genre"])
tfidf_matrix_desc = tfidf_desc.fit_transform(df["description"])
tfidf_matrix_director = tfidf_director.fit_transform(df["director"])
tfidf_matrix_cast = tfidf_cast.fit_transform(df["cast"])

cosine_genre = cosine_similarity(tfidf_matrix_genre)
cosine_desc = cosine_similarity(tfidf_matrix_desc)
cosine_director = cosine_similarity(tfidf_matrix_director)
cosine_cast = cosine_similarity(tfidf_matrix_cast)

def get_recommendations(title, genre_w, desc_w, director_w, cast_w, top_n=10):
    """Returns a list of recommended movies using weighted cosine similarity."""
    if title not in df["title"].values:
        return []

    idx = df.index[df["title"] == title].tolist()[0]

    # ✅ Normalize the weights so they always sum to 1
    total_weight = genre_w + desc_w + director_w + cast_w
    genre_w, desc_w, director_w, cast_w = (
        genre_w / total_weight, desc_w / total_weight, director_w / total_weight, cast_w / total_weight
    )

    # ✅ Compute weighted similarity using a weighted mean
    combined_similarity = (
        (cosine_genre[idx] * genre_w) +
        (cosine_desc[idx] * desc_w) +
        (cosine_director[idx] * director_w) +
        (cosine_cast[idx] * cast_w)
    )

    sim_scores = list(enumerate(combined_similarity))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n + 1]

    movie_indices = [i[0] for i in sim_scores]
    raw_similarities = [score for _, score in sim_scores]

    # ✅ Prevent zero-division in normalization
    max_similarity = max(raw_similarities) if max(raw_similarities) > 0 else 1
    normalized_similarities = [round((score / max_similarity) * 100, 2) for score in raw_similarities]

    recommendations = df.iloc[movie_indices][["title", "listed_in", "description", "director", "cast"]].copy()
    recommendations["similarity"] = normalized_similarities  

    return recommendations.to_dict(orient="records")

@app.route("/recommend", methods=["GET"])
def recommend():
    """API Endpoint: Get recommendations based on adjustable weights"""
    movie_title = request.args.get("title", "").strip()
    
    genre_w = float(request.args.get("genreWeight", 1))
    desc_w = float(request.args.get("descWeight", 1))
    director_w = float(request.args.get("directorWeight", 1))
    cast_w = float(request.args.get("castWeight", 1))

    recommendations = get_recommendations(movie_title, genre_w, desc_w, director_w, cast_w)
    
    return jsonify({"recommendations": recommendations})

@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("query", "").lower().strip()
    if not query:
        return jsonify([])

    suggestions = df[df["title"].str.lower().str.startswith(query)]["title"].head(10).tolist()
    return jsonify(suggestions)

@app.route("/cosine-heatmap", methods=["GET"])
def cosine_heatmap():
    """Generates a heatmap for similar movies."""
    movie_title = request.args.get("title", "").strip()

    if not movie_title or movie_title not in df["title"].values:
        return jsonify({"error": "Movie not found"}), 404

    idx = df.index[df["title"] == movie_title].tolist()[0]
    sim_scores = sorted(enumerate(cosine_desc[idx]), key=lambda x: x[1], reverse=True)[1:10]

    if not sim_scores:
        return jsonify({"error": "No similarity scores available"}), 404

    movie_indices = [i[0] for i in sim_scores]
    movie_names = df.iloc[movie_indices]["title"].tolist()
    similarity_matrix = cosine_desc[np.ix_(movie_indices, movie_indices)]

    try:
        plt.figure(figsize=(10, 8))
        sns.heatmap(similarity_matrix, annot=True, fmt=".2f", xticklabels=movie_names, yticklabels=movie_names, cmap="coolwarm", linewidths=0.5)
        plt.xticks(rotation=45, ha="right")
        plt.title(f"Cosine Similarity Heatmap for '{movie_title}'")

        img = BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight")
        plt.close()  # ✅ Prevent memory leaks by closing figure
        img.seek(0)
        heatmap_url = base64.b64encode(img.getvalue()).decode()

        return jsonify({"heatmap": f"data:image/png;base64,{heatmap_url}"})
    except Exception as e:
        print("❌ Error generating heatmap:", e)
        return jsonify({"error": "Failed to generate heatmap"}), 500

@app.route("/feature-importance", methods=["GET"])
def feature_importance():
    """Generates a bar chart showing the most important features (words) in TF-IDF."""
    movie_title = request.args.get("title", "").strip()

    if not movie_title or movie_title not in df["title"].values:
        return jsonify({"error": "Movie not found"}), 404

    idx = df[df["title"] == movie_title].index[0]
    
    feature_array = np.array(tfidf_desc.get_feature_names_out())
    tfidf_scores = tfidf_matrix_desc[idx].toarray().flatten()

    if tfidf_scores.sum() == 0:
        return jsonify({"error": "No TF-IDF scores found for this movie."}), 500

    top_indices = np.argsort(tfidf_scores)[-10:][::-1]
    top_words = feature_array[top_indices]
    top_scores = tfidf_scores[top_indices]

    try:
        plt.figure(figsize=(8, 6))
        plt.barh(top_words[::-1], top_scores[::-1], color="royalblue")
        plt.xlabel("TF-IDF Score")
        plt.ylabel("Words")
        plt.title(f"Top Words in '{movie_title}'")

        img = BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight")
        img.seek(0)
        feature_chart_url = base64.b64encode(img.getvalue()).decode()

        return jsonify({"feature_chart": f"data:image/png;base64,{feature_chart_url}"})
    except Exception as e:
        print("❌ Error generating feature importance chart:", e)
        return jsonify({"error": "Failed to generate feature importance chart"}), 500

@app.route("/genre-distribution", methods=["GET"])
def genre_distribution():
    """Generates a bar chart of genre distribution for a given movie."""
    movie_title = request.args.get("title", "").strip()

    if not movie_title or movie_title not in df["title"].values:
        return jsonify({"error": "Movie not found"}), 404

    # Get genres for the requested movie
    idx = df[df["title"] == movie_title].index[0]
    movie_genres = df.at[idx, "genre"].split(", ")

    if not movie_genres or movie_genres == [""]:
        return jsonify({"error": "No genre data available"}), 404

    # Count how many movies exist for each genre
    genre_counts = df["genre"].str.split(", ").explode().value_counts()

    # Filter for the genres of the selected movie
    filtered_genres = genre_counts[genre_counts.index.isin(movie_genres)]

    try:
        plt.figure(figsize=(8, 5))
        filtered_genres.plot(kind="bar", color="royalblue")
        plt.xlabel("Genres")
        plt.ylabel("Number of Movies")
        plt.title(f"Genre Distribution for '{movie_title}'")
        plt.xticks(rotation=45, ha="right")

        img = BytesIO()
        plt.savefig(img, format="png", bbox_inches="tight")
        img.seek(0)
        genre_chart_url = base64.b64encode(img.getvalue()).decode()

        return jsonify({"genre_chart": f"data:image/png;base64,{genre_chart_url}"})
    except Exception as e:
        print("❌ Error generating genre distribution chart:", e)
        return jsonify({"error": "Failed to generate genre distribution chart"}), 500

if __name__ == "__main__":
    print("🚀 Movie Recommender API Running at http://127.0.0.1:5000/")
    app.run(debug=True)
