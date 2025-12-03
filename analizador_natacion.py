import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

# Configuración de estilo para los gráficos
sns.set_theme(style="whitegrid")

class NatacionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SwimAnalytics - Analizador de Rendimiento")
        self.root.geometry("1200x800")
        
        # --- FORZAR MODO CLARO (Solución para Mac Dark Mode) ---
        # Configuramos el fondo principal blanco
        self.root.configure(bg="white")
        
        # Estilos globales para evitar textos invisibles
        self.style = ttk.Style()
        self.style.theme_use('clam') # Un tema más moderno y compatible
        
        # --- Variables de Estado ---
        self.df = None
        self.file_path = None

        # --- Interfaz Gráfica (Layout) ---
        self.create_widgets()

    def create_widgets(self):
        # 1. Panel Superior (Controles) - Fondo oscuro, texto blanco
        control_frame = tk.Frame(self.root, bg="#2c3e50", height=80)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        control_frame.pack_propagate(False)

        # Título
        lbl_title = tk.Label(control_frame, text="SwimAnalytics", 
                             font=("Helvetica", 18, "bold"), 
                             bg="#2c3e50", fg="white") # Forzamos blanco
        lbl_title.pack(side=tk.LEFT, padx=20)

        # Botón
        btn_load = tk.Button(control_frame, text="📂 Cargar CSV", command=self.load_csv, 
                             bg="#27ae60", fg="white", # Verde con texto blanco
                             font=("Arial", 11, "bold"), relief=tk.FLAT, padx=15, pady=5)
        # Nota: En Mac los botones nativos a veces ignoran el BG, pero el texto se leerá
        btn_load.pack(side=tk.RIGHT, padx=20, pady=20)

        # Estado
        self.lbl_status = tk.Label(control_frame, text="Esperando archivo...", 
                                   bg="#2c3e50", fg="#ecf0f1", font=("Arial", 10))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # 2. Panel Principal (Dividido)
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg="#bdc3c7")
        main_pane.pack(fill=tk.BOTH, expand=True)

        # --- Panel Izquierdo: Estadísticas ---
        stats_frame = tk.Frame(main_pane, bg="white", width=350)
        main_pane.add(stats_frame)
        
        # Título de estadísticas (Texto negro forzado)
        tk.Label(stats_frame, text="Resumen del Nadador", 
                 font=("Arial", 14, "bold"), 
                 bg="white", fg="black").pack(pady=20)
        
        # Caja de texto de estadísticas (Fondo gris claro, texto negro)
        self.stats_text = tk.Text(stats_frame, height=20, width=40, 
                                  font=("Consolas", 12), 
                                  bg="#f4f6f7", fg="black", # Colores fijos
                                  relief=tk.FLAT, padx=10, pady=10)
        self.stats_text.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)
        self.stats_text.insert(tk.END, "Carga un archivo para ver los datos.")
        self.stats_text.config(state=tk.DISABLED)

        # --- Panel Derecho: Gráficos ---
        self.plot_frame = tk.Frame(main_pane, bg="white")
        main_pane.add(self.plot_frame)

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")])
        if not file_path:
            return

        try:
            col_names = ['Licencia', 'Nombre', 'AnoNacimiento', 'Club', 'Prueba', 'Tiempo', 'InfoPiscina', 'Fecha', 'Lugar', 'CodigoExtra']
            self.df = pd.read_csv(file_path, header=None, names=col_names)

            # Preprocesamiento
            self.df['Fecha'] = pd.to_datetime(self.df['Fecha'], format='%Y%m%d', errors='coerce')
            self.df['Tiempo'] = pd.to_numeric(self.df['Tiempo'], errors='coerce')

            def clasificar_piscina(codigo):
                c = str(codigo).upper()
                if '25' in c: return '25m'
                if '50' in c: return '50m'
                return 'Desconocida'
            
            self.df['TipoPiscina'] = self.df['InfoPiscina'].apply(clasificar_piscina)
            self.df = self.df.sort_values('Fecha')

            # Actualizar UI
            self.file_path = file_path
            self.lbl_status.config(text=f"Archivo: {file_path.split('/')[-1]}")
            
            self.update_stats()
            self.update_plots()

        except Exception as e:
            messagebox.showerror("Error", f"Detalle: {str(e)}")

    def update_stats(self):
        if self.df is None: return

        df_25 = self.df[self.df['TipoPiscina'] == '25m']
        df_50 = self.df[self.df['TipoPiscina'] == '50m']
        
        nadador = self.df['Nombre'].iloc[0]
        club = self.df['Club'].iloc[-1]
        
        pb_25 = df_25['Tiempo'].min() if not df_25.empty else "N/A"
        pb_50 = df_50['Tiempo'].min() if not df_50.empty else "N/A"
        avg_25 = df_25['Tiempo'].mean() if not df_25.empty else 0
        avg_50 = df_50['Tiempo'].mean() if not df_50.empty else 0

        info = (
            f"NADADOR:\n{nadador}\n\n"
            f"CLUB ACTUAL:\n{club}\n"
            f"{'-'*30}\n"
            f"PISCINA 25m (Corta):\n"
            f"  Mejor Marca: {pb_25} s\n"
            f"  Promedio:    {avg_25:.2f} s\n"
            f"  Carreras:    {len(df_25)}\n\n"
            f"PISCINA 50m (Larga):\n"
            f"  Mejor Marca: {pb_50} s\n"
            f"  Promedio:    {avg_50:.2f} s\n"
            f"  Carreras:    {len(df_50)}\n"
        )

        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, info)
        self.stats_text.config(state=tk.DISABLED)

    def update_plots(self):
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        # Forzamos el fondo de la figura a blanco para que contraste
        fig = plt.Figure(figsize=(8, 6), dpi=100, facecolor='white')
        
        # Subplots
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212)

        # Colores personalizados
        colors = {'25m': '#2980b9', '50m': '#e67e22'} # Azul fuerte y Naranja fuerte

        # Gráfico 1
        for pool_type in ['25m', '50m']:
            data = self.df[self.df['TipoPiscina'] == pool_type]
            if not data.empty:
                ax1.plot(data['Fecha'], data['Tiempo'], marker='o', linestyle='-', 
                         label=f'Piscina {pool_type}', color=colors.get(pool_type, 'black'))

        ax1.set_title("Progresión de Tiempos", fontsize=12, fontweight='bold', color='black')
        ax1.set_ylabel("Tiempo (s)", color='black')
        ax1.tick_params(colors='black') # Ejes en negro
        ax1.legend()
        ax1.grid(True, linestyle='--', alpha=0.3)
        ax1.set_facecolor('#f9f9f9') # Fondo suave dentro del gráfico

        # Gráfico 2
        sns.boxplot(data=self.df, x='TipoPiscina', y='Tiempo', ax=ax2, palette="Set2")
        sns.stripplot(data=self.df, x='TipoPiscina', y='Tiempo', color='#2c3e50', alpha=0.5, ax=ax2)
        
        ax2.set_title("Distribución de Tiempos", fontsize=12, fontweight='bold', color='black')
        ax2.set_ylabel("Tiempo (s)", color='black')
        ax2.set_xlabel("Piscina", color='black')
        ax2.tick_params(colors='black')
        ax2.set_facecolor('#f9f9f9')

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    try:
        # Intento de mejora de resolución en pantallas Retina (Mac)
        from ctypes import cdll
        lib = cdll.LoadLibrary(util.find_library('CoreGraphics'))
    except:
        pass
    
    app = NatacionApp(root)
    root.mainloop()