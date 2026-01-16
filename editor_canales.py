#!/usr/bin/env python3
import json
import re
import traceback
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk
from urllib.request import urlopen, Request
from urllib.error import URLError


class SDXEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Canales SDX - v2.4")
        self.root.geometry("1500x800")

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

        tk.Button(top_frame, text="1. Cargar Archivo .sdx", command=self.load_file, bg="#e1e1e1").pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="2. Guardar Cambios", command=self.save_file, bg="#8fbc8f", fg="black").pack(side=tk.LEFT, padx=5)
        
        # Separador
        ttk.Separator(top_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        # Botón de importar desde KingOfSat
        tk.Button(top_frame, text="📡 Importar desde KingOfSat", command=self.import_from_kingofsat, 
                  bg="#fff3cd", fg="black").pack(side=tk.LEFT, padx=5)

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
        tk.Button(btn_f, text="Renombrar", command=self.rename_fav_group).pack(side=tk.RIGHT, padx=5)

    def import_from_kingofsat(self):
        """Importa canales desde una URL de KingOfSat."""
        if not self.program_list:
            messagebox.showwarning("Aviso", "Primero debes cargar un archivo .sdx")
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
            self.root.config(cursor="wait")
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
            
            # Hacer matching con canales locales
            matched, not_matched = self._match_channels(kos_channels)
            
            if not matched:
                messagebox.showwarning("Aviso", 
                    f"No se encontró ninguna coincidencia entre los {len(kos_channels)} canales de KingOfSat "
                    f"y tu archivo SDX.\n\n{len(not_matched)} canales no encontrados.")
                return
            
            # Preguntar en qué lista añadir
            self._show_import_dialog(matched, not_matched, url)
            
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
        
        # El HTML real tiene tags <table>, <tr>, <td>
        # Buscar frecuencias en filas de transponder
        # Patrón: frecuencia tipo 10758.50 dentro de una celda
        freq_pattern = re.compile(r'>(\d{4,5})[.,]\d{2}<')
        
        # Buscar todas las filas de la tabla
        # Patrón para filas de canal: tienen un SID de 5 dígitos
        row_pattern = re.compile(r'<tr[^>]*>(.*?)</tr>', re.DOTALL | re.IGNORECASE)
        cell_pattern = re.compile(r'<td[^>]*>(.*?)</td>', re.DOTALL | re.IGNORECASE)
        
        for row_match in row_pattern.finditer(html_content):
            row_content = row_match.group(1)
            
            # Extraer todas las celdas de la fila
            cells = cell_pattern.findall(row_content)
            
            if not cells:
                continue
            
            # Buscar si es una fila de transponder (contiene frecuencia)
            row_text = ' '.join(cells)
            freq_match = freq_pattern.search(row_text)
            if freq_match and ('DVB-S' in row_text or 'QPSK' in row_text or '8PSK' in row_text):
                current_freq = int(freq_match.group(1))
                continue
            
            # Buscar SID de 5 dígitos en las celdas
            sid = None
            sid_index = -1
            for i, cell in enumerate(cells):
                cell_clean = re.sub(r'<[^>]+>', '', cell).strip()
                if re.match(r'^\d{5}$', cell_clean):
                    sid = int(cell_clean)
                    sid_index = i
                    break
            
            if not sid or sid_index < 3:
                continue
            
            # El nombre está en las primeras celdas (generalmente posición 2 o 3)
            name = None
            skip_words = [
                'spain', 'france', 'germany', 'united kingdom', 'italy', 'portugal',
                'sport', 'movies', 'news', 'general', 'various', 'music', 'children',
                'entertainment', 'documentaries', 'series', 'regional', 'lifestyle',
                'comedy', 'cooking', 'history', 'erotic', 'pay per view',
                'nagravision', 'mediaguard', 'clear', 'conax', 'viaccess',
                'movistar+', 'movistar', 'name', 'country', 'category', 'packages',
                'encryption', 'sid', 'vpid', 'audio', 'pmt', 'pcr', 'txt', 'update',
                'undefined', ''
            ]
            
            for i in range(min(sid_index, 5)):
                cell = cells[i]
                # Limpiar HTML
                cell_clean = re.sub(r'<[^>]+>', ' ', cell)
                cell_clean = re.sub(r'\s+', ' ', cell_clean).strip()
                
                # Extraer texto del enlace si existe
                link_match = re.search(r'>([^<]+)<', cell)
                if link_match:
                    cell_clean = link_match.group(1).strip()
                
                # Verificar si es un nombre válido
                if not cell_clean:
                    continue
                    
                cell_lower = cell_clean.lower()
                if cell_lower in skip_words:
                    continue
                if cell_clean.isdigit():
                    continue
                if len(cell_clean) < 2:
                    continue
                
                # Parece un nombre de canal
                name = cell_clean
                break
            
            if name and sid:
                channels.append({
                    'name': name,
                    'sid': sid,
                    'freq': current_freq
                })
        
        # Si no encontramos nada con el método HTML, intentar con el texto plano
        if not channels:
            channels = self._parse_kingofsat_text(html_content)
        
        # Eliminar duplicados
        seen = set()
        unique = []
        for ch in channels:
            key = (ch['name'], ch['sid'])
            if key not in seen:
                seen.add(key)
                unique.append(ch)
        
        return unique

    def _parse_kingofsat_text(self, content):
        """Parser alternativo que busca patrones en el texto."""
        channels = []
        current_freq = 0
        
        # Limpiar HTML tags para obtener texto
        text = re.sub(r'<[^>]+>', '|', content)
        text = re.sub(r'\|+', '|', text)
        
        lines = text.split('\n')
        
        for line in lines:
            # Buscar frecuencia
            freq_match = re.search(r'(\d{4,5})[.,]\d{2}\s*\|?\s*[VH]', line)
            if freq_match:
                current_freq = int(freq_match.group(1))
                continue
            
            # Buscar SID
            sid_match = re.search(r'\|\s*(\d{5})\s*\|', line)
            if not sid_match:
                continue
            
            sid = int(sid_match.group(1))
            
            # Buscar nombre (texto antes del SID que no sea categoría/país)
            parts = line.split('|')
            skip_words = ['spain', 'france', 'germany', 'sport', 'movies', 'news', 
                         'general', 'various', 'music', 'nagravision', 'mediaguard',
                         'clear', 'movistar', '']
            
            name = None
            for part in parts:
                part = part.strip()
                if not part or part.lower() in skip_words:
                    continue
                if part.isdigit() or re.match(r'^\d{5}$', part):
                    continue
                if len(part) >= 2 and len(part) <= 60:
                    name = part
                    break
            
            if name and sid:
                channels.append({
                    'name': name,
                    'sid': sid,
                    'freq': current_freq
                })
        
        return channels

    def _parse_kingofsat_alternative(self, html_content):
        """Método alternativo - no usado."""
        return []

    def _match_channels(self, kos_channels):
        """Busca coincidencias entre canales de KingOfSat y el archivo SDX."""
        matched = []
        not_matched = []
        
        # Crear índice por SID para búsqueda rápida
        sid_index = {}
        for unique_key, name in self.program_list:
            info = self.programs_dict[unique_key]
            sid = info['sid']
            if sid not in sid_index:
                sid_index[sid] = []
            sid_index[sid].append((unique_key, info))
        
        # Crear índice por nombre normalizado
        name_index = {}
        for unique_key, name in self.program_list:
            info = self.programs_dict[unique_key]
            norm_name = self._normalize_name(name)
            if norm_name not in name_index:
                name_index[norm_name] = []
            name_index[norm_name].append((unique_key, info))
        
        for kos_ch in kos_channels:
            found = False
            
            # Intento 1: Match por SID exacto
            if kos_ch['sid'] in sid_index:
                candidates = sid_index[kos_ch['sid']]
                # Si hay múltiples, preferir el que coincida en frecuencia
                if len(candidates) == 1:
                    matched.append({
                        'kos': kos_ch,
                        'local': candidates[0][1],
                        'unique_key': candidates[0][0],
                        'match_type': 'SID'
                    })
                    found = True
                else:
                    # Buscar por frecuencia también
                    for unique_key, info in candidates:
                        if kos_ch['freq'] and abs(info['freq'] - kos_ch['freq']) < 5:
                            matched.append({
                                'kos': kos_ch,
                                'local': info,
                                'unique_key': unique_key,
                                'match_type': 'SID+Freq'
                            })
                            found = True
                            break
                    if not found and candidates:
                        # Usar el primero si no hay match por frecuencia
                        matched.append({
                            'kos': kos_ch,
                            'local': candidates[0][1],
                            'unique_key': candidates[0][0],
                            'match_type': 'SID'
                        })
                        found = True
            
            # Intento 2: Match por nombre normalizado
            if not found:
                norm_name = self._normalize_name(kos_ch['name'])
                if norm_name in name_index:
                    candidates = name_index[norm_name]
                    matched.append({
                        'kos': kos_ch,
                        'local': candidates[0][1],
                        'unique_key': candidates[0][0],
                        'match_type': 'Nombre'
                    })
                    found = True
            
            # Intento 3: Match parcial por nombre
            if not found:
                for norm_name, candidates in name_index.items():
                    kos_norm = self._normalize_name(kos_ch['name'])
                    if kos_norm in norm_name or norm_name in kos_norm:
                        matched.append({
                            'kos': kos_ch,
                            'local': candidates[0][1],
                            'unique_key': candidates[0][0],
                            'match_type': 'Parcial'
                        })
                        found = True
                        break
            
            if not found:
                not_matched.append(kos_ch)
        
        return matched, not_matched

    def _normalize_name(self, name):
        """Normaliza un nombre de canal para comparación."""
        # Convertir a minúsculas
        name = name.lower()
        # Eliminar caracteres especiales
        name = re.sub(r'[^a-z0-9]', '', name)
        # Eliminar sufijos comunes
        name = re.sub(r'(hd|sd|fhd|uhd|4k|spain|españa|esp)$', '', name)
        return name

    def _show_import_dialog(self, matched, not_matched, url):
        """Muestra diálogo con resultados y opciones de importación."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Resultados de importación")
        dialog.geometry("700x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame de información
        info_frame = tk.Frame(dialog, pady=10)
        info_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(info_frame, text=f"URL: {url}", anchor="w", fg="blue").pack(fill=tk.X)
        tk.Label(info_frame, text=f"✅ Canales encontrados: {len(matched)}", anchor="w", fg="green").pack(fill=tk.X)
        tk.Label(info_frame, text=f"❌ No encontrados: {len(not_matched)}", anchor="w", fg="red").pack(fill=tk.X)
        
        # Notebook con pestañas
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Pestaña de canales encontrados
        found_frame = tk.Frame(notebook)
        notebook.add(found_frame, text=f"Encontrados ({len(matched)})")
        
        columns = ("kos_name", "local_name", "sid", "freq", "match")
        tree_found = ttk.Treeview(found_frame, columns=columns, show="headings", height=15)
        tree_found.heading("kos_name", text="Nombre KingOfSat")
        tree_found.heading("local_name", text="Nombre Local")
        tree_found.heading("sid", text="SID")
        tree_found.heading("freq", text="Freq")
        tree_found.heading("match", text="Tipo Match")
        
        tree_found.column("kos_name", width=180)
        tree_found.column("local_name", width=180)
        tree_found.column("sid", width=60)
        tree_found.column("freq", width=60)
        tree_found.column("match", width=80)
        
        for m in matched:
            tree_found.insert("", "end", values=(
                m['kos']['name'],
                m['local']['name'],
                m['kos']['sid'],
                m['local']['freq'],
                m['match_type']
            ))
        
        tree_found.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_found = ttk.Scrollbar(found_frame, command=tree_found.yview)
        sb_found.pack(side=tk.RIGHT, fill=tk.Y)
        tree_found.config(yscrollcommand=sb_found.set)
        
        # Pestaña de no encontrados
        notfound_frame = tk.Frame(notebook)
        notebook.add(notfound_frame, text=f"No encontrados ({len(not_matched)})")
        
        columns_nf = ("name", "sid", "freq")
        tree_notfound = ttk.Treeview(notfound_frame, columns=columns_nf, show="headings", height=15)
        tree_notfound.heading("name", text="Nombre")
        tree_notfound.heading("sid", text="SID")
        tree_notfound.heading("freq", text="Freq")
        
        for ch in not_matched:
            tree_notfound.insert("", "end", values=(ch['name'], ch['sid'], ch['freq']))
        
        tree_notfound.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb_nf = ttk.Scrollbar(notfound_frame, command=tree_notfound.yview)
        sb_nf.pack(side=tk.RIGHT, fill=tk.Y)
        tree_notfound.config(yscrollcommand=sb_nf.set)
        
        # Frame de acciones
        action_frame = tk.Frame(dialog, pady=10)
        action_frame.pack(fill=tk.X, padx=10)
        
        tk.Label(action_frame, text="Añadir a lista de favoritos:").pack(side=tk.LEFT)
        
        # Combo con listas de favoritos
        fav_names = []
        if self.fav_names_obj_index != -1:
            fav_names = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"].get("aucFavReName", [])
        
        fav_options = []
        for f_idx in sorted(self.fav_lists_indices.keys()):
            name = fav_names[f_idx] if f_idx < len(fav_names) and fav_names[f_idx].strip() else f"Lista {f_idx}"
            fav_options.append((f_idx, name))
        
        combo_var = tk.StringVar()
        combo = ttk.Combobox(action_frame, textvariable=combo_var, state="readonly", width=20)
        combo['values'] = [f"{idx}: {name}" for idx, name in fav_options]
        if combo['values']:
            combo.current(0)
        combo.pack(side=tk.LEFT, padx=10)
        
        def do_import():
            if not combo_var.get():
                return
            tab_id = int(combo_var.get().split(":")[0])
            self._add_matched_to_favorites(matched, tab_id)
            dialog.destroy()
            messagebox.showinfo("Importación completada", 
                               f"Se añadieron {len(matched)} canales a la lista de favoritos.")
        
        tk.Button(action_frame, text="Importar canales encontrados", command=do_import, 
                  bg="#90EE90", fg="black", activebackground="#32CD32").pack(side=tk.LEFT, padx=10)
        tk.Button(action_frame, text="Cancelar", command=dialog.destroy).pack(side=tk.RIGHT)

    def _add_matched_to_favorites(self, matched, tab_id):
        """Añade los canales coincidentes a una lista de favoritos."""
        tree = self.fav_trees[tab_id]
        current_count = len(tree.get_children())
        
        for m in matched:
            unique_key = m['unique_key']
            channel_info = self.programs_dict.get(unique_key)
            
            if channel_info:
                current_count += 1
                st_prog_no = channel_info['stProgNo']
                un_short = st_prog_no.get("unShort", {})
                s_lo16 = un_short.get("sLo16", 0)
                s_hi16 = un_short.get("sHi16", 0)
                
                ui_word32 = (s_hi16 << 16) | s_lo16
                
                fav_entry = {
                    "uiWord32": ui_word32,
                    "unShort": {
                        "sLo16": s_lo16,
                        "sHi16": s_hi16
                    }
                }
                
                fav_json = json.dumps(fav_entry, sort_keys=True, separators=(',', ':'))
                tree.insert("", "end", tags=(fav_json,), values=(
                    current_count,
                    channel_info['name'],
                    channel_info['freq'],
                    channel_info['sid'],
                    channel_info['lcn'],
                    channel_info['hd'],
                    channel_info['ca'],
                    channel_info['tipo']
                ))
        
        self._sync(tab_id)
        self._mark_unsaved()

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
            self.root.title("Gestor de Canales SDX - v2.4")
            
            messagebox.showinfo("Éxito", f"Carga completada: {len(self.program_list)} canales encontrados.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer: {e}")

    def _get_service_type(self, sdt_type):
        types = {1: "TV SD", 2: "Radio", 17: "TV SD", 22: "TV SD", 25: "TV HD", 31: "TV UHD"}
        return types.get(sdt_type, f"Tipo {sdt_type}")

    def _process_data(self):
        self.programs_dict = {}
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
                unique_key = f"{s_lo16}_{s_hi16}"
                
                self.programs_dict[unique_key] = {
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
                channel_info = self.programs_dict.get(lookup_key)
                
                if channel_info:
                    fav_json = json.dumps(fav_entry, sort_keys=True, separators=(',', ':'))
                    tree.insert("", "end", tags=(fav_json,), values=(
                        fav_order, channel_info['name'], channel_info['freq'],
                        channel_info['sid'], channel_info['lcn'], channel_info['hd'],
                        channel_info['ca'], channel_info['tipo']
                    ))
                else:
                    fav_json = json.dumps(fav_entry, sort_keys=True, separators=(',', ':'))
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
                fav_json = json.dumps(fav_entry, sort_keys=True, separators=(',', ':'))
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
            # Guardar nombre completo en los datos
            self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"]["aucFavReName"][tab_id] = new
            # Mostrar nombre truncado en la pestaña (máximo 7 caracteres)
            tab_name = new[:7] if len(new) > 7 else new
            # Añadir espacios para forzar ancho mínimo
            tab_name = tab_name.center(7)
            self.fav_notebook.tab(cur_idx, text=tab_name)
            self._mark_unsaved()

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

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    if 'clam' in style.theme_names(): 
        style.theme_use('clam')
    
    # Configurar estilo de las pestañas
    style.configure('TNotebook.Tab', padding=[6, 4])
    
    app = SDXEditorApp(root)
    root.mainloop()
