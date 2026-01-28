"""
Unit tests for utility functions.
"""

import pytest
from channel_processor import ChannelDataProcessor


class TestServiceType:
    """Test service type mapping functionality."""

    def test_get_service_type_tv_sd(self):
        """Test TV SD service types."""
        assert ChannelDataProcessor.get_service_type(1) == "TV SD"
        assert ChannelDataProcessor.get_service_type(17) == "TV SD"
        assert ChannelDataProcessor.get_service_type(22) == "TV SD"
        
    def test_get_service_type_radio(self):
        """Test radio service type."""
        assert ChannelDataProcessor.get_service_type(2) == "Radio"
        
    def test_get_service_type_tv_hd(self):
        """Test TV HD service type."""
        assert ChannelDataProcessor.get_service_type(25) == "TV HD"
        
    def test_get_service_type_tv_uhd(self):
        """Test TV UHD service type."""
        assert ChannelDataProcessor.get_service_type(31) == "TV UHD"
        
    def test_get_service_type_unknown(self):
        """Test unknown service type returns formatted string."""
        assert ChannelDataProcessor.get_service_type(99) == "Tipo 99"
        assert ChannelDataProcessor.get_service_type(0) == "Tipo 0"
        assert ChannelDataProcessor.get_service_type(100) == "Tipo 100"
