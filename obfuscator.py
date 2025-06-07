import base64
import random
import string
import re
import zlib
import ast
import tokenize
from io import BytesIO
import argparse

class CodeObfuscator:
    """Module d'obfuscation pour réduire la détection par signatures."""
    
    def __init__(self, options=None):
        """
        Initialise l'obfuscateur avec les options spécifiées.
        
        Options disponibles:
        - remove_comments: Supprime tous les commentaires du code
        - remove_docstrings: Supprime les docstrings (commentaires triple quotes)
        - obfuscate_strings_b64: Obfusque les chaînes avec encodage Base64
        - obfuscate_strings_xor: Obfusque les chaînes avec XOR
        """
        self.default_options = {
            'remove_comments': False,
            'remove_docstrings': False,
            'obfuscate_strings_b64': False,
            'obfuscate_strings_xor': False
        }
        
        # Si des options sont fournies, les utiliser, sinon utiliser les valeurs par défaut
        self.options = self.default_options.copy()
        if options:
            for key, value in options.items():
                if key in self.options:
                    self.options[key] = value
    
    @staticmethod
    def full_obfuscation(code):
        """Applique une obfuscation complète mais sûre."""
        # Créer un obfuscateur avec des options plus sûres
        obfuscator = CodeObfuscator({
            'remove_comments': True,
            'remove_docstrings': True,
            'obfuscate_strings_b64': True,  # Obfuscation des chaînes avec Base64
            'obfuscate_strings_xor': False  # Désactivé pour éviter les erreurs de syntaxe
        })
        
        # Étape 1: Obfuscation de base avec les options configurées
        obfuscated_code = obfuscator.obfuscate(code)
        
        # Vérifier que le code est syntaxiquement valide
        try:
            ast.parse(obfuscated_code)
        except SyntaxError:
            # En cas d'erreur, revenir au code original avec juste la suppression des commentaires
            print(f"[!] Erreur de syntaxe détectée, utilisation d'une obfuscation minimale.")
            obfuscator = CodeObfuscator({
                'remove_comments': True,
                'remove_docstrings': True,
                'obfuscate_strings_b64': False,
                'obfuscate_strings_xor': False
            })
            obfuscated_code = obfuscator.obfuscate(code)
        
        # Ajouter du code factice si c'est possible
        try:
            temp_code = obfuscator.add_junk_code(obfuscated_code)
            ast.parse(temp_code)  # Vérifier que l'ajout de code factice n'a pas introduit d'erreurs
            obfuscated_code = temp_code
        except:
            print(f"[!] Impossible d'ajouter du code factice, poursuite avec l'obfuscation de base.")
        
        return obfuscated_code

    @staticmethod
    def string_to_base64(input_string):
        """Convertit une chaîne en version encodée base64."""
        return base64.b64encode(input_string.encode()).decode()
    
    @staticmethod
    def base64_to_string(encoded_string):
        """Décode une chaîne base64."""
        return base64.b64decode(encoded_string.encode()).decode()
    
    @staticmethod
    def xor_encrypt(text, key=5):
        """Chiffre une chaîne avec XOR et une clé simple."""
        return ''.join(chr(ord(c) ^ key) for c in text)
    
    @staticmethod
    def generate_random_variable_name(length=8):
        """Génère un nom de variable aléatoire."""
        return '_' + ''.join(random.choices(string.ascii_lowercase, k=length))
    
    def remove_comments(self, code):
        """Supprime les commentaires du code sans affecter les chaînes."""
        # Préserver les chaînes
        string_placeholders = {}
        
        def replace_strings(match):
            placeholder = f"__STR_PLACEHOLDER_{len(string_placeholders)}__"
            string_placeholders[placeholder] = match.group(0)
            return placeholder
        
        # Remplacer temporairement les chaînes
        modified_code = re.sub(r'(["\'])((?:\\.|.)*?)\1', replace_strings, code)
        
        # Supprimer les commentaires de ligne
        modified_code = re.sub(r'#.*$', '', modified_code, flags=re.MULTILINE)
        
        # Restaurer les chaînes
        for placeholder, string_value in string_placeholders.items():
            modified_code = modified_code.replace(placeholder, string_value)
            
        return modified_code
    
    def remove_docstrings(self, code):
        """Supprime les docstrings (commentaires triples quotes) du code."""
        try:
            tree = ast.parse(code)
            
            class DocstringRemover(ast.NodeTransformer):
                class DocstringRemover(ast.NodeTransformer):
                    def visit_Module(self, node):
                        # Supprimer docstring du module
                        if (node.body and isinstance(node.body[0], ast.Expr) and 
                            isinstance(node.body[0].value, ast.Constant) and 
                            isinstance(node.body[0].value.value, str)):
                            node.body = node.body[1:]
                        return self.generic_visit(node)
                    
                    def visit_ClassDef(self, node):
                        # Supprimer docstring de classe
                        if (node.body and isinstance(node.body[0], ast.Expr) and 
                            isinstance(node.body[0].value, ast.Constant) and 
                            isinstance(node.body[0].value.value, str)):
                            node.body = node.body[1:]
                        return self.generic_visit(node)
                    
                    def visit_FunctionDef(self, node):
                        # Supprimer docstring de fonction
                        if (node.body and isinstance(node.body[0], ast.Expr) and 
                            isinstance(node.body[0].value, ast.Constant) and
                            isinstance(node.body[0].value.value, str)):
                            node.body = node.body[1:]
                        return self.generic_visit(node)
            
            # Appliquer la transformation et recompiler
            modified_tree = DocstringRemover().visit(tree)
            return ast.unparse(modified_tree)
        except:
            # Fallback en cas d'erreur avec ast.unparse (Python < 3.9)
            # ou autre souci d'analyse
            pattern = r'(\s*)("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')'
            return re.sub(pattern, '', code)
    
    def obfuscate_strings_base64(self, code):
        """Obfusque les chaînes de caractères avec encodage Base64."""
        return self._obfuscate_strings(code, method='base64')
    
    def obfuscate_strings_xor(self, code):
        """Obfusque les chaînes de caractères avec XOR."""
        return self._obfuscate_strings(code, method='xor')
    
    def _obfuscate_strings(self, code, method='base64'):
        """Méthode commune pour l'obfuscation des chaînes selon la méthode choisie."""
        # Vérifier d'abord si le code est syntaxiquement valide
        try:
            ast.parse(code)
        except SyntaxError:
            # Si le code n'est pas valide, le traiter ligne par ligne
            return self._obfuscate_strings_line_by_line(code, method)
        
        # Tokenizer le code pour identifier avec précision les chaînes
        tokens = []
        try:
            token_generator = tokenize.tokenize(BytesIO(code.encode('utf-8')).readline)
            tokens = list(token_generator)
        except tokenize.TokenError:
            # En cas d'erreur de tokenization, revenir au traitement ligne par ligne
            return self._obfuscate_strings_line_by_line(code, method)
        
        # Identifier les chaînes à obfusquer
        string_tokens = [(i, tok) for i, tok in enumerate(tokens) 
                         if tok.type == tokenize.STRING and 
                         not (tok.string.startswith('"""') or tok.string.startswith("'''"))]
        
        if not string_tokens:
            return code
        
        # Créer une liste des remplacements à faire
        replacements = []
        for i, tok in string_tokens:
            # Ignorer les chaînes dans les imports et les docstrings
            prev_tokens = [tokens[j].string for j in range(max(0, i-5), i)]
            if "import" in prev_tokens or "__" in tok.string:
                continue
            
            # Extraire la chaîne sans les guillemets
            # Gérer différents types de quotes
            string_val = tok.string
            if string_val.startswith(("'", '"')):
                string_val = string_val[1:-1]
            else:  # Pour les raw strings, bytes, etc.
                if string_val.startswith(('r', 'b', 'f')):
                    prefix = string_val[0]
                    string_val = string_val[2:-1]  # Enlever préfixe + quotes
                else:
                    continue  # Ignorer les cas complexes
            
            if len(string_val) <= 3:  # Ne pas obfusquer les chaînes courtes
                continue
            
            # Encoder la chaîne selon la méthode choisie
            if method == 'base64':
                encoded_string = self.string_to_base64(string_val)
                replacement = f"base64.b64decode('{encoded_string}'.encode()).decode()"
            elif method == 'xor':
                xor_key = random.randint(1, 10)
                encrypted = ''.join([chr(ord(c) ^ xor_key) for c in string_val])
                encoded_string = self.string_to_base64(encrypted)
                replacement = f"''.join([chr(ord(c) ^ {xor_key}) for c in base64.b64decode('{encoded_string}'.encode()).decode()])"
                
            replacements.append((tok.start[0], tok.start[1], tok.end[0], tok.end[1], replacement))
        
        # Appliquer les remplacements en commençant par la fin pour ne pas décaler les positions
        if not replacements:
            return code
            
        lines = code.split('\n')
        for line_start, col_start, line_end, col_end, replacement in sorted(replacements, reverse=True):
            # Cas simple : remplacement sur une seule ligne
            if line_start == line_end:
                line = lines[line_start-1]
                lines[line_start-1] = line[:col_start] + replacement + line[col_end:]
            else:
                # Cas multi-lignes (rare avec des chaînes simples)
                lines[line_start-1] = lines[line_start-1][:col_start] + replacement
                for i in range(line_start, line_end-1):
                    lines[i] = ""
                lines[line_end-1] = lines[line_end-1][col_end:]
        
        obfuscated_code = '\n'.join(lines)
        
        # Ajouter les imports nécessaires
        if "base64.b64decode" in obfuscated_code and "import base64" not in obfuscated_code:
            obfuscated_code = "import base64\n" + obfuscated_code
            
        # Vérifier que le code reste syntaxiquement valide
        try:
            ast.parse(obfuscated_code)
            return obfuscated_code
        except SyntaxError:
            # Si échoue, revenir au traitement ligne par ligne
            return self._obfuscate_strings_line_by_line(code, method)
    
    def _obfuscate_strings_line_by_line(self, code, method='base64'):
        """Traitement ligne par ligne pour l'obfuscation des chaînes."""
        lines = code.split('\n')
        processed_lines = []
        
        for line in lines:
            # Ignorer les lignes de commentaires
            if line.strip().startswith('#'):
                processed_lines.append(line)
                continue
                
            # Trouver toutes les chaînes dans la ligne
            string_pattern = re.compile(r'(?<![\\])(["\'])((?:.(?!(?<![\\])\1))*.?)\1')
            matches = list(string_pattern.finditer(line))
            
            if not matches:
                processed_lines.append(line)
                continue
                
            # Traiter chaque ligne individuellement pour préserver l'indentation
            current_line = line
            offset = 0
            
            for match in matches:
                # Ignorer certaines chaînes système
                if "import" in match.group() or "__" in match.group():
                    continue
                    
                # Ignorer les chaînes dans les commentaires
                line_before_match = current_line[:match.start() + offset]
                if '#' in line_before_match and line_before_match.find('#') < match.start() + offset:
                    continue
                    
                # Encoder la chaîne selon la méthode choisie
                original_string = match.group(2)
                if len(original_string) > 3:  # Ne pas obfusquer les chaînes trop courtes
                    if method == 'base64':
                        encoded_string = self.string_to_base64(original_string)
                        decode_expr = f"base64.b64decode('{encoded_string}'.encode()).decode()"
                    elif method == 'xor':
                        xor_key = random.randint(1, 10)
                        encrypted = ''.join([chr(ord(c) ^ xor_key) for c in original_string])
                        encoded_string = self.string_to_base64(encrypted)
                        decode_expr = f"''.join([chr(ord(c) ^ {xor_key}) for c in base64.b64decode('{encoded_string}'.encode()).decode()])"
                    
                    # Remplacer la chaîne originale
                    start = match.start() + offset
                    end = match.end() + offset
                    
                    current_line = current_line[:start] + decode_expr + current_line[end:]
                    
                    # Ajuster l'offset pour les remplacements futurs
                    offset += len(decode_expr) - (end - start)
            
            processed_lines.append(current_line)
        
        obfuscated_code = '\n'.join(processed_lines)
        
        # Ajouter les imports nécessaires
        if "base64.b64decode" in obfuscated_code and "import base64" not in obfuscated_code:
            obfuscated_code = "import base64\n" + obfuscated_code
            
        return obfuscated_code
    
    def rename_functions_and_variables(self, code):
        """Renomme les fonctions et variables en préservant la syntaxe Python."""
        # Identifier les mots réservés Python qui ne doivent pas être remplacés
        reserved_words = {
            'if', 'elif', 'else', 'for', 'while', 'def', 'class', 'try', 'except',
            'finally', 'with', 'as', 'import', 'from', 'return', 'yield', 'break',
            'continue', 'pass', 'True', 'False', 'None', 'and', 'or', 'not', 'is',
            'in', 'lambda', 'global', 'nonlocal', 'assert', 'del', 'raise', 'print',
            'input', 'open', 'range', 'len', 'str', 'int', 'float', 'list', 'dict',
            'set', 'tuple', 'sum', 'min', 'max', 'enumerate', 'zip', 'map', 'filter',
            'sorted', 'any', 'all', 'next', 'iter', 'hasattr', 'getattr', 'setattr'
        }
        
        # Essayer d'utiliser l'AST pour une analyse fiable si possible
        try:
            tree = ast.parse(code)
            name_map = {}
            
            # Parcourir l'AST pour identifier les noms à renommer
            for node in ast.walk(tree):
                # Fonctions
                if isinstance(node, ast.FunctionDef):
                    if (node.name not in reserved_words and not node.name.startswith('__') 
                            and node.name != 'main' and node.name not in name_map):
                        name_map[node.name] = self.generate_random_variable_name()
                
                # Variables
                elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if (node.id not in reserved_words and not node.id.startswith('__') 
                            and node.id != 'self' and node.id not in name_map):
                        name_map[node.id] = self.generate_random_variable_name()
            
            # Appliquer les remplacements
            for original_name, random_name in name_map.items():
                # Utiliser une regex avec des word boundaries pour éviter les remplacements partiels
                code = re.sub(r'\b' + re.escape(original_name) + r'\b', random_name, code)
                
            return code
            
        except SyntaxError:
            # Fallback en cas d'échec de l'analyse AST
            return self._rename_functions_and_variables_regex(code, reserved_words)
    
    def _rename_functions_and_variables_regex(self, code, reserved_words):
        """Utilise des regex pour renommer les fonctions et variables."""
        function_pattern = re.compile(r'def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(')
        variable_pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*')
        
        name_map = {}
        
        # Identifier les fonctions
        for match in function_pattern.finditer(code):
            original_name = match.group(1)
            if (original_name not in reserved_words and not original_name.startswith('__') 
                    and original_name != 'main' and original_name not in name_map):
                name_map[original_name] = self.generate_random_variable_name()
        
        # Identifier les variables
        for match in variable_pattern.finditer(code):
            original_name = match.group(1)
            if (original_name not in reserved_words and not original_name.startswith('__') 
                    and original_name != 'self' and original_name not in name_map):
                name_map[original_name] = self.generate_random_variable_name()
        
        # Appliquer les remplacements
        for original_name, random_name in name_map.items():
            code = re.sub(r'\b' + re.escape(original_name) + r'\b', random_name, code)
            
        return code
    
    def add_junk_code(self, code):
        """Ajoute du code inutilisé mais légitime pour perturber les signatures."""
        junk_functions = [
            """
def {0}():
    \"\"\"Fonction légitime pour l'analyse de configuration système.\"\"\"
    try:
        import platform
        info = platform.uname()
        return sum([len(i) for i in [info.system, info.node, info.release]])
    except:
        return 0
""",
            """
def {0}():
    \"\"\"Fonction utilitaire pour la gestion de fichiers.\"\"\"
    try:
        import os
        temp_dir = os.path.join(os.environ.get('TEMP', ''), 'logs')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        return os.path.abspath(temp_dir)
    except:
        return ""
""",
            """
def {0}():
    \"\"\"Fonction de vérification des mises à jour.\"\"\"
    try:
        import datetime
        now = datetime.datetime.now()
        expiration = datetime.datetime(now.year + 1, now.month, now.day)
        delta = expiration - now
        return delta.days > 30
    except:
        return True
"""
        ]
        
        # Trouver un endroit sûr pour insérer le code factice
        try:
            tree = ast.parse(code)
            
            # Trouver la dernière position des imports
            import_end_pos = 0
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    if hasattr(node, 'end_lineno'):
                        import_end_pos = max(import_end_pos, node.end_lineno)
                    else:
                        import_end_pos = max(import_end_pos, node.lineno)
            
            lines = code.split('\n')
            
            # Ajouter des fonctions factices après les imports
            added_junk = []
            for _ in range(3):
                func = random.choice(junk_functions)
                random_name = self.generate_random_variable_name()
                added_junk.extend(func.format(random_name).split('\n'))
            
            # Ajouter une condition factice à la fin
            condition_code = f"""
if False and {self.generate_random_variable_name()}():
    print("Application mise à jour avec succès.")
"""
            
            # Construire le code final
            result = lines[:import_end_pos] + added_junk + lines[import_end_pos:] + condition_code.split('\n')
            return '\n'.join(result)
            
        except SyntaxError:
            # Fallback simple: ajouter au début du fichier
            added_code = ""
            for _ in range(3):
                func = random.choice(junk_functions)
                random_name = self.generate_random_variable_name()
                added_code += func.format(random_name)
            
            condition_code = f"""
if False and {self.generate_random_variable_name()}():
    print("Application mise à jour avec succès.")
"""
            
            # Trouver la position des imports existants
            lines = code.split('\n')
            import_end = 0
            for i, line in enumerate(lines):
                if line.strip().startswith(('import ', 'from ')):
                    import_end = i + 1
            
            if import_end > 0:
                return '\n'.join(lines[:import_end]) + '\n' + added_code + '\n' + '\n'.join(lines[import_end:]) + condition_code
            else:
                return added_code + code + condition_code
    
    def fix_indentation(self, code):
        """Corrige les problèmes d'indentation en analysant les structures de contrôle."""
        lines = code.split('\n')
        result = []
        
        # Pile pour suivre les niveaux d'indentation
        indent_stack = [0]
        conditional_stack = []  # Pour suivre les structures if/elif/else
        
        i = 0
        while i < len(lines):
            line = lines[i].rstrip()
            
            # Ignorer les lignes vides
            if not line.strip():
                result.append(line)
                i += 1
                continue
                
            # Calculer l'indentation actuelle
            current_indent = len(line) - len(line.lstrip())
            content = line.strip()
            
            # Vérifier si cette ligne est une structure de contrôle
            is_control = False
            control_type = None
            
            if content.endswith(':'):
                if content.startswith('if '):
                    is_control = True
                    control_type = 'if'
                    conditional_stack.append((current_indent, 'if'))
                elif content.startswith('elif '):
                    is_control = True
                    control_type = 'elif'
                    # Trouver le 'if' correspondant et aligner l'indentation
                    for j in range(len(conditional_stack)-1, -1, -1):
                        if conditional_stack[j][1] in ('if', 'elif'):
                            current_indent = conditional_stack[j][0]
                            line = ' ' * current_indent + content
                            conditional_stack.append((current_indent, 'elif'))
                            break
                elif content == 'else:':
                    is_control = True
                    control_type = 'else'
                    # Trouver le 'if' correspondant et aligner l'indentation
                    for j in range(len(conditional_stack)-1, -1, -1):
                        if conditional_stack[j][1] in ('if', 'elif'):
                            current_indent = conditional_stack[j][0]
                            line = ' ' * current_indent + content
                            conditional_stack.append((current_indent, 'else'))
                            break
                elif any(content.startswith(kw) for kw in ('for ', 'while ', 'def ', 'class ', 'try:', 'except', 'with ')):
                    is_control = True
            
            # Ajuster la pile d'indentation en fonction de l'indentation actuelle
            while len(indent_stack) > 1 and current_indent < indent_stack[-1]:
                indent_stack.pop()
                
            # Ajouter le niveau d'indentation pour la prochaine ligne si c'est une structure de contrôle
            if is_control and content.endswith(':'):
                next_indent = current_indent + 4  # Python standard: 4 espaces
                indent_stack.append(next_indent)
                
                # Vérifier et corriger l'indentation de la ligne suivante
                if i + 1 < len(lines) and len(lines[i+1].strip()) > 0:
                    next_line = lines[i+1]
                    next_line_indent = len(next_line) - len(next_line.lstrip())
                    
                    # Si la ligne suivante n'est pas correctement indentée dans un bloc
                    if next_line_indent <= current_indent:
                        lines[i+1] = ' ' * next_indent + next_line.lstrip()
            
            result.append(line)
            i += 1
        
        return '\n'.join(result)
    
    def compress_code(self, code):
        """Compresse le code en utilisant zlib et l'encapsule dans un script d'exécution."""
        compressed = zlib.compress(code.encode())
        encoded = base64.b64encode(compressed).decode()
        
        # Créer un script qui décompresse et exécute le code
        loader_code = f"""
import base64
import zlib
import sys
import os

def _load_and_run():
    try:
        code = base64.b64decode("{encoded}")
        decompressed = zlib.decompress(code).decode()
        exec(decompressed)
    except Exception as e:
        sys.exit(1)

if __name__ == "__main__":
    _load_and_run()
"""
        return loader_code
    
    def validate_obfuscated_code(self, code):
        """Vérifie si le code obfusqué est syntaxiquement valide."""
        try:
            ast.parse(code)
            return True, code
        except SyntaxError as e:
            # Essayer de réparer automatiquement les problèmes courants
            print(f"Erreur de syntaxe détectée: {e}")
            
            # Réparer les problèmes d'indentation les plus courants
            fixed_code = self.fix_indentation(code)
            
            # Vérifier si la réparation a fonctionné
            try:
                ast.parse(fixed_code)
                print("Code réparé avec succès")
                return True, fixed_code
            except SyntaxError as e2:
                print(f"La réparation a échoué: {e2}")
                return False, code
    
    def obfuscate(self, code):
        """Applique les techniques d'obfuscation sélectionnées avec validation syntaxique."""
        # Étape 0: Vérifier que le code de départ est valide
        try:
            ast.parse(code)
        except SyntaxError as e:
            print(f"Le code source contient une erreur de syntaxe: {e}")
            return code
        
        # Sauvegarder le code original
        current_code = code
        
        # Étape 1: Supprimer les commentaires si demandé
        if self.options['remove_comments']:
            temp_code = self.remove_comments(current_code)
            valid, temp_code = self.validate_obfuscated_code(temp_code)
            if valid:
                current_code = temp_code
            else:
                print("Erreur lors de la suppression des commentaires")
        
        # Étape 2: Supprimer les docstrings si demandé
        if self.options['remove_docstrings']:
            temp_code = self.remove_docstrings(current_code)
            valid, temp_code = self.validate_obfuscated_code(temp_code)
            if valid:
                current_code = temp_code
            else:
                print("Erreur lors de la suppression des docstrings")
        
        # Étape 4: Obfusquer les chaînes avec Base64 si demandé
        if self.options['obfuscate_strings_b64']:
            temp_code = self.obfuscate_strings_base64(current_code)
            valid, temp_code = self.validate_obfuscated_code(temp_code)
            if valid:
                current_code = temp_code
            else:
                print("Erreur lors de l'obfuscation des chaînes avec Base64")
        
        # Étape 5: Obfusquer les chaînes avec XOR si demandé
        if self.options['obfuscate_strings_xor']:
            temp_code = self.obfuscate_strings_xor(current_code)
            valid, temp_code = self.validate_obfuscated_code(temp_code)
            if valid:
                current_code = temp_code
            else:
                print("Erreur lors de l'obfuscation des chaînes avec XOR")
        
        # Étape 7: Correction finale de l'indentation
        current_code = self.fix_indentation(current_code)
        
        # Vérification finale
        valid, current_code = self.validate_obfuscated_code(current_code)
        if not valid:
            print("Échec de la vérification finale")
            return code
        
        # Ajout de cette ligne pour retourner le code obfusqué
        return current_code

def main():
    parser = argparse.ArgumentParser(description='Obfuscateur de code Python avec options personnalisables')
    parser.add_argument('input_file', help='Fichier Python à obfusquer')
    parser.add_argument('--output', '-o', help='Fichier de sortie (par défaut: [nom_fichier]_obf.py)')
    parser.add_argument('--remove-comments', '-rc', action='store_true', help='Supprimer les commentaires')
    parser.add_argument('--remove-docstrings', '-rd', action='store_true', help='Supprimer les docstrings (commentaires triple quotes)')
    parser.add_argument('--obfuscate-b64', '-b64', action='store_true', help='Obfusquer les chaînes avec encodage Base64')
    parser.add_argument('--obfuscate-xor', '-xor', action='store_true', help='Obfusquer les chaînes avec XOR')
    parser.add_argument('--all', '-a', action='store_true', help='Appliquer toutes les techniques d\'obfuscation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Mode verbeux (affiche plus de détails)')
    
    args = parser.parse_args()
    verbose = args.verbose
    
    if verbose:
        print(f"Démarrage de l'obfuscation pour le fichier: {args.input_file}")
    
    # Déterminer le fichier de sortie
    if args.output:
        output_file = args.output
    else:
        file_name, file_ext = os.path.splitext(args.input_file)
        output_file = f"{file_name}_obf{file_ext}"
    
    if verbose:
        print(f"Fichier de sortie: {output_file}")
    
    # Définir les options d'obfuscation
    options = {
        'remove_comments': args.remove_comments or args.all,
        'remove_docstrings': args.remove_docstrings or args.all,
        'obfuscate_strings_b64': args.obfuscate_b64 or args.all,
        'obfuscate_strings_xor': args.obfuscate_xor or args.all
    }
    
    if verbose:
        print("Options d'obfuscation sélectionnées:")
        for key, value in options.items():
            if value:
                print(f"- {key}: Activé")
    
    # Vérifier qu'au moins une option est activée
    if not any(options.values()):
        print("ATTENTION: Aucune technique d'obfuscation n'a été sélectionnée. Le code ne sera pas modifié.")
        print("Utilisez une ou plusieurs options comme --obfuscate-b64, --remove-comments, etc.")
        print("Pour voir toutes les options: python obfuscator.py --help")
        return
    
    try:
        print(f"Lecture du fichier source: {args.input_file}")
        # Lire le fichier source
        with open(args.input_file, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        print(f"Taille du code source: {len(source_code)} caractères")
        
        # Créer l'obfuscateur avec les options spécifiées
        print("Initialisation de l'obfuscateur...")
        obfuscator = CodeObfuscator(options)
        
        # Obfusquer le code
        print("Obfuscation en cours...")
        obfuscated_code = obfuscator.obfuscate(source_code)
        
        print(f"Taille du code obfusqué: {len(obfuscated_code)} caractères")
        
        # Écrire le résultat dans le fichier de sortie
        print(f"Écriture du résultat dans {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(obfuscated_code)
        
        print(f"Obfuscation terminée avec succès. Résultat écrit dans '{output_file}'")
        
        # Afficher les techniques appliquées
        applied_techniques = [key for key, value in options.items() if value]
        if applied_techniques:
            print("Techniques d'obfuscation appliquées:")
            for technique in applied_techniques:
                print(f"- {technique}")
            
    except FileNotFoundError:
        print(f"ERREUR: Le fichier '{args.input_file}' n'a pas été trouvé.")
    except PermissionError:
        print(f"ERREUR: Permission refusée pour l'accès au fichier '{args.input_file}' ou '{output_file}'.")
    except Exception as e:
        print(f"ERREUR critique lors de l'obfuscation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import os
    print("CodeObfuscator - Outil d'obfuscation Python")
    print("===========================================")
    main()
    print("\nTerminé.")