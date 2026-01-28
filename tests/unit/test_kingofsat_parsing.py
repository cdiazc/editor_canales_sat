"""
Unit tests for KingOfSat HTML parsing functionality.
"""

import pytest
from channel_processor import ChannelDataProcessor


class TestKingOfSatParsing:
    """Test KingOfSat HTML parsing functionality."""

    def test_parse_kingofsat_html_basic(self):
        """Test basic HTML parsing from KingOfSat."""
        html = '''<html>
        <tr><td class="bld">10758.50</td></tr>
        <tr data-channel-id="12345">
        <td><a class="A3">BBC World News</a></td>
        <td class="s">28654</td>
        </tr>
        </html>'''
        
        result = ChannelDataProcessor.parse_kingofsat_html(html)
        
        assert len(result) == 1
        assert result[0]['name'] == 'BBC World News'
        assert result[0]['sid'] == 28654
        assert result[0]['freq'] == 10758
        
    def test_parse_kingofsat_html_multiple_channels(self):
        """Test parsing multiple channels with different frequencies."""
        html = '''<html>
        <tr><td class="bld">10758.50</td></tr>
        <tr data-channel-id="1">
        <td><a class="A3">Channel A</a></td>
        <td class="s">1001</td>
        </tr>
        <tr data-channel-id="2">
        <td><a class="A3">Channel B</a></td>
        <td class="s">1002</td>
        </tr>
        <tr><td class="bld">11954.00</td></tr>
        <tr data-channel-id="3">
        <td><a class="A3">Channel C</a></td>
        <td class="s">2001</td>
        </tr>
        </html>'''
        
        result = ChannelDataProcessor.parse_kingofsat_html(html)
        
        assert len(result) == 3
        assert result[0]['freq'] == 10758
        assert result[1]['freq'] == 10758
        assert result[2]['freq'] == 11954
        
    def test_parse_kingofsat_html_removes_duplicates(self):
        """Test that duplicate channels (same name and SID) are removed."""
        html = '''<html>
        <tr><td class="bld">10758.50</td></tr>
        <tr data-channel-id="1">
        <td><a class="A3">BBC News</a></td>
        <td class="s">1001</td>
        </tr>
        <tr data-channel-id="2">
        <td><a class="A3">BBC News</a></td>
        <td class="s">1001</td>
        </tr>
        <tr data-channel-id="3">
        <td><a class="A3">CNN</a></td>
        <td class="s">1002</td>
        </tr>
        </html>'''
        
        result = ChannelDataProcessor.parse_kingofsat_html(html)
        
        # Should only have 2 unique channels
        assert len(result) == 2
        assert result[0]['name'] == 'BBC News'
        assert result[1]['name'] == 'CNN'
        
    def test_parse_kingofsat_html_empty(self):
        """Test parsing empty HTML."""
        html = '<html></html>'
        result = ChannelDataProcessor.parse_kingofsat_html(html)
        assert result == []
        
    def test_parse_kingofsat_html_no_frequency(self):
        """Test parsing HTML with channels but no frequency."""
        html = '''<html>
        <tr data-channel-id="1">
        <td><a class="A3">Test Channel</a></td>
        <td class="s">1001</td>
        </tr>
        </html>'''
        
        result = ChannelDataProcessor.parse_kingofsat_html(html)
        
        # Should still parse but with freq = 0
        assert len(result) == 1
        assert result[0]['freq'] == 0
        
    def test_parse_kingofsat_html_missing_sid(self):
        """Test parsing HTML with channel missing SID."""
        html = '''<html>
        <tr><td class="bld">10758.50</td></tr>
        <tr data-channel-id="1">
        <td><a class="A3">Test Channel</a></td>
        </tr>
        </html>'''
        
        result = ChannelDataProcessor.parse_kingofsat_html(html)
        
        # Should skip channels without SID
        assert len(result) == 0
        
    def test_parse_kingofsat_html_missing_name(self):
        """Test parsing HTML with channel missing name."""
        html = '''<html>
        <tr><td class="bld">10758.50</td></tr>
        <tr data-channel-id="1">
        <td class="s">1001</td>
        </tr>
        </html>'''
        
        result = ChannelDataProcessor.parse_kingofsat_html(html)
        
        # Should skip channels without name
        assert len(result) == 0
        
    def test_parse_kingofsat_html_whitespace_in_name(self):
        """Test that channel names are properly trimmed."""
        html = '''<html>
        <tr><td class="bld">10758.50</td></tr>
        <tr data-channel-id="1">
        <td><a class="A3">  BBC News  </a></td>
        <td class="s">1001</td>
        </tr>
        </html>'''
        
        result = ChannelDataProcessor.parse_kingofsat_html(html)
        
        assert len(result) == 1
        assert result[0]['name'] == 'BBC News'
