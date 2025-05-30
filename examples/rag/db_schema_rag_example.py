import os

from dbgpt.configs.model_config import MODEL_PATH, PILOT_PATH
from dbgpt.rag.embedding import DefaultEmbeddingFactory
from dbgpt_ext.datasource.rdbms.conn_sqlite import SQLiteTempConnector
from dbgpt_ext.rag.assembler import DBSchemaAssembler
from dbgpt_ext.storage.vector_store.chroma_store import ChromaStore, ChromaVectorConfig

"""DB struct rag example.
    pre-requirements:
    set your embedding model path in your example code.
    ```
    embedding_model_path = "{your_embedding_model_path}"
    ```

    Examples:
        ..code-block:: shell
            python examples/rag/db_schema_rag_example.py
"""


def _create_temporary_connection():
    """Create a temporary database connection for testing."""
    connect = SQLiteTempConnector.create_temporary_db()
    connect.create_temp_tables(
        {
            "user": {
                "columns": {
                    "id": "INTEGER PRIMARY KEY",
                    "name": "TEXT",
                    "age": "INTEGER",
                },
                "data": [
                    (1, "Tom", 10),
                    (2, "Jerry", 16),
                    (3, "Jack", 18),
                    (4, "Alice", 20),
                    (5, "Bob", 22),
                ],
            }
        }
    )
    return connect


def _create_vector_connector():
    """Create vector connector."""
    config = ChromaVectorConfig(
        persist_path=PILOT_PATH,
    )
    return ChromaStore(
        config,
        name="embedding_rag_test",
        embedding_fn=DefaultEmbeddingFactory(
            default_model_name=os.path.join(MODEL_PATH, "text2vec-large-chinese"),
        ).create(),
    )


if __name__ == "__main__":
    connection = _create_temporary_connection()
    vector_connector = _create_vector_connector()
    assembler = DBSchemaAssembler.load_from_connection(
        connector=connection, table_vector_store_connector=vector_connector
    )
    assembler.persist()
    # get db schema retriever
    retriever = assembler.as_retriever(top_k=1)
    chunks = retriever.retrieve("show columns from user")
    print(f"db schema rag example results:{[chunk.content for chunk in chunks]}")
