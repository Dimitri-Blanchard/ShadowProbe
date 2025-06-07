import os
import base64
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class Encryptor:
    """Gère le chiffrement et le déchiffrement des fichiers."""
    
    def __init__(self, settings):
        """Initialise le module de chiffrement avec les paramètres de l'application."""
        self.settings = settings
        self.salt = self._generate_salt()
        self.key = self._derive_key()
        self.cipher = Fernet(self.key)
        
    def _generate_salt(self):
        """Génère un sel unique pour la dérivation de clé."""
        # Utiliser un sel fixe pour garantir la cohérence entre les exécutions
        fixed_salt = "SECUREpersistenceKEY2025"
        
        # Combiner avec des informations du système qui sont moins susceptibles de changer
        hostname = os.environ.get('COMPUTERNAME', '')
        username = os.environ.get('USERNAME', '')
        
        # Créer un sel stable
        seed = fixed_salt + hostname + username
        
        # Hacher pour obtenir un sel fixe
        return hashlib.sha256(seed.encode()).digest()[:16]
    
    def _derive_key(self):
        """Dérive une clé de chiffrement à partir du salt et d'une passphrase."""
        # Utiliser une passphrase fixe combinée avec le nom du service
        fixed_passphrase = "FERNETsecureKEY2025"
        passphrase = fixed_passphrase + self.settings.service_name
        
        # Dériver la clé avec PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        
        # Générer et formater la clé pour Fernet
        return base64.urlsafe_b64encode(kdf.derive(passphrase.encode()))
    
    def encrypt_file(self, file_path):
        """Chiffre un fichier et remplace l'original."""
        try:
            if not os.path.exists(file_path):
                return False
                
            # Lire le contenu
            with open(file_path, 'rb') as f:
                data = f.read()
                
            # Chiffrer
            encrypted_data = self.cipher.encrypt(data)
            
            # Écrire le fichier chiffré
            with open(file_path, 'wb') as f:
                f.write(encrypted_data)
                
            return True
        except Exception as e:
            print(f"[-] Erreur de chiffrement: {e}")
            return False
    
    def decrypt_file(self, file_path):
        """Déchiffre un fichier et retourne le contenu."""
        try:
            if not os.path.exists(file_path):
                return None
                
            # Lire le contenu chiffré
            with open(file_path, 'rb') as f:
                encrypted_data = f.read()
            
            try:
                # Essayer de déchiffrer
                decrypted_data = self.cipher.decrypt(encrypted_data)
                return decrypted_data
            except Exception as decrypt_error:
                print(f"[-] Erreur lors du déchiffrement: {decrypt_error}")
                # Si le déchiffrement échoue, retourner les données brutes
                # Cela permet au programme de continuer même si le fichier n'est pas chiffré
                if len(encrypted_data) > 0:
                    print("[!] Retour du contenu brut puisque le déchiffrement a échoué")
                    return encrypted_data
                return None
                
        except Exception as e:
            print(f"[-] Erreur d'accès au fichier: {e}")
            return None
            
    def decrypt_to_file(self, encrypted_path, output_path):
        """Déchiffre un fichier et enregistre le résultat."""
        decrypted_data = self.decrypt_file(encrypted_path)
        if decrypted_data:
            try:
                with open(output_path, 'wb') as f:
                    f.write(decrypted_data)
                return True
            except Exception as e:
                print(f"[-] Erreur d'écriture du fichier déchiffré: {e}")
        return False