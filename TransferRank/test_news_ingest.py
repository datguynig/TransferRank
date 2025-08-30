"""Basic tests for news ingestion services."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

from services.ingest.bbc_rss import fetch_bbc_rss, extract_player_from_title, extract_clubs_from_text
from services.ingest.guardian import fetch_guardian_transfers
from services.ingest.dedupe import deduplicate_rumours, get_source_credibility
from services.images.wikimedia import get_player_image, search_wikipedia_page


class TestBBCRSSIngest:
    """Test BBC RSS parsing and normalisation."""
    
    def test_extract_player_from_title(self):
        """Test player name extraction from news titles."""
        # Test exact match
        title = "Harry Kane latest transfer news from Bayern Munich"
        player = extract_player_from_title(title)
        assert player == "Harry Kane"
        
        # Test no match
        title = "Premier League transfer news and updates"
        player = extract_player_from_title(title)
        assert player is None
    
    def test_extract_clubs_from_text(self):
        """Test club extraction from news text."""
        # Test "to" pattern
        text = "Manchester United to Real Madrid transfer completed"
        clubs = extract_clubs_from_text(text)
        assert clubs["from_club"] == "Manchester United"
        assert clubs["to_club"] == "Real Madrid"
        
        # Test no pattern match
        text = "Football transfer news today"
        clubs = extract_clubs_from_text(text)
        assert clubs["from_club"] is None
        assert clubs["to_club"] is None
    
    @patch('services.ingest.bbc_rss.feedparser.parse')
    def test_fetch_bbc_rss_success(self, mock_feedparser):
        """Test successful BBC RSS fetch and parsing."""
        # Mock RSS feed response
        mock_feed = MagicMock()
        mock_feed.bozo = False
        mock_feed.entries = [
            {
                'title': 'Harry Kane to Bayern Munich transfer latest',
                'description': 'The England striker is set to join the German club',
                'link': 'https://bbc.co.uk/sport/example',
                'published_parsed': (2025, 8, 30, 12, 0, 0, 0, 0, 0)
            }
        ]
        mock_feedparser.return_value = mock_feed
        
        rumours = fetch_bbc_rss()
        
        assert len(rumours) == 1
        assert rumours[0]['source_name'] == 'BBC Sport'
        assert rumours[0]['source_type'] == 'outlet'
        assert rumours[0]['player_name'] == 'Harry Kane'
    
    @patch('services.ingest.bbc_rss.feedparser.parse')
    def test_fetch_bbc_rss_error(self, mock_feedparser):
        """Test BBC RSS fetch with network error."""
        mock_feedparser.side_effect = Exception("Network error")
        
        rumours = fetch_bbc_rss()
        
        assert rumours == []


class TestGuardianIngest:
    """Test Guardian API integration."""
    
    @patch('services.ingest.guardian.requests.get')
    @patch('os.environ.get')
    def test_fetch_guardian_success(self, mock_env, mock_requests):
        """Test successful Guardian API fetch."""
        # Mock environment and API response
        mock_env.return_value = 'test-api-key'
        
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'response': {
                'status': 'ok',
                'results': [
                    {
                        'webTitle': 'Erling Haaland transfer news and updates',
                        'fields': {'trailText': 'The Manchester City striker'},
                        'webUrl': 'https://theguardian.com/example',
                        'webPublicationDate': '2025-08-30T12:00:00Z'
                    }
                ]
            }
        }
        mock_requests.return_value = mock_response
        
        rumours = fetch_guardian_transfers()
        
        assert len(rumours) == 1
        assert rumours[0]['source_name'] == 'The Guardian'
        assert rumours[0]['source_type'] == 'outlet'
    
    @patch('os.environ.get')
    def test_fetch_guardian_no_api_key(self, mock_env):
        """Test Guardian fetch with no API key."""
        mock_env.return_value = None
        
        rumours = fetch_guardian_transfers()
        
        assert rumours == []


class TestDeduplication:
    """Test rumour deduplication logic."""
    
    def test_get_source_credibility(self):
        """Test source credibility scoring."""
        # Test known credible source
        credibility = get_source_credibility('BBC Sport')
        assert credibility == 5
        
        # Test known unreliable source
        credibility = get_source_credibility('The Sun')
        assert credibility == 1
        
        # Test unknown source
        credibility = get_source_credibility('Unknown Source')
        assert credibility == 3
    
    def test_deduplicate_rumours_url_duplicate(self):
        """Test deduplication removes URL duplicates."""
        rumours = [
            {
                'source_url': 'https://bbc.co.uk/example',
                'player_name': 'Harry Kane',
                'to_club': 'Bayern Munich',
                'source_name': 'BBC Sport'
            },
            {
                'source_url': 'https://bbc.co.uk/example',  # Same URL
                'player_name': 'Harry Kane',
                'to_club': 'Bayern Munich',
                'source_name': 'BBC Sport'
            }
        ]
        
        with patch('services.ingest.dedupe.Rumour') as mock_rumour:
            mock_rumour.query.filter_by.return_value.first.return_value = MagicMock()
            
            unique = deduplicate_rumours(rumours)
            
            assert len(unique) == 0  # Both filtered out due to existing URL


class TestWikimediaImages:
    """Test Wikimedia image resolution."""
    
    @patch('services.images.wikimedia.requests.get')
    def test_search_wikipedia_page_success(self, mock_requests):
        """Test successful Wikipedia page search."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            'search term',
            ['Harry Kane', 'Harry Potter'],
            ['English footballer', 'Fictional character'],
            ['https://en.wikipedia.org/wiki/Harry_Kane', 'https://en.wikipedia.org/wiki/Harry_Potter']
        ]
        mock_requests.return_value = mock_response
        
        page_title = search_wikipedia_page('Harry Kane')
        
        assert page_title == 'Harry Kane'
    
    @patch('services.images.wikimedia.requests.get')
    def test_search_wikipedia_page_not_found(self, mock_requests):
        """Test Wikipedia search with no results."""
        mock_response = MagicMock()
        mock_response.json.return_value = ['search term', [], [], []]
        mock_requests.return_value = mock_response
        
        page_title = search_wikipedia_page('Unknown Player')
        
        assert page_title is None
    
    def test_get_player_image_no_name(self):
        """Test image fetch with no player name."""
        result = get_player_image(None)
        assert result is None
        
        result = get_player_image('')
        assert result is None


if __name__ == '__main__':
    pytest.main([__file__, '-v'])