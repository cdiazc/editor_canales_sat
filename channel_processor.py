#!/usr/bin/env python3
"""
Channel Data Processor Module

This module contains the business logic for parsing, converting, and processing
satellite TV channel data in SDX and CHL formats. It is separated from the GUI
to enable unit testing.
"""

import json
import re


class ChannelDataProcessor:
    """
    Handles parsing, conversion, and processing of satellite channel data.
    """

    @staticmethod
    def parse_chl_file(path):
        """
        Parse a CHL file and extract all data.
        
        Args:
            path (str): Path to the CHL file
            
        Returns:
            dict: Parsed data containing index, favorites, satellites, 
                  transponders, and channels
        """
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        data = {
            'index': None,
            'favorites': [],
            'satellites': [],
            'transponders': [],
            'channels': []
        }

        decoder = json.JSONDecoder()
        pos = 0
        while pos < len(content):
            chunk = content[pos:].lstrip()
            if not chunk:
                break
            try:
                obj, index = decoder.raw_decode(chunk)
                obj_type = obj.get('Type', '')

                if obj_type == 'index':
                    data['index'] = obj
                elif obj_type == 'fav':
                    data['favorites'].append(obj)
                elif obj_type == 'sat':
                    data['satellites'].append(obj)
                elif obj_type == 'tp':
                    data['transponders'].append(obj)
                elif obj_type == 'ch':
                    data['channels'].append(obj)

                pos += (len(content[pos:]) - len(chunk)) + index
            except json.JSONDecodeError:
                pos += 1

        return data

    @staticmethod
    def parse_kingofsat_html(html_content):
        """
        Parse KingOfSat HTML to extract channel information.
        
        Args:
            html_content (str): HTML content from KingOfSat
            
        Returns:
            list: List of channel dictionaries with name, sid, and freq
        """
        channels = []
        
        # Search for frequencies: class="bld">10758.50</td>
        # Format: 5 digits dot 2 decimals
        freq_pattern = re.compile(r'class="bld">(\d{5})\.\d{2}</td>')
        
        # Search for channel blocks: from <tr data-channel-id to </tr>
        channel_pattern = re.compile(
            r'<tr\s+data-channel-id="(\d+)">(.*?)</tr>',
            re.DOTALL | re.IGNORECASE
        )
        
        # First, extract all frequencies with their positions
        freq_positions = []
        for match in freq_pattern.finditer(html_content):
            freq_positions.append((match.start(), int(match.group(1))))
        
        # For each channel, find the most recent frequency (earlier in HTML)
        for match in channel_pattern.finditer(html_content):
            channel_pos = match.start()
            channel_html = match.group(2)
            
            # Find the closest previous frequency
            freq = 0
            for pos, f in freq_positions:
                if pos < channel_pos:
                    freq = f
                else:
                    break
            
            # Extract name: class="A3">ChannelName</a>
            name_match = re.search(r'class="A3">([^<]+)</a>', channel_html)
            if not name_match:
                continue
            name = name_match.group(1).strip()
            
            # Extract SID: <td class="s">29850</td>
            sid_match = re.search(r'<td class="s">(\d+)</td>', channel_html)
            if not sid_match:
                continue
            sid = int(sid_match.group(1))
            
            if name and sid:
                channels.append({
                    'name': name,
                    'sid': sid,
                    'freq': freq
                })
        
        # Remove duplicates (same name and SID)
        seen = set()
        unique = []
        for ch in channels:
            key = (ch['name'], ch['sid'])
            if key not in seen:
                seen.add(key)
                unique.append(ch)
        
        return unique

    @staticmethod
    def get_service_type(sdt_type):
        """
        Map SDT service type code to human-readable string.
        
        Args:
            sdt_type (int): SDT service type code
            
        Returns:
            str: Human-readable service type
        """
        types = {
            1: "TV SD",
            2: "Radio",
            17: "TV SD",
            22: "TV SD",
            25: "TV HD",
            31: "TV UHD"
        }
        return types.get(sdt_type, f"Tipo {sdt_type}")

    @staticmethod
    def convert_chl_to_sdx(chl_data):
        """
        Convert CHL data to SDX format.
        
        Args:
            chl_data (dict): Parsed CHL data
            
        Returns:
            list: List of SDX objects
        """
        sdx_objects = []

        # Convert satellites
        for sat in chl_data.get('satellites', []):
            idx = sat.get('Index', 0)
            angle = int(sat.get('Angle', '0'))
            sdx_sat = {
                f"satellite_object_{idx}": {
                    "SatName": sat.get('Name', f'Sat {idx}'),
                    "LowLnbFreq": 9750,
                    "HighLnbFreq": 10600,
                    "SatAngle": angle,
                    "iSatMotoPosition": idx,
                    "usUnicableIndex_old": 0,
                    "TunerMask": 1,
                    "UnicableFreq": 1210,
                    "DLNBMask": 0,
                    "DLNBUserBand": 0,
                    "DLNBType": 0,
                    "UnicableCH": 0,
                    "uiSet": {
                        "uiBit": {
                            "22Hz": 2,
                            "V12": 0,
                            "DiSEqC": 0,
                            "DiSEqC11": 0,
                            "IsUnicable": 0,
                            "UnicableType": 0,
                            "FTAOnly": 0,
                            "Motor": 0,
                            "SatDir": 0,
                            "LNBPower": 0,
                            "SelectedTP": 0,
                            "NetWorkSearch": 0,
                            "Hide": 0
                        },
                        "uiStatus": 5
                    },
                    "tuner2_antena": {
                        "LowLnbFreq": 9750,
                        "HighLnbFreq": 10600,
                        "iSatMotoPosition": idx,
                        "UnicableCH": 0,
                        "UnicableFreq": 1210,
                        "uiSet": {
                            "uiBit": {
                                "22Hz": 2,
                                "DiSEqC": 0,
                                "DiSEqC11": 0,
                                "UnicableType": 0,
                                "Motor": 0,
                                "LNBPower": 0,
                                "SelectedTP": 0
                            },
                            "uiStatus": 5
                        }
                    }
                }
            }
            sdx_objects.append(sdx_sat)

        # Convert transponders
        pol_map = {'H': 0, 'V': 1, 'L': 2, 'R': 3}
        for tp in chl_data.get('transponders', []):
            idx = tp.get('Index', 0)
            freq = int(tp.get('Freq', '0'))
            sr = int(tp.get('SR', '0'))
            pol_str = tp.get('Pol', 'H')
            pol = pol_map.get(pol_str.upper(), 0)
            sat_idx = tp.get('SatIndex', 0)

            sdx_tp = {
                f"transponder_object_{idx}": {
                    "usStartCode": 43690,
                    "usNetworkLen": 0,
                    "Freq": freq,
                    "SR": sr,
                    "t2_plp_index": 0,
                    "t2_signal": 0,
                    "uiFlag": 0,
                    "ucMUX": 0,
                    "ucQam": 0,
                    "stFlag": {
                        "POL": pol,
                        "FEC": 4,
                        "IQ": 0,
                        "SatIndex": sat_idx,
                        "NetNameNo": 0,
                        "TPIndex": idx
                    }
                }
            }
            sdx_objects.append(sdx_tp)

        # Convert channels
        video_codec_map = {'MPEG2': 1, 'H264': 2, 'HEVC': 3, 'H265': 3}
        for ch in chl_data.get('channels', []):
            idx = ch.get('Index', 0)
            tp_idx = ch.get('TPIndex', 0)
            sid = int(ch.get('SID', '0'))
            name = ch.get('Name', f'Canal {idx}')

            # Video codec
            video_type = ch.get('VideoType', 'MPEG2')
            video_codec = video_codec_map.get(video_type, 1)

            # HD detection
            is_hd = 1 if 'HD' in video_type or video_type in ['HEVC', 'H265'] else 0

            # Audio language
            audio_lang = ch.get('AudioLang', 'spa')
            lang_map = {'spa': 83, 'eng': 69, 'por': 80, 'fre': 70, 'ger': 71, 'ita': 73}
            audio_lang_code = lang_map.get(audio_lang.lower()[:3], 83)

            # CA (encryption)
            is_ca = ch.get('CA', 0)

            sdx_ch = {
                f"program_tv_object_{idx}": {
                    "usStartCode": 43690,
                    "ServiceName": name,
                    "stProgNo": {
                        "unShort": {
                            "sLo16": sid,
                            "sHi16": tp_idx
                        }
                    },
                    "iLCN": 0,
                    "SDTServiceType": 25 if is_hd else 1,
                    "ucVideoCodec": video_codec,
                    "ucAudioCodec": 2,
                    "signal_quality": 0,
                    "FEC": 4,
                    "ucTotalCountry": 1,
                    "ucSubtitle": 0,
                    "ucCountry": 0,
                    "ucAC3": 0,
                    "language_code": audio_lang_code,
                    "subtitle_language_code": 0,
                    "uiSet": {
                        "uiBit": {
                            "HD": is_hd,
                            "CA": is_ca,
                            "Skip": 0,
                            "Lock": 0,
                            "Fav": 0,
                            "Mosaic": 0,
                            "ServiceType": 3 if is_hd else 0
                        },
                        "uiStatus": 0
                    },
                    "FavBit": 0
                }
            }
            sdx_objects.append(sdx_ch)

        # Convert favorites
        for fav in chl_data.get('favorites', []):
            idx = fav.get('Index', 0)
            channels_list = fav.get('Channels', [])
            
            # Build favorite entries
            fav_entries = []
            for pos, ch_idx in enumerate(channels_list):
                fav_entries.append({
                    "stProgNo": {
                        "unShort": {
                            "sLo16": 0,  # Will be filled by actual channel SID
                            "sHi16": 0   # Will be filled by actual channel TP
                        }
                    },
                    "usPosition": pos
                })

            sdx_fav = {
                f"fav_list_object_{idx}": {
                    "usStartCode": 43690,
                    "usTotalNO": len(fav_entries),
                    "entries": fav_entries
                }
            }
            sdx_objects.append(sdx_fav)

        # Add box object with favorite names
        if chl_data.get('favorites'):
            fav_names = []
            for fav in chl_data.get('favorites', []):
                name = fav.get('Name', f"Favoritos {fav.get('Index', 0)}")
                # Pad or truncate to 16 characters
                padded_name = (name[:16]).ljust(16, '\x00')
                fav_names.append(padded_name)

            sdx_objects.append({
                "fav_list_info_in_box_object": {
                    "usStartCode": 43690,
                    "ucTotalFavList": len(fav_names),
                    "FavListName": fav_names
                }
            })

        return sdx_objects

    @staticmethod
    def process_sdx_data(all_data_objects):
        """
        Process SDX data objects and extract programs and transponders.
        
        Args:
            all_data_objects (list): List of SDX objects
            
        Returns:
            tuple: (programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index)
        """
        programs_dict = {}
        programs_by_sid_tp = {}
        transponders = {}
        fav_lists_indices = {}
        fav_names_obj_index = -1
        
        # First pass: extract transponders
        for obj in all_data_objects:
            if not isinstance(obj, dict):
                continue
            key = list(obj.keys())[0]
            if "transponder_object_" in key:
                try:
                    idx = int(key.split("_")[-1])
                    data = obj[key]
                    freq = data.get("Freq", 0)
                    transponders[idx] = freq
                except:
                    pass
        
        # Second pass: extract channels and favorites
        channel_order = 0
        for i, obj in enumerate(all_data_objects):
            if not isinstance(obj, dict):
                continue
            key = list(obj.keys())[0]
            
            if "program_tv_object" in key:
                channel_order += 1
                data = obj[key]
                c_name = str(data.get("ServiceName", "Sin Nombre")).strip()
                st_prog_no = data.get("stProgNo", {})
                un_short = st_prog_no.get("unShort", {})
                s_lo16 = un_short.get("sLo16", 0)
                s_hi16 = un_short.get("sHi16", 0)
                ui_set = data.get("uiSet", {}).get("uiBit", {})
                is_hd = ui_set.get("HD", 0)
                is_ca = ui_set.get("CA", 0)
                lcn = data.get("iLCN", 0)
                sdt_type = data.get("SDTServiceType", 0)
                signal_quality = data.get("signal_quality", 0)
                freq = transponders.get(s_hi16, 0)
                prog_idx = key.split("_")[-1]
                unique_key = f"{s_lo16}_{s_hi16}_{prog_idx}"

                channel_data = {
                    'name': c_name,
                    'stProgNo': st_prog_no,
                    'obj_index': i,
                    'order': channel_order,
                    'freq': freq,
                    'sid': s_lo16,
                    'lcn': lcn,
                    'hd': "Sí" if is_hd else "",
                    'ca': "Cifrado" if is_ca else "Libre",
                    'tipo': ChannelDataProcessor.get_service_type(sdt_type),
                    'calidad': f"{signal_quality}%"
                }
                programs_dict[unique_key] = channel_data
                sid_tp_key = f"{s_lo16}_{s_hi16}"
                if sid_tp_key not in programs_by_sid_tp:
                    programs_by_sid_tp[sid_tp_key] = channel_data
            
            elif "fav_list_object_" in key:
                try:
                    idx = int(key.split("_")[-1])
                    fav_lists_indices[idx] = i
                except:
                    pass
            
            elif "fav_list_info_in_box_object" in key:
                fav_names_obj_index = i
        
        return programs_dict, programs_by_sid_tp, transponders, fav_lists_indices, fav_names_obj_index
