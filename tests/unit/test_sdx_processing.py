"""
Unit tests for SDX data processing functionality.
"""

import pytest
from channel_processor import ChannelDataProcessor


class TestSDXDataProcessing:
    """Test SDX data processing functionality."""

    def test_process_sdx_data_empty(self):
        """Test processing empty SDX data."""
        result = ChannelDataProcessor.process_sdx_data([])
        
        programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index = result
        
        assert programs_dict == {}
        assert programs_by_sid_tp == {}
        assert transponders == {}
        assert fav_lists_indices == {}
        assert fav_names_obj_index == -1
        
    def test_process_sdx_data_transponders(self):
        """Test transponder extraction from SDX data."""
        sdx_objects = [
            {
                'transponder_object_0': {
                    'Freq': 10758,
                    'SR': 22000
                }
            },
            {
                'transponder_object_5': {
                    'Freq': 11954,
                    'SR': 27500
                }
            }
        ]
        
        result = ChannelDataProcessor.process_sdx_data(sdx_objects)
        programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index = result
        
        assert len(transponders) == 2
        assert transponders[0] == 10758
        assert transponders[5] == 11954
        
    def test_process_sdx_data_channels(self):
        """Test channel extraction from SDX data."""
        sdx_objects = [
            {
                'transponder_object_0': {
                    'Freq': 10758
                }
            },
            {
                'program_tv_object_0': {
                    'ServiceName': 'BBC World',
                    'stProgNo': {
                        'unShort': {
                            'sLo16': 1000,  # SID
                            'sHi16': 0      # TP Index
                        }
                    },
                    'iLCN': 100,
                    'SDTServiceType': 1,
                    'signal_quality': 85,
                    'uiSet': {
                        'uiBit': {
                            'HD': 0,
                            'CA': 0
                        }
                    }
                }
            }
        ]
        
        result = ChannelDataProcessor.process_sdx_data(sdx_objects)
        programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index = result
        
        assert len(programs_dict) == 1
        
        # Check the unique key format: sid_tp_progidx
        key = '1000_0_0'
        assert key in programs_dict
        
        channel = programs_dict[key]
        assert channel['name'] == 'BBC World'
        assert channel['sid'] == 1000
        assert channel['freq'] == 10758
        assert channel['lcn'] == 100
        assert channel['hd'] == ''
        assert channel['ca'] == 'Libre'
        assert channel['tipo'] == 'TV SD'
        assert channel['calidad'] == '85%'
        
    def test_process_sdx_data_hd_channel(self):
        """Test HD channel processing."""
        sdx_objects = [
            {
                'program_tv_object_0': {
                    'ServiceName': 'Discovery HD',
                    'stProgNo': {
                        'unShort': {
                            'sLo16': 2000,
                            'sHi16': 1
                        }
                    },
                    'iLCN': 0,
                    'SDTServiceType': 25,
                    'signal_quality': 0,
                    'uiSet': {
                        'uiBit': {
                            'HD': 1,
                            'CA': 1
                        }
                    }
                }
            }
        ]
        
        result = ChannelDataProcessor.process_sdx_data(sdx_objects)
        programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index = result
        
        channel = list(programs_dict.values())[0]
        assert channel['hd'] == 'Sí'
        assert channel['ca'] == 'Cifrado'
        assert channel['tipo'] == 'TV HD'
        
    def test_process_sdx_data_favorites_lists(self):
        """Test favorites list index extraction."""
        sdx_objects = [
            {
                'fav_list_object_0': {
                    'usTotalNO': 5,
                    'entries': []
                }
            },
            {
                'fav_list_object_3': {
                    'usTotalNO': 10,
                    'entries': []
                }
            }
        ]
        
        result = ChannelDataProcessor.process_sdx_data(sdx_objects)
        programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index = result
        
        assert len(fav_lists_indices) == 2
        assert fav_lists_indices[0] == 0
        assert fav_lists_indices[3] == 1
        
    def test_process_sdx_data_fav_names_object(self):
        """Test fav names object index extraction."""
        sdx_objects = [
            {
                'program_tv_object_0': {
                    'ServiceName': 'Test'
                }
            },
            {
                'fav_list_info_in_box_object': {
                    'ucTotalFavList': 2,
                    'FavListName': []
                }
            }
        ]
        
        result = ChannelDataProcessor.process_sdx_data(sdx_objects)
        programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index = result
        
        assert fav_names_obj_index == 1
        
    def test_process_sdx_data_sid_tp_lookup(self):
        """Test that programs_by_sid_tp uses first occurrence for duplicate SID_TP."""
        sdx_objects = [
            {
                'program_tv_object_0': {
                    'ServiceName': 'First Channel',
                    'stProgNo': {
                        'unShort': {
                            'sLo16': 1000,
                            'sHi16': 0
                        }
                    },
                    'iLCN': 0,
                    'SDTServiceType': 1,
                    'signal_quality': 0,
                    'uiSet': {
                        'uiBit': {
                            'HD': 0,
                            'CA': 0
                        }
                    }
                }
            },
            {
                'program_tv_object_1': {
                    'ServiceName': 'Duplicate Channel',
                    'stProgNo': {
                        'unShort': {
                            'sLo16': 1000,  # Same SID
                            'sHi16': 0      # Same TP
                        }
                    },
                    'iLCN': 0,
                    'SDTServiceType': 1,
                    'signal_quality': 0,
                    'uiSet': {
                        'uiBit': {
                            'HD': 0,
                            'CA': 0
                        }
                    }
                }
            }
        ]
        
        result = ChannelDataProcessor.process_sdx_data(sdx_objects)
        programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index = result
        
        # Should have 2 entries in programs_dict (different prog_idx)
        assert len(programs_dict) == 2
        
        # Should have only 1 entry in programs_by_sid_tp (first occurrence)
        assert len(programs_by_sid_tp) == 1
        sid_tp_key = '1000_0'
        assert sid_tp_key in programs_by_sid_tp
        assert programs_by_sid_tp[sid_tp_key]['name'] == 'First Channel'
        
    def test_process_sdx_data_channel_order(self):
        """Test that channels maintain their order."""
        sdx_objects = [
            {
                'program_tv_object_0': {
                    'ServiceName': 'Channel 1',
                    'stProgNo': {'unShort': {'sLo16': 1, 'sHi16': 0}},
                    'iLCN': 0,
                    'SDTServiceType': 1,
                    'signal_quality': 0,
                    'uiSet': {'uiBit': {'HD': 0, 'CA': 0}}
                }
            },
            {
                'program_tv_object_1': {
                    'ServiceName': 'Channel 2',
                    'stProgNo': {'unShort': {'sLo16': 2, 'sHi16': 0}},
                    'iLCN': 0,
                    'SDTServiceType': 1,
                    'signal_quality': 0,
                    'uiSet': {'uiBit': {'HD': 0, 'CA': 0}}
                }
            }
        ]
        
        result = ChannelDataProcessor.process_sdx_data(sdx_objects)
        programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index = result
        
        channels = list(programs_dict.values())
        assert channels[0]['order'] == 1
        assert channels[1]['order'] == 2
        
    def test_process_sdx_data_service_type_mapping(self):
        """Test service type mapping for different SDT types."""
        service_types = [
            (1, "TV SD"),
            (2, "Radio"),
            (17, "TV SD"),
            (22, "TV SD"),
            (25, "TV HD"),
            (31, "TV UHD"),
            (99, "Tipo 99"),  # Unknown type
        ]
        
        for sdt_type, expected_type in service_types:
            sdx_objects = [
                {
                    'program_tv_object_0': {
                        'ServiceName': 'Test',
                        'stProgNo': {'unShort': {'sLo16': 1000, 'sHi16': 0}},
                        'iLCN': 0,
                        'SDTServiceType': sdt_type,
                        'signal_quality': 0,
                        'uiSet': {'uiBit': {'HD': 0, 'CA': 0}}
                    }
                }
            ]
            
            result = ChannelDataProcessor.process_sdx_data(sdx_objects)
            programs_dict, _, _, _, _ = result
            
            channel = list(programs_dict.values())[0]
            assert channel['tipo'] == expected_type
