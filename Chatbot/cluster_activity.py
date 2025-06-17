import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import nltk
import re
from collections import Counter
from sklearn.metrics import silhouette_score
import ast


# Download required NLTK data
# nltk.download('punkt')
# nltk.download('stopwords')

# def preprocess_text(text):
#     if isinstance(text, str):
#         # Convert to lowercase
#         text = text.lower()
#         # Remove special characters and digits
#         text = re.sub(r'[^a-zA-Z\s]', '', text)
#         # Tokenize
#         tokens = word_tokenize(text)
#         # Remove stopwords
#         stop_words = set(stopwords.words('english'))
#         tokens = [t for t in tokens if t not in stop_words]
#         return ' '.join(tokens)
#     return ''

def get_cluster_name(cluster_docs, n_terms=5):
    # Get all words in the cluster
    all_words = ' '.join(cluster_docs).lower()
    words = word_tokenize(all_words)

    # Remove stopwords and short words
    stop_words = set(stopwords.words('english'))
    words = [w for w in words if w not in stop_words and len(w) > 2]

    # Get most common words
    word_freq = Counter(words)
    common_words = [word for word, _ in word_freq.most_common(n_terms)]

    # Create a meaningful name
    return ' '.join(common_words).title()


def find_optimal_clusters(embeddings_matrix, max_clusters=10):
    """
    Find the optimal number of clusters using both Elbow Method and Silhouette Analysis
    """
    # Calculate inertia (within-cluster sum of squares) for different numbers of clusters
    inertias = []
    silhouette_scores = []
    K = range(2, max_clusters + 1)

    for k in K:
        kmeans = KMeans(n_clusters=k, random_state=42)
        kmeans.fit(embeddings_matrix)
        inertias.append(kmeans.inertia_)

        # Calculate silhouette score
        if k > 1:  # Silhouette score requires at least 2 clusters
            labels = kmeans.labels_
            silhouette_scores.append(silhouette_score(embeddings_matrix, labels))

    # Plot elbow curve
    plt.figure(figsize=(12, 5))

    # Elbow plot
    plt.subplot(1, 2, 1)
    plt.plot(K, inertias, 'bx-')
    plt.xlabel('k')
    plt.ylabel('Inertia')
    plt.title('Elbow Method')

    # Silhouette plot
    plt.subplot(1, 2, 2)
    plt.plot(K, silhouette_scores, 'rx-')
    plt.xlabel('k')
    plt.ylabel('Silhouette Score')
    plt.title('Silhouette Analysis')

    plt.tight_layout()
    plt.savefig('cluster_analysis.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Find optimal k using silhouette score
    optimal_k = K[np.argmax(silhouette_scores)]
    return optimal_k


def main():
    # Read the activities data
    print("Loading data...")
    df = pd.read_csv('activities.csv')

    # Convert string representation of embeddings to numpy array
    print("Processing embeddings...")
    df['fake_embedding'] = df['embedding'].apply(lambda x: np.array(ast.literal_eval(x)))
    embeddings_matrix = np.stack(df['fake_embedding'].values)

    # Find optimal number of clusters
    print("Finding optimal number of clusters...")
    n_clusters = find_optimal_clusters(embeddings_matrix)
    print(f"Optimal number of clusters: {n_clusters}")

    # Perform K-means clustering with optimal number of clusters
    print("Performing clustering...")
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(embeddings_matrix)

    # Add cluster labels to the dataframe
    df['cluster'] = clusters

    # Name the clusters
    cluster_names = {}
    print("\nAnalyzing clusters to generate names...")
    for i in range(n_clusters):
        cluster_docs = df[df['cluster'] == i]['Description'].tolist()
        cluster_name = get_cluster_name(cluster_docs)
        cluster_names[i] = cluster_name
        df.loc[df['cluster'] == i, 'cluster_name'] = cluster_name

    # Reduce dimensionality for visualization
    pca = PCA(n_components=2)
    reduced_features = pca.fit_transform(embeddings_matrix)

    # Create visualization
    plt.figure(figsize=(15, 10))
    scatter = plt.scatter(reduced_features[:, 0], reduced_features[:, 1],
                          c=clusters, cmap='viridis')

    # Add cluster names to the plot
    for i in range(n_clusters):
        # Get the center of each cluster
        cluster_center = np.mean(reduced_features[clusters == i], axis=0)
        plt.annotate(cluster_names[i],
                     cluster_center,
                     xytext=(10, 10),
                     textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.5),
                     fontsize=8)

    plt.title('Activity Clusters Visualization')
    plt.xlabel('Principal Component 1')
    plt.ylabel('Principal Component 2')
    plt.colorbar(scatter, label='Cluster')
    plt.tight_layout()
    plt.savefig('activity_clusters.png', dpi=300, bbox_inches='tight')
    plt.close()

    # Print cluster information
    print("\nCluster Information:")
    for i in range(n_clusters):
        cluster_docs = df[df['cluster'] == i]['Description'].head(3)
        print(f"\nCluster {i} - {cluster_names[i]}")
        print("Sample descriptions:")
        for doc in cluster_docs:
            print(f"- {doc[:100]}...")
        print(f"Number of activities in this cluster: {len(df[df['cluster'] == i])}")

    # Save results
    df['Name'] = df['cluster_name']
    # Keep all original columns including embedding, but remove temporary columns
    columns_to_keep = [col for col in df.columns if col not in ['cluster', 'cluster_name', 'fake_embedding']]
    df = df[columns_to_keep]
    df.to_csv('activities_clustered.csv', index=False)
    print("\nResults have been saved to 'activities_clustered.csv'")


if __name__ == "__main__":
    main()
