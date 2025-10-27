# Caching Protocol

**Version**: 1.0
**Based on**: L208 lines 283-300 (Caching Strategy)
**Last Updated**: 2025-10-26

## Overview

This protocol defines caching procedures for LLM responses to reduce costs and improve performance.

## Cache Operations

### Initialize Cache

```python
from processing.cache_manager import CacheManager

# Initialize with defaults
cache = CacheManager(
    backend_type="simple",
    max_size=10000,
    ttl_seconds=3600
)

print(f"✅ Cache initialized (max_size={cache.max_size}, ttl={cache.ttl_seconds}s)")
```

### Generate Cache Key

```python
# Generate cache key
cache_key = cache.generate_key(
    provider="openai",
    model="gpt-4o-2024-08-06",
    prompt="Extract data from document",
    temperature=0.0,
    seed=42
)

print(f"Cache key: {cache_key}")
```

### Check Cache

```python
# Try to get from cache
cached_response = cache.get(cache_key)

if cached_response:
    print(f"✅ Cache hit! Saved ${cached_response.cost_usd:.4f}")
    response = cached_response.response
else:
    print("Cache miss - calling LLM")
    # Call LLM...
    response = llm_provider.complete(prompt)

    # Store in cache
    cache.set(
        key=cache_key,
        response=response,
        ttl_seconds=7200  # Cache for 2 hours
    )
```

### Cache Statistics

```python
# Get cache stats
stats = cache.get_stats()

print(f"Cache Statistics:")
print(f"  Hit rate: {stats['hit_rate']:.2%}")
print(f"  Total requests: {stats['total_requests']}")
print(f"  Hits: {stats['hits']}")
print(f"  Misses: {stats['misses']}")
print(f"  Size: {stats['size']}")
print(f"  Est. savings: ${stats.get('cost_savings_usd', 0):.2f}")
```

**Bash cache stats**:

```bash
python3 -c "
from processing.cache_manager import CacheManager
cache = CacheManager()
stats = cache.get_stats()
print(f\"Hit rate: {stats['hit_rate']:.1%}\")
print(f\"Size: {stats['size']} / {stats['max_size']}\")
"
```

## Cache Maintenance

### Clear Cache

```python
# Clear all cache entries
cache.clear()
print("✅ Cache cleared")
```

### Invalidate Specific Keys

```python
# Invalidate cache entry
cache.invalidate(cache_key)
print(f"✅ Invalidated: {cache_key}")
```

## Related Protocols

- **PROCESSING_PROTOCOL.md** - Cache integration

## Configuration References

- `configs/caching.yaml` - Cache configuration
- `configs/llm_providers.yaml` - Provider-specific caching

## Module References

- `src/processing/cache_manager.py` - Cache implementation
