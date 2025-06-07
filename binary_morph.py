# binary_morph.py
import os
import random
import string
import struct
import time
import sys

class BinaryMorphing:
    """Techniques avancées de morphing binaire pour éviter la détection AV."""
    
    @staticmethod
    def generate_random_bytes(length):
        """Génère une séquence d'octets aléatoires."""
        return bytes(random.randint(0, 255) for _ in range(length))
    
    @staticmethod
    def generate_legitimate_resource_name():
        """Génère un nom de ressource qui semble légitime."""
        prefixes = ["MS", "Win", "Sys", "Net", "Update", "Config", "Registry", "Service"]
        suffixes = ["Data", "Resource", "Config", "Info", "Manager", "Helper", "Update", "Service"]
        
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        # Ajouter un nombre aléatoire pour plus de diversité
        number = random.randint(1, 99)
        
        return f"{prefix}{suffix}{number}"
    
    @staticmethod
    def create_dummy_resources(count=5, min_size=1024, max_size=8192):
        """Crée des ressources factices qui ressemblent à des ressources légitimes."""
        resources = []
        
        for _ in range(count):
            # Générer une taille aléatoire
            size = random.randint(min_size, max_size)
            
            # Générer un nom légitime
            name = BinaryMorphing.generate_legitimate_resource_name()
            
            # Générer le contenu
            content = BinaryMorphing.generate_random_bytes(size)
            
            resources.append({
                'name': name,
                'content': content,
                'size': size
            })
        
        return resources
    
    @staticmethod
    def create_dummy_import_table():
        """Crée une fausse table d'importation avec des DLLs Windows légitimes."""
        legitimate_dlls = [
            "kernel32.dll",
            "user32.dll",
            "advapi32.dll",
            "shell32.dll",
            "ole32.dll",
            "oleaut32.dll",
            "ntdll.dll",
            "gdi32.dll",
            "comctl32.dll",
            "ws2_32.dll",
            "winspool.drv",
            "comdlg32.dll"
        ]
        
        legitimate_functions = [
            # Kernel32.dll
            ("GetProcAddress", "LoadLibraryA", "GetModuleHandleA", "VirtualAlloc", "VirtualProtect",
            "CreateProcessA", "WriteFile", "ReadFile", "CloseHandle", "GetLastError"),
            
            # User32.dll
            ("MessageBoxA", "RegisterClassExA", "CreateWindowExA", "ShowWindow", "UpdateWindow",
            "GetMessageA", "DispatchMessageA", "DefWindowProcA", "SendMessageA"),
            
            # Advapi32.dll
            ("RegOpenKeyExA", "RegQueryValueExA", "RegCloseKey", "GetUserNameA", "LookupAccountNameA",
            "InitializeSecurityDescriptor", "SetSecurityDescriptorDacl"),
            
            # Shell32.dll
            ("ShellExecuteA", "SHGetFileInfoA", "SHGetFolderPathA", "SHFileOperationA")
        ]
        
        # Sélectionner un sous-ensemble aléatoire de DLLs
        num_dlls_to_select = min(random.randint(4, 8), len(legitimate_dlls))
        selected_dlls = random.sample(legitimate_dlls, num_dlls_to_select)
        
        # Pour chaque DLL, sélectionner des fonctions
        import_table = {}
        for dll in selected_dlls:
            # Déterminer l'index des fonctions à utiliser, avec une valeur par défaut sécurisée
            dll_index = legitimate_dlls.index(dll) if dll in legitimate_dlls[:len(legitimate_functions)] else 0
            
            # S'assurer que l'index est dans les limites
            if dll_index >= len(legitimate_functions):
                dll_index = 0
                
            # Récupérer les fonctions disponibles pour cette DLL
            available_functions = legitimate_functions[dll_index]
            
            # Calculer combien de fonctions nous pouvons sélectionner en toute sécurité
            max_functions = len(available_functions)
            num_functions_to_select = min(random.randint(3, 8), max_functions)
            
            # Sélectionner les fonctions
            if num_functions_to_select > 0:
                functions = random.sample(available_functions, num_functions_to_select)
                import_table[dll] = functions
    
        return import_table
    
    @staticmethod
    def add_dummy_sections(pe_data, sections_count=2):
        """Ajoute des sections factices à un fichier PE (simulation)."""
        # Cette fonction est une simulation - dans un vrai scénario, il faudrait
        # modifier le fichier PE avec des bibliothèques comme pefile
        
        section_names = [
            ".rdata", ".data", ".rsrc", ".reloc", ".text2", 
            ".idata", ".didat", ".tls", ".CRT", ".bss"
        ]
        
        # Sélectionner des noms de sections uniques
        selected_names = random.sample(section_names, min(sections_count, len(section_names)))
        
        # Générer des caractéristiques de section aléatoires pour chaque section
        dummy_sections = []
        for name in selected_names:
            section = {
                'name': name,
                'virtual_size': random.randint(4096, 16384),
                'virtual_address': random.randint(4096, 65536),
                'characteristics': random.randint(0x40000000, 0x50000000)  # Caractéristiques typiques
            }
            dummy_sections.append(section)
        
        return dummy_sections
    
    @staticmethod
    def add_legitimate_version_info():
        """Crée des informations de version légitimes (simulation)."""
        company_names = [
            "Microsoft Corporation",
            "Windows System Components",
            "Microsoft Windows",
            "Windows Security"
        ]
        
        product_names = [
            "Windows Update Assistant",
            "Windows Security Update",
            "System Component Manager",
            "Microsoft Compatibility Framework"
        ]
        
        descriptions = [
            "Updates critical system components",
            "Maintains system security and stability",
            "Windows System Management Tool",
            "System Component Configuration"
        ]
        
        # Générer des numéros de version qui ressemblent à ceux de Windows
        major = random.randint(10, 11)
        minor = 0
        build = random.randint(19041, 22000)
        private = random.randint(100, 999)
        
        version_info = {
            'CompanyName': random.choice(company_names),
            'ProductName': random.choice(product_names),
            'FileDescription': random.choice(descriptions),
            'FileVersion': f"{major}.{minor}.{build}.{private}",
            'ProductVersion': f"{major}.{minor}.{build}.{private}",
            'InternalName': f"update_{build}",
            'OriginalFilename': "SystemUpdate.exe",
            'LegalCopyright': f"© Microsoft Corporation. All rights reserved.",
            'Language': "English (United States)"
        }
        
        return version_info
    
    @staticmethod
    def add_legitimate_export_functions(count=3):
        """Ajoute des fonctions d'exportation légitimes (simulation)."""
        legitimate_export_names = [
            "Initialize",
            "Update",
            "GetVersion",
            "Configure",
            "CheckCompatibility",
            "InstallUpdate",
            "VerifySystem",
            "SetupEnvironment",
            "ValidateComponents",
            "RegisterService"
        ]
        
        # Sélectionner un sous-ensemble aléatoire
        if count > len(legitimate_export_names):
            count = len(legitimate_export_names)
        
        export_functions = random.sample(legitimate_export_names, count)
        
        # Ajouter des ordinals aléatoires
        exports = []
        for i, name in enumerate(export_functions):
            exports.append({
                'name': name,
                'ordinal': i + 1,
                'address': 0x1000 + (i * 0x100)  # Adresse factice
            })
        
        return exports
    
    @staticmethod
    def modify_binary_headers(original_file, output_file):
        """Modifie les en-têtes du fichier binaire (simulation)."""
        print(f"[+] Modification des en-têtes du fichier binaire {original_file}...")
        
        # Dans un scénario réel, cette fonction utiliserait une bibliothèque comme pefile
        # pour modifier les en-têtes PE. Cette implémentation est une simulation.
        
        # Créer une copie du fichier original
        with open(original_file, 'rb') as f_in:
            data = f_in.read()
        
        # Générer des ressources factices
        resources = BinaryMorphing.create_dummy_resources()
        print(f"[+] Ajout de {len(resources)} ressources factices")
        
        # Générer une table d'importation factice
        import_table = BinaryMorphing.create_dummy_import_table()
        dlls_count = len(import_table)
        functions_count = sum(len(funcs) for funcs in import_table.values())
        print(f"[+] Ajout d'une table d'importation avec {dlls_count} DLLs et {functions_count} fonctions")
        
        # Générer des sections PE factices
        sections = BinaryMorphing.add_dummy_sections(data)
        print(f"[+] Ajout de {len(sections)} sections PE factices")
        
        # Générer les informations de version
        version_info = BinaryMorphing.add_legitimate_version_info()
        print(f"[+] Configuration des informations de version: {version_info['ProductName']} {version_info['FileVersion']}")
        
        # Ajouter des fonctions d'exportation
        exports = BinaryMorphing.add_legitimate_export_functions()
        print(f"[+] Ajout de {len(exports)} fonctions d'exportation")
        
        # Écrire le fichier modifié (dans un scénario réel, les modifications seraient appliquées)
        with open(output_file, 'wb') as f_out:
            f_out.write(data)
        
        # Simuler un délai pour le traitement
        time.sleep(2)
        
        print(f"[+] Modifications des en-têtes terminées: {output_file}")
        return True
    
    @staticmethod
    def apply_all_techniques(input_file, output_file):
        """Applique toutes les techniques de morphing binaire."""
        print("\n[+] Application des techniques de morphing binaire avancées...")
        
        # Vérifier que le fichier existe
        if not os.path.exists(input_file):
            print(f"[-] Fichier d'entrée non trouvé: {input_file}")
            return False
        
        # Appliquer les modifications d'en-têtes binaires
        success = BinaryMorphing.modify_binary_headers(input_file, output_file)
        
        return success