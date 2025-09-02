"""
Verificador e Instalador de Drivers USB para HS3
═══════════════════════════════════════════════════════════════════

Este script verifica se todos os drivers necessários para o HS3 estão instalados
e fornece instruções para instalação se necessário.
"""

import subprocess
import sys
import os
import winreg
from typing import List, Tuple, Dict

def check_pyusb_backends():
    """Verifica se os backends USB estão disponíveis"""
    print("🔍 Verificando backends USB...")
    
    try:
        import usb.backend.libusb1
        import usb.backend.libusb0
        import usb.backend.openusb
        
        # Verificar libusb
        backend_libusb1 = usb.backend.libusb1.get_backend()
        backend_libusb0 = usb.backend.libusb0.get_backend()
        backend_openusb = usb.backend.openusb.get_backend()
        
        print(f"  ✅ libusb-1.0: {'Disponível' if backend_libusb1 else 'Não disponível'}")
        print(f"  ✅ libusb-0.1: {'Disponível' if backend_libusb0 else 'Não disponível'}")
        print(f"  ✅ OpenUSB: {'Disponível' if backend_openusb else 'Não disponível'}")
        
        if backend_libusb1 or backend_libusb0:
            return True
        else:
            print("  ❌ Nenhum backend USB funcional encontrado!")
            return False
            
    except ImportError as e:
        print(f"  ❌ Erro ao importar backends: {e}")
        return False

def check_windows_usb_drivers():
    """Verifica drivers USB do Windows"""
    print("\n🔍 Verificando drivers USB do Windows...")
    
    try:
        # Verificar se o Windows USB driver está funcionando
        result = subprocess.run([
            'powershell', '-Command', 
            'Get-PnpDevice | Where-Object {$_.Class -eq "USB"} | Measure-Object'
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("  ✅ Drivers USB básicos do Windows: OK")
            return True
        else:
            print("  ❌ Problema com drivers USB do Windows")
            return False
            
    except Exception as e:
        print(f"  ❌ Erro ao verificar drivers: {e}")
        return False

def check_libusb_installation():
    """Verifica se libusb está instalado no sistema"""
    print("\n🔍 Verificando instalação do libusb...")
    
    # Locais comuns onde libusb pode estar
    common_paths = [
        "C:\\Windows\\System32\\libusb-1.0.dll",
        "C:\\Windows\\SysWOW64\\libusb-1.0.dll",
        os.path.join(os.path.dirname(sys.executable), "libusb-1.0.dll"),
        os.path.join(os.path.dirname(sys.executable), "DLLs", "libusb-1.0.dll"),
    ]
    
    found = False
    for path in common_paths:
        if os.path.exists(path):
            print(f"  ✅ Encontrado: {path}")
            found = True
    
    if not found:
        print("  ❌ libusb-1.0.dll não encontrado no sistema")
        return False
    
    return True

def install_libusb_windows():
    """Instala libusb no Windows"""
    print("\n📦 Instalando libusb para Windows...")
    
    try:
        # Tentar instalar via pip primeiro
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install', 'libusb1'
        ], check=True, capture_output=True, text=True)
        
        print("  ✅ libusb1 instalado via pip")
        
        # Verificar se precisa baixar DLL separadamente
        import libusb1
        print("  ✅ libusb1 Python package importado com sucesso")
        
        return True
        
    except subprocess.CalledProcessError:
        print("  ❌ Falha ao instalar libusb1 via pip")
        return False
    except ImportError:
        print("  ❌ libusb1 instalado mas não pode ser importado")
        return False

def download_libusb_dll():
    """Baixa e instala DLL do libusb"""
    print("\n⬇️ Baixando libusb DLL...")
    
    try:
        import requests
        
        # URL da DLL do libusb (versão oficial)
        dll_url = "https://github.com/libusb/libusb/releases/download/v1.0.26/libusb-1.0.26-binaries.7z"
        
        print("  ⚠️ Para instalar libusb manualmente:")
        print(f"  1. Baixe: {dll_url}")
        print("  2. Extraia libusb-1.0.dll para C:\\Windows\\System32\\")
        print("  3. Para sistemas 64-bit, copie também para C:\\Windows\\SysWOW64\\")
        
        return False  # Retorna False pois requer instalação manual
        
    except ImportError:
        print("  ❌ requests não disponível para download automático")
        return False

def check_serial_drivers():
    """Verifica drivers de porta série"""
    print("\n🔍 Verificando drivers de porta série...")
    
    try:
        import serial.tools.list_ports
        
        ports = list(serial.tools.list_ports.comports())
        print(f"  ✅ Portas série disponíveis: {len(ports)}")
        
        for port in ports:
            print(f"    - {port.device}: {port.description}")
        
        return len(ports) > 0
        
    except ImportError:
        print("  ❌ pyserial não disponível")
        return False

def check_hs3_specific_requirements():
    """Verifica requisitos específicos do HS3"""
    print("\n🔍 Verificando requisitos específicos do HS3...")
    
    requirements = {
        "numpy": "Cálculos numéricos",
        "scipy": "Processamento de sinais", 
        "sounddevice": "Interface de áudio",
        "PyQt6": "Interface gráfica",
        "serial": "Comunicação série",
        "usb": "Comunicação USB"
    }
    
    missing = []
    
    for package, description in requirements.items():
        try:
            __import__(package)
            print(f"  ✅ {package}: {description}")
        except ImportError:
            print(f"  ❌ {package}: {description} - NÃO INSTALADO")
            missing.append(package)
    
    return missing

def install_missing_packages(packages: List[str]):
    """Instala pacotes em falta"""
    if not packages:
        return True
        
    print(f"\n📦 Instalando pacotes em falta: {', '.join(packages)}")
    
    try:
        result = subprocess.run([
            sys.executable, '-m', 'pip', 'install'] + packages,
            check=True, capture_output=True, text=True
        )
        
        print("  ✅ Todos os pacotes instalados com sucesso")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Erro ao instalar pacotes: {e}")
        return False

def generate_driver_report():
    """Gera relatório completo do estado dos drivers"""
    print("\n" + "="*60)
    print("  RELATÓRIO DE VERIFICAÇÃO DE DRIVERS HS3")
    print("="*60)
    
    # Verificações
    usb_backends_ok = check_pyusb_backends()
    windows_drivers_ok = check_windows_usb_drivers()
    libusb_ok = check_libusb_installation()
    serial_ok = check_serial_drivers()
    missing_packages = check_hs3_specific_requirements()
    
    print("\n" + "="*60)
    print("  RESUMO")
    print("="*60)
    
    # Status geral
    overall_status = (
        usb_backends_ok and 
        windows_drivers_ok and 
        libusb_ok and 
        serial_ok and 
        len(missing_packages) == 0
    )
    
    if overall_status:
        print("🟢 SISTEMA PRONTO PARA HS3")
        print("   Todos os drivers e dependências estão instalados.")
    else:
        print("🔴 SISTEMA NÃO ESTÁ PRONTO")
        print("   Algumas dependências precisam ser resolvidas:")
        
        if not usb_backends_ok:
            print("   ❌ Backends USB não funcionais")
        if not windows_drivers_ok:
            print("   ❌ Drivers USB do Windows com problemas")
        if not libusb_ok:
            print("   ❌ libusb não instalado")
        if not serial_ok:
            print("   ❌ Drivers de porta série com problemas")
        if missing_packages:
            print(f"   ❌ Pacotes em falta: {', '.join(missing_packages)}")
    
    print("\n" + "="*60)
    print("  AÇÕES RECOMENDADAS")
    print("="*60)
    
    if missing_packages:
        print("1. Instalar pacotes Python em falta:")
        print(f"   pip install {' '.join(missing_packages)}")
    
    if not libusb_ok:
        print("2. Instalar libusb:")
        print("   - Baixar de: https://libusb.info/")
        print("   - Ou executar: pip install libusb1")
    
    if not usb_backends_ok or not windows_drivers_ok:
        print("3. Verificar drivers USB:")
        print("   - Atualizar drivers via Device Manager")
        print("   - Reinstalar drivers USB se necessário")
    
    return overall_status

def auto_fix_issues():
    """Tenta corrigir automaticamente os problemas encontrados"""
    print("\n🔧 Tentando corrigir problemas automaticamente...")
    
    success = True
    
    # Instalar pacotes em falta
    missing_packages = check_hs3_specific_requirements()
    if missing_packages:
        success = install_missing_packages(missing_packages) and success
    
    # Tentar instalar libusb
    if not check_libusb_installation():
        success = install_libusb_windows() and success
    
    return success

def main():
    """Função principal"""
    print("HS3 Driver Checker & Installer")
    print("=" * 50)
    
    # Gerar relatório inicial
    system_ready = generate_driver_report()
    
    if not system_ready:
        print("\n🤔 Deseja tentar corrigir automaticamente? (s/n): ", end="")
        choice = input().lower().strip()
        
        if choice in ('s', 'sim', 'y', 'yes'):
            if auto_fix_issues():
                print("\n✅ Correções aplicadas! Execute novamente para verificar.")
            else:
                print("\n❌ Nem todos os problemas puderam ser corrigidos automaticamente.")
                print("   Siga as ações recomendadas acima.")
        else:
            print("\n💡 Siga as ações recomendadas para preparar o sistema.")
    
    print("\n🏁 Verificação concluída.")

if __name__ == "__main__":
    main()
