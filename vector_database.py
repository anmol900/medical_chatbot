from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
# Initialize the RecursiveCharacterTextSplitter with the desired parameters
character_splitter = RecursiveCharacterTextSplitter(
    separators=["\n\n", "\n", ". ", " ", ""],
    chunk_size=1000,
    chunk_overlap=0
)

# Read the text from the file with utf-8 encoding
try:
    with open('data.csv', 'r', encoding='utf-8') as file:
        text = file.read()
except UnicodeDecodeError:
    # Fallback to latin-1 encoding if utf-8 fails
    with open('data.csv', 'r', encoding='latin-1') as file:
        text = file.read()

# Split the text into chunks
character_split_texts = character_splitter.split_text(text)

# Print the total number of chunks
#print(f"\nTotal chunks: {len(character_split_texts)}")
token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, tokens_per_chunk=256)

token_split_texts = []
for text in character_split_texts:
    token_split_texts += token_splitter.split_text(text)

#print(f"\nTotal chunks: {len(token_split_texts)}")

embedding_function = SentenceTransformerEmbeddingFunction()
#print(embedding_function([token_split_texts[10]]))

chroma_client = chromadb.Client()
chroma_collection = chroma_client.create_collection("combined", embedding_function=embedding_function)

ids = [str(i) for i in range(len(token_split_texts))]

chroma_collection.add(ids=ids, documents=token_split_texts)
chroma_collection.count()

# query = 'A 69 year old female with difficulty in breathing'

# results = chroma_collection.query(query_texts=[query], n_results=5)
# retrieved_documents = results['documents'][0]

# for document in retrieved_documents:
#     print(document)
#     print('\n')
    
def retrival(query:str):
    results = chroma_collection.query(query_texts=[query], n_results=20)
    retrieved_documents = results['documents'][0]
    return retrieved_documents
    
    
