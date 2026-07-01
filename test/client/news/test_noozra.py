"""Tests for mydash.client.news.noozra.

Target: NoozraClient
Usage pattern: set_news_headlines(category=...) then get_news_headlines()
Strategy: patch _make_request or mock client.client.get; use mock_urls fixture
Depends on: conftest.mock_urls, conftest.sample_noozra_articles
"""

# --- set_news_headlines ---
#
# TODO(testing): category kwarg passed to _make_request as NoozraParams —
#   call set_news_headlines(category="technology"); assert params.category
#
# TODO(testing): article dict fields map to HeadLine correctly —
#   headline, source→publication, description, url→source_url,
#   category, published_at→published_time

# --- _make_request / HTTP errors ---
#
# TODO(testing): HTTP 500 propagates httpx.HTTPError —
#   mock client.client.get with httpx.HTTPStatusError

# --- Error handling ---
#
# TODO(testing): malformed article data triggers ValidationError handling in
#   set_news_headlines without crashing (verify console logging or empty result)