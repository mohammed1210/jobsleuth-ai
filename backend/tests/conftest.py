"""Pytest configuration and fixtures."""

import pytest


@pytest.fixture
def mock_supabase_client(monkeypatch):
    """Mock Supabase client for testing without database."""
    class MockTable:
        def __init__(self, data=None):
            self.data = data or []
            self._filters = {}
            self._limit = None
            self._offset = None
            
        def select(self, *args, **kwargs):
            return self
            
        def insert(self, data):
            self.data = [data] if not isinstance(data, list) else data
            return self
            
        def update(self, data):
            return self
            
        def delete(self):
            return self
            
        def eq(self, field, value):
            return self
            
        def gte(self, field, value):
            return self
            
        def lte(self, field, value):
            return self
            
        def ilike(self, field, value):
            return self
            
        def or_(self, query):
            return self
            
        def order(self, field, desc=False):
            return self
            
        def limit(self, n):
            self._limit = n
            return self
            
        def range(self, start, end):
            return self
            
        def execute(self):
            class Result:
                def __init__(self, data):
                    self.data = data
                    self.count = len(data) if data else 0
            return Result(self.data)
    
    class MockClient:
        def table(self, name):
            return MockTable()
    
    def mock_get_client():
        return MockClient()
    
    monkeypatch.setattr("backend.lib.supabase.get_supabase_client", mock_get_client)
    return mock_get_client
