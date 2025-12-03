import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from datetime import datetime

# Configuración de estilo visual
sns.set_theme(style="whitegrid")

class NatacionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SwimAnalytics PRO - Filtrado Avanzado")
        self.root.geometry("1300x850")
        
        # --- CONFIGURACIÓN PARA MAC (Modo Claro Forzado) ---
        self.root.configure(bg="white")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colores de interfaz
        self.bg_dark = "#2c3e50"
        self.bg_light = "#ecf0f1"
        self.accent = "#2980b9"
        
        # --- Variables de Datos ---
        self.df_original = None # Aquí guardamos TODO el archivo
        self.df_filtered = None # Aquí guardamos lo que se ve en pantalla
        
        # --- Variables de Filtros ---
        self.var_tipo = tk.StringVar(value="Solo Finales (N)")
        self.var_club = tk.StringVar(value="Todos")
        self.var_fecha_inicio = tk.StringVar()
        self.var_fecha_fin = tk.StringVar()

        # --- Interfaz Gráfica ---
        self.create_header()
        
        # Contenedor principal (divide filtros y gráficos)
        self.main_container = tk.Frame(self.root, bg="white")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.create_sidebar()
        self.create_dashboard()

    def create_header(self):
        header = tk.Frame(self.root, bg=self.bg_dark, height=70)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        lbl_title = tk.Label(header, text="🏊 SwimAnalytics PRO", 
                             font=("Helvetica", 20, "bold"), 
                             bg=self.bg_dark, fg="white")
        lbl_title.pack(side=tk.LEFT, padx=20)

        btn_load = tk.Button(header, text="📂 Cargar CSV", command=self.load_csv, 
                             bg="#27ae60", fg="white", 
                             font=("Arial", 11, "bold"), relief=tk.FLAT, padx=15)
        btn_load.pack(side=tk.RIGHT, padx=20, pady=15)

    def create_sidebar(self):
        # Panel lateral para filtros
        sidebar = tk.Frame(self.main_container, bg=self.bg_light, width=250, padx=15, pady=15)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Título Filtros
        tk.Label(sidebar, text="FILTROS", font=("Arial", 12, "bold"), 
                 bg=self.bg_light, fg="#7f8c8d").pack(anchor="w", pady=(0, 10))

        # 1. Filtro Tipo (Parcial vs Final)
        tk.Label(sidebar, text="Tipo de Tiempo:", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        self.combo_tipo = ttk.Combobox(sidebar, textvariable=self.var_tipo, state="readonly", 
                                       values=["Todos", "Solo Finales (N)", "Solo Parciales (S)"])
        self.combo_tipo.pack(fill=tk.X, pady=(0, 15))

        # 2. Filtro Club
        tk.Label(sidebar, text="Club:", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        self.combo_club = ttk.Combobox(sidebar, textvariable=self.var_club, state="readonly", values=["Todos"])
        self.combo_club.pack(fill=tk.X, pady=(0, 15))

        # 3. Filtro Fechas
        tk.Label(sidebar, text="Rango de Fechas (AAAA-MM-DD):", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        
        tk.Label(sidebar, text="Desde:", bg=self.bg_light, fg="#555").pack(anchor="w")
        entry_start = tk.Entry(sidebar, textvariable=self.var_fecha_inicio, bg="white", fg="black")
        entry_start.pack(fill=tk.X)
        
        tk.Label(sidebar, text="Hasta:", bg=self.bg_light, fg="#555").pack(anchor="w", pady=(5,0))
        entry_end = tk.Entry(sidebar, textvariable=self.var_fecha_fin, bg="white", fg="black")
        entry_end.pack(fill=tk.X, pady=(0, 15))

        # Botón Aplicar
        btn_apply = tk.Button(sidebar, text="Aplicar Filtros", command=self.apply_filters,
                              bg=self.accent, fg="white", font=("Arial", 11, "bold"), pady=5)
        btn_apply.pack(fill=tk.X, pady=20)
        
        # Información rápida
        self.lbl_info_count = tk.Label(sidebar, text="Registros: 0", bg=self.bg_light, fg="#7f8c8d")
        self.lbl_info_count.pack(side=tk.BOTTOM)

    def create_dashboard(self):
        # Área derecha (Gráficos y Stats)
        self.dashboard_frame = tk.Frame(self.main_container, bg="white")
        self.dashboard_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel de Estadísticas (Arriba)
        self.stats_frame = tk.Frame(self.dashboard_frame, bg="#f9f9f9", height=120, bd=1, relief=tk.SOLID)
        self.stats_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        self.stats_frame.pack_propagate(False)
        
        # Etiquetas de estadísticas (Placeholders)
        self.lbl_stat_25 = tk.Label(self.stats_frame, text="PB 25m: --", font=("Arial", 14), bg="#f9f9f9", fg="black")
        self.lbl_stat_25.pack(side=tk.LEFT, expand=True)
        
        self.lbl_stat_50 = tk.Label(self.stats_frame, text="PB 50m: --", font=("Arial", 14), bg="#f9f9f9", fg="black")
        self.lbl_stat_50.pack(side=tk.LEFT, expand=True)

        # Área de Gráficos (Abajo)
        self.plot_container = tk.Frame(self.dashboard_frame, bg="white")
        self.plot_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not file_path: return

        try:
            col_names = ['Licencia', 'Nombre', 'AnoNacimiento', 'Club', 'Prueba', 'Tiempo', 'InfoPiscina', 'Fecha', 'Lugar', 'CodigoExtra']
            df = pd.read_csv(file_path, header=None, names=col_names)

            # Preprocesamiento
            df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y%m%d', errors='coerce')
            df['Tiempo'] = pd.to_numeric(df['Tiempo'], errors='coerce')
            
            # Limpiar columna de códigos (quitar espacios)
            if 'CodigoExtra' in df.columns:
                df['CodigoExtra'] = df['CodigoExtra'].astype(str).str.strip()

            def clasificar_piscina(codigo):
                c = str(codigo).upper()
                if '25' in c: return '25m'
                if '50' in c: return '50m'
                return 'Otros'
            
            df['TipoPiscina'] = df['InfoPiscina'].apply(clasificar_piscina)
            df = df.sort_values('Fecha')

            # Guardar en variable ORIGINAL
            self.df_original = df
            
            # --- Actualizar Dropdown de Clubes ---
            clubes = sorted(df['Club'].unique().tolist())
            self.combo_club['values'] = ["Todos"] + clubes
            self.var_club.set("Todos") # Resetear selección
            
            # Resetear fechas
            self.var_fecha_inicio.set("")
            self.var_fecha_fin.set("")

            # Aplicar filtros iniciales
            self.apply_filters()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    def apply_filters(self):
        if self.df_original is None: return

        df = self.df_original.copy()

        # 1. Filtro Tipo (N vs S)
        tipo = self.var_tipo.get()
        if tipo == "Solo Finales (N)":
            df = df[df['CodigoExtra'] == 'N']
        elif tipo == "Solo Parciales (S)":
            df = df[df['CodigoExtra'] == 'S']
        # Si es "Todos", no filtramos nada aquí

        # 2. Filtro Club
        club = self.var_club.get()
        if club != "Todos":
            df = df[df['Club'] == club]

        # 3. Filtro Fechas
        f_inicio = self.var_fecha_inicio.get()
        f_fin = self.var_fecha_fin.get()

        try:
            if f_inicio:
                date_start = pd.to_datetime(f_inicio)
                df = df[df['Fecha'] >= date_start]
            if f_fin:
                date_end = pd.to_datetime(f_fin)
                df = df[df['Fecha'] <= date_end]
        except:
            messagebox.showwarning("Fechas Incorrectas", "Usa el formato AAAA-MM-DD (ej: 2023-01-01)")

        # Guardar resultado filtrado
        self.df_filtered = df
        
        # Actualizar UI
        self.lbl_info_count.config(text=f"Registros visibles: {len(df)}")
        self.update_stats()
        self.update_plots()

    def update_stats(self):
        if self.df_filtered is None or self.df_filtered.empty:
            self.lbl_stat_25.config(text="PB 25m: --")
            self.lbl_stat_50.config(text="PB 50m: --")
            return

        # Calcular mejores tiempos sobre la data FILTRADA
        df_25 = self.df_filtered[self.df_filtered['TipoPiscina'] == '25m']
        df_50 = self.df_filtered[self.df_filtered['TipoPiscina'] == '50m']

        pb_25 = f"{df_25['Tiempo'].min():.2f}s" if not df_25.empty else "--"
        pb_50 = f"{df_50['Tiempo'].min():.2f}s" if not df_50.empty else "--"

        # Nombre del nadador (tomado del primer registro disponible)
        nadador = self.df_filtered['Nombre'].iloc[0] if not self.df_filtered.empty else "Desconocido"

        self.lbl_stat_25.config(text=f"🏊 {nadador}\nPB 25m: {pb_25}")
        self.lbl_stat_50.config(text=f"\nPB 50m: {pb_50}")

    def update_plots(self):
        # Limpiar
        for widget in self.plot_container.winfo_children():
            widget.destroy()

        if self.df_filtered is None or self.df_filtered.empty:
            tk.Label(self.plot_container, text="No hay datos con estos filtros", bg="white", fg="red").pack(pady=50)
            return

        # Figura
        fig = plt.Figure(figsize=(8, 6), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)

        # Colores
        colors = {'25m': '#2980b9', '50m': '#e67e22', 'Otros': 'gray'}

        # Graficar líneas separadas por tipo de piscina
        for piscina in ['25m', '50m']:
            data = self.df_filtered[self.df_filtered['TipoPiscina'] == piscina]
            if not data.empty:
                ax.plot(data['Fecha'], data['Tiempo'], marker='o', linestyle='-', 
                        label=f'Piscina {piscina}', color=colors.get(piscina))
                
                # Opcional: Añadir etiquetas de texto a los mejores puntos
                min_idx = data['Tiempo'].idxmin()
                best_row = data.loc[min_idx]
                ax.annotate(f"{best_row['Tiempo']}", 
                            (best_row['Fecha'], best_row['Tiempo']),
                            textcoords="offset points", xytext=(0,10), ha='center',
                            fontsize=8, color=colors.get(piscina))

        ax.set_title("Evolución de Tiempos (Datos Filtrados)", fontsize=12, fontweight='bold', color='black')
        ax.set_ylabel("Tiempo (s)", color='black')
        ax.tick_params(colors='black')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_facecolor('#f9f9f9')

        # Insertar en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.plot_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = NatacionApp(root)
    root.mainloop()