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
        self.root.title("SwimAnalytics PRO - FEGAN Edition")
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
        
        # Contenedor principal
        self.main_container = tk.Frame(self.root, bg="white")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        self.create_sidebar()
        self.create_dashboard()
        
        # --- FIRMA DEL CREADOR (Footer) ---
        self.create_footer()

    def create_header(self):
        header = tk.Frame(self.root, bg=self.bg_dark, height=70)
        header.pack(side=tk.TOP, fill=tk.X)
        header.pack_propagate(False)

        lbl_title = tk.Label(header, text="🏊 SwimAnalytics PRO", 
                             font=("Helvetica", 20, "bold"), 
                             bg=self.bg_dark, fg="white")
        lbl_title.pack(side=tk.LEFT, padx=20)

        # Contenedor botones
        btn_frame = tk.Frame(header, bg=self.bg_dark)
        btn_frame.pack(side=tk.RIGHT, padx=20)

        btn_help = tk.Button(btn_frame, text="❓ ¿Cómo obtener el CSV?", command=self.show_instructions,
                             bg="#f39c12", fg="black",
                             font=("Arial", 10, "bold"), relief=tk.FLAT, padx=10, pady=5)
        btn_help.pack(side=tk.LEFT, padx=10)

        btn_load = tk.Button(btn_frame, text="📂 Cargar CSV", command=self.load_csv, 
                             bg="#27ae60", fg="black",
                             font=("Arial", 11, "bold"), relief=tk.FLAT, padx=15, pady=5)
        btn_load.pack(side=tk.LEFT)

    def create_footer(self):
        # Barra inferior delgada
        footer = tk.Frame(self.root, bg="#f2f2f2", height=30)
        footer.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Etiqueta en la derecha
        # CAMBIA "Xabier Guitian" POR TU NOMBRE
        lbl_credit = tk.Label(footer, text="Aplicación creada por Xabier Guitián López", 
                              font=("Arial", 9, "italic"), 
                              bg="#f2f2f2", fg="#7f8c8d")
        lbl_credit.pack(side=tk.RIGHT, padx=20, pady=5)

    def show_instructions(self):
        info_text = (
            "GUÍA PARA DESCARGAR DATOS DE LA FEGAN:\n\n"
            "1. Ve a la página web de la FEGAN (fegan.org).\n"
            "2. Entra en el apartado 'Natación' > 'Consulta de marcas'.\n"
            "3. En el filtro, busca por 'Apellido Apellido, Nombre'.\n"
            "4. Selecciona la prueba que quieras analizar.\n"
            "5. IMPORTANTE: Selecciona un rango de fechas muy amplio.\n"
            "6. En 'Amosar os primeiros', selecciona el máximo (100) y pulsa ENVIAR.\n"
            "7. Baja al final y pulsa: 'Exportar a táboa a CSV'."
        )
        messagebox.showinfo("Ayuda", info_text)

    def create_sidebar(self):
        sidebar = tk.Frame(self.main_container, bg=self.bg_light, width=250, padx=15, pady=15)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="FILTROS", font=("Arial", 12, "bold"), 
                 bg=self.bg_light, fg="#7f8c8d").pack(anchor="w", pady=(0, 10))

        # Filtros...
        tk.Label(sidebar, text="Tipo de Tiempo:", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        self.combo_tipo = ttk.Combobox(sidebar, textvariable=self.var_tipo, state="readonly", 
                                       values=["Todos", "Solo Finales (N)", "Solo Parciales (S)"])
        self.combo_tipo.pack(fill=tk.X, pady=(0, 15))

        tk.Label(sidebar, text="Club:", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        self.combo_club = ttk.Combobox(sidebar, textvariable=self.var_club, state="readonly", values=["Todos"])
        self.combo_club.pack(fill=tk.X, pady=(0, 15))

        tk.Label(sidebar, text="Rango de Fechas (DD/MM/AAAA):", bg=self.bg_light, fg="black", font=("Arial", 10, "bold")).pack(anchor="w")
        
        tk.Label(sidebar, text="Desde:", bg=self.bg_light, fg="#555").pack(anchor="w")
        entry_start = tk.Entry(sidebar, textvariable=self.var_fecha_inicio, bg="white", fg="black")
        entry_start.pack(fill=tk.X)
        
        tk.Label(sidebar, text="Hasta:", bg=self.bg_light, fg="#555").pack(anchor="w", pady=(5,0))
        entry_end = tk.Entry(sidebar, textvariable=self.var_fecha_fin, bg="white", fg="black")
        entry_end.pack(fill=tk.X, pady=(0, 15))

        btn_apply = tk.Button(sidebar, text="Aplicar Filtros", command=self.apply_filters,
                              bg=self.accent, fg="black", font=("Arial", 11, "bold"), pady=5)
        btn_apply.pack(fill=tk.X, pady=20)
        
        self.lbl_info_count = tk.Label(sidebar, text="Registros: 0", bg=self.bg_light, fg="#7f8c8d")
        self.lbl_info_count.pack(side=tk.BOTTOM)

    def create_dashboard(self):
        self.dashboard_frame = tk.Frame(self.main_container, bg="white")
        self.dashboard_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Stats
        self.stats_frame = tk.Frame(self.dashboard_frame, bg="#f9f9f9", height=130, bd=1, relief=tk.SOLID)
        self.stats_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        self.stats_frame.pack_propagate(False)
        
        # Nombre centrado
        self.lbl_nadador = tk.Label(self.stats_frame, text="Esperando datos...", 
                                    font=("Arial", 18, "bold"), bg="#f9f9f9", fg="#2c3e50")
        self.lbl_nadador.pack(side=tk.TOP, pady=(15, 5))

        times_frame = tk.Frame(self.stats_frame, bg="#f9f9f9")
        times_frame.pack(side=tk.TOP, fill=tk.X, pady=5)

        self.lbl_stat_25 = tk.Label(times_frame, text="PB 25m: --", font=("Arial", 14), bg="#f9f9f9", fg="black")
        self.lbl_stat_25.pack(side=tk.LEFT, expand=True)
        
        self.lbl_stat_50 = tk.Label(times_frame, text="PB 50m: --", font=("Arial", 14), bg="#f9f9f9", fg="black")
        self.lbl_stat_50.pack(side=tk.LEFT, expand=True)

        # Gráfico
        self.plot_container = tk.Frame(self.dashboard_frame, bg="white")
        self.plot_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

    # --- LÓGICA ---
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

            df['Fecha'] = pd.to_datetime(df['Fecha'], format='%Y%m%d', errors='coerce')
            df['Tiempo'] = df['Tiempo'].apply(self.convert_time_to_seconds)
            df = df.dropna(subset=['Tiempo'])

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

        tipo = self.var_tipo.get()
        if tipo == "Solo Finales (N)": df = df[df['CodigoExtra'] == 'N']
        elif tipo == "Solo Parciales (S)": df = df[df['CodigoExtra'] == 'S']

        club = self.var_club.get()
        if club != "Todos": df = df[df['Club'] == club]

        f_inicio = self.var_fecha_inicio.get()
        f_fin = self.var_fecha_fin.get()
        try:
            if f_inicio: df = df[df['Fecha'] >= pd.to_datetime(f_inicio, dayfirst=True)]
            if f_fin: df = df[df['Fecha'] <= pd.to_datetime(f_fin, dayfirst=True)]
        except:
            messagebox.showwarning("Fechas", "Usa formato DD/MM/AAAA")

        self.df_filtered = df
        self.lbl_info_count.config(text=f"Registros visibles: {len(df)}")
        self.update_stats()
        self.update_plots()

    def update_stats(self):
        if self.df_filtered is None or self.df_filtered.empty:
            self.lbl_nadador.config(text="Sin datos")
            self.lbl_stat_25.config(text="PB 25m: --")
            self.lbl_stat_50.config(text="PB 50m: --")
            return

        df_25 = self.df_filtered[self.df_filtered['TipoPiscina'] == '25m']
        df_50 = self.df_filtered[self.df_filtered['TipoPiscina'] == '50m']

        pb_25 = self.format_seconds_to_time(df_25['Tiempo'].min())
        pb_50 = self.format_seconds_to_time(df_50['Tiempo'].min())

        nadador = self.df_filtered['Nombre'].iloc[0]
        prueba = self.df_filtered['Prueba'].iloc[0]

        self.lbl_nadador.config(text=f"{nadador} - {prueba}")
        self.lbl_stat_25.config(text=f"PB 25m: {pb_25}")
        self.lbl_stat_50.config(text=f"PB 50m: {pb_50}")

    def update_plots(self):
        for widget in self.plot_container.winfo_children(): widget.destroy()

        if self.df_filtered is None or self.df_filtered.empty:
            tk.Label(self.plot_container, text="No hay datos", bg="white", fg="red").pack(pady=50)
            return

        fig = plt.Figure(figsize=(8, 6), dpi=100, facecolor='white')
        ax = fig.add_subplot(111)
        colors = {'25m': '#2980b9', '50m': '#e67e22', 'Otros': 'gray'}

        for piscina in ['25m', '50m']:
            data = self.df_filtered[self.df_filtered['TipoPiscina'] == piscina]
            if not data.empty:
                ax.plot(data['Fecha'], data['Tiempo'], marker='o', linestyle='-', 
                        label=f'Piscina {piscina}', color=colors.get(piscina))
                
                # Etiqueta mejor marca
                best = data.loc[data['Tiempo'].idxmin()]
                ax.annotate(self.format_seconds_to_time(best['Tiempo']), 
                            (best['Fecha'], best['Tiempo']),
                            textcoords="offset points", xytext=(0,10), ha='center',
                            fontsize=9, weight='bold', color=colors.get(piscina))

        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: self.format_seconds_to_time(x)))
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m/%Y'))
        fig.autofmt_xdate(rotation=45)

        ax.set_title("Evolución de Tiempos", fontsize=12, fontweight='bold', color='black')
        ax.set_ylabel("Tiempo", color='black')
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