#!/usr/bin/env python3
import json
import os
import re
import sys
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib.request import urlopen, Request
from urllib.error import URLError


class SDXEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Editor de canales SAT - v3.0")
        self.root.geometry("1500x800")

        # Configurar icono de la aplicación
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            icon_path = os.path.join(script_dir, "icon.png")
            if os.path.exists(icon_path):
                icon = tk.PhotoImage(file=icon_path)
                self.root.iconphoto(True, icon)
                self._icon = icon  # Mantener referencia para evitar garbage collection
        except Exception:
            pass  # Si falla, usar icono por defecto

        # Cursor de espera compatible con Linux, macOS y Windows
        self.cursor_wait = "watch" if sys.platform == "linux" else "wait"

        self.all_data_objects = []
        self.programs_dict = {}
        self.program_list = []
        self.transponders = {}
        self.fav_lists_indices = {}
        self.fav_names_obj_index = -1
        self.fav_trees = {}
        
        # Flag para controlar cambios no guardados
        self.unsaved_changes = False
        
        # Variables para drag & drop
        self.drag_data = {"item": None, "tree": None}
        
        # Variable para edición inline
        self.edit_entry = None

        self._setup_ui()
        
        # Configurar confirmación al cerrar
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _on_closing(self):
        """Confirmar antes de cerrar la aplicación."""
        if self.unsaved_changes:
            result = messagebox.askyesnocancel(
                "Guardar cambios",
                "Hay cambios sin guardar. ¿Deseas guardarlos antes de salir?"
            )
            if result is True:  # Sí, guardar
                self.save_file()
                self.root.destroy()
            elif result is False:  # No, salir sin guardar
                self.root.destroy()
            # Si es None (Cancelar), no hacer nada
        else:
            if messagebox.askokcancel("Salir", "¿Estás seguro de que quieres salir?"):
                self.root.destroy()

    def _mark_unsaved(self):
        """Marca que hay cambios sin guardar."""
        self.unsaved_changes = True
        if not self.root.title().endswith(" *"):
            self.root.title(self.root.title() + " *")

    def _setup_ui(self):
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill=tk.X, padx=10)

        # Grupo: Cargar archivos
        tk.Button(top_frame, text="📂 Cargar SDX", command=self.load_file, bg="#e1e1e1").pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="📂 Cargar CHL", command=self.import_chl_file, bg="#e1e1e1").pack(side=tk.LEFT, padx=2)

        # Separador
        ttk.Separator(top_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Grupo: Guardar archivos
        tk.Button(top_frame, text="💾 Guardar en SDX", command=self.save_file, bg="#8fbc8f", fg="black").pack(side=tk.LEFT, padx=2)
        tk.Button(top_frame, text="💾 Guardar en CHL", command=self.save_as_chl, bg="#87CEEB", fg="black").pack(side=tk.LEFT, padx=2)

        # Botón de KingOfSat a la derecha
        tk.Button(top_frame, text="📡 Importar desde KingOfSat", command=self.import_from_kingofsat,
                  bg="#fff3cd", fg="black").pack(side=tk.RIGHT, padx=5)

        pw = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        pw.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel izquierdo - Lista General
        left_f = tk.LabelFrame(pw, text="Lista General de Canales")
        pw.add(left_f, width=750)

        self.search_var = tk.StringVar()
        try:
            self.search_var.trace_add("write", lambda *args: self._refresh_all_channels_list())
        except AttributeError:
            self.search_var.trace("w", lambda *args: self._refresh_all_channels_list())
        
        search_frame = tk.Frame(left_f)
        search_frame.pack(fill=tk.X, padx=5, pady=5)
        tk.Label(search_frame, text="Buscar:").pack(side=tk.LEFT)
        tk.Entry(search_frame, textvariable=self.search_var).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # Definir columnas para lista general
        columns = ("#", "nombre", "freq", "sid", "lcn", "hd", "ca", "tipo", "calidad")
        self.tree_all = ttk.Treeview(left_f, columns=columns, show="headings", selectmode="extended")
        
        self.tree_all.heading("#", text="#")
        self.tree_all.heading("nombre", text="Nombre")
        self.tree_all.heading("freq", text="Freq (MHz)")
        self.tree_all.heading("sid", text="SID")
        self.tree_all.heading("lcn", text="LCN")
        self.tree_all.heading("hd", text="HD")
        self.tree_all.heading("ca", text="Cifrado")
        self.tree_all.heading("tipo", text="Tipo")
        self.tree_all.heading("calidad", text="Señal")
        
        self.tree_all.column("#", width=45, anchor="center")
        self.tree_all.column("nombre", width=180, anchor="w")
        self.tree_all.column("freq", width=70, anchor="center")
        self.tree_all.column("sid", width=55, anchor="center")
        self.tree_all.column("lcn", width=45, anchor="center")
        self.tree_all.column("hd", width=35, anchor="center")
        self.tree_all.column("ca", width=55, anchor="center")
        self.tree_all.column("tipo", width=60, anchor="center")
        self.tree_all.column("calidad", width=50, anchor="center")

        self.tree_all.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_all = ttk.Scrollbar(left_f, command=self.tree_all.yview)
        sb_all.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree_all.config(yscrollcommand=sb_all.set)

        # Panel derecho - Favoritos
        right_f = tk.LabelFrame(pw, text="Listas de Favoritos (Arrastra para reordenar o haz doble clic en #)")
        pw.add(right_f)

        self.fav_notebook = ttk.Notebook(right_f)
        self.fav_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        btn_f = tk.Frame(right_f)
        btn_f.pack(fill=tk.X, pady=10)
        tk.Button(btn_f, text="Añadir ->", command=self.add_to_fav, bg="#d4edda").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="<- Quitar", command=self.remove_from_fav, bg="#f8d7da").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="↑ Subir", command=lambda: self.move_item(-1)).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_f, text="↓ Bajar", command=lambda: self.move_item(1)).pack(side=tk.LEFT, padx=2)

        # Separador visual
        ttk.Separator(btn_f, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)

        # Gestión de listas
        tk.Button(btn_f, text="➕ Nueva Lista", command=self.create_fav_list, bg="#e1e1e1").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="🗑️ Eliminar Lista", command=self.delete_fav_list, bg="#ffcccc").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_f, text="Renombrar", command=self.rename_fav_group).pack(side=tk.RIGHT, padx=5)

    def import_from_kingofsat(self):
        """Importa canales desde una URL de KingOfSat."""
        if not self.program_list:
            messagebox.showwarning("Aviso", "Primero debes cargar un archivo SDX o CHL")
            return
        
        # Pedir URL al usuario
        url = simpledialog.askstring(
            "Importar desde KingOfSat",
            "Introduce la URL del paquete de KingOfSat:\n\nEjemplo: https://en.kingofsat.net/pack-digitalplusa",
            initialvalue="https://en.kingofsat.net/pack-"
        )
        
        if not url:
            return
        
        # Validar URL
        if "kingofsat.net" not in url:
            messagebox.showerror("Error", "La URL debe ser de kingofsat.net")
            return
        
        try:
            # Mostrar progreso
            self.root.config(cursor=self.cursor_wait)
            self.root.update()
            
            # Descargar página
            req = Request(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            })
            with urlopen(req, timeout=30) as response:
                html_content = response.read().decode('utf-8', errors='replace')
            
            # DEBUG: Guardar HTML para análisis
            debug_path = '/tmp/kingofsat_debug.html'
            try:
                with open(debug_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                print(f"HTML guardado en {debug_path}")
            except:
                pass
            
            # Parsear canales
            kos_channels = self._parse_kingofsat_html(html_content)
            
            if not kos_channels:
                # Mostrar información de debug
                sample = html_content[:2000] if len(html_content) > 2000 else html_content
                has_tables = '<table' in html_content.lower()
                has_tr = '<tr' in html_content.lower()
                num_5digit = len(re.findall(r'\b\d{5}\b', html_content))
                
                messagebox.showwarning("Aviso", 
                    f"No se encontraron canales en la página.\n\n"
                    f"Información de debug:\n"
                    f"- Tamaño HTML: {len(html_content)} bytes\n"
                    f"- Contiene <table>: {has_tables}\n"
                    f"- Contiene <tr>: {has_tr}\n"
                    f"- Números de 5 dígitos encontrados: {num_5digit}\n\n"
                    f"Primeros caracteres:\n{html_content[:500]}")
                return
            
            # Mostrar diálogo de importación con los canales de KingOfSat
            self._show_import_dialog(kos_channels, url)
            
        except URLError as e:
            messagebox.showerror("Error de conexión", f"No se pudo conectar a KingOfSat:\n{e}")
        except Exception as e:
            error_details = traceback.format_exc()
            messagebox.showerror("Error", f"Error al procesar:\n{e}\n\nDetalles:\n{error_details[:500]}")
        finally:
            self.root.config(cursor="")

    def _parse_kingofsat_html(self, html_content):
        """Parsea el HTML real de KingOfSat para extraer canales."""
        channels = []
        current_freq = 0
        
        # Buscar frecuencias: class="bld">10758.50</td>
        # Formato: 5 dígitos punto 2 decimales
        freq_pattern = re.compile(r'class="bld">(\d{5})\.\d{2}</td>')
        
        # Buscar bloques de canal: desde <tr data-channel-id hasta </tr>
        channel_pattern = re.compile(
            r'<tr\s+data-channel-id="(\d+)">(.*?)</tr>',
            re.DOTALL | re.IGNORECASE
        )
        
        # Primero, extraer todas las frecuencias con sus posiciones
        freq_positions = []
        for match in freq_pattern.finditer(html_content):
            freq_positions.append((match.start(), int(match.group(1))))
        
        # Para cada canal, encontrar la frecuencia más reciente (anterior en el HTML)
        for match in channel_pattern.finditer(html_content):
            channel_pos = match.start()
            channel_html = match.group(2)
            
            # Encontrar la frecuencia más cercana anterior
            freq = 0
            for pos, f in freq_positions:
                if pos < channel_pos:
                    freq = f
                else:
                    break
            
            # Extraer nombre: class="A3">NombreCanal</a>
            name_match = re.search(r'class="A3">([^<]+)</a>', channel_html)
            if not name_match:
                continue
            name = name_match.group(1).strip()
            
            # Extraer SID: <td class="s">29850</td>
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
        
        # Eliminar duplicados (mismo nombre y SID)
        seen = set()
        unique = []
        for ch in channels:
            key = (ch['name'], ch['sid'])
            if key not in seen:
                seen.add(key)
                unique.append(ch)
        
        return unique

    def _parse_kingofsat_text(self, content):
        """Parser alternativo - ya no se usa."""
        return []

    def _parse_kingofsat_alternative(self, html_content):
        """Método alternativo - no usado."""
        return []

    def _show_import_dialog(self, kos_channels, url):
        """Muestra diálogo con resultados y opciones de importación."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Importar desde KingOfSat")
        dialog.geometry("700x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame de información
        info_frame = tk.Frame(dialog, pady=10)
        info_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(info_frame, text=f"URL: {url}", anchor="w", fg="blue").pack(fill=tk.X)
        tk.Label(info_frame, text=f"📡 Canales encontrados: {len(kos_channels)}", 
                anchor="w", fg="green", font=('TkDefaultFont', 10, 'bold')).pack(fill=tk.X)
        
        # Lista de canales
        list_frame = tk.LabelFrame(dialog, text="Canales a importar")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        columns = ("name", "sid", "freq")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        tree.heading("name", text="Nombre")
        tree.heading("sid", text="SID")
        tree.heading("freq", text="Freq (MHz)")
        
        tree.column("name", width=350)
        tree.column("sid", width=100)
        tree.column("freq", width=100)
        
        for ch in kos_channels:
            tree.insert("", "end", values=(ch['name'], ch['sid'], ch['freq']))
        
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(list_frame, command=tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=sb.set)
        
        # Frame de opciones
        options_frame = tk.LabelFrame(dialog, text="Opciones")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Selector de lista
        fav_select_frame = tk.Frame(options_frame)
        fav_select_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(fav_select_frame, text="Importar a lista:").pack(side=tk.LEFT)
        
        fav_names = []
        if self.fav_names_obj_index != -1:
            fav_names = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"].get("aucFavReName", [])
        
        fav_options = []
        for f_idx in sorted(self.fav_lists_indices.keys()):
            name = fav_names[f_idx] if f_idx < len(fav_names) and fav_names[f_idx].strip() else f"Lista {f_idx}"
            fav_options.append((f_idx, name))
        
        combo_var = tk.StringVar()
        combo = ttk.Combobox(fav_select_frame, textvariable=combo_var, state="readonly", width=25)
        combo['values'] = [f"{idx}: {name}" for idx, name in fav_options]
        if combo['values']:
            combo.current(0)
        combo.pack(side=tk.LEFT, padx=10)
        
        # Checkbox sobreescribir
        overwrite_var = tk.BooleanVar(value=False)
        overwrite_check = tk.Checkbutton(options_frame, text="Sobreescribir lista (eliminar canales existentes)", 
                                          variable=overwrite_var, fg="red")
        overwrite_check.pack(anchor=tk.W, padx=5, pady=5)
        
        # Botones
        action_frame = tk.Frame(dialog, pady=10)
        action_frame.pack(fill=tk.X, padx=10)
        
        def do_import():
            if not combo_var.get():
                return
            tab_id = int(combo_var.get().split(":")[0])
            overwrite = overwrite_var.get()
            self._import_kos_channels(kos_channels, tab_id, overwrite)
            dialog.destroy()
            action = "reemplazaron" if overwrite else "añadieron"
            messagebox.showinfo("Importación completada", f"Se {action} {len(kos_channels)} canales.")
        
        tk.Button(action_frame, text="Importar canales", command=do_import, 
                  bg="#90EE90", fg="black", activebackground="#32CD32", 
                  font=('TkDefaultFont', 10, 'bold'), padx=20).pack(side=tk.LEFT, padx=10)
        tk.Button(action_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT)

    def _import_kos_channels(self, channels, tab_id, overwrite=False):
        """Importa canales de KingOfSat a una lista de favoritos."""
        tree = self.fav_trees[tab_id]
        
        # Si overwrite, eliminar todos los canales existentes
        if overwrite:
            for item in tree.get_children():
                tree.delete(item)
        
        # Crear índice de frecuencia -> transponder del SDX
        freq_to_tp = {}
        for tp_idx, freq in self.transponders.items():
            # Guardar frecuencia exacta y con tolerancia ±3 MHz
            for delta in range(-3, 4):
                f = freq + delta
                if f not in freq_to_tp:
                    freq_to_tp[f] = tp_idx
        
        current_count = len(tree.get_children())
        
        for ch in channels:
            current_count += 1
            sid = ch['sid']
            freq = ch['freq']
            
            # Buscar transponder por frecuencia
            tp_idx = freq_to_tp.get(freq, 0)
            
            # Fabricar entrada (orden de claves importante para el receptor)
            ui_word32 = (tp_idx << 16) | sid
            
            fav_entry = {
                "uiWord32": ui_word32,
                "unShort": {
                    "sLo16": sid,
                    "sHi16": tp_idx
                }
            }
            
            fav_json = json.dumps(fav_entry, separators=(',', ':'))
            
            tree.insert("", "end", tags=(fav_json,), values=(
                current_count,
                ch['name'],
                freq,
                sid,
                "",  # LCN
                "",  # HD
                "",  # CA
                ""   # Tipo
            ))
        
        self._sync(tab_id)
        self._mark_unsaved()

    def import_chl_file(self):
        """Importa un archivo CHL convirtiéndolo a formato SDX."""
        path = filedialog.askopenfilename(
            title="Seleccionar archivo CHL",
            filetypes=[("CHL Files", "*.chl"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            self.root.config(cursor=self.cursor_wait)
            self.root.update()

            # Parse the CHL file
            chl_data = self._parse_chl_file(path)

            if not chl_data.get('channels'):
                messagebox.showwarning("Aviso", "No se encontraron canales en el archivo CHL.")
                return

            # Convert to SDX format
            sdx_objects = self._convert_chl_to_sdx(chl_data)

            # Load the converted data
            self.all_data_objects = sdx_objects
            self._process_data()
            self._refresh_all_channels_list()
            self._build_fav_tabs()

            # Reset unsaved changes flag
            self.unsaved_changes = False
            self.root.title("Editor de canales SAT - v3.0 (Importado desde CHL)")

            messagebox.showinfo("Éxito",
                f"Importación CHL completada:\n"
                f"- {len(chl_data.get('satellites', []))} satélites\n"
                f"- {len(chl_data.get('transponders', []))} transponders\n"
                f"- {len(chl_data.get('channels', []))} canales\n"
                f"- {len(chl_data.get('favorites', []))} listas de favoritos")

        except Exception as e:
            error_details = traceback.format_exc()
            messagebox.showerror("Error", f"Error al importar CHL:\n{e}\n\nDetalles:\n{error_details[:500]}")
        finally:
            self.root.config(cursor="")

    def _parse_chl_file(self, path):
        """Parse a CHL file and extract all data."""
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

    def _convert_chl_to_sdx(self, chl_data):
        """Convert CHL data to SDX format."""
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
            is_hd = 1 if ('HD' in name.upper() or video_type in ['H264', 'HEVC', 'H265']) else 0

            # CA (encrypted)
            ca_val = ch.get('CA', 0)
            is_ca = 1 if ca_val > 0 else 0

            # Service type
            sdt_type = 25 if is_hd else 1  # 25=HD, 1=SD

            # Audio array
            audio_array = []
            for aud in ch.get('Audio', []):
                lang_str = aud.get('Lang', 'und')
                # Map language string to numeric code (simplified)
                lang_code = 0
                if lang_str == 'spa':
                    lang_code = 83
                elif lang_str == 'eng':
                    lang_code = 69
                elif lang_str == 'por':
                    lang_code = 80

                audio_codec = 0  # MPEG
                if aud.get('Type') == 'AAC':
                    audio_codec = 1
                elif aud.get('Type') == 'AC3' or aud.get('DolbyAC3', 0):
                    audio_codec = 2

                audio_array.append({
                    "PID": aud.get('PID', 0),
                    "Mode": 0,
                    "Lang": lang_code,
                    "Codec": audio_codec
                })

            # If no audio, add default
            if not audio_array:
                audio_array.append({"PID": 0, "Mode": 0, "Lang": 0, "Codec": 0})

            sdx_ch = {
                f"program_tv_object_{idx}": {
                    "uiStartCode": 21845,
                    "ucNameLen": len(name),
                    "ucAudioPID": len(audio_array),
                    "ucSubPID": 0,
                    "VideoPID": ch.get('VideoPID', 0),
                    "PCRPID": ch.get('PcrPID', ch.get('VideoPID', 0)),
                    "PMTPID": ch.get('PmtPID', 0),
                    "TTXPID": ch.get('TTXPID', 8191),
                    "stProgNo": {
                        "ServiceID": f"{tp_idx:08d}{sid:06d}",
                        "unShort": {
                            "sLo16": sid,
                            "sHi16": tp_idx
                        }
                    },
                    "uiSet": {
                        "uiBit": {
                            "Lock": ch.get('Lock', 0),
                            "TV": 0,
                            "Skip": ch.get('Skip', 0),
                            "CA": is_ca,
                            "VideoCodec": video_codec,
                            "HD": is_hd,
                            "Hide": ch.get('Hide', 0),
                            "NetNameSelected": 0
                        },
                        "uiStatus": 0
                    },
                    "TSID": 0,
                    "ONID": 0,
                    "SDTServiceType": sdt_type,
                    "t2mi_pg": ch.get('t2miPg', 0),
                    "t2mi_plp_id": ch.get('t2miPlpId', 0),
                    "t2mi_payload_pid": ch.get('t2miPayloadPid', 8191),
                    "FavBit": 0,
                    "iLCN": 0,
                    "uiOriginalLCN": 0,
                    "country_code": 0,
                    "channel_list_id": 0,
                    "visible": 0,
                    "signal_quality": 75,
                    "t2_signal": 0,
                    "t2_plp_index": 0,
                    "t2_plp_id": 0,
                    "t2_lite_or_base": 0,
                    "ServiceName": name,
                    "AudioSelected": 0,
                    "AudioArray": audio_array,
                    "SubtSelected": 0,
                    "SubtArray": []
                }
            }
            sdx_objects.append(sdx_ch)

        # Build channel index to (SID, TPIndex) mapping
        ch_idx_to_sid_tp = {}
        for ch in chl_data.get('channels', []):
            ch_idx = ch.get('Index', 0)
            sid = int(ch.get('SID', '0'))
            tp_idx = ch.get('TPIndex', 0)
            ch_idx_to_sid_tp[ch_idx] = (sid, tp_idx)

        # Convert favorites
        fav_names = []
        for fav in chl_data.get('favorites', []):
            idx = fav.get('Index', 0)
            name = fav.get('Name', f'Lista {idx}')
            fav_names.append(name)

            # Convert TVChs to stProgNo
            st_prog_no = []
            for ch_idx in fav.get('TVChs', []):
                if ch_idx in ch_idx_to_sid_tp:
                    sid, tp_idx = ch_idx_to_sid_tp[ch_idx]
                    ui_word32 = (tp_idx << 16) | sid
                    st_prog_no.append({
                        "uiWord32": ui_word32,
                        "unShort": {
                            "sLo16": sid,
                            "sHi16": tp_idx
                        }
                    })

            sdx_fav = {
                f"fav_list_object_{idx}": {
                    "sNoOfTVFavor": len(st_prog_no),
                    "sNoOfRadioFavor": 0,
                    "stProgNo": st_prog_no
                }
            }
            sdx_objects.append(sdx_fav)

        # Asegurar que fav_names tenga al menos 8 entradas y esté ordenado por índice
        # Crear lista con todos los nombres en sus posiciones correctas
        max_idx = max([fav.get('Index', 0) for fav in chl_data.get('favorites', [])] + [7])
        all_fav_names = [f"Lista {i}" for i in range(max_idx + 1)]
        for fav in chl_data.get('favorites', []):
            idx = fav.get('Index', 0)
            name = fav.get('Name', f'Lista {idx}')
            if idx < len(all_fav_names):
                all_fav_names[idx] = name

        # Create fav_list_info_in_box_object
        sdx_fav_info = {
            "fav_list_info_in_box_object": {
                "aucFavReName": all_fav_names,
                "ucFavNameChangeMask": (1 << len(all_fav_names)) - 1  # Todos los bits activos
            }
        }
        sdx_objects.append(sdx_fav_info)

        # Create box_object with basic settings
        sdx_box = {
            "box_object": {
                "aucFavReName": all_fav_names,
                "ucFavNameChangeMask": (1 << len(all_fav_names)) - 1
            }
        }
        sdx_objects.append(sdx_box)

        return sdx_objects

    def _setup_drag_and_drop(self, tree, tab_id):
        """Configura drag & drop, edición inline y tecla Delete para un Treeview de favoritos."""
        tree.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, tree, tab_id))
        tree.bind("<B1-Motion>", lambda e: self._on_drag_motion(e, tree))
        tree.bind("<ButtonRelease-1>", lambda e: self._on_drag_release(e, tree, tab_id))
        tree.bind("<Double-1>", lambda e: self._on_double_click(e, tree, tab_id))
        tree.bind("<Delete>", lambda e: self._on_delete_key(tree, tab_id))
        tree.bind("<BackSpace>", lambda e: self._on_delete_key(tree, tab_id))

    def _on_delete_key(self, tree, tab_id):
        """Maneja la tecla Delete/Supr para eliminar canales."""
        self._remove_selected_from_fav(tree, tab_id)

    def _on_drag_start(self, event, tree, tab_id):
        self._close_edit_entry()
        item = tree.identify_row(event.y)
        if item:
            self.drag_data["item"] = item
            self.drag_data["tree"] = tree
            self.drag_data["tab_id"] = tab_id
            tree.selection_set(item)

    def _on_drag_motion(self, event, tree):
        if not self.drag_data["item"]:
            return
        target = tree.identify_row(event.y)
        if target and target != self.drag_data["item"]:
            bbox = tree.bbox(target)
            if bbox:
                mid_y = bbox[1] + bbox[3] // 2
                source_idx = tree.index(self.drag_data["item"])
                target_idx = tree.index(target)
                if event.y < mid_y and source_idx > target_idx:
                    tree.move(self.drag_data["item"], "", target_idx)
                elif event.y >= mid_y and source_idx < target_idx:
                    tree.move(self.drag_data["item"], "", target_idx)

    def _on_drag_release(self, event, tree, tab_id):
        if self.drag_data["item"]:
            self._renumber_fav_tree(tree)
            self._sync(tab_id)
            self._mark_unsaved()
        self.drag_data["item"] = None
        self.drag_data["tree"] = None

    def _on_double_click(self, event, tree, tab_id):
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        if not item or column != "#1":
            return
        self._close_edit_entry()
        bbox = tree.bbox(item, column)
        if not bbox:
            return
        x, y, width, height = bbox
        values = tree.item(item, "values")
        current_value = values[0] if values else ""
        self.edit_entry = tk.Entry(tree, width=5, justify="center")
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus()
        self.edit_entry.item = item
        self.edit_entry.tree = tree
        self.edit_entry.tab_id = tab_id
        self.edit_entry.bind("<Return>", self._confirm_edit)
        self.edit_entry.bind("<Escape>", lambda e: self._close_edit_entry())
        self.edit_entry.bind("<FocusOut>", self._confirm_edit)

    def _confirm_edit(self, event=None):
        if not self.edit_entry:
            return
        try:
            new_pos = int(self.edit_entry.get())
            tree = self.edit_entry.tree
            item = self.edit_entry.item
            tab_id = self.edit_entry.tab_id
            total_items = len(tree.get_children())
            if new_pos < 1:
                new_pos = 1
            elif new_pos > total_items:
                new_pos = total_items
            tree.move(item, "", new_pos - 1)
            self._renumber_fav_tree(tree)
            self._sync(tab_id)
            self._mark_unsaved()
        except ValueError:
            pass
        self._close_edit_entry()

    def _close_edit_entry(self):
        if self.edit_entry:
            self.edit_entry.destroy()
            self.edit_entry = None

    def load_file(self):
        path = filedialog.askopenfilename(filetypes=[("SDX Files", "*.sdx")])
        if not path: return
        try:
            with open(path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()

            self.all_data_objects = []
            self.programs_dict = {}
            self.program_list = []
            self.transponders = {}
            
            decoder = json.JSONDecoder()
            pos = 0
            while pos < len(content):
                chunk = content[pos:].lstrip()
                if not chunk: break
                try:
                    obj, index = decoder.raw_decode(chunk)
                    self.all_data_objects.append(obj)
                    pos += (len(content[pos:]) - len(chunk)) + index
                except json.JSONDecodeError:
                    pos += 1

            self._process_data()
            self._refresh_all_channels_list()
            self._build_fav_tabs()
            
            # Resetear flag de cambios
            self.unsaved_changes = False
            self.root.title("Editor de canales SAT - v3.0")
            
            messagebox.showinfo("Éxito", f"Carga completada: {len(self.program_list)} canales encontrados.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer: {e}")

    def _get_service_type(self, sdt_type):
        types = {1: "TV SD", 2: "Radio", 17: "TV SD", 22: "TV SD", 25: "TV HD", 31: "TV UHD"}
        return types.get(sdt_type, f"Tipo {sdt_type}")

    def _process_data(self):
        self.programs_dict = {}
        self.programs_by_sid_tp = {}  # Secondary lookup by SID_TP only
        self.program_list = []
        self.transponders = {}
        self.fav_lists_indices = {}
        
        for obj in self.all_data_objects:
            if not isinstance(obj, dict): continue
            key = list(obj.keys())[0]
            if "transponder_object_" in key:
                try:
                    idx = int(key.split("_")[-1])
                    data = obj[key]
                    freq = data.get("Freq", 0)
                    self.transponders[idx] = freq
                except: pass
        
        channel_order = 0
        for i, obj in enumerate(self.all_data_objects):
            if not isinstance(obj, dict): continue
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
                freq = self.transponders.get(s_hi16, 0)
                # Use program index to ensure uniqueness for duplicate SID/TP combinations
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
                    'tipo': self._get_service_type(sdt_type),
                    'calidad': f"{signal_quality}%"
                }
                self.programs_dict[unique_key] = channel_data
                # Also store by SID_TP for favorites lookup (keeps first occurrence)
                sid_tp_key = f"{s_lo16}_{s_hi16}"
                if sid_tp_key not in self.programs_by_sid_tp:
                    self.programs_by_sid_tp[sid_tp_key] = channel_data
                self.program_list.append((unique_key, c_name))
            
            elif "fav_list_object_" in key:
                try:
                    idx = int(key.split("_")[-1])
                    self.fav_lists_indices[idx] = i
                except: pass
            
            elif "fav_list_info_in_box_object" in key:
                self.fav_names_obj_index = i

    def _refresh_all_channels_list(self):
        self.tree_all.delete(*self.tree_all.get_children())
        query = self.search_var.get().lower()
        for unique_key, name in sorted(self.program_list, key=lambda x: x[1].lower()):
            if query in name.lower():
                info = self.programs_dict[unique_key]
                self.tree_all.insert("", "end", iid=unique_key, values=(
                    info['order'], info['name'], info['freq'], info['sid'],
                    info['lcn'], info['hd'], info['ca'], info['tipo'], info['calidad']
                ))

    def _create_fav_tree(self, parent, tab_id):
        columns = ("#", "nombre", "freq", "sid", "lcn", "hd", "ca", "tipo")
        tree = ttk.Treeview(parent, columns=columns, show="headings", selectmode="browse")
        tree.heading("#", text="#")
        tree.heading("nombre", text="Nombre")
        tree.heading("freq", text="Freq")
        tree.heading("sid", text="SID")
        tree.heading("lcn", text="LCN")
        tree.heading("hd", text="HD")
        tree.heading("ca", text="Cifrado")
        tree.heading("tipo", text="Tipo")
        tree.column("#", width=40, anchor="center")
        tree.column("nombre", width=150, anchor="w")
        tree.column("freq", width=55, anchor="center")
        tree.column("sid", width=50, anchor="center")
        tree.column("lcn", width=45, anchor="center")
        tree.column("hd", width=30, anchor="center")
        tree.column("ca", width=55, anchor="center")
        tree.column("tipo", width=55, anchor="center")
        self._setup_drag_and_drop(tree, tab_id)
        return tree

    def _build_fav_tabs(self):
        for tab in self.fav_notebook.tabs(): 
            self.fav_notebook.forget(tab)
        self.fav_trees = {}
        
        names = []
        if self.fav_names_obj_index != -1:
            names = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"].get("aucFavReName", [])

        for f_idx in sorted(self.fav_lists_indices.keys()):
            full_name = names[f_idx] if f_idx < len(names) and names[f_idx].strip() else f"Lista {f_idx}"
            # Truncar nombre a máximo 7 caracteres para la pestaña
            tab_name = full_name[:7] if len(full_name) > 7 else full_name
            # Añadir espacios para forzar ancho mínimo de 7 caracteres
            tab_name = tab_name.center(7)
            
            frame = tk.Frame(self.fav_notebook)
            self.fav_notebook.add(frame, text=tab_name)
            
            tree = self._create_fav_tree(frame, f_idx)
            tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb = ttk.Scrollbar(frame, command=tree.yview)
            sb.pack(side=tk.RIGHT, fill=tk.Y)
            tree.config(yscrollcommand=sb.set)
            self.fav_trees[f_idx] = tree
            
            obj_idx = self.fav_lists_indices[f_idx]
            key = f"fav_list_object_{f_idx}"
            
            fav_order = 0
            for fav_entry in self.all_data_objects[obj_idx][key].get("stProgNo", []):
                fav_order += 1
                un_short = fav_entry.get("unShort", {})
                s_lo16 = un_short.get("sLo16", 0)
                s_hi16 = un_short.get("sHi16", 0)
                lookup_key = f"{s_lo16}_{s_hi16}"
                channel_info = self.programs_by_sid_tp.get(lookup_key)
                
                if channel_info:
                    fav_json = json.dumps(fav_entry, separators=(',', ':'))
                    tree.insert("", "end", tags=(fav_json,), values=(
                        fav_order, channel_info['name'], channel_info['freq'],
                        channel_info['sid'], channel_info['lcn'], channel_info['hd'],
                        channel_info['ca'], channel_info['tipo']
                    ))
                else:
                    fav_json = json.dumps(fav_entry, separators=(',', ':'))
                    tree.insert("", "end", tags=(fav_json,), values=(
                        fav_order, f"Desconocido ({s_lo16}_{s_hi16})", "", s_lo16, "", "", "", ""
                    ))

    def _renumber_fav_tree(self, tree):
        for idx, item in enumerate(tree.get_children(), 1):
            values = list(tree.item(item, "values"))
            values[0] = idx
            tree.item(item, values=values)

    def add_to_fav(self):
        tab_id = self._get_current_fav_id()
        if tab_id is None: return
        sel = self.tree_all.selection()
        if not sel:
            return
        tree = self.fav_trees[tab_id]
        current_count = len(tree.get_children())
        
        for unique_key in sel:
            channel_info = self.programs_dict.get(unique_key)
            if channel_info:
                current_count += 1
                st_prog_no = channel_info['stProgNo']
                un_short = st_prog_no.get("unShort", {})
                s_lo16 = un_short.get("sLo16", 0)
                s_hi16 = un_short.get("sHi16", 0)
                ui_word32 = (s_hi16 << 16) | s_lo16
                fav_entry = {"uiWord32": ui_word32, "unShort": {"sLo16": s_lo16, "sHi16": s_hi16}}
                fav_json = json.dumps(fav_entry, separators=(',', ':'))
                tree.insert("", "end", tags=(fav_json,), values=(
                    current_count, channel_info['name'], channel_info['freq'],
                    channel_info['sid'], channel_info['lcn'], channel_info['hd'],
                    channel_info['ca'], channel_info['tipo']
                ))
        self._sync(tab_id)
        self._mark_unsaved()

    def remove_from_fav(self):
        """Elimina canales seleccionados de favoritos (botón)."""
        tab_id = self._get_current_fav_id()
        if tab_id is None: return
        tree = self.fav_trees[tab_id]
        self._remove_selected_from_fav(tree, tab_id)

    def _remove_selected_from_fav(self, tree, tab_id):
        """Elimina canales seleccionados y selecciona el siguiente."""
        selection = tree.selection()
        if not selection:
            return
        
        # Obtener todos los items y encontrar el índice del primero seleccionado
        all_items = tree.get_children()
        if not all_items:
            return
        
        # Encontrar el índice del primer item seleccionado
        first_selected_idx = 0
        for i, item in enumerate(all_items):
            if item in selection:
                first_selected_idx = i
                break
        
        # Eliminar los items seleccionados
        for item in selection:
            tree.delete(item)
        
        # Renumerar
        self._renumber_fav_tree(tree)
        self._sync(tab_id)
        self._mark_unsaved()
        
        # Seleccionar el siguiente item (o el anterior si era el último)
        remaining_items = tree.get_children()
        if remaining_items:
            # Intentar seleccionar el item en la misma posición
            if first_selected_idx < len(remaining_items):
                next_item = remaining_items[first_selected_idx]
            else:
                # Si era el último, seleccionar el nuevo último
                next_item = remaining_items[-1]
            tree.selection_set(next_item)
            tree.focus(next_item)
            tree.see(next_item)

    def move_item(self, direction):
        tab_id = self._get_current_fav_id()
        if tab_id is None: return
        tree = self.fav_trees[tab_id]
        sel = tree.selection()
        if not sel: return
        for item in sorted(sel, reverse=(direction==1)):
            idx = tree.index(item)
            new_idx = idx + direction
            if 0 <= new_idx < len(tree.get_children()):
                tree.move(item, "", new_idx)
        self._renumber_fav_tree(tree)
        self._sync(tab_id)
        self._mark_unsaved()

    def rename_fav_group(self):
        tab_id = self._get_current_fav_id()
        if tab_id is None: return
        cur_idx = self.fav_notebook.index(self.fav_notebook.select())
        
        # Obtener el nombre completo actual (no el truncado)
        names = []
        if self.fav_names_obj_index != -1:
            names = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"].get("aucFavReName", [])
        old_full = names[tab_id] if tab_id < len(names) and names[tab_id].strip() else f"Lista {tab_id}"
        
        new = simpledialog.askstring("Renombrar", "Nuevo nombre:", initialvalue=old_full)
        if new and self.fav_names_obj_index != -1:
            # Guardar nombre completo en fav_list_info_in_box_object
            self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"]["aucFavReName"][tab_id] = new
            
            # Actualizar ucFavNameChangeMask para indicar que esta lista tiene nombre personalizado
            fav_info = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"]
            current_mask = fav_info.get("ucFavNameChangeMask", 0)
            new_mask = current_mask | (1 << tab_id)  # Setear el bit correspondiente
            fav_info["ucFavNameChangeMask"] = new_mask
            
            # IMPORTANTE: También actualizar en box_object (donde el deco lee los nombres)
            self._sync_fav_names_to_box_object()
            
            # Mostrar nombre truncado en la pestaña (máximo 7 caracteres)
            tab_name = new[:7] if len(new) > 7 else new
            # Añadir espacios para forzar ancho mínimo
            tab_name = tab_name.center(7)
            self.fav_notebook.tab(cur_idx, text=tab_name)
            self._mark_unsaved()

    def create_fav_list(self):
        """Crea una nueva lista de favoritos."""
        if not self.all_data_objects:
            messagebox.showwarning("Aviso", "Primero debes cargar un archivo SDX o CHL")
            return

        # Pedir nombre para la nueva lista
        name = simpledialog.askstring("Nueva Lista", "Nombre de la nueva lista:")
        if not name:
            return

        # Encontrar el siguiente índice disponible
        existing_indices = set(self.fav_lists_indices.keys())
        new_idx = 0
        while new_idx in existing_indices:
            new_idx += 1

        # Crear el objeto fav_list_object
        new_fav_obj = {
            f"fav_list_object_{new_idx}": {
                "sNoOfTVFavor": 0,
                "sNoOfRadioFavor": 0,
                "stProgNo": []
            }
        }
        self.all_data_objects.append(new_fav_obj)
        self.fav_lists_indices[new_idx] = len(self.all_data_objects) - 1

        # Actualizar nombres en fav_list_info_in_box_object
        if self.fav_names_obj_index != -1:
            fav_info = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"]
            names = fav_info.get("aucFavReName", [])
            # Extender la lista si es necesario
            while len(names) <= new_idx:
                names.append(f"Lista {len(names)}")
            names[new_idx] = name
            fav_info["aucFavReName"] = names
            # Actualizar mask
            current_mask = fav_info.get("ucFavNameChangeMask", 0)
            fav_info["ucFavNameChangeMask"] = current_mask | (1 << new_idx)
            self._sync_fav_names_to_box_object()

        # Crear la pestaña en el notebook
        frame = tk.Frame(self.fav_notebook)
        tab_name = name[:7] if len(name) > 7 else name
        tab_name = tab_name.center(7)
        self.fav_notebook.add(frame, text=tab_name)

        tree = self._create_fav_tree(frame, new_idx)
        tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb = ttk.Scrollbar(frame, command=tree.yview)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        tree.config(yscrollcommand=sb.set)
        self.fav_trees[new_idx] = tree

        # Seleccionar la nueva pestaña
        self.fav_notebook.select(frame)

        self._mark_unsaved()
        messagebox.showinfo("Lista creada", f"Lista '{name}' creada correctamente.")

    def delete_fav_list(self):
        """Elimina la lista de favoritos actualmente seleccionada."""
        tab_id = self._get_current_fav_id()
        if tab_id is None:
            messagebox.showwarning("Aviso", "No hay ninguna lista seleccionada")
            return

        # Obtener nombre de la lista
        fav_name = f"Lista {tab_id}"
        if self.fav_names_obj_index != -1:
            names = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"].get("aucFavReName", [])
            if tab_id < len(names) and names[tab_id].strip():
                fav_name = names[tab_id]

        # Confirmar eliminación
        if not messagebox.askyesno("Confirmar eliminación",
                                    f"¿Estás seguro de que quieres eliminar la lista '{fav_name}'?\n\n"
                                    "Se eliminarán todos los canales de esta lista."):
            return

        # Obtener índice de la pestaña actual
        cur_tab_idx = self.fav_notebook.index(self.fav_notebook.select())

        # Eliminar la pestaña del notebook
        self.fav_notebook.forget(cur_tab_idx)

        # Eliminar el tree de fav_trees
        if tab_id in self.fav_trees:
            del self.fav_trees[tab_id]

        # Eliminar el objeto fav_list_object de all_data_objects
        obj_idx = self.fav_lists_indices.get(tab_id)
        if obj_idx is not None:
            # Marcar para eliminar (ponemos None y luego limpiamos)
            self.all_data_objects[obj_idx] = None

        # Eliminar del índice
        if tab_id in self.fav_lists_indices:
            del self.fav_lists_indices[tab_id]

        # Limpiar objetos None de all_data_objects y reindexar
        self.all_data_objects = [obj for obj in self.all_data_objects if obj is not None]

        # Reindexar fav_lists_indices
        self.fav_lists_indices = {}
        for i, obj in enumerate(self.all_data_objects):
            if isinstance(obj, dict):
                key = list(obj.keys())[0]
                if "fav_list_object_" in key:
                    idx = int(key.split("_")[-1])
                    self.fav_lists_indices[idx] = i
                elif "fav_list_info_in_box_object" in key:
                    self.fav_names_obj_index = i

        # Limpiar nombre de la lista eliminada
        if self.fav_names_obj_index != -1:
            fav_info = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"]
            names = fav_info.get("aucFavReName", [])
            if tab_id < len(names):
                names[tab_id] = ""
            self._sync_fav_names_to_box_object()

        self._mark_unsaved()
        messagebox.showinfo("Lista eliminada", f"Lista '{fav_name}' eliminada correctamente.")

    def _sync_fav_names_to_box_object(self):
        """Sincroniza los nombres de favoritos de fav_list_info_in_box_object a box_object."""
        if self.fav_names_obj_index == -1:
            return
        
        # Obtener nombres y mask de fav_list_info_in_box_object
        fav_info = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"]
        names = fav_info.get("aucFavReName", [])
        mask = fav_info.get("ucFavNameChangeMask", 0)
        
        # Buscar y actualizar box_object
        for obj in self.all_data_objects:
            if not isinstance(obj, dict):
                continue
            if "box_object" in obj:
                box = obj["box_object"]
                if "aucFavReName" in box:
                    box["aucFavReName"] = names.copy()
                    box["ucFavNameChangeMask"] = mask
                break

    def _sync(self, tab_id):
        tree = self.fav_trees[tab_id]
        new_data = []
        for item in tree.get_children():
            tags = tree.item(item, "tags")
            if tags:
                fav_entry = json.loads(tags[0])
                new_data.append(fav_entry)
        obj_idx = self.fav_lists_indices[tab_id]
        fav_key = f"fav_list_object_{tab_id}"
        self.all_data_objects[obj_idx][fav_key]["stProgNo"] = new_data
        self.all_data_objects[obj_idx][fav_key]["sNoOfTVFavor"] = len(new_data)
        
        # Actualizar FavBit de todos los programas
        self._update_all_favbits()
    
    def _update_all_favbits(self):
        """Recalcula el FavBit de cada programa basándose en las listas de favoritos."""
        # Primero, limpiar todos los FavBit
        for obj in self.all_data_objects:
            if not isinstance(obj, dict):
                continue
            key = list(obj.keys())[0]
            if "program_tv_object" in key:
                obj[key]["FavBit"] = 0
        
        # Luego, recorrer todas las listas de favoritos y setear los bits correspondientes
        for fav_idx, obj_idx in self.fav_lists_indices.items():
            fav_key = f"fav_list_object_{fav_idx}"
            fav_obj = self.all_data_objects[obj_idx].get(fav_key, {})
            fav_channels = fav_obj.get("stProgNo", [])
            
            bit_mask = 1 << fav_idx  # bit 0 para lista 0, bit 1 para lista 1, etc.
            
            for fav_entry in fav_channels:
                un_short = fav_entry.get("unShort", {})
                s_lo16 = un_short.get("sLo16", 0)
                s_hi16 = un_short.get("sHi16", 0)
                lookup_key = f"{s_lo16}_{s_hi16}"
                
                # Buscar el programa en programs_dict para obtener su obj_index
                if lookup_key in self.programs_dict:
                    prog_obj_idx = self.programs_dict[lookup_key].get('obj_index')
                    if prog_obj_idx is not None:
                        prog_obj = self.all_data_objects[prog_obj_idx]
                        prog_key = list(prog_obj.keys())[0]
                        if "program_tv_object" in prog_key:
                            current_favbit = prog_obj[prog_key].get("FavBit", 0)
                            prog_obj[prog_key]["FavBit"] = current_favbit | bit_mask

    def _get_current_fav_id(self):
        try:
            sel = self.fav_notebook.select()
            if not sel: return None
            return sorted(self.fav_lists_indices.keys())[self.fav_notebook.index(sel)]
        except: return None

    def save_file(self):
        path = filedialog.asksaveasfilename(defaultextension=".sdx", initialfile="LISTA_CANALES_MOD.sdx")
        if not path: return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                for obj in self.all_data_objects:
                    f.write(json.dumps(obj, separators=(',', ':')))
            self.unsaved_changes = False
            # Quitar el asterisco del título
            title = self.root.title()
            if title.endswith(" *"):
                self.root.title(title[:-2])
            messagebox.showinfo("Guardado", "Cambios guardados con éxito.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

    def save_as_chl(self):
        """Guarda los datos en formato CHL."""
        if not self.all_data_objects:
            messagebox.showwarning("Aviso", "No hay datos para guardar.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".chl",
            initialfile="LISTA_CANALES.chl",
            filetypes=[("CHL Files", "*.chl"), ("All Files", "*.*")]
        )
        if not path:
            return

        try:
            self.root.config(cursor=self.cursor_wait)
            self.root.update()

            chl_objects = self._convert_sdx_to_chl()

            with open(path, 'w', encoding='utf-8') as f:
                for obj in chl_objects:
                    f.write(json.dumps(obj, indent=2))
                    f.write('\n')

            self.unsaved_changes = False
            title = self.root.title()
            if title.endswith(" *"):
                self.root.title(title[:-2])
            messagebox.showinfo("Guardado", f"Archivo CHL guardado con éxito.\n{path}")

        except Exception as e:
            error_details = traceback.format_exc()
            messagebox.showerror("Error", f"No se pudo guardar en CHL:\n{e}\n\nDetalles:\n{error_details[:500]}")
        finally:
            self.root.config(cursor="")

    def _convert_sdx_to_chl(self):
        """Convierte los datos SDX a formato CHL."""
        chl_objects = []

        # Contar elementos
        satellites = []
        transponders = []
        channels = []
        favorites = []

        # Extraer datos de los objetos SDX
        for obj in self.all_data_objects:
            if not isinstance(obj, dict):
                continue
            key = list(obj.keys())[0]

            if "satellite_object_" in key:
                idx = int(key.split("_")[-1])
                data = obj[key]
                sat = {
                    "Type": "sat",
                    "Index": idx,
                    "Name": data.get("SatName", f"Sat {idx}"),
                    "Angle": str(data.get("SatAngle", 0)),
                    "Band": "KU"
                }
                satellites.append((idx, sat))

            elif "transponder_object_" in key:
                idx = int(key.split("_")[-1])
                data = obj[key]
                st_flag = data.get("stFlag", {})
                pol_map = {0: "H", 1: "V", 2: "L", 3: "R"}
                tp = {
                    "Type": "tp",
                    "Index": idx,
                    "SatIndex": st_flag.get("SatIndex", 0),
                    "Freq": str(data.get("Freq", 0)),
                    "SR": str(data.get("SR", 0)),
                    "Pol": pol_map.get(st_flag.get("POL", 0), "H"),
                    "FEC": "auto",
                    "plsNumber": 0,
                    "msTp": 0,
                    "msIsid": 0,
                    "tsnTp": 0,
                    "tsnId": 0
                }
                transponders.append((idx, tp))

            elif "program_tv_object" in key:
                idx = int(key.split("_")[-1])
                data = obj[key]
                st_prog_no = data.get("stProgNo", {})
                un_short = st_prog_no.get("unShort", {})
                ui_set = data.get("uiSet", {}).get("uiBit", {})

                # Video codec mapping
                video_codec = ui_set.get("VideoCodec", 1)
                video_type_map = {1: "MPEG2", 2: "H264", 3: "HEVC"}
                video_type = video_type_map.get(video_codec, "MPEG2")

                # Audio array
                audio_array = []
                for aud in data.get("AudioArray", []):
                    lang_code = aud.get("Lang", 0)
                    lang_map = {83: "spa", 69: "eng", 80: "por", 0: "und"}
                    lang_str = lang_map.get(lang_code, "und")

                    codec = aud.get("Codec", 0)
                    audio_type_map = {0: "MPEG", 1: "AAC", 2: "AC3"}
                    audio_type = audio_type_map.get(codec, "MPEG")

                    audio_array.append({
                        "PID": aud.get("PID", 0),
                        "Type": audio_type,
                        "Lang": lang_str,
                        "DolbyAC3": 1 if codec == 2 else 0
                    })

                ch = {
                    "dataPidSid": None,
                    "Type": "ch",
                    "TVType": "TV",
                    "Index": idx,
                    "TPIndex": un_short.get("sHi16", 0),
                    "SID": str(un_short.get("sLo16", 0)),
                    "Name": data.get("ServiceName", f"Canal {idx}"),
                    "VideoPID": data.get("VideoPID", 0),
                    "PcrPID": data.get("PCRPID", 0),
                    "PmtPID": data.get("PMTPID", 0),
                    "TTXPID": data.get("TTXPID", 8191),
                    "Provider": "",
                    "CA": 2 if ui_set.get("CA", 0) else 0,
                    "Lock": ui_set.get("Lock", 0),
                    "Skip": ui_set.get("Skip", 0),
                    "Hide": ui_set.get("Hide", 0),
                    "VideoType": video_type,
                    "t2miPg": data.get("t2mi_pg", 0),
                    "t2miPlpId": data.get("t2mi_plp_id", 0),
                    "t2miPayloadPid": data.get("t2mi_payload_pid", 8191),
                    "Audio": audio_array if audio_array else [{"PID": 0, "Type": "MPEG", "Lang": "und", "DolbyAC3": 0}],
                    "Sub": [],
                    "sattv": None,
                    "data_pid": None,
                    "PvtPID": None,
                    "CaSystemIdList": None
                }
                channels.append((idx, ch))

            elif "fav_list_object_" in key:
                idx = int(key.split("_")[-1])
                data = obj[key]
                # Get fav name
                fav_name = f"Lista {idx}"
                if self.fav_names_obj_index != -1:
                    names = self.all_data_objects[self.fav_names_obj_index].get("fav_list_info_in_box_object", {}).get("aucFavReName", [])
                    if idx < len(names) and names[idx].strip():
                        fav_name = names[idx]

                # Store stProgNo for later processing
                fav = {
                    "Type": "fav",
                    "Index": idx,
                    "Name": fav_name,
                    "TVChs": [],
                    "RadioChs": [],
                    "_stProgNo": data.get("stProgNo", [])  # Temporary, will be processed later
                }
                favorites.append((idx, fav))

        # Ordenar por índice
        satellites.sort(key=lambda x: x[0])
        transponders.sort(key=lambda x: x[0])
        channels.sort(key=lambda x: x[0])
        favorites.sort(key=lambda x: x[0])

        # Crear mapa de (SID, TPIndex) -> channel Index
        sid_tp_to_channel_idx = {}
        for ch_idx, ch in channels:
            sid = int(ch["SID"])
            tp_idx = ch["TPIndex"]
            key = (sid, tp_idx)
            if key not in sid_tp_to_channel_idx:
                sid_tp_to_channel_idx[key] = ch_idx

        # Procesar favoritos para añadir índices de canales
        for _, fav in favorites:
            st_prog_no = fav.pop("_stProgNo", [])
            for prog in st_prog_no:
                un_short = prog.get("unShort", {})
                sid = un_short.get("sLo16", 0)
                tp_idx = un_short.get("sHi16", 0)
                ch_idx = sid_tp_to_channel_idx.get((sid, tp_idx))
                if ch_idx is not None:
                    fav["TVChs"].append(ch_idx)

        # Crear objeto index
        index_obj = {
            "Type": "index",
            "Ver": 1,
            "Sat": len(satellites),
            "TP": len(transponders),
            "ChTV": len(channels),
            "CHRadio": 0,
            "FAV": len(favorites)
        }
        chl_objects.append(index_obj)

        # Añadir favoritos
        for _, fav in favorites:
            chl_objects.append(fav)

        # Añadir satélites
        for _, sat in satellites:
            chl_objects.append(sat)

        # Añadir transponders
        for _, tp in transponders:
            chl_objects.append(tp)

        # Añadir canales
        for _, ch in channels:
            chl_objects.append(ch)

        return chl_objects

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    if 'clam' in style.theme_names(): 
        style.theme_use('clam')
    
    # Configurar estilo de las pestañas
    style.configure('TNotebook.Tab', padding=[6, 4])
    
    app = SDXEditorApp(root)
    root.mainloop()
