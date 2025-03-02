import atexit
import logging
import os
import pickle
from typing import Dict, Optional, Any


class CacheKit:
    """A simple caching mechanism for storing and retrieving values by key."""
    
    def __init__(self, file_path: str):
        """
        Initialize the cache.
        
        Args:
            file_path: Path to the cache file
        """
        self.file_path = file_path
        self.cache: Dict[str, Any] = {}
        self.logger = logging.getLogger()
        self.loaded = False
        atexit.register(self.save_cache)

    def load_cache(self) -> None:
        """Load the cache from disk."""
        self.logger.debug(f"Loading cache from: {self.file_path}")
        try:
            if os.path.exists(self.file_path) and os.path.getsize(self.file_path) > 0:
                with open(self.file_path, 'rb') as f:
                    self.cache = pickle.load(f)
                self.logger.info(f"Cache loaded successfully with {len(self.cache)} entries")
            else:
                self.logger.info("Cache file doesn't exist or is empty, creating a new cache")
                self.cache = {}
            self.loaded = True
        except (pickle.PickleError, EOFError) as e:
            self.logger.error(f"Error loading cache, creating a new one: {str(e)}")
            self.cache = {}
            self.loaded = True

    def save_cache(self) -> None:
        """Save the cache to disk."""
        if not self.loaded:
            self.logger.debug("Cache not loaded, skipping save")
            return
            
        self.logger.debug(f"Saving cache with {len(self.cache)} entries")
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            
            # Safely write to a temporary file first, then rename
            temp_path = f"{self.file_path}.tmp"
            with open(temp_path, 'wb') as f:
                pickle.dump(self.cache, f)
            
            # Replace the original file with the temp file
            if os.path.exists(self.file_path):
                os.replace(temp_path, self.file_path)
            else:
                os.rename(temp_path, self.file_path)
                
            self.logger.info(f"Cache saved successfully with {len(self.cache)} entries")
        except Exception as e:
            self.logger.error(f"Error saving cache: {str(e)}")

    def get(self, key: str) -> str:
        """
        Get a value from the cache.
        
        Args:
            key: The cache key
            
        Returns:
            The cached value or empty string if not found
        """
        if not self.loaded:
            self.load_cache()
            
        value = self.cache.get(key, "")
        self.logger.debug(f"Cache get: {key} -> {'[Found]' if value else '[Not Found]'}")
        return value

    def set(self, key: str, value: str) -> None:
        """
        Set a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
        """
        if not self.loaded:
            self.load_cache()
            
        self.logger.debug(f"Cache set: {key}")
        self.cache[key] = value

    def delete(self, key: str) -> None:
        """
        Delete a value from the cache.
        
        Args:
            key: The cache key to delete
        """
        if not self.loaded:
            self.load_cache()
            
        if key in self.cache:
            del self.cache[key]
            self.logger.debug(f"Cache delete: {key}")
            
    def has(self, key: str) -> bool:
        """
        Check if a key exists in the cache.
        
        Args:
            key: The cache key to check
            
        Returns:
            True if the key exists, False otherwise
        """
        if not self.loaded:
            self.load_cache()
            
        exists = key in self.cache
        self.logger.debug(f"Cache check: {key} -> {'[Exists]' if exists else '[Does Not Exist]'}")
        return exists

    def clear(self) -> None:
        """Clear all entries from the cache."""
        if not self.loaded:
            self.load_cache()
            
        self.logger.debug(f"Clearing cache with {len(self.cache)} entries")
        self.cache = {}