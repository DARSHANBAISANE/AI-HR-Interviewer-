from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct
from fastembed import TextEmbedding

# Local embedding model (downloads automatically on first run ~100MB)
embedding_model = TextEmbedding(model_name="BAAI/bge-small-en-v1.5")

# Local database stored in project directory
qdrant_client = QdrantClient(path="./qdrant_data")

COLLECTION_NAME = "interview_context"

def get_embedding(text: str):
    # Generates a 384-dim vector locally without API keys
    embeddings = list(embedding_model.embed([text]))
    return embeddings[0].tolist()

def setup_vector_db():
    if qdrant_client.collection_exists(collection_name=COLLECTION_NAME):
        qdrant_client.delete_collection(collection_name=COLLECTION_NAME)

    # 384 dimensions for bge-small-en-v1.5
    qdrant_client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=384, distance=Distance.COSINE),
    )

    documents = [
        {"id": 1, "type": "job_description", "text": "Senior Python Engineer position requiring 4+ years experience in FastAPI, WebSockets, microservices, and RAG architectures."},
        {"id": 2, "type": "candidate_resume", "text": "Candidate John Doe has 5 years of software development experience specializing in Python, FastAPI, and building high-concurrency real-time systems."}
    ]

    points = []
    for doc in documents:
        vector = get_embedding(doc["text"])
        points.append(PointStruct(
            id=doc["id"],
            vector=vector,
            payload={"type": doc["type"], "text": doc["text"]}
        ))

    qdrant_client.upsert(collection_name=COLLECTION_NAME, points=points)
    print("Ingestion complete! Local embeddings stored successfully in Qdrant.")

if __name__ == "__main__":
    setup_vector_db()