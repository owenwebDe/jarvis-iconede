"""Knowledge Base MCP Server.

Document management, searchable knowledge graph, and company memory.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Dict, List, Any, Optional
from enum import Enum

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger("knowledge_base")
mcp = FastMCP("KnowledgeBase")


class DocType(Enum):
    DOCUMENT = "document"
    MEETING_NOTES = "meeting_notes"
    POLICY = "policy"
    PROCEDURE = "procedure"
    CLIENT_INFO = "client_info"
    CONTRACT = "contract"
    REPORT = "report"
    DECISION = "decision"
    LEARNING = "learning"


# Knowledge storage
_documents: Dict[str, Dict[str, Any]] = {}
_tags: Dict[str, List[str]] = {}  # tag -> [doc_ids]
_entities: Dict[str, Dict[str, Any]] = {}  # entities extracted from docs
_relationships: List[Dict[str, Any]] = []


@mcp.tool()
def add_document(
    title: str,
    content: str,
    doc_type: str = "document",
    tags: str = "",
    author: str = "system",
    metadata: str = "",
) -> str:
    """Add a document to the knowledge base.

    Args:
        title: Document title
        content: Document content
        doc_type: Document type ('document', 'meeting_notes', 'policy', etc.)
        tags: Comma-separated tags
        author: Document author
        metadata: Additional metadata as JSON

    Returns:
        JSON with document details
    """
    doc_id = f"doc-{int(time.time())}-{len(_documents)}"

    tag_list = [t.strip() for t in tags.split(",") if t.strip()] if tags else []

    meta = {}
    if metadata:
        try:
            meta = json.loads(metadata)
        except json.JSONDecodeError:
            meta = {"raw": metadata}

    document = {
        "id": doc_id,
        "title": title,
        "content": content,
        "type": doc_type,
        "tags": tag_list,
        "author": author,
        "metadata": meta,
        "created_at": time.time(),
        "updated_at": time.time(),
        "version": 1,
    }

    _documents[doc_id] = document

    # Index tags
    for tag in tag_list:
        if tag not in _tags:
            _tags[tag] = []
        _tags[tag].append(doc_id)

    # Extract entities (simplified)
    _extract_entities(doc_id, content)

    return json.dumps({
        "status": "created",
        "document_id": doc_id,
        "title": title,
        "tags": tag_list,
    })


@mcp.tool()
def search_documents(
    query: str = "",
    doc_type: str = "",
    tags: str = "",
    limit: int = 20,
) -> str:
    """Search documents in the knowledge base.

    Args:
        query: Search query (searches title and content)
        doc_type: Filter by document type
        tags: Comma-separated tags to filter by
        limit: Max results (default 20)

    Returns:
        JSON with matching documents
    """
    results = []
    query_lower = query.lower() if query else ""

    for doc_id, doc in _documents.items():
        # Filter by type
        if doc_type and doc["type"] != doc_type:
            continue

        # Filter by tags
        if tags:
            tag_list = [t.strip() for t in tags.split(",")]
            if not any(t in doc["tags"] for t in tag_list):
                continue

        # Search in title and content
        if query:
            if query_lower in doc["title"].lower() or query_lower in doc["content"].lower():
                results.append(doc)
        else:
            results.append(doc)

    # Sort by updated_at
    results.sort(key=lambda x: x["updated_at"], reverse=True)
    results = results[:limit]

    return json.dumps({
        "status": "success",
        "documents": results,
        "total_matches": len(results),
    })


@mcp.tool()
def get_document(doc_id: str) -> str:
    """Get a specific document by ID.

    Args:
        doc_id: Document ID

    Returns:
        JSON with document details
    """
    doc = _documents.get(doc_id)
    if not doc:
        return json.dumps({"status": "error", "message": "Document not found"})

    return json.dumps({
        "status": "success",
        "document": doc,
    })


@mcp.tool()
def update_document(
    doc_id: str,
    title: str = "",
    content: str = "",
    tags: str = "",
    updated_by: str = "system",
) -> str:
    """Update a document.

    Args:
        doc_id: Document ID to update
        title: New title (optional)
        content: New content (optional)
        tags: New tags (optional, comma-separated)
        updated_by: Who is updating

    Returns:
        JSON confirmation
    """
    doc = _documents.get(doc_id)
    if not doc:
        return json.dumps({"status": "error", "message": "Document not found"})

    if title:
        doc["title"] = title
    if content:
        doc["content"] = content
        _extract_entities(doc_id, content)
    if tags:
        # Remove old tag indexes
        for tag in doc["tags"]:
            if tag in _tags and doc_id in _tags[tag]:
                _tags[tag].remove(doc_id)

        # Add new tags
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        doc["tags"] = tag_list
        for tag in tag_list:
            if tag not in _tags:
                _tags[tag] = []
            _tags[tag].append(doc_id)

    doc["updated_at"] = time.time()
    doc["version"] += 1

    return json.dumps({
        "status": "updated",
        "document_id": doc_id,
        "version": doc["version"],
    })


@mcp.tool()
def delete_document(doc_id: str) -> str:
    """Delete a document from the knowledge base.

    Args:
        doc_id: Document ID to delete

    Returns:
        JSON confirmation
    """
    doc = _documents.get(doc_id)
    if not doc:
        return json.dumps({"status": "error", "message": "Document not found"})

    # Remove tag indexes
    for tag in doc["tags"]:
        if tag in _tags and doc_id in _tags[tag]:
            _tags[tag].remove(doc_id)

    del _documents[doc_id]

    return json.dumps({
        "status": "deleted",
        "document_id": doc_id,
    })


@mcp.tool()
def get_all_tags() -> str:
    """Get all tags used in the knowledge base.

    Returns:
        JSON with tag index
    """
    tags = {}
    for tag, doc_ids in _tags.items():
        tags[tag] = {
            "count": len(doc_ids),
            "document_ids": doc_ids,
        }

    return json.dumps({
        "status": "success",
        "tags": tags,
        "total_tags": len(tags),
    })


@mcp.tool()
def get_entity_graph() -> str:
    """Get the entity relationship graph.

    Returns:
        JSON with entities and relationships
    """
    return json.dumps({
        "status": "success",
        "entities": _entities,
        "relationships": _relationships,
        "total_entities": len(_entities),
        "total_relationships": len(_relationships),
    })


@mcp.tool()
def link_documents(doc_id_1: str, doc_id_2: str, relationship: str) -> str:
    """Create a relationship link between two documents.

    Args:
        doc_id_1: First document ID
        doc_id_2: Second document ID
        relationship: Type of relationship (e.g., 'related_to', 'references', 'contradicts')

    Returns:
        JSON confirmation
    """
    if doc_id_1 not in _documents or doc_id_2 not in _documents:
        return json.dumps({"status": "error", "message": "One or both documents not found"})

    rel = {
        "from": doc_id_1,
        "to": doc_id_2,
        "relationship": relationship,
        "created_at": time.time(),
    }
    _relationships.append(rel)

    return json.dumps({
        "status": "linked",
        "from": doc_id_1,
        "to": doc_id_2,
        "relationship": relationship,
    })


@mcp.tool()
def get_knowledge_stats() -> str:
    """Get knowledge base statistics.

    Returns:
        JSON with KB stats
    """
    type_counts = {}
    for doc in _documents.values():
        doc_type = doc["type"]
        type_counts[doc_type] = type_counts.get(doc_type, 0) + 1

    return json.dumps({
        "status": "success",
        "total_documents": len(_documents),
        "total_tags": len(_tags),
        "total_entities": len(_entities),
        "total_relationships": len(_relationships),
        "documents_by_type": type_counts,
    })


def _extract_entities(doc_id: str, content: str):
    """Extract entities from document content (simplified)."""
    # Simple entity extraction - in production, use NLP
    words = content.split()
    for word in words:
        if word.istitle() and len(word) > 2:
            if word not in _entities:
                _entities[word] = {"mentions": 0, "documents": []}
            _entities[word]["mentions"] += 1
            if doc_id not in _entities[word]["documents"]:
                _entities[word]["documents"].append(doc_id)


if __name__ == "__main__":
    mcp.run()
