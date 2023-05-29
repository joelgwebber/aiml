from pathlib import Path
import chromadb
from chromadb.api import API
from chromadb.api.models.Collection import Collection
from openai.embeddings_utils import get_embedding


# Encapsulates knowledge about the world, encoding it using embeddings, so that it can
# be queried by relevance to context.
# TODO: Use filters or multiple collections to query knowledge unique to each character.
class Lore:
    items: list[str]
    api: API
    embeddings: Collection

    def __init__(self):
        # For now, create a single collection for all lore, as a single in-memory ChromaDB collection.
        # TODO: Make this persistent, so we don't have to keep spending time and money to re-encode lore.
        self.items = []
        self.api = chromadb.Client()
        self.embeddings = self.api.create_collection(name="lore")
        self._parse_all()

    # Parse everything in the lore directory, treating each line as a separate document.
    def _parse_all(self):
        p = Path("./lore")
        for i in p.rglob("**/*.txt"):
            if i.is_file():
                lines = i.read_text().splitlines()
                for line in lines:
                    line = line.strip()
                    if len(line) > 0:
                        self.items.append(line)
                        id = f"{len(self.items)}"
                        vec = get_embedding(line, "text-embedding-ada-002")
                        self.embeddings.add(id, vec)

    # Query for knoledge relevant to the given context.
    # This can be fed directly into the prompt.
    def query(self, context: str, max: int) -> list[str]:
        vec = get_embedding(context, "text-embedding-ada-002")
        result = self.embeddings.query(vec, None, max)
        ids = result['ids'][0]
        items: list[str] = []
        for id in ids:
            idx = int(id)-1
            items.append(self.items[idx])
        return items
