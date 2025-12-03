import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from datetime import datetime

# Configuración de estilo para los gráficos
sns.set_theme(style="whitegrid")

class NatacionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SwimAnalytics - Analizador de Rendimiento")
        self.root.geometry("1200x800")
        
        # --- Variables de Estado ---
        self.df = None
        self.file_path = None

        # --- Interfaz Gráfica (Layout) ---
        self.create_widgets()

    def create_widgets(self):
        # 1. Panel Superior (Controles)
        control_frame = tk.Frame(self.root, bg="#34495e", height=80)
        control_frame.pack(side=tk.TOP, fill=tk.X)
        control_frame.pack_propagate(False)

        lbl_title = tk.Label(control_frame, text="SwimAnalytics", font=("Helvetica", 18, "bold"), bg="#34495e", fg="white")
        lbl_title.pack(side=tk.LEFT, padx=20)

        btn_load = tk.Button(control_frame, text="📂 Cargar CSV", command=self.load_csv, 
                             bg="#2ecc71", fg="white", font=("Arial", 11, "bold"), relief=tk.FLAT, padx=15, pady=5)
        btn_load.pack(side=tk.RIGHT, padx=20, pady=20)

        self.lbl_status = tk.Label(control_frame, text="Esperando archivo...", bg="#34495e", fg="#bdc3c7", font=("Arial", 10))
        self.lbl_status.pack(side=tk.RIGHT, padx=10)

        # 2. Panel Principal (Dividido en Estadísticas y Gráficos)
        main_pane = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, sashwidth=5, bg="#ecf0f1")
        main_pane.pack(fill=tk.BOTH, expand=True)

        # --- Panel Izquierdo: Estadísticas ---
        stats_frame = tk.Frame(main_pane, bg="white", width=300)
        main_pane.add(stats_frame)
        
        tk.Label(stats_frame, text="Resumen del Nadador", font=("Arial", 14, "bold"), bg="white", fg="#2c3e50").pack(pady=20)
        
        self.stats_text = tk.Text(stats_frame, height=20, width=35, font=("Consolas", 11), bg="#f8f9fa", relief=tk.FLAT, padx=10, pady=10)
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
            # Leer CSV (sin cabecera según tu ejemplo)
            # Asignamos nombres manualmente basándonos en tu archivo
            col_names = ['Licencia', 'Nombre', 'AnoNacimiento', 'Club', 'Prueba', 'Tiempo', 'InfoPiscina', 'Fecha', 'Lugar', 'CodigoExtra']
            self.df = pd.read_csv(file_path, header=None, names=col_names)

            # --- Preprocesamiento de Datos ---
            
            # 1. Convertir Fecha
            self.df['Fecha'] = pd.to_datetime(self.df['Fecha'], format='%Y%m%d', errors='coerce')
            
            # 2. Convertir Tiempo a numérico
            self.df['Tiempo'] = pd.to_numeric(self.df['Tiempo'], errors='coerce')

            # 3. Determinar Piscina (25m vs 50m)
            def clasificar_piscina(codigo):
                c = str(codigo).upper()
                if '25' in c: return '25m'
                if '50' in c: return '50m'
                return 'Desconocida'
            
            self.df['TipoPiscina'] = self.df['InfoPiscina'].apply(clasificar_piscina)

            # Ordenar por fecha
            self.df = self.df.sort_values('Fecha')

            # Actualizar Interfaz
            self.file_path = file_path
            self.lbl_status.config(text=f"Archivo: {file_path.split('/')[-1]}")
            
            self.update_stats()
            self.update_plots()

        except Exception as e:
            messagebox.showerror("Error de Carga", f"No se pudo leer el archivo correctamente.\n\nDetalle: {str(e)}")

    def update_stats(self):
        if self.df is None: return

        # Filtrar datos
        df_25 = self.df[self.df['TipoPiscina'] == '25m']
        df_50 = self.df[self.df['TipoPiscina'] == '50m']

        nadador = self.df['Nombre'].iloc[0]
        prueba = self.df['Prueba'].iloc[0]
        club = self.df['Club'].iloc[-1]  # Último club registrado

        # Cálculos
        pb_25 = df_25['Tiempo'].min() if not df_25.empty else "N/A"
        pb_50 = df_50['Tiempo'].min() if not df_50.empty else "N/A"
        
        avg_25 = df_25['Tiempo'].mean() if not df_25.empty else 0
        avg_50 = df_50['Tiempo'].mean() if not df_50.empty else 0

        # Formatear texto
        info = (
            f"NADADOR:\n{nadador}\n\n"
            f"CLUB ACTUAL:\n{club}\n\n"
            f"PRUEBA PRINCIPAL:\n{prueba}\n"
            f"{'-'*30}\n"
            f"ESTADÍSTICAS PISCINA 25m:\n"
            f"  Mejor Marca: {pb_25} s\n"
            f"  Promedio:    {avg_25:.2f} s\n"
            f"  Nº Carreras: {len(df_25)}\n\n"
            f"ESTADÍSTICAS PISCINA 50m:\n"
            f"  Mejor Marca: {pb_50} s\n"
            f"  Promedio:    {avg_50:.2f} s\n"
            f"  Nº Carreras: {len(df_50)}\n"
        )

        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, info)
        self.stats_text.config(state=tk.DISABLED)

    def update_plots(self):
        # Limpiar gráfico anterior
        for widget in self.plot_frame.winfo_children():
            widget.destroy()

        # Crear figura con 2 subgráficos
        fig = plt.Figure(figsize=(8, 6), dpi=100)
        ax1 = fig.add_subplot(211) # Arriba: Evolución
        ax2 = fig.add_subplot(212) # Abajo: Distribución (Boxplot)

        # Gráfico 1: Evolución de Tiempos
        # Separamos manualmente para controlar colores y etiquetas mejor en Matplotlib puro dentro de Tkinter
        colors = {'25m': '#3498db', '50m': '#e67e22'}
        
        for pool_type in ['25m', '50m']:
            data = self.df[self.df['TipoPiscina'] == pool_type]
            if not data.empty:
                ax1.plot(data['Fecha'], data['Tiempo'], marker='o', linestyle='-', 
                         label=f'Piscina {pool_type}', color=colors.get(pool_type, 'gray'), alpha=0.7)

        ax1.set_title("Progresión de Tiempos", fontsize=12, fontweight='bold')
        ax1.set_ylabel("Tiempo (segundos)")
        ax1.legend()
        ax1.grid(True, linestyle='--', alpha=0.5)

        # Gráfico 2: Boxplot (Distribución)
        sns.boxplot(data=self.df, x='TipoPiscina', y='Tiempo', ax=ax2, palette="Set2")
        sns.stripplot(data=self.df, x='TipoPiscina', y='Tiempo', color='black', alpha=0.3, ax=ax2)
        ax2.set_title("Consistencia y Distribución de Tiempos", fontsize=12, fontweight='bold')
        ax2.set_xlabel("")
        ax2.set_ylabel("Tiempo (segundos)")

        fig.tight_layout()

        # Insertar gráfico en Tkinter
        canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    # Intentar maximizar la ventana según el sistema operativo
    try:
        root.state('zoomed') 
    except:
        pass
    app = NatacionApp(root)
    root.mainloop()