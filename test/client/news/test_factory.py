"""Tests for mydash.client.news.factory.

Target: get_news_client(provider, **config)
Strategy: direct instantiation checks; no HTTP mocking needed.
"""

# --- Factory ---
#
# TODO(testing): default/no provider returns NoozraClient instance —
#   assert isinstance(get_news_client(), NoozraClient)
#
# TODO(testing): unknown provider raises ValueError — parametrize invalid names