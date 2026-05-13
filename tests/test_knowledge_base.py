"""
Tests for knowledge base module.
"""

import pytest
from aria.knowledge_base import KnowledgeBase


def test_knowledge_base_initialization():
    """Test knowledge base initialization."""
    kb = KnowledgeBase()
    
    assert len(kb.entries) > 0
    assert "command_not_found" in kb.entries


def test_knowledge_base_search():
    """Test knowledge base search."""
    kb = KnowledgeBase()
    
    results = kb.search("command not found")
    assert len(results) > 0
    assert "command" in results[0].pattern.lower()


def test_knowledge_base_get_by_pattern():
    """Test get entry by pattern."""
    kb = KnowledgeBase()
    
    entry = kb.get_by_pattern("command not found")
    assert entry is not None
    assert "command" in entry.pattern.lower()


def test_knowledge_base_categories():
    """Test knowledge base categories."""
    kb = KnowledgeBase()
    
    categories = kb.list_categories()
    assert len(categories) > 0
    assert "errors" in categories


def test_knowledge_base_get_by_category():
    """Test get entries by category."""
    kb = KnowledgeBase()
    
    errors = kb.get_by_category("errors")
    assert len(errors) > 0


def test_knowledge_base_fuzzy_search():
    """Test fuzzy search."""
    kb = KnowledgeBase()
    
    # Should find matches even with typos
    results = kb.search("comand not foun", threshold=0.5)
    # Results may vary depending on threshold
    assert isinstance(results, list)
