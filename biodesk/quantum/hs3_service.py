"""
Serviço HS3 - TiePie Handyscope HS3
═══════════════════════════════════════════════════════════════════════

Classe HS3Service para gerir o TiePie Handyscope HS3 como gerador (AWG) 
e osciloscópio (stream).

NUNCA simula hardware - sem hardware real => erro claro.
Todas as operações são validadas pelo sistema de segurança.
"""

import os
import time
import logging
import numpy as np
from typing import Literal, Tuple, Optional
from dataclasses import dataclass

# Importar LibTiePie se disponível
try:
    import libtiepie
    LIBTIEPIE_AVAILABLE = True
except ImportError:
    LIBTIEPIE_AVAILABLE = False
    libtiepie = None

# Importar sistema de segurança local
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from safety_manager import SafetyManager

class HS3NotFoundError(Exception):
    """Erro quando o HS3 não é encontrado"""
    pass

class HS3SafetyError(Exception):
    """Erro de segurança do HS3"""
    pass

@dataclass
class HS3DeviceInfo:
    """Informações do dispositivo HS3"""
    serial_number: str
    name: str
    version: str
    channels_awg: int
    channels_scope: int

class HS3Service:
    """
    Serviço principal para controlo do TiePie Handyscope HS3
    
    Funcionalidades:
    - Gerador de sinais (AWG) com validação de segurança
    - Osciloscópio (stream) para aquisição de dados
    - Validação rigorosa de todos os parâmetros
    - Integração com sistema de segurança Biodesk
    """
    
    def __init__(self):
        """Inicializa o serviço HS3"""
        self.logger = logging.getLogger("HS3Service")
        self.safety_manager = SafetyManager()
        
        # Estado do dispositivo
        self.device = None
        self.generator = None
        self.oscilloscope = None
        self.is_connected = False
        self.device_info: Optional[HS3DeviceInfo] = None
        
        # Estado do gerador
        self.is_generating = False
        self.current_frequency = 0.0
        self.current_amplitude = 0.0
        self.current_offset = 0.0
        
        # Estado do osciloscópio
        self.is_streaming = False
        self.stream_sample_rate = 0.0
        
        # Verificar disponibilidade da LibTiePie
        if not LIBTIEPIE_AVAILABLE:
            raise HS3NotFoundError(
                "LibTiePie não disponível. Instale: pip install libtiepie"
            )
    
    def open(self) -> None:
        """
        Abre conexão com o HS3
        
        Raises:
            HS3NotFoundError: Se o dispositivo não for encontrado
        """
        try:
            self.logger.info("🔌 A procurar dispositivo HS3...")
            
            # Inicializar LibTiePie
            libtiepie.network.auto_detect_enabled = True
            libtiepie.device_list.update()
            
            # Procurar HS3
            device_count = libtiepie.device_list.count
            if device_count == 0:
                raise HS3NotFoundError(
                    "Nenhum dispositivo TiePie encontrado. "
                    "Verifique se o HS3 está conectado e ligado."
                )
            
            # Abrir primeiro dispositivo HS3 encontrado
            device_found = False
            for i in range(device_count):
                if libtiepie.device_list.get_product_id(i) == libtiepie.PRODUCTID.HS3:
                    self.device = libtiepie.device_list.create_device(i)
                    device_found = True
                    break
            
            if not device_found:
                raise HS3NotFoundError(
                    f"HS3 não encontrado entre {device_count} dispositivos TiePie. "
                    "Verifique se é um Handyscope HS3."
                )
            
            # Obter informações do dispositivo
            self.device_info = HS3DeviceInfo(
                serial_number=self.device.serial_number,
                name=self.device.name,
                version=str(self.device.driver_version),
                channels_awg=self.device.generator.channel_count if hasattr(self.device, 'generator') else 0,
                channels_scope=self.device.oscilloscope.channel_count if hasattr(self.device, 'oscilloscope') else 0
            )
            
            # Configurar gerador (AWG)
            if hasattr(self.device, 'generator') and self.device.generator.channel_count > 0:
                self.generator = self.device.generator
                # Configurar canal 1 do gerador
                self.generator.channels[0].enabled = True
            else:
                raise HS3NotFoundError("HS3 não tem capacidades de gerador (AWG)")
            
            # Configurar osciloscópio
            if hasattr(self.device, 'oscilloscope') and self.device.oscilloscope.channel_count >= 2:
                self.oscilloscope = self.device.oscilloscope
                # Configurar 2 canais (CH1: shunt, CH2: paciente)
                for i in range(2):
                    self.oscilloscope.channels[i].enabled = True
                    self.oscilloscope.channels[i].coupling = libtiepie.CK_DCV  # DC coupling
            else:
                raise HS3NotFoundError("HS3 não tem pelo menos 2 canais de osciloscópio")
            
            self.is_connected = True
            self.logger.info(f"✅ HS3 conectado: {self.device_info.name} (SN: {self.device_info.serial_number})")
            
        except Exception as e:
            self.is_connected = False
            if isinstance(e, HS3NotFoundError):
                raise
            else:
                raise HS3NotFoundError(f"Erro ao conectar HS3: {e}")
    
    def close(self) -> None:
        """Fecha conexão com o HS3"""
        try:
            if self.is_generating:
                self.stop_output()
            
            if self.is_streaming:
                self.stop_stream()
            
            if self.device:
                self.device.close()
                self.device = None
            
            self.generator = None
            self.oscilloscope = None
            self.is_connected = False
            self.device_info = None
            
            self.logger.info("🔌 HS3 desconectado")
            
        except Exception as e:
            self.logger.error(f"Erro ao desconectar HS3: {e}")
    
    def is_connected(self) -> bool:
        """Verifica se o HS3 está conectado"""
        return self.is_connected and self.device is not None
    
    def configure_generator(self, 
                          signal_type: Literal["sine", "square", "triangle", "arb"],
                          amplitude_vpp: float, 
                          offset_v: float) -> None:
        """
        Configura o gerador de sinais
        
        Args:
            signal_type: Tipo de sinal (sine, square, triangle, arb)
            amplitude_vpp: Amplitude pico-a-pico em volts
            offset_v: Offset DC em volts
            
        Raises:
            HS3NotFoundError: Se não estiver conectado
            HS3SafetyError: Se os parâmetros não passarem validação de segurança
        """
        if not self.is_connected:
            raise HS3NotFoundError("HS3 não está conectado")
        
        # Validação de segurança OBRIGATÓRIA
        is_safe, safety_msg = self.safety_manager.validate_parameters_before_start(
            frequency=self.current_frequency,  # Usa frequência atual
            amplitude=amplitude_vpp,
            offset=offset_v
        )
        
        if not is_safe:
            raise HS3SafetyError(f"Parâmetros rejeitados pelo sistema de segurança: {safety_msg}")
        
        try:
            gen_ch = self.generator.channels[0]
            
            # Configurar tipo de sinal
            if signal_type == "sine":
                gen_ch.signal_type = libtiepie.ST_SINE
            elif signal_type == "square":
                gen_ch.signal_type = libtiepie.ST_SQUARE
            elif signal_type == "triangle":
                gen_ch.signal_type = libtiepie.ST_TRIANGLE
            elif signal_type == "arb":
                gen_ch.signal_type = libtiepie.ST_ARBITRARY
            else:
                raise ValueError(f"Tipo de sinal inválido: {signal_type}")
            
            # Configurar amplitude e offset com ramp suave
            self.soft_ramp(gen_ch, "amplitude", amplitude_vpp)
            self.soft_ramp(gen_ch, "offset", offset_v)
            
            self.current_amplitude = amplitude_vpp
            self.current_offset = offset_v
            
            self.logger.info(
                f"🎛️ Gerador configurado: {signal_type}, "
                f"Amplitude: {amplitude_vpp:.3f}V, Offset: {offset_v:.3f}V"
            )
            
        except Exception as e:
            raise HS3NotFoundError(f"Erro ao configurar gerador: {e}")
    
    def set_frequency(self, freq_hz: float) -> None:
        """
        Define a frequência do gerador
        
        Args:
            freq_hz: Frequência em Hz
            
        Raises:
            HS3NotFoundError: Se não estiver conectado
            HS3SafetyError: Se a frequência não passar validação de segurança
        """
        if not self.is_connected:
            raise HS3NotFoundError("HS3 não está conectado")
        
        # Validação de segurança
        is_safe, safety_msg = self.safety_manager.validate_parameters_before_start(
            frequency=freq_hz,
            amplitude=self.current_amplitude,
            offset=self.current_offset
        )
        
        if not is_safe:
            raise HS3SafetyError(f"Frequência rejeitada pelo sistema de segurança: {safety_msg}")
        
        try:
            gen_ch = self.generator.channels[0]
            gen_ch.frequency = freq_hz
            self.current_frequency = freq_hz
            
            self.logger.info(f"🔊 Frequência definida: {freq_hz:.2f} Hz")
            
        except Exception as e:
            raise HS3NotFoundError(f"Erro ao definir frequência: {e}")
    
    def start_output(self) -> None:
        """Inicia saída do gerador"""
        if not self.is_connected:
            raise HS3NotFoundError("HS3 não está conectado")
        
        try:
            self.generator.start()
            self.is_generating = True
            self.logger.info("▶️ Gerador iniciado")
            
        except Exception as e:
            raise HS3NotFoundError(f"Erro ao iniciar gerador: {e}")
    
    def stop_output(self) -> None:
        """Para saída do gerador"""
        if not self.is_connected:
            return
        
        try:
            if self.generator:
                self.generator.stop()
            self.is_generating = False
            self.logger.info("⏹️ Gerador parado")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar gerador: {e}")
    
    def set_burst_by_cycles(self, cycles: int) -> None:
        """
        Configura modo burst por número de ciclos
        
        Args:
            cycles: Número de ciclos do burst
        """
        if not self.is_connected:
            raise HS3NotFoundError("HS3 não está conectado")
        
        try:
            gen_ch = self.generator.channels[0]
            gen_ch.burst.enabled = True
            gen_ch.burst.mode = libtiepie.BM_COUNT
            gen_ch.burst.count = cycles
            
            self.logger.info(f"💥 Burst configurado: {cycles} ciclos")
            
        except Exception as e:
            raise HS3NotFoundError(f"Erro ao configurar burst: {e}")
    
    def enable_ext_trigger_gated(self, enabled: bool) -> None:
        """
        Habilita/desabilita trigger externo gated
        
        Args:
            enabled: True para habilitar, False para desabilitar
        """
        if not self.is_connected:
            raise HS3NotFoundError("HS3 não está conectado")
        
        try:
            gen_ch = self.generator.channels[0]
            
            if enabled:
                gen_ch.trigger.enabled = True
                gen_ch.trigger.kind = libtiepie.TK_GATED
            else:
                gen_ch.trigger.enabled = False
            
            self.logger.info(f"🎯 Trigger externo gated: {'ativado' if enabled else 'desativado'}")
            
        except Exception as e:
            raise HS3NotFoundError(f"Erro ao configurar trigger: {e}")
    
    def start_stream(self, sample_hz: float, v_range: float) -> None:
        """
        Inicia aquisição em stream
        
        Args:
            sample_hz: Taxa de amostragem em Hz
            v_range: Faixa de tensão (+/- volts)
        """
        if not self.is_connected:
            raise HS3NotFoundError("HS3 não está conectado")
        
        try:
            # Configurar osciloscópio
            self.oscilloscope.sample_frequency = sample_hz
            self.oscilloscope.record_length = int(sample_hz)  # 1 segundo de buffer
            
            # Configurar canais
            for i in range(2):
                ch = self.oscilloscope.channels[i]
                ch.range = v_range
                ch.enabled = True
            
            # Configurar trigger
            self.oscilloscope.trigger.time_out = 1.0  # 1 segundo timeout
            
            self.oscilloscope.start()
            self.is_streaming = True
            self.stream_sample_rate = sample_hz
            
            self.logger.info(f"📡 Stream iniciado: {sample_hz:.0f} Hz, Range: ±{v_range}V")
            
        except Exception as e:
            raise HS3NotFoundError(f"Erro ao iniciar stream: {e}")
    
    def read_stream(self, seconds: float) -> Tuple[np.ndarray, np.ndarray]:
        """
        Lê dados do stream
        
        Args:
            seconds: Duração da leitura em segundos
            
        Returns:
            Tuple com arrays numpy (CH1_shunt, CH2_paciente)
        """
        if not self.is_streaming:
            raise HS3NotFoundError("Stream não está ativo")
        
        try:
            # Calcular número de amostras
            samples_needed = int(self.stream_sample_rate * seconds)
            
            # Aguardar dados disponíveis
            timeout = seconds + 1.0  # Timeout extra
            start_time = time.time()
            
            while self.oscilloscope.is_data_ready is False:
                if time.time() - start_time > timeout:
                    raise TimeoutError(f"Timeout ao aguardar dados ({timeout:.1f}s)")
                time.sleep(0.001)  # 1ms
            
            # Ler dados
            data = self.oscilloscope.get_data()
            
            # Extrair canais (CH1: shunt, CH2: paciente)
            ch1_data = np.array(data[0][:samples_needed], dtype=np.float64)
            ch2_data = np.array(data[1][:samples_needed], dtype=np.float64)
            
            self.logger.debug(f"📊 Dados lidos: {len(ch1_data)} amostras por canal")
            
            return ch1_data, ch2_data
            
        except Exception as e:
            raise HS3NotFoundError(f"Erro ao ler stream: {e}")
    
    def stop_stream(self) -> None:
        """Para aquisição em stream"""
        if not self.is_connected:
            return
        
        try:
            if self.oscilloscope:
                self.oscilloscope.stop()
            self.is_streaming = False
            self.stream_sample_rate = 0.0
            
            self.logger.info("⏹️ Stream parado")
            
        except Exception as e:
            self.logger.error(f"Erro ao parar stream: {e}")
    
    def soft_ramp(self, generator_channel, attribute: str, target_value: float, 
                  steps: int = 20, delay_ms: float = 50) -> None:
        """
        Utilitário para transições suaves de parâmetros
        
        Args:
            generator_channel: Canal do gerador
            attribute: Nome do atributo ('amplitude', 'offset', etc.)
            target_value: Valor alvo
            steps: Número de passos da rampa
            delay_ms: Delay entre passos em milissegundos
        """
        try:
            current_value = getattr(generator_channel, attribute)
            step_size = (target_value - current_value) / steps
            
            for i in range(steps):
                new_value = current_value + (step_size * (i + 1))
                setattr(generator_channel, attribute, new_value)
                time.sleep(delay_ms / 1000.0)
            
            # Garantir valor final exato
            setattr(generator_channel, attribute, target_value)
            
        except Exception as e:
            self.logger.warning(f"Erro na rampa suave para {attribute}: {e}")
            # Fallback: definir valor diretamente
            setattr(generator_channel, attribute, target_value)


# ═══════════════════════════════════════════════════════════════════════
# TESTE DE LOOPBACK (apenas com variável de ambiente)
# ═══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Só executar se explicitamente autorizado
    if os.environ.get("BIODESK_ALLOW_LOOPBACK_TEST") != "1":
        print("⚠️  Teste de loopback não autorizado.")
        print("   Para executar, defina: BIODESK_ALLOW_LOOPBACK_TEST=1")
        exit(0)
    
    print("🧪 TESTE DE LOOPBACK HS3")
    print("═" * 50)
    
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    hs3 = None
    try:
        # Inicializar serviço
        print("🔌 Conectando ao HS3...")
        hs3 = HS3Service()
        hs3.open()
        
        print(f"✅ Conectado: {hs3.device_info.name}")
        print(f"   Serial: {hs3.device_info.serial_number}")
        print(f"   AWG Channels: {hs3.device_info.channels_awg}")
        print(f"   Scope Channels: {hs3.device_info.channels_scope}")
        
        # ATENÇÃO: Amplitude baixa para segurança!
        test_amplitude = 0.1  # 100mV apenas
        test_frequency = 1000  # 1 kHz
        test_duration = 2.0    # 2 segundos
        
        print(f"\n🎛️ Configurando gerador:")
        print(f"   Frequência: {test_frequency} Hz")
        print(f"   Amplitude: {test_amplitude} V (baixa para segurança)")
        print(f"   Offset: 0.0 V")
        
        # Configurar gerador
        hs3.configure_generator("sine", test_amplitude, 0.0)
        hs3.set_frequency(test_frequency)
        
        # Configurar stream
        sample_rate = 10000  # 10 kHz
        voltage_range = 1.0  # ±1V
        
        print(f"\n📡 Configurando osciloscópio:")
        print(f"   Sample Rate: {sample_rate} Hz")
        print(f"   Range: ±{voltage_range} V")
        print(f"   Duração: {test_duration} s")
        
        hs3.start_stream(sample_rate, voltage_range)
        
        # Iniciar geração e aquisição
        print(f"\n▶️ Iniciando teste de {test_duration}s...")
        hs3.start_output()
        
        # Aguardar estabilização
        time.sleep(0.5)
        
        # Ler dados
        ch1_data, ch2_data = hs3.read_stream(test_duration)
        
        # Parar tudo
        hs3.stop_output()
        hs3.stop_stream()
        
        # Analisar resultados
        print(f"\n📊 RESULTADOS:")
        print(f"   Amostras por canal: {len(ch1_data)}")
        
        # Calcular RMS
        ch1_rms = np.sqrt(np.mean(ch1_data**2))
        ch2_rms = np.sqrt(np.mean(ch2_data**2))
        
        print(f"   CH1 RMS: {ch1_rms:.4f} V")
        print(f"   CH2 RMS: {ch2_rms:.4f} V")
        
        # Calcular frequência dominante (FFT simples)
        fft_ch1 = np.fft.fft(ch1_data)
        freqs = np.fft.fftfreq(len(ch1_data), 1/sample_rate)
        dominant_freq_idx = np.argmax(np.abs(fft_ch1[1:len(freqs)//2])) + 1
        dominant_freq = abs(freqs[dominant_freq_idx])
        
        print(f"   Frequência dominante CH1: {dominant_freq:.1f} Hz")
        
        # Verificar se está próximo da frequência esperada
        freq_error = abs(dominant_freq - test_frequency) / test_frequency * 100
        print(f"   Erro de frequência: {freq_error:.2f}%")
        
        # Validação
        if freq_error < 5.0 and ch1_rms > 0.01:  # Tolerância 5%, mínimo 10mV
            print(f"\n✅ TESTE PASSOU: Sinal detectado corretamente")
        else:
            print(f"\n❌ TESTE FALHOU: Sinal não detectado como esperado")
        
    except HS3NotFoundError as e:
        print(f"❌ ERRO HS3: {e}")
        print("   Verifique se o HS3 está conectado e LibTiePie instalada")
        
    except HS3SafetyError as e:
        print(f"❌ ERRO SEGURANÇA: {e}")
        
    except Exception as e:
        print(f"❌ ERRO GERAL: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if hs3:
            hs3.close()
            print("🔌 HS3 desconectado")
        
    print("\n🧪 Teste concluído")
