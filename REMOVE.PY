import os
import sys
import ctypes
import subprocess
import winreg
import shutil
import re
import random
import time
import tempfile
from pathlib import Path

def is_admin():
    """Vérifie si le script est exécuté avec les privilèges administrateur."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def run_as_admin():
    """Relance le script avec des privilèges administrateur."""
    if is_admin():
        return True
    
    try:
        script = os.path.abspath(sys.argv[0])
        params = ' '.join([f'"{x}"' for x in sys.argv[1:]])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 1)
        return False
    except Exception as e:
        print(f"[!] Erreur lors de l'élévation des privilèges: {e}")
        return False

def search_registry_for_malware(service_name_patterns):
    """Recherche toutes les clés de registre potentiellement créées par le malware."""
    found_keys = []
    
    # Recherche des clés de démarrage
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run") as key:
            i = 0
            while True:
                try:
                    name, value, _ = winreg.EnumValue(key, i)
                    for pattern in service_name_patterns:
                        if re.search(pattern, name, re.IGNORECASE) or re.search(pattern, value, re.IGNORECASE):
                            found_keys.append((winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run", name))
                    i += 1
                except WindowsError:
                    break
    except Exception as e:
        print(f"[!] Erreur lors de la recherche dans le registre: {e}")
    
    # Recherche dans les exceptions de Windows Defender
    try:
        key_path = r"SOFTWARE\Microsoft\Windows Defender\Exclusions\Paths"
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            i = 0
            while True:
                try:
                    name, _, _ = winreg.EnumValue(key, i)
                    for temp_pattern in ['\\Temp\\', '\\AppData\\']:
                        if temp_pattern in name:
                            found_keys.append((winreg.HKEY_LOCAL_MACHINE, key_path, name))
                    i += 1
                except WindowsError:
                    break
    except Exception:
        pass
    
    return found_keys

def remove_registry_entries(reg_entries):
    """Supprime les entrées de registre identifiées."""
    for hkey, key_path, name in reg_entries:
        try:
            with winreg.OpenKey(hkey, key_path, 0, winreg.KEY_WRITE) as key:
                winreg.DeleteValue(key, name)
                print(f"[+] Entrée de registre supprimée: {key_path}\\{name}")
        except Exception as e:
            print(f"[-] Erreur lors de la suppression de l'entrée de registre {key_path}\\{name}: {e}")

def find_scheduled_tasks(patterns):
    """Trouve toutes les tâches planifiées qui correspondent aux patterns du malware."""
    found_tasks = []
    
    try:
        # Obtenir toutes les tâches planifiées
        result = subprocess.run(
            ['schtasks', '/query', '/fo', 'csv'],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if line.strip():
                    for pattern in patterns:
                        if re.search(pattern, line, re.IGNORECASE):
                            # Extraire le nom de la tâche
                            parts = line.split('"')
                            if len(parts) > 1:
                                task_name = parts[1].strip()
                                if task_name and task_name != "TaskName":
                                    found_tasks.append(task_name)
    except Exception as e:
        print(f"[!] Erreur lors de la recherche des tâches planifiées: {e}")
    
    return found_tasks

def remove_scheduled_tasks(tasks):
    """Supprime les tâches planifiées identifiées."""
    for task in tasks:
        try:
            subprocess.run(['schtasks', '/delete', '/tn', task, '/f'], check=False, capture_output=True)
            print(f"[+] Tâche planifiée supprimée: {task}")
        except Exception as e:
            print(f"[-] Erreur lors de la suppression de la tâche {task}: {e}")

def find_suspicious_directories():
    """Trouve les répertoires potentiellement créés par le malware."""
    suspicious_dirs = []
    
    # Patterns de noms légitimes utilisés par le malware
    name_patterns = [
        "WindowsUpdateAssistant",
        "MicrosoftEdgeUpdate",
        "OfficeClickToRun",
        "WindowsSecurityHealth",
        "SystemComponentMonitor"
    ]
    
    # Recherche dans les dossiers courants
    check_dirs = [
        tempfile.gettempdir(),
        os.path.expandvars("%APPDATA%"),
        os.path.expandvars("%LOCALAPPDATA%")
    ]
    
    for base_dir in check_dirs:
        try:
            for item in os.listdir(base_dir):
                full_path = os.path.join(base_dir, item)
                if os.path.isdir(full_path):
                    for pattern in name_patterns:
                        if re.search(f"{pattern}_[a-z0-9]+", item, re.IGNORECASE):
                            suspicious_dirs.append(full_path)
        except Exception:
            pass
    
    return suspicious_dirs

def remove_suspicious_directories(directories):
    """Supprime les répertoires suspects."""
    for directory in directories:
        try:
            # D'abord, essayez de retirer les attributs cachés
            subprocess.run(['attrib', '-h', '-s', directory], check=False)
            
            # Essayez de supprimer tous les fichiers à l'intérieur
            for root, dirs, files in os.walk(directory, topdown=False):
                for file in files:
                    full_path = os.path.join(root, file)
                    try:
                        os.chmod(full_path, 0o666)  # Rendre le fichier accessible
                        subprocess.run(['attrib', '-h', '-s', full_path], check=False)
                        os.remove(full_path)
                    except Exception:
                        pass
            
            # Supprimer le répertoire
            shutil.rmtree(directory, ignore_errors=True)
            print(f"[+] Répertoire suspect supprimé: {directory}")
        except Exception as e:
            print(f"[-] Erreur lors de la suppression du répertoire {directory}: {e}")

def clean_wmi_persistence():
    """Nettoie les persistances WMI."""
    print("[*] Nettoyage des persistances WMI...")
    
    # Supprimer les filtres d'événements WMI
    ps_remove_filters = """
    Get-WmiObject -Namespace root\\subscription -Class __EventFilter | Where-Object {
        $_.Name -match "^(MS|StartupFilter|LogonFilter|TimeFilter)_[A-Z0-9]{8}$"
    } | ForEach-Object {
        Write-Output "Suppression du filtre: $($_.Name)"
        Remove-WmiObject -InputObject $_
    }
    """
    
    # Supprimer les consommateurs d'événements WMI
    ps_remove_consumers = """
    Get-WmiObject -Namespace root\\subscription -Class CommandLineEventConsumer | Where-Object {
        $_.Name -match "^(MS|StartupConsumer|LogonConsumer|TimeConsumer)_[A-Z0-9]{8}$"
    } | ForEach-Object {
        Write-Output "Suppression du consommateur: $($_.Name)"
        Remove-WmiObject -InputObject $_
    }
    """
    
    # Supprimer les liaisons WMI
    ps_remove_bindings = """
    Get-WmiObject -Namespace root\\subscription -Class __FilterToConsumerBinding | ForEach-Object {
        $filterName = $_.Filter.Split('=')[1].Replace('\\"', '"')
        if ($filterName -match "^(MS|StartupFilter|LogonFilter|TimeFilter)_[A-Z0-9]{8}$") {
            Write-Output "Suppression de la liaison WMI pour: $filterName"
            Remove-WmiObject -InputObject $_
        }
    }
    """
    
    try:
        # Exécuter les commandes PowerShell
        for ps_cmd in [ps_remove_bindings, ps_remove_consumers, ps_remove_filters]:
            subprocess.run(
                ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
                check=False,
                capture_output=True
            )
        print("[+] Nettoyage WMI terminé")
    except Exception as e:
        print(f"[-] Erreur lors du nettoyage WMI: {e}")

def check_running_processes():
    """Vérifie si des processus malveillants sont toujours en cours d'exécution."""
    suspicious_procs = []
    
    try:
        # Utiliser PowerShell pour lister les processus avec leurs chemins
        ps_cmd = """
        Get-Process | Where-Object { $_.Path -ne $null } | ForEach-Object {
            $proc = $_
            $path = $proc.Path
            $name = $proc.ProcessName
            Write-Output "$($proc.Id)|$name|$path"
        }
        """
        
        result = subprocess.run(
            ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_cmd],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            for line in result.stdout.split('\n'):
                if not line.strip():
                    continue
                
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    pid, name, path = parts[0], parts[1], parts[2]
                    
                    # Vérifier si le chemin contient des dossiers suspects
                    for pattern in ["WindowsUpdateAssistant_", "MicrosoftEdgeUpdate_", "OfficeClickToRun_", 
                                   "WindowsSecurityHealth_", "SystemComponentMonitor_"]:
                        if pattern.lower() in path.lower():
                            suspicious_procs.append((pid, name, path))
    except Exception as e:
        print(f"[!] Erreur lors de la vérification des processus: {e}")
    
    return suspicious_procs

def terminate_suspicious_processes(processes):
    """Termine les processus suspects."""
    for pid, name, path in processes:
        try:
            subprocess.run(['taskkill', '/F', '/PID', pid], check=False)
            print(f"[+] Processus terminé: {name} (PID: {pid}, Chemin: {path})")
        except Exception as e:
            print(f"[-] Erreur lors de la terminaison du processus {name} (PID: {pid}): {e}")

def clean_dll_hijacking():
    """Nettoie les tentatives de DLL hijacking."""
    print("[*] Recherche et nettoyage des DLL hijackées...")
    
    # Liste des DLL souvent ciblées
    target_dlls = [
        "version.dll",
        "wininet.dll",
        "wintrust.dll",
        "secur32.dll",
        "apphelp.dll",
        "cryptsp.dll"
    ]
    
    # Applications couramment ciblées
    target_apps = [
        os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), "Internet Explorer"),
        os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), "Windows NT", "Accessories"),
        os.path.join(os.environ.get('WINDIR', 'C:\\Windows'))
    ]
    
    # Recherche des DLL potentiellement hijackées
    hijacked_dlls = []
    for app_dir in target_apps:
        if os.path.exists(app_dir):
            for root, dirs, files in os.walk(app_dir):
                for file in files:
                    if file.lower() in [dll.lower() for dll in target_dlls]:
                        hijacked_dlls.append(os.path.join(root, file))
    
    # Pour chaque DLL trouvée, vérifiez si c'est une DLL légitime ou hijackée
    for dll_path in hijacked_dlls:
        try:
            # Vérifier la taille et les attributs pour identifier les DLL suspectes
            # Les DLL système sont généralement plus grandes et signées
            file_size = os.path.getsize(dll_path)
            if file_size < 100000:  # Moins de 100KB est suspect
                print(f"[!] DLL potentiellement hijackée trouvée: {dll_path}")
                
                # Sauvegarde avant suppression
                backup_path = f"{dll_path}.bak"
                try:
                    shutil.copy2(dll_path, backup_path)
                    print(f"[+] Sauvegarde créée: {backup_path}")
                except Exception:
                    pass
                
                # Supprimer la DLL suspectée
                try:
                    os.chmod(dll_path, 0o666)  # Rendre le fichier accessible
                    subprocess.run(['attrib', '-h', '-s', dll_path], check=False)
                    os.remove(dll_path)
                    print(f"[+] DLL hijackée supprimée: {dll_path}")
                except Exception as e:
                    print(f"[-] Erreur lors de la suppression de la DLL {dll_path}: {e}")
        except Exception:
            pass

def main():
    """Fonction principale du nettoyeur de malware."""
    print("\n===== NETTOYEUR DE MALWARE AVANCÉ =====")
    print(f"Date d'exécution: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("========================================")
    
    # Vérifier les privilèges administrateur
    if not is_admin():
        print("[!] Ce script nécessite des privilèges administrateur.")
        print("[*] Tentative d'élévation des privilèges...")
        if not run_as_admin():
            print("[!] Impossible d'obtenir les privilèges administrateur. Exécutez ce script en tant qu'administrateur.")
            sys.exit(1)
        return
    
    print("[+] Privilèges administrateur confirmés.")
    
    # 1. Arrêter les processus suspects
    print("\n[*] Recherche de processus suspects...")
    suspicious_processes = check_running_processes()
    if suspicious_processes:
        print(f"[!] {len(suspicious_processes)} processus suspects trouvés.")
        terminate_suspicious_processes(suspicious_processes)
    else:
        print("[+] Aucun processus suspect trouvé.")
    
    # 2. Supprimer les tâches planifiées
    print("\n[*] Recherche de tâches planifiées malveillantes...")
    task_patterns = [
        "WindowsUpdateAssistant",
        "MicrosoftEdgeUpdate",
        "OfficeClickToRun",
        "WindowsSecurityHealth",
        "SystemComponentMonitor",
        "Service"
    ]
    
    suspicious_tasks = find_scheduled_tasks(task_patterns)
    if suspicious_tasks:
        print(f"[!] {len(suspicious_tasks)} tâches planifiées suspectes trouvées.")
        remove_scheduled_tasks(suspicious_tasks)
    else:
        print("[+] Aucune tâche planifiée suspecte trouvée.")
    
    # 3. Nettoyer le registre
    print("\n[*] Recherche d'entrées de registre malveillantes...")
    registry_patterns = [
        "WindowsUpdateAssistant",
        "MicrosoftEdgeUpdate",
        "OfficeClickToRun",
        "WindowsSecurityHealth",
        "SystemComponentMonitor",
        "Service"
    ]
    
    registry_entries = search_registry_for_malware(registry_patterns)
    if registry_entries:
        print(f"[!] {len(registry_entries)} entrées de registre suspectes trouvées.")
        remove_registry_entries(registry_entries)
    else:
        print("[+] Aucune entrée de registre suspecte trouvée.")
    
    # 4. Nettoyer les persistances WMI
    clean_wmi_persistence()
    
    # 5. Nettoyer les DLL hijackées
    clean_dll_hijacking()
    
    # 6. Supprimer les répertoires suspects
    print("\n[*] Recherche de répertoires malveillants...")
    suspicious_dirs = find_suspicious_directories()
    if suspicious_dirs:
        print(f"[!] {len(suspicious_dirs)} répertoires suspects trouvés.")
        remove_suspicious_directories(suspicious_dirs)
    else:
        print("[+] Aucun répertoire suspect trouvé.")
    
    # 7. Réactiver les protections
    print("\n[*] Réactivation des protections Windows Defender...")
    try:
        # Réactiver Windows Defender
        subprocess.run(
            ['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command',
             "Set-MpPreference -DisableRealtimeMonitoring $false"],
            check=False,
            capture_output=True
        )
        print("[+] Protection en temps réel de Windows Defender réactivée.")
    except Exception:
        print("[-] Erreur lors de la réactivation de Windows Defender.")
    
    print("\n===== NETTOYAGE TERMINÉ =====")
    print("Il est fortement recommandé de redémarrer votre système pour finaliser le nettoyage.")
    restart = input("Voulez-vous redémarrer maintenant? (o/n): ").lower()
    if restart == 'o':
        subprocess.run(['shutdown', '/r', '/t', '10', '/c', "Redémarrage pour finaliser le nettoyage du malware"])
        print("Le système va redémarrer dans 10 secondes.")
    else:
        print("N'oubliez pas de redémarrer votre système dès que possible.")

if __name__ == "__main__":
    main()