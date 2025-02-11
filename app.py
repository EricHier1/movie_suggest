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

# Initialize Flask App
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Load Dataset
df = pd.read_csv("netflix_titles.csv")
df.fillna("", inplace=True)
df["content"] = df["listed_in"] + " " + df["description"]

# Apply TF-IDF and Compute Cosine Similarity
tfidf = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf.fit_transform(df["content"])
cosine_sim = cosine_similarity(tfidf_matrix)

def get_recommendations(title, top_n=10):
    if title not in df["title"].values:
        return []

    idx = df[df["title"] == title].index[0]
    sim_scores = sorted(enumerate(cosine_sim[idx]), key=lambda x: x[1], reverse=True)[1:top_n+1]
    movie_indices = [i[0] for i in sim_scores]

    return df.iloc[movie_indices][["title", "listed_in", "description"]].to_dict(orient="records")

@app.route("/recommend", methods=["GET"])
def recommend():
    movie_title = request.args.get("title")
    recommendations = get_recommendations(movie_title)
    return jsonify({"recommendations": recommendations})

@app.route("/autocomplete", methods=["GET"])
def autocomplete():
    query = request.args.get("query", "").lower()
    if not query:
        return jsonify([])

    suggestions = df[df["title"].str.lower().str.startswith(query)]["title"].head(10).tolist()
    return jsonify(suggestions)

@app.route("/cosine-heatmap", methods=["GET"])
def cosine_heatmap():
    movie_title = request.args.get("title")
    if movie_title not in df["title"].values:
        return jsonify({"error": "Movie not found"})

    idx = df[df["title"] == movie_title].index[0]
    sim_scores = sorted(enumerate(cosine_sim[idx]), key=lambda x: x[1], reverse=True)[1:10]
    movie_indices = [i[0] for i in sim_scores]
    movie_names = df.iloc[movie_indices]["title"].tolist()

    similarity_matrix = cosine_sim[np.ix_(movie_indices, movie_indices)]

    plt.figure(figsize=(10, 8))
    sns.heatmap(similarity_matrix, annot=True, xticklabels=movie_names, yticklabels=movie_names, cmap="coolwarm")
    plt.xticks(rotation=45, ha="right")
    plt.title(f"Cosine Similarity Heatmap for '{movie_title}'")

    img = BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    heatmap_url = base64.b64encode(img.getvalue()).decode()

    return jsonify({"heatmap": f"data:image/png;base64,{heatmap_url}"})

@app.route("/genre-distribution", methods=["GET"])
def genre_distribution():
    movie_title = request.args.get("title")
    if movie_title not in df["title"].values:
        return jsonify({"error": "Movie not found"}), 404

    movie_genres = df[df["title"] == movie_title]["listed_in"].values[0]
    if not movie_genres:
        return jsonify({"error": "No genres available for this movie."}), 404

    genre_counts = pd.Series(movie_genres.split(", ")).value_counts()

    plt.figure(figsize=(8, 8))
    plt.pie(genre_counts, labels=genre_counts.index, autopct="%1.1f%%", colors=sns.color_palette("pastel"))
    plt.title(f"Genre Distribution for '{movie_title}'")

    img = BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    genre_chart_url = base64.b64encode(img.getvalue()).decode()

    return jsonify({"genre_chart": f"data:image/png;base64,{genre_chart_url}"})

@app.route("/feature-importance", methods=["GET"])
def feature_importance():
    movie_title = request.args.get("title")
    if movie_title not in df["title"].values:
        return jsonify({"error": "Movie not found"}), 404

    idx = df[df["title"] == movie_title].index[0]
    
    feature_array = np.array(tfidf.get_feature_names_out())
    tfidf_scores = tfidf_matrix[idx].toarray().flatten()

    if tfidf_scores.sum() == 0:
        return jsonify({"error": "No TF-IDF scores found for this movie."}), 500

    top_indices = np.argsort(tfidf_scores)[-10:][::-1]
    top_words = feature_array[top_indices]
    top_scores = tfidf_scores[top_indices]

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

if __name__ == "__main__":
    app.run(debug=True)
