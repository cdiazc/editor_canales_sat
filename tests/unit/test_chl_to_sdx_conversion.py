"""
Unit tests for CHL to SDX conversion functionality.
"""

import pytest
from channel_processor import ChannelDataProcessor


class TestCHLToSDXConversion:
    """Test CHL to SDX data conversion."""

    def test_convert_chl_to_sdx_satellites(self):
        """Test satellite conversion from CHL to SDX."""
        chl_data = {
            'satellites': [
                {'Index': 0, 'Name': 'Astra 19.2E', 'Angle': '192'}
            ],
            'transponders': [],
            'channels': [],
            'favorites': []
        }
        
        result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
        
        # Should have one satellite object
        sat_objects = [obj for obj in result if 'satellite_object_' in list(obj.keys())[0]]
        assert len(sat_objects) == 1
        
        sat = sat_objects[0]['satellite_object_0']
        assert sat['SatName'] == 'Astra 19.2E'
        assert sat['SatAngle'] == 192
        assert sat['LowLnbFreq'] == 9750
        assert sat['HighLnbFreq'] == 10600
        
    def test_convert_chl_to_sdx_transponders(self):
        """Test transponder conversion from CHL to SDX."""
        chl_data = {
            'satellites': [],
            'transponders': [
                {'Index': 0, 'Freq': '10758', 'SR': '22000', 'Pol': 'H', 'SatIndex': 0}
            ],
            'channels': [],
            'favorites': []
        }
        
        result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
        
        tp_objects = [obj for obj in result if 'transponder_object_' in list(obj.keys())[0]]
        assert len(tp_objects) == 1
        
        tp = tp_objects[0]['transponder_object_0']
        assert tp['Freq'] == 10758
        assert tp['SR'] == 22000
        assert tp['stFlag']['POL'] == 0  # H = 0
        assert tp['stFlag']['SatIndex'] == 0
        
    def test_convert_chl_to_sdx_polarization_mapping(self):
        """Test correct polarization mapping (H=0, V=1, L=2, R=3)."""
        test_cases = [
            ('H', 0),
            ('V', 1),
            ('L', 2),
            ('R', 3),
            ('h', 0),  # lowercase
            ('v', 1),
        ]
        
        for pol_str, expected_pol in test_cases:
            chl_data = {
                'satellites': [],
                'transponders': [
                    {'Index': 0, 'Freq': '10758', 'SR': '22000', 'Pol': pol_str, 'SatIndex': 0}
                ],
                'channels': [],
                'favorites': []
            }
            
            result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
            tp = result[0]['transponder_object_0']
            assert tp['stFlag']['POL'] == expected_pol
        
    def test_convert_chl_to_sdx_channels_basic(self):
        """Test basic channel conversion from CHL to SDX."""
        chl_data = {
            'satellites': [],
            'transponders': [],
            'channels': [
                {
                    'Index': 0,
                    'Name': 'BBC World',
                    'SID': '1000',
                    'TPIndex': 5,
                    'VideoType': 'MPEG2',
                    'AudioLang': 'eng',
                    'CA': 0
                }
            ],
            'favorites': []
        }
        
        result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
        
        ch_objects = [obj for obj in result if 'program_tv_object_' in list(obj.keys())[0]]
        assert len(ch_objects) == 1
        
        ch = ch_objects[0]['program_tv_object_0']
        assert ch['ServiceName'] == 'BBC World'
        assert ch['stProgNo']['unShort']['sLo16'] == 1000
        assert ch['stProgNo']['unShort']['sHi16'] == 5
        
    def test_convert_chl_to_sdx_video_codec_mapping(self):
        """Test video codec mapping (MPEG2=1, H264=2, HEVC/H265=3)."""
        test_cases = [
            ('MPEG2', 1),
            ('H264', 2),
            ('HEVC', 3),
            ('H265', 3),
            ('Unknown', 1),  # default
        ]
        
        for video_type, expected_codec in test_cases:
            chl_data = {
                'satellites': [],
                'transponders': [],
                'channels': [
                    {
                        'Index': 0,
                        'Name': 'Test',
                        'SID': '1000',
                        'TPIndex': 0,
                        'VideoType': video_type,
                        'AudioLang': 'spa',
                        'CA': 0
                    }
                ],
                'favorites': []
            }
            
            result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
            ch = result[0]['program_tv_object_0']
            assert ch['ucVideoCodec'] == expected_codec
        
    def test_convert_chl_to_sdx_hd_detection(self):
        """Test HD flag detection based on video type."""
        hd_types = ['HEVC', 'H265']
        sd_types = ['MPEG2', 'H264']
        
        for video_type in hd_types:
            chl_data = {
                'satellites': [],
                'transponders': [],
                'channels': [
                    {
                        'Index': 0,
                        'Name': 'Test',
                        'SID': '1000',
                        'TPIndex': 0,
                        'VideoType': video_type,
                        'AudioLang': 'spa',
                        'CA': 0
                    }
                ],
                'favorites': []
            }
            
            result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
            ch = result[0]['program_tv_object_0']
            assert ch['uiSet']['uiBit']['HD'] == 1
            assert ch['SDTServiceType'] == 25  # HD service type
        
        for video_type in sd_types:
            chl_data = {
                'satellites': [],
                'transponders': [],
                'channels': [
                    {
                        'Index': 0,
                        'Name': 'Test',
                        'SID': '1000',
                        'TPIndex': 0,
                        'VideoType': video_type,
                        'AudioLang': 'spa',
                        'CA': 0
                    }
                ],
                'favorites': []
            }
            
            result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
            ch = result[0]['program_tv_object_0']
            assert ch['uiSet']['uiBit']['HD'] == 0
            assert ch['SDTServiceType'] == 1  # SD service type
        
    def test_convert_chl_to_sdx_audio_language_mapping(self):
        """Test audio language code mapping."""
        test_cases = [
            ('spa', 83),
            ('eng', 69),
            ('por', 80),
            ('fre', 70),
            ('ger', 71),
            ('ita', 73),
            ('unknown', 83),  # default to spanish
        ]
        
        for lang, expected_code in test_cases:
            chl_data = {
                'satellites': [],
                'transponders': [],
                'channels': [
                    {
                        'Index': 0,
                        'Name': 'Test',
                        'SID': '1000',
                        'TPIndex': 0,
                        'VideoType': 'MPEG2',
                        'AudioLang': lang,
                        'CA': 0
                    }
                ],
                'favorites': []
            }
            
            result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
            ch = result[0]['program_tv_object_0']
            assert ch['language_code'] == expected_code
        
    def test_convert_chl_to_sdx_ca_flag(self):
        """Test CA (encryption) flag conversion."""
        for ca_value in [0, 1]:
            chl_data = {
                'satellites': [],
                'transponders': [],
                'channels': [
                    {
                        'Index': 0,
                        'Name': 'Test',
                        'SID': '1000',
                        'TPIndex': 0,
                        'VideoType': 'MPEG2',
                        'AudioLang': 'spa',
                        'CA': ca_value
                    }
                ],
                'favorites': []
            }
            
            result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
            ch = result[0]['program_tv_object_0']
            assert ch['uiSet']['uiBit']['CA'] == ca_value
        
    def test_convert_chl_to_sdx_favorites(self):
        """Test favorites list conversion."""
        chl_data = {
            'satellites': [],
            'transponders': [],
            'channels': [],
            'favorites': [
                {'Index': 0, 'Name': 'News', 'Channels': [0, 1, 2]},
                {'Index': 1, 'Name': 'Sports', 'Channels': [5, 6]}
            ]
        }
        
        result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
        
        fav_objects = [obj for obj in result if 'fav_list_object_' in list(obj.keys())[0]]
        assert len(fav_objects) == 2
        
        fav0 = fav_objects[0]['fav_list_object_0']
        assert fav0['usTotalNO'] == 3
        assert len(fav0['entries']) == 3
        
        fav1 = fav_objects[1]['fav_list_object_1']
        assert fav1['usTotalNO'] == 2
        assert len(fav1['entries']) == 2
        
    def test_convert_chl_to_sdx_favorite_names_box(self):
        """Test creation of fav_list_info_in_box_object with favorite names."""
        chl_data = {
            'satellites': [],
            'transponders': [],
            'channels': [],
            'favorites': [
                {'Index': 0, 'Name': 'News', 'Channels': []},
                {'Index': 1, 'Name': 'VeryLongNameThatExceeds16Chars', 'Channels': []}
            ]
        }
        
        result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
        
        box_objects = [obj for obj in result if 'fav_list_info_in_box_object' in list(obj.keys())[0]]
        assert len(box_objects) == 1
        
        box = box_objects[0]['fav_list_info_in_box_object']
        assert box['ucTotalFavList'] == 2
        assert len(box['FavListName']) == 2
        
        # Names should be padded/truncated to 16 chars
        assert len(box['FavListName'][0]) == 16
        assert len(box['FavListName'][1]) == 16
        
    def test_convert_chl_to_sdx_empty_data(self):
        """Test conversion with empty CHL data."""
        chl_data = {
            'satellites': [],
            'transponders': [],
            'channels': [],
            'favorites': []
        }
        
        result = ChannelDataProcessor.convert_chl_to_sdx(chl_data)
        
        # Should return empty list
        assert result == []
