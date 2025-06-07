# ShadowProbe – Les vecteurs d’évasion sous Windows

## ⚠️ Avertissement

> Ce projet est une **preuve éducative** visant à démontrer certains mécanismes par lesquels des logiciels malveillants peuvent tenter d’échapper à la détection ou d’exploiter des systèmes Windows.  
> **Il ne doit en aucun cas être utilisé à des fins malveillantes.**

---

## 🎯 Objectif

ShadowProbe explore différents vecteurs techniques utilisés par des logiciels malveillants :
- Elévation de privilèges
- Persistance système (via WMI, clés de registre, tâches planifiées)
- Techniques de dissimulation (désactivation ou contournement de certaines protections)
- Obfuscation de code et transformation binaire
- Injections de DLL ou manipulation de processus
- Analyse de comportements par morphing et chiffrement de charge utile

Ce projet a été créé dans un but **strictement pédagogique et de recherche**, pour sensibiliser sur :
- Les limites des outils de protection traditionnels (comme Windows Defender)
- La nécessité d’une défense en profondeur
- L’évolution des tactiques de malware modernes

---

## 📁 Structure du projet

| Fichier            | Description |
|--------------------|-------------|
| `main.py`          | Point d’entrée principal |
| `admin.py`         | Gestion des droits d’administrateur |
| `binary_morph.py`  | Morphing de binaire pour évasion AV |
| `obf.py`           | Techniques d’obfuscation |
| `crypto.py`        | Chiffrement/déchiffrement de payload |
| `dll.py`           | Injection ou manipulation de DLL |
| `persist.py`       | Persistance via registre, WMI, etc. |
| `wmi.py`           | Intégration avec Windows Management Instrumentation |
| `stealth.py`       | Techniques d’évasion |
| `build.py`         | Script de génération de charge utile |
| `REMOVE.py`        | Permet de supprimez le malware d'une machine |

---

## 🔐 Public visé

- Étudiants en cybersécurité
- Chercheurs en sécurité offensive
- Analystes malware
- Développeurs d’antivirus ou EDR

---

## 📚 Ressources complémentaires

- [Malware Techniques - MITRE ATT&CK](https://attack.mitre.org/)
- [Windows Defender Architecture (Microsoft)](https://learn.microsoft.com/en-us/microsoft-365/security/defender-endpoint/microsoft-defender-antivirus)
- [Offensive Security Certified Professional (OSCP)](https://www.offensive-security.com/pwk-oscp/)

---

## 📜 Licence

Ce projet est fourni uniquement à des fins éducatives.  
**Toute utilisation illégale ou non éthique est strictement interdite.**
