"""
Unit tests for CHL file parsing functionality.
"""

import os
import pytest
from channel_processor import ChannelDataProcessor


def get_fixture_path(filename):
    """Get the full path to a test fixture file."""
    return os.path.join(os.path.dirname(__file__), '..', 'fixtures', filename)


class TestCHLParsing:
    """Test CHL file parsing functionality."""

    def test_parse_chl_file_basic(self):
        """Test basic CHL file parsing."""
        fixture_path = get_fixture_path('sample.chl')
        result = ChannelDataProcessor.parse_chl_file(fixture_path)
        
        # Check structure
        assert 'satellites' in result
        assert 'transponders' in result
        assert 'channels' in result
        assert 'favorites' in result
        
    def test_parse_chl_file_satellites(self):
        """Test satellite parsing from CHL file."""
        fixture_path = get_fixture_path('sample.chl')
        result = ChannelDataProcessor.parse_chl_file(fixture_path)
        
        satellites = result['satellites']
        assert len(satellites) == 1
        assert satellites[0]['Name'] == 'Astra 19.2E'
        assert satellites[0]['Angle'] == '192'
        assert satellites[0]['Index'] == 0
        
    def test_parse_chl_file_transponders(self):
        """Test transponder parsing from CHL file."""
        fixture_path = get_fixture_path('sample.chl')
        result = ChannelDataProcessor.parse_chl_file(fixture_path)
        
        transponders = result['transponders']
        assert len(transponders) == 1
        assert transponders[0]['Freq'] == '10758'
        assert transponders[0]['SR'] == '22000'
        assert transponders[0]['Pol'] == 'H'
        assert transponders[0]['SatIndex'] == 0
        
    def test_parse_chl_file_channels(self):
        """Test channel parsing from CHL file."""
        fixture_path = get_fixture_path('sample.chl')
        result = ChannelDataProcessor.parse_chl_file(fixture_path)
        
        channels = result['channels']
        assert len(channels) == 2
        
        # Check first channel
        assert channels[0]['Name'] == 'BBC World News'
        assert channels[0]['SID'] == '28654'
        assert channels[0]['VideoType'] == 'MPEG2'
        assert channels[0]['AudioLang'] == 'eng'
        
        # Check second channel
        assert channels[1]['Name'] == 'CNN International'
        assert channels[1]['SID'] == '28655'
        
    def test_parse_chl_file_favorites(self):
        """Test favorites parsing from CHL file."""
        fixture_path = get_fixture_path('sample.chl')
        result = ChannelDataProcessor.parse_chl_file(fixture_path)
        
        favorites = result['favorites']
        assert len(favorites) == 1
        assert favorites[0]['Name'] == 'News Channels'
        assert favorites[0]['Channels'] == [0, 1]
        
    def test_parse_empty_chl_file(self, tmp_path):
        """Test parsing an empty CHL file."""
        empty_file = tmp_path / "empty.chl"
        empty_file.write_text("")
        
        result = ChannelDataProcessor.parse_chl_file(str(empty_file))
        
        assert result['satellites'] == []
        assert result['transponders'] == []
        assert result['channels'] == []
        assert result['favorites'] == []
        
    def test_parse_chl_file_with_invalid_json(self, tmp_path):
        """Test parsing CHL file with some invalid JSON (should skip bad lines)."""
        invalid_file = tmp_path / "invalid.chl"
        content = '''{"Type": "sat", "Index": 0, "Name": "Test Sat", "Angle": "192"}
Invalid JSON line here
{"Type": "ch", "Index": 0, "Name": "Test Channel", "SID": "1000", "TPIndex": 0}
'''
        invalid_file.write_text(content)
        
        result = ChannelDataProcessor.parse_chl_file(str(invalid_file))
        
        # Should still parse valid objects
        assert len(result['satellites']) == 1
        assert len(result['channels']) == 1
