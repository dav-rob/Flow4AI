# Massive Parallel RAG Pipeline

Demonstrates Flow4AI's parallel execution at scale with 1000+ document chunks.

## Technical Decisions

| Component | Choice | Rationale |
|-----------|--------|-----------|
| **Vector DB** | ChromaDB | Pure Python, persistent, no external DB needed |
| **Ordinary DB** | None | ChromaDB handles persistence (stores to disk) |
| **Embedding Model** | OpenAI `text-embedding-3-small` | Fast, cheap, 1536 dimensions |
| **Generation Model** | OpenAI `gpt-4o-mini` | Cost-effective, good quality |
| **Reranking** | BM25 via `rank-bm25` | Lightweight, pure Python, no GPU |

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      INDEXING PIPELINE                           │
├─────────────────────────────────────────────────────────────────┤
│  Download Books → Chunk Text → Parallel Embed → Store in Chroma │
│       (1)            (N)       (N parallel)        (batch)      │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                        QUERY PIPELINE                            │
├─────────────────────────────────────────────────────────────────┤
│  Query → Embed → Vector Search → BM25 Rerank → Generate Answer  │
└─────────────────────────────────────────────────────────────────┘
```

## Dependencies

```bash
pip install chromadb rank-bm25
# OpenAI API key required
export OPENAI_API_KEY=your_key_here
```

## Usage

```bash
# Full pipeline (index + query)
python rag_pipeline.py

# Index only (with chunk limit for testing)
python rag_pipeline.py --mode index --chunks 100

# Query only (uses existing index)
python rag_pipeline.py --mode query --query "What is Alice's adventure?"

# Specific books
python rag_pipeline.py --books alice_wonderland sherlock_holmes
```

## Flow4AI Pattern

The key demonstration is **parallel embedding** with Flow4AI:

```python
# Submit 1000+ embedding tasks concurrently
workflow = job(embed=embed_chunk)
fm = FlowManager(on_complete=on_complete)
fq_name = fm.add_workflow(workflow, "embedding_pipeline")

for chunk in chunks:
    task = {"embed.chunk_id": chunk.id, "embed.text": chunk.text}
    fm.submit_task(task, fq_name)

fm.wait_for_completion(timeout=300)
```

## Scale Testing Results

| Chunks | Status |
|--------|--------|
| 1 | ✅ Tested (1.54s, 0.6 chunks/sec) |
| 10 | 🔄 In progress |
| 100 | ⏳ Pending |
| 1000 | ⏳ Pending |

## Status

**Branch**: `feature/massive-parallel-rag`  
**Current State**: Work in progress - basic pipeline functional with 1 chunk

### Known Issues
- Need to investigate async/sync behavior with OpenAI embeddings
- Scale testing incomplete

### TODO
- [ ] Complete scale testing (10, 100, 1000 chunks)
- [ ] Needle-in-haystack tests
- [ ] Edge case testing
