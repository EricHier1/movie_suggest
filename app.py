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


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Allow all origins for all routes


# Load dataset
df = pd.read_csv("netflix_titles.csv")
df.fillna("", inplace=True)
df["content"] = df["listed_in"] + " " + df["description"]

# Apply TF-IDF and Cosine Similarity
tfidf = TfidfVectorizer(stop_words="english")
tfidf_matrix = tfidf.fit_transform(df["content"])
cosine_sim = cosine_similarity(tfidf_matrix, tfidf_matrix)

def get_recommendations(title, top_n=10):
    if title not in df["title"].values:
        return []
    
    idx = df[df["title"] == title].index[0]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:top_n+1]
    movie_indices = [i[0] for i in sim_scores]

    recommendations = df.iloc[movie_indices][["title", "listed_in", "description"]].to_dict(orient="records")
    
    return recommendations

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
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)[1:10]  # Top 10 most similar
    
    movie_indices = [i[0] for i in sim_scores]
    movie_names = df.iloc[movie_indices]["title"].tolist()

    # Create similarity matrix
    similarity_matrix = cosine_sim[np.ix_(movie_indices, movie_indices)]

    # Plot heatmap
    plt.figure(figsize=(10, 8))
    sns.heatmap(similarity_matrix, annot=True, xticklabels=movie_names, yticklabels=movie_names, cmap="coolwarm")
    plt.xticks(rotation=45, ha="right")
    plt.title(f"Cosine Similarity Heatmap for '{movie_title}'")

    # Save plot to a byte stream
    img = BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    heatmap_url = base64.b64encode(img.getvalue()).decode()

    return jsonify({"heatmap": f"data:image/png;base64,{heatmap_url}"})

@app.route("/genre-distribution", methods=["GET"])
def genre_distribution():
    genre_counts = df["listed_in"].str.split(", ").explode().value_counts().head(10)

    # Create pie chart
    plt.figure(figsize=(8, 8))
    plt.pie(genre_counts, labels=genre_counts.index, autopct="%1.1f%%", colors=sns.color_palette("pastel"))
    plt.title("Top 10 Movie Genres")

    # Save plot to a byte stream
    img = BytesIO()
    plt.savefig(img, format="png", bbox_inches="tight")
    img.seek(0)
    genre_chart_url = base64.b64encode(img.getvalue()).decode()

    return jsonify({"genre_chart": f"data:image/png;base64,{genre_chart_url}"})

if __name__ == "__main__":
    app.run(debug=True)
