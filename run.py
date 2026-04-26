import subprocess
import sys
import os

# Pega o caminho da pasta onde o run.py está
dir_projeto = os.path.dirname(os.path.abspath(__file__))

# Roda o streamlit garantindo que ele comece dentro da pasta certa
subprocess.run(
    [sys.executable, "-m", "streamlit", "run", "app.py"],
    cwd=dir_projeto
)