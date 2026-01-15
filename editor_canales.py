#!/usr/bin/env python3
import json
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

class SDXEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Gestor de Canales SDX - v2.2")
        self.root.geometry("1500x800")

        self.all_data_objects = []
        self.programs_dict = {}
        self.program_list = []
        self.transponders = {}
        self.fav_lists_indices = {}
        self.fav_names_obj_index = -1
        self.fav_trees = {}
        
        # Variables para drag & drop
        self.drag_data = {"item": None, "tree": None}
        
        # Variable para edición inline
        self.edit_entry = None

        self._setup_ui()

    def _setup_ui(self):
        top_frame = tk.Frame(self.root, pady=10)
        top_frame.pack(fill=tk.X, padx=10)

        tk.Button(top_frame, text="1. Cargar Archivo .sdx", command=self.load_file, bg="#e1e1e1").pack(side=tk.LEFT, padx=5)
        tk.Button(top_frame, text="2. Guardar Cambios", command=self.save_file, bg="#8fbc8f", fg="black").pack(side=tk.LEFT, padx=5)

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

    def _setup_drag_and_drop(self, tree, tab_id):
        """Configura drag & drop y edición inline para un Treeview de favoritos."""
        # Drag & Drop
        tree.bind("<ButtonPress-1>", lambda e: self._on_drag_start(e, tree, tab_id))
        tree.bind("<B1-Motion>", lambda e: self._on_drag_motion(e, tree))
        tree.bind("<ButtonRelease-1>", lambda e: self._on_drag_release(e, tree, tab_id))
        
        # Doble clic para editar número
        tree.bind("<Double-1>", lambda e: self._on_double_click(e, tree, tab_id))

    def _on_drag_start(self, event, tree, tab_id):
        """Inicia el arrastre."""
        # Cerrar cualquier edición activa
        self._close_edit_entry()
        
        item = tree.identify_row(event.y)
        if item:
            self.drag_data["item"] = item
            self.drag_data["tree"] = tree
            self.drag_data["tab_id"] = tab_id
            tree.selection_set(item)

    def _on_drag_motion(self, event, tree):
        """Mueve el elemento durante el arrastre."""
        if not self.drag_data["item"]:
            return
            
        # Obtener el elemento sobre el que estamos
        target = tree.identify_row(event.y)
        if target and target != self.drag_data["item"]:
            # Determinar si mover arriba o abajo
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
        """Finaliza el arrastre y sincroniza."""
        if self.drag_data["item"]:
            self._renumber_fav_tree(tree)
            self._sync(tab_id)
        self.drag_data["item"] = None
        self.drag_data["tree"] = None

    def _on_double_click(self, event, tree, tab_id):
        """Maneja el doble clic para editar el número de orden."""
        # Identificar la columna y fila
        region = tree.identify("region", event.x, event.y)
        if region != "cell":
            return
            
        column = tree.identify_column(event.x)
        item = tree.identify_row(event.y)
        
        if not item:
            return
        
        # Solo permitir edición en la columna #1 (el número de orden)
        if column != "#1":
            return
        
        # Cerrar cualquier edición anterior
        self._close_edit_entry()
        
        # Obtener la posición de la celda
        bbox = tree.bbox(item, column)
        if not bbox:
            return
        
        x, y, width, height = bbox
        
        # Obtener el valor actual
        values = tree.item(item, "values")
        current_value = values[0] if values else ""
        
        # Crear Entry para edición
        self.edit_entry = tk.Entry(tree, width=5, justify="center")
        self.edit_entry.place(x=x, y=y, width=width, height=height)
        self.edit_entry.insert(0, current_value)
        self.edit_entry.select_range(0, tk.END)
        self.edit_entry.focus()
        
        # Guardar referencia al item y tree
        self.edit_entry.item = item
        self.edit_entry.tree = tree
        self.edit_entry.tab_id = tab_id
        
        # Bindings para confirmar o cancelar
        self.edit_entry.bind("<Return>", self._confirm_edit)
        self.edit_entry.bind("<Escape>", lambda e: self._close_edit_entry())
        self.edit_entry.bind("<FocusOut>", self._confirm_edit)

    def _confirm_edit(self, event=None):
        """Confirma la edición del número de orden."""
        if not self.edit_entry:
            return
        
        try:
            new_pos = int(self.edit_entry.get())
            tree = self.edit_entry.tree
            item = self.edit_entry.item
            tab_id = self.edit_entry.tab_id
            
            total_items = len(tree.get_children())
            
            # Validar rango
            if new_pos < 1:
                new_pos = 1
            elif new_pos > total_items:
                new_pos = total_items
            
            # Mover el elemento a la nueva posición
            tree.move(item, "", new_pos - 1)
            
            # Renumerar y sincronizar
            self._renumber_fav_tree(tree)
            self._sync(tab_id)
            
        except ValueError:
            pass  # Si no es un número válido, ignorar
        
        self._close_edit_entry()

    def _close_edit_entry(self):
        """Cierra el Entry de edición."""
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
            messagebox.showinfo("Éxito", f"Carga completada: {len(self.program_list)} canales encontrados.")
        except Exception as e:
            messagebox.showerror("Error", f"Error al leer: {e}")

    def _get_service_type(self, sdt_type):
        """Convierte el tipo de servicio SDT a texto legible."""
        types = {
            1: "TV SD",
            2: "Radio",
            17: "TV SD",
            22: "TV SD",
            25: "TV HD",
            31: "TV UHD"
        }
        return types.get(sdt_type, f"Tipo {sdt_type}")

    def _process_data(self):
        """Indexa transponders y canales con toda su información."""
        self.programs_dict = {}
        self.program_list = []
        self.transponders = {}
        self.fav_lists_indices = {}
        
        # Primero indexar transponders
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
        
        # Luego procesar canales
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
                    info['order'],
                    info['name'],
                    info['freq'],
                    info['sid'],
                    info['lcn'],
                    info['hd'],
                    info['ca'],
                    info['tipo'],
                    info['calidad']
                ))

    def _create_fav_tree(self, parent, tab_id):
        """Crea un Treeview para favoritos con columnas y drag & drop."""
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
        
        # Configurar drag & drop y edición inline
        self._setup_drag_and_drop(tree, tab_id)
        
        return tree

    def _build_fav_tabs(self):
        """Construye las pestañas de favoritos con columnas."""
        for tab in self.fav_notebook.tabs(): 
            self.fav_notebook.forget(tab)
        self.fav_trees = {}
        
        names = []
        if self.fav_names_obj_index != -1:
            names = self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"].get("aucFavReName", [])

        for f_idx in sorted(self.fav_lists_indices.keys()):
            title = names[f_idx] if f_idx < len(names) and names[f_idx].strip() else f"Lista {f_idx}"
            frame = tk.Frame(self.fav_notebook)
            self.fav_notebook.add(frame, text=title)
            
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
                        fav_order,
                        channel_info['name'],
                        channel_info['freq'],
                        channel_info['sid'],
                        channel_info['lcn'],
                        channel_info['hd'],
                        channel_info['ca'],
                        channel_info['tipo']
                    ))
                else:
                    fav_json = json.dumps(fav_entry, sort_keys=True, separators=(',', ':'))
                    tree.insert("", "end", tags=(fav_json,), values=(
                        fav_order,
                        f"Desconocido ({s_lo16}_{s_hi16})",
                        "", s_lo16, "", "", "", ""
                    ))

    def _renumber_fav_tree(self, tree):
        """Renumera los elementos del árbol de favoritos."""
        for idx, item in enumerate(tree.get_children(), 1):
            values = list(tree.item(item, "values"))
            values[0] = idx
            tree.item(item, values=values)

    def add_to_fav(self):
        tab_id = self._get_current_fav_id()
        if tab_id is None: return
        sel = self.tree_all.selection()
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

    def remove_from_fav(self):
        tab_id = self._get_current_fav_id()
        if tab_id is None: return
        tree = self.fav_trees[tab_id]
        for item in tree.selection(): 
            tree.delete(item)
        self._renumber_fav_tree(tree)
        self._sync(tab_id)

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

    def rename_fav_group(self):
        tab_id = self._get_current_fav_id()
        if tab_id is None: return
        cur_idx = self.fav_notebook.index(self.fav_notebook.select())
        old = self.fav_notebook.tab(cur_idx, "text")
        new = simpledialog.askstring("Renombrar", "Nuevo nombre:", initialvalue=old)
        if new and self.fav_names_obj_index != -1:
            self.fav_notebook.tab(cur_idx, text=new)
            self.all_data_objects[self.fav_names_obj_index]["fav_list_info_in_box_object"]["aucFavReName"][tab_id] = new

    def _sync(self, tab_id):
        """Sincroniza el Treeview con los datos internos."""
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
            messagebox.showinfo("Guardado", "Cambios guardados con éxito.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    style = ttk.Style()
    if 'clam' in style.theme_names(): 
        style.theme_use('clam')
    app = SDXEditorApp(root)
    root.mainloop()
