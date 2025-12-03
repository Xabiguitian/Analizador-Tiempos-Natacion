import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.ticker import FuncFormatter
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime

# Configuración de estilo visual
sns.set_theme(style="whitegrid")

class NatacionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SwimAnalytics PRO - Edición Mac")
        self.root.geometry("1300x850")
        
        # --- CONFIGURACIÓN PARA MAC ---
        self.root.configure(bg="white")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Colores
        self.bg_dark = "#2c3e50"
        self.bg_light = "#ecf0f1"
        self.accent = "#2980b9"
        
        # --- Variables ---
        self.df_original = None 
        self.df_filtered = None
        
        self.var_tipo = tk.StringVar(value="Solo Finales (N)")
        self.var_club = tk.StringVar(value="Todos")
        self.var_fecha_inicio = tk.StringVar()
        self.var_fecha_fin = tk.StringVar()

        # --- Interfaz ---
        self.create_header()
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

        # CAMBIO: Texto negro (fg="black") para mejorar legibilidad
        btn_load = tk.Button(header, text="📂 Cargar CSV", command=self.load_csv, 
                             bg="#27ae60", fg="black", 
                             font=("Arial", 11, "bold"), relief=tk.FLAT, padx=15)
        btn_load.pack(side=tk.RIGHT, padx=20, pady=15)

    def create_sidebar(self):
        sidebar = tk.Frame(self.main_container, bg=self.bg_light, width=250, padx=15, pady=15)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="FILTROS", font=("Arial", 12, "bold"), 
                 bg=self.bg_light, fg="#7f8c8d").pack(anchor="w", pady=(0, 10))

        # 1. Filtro Tipo
        tk.Label(sidebar, text="Tipo de Tiempo:", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        self.combo_tipo = ttk.Combobox(sidebar, textvariable=self.var_tipo, state="readonly", 
                                       values=["Todos", "Solo Finales (N)", "Solo Parciales (S)"])
        self.combo_tipo.pack(fill=tk.X, pady=(0, 15))

        # 2. Filtro Club
        tk.Label(sidebar, text="Club:", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        self.combo_club = ttk.Combobox(sidebar, textvariable=self.var_club, state="readonly", values=["Todos"])
        self.combo_club.pack(fill=tk.X, pady=(0, 15))

        # 3. Filtro Fechas (CAMBIO: Formato DD/MM/AAAA)
        tk.Label(sidebar, text="Rango de Fechas (DD/MM/AAAA):", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        
        tk.Label(sidebar, text="Desde:", bg=self.bg_light, fg="#555").pack(anchor="w")
        entry_start = tk.Entry(sidebar, textvariable=self.var_fecha_inicio, bg="white", fg="black")
        entry_start.pack(fill=tk.X)
        
        tk.Label(sidebar, text="Hasta:", bg=self.bg_light, fg="#555").pack(anchor="w", pady=(5,0))
        entry_end = tk.Entry(sidebar, textvariable=self.var_fecha_fin, bg="white", fg="black")
        entry_end.pack(fill=tk.X, pady=(0, 15))

        # CAMBIO: Texto negro en botón aplicar
        btn_apply = tk.Button(sidebar, text="Aplicar Filtros", command=self.apply_filters,
                              bg=self.accent, fg="black", font=("Arial", 11, "bold"), pady=5)
        btn_apply.pack(fill=tk.X, pady=20)
        
        self.lbl_info_count = tk.Label(sidebar, text="Registros: 0", bg=self.bg_light, fg="#7f8c8d")
        self.lbl_info_count.pack(side=tk.BOTTOM)

    def create_dashboard(self):
        self.dashboard_frame = tk.Frame(self.main_container, bg="white")
        self.dashboard_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.stats_frame = tk.Frame(self.dashboard_frame, bg="#f9f9f9", height=120, bd=1, relief=tk.SOLID)
        self.stats_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        self.stats_frame.pack_propagate(False)
        
        self.lbl_stat_25 = tk.Label(self.stats_frame, text="PB 25m: --", font=("Arial", 14), bg="#f9f9f9", fg="black")
        self.lbl_stat_25.pack(side=tk.LEFT, expand=True)
        
        self.lbl_stat_50 = tk.Label(self.stats_frame, text="PB 50m: --", font=("Arial", 14), bg="#f9f9f9", fg="black")
        self.lbl_stat_50.pack(side=tk.LEFT, expand=True)

        self.plot_container = tk.Frame(self.dashboard_frame, bg="white")
        self.plot_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # --- UTILIDADES DE TIEMPO ---
    def convert_time_to_seconds(self, time_str):
        try:
            time_str = str(time_str).strip()
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except:
            return None 

    def format_seconds_to_time(self, seconds):
        if pd.isna(seconds): return "--"
        m = int(seconds // 60)
        s = seconds % 60
        if m > 0:
            return f"{m}:{s:05.2f}"
        else:
            return f"{s:.2f}"

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
        if not file_path: return

        try:
            col_names = ['Licencia', 'Nombre', 'AnoNacimiento', 'Club', 'Prueba', 'Tiempo', 'InfoPiscina', 'Fecha', 'Lugar', 'CodigoExtra']
            df = pd.read_csv(file_path, header=None, names=col_names)

            # Limpieza de Fecha
            df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y%m%d', errors='coerce')
            
            # Limpieza de Tiempo
            df['Tiempo'] = df['Tiempo'].apply(self.convert_time_to_seconds)
            df = df.dropna(subset=['Tiempo'])

            # Limpieza códigos
            if 'CodigoExtra' in df.columns:
                df['CodigoExtra'] = df['CodigoExtra'].astype(str).str.strip()

            def clasificar_piscina(codigo):
                c = str(codigo).upper()
                if '25' in c: return '25m'
                if '50' in c: return '50m'
                return 'Otros'
            
            df['TipoPiscina'] = df['InfoPiscina'].apply(clasificar_piscina)
            df = df.sort_values('Fecha')

            self.df_original = df
            
            # Reset UI
            clubes = sorted(df['Club'].astype(str).unique().tolist())
            self.combo_club['values'] = ["Todos"] + clubes
            self.var_club.set("Todos")
            self.var_fecha_inicio.set("")
            self.var_fecha_fin.set("")

            self.apply_filters()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el archivo:\n{e}")

    def apply_filters(self):
        if self.df_original is None: return

        df = self.df_original.copy()

        # Filtros básicos
        tipo = self.var_tipo.get()
        if tipo == "Solo Finales (N)":
            df = df[df['CodigoExtra'] == 'N']
        elif tipo == "Solo Parciales (S)":
            df = df[df['CodigoExtra'] == 'S']

        club = self.var_club.get()
        if club != "Todos":
            df = df[df['Club'] == club]

        # Filtro de Fechas (CAMBIO: Parseo formato DD/MM/AAAA)
        f_inicio = self.var_fecha_inicio.get()
        f_fin = self.var_fecha_fin.get()

        try:
            if f_inicio:
                # dayfirst=True ayuda a interpretar 01/02 como 1 de Febrero
                date_start = pd.to_datetime(f_inicio, dayfirst=True)
                df = df[df['Fecha'] >= date_start]
            if f_fin:
                date_end = pd.to_datetime(f_fin, dayfirst=True)
                df = df[df['Fecha'] <= date_end]
        except:
            messagebox.showwarning("Fechas", "Por favor usa el formato DD/MM/AAAA (Ej: 31/12/2023)")

        self.df_filtered = df
        self.lbl_info_count.config(text=f"Registros visibles: {len(df)}")
        self.update_stats()
        self.update_plots()

    def update_stats(self):
        if self.df_filtered is None or self.df_filtered.empty:
            self.lbl_stat_25.config(text="PB 25m: --")
            self.lbl_stat_50.config(text="PB 50m: --")
            return

        df_25 = self.df_filtered[self.df_filtered['TipoPiscina'] == '25m']
        df_50 = self.df_filtered[self.df_filtered['TipoPiscina'] == '50m']

        min_25 = df_25['Tiempo'].min()
        min_50 = df_50['Tiempo'].min()
        
        pb_25 = self.format_seconds_to_time(min_25)
        pb_50 = self.format_seconds_to_time(min_50)

        nadador = self.df_filtered['Nombre'].iloc[0] if not self.df_filtered.empty else "Desconocido"
        prueba = self.df_filtered['Prueba'].iloc[0] if not self.df_filtered.empty else ""

        self.lbl_stat_25.config(text=f"🏊 {nadador} ({prueba})\nPB 25m: {pb_25}")
        self.lbl_stat_50.config(text=f"\nPB 50m: {pb_50}")

    def update_plots(self):
        for widget in self.plot_container.winfo_children():
            widget.destroy()

        if self.df_filtered is None or self.df_filtered.empty:
            tk.Label(self.plot_container, text="No hay datos con estos filtros", bg="white", fg="red").pack(pady=50)
            return

        fig = plt.Figure(figsize=(8, 6), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        colors = {'25m': '#2980b9', '50m': '#e67e22', 'Otros': 'gray'}

        # Graficar
        for piscina in ['25m', '50m']:
            data = self.df_filtered[self.df_filtered['TipoPiscina'] == piscina]
            if not data.empty:
                ax.plot(data['Fecha'], data['Tiempo'], marker='o', linestyle='-', 
                        label=f'Piscina {piscina}', color=colors.get(piscina))
                
                # Anotaciones
                min_idx = data['Tiempo'].idxmin()
                best_row = data.loc[min_idx]
                tiempo_str = self.format_seconds_to_time(best_row['Tiempo'])
                
                ax.annotate(f"{tiempo_str}", 
                            (best_row['Fecha'], best_row['Tiempo']),
                            textcoords="offset points", xytext=(0,10), ha='center',
                            fontsize=9, weight='bold', color=colors.get(piscina))

        # --- CAMBIO: Formato Eje Y (Minutos:Segundos) ---
        def axis_formatter(x, pos):
            return self.format_seconds_to_time(x)
        
        ax.yaxis.set_major_formatter(FuncFormatter(axis_formatter))

        # --- CAMBIO: Formato Eje X (DD/MM/AAAA) ---
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        fig.autofmt_xdate(rotation=45) # Rotar fechas para que no se pisen

        # Estética
        ax.set_title("Evolución de Tiempos", fontsize=12, fontweight='bold', color='black')
        ax.set_ylabel("Tiempo", color='black') # Ya no ponemos "(s)" porque el formato es claro
        ax.tick_params(colors='black', labelcolor='black')
        ax.legend()
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_facecolor('#f9f9f9')

        canvas = FigureCanvasTkAgg(fig, master=self.plot_container)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = NatacionApp(root)
    root.mainloop()