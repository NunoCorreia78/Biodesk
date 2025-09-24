"""
Monitor de Saúde dos Serviços Quarkus - Biodesk Integration
═══════════════════════════════════════════════════════════════

Monitor contínuo de saúde e performance dos serviços Quarkus
integrados com o sistema Biodesk.
"""

import sys
import os
import time
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime, timedelta

# Adicionar diretório pai ao path para importar o cliente
sys.path.append(str(Path(__file__).parent.parent))

from biodesk_quarkus_client import BiodeskQuarkusIntegration, ServiceStatus
import logging

class HealthMonitor:
    """Monitor de saúde dos serviços Quarkus"""
    
    def __init__(self, client: BiodeskQuarkusIntegration):
        self.client = client
        self.logger = logging.getLogger("HealthMonitor")
        
        # Histórico de saúde
        self.health_history: List[Dict] = []
        self.max_history = 100  # Manter últimas 100 verificações
        
        # Alertas
        self.alert_thresholds = {
            "response_time_ms": 5000,  # 5 segundos
            "consecutive_failures": 3,
            "uptime_percentage": 95.0
        }
        
        # Contadores
        self.service_counters = {}
        self.start_time = time.time()
        
    def check_health_with_history(self) -> Dict:
        """Verificar saúde e manter histórico"""
        
        health_check = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "services": {},
            "overall_healthy": False,
            "alerts": []
        }
        
        # Verificar cada serviço
        services_status = self.client.check_services_health()
        healthy_count = 0
        
        for service_name, status in services_status.items():
            service_health = {
                "healthy": status.healthy,
                "response_time_ms": status.response_time_ms,
                "url": status.url,
                "last_check": status.last_check,
                "error_message": status.error_message
            }
            
            health_check["services"][service_name] = service_health
            
            if status.healthy:
                healthy_count += 1
            
            # Verificar alertas
            alerts = self._check_service_alerts(service_name, status)
            health_check["alerts"].extend(alerts)
            
            # Atualizar contadores
            self._update_service_counters(service_name, status)
        
        # Status geral
        health_check["overall_healthy"] = healthy_count >= len(services_status) * 0.6  # 60% dos serviços
        health_check["healthy_services"] = healthy_count
        health_check["total_services"] = len(services_status)
        
        # Adicionar ao histórico
        self.health_history.append(health_check)
        
        # Limitar tamanho do histórico
        if len(self.health_history) > self.max_history:
            self.health_history = self.health_history[-self.max_history:]
        
        return health_check
    
    def _check_service_alerts(self, service_name: str, status: ServiceStatus) -> List[Dict]:
        """Verificar alertas para um serviço"""
        
        alerts = []
        
        # Alert: Tempo de resposta alto
        if status.healthy and status.response_time_ms > self.alert_thresholds["response_time_ms"]:
            alerts.append({
                "type": "HIGH_RESPONSE_TIME",
                "service": service_name,
                "message": f"Response time {status.response_time_ms}ms exceeds threshold",
                "severity": "WARNING",
                "threshold": self.alert_thresholds["response_time_ms"]
            })
        
        # Alert: Serviço indisponível
        if not status.healthy:
            alerts.append({
                "type": "SERVICE_DOWN",
                "service": service_name,
                "message": f"Service is not responding",
                "severity": "CRITICAL",
                "error": status.error_message
            })
        
        return alerts
    
    def _update_service_counters(self, service_name: str, status: ServiceStatus):
        """Atualizar contadores de um serviço"""
        
        if service_name not in self.service_counters:
            self.service_counters[service_name] = {
                "total_checks": 0,
                "successful_checks": 0,
                "failed_checks": 0,
                "consecutive_failures": 0,
                "consecutive_successes": 0,
                "total_response_time": 0,
                "first_check": time.time()
            }
        
        counters = self.service_counters[service_name]
        counters["total_checks"] += 1
        
        if status.healthy:
            counters["successful_checks"] += 1
            counters["consecutive_successes"] += 1
            counters["consecutive_failures"] = 0
            counters["total_response_time"] += status.response_time_ms
        else:
            counters["failed_checks"] += 1
            counters["consecutive_failures"] += 1
            counters["consecutive_successes"] = 0
    
    def get_service_statistics(self, service_name: str = None) -> Dict:
        """Obter estatísticas de um ou todos os serviços"""
        
        if service_name:
            if service_name in self.service_counters:
                counters = self.service_counters[service_name]
                uptime_percentage = (counters["successful_checks"] / counters["total_checks"]) * 100
                avg_response_time = counters["total_response_time"] / max(1, counters["successful_checks"])
                
                return {
                    "service": service_name,
                    "uptime_percentage": round(uptime_percentage, 2),
                    "total_checks": counters["total_checks"],
                    "successful_checks": counters["successful_checks"],
                    "failed_checks": counters["failed_checks"],
                    "consecutive_failures": counters["consecutive_failures"],
                    "average_response_time_ms": round(avg_response_time, 2),
                    "monitoring_duration_hours": round((time.time() - counters["first_check"]) / 3600, 2)
                }
            else:
                return {"error": f"Service {service_name} not found"}
        else:
            # Estatísticas de todos os serviços
            all_stats = {}
            for svc_name in self.service_counters.keys():
                all_stats[svc_name] = self.get_service_statistics(svc_name)
            return all_stats
    
    def get_active_alerts(self) -> List[Dict]:
        """Obter alertas ativos baseados no histórico recente"""
        
        if not self.health_history:
            return []
        
        # Pegar alertas das últimas 5 verificações
        recent_checks = self.health_history[-5:]
        active_alerts = []
        
        for check in recent_checks:
            active_alerts.extend(check.get("alerts", []))
        
        # Remover duplicatas e manter apenas alertas críticos recentes
        unique_alerts = []
        seen_alerts = set()
        
        for alert in reversed(active_alerts):  # Mais recentes primeiro
            alert_key = f"{alert['service']}_{alert['type']}"
            if alert_key not in seen_alerts:
                unique_alerts.append(alert)
                seen_alerts.add(alert_key)
        
        return unique_alerts
    
    def generate_health_report(self) -> Dict:
        """Gerar relatório completo de saúde"""
        
        if not self.health_history:
            return {"error": "No health data available"}
        
        latest_check = self.health_history[-1]
        all_stats = self.get_service_statistics()
        active_alerts = self.get_active_alerts()
        
        # Calcular métricas gerais
        total_checks = sum(stats["total_checks"] for stats in all_stats.values() if isinstance(stats, dict) and "total_checks" in stats)
        total_successful = sum(stats["successful_checks"] for stats in all_stats.values() if isinstance(stats, dict) and "successful_checks" in stats)
        
        overall_uptime = (total_successful / max(1, total_checks)) * 100 if total_checks > 0 else 0
        
        report = {
            "report_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "monitoring_duration_hours": round((time.time() - self.start_time) / 3600, 2),
            "overall_status": {
                "healthy": latest_check["overall_healthy"],
                "healthy_services": latest_check["healthy_services"],
                "total_services": latest_check["total_services"],
                "overall_uptime_percentage": round(overall_uptime, 2)
            },
            "services_statistics": all_stats,
            "active_alerts": active_alerts,
            "recent_health_checks": len(self.health_history),
            "recommendations": self._generate_recommendations(all_stats, active_alerts)
        }
        
        return report
    
    def _generate_recommendations(self, stats: Dict, alerts: List[Dict]) -> List[str]:
        """Gerar recomendações baseadas nas estatísticas"""
        
        recommendations = []
        
        # Verificar uptime baixo
        for service_name, service_stats in stats.items():
            if isinstance(service_stats, dict) and "uptime_percentage" in service_stats:
                uptime = service_stats["uptime_percentage"]
                if uptime < self.alert_thresholds["uptime_percentage"]:
                    recommendations.append(
                        f"Investigate {service_name} - uptime is {uptime:.1f}% (below {self.alert_thresholds['uptime_percentage']}% threshold)"
                    )
        
        # Verificar tempo de resposta alto
        for service_name, service_stats in stats.items():
            if isinstance(service_stats, dict) and "average_response_time_ms" in service_stats:
                avg_time = service_stats["average_response_time_ms"]
                if avg_time > self.alert_thresholds["response_time_ms"]:
                    recommendations.append(
                        f"Optimize {service_name} - average response time is {avg_time:.0f}ms (above {self.alert_thresholds['response_time_ms']}ms threshold)"
                    )
        
        # Verificar alertas críticos
        critical_alerts = [alert for alert in alerts if alert.get("severity") == "CRITICAL"]
        if critical_alerts:
            recommendations.append(f"Address {len(critical_alerts)} critical alert(s) immediately")
        
        # Se tudo estiver bem
        if not recommendations:
            recommendations.append("All services are performing within acceptable parameters")
        
        return recommendations

def display_health_dashboard(monitor: HealthMonitor):
    """Exibir dashboard de saúde"""
    
    print("🏥 DASHBOARD DE SAÚDE - SERVIÇOS QUARKUS")
    print("=" * 60)
    
    # Verificar saúde atual
    current_health = monitor.check_health_with_history()
    
    # Status geral
    status_icon = "✅" if current_health["overall_healthy"] else "❌"
    print(f"\n{status_icon} STATUS GERAL:")
    print(f"   Serviços saudáveis: {current_health['healthy_services']}/{current_health['total_services']}")
    print(f"   Verificação: {current_health['timestamp']}")
    
    # Status individual dos serviços
    print(f"\n🔍 STATUS DOS SERVIÇOS:")
    print("-" * 40)
    
    for service_name, service_health in current_health["services"].items():
        icon = "✅" if service_health["healthy"] else "❌"
        status_text = "OK" if service_health["healthy"] else "FALHA"
        
        print(f"{icon} {service_name}: {status_text}")
        print(f"   URL: {service_health['url']}")
        print(f"   Tempo de resposta: {service_health['response_time_ms']}ms")
        
        if not service_health["healthy"] and service_health["error_message"]:
            print(f"   Erro: {service_health['error_message']}")
        print()
    
    # Alertas ativos
    active_alerts = monitor.get_active_alerts()
    if active_alerts:
        print(f"🚨 ALERTAS ATIVOS ({len(active_alerts)}):")
        print("-" * 40)
        
        for alert in active_alerts[:5]:  # Mostrar apenas os 5 primeiros
            severity_icon = "🔴" if alert["severity"] == "CRITICAL" else "🟡"
            print(f"{severity_icon} {alert['service']}: {alert['message']}")
        
        if len(active_alerts) > 5:
            print(f"   ... e mais {len(active_alerts) - 5} alertas")
        print()
    else:
        print("✅ NENHUM ALERTA ATIVO\n")
    
    # Estatísticas resumidas
    all_stats = monitor.get_service_statistics()
    if all_stats:
        print("📊 ESTATÍSTICAS RESUMIDAS:")
        print("-" * 40)
        
        for service_name, stats in all_stats.items():
            if isinstance(stats, dict) and "uptime_percentage" in stats:
                uptime_icon = "🟢" if stats["uptime_percentage"] >= 95 else "🟡" if stats["uptime_percentage"] >= 90 else "🔴"
                print(f"{uptime_icon} {service_name}:")
                print(f"   Uptime: {stats['uptime_percentage']}%")
                print(f"   Tempo médio: {stats['average_response_time_ms']:.0f}ms")
                print(f"   Verificações: {stats['total_checks']} ({stats['failed_checks']} falhas)")
                print()

def continuous_health_monitoring(monitor: HealthMonitor, interval_seconds: int = 60):
    """Monitor contínuo de saúde"""
    
    print(f"🔄 MONITOR CONTÍNUO DE SAÚDE")
    print(f"Intervalo: {interval_seconds} segundos")
    print("Pressione Ctrl+C para parar\n")
    
    cycle_count = 0
    
    try:
        while True:
            cycle_count += 1
            
            print(f"🔄 CICLO {cycle_count} - {time.strftime('%H:%M:%S')}")
            print("-" * 50)
            
            # Verificar saúde
            health_check = monitor.check_health_with_history()
            
            # Status resumido
            status_icon = "✅" if health_check["overall_healthy"] else "❌"
            print(f"{status_icon} Status: {health_check['healthy_services']}/{health_check['total_services']} serviços saudáveis")
            
            # Alertas novos
            if health_check["alerts"]:
                print(f"🚨 {len(health_check['alerts'])} alerta(s) detectado(s)")
                for alert in health_check["alerts"][:3]:  # Mostrar até 3
                    severity_icon = "🔴" if alert["severity"] == "CRITICAL" else "🟡"
                    print(f"   {severity_icon} {alert['service']}: {alert['type']}")
            else:
                print("✅ Nenhum alerta")
            
            # Próxima verificação
            print(f"⏳ Próxima verificação em {interval_seconds}s...\n")
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print(f"\n👋 Monitoramento interrompido pelo usuário")
        print(f"Total de ciclos executados: {cycle_count}")
        
        # Exibir relatório final
        print(f"\n📋 RELATÓRIO FINAL:")
        report = monitor.generate_health_report()
        
        print(f"Tempo de monitoramento: {report['monitoring_duration_hours']:.2f} horas")
        print(f"Uptime geral: {report['overall_status']['overall_uptime_percentage']:.2f}%")
        print(f"Verificações realizadas: {report['recent_health_checks']}")
        
        if report["recommendations"]:
            print(f"\n💡 RECOMENDAÇÕES:")
            for rec in report["recommendations"][:3]:
                print(f"   • {rec}")

def main():
    """Função principal do monitor de saúde"""
    
    # Configurar logging
    logging.basicConfig(level=logging.WARNING)  # Reduzir verbosidade
    
    # Inicializar cliente e monitor
    client = BiodeskQuarkusIntegration()
    monitor = HealthMonitor(client)
    
    while True:
        print("\n🏥 MONITOR DE SAÚDE DOS SERVIÇOS QUARKUS")
        print("=" * 60)
        print("Escolha uma opção:")
        print("1. 📊 Dashboard de saúde atual")
        print("2. 🔄 Monitor contínuo (1 minuto)")
        print("3. ⚡ Monitor contínuo (30 segundos)")
        print("4. 📋 Relatório completo")
        print("5. 📈 Estatísticas detalhadas")
        print("6. 🚨 Alertas ativos")
        print("7. 💾 Exportar relatório JSON")
        print("0. ❌ Sair")
        
        try:
            choice = input("\nOpção: ").strip()
            
            if choice == '0':
                print("👋 Encerrando monitor de saúde...")
                break
                
            elif choice == '1':
                display_health_dashboard(monitor)
                input("\nPressione Enter para continuar...")
                
            elif choice == '2':
                continuous_health_monitoring(monitor, 60)
                
            elif choice == '3':
                continuous_health_monitoring(monitor, 30)
                
            elif choice == '4':
                print("\n📋 GERANDO RELATÓRIO COMPLETO...")
                report = monitor.generate_health_report()
                
                print(f"\n📊 RELATÓRIO DE SAÚDE DOS SERVIÇOS")
                print("=" * 50)
                print(f"Timestamp: {report['report_timestamp']}")
                print(f"Monitoramento: {report['monitoring_duration_hours']:.2f} horas")
                print(f"Uptime geral: {report['overall_status']['overall_uptime_percentage']:.2f}%")
                
                if report["recommendations"]:
                    print(f"\n💡 RECOMENDAÇÕES:")
                    for rec in report["recommendations"]:
                        print(f"   • {rec}")
                
                input("\nPressione Enter para continuar...")
                
            elif choice == '5':
                print(f"\n📈 ESTATÍSTICAS DETALHADAS:")
                print("-" * 40)
                
                all_stats = monitor.get_service_statistics()
                for service_name, stats in all_stats.items():
                    if isinstance(stats, dict):
                        print(f"\n🔹 {service_name.upper()}:")
                        print(f"   Uptime: {stats.get('uptime_percentage', 0):.2f}%")
                        print(f"   Verificações totais: {stats.get('total_checks', 0)}")
                        print(f"   Sucessos/Falhas: {stats.get('successful_checks', 0)}/{stats.get('failed_checks', 0)}")
                        print(f"   Falhas consecutivas: {stats.get('consecutive_failures', 0)}")
                        print(f"   Tempo médio de resposta: {stats.get('average_response_time_ms', 0):.0f}ms")
                        print(f"   Monitoramento: {stats.get('monitoring_duration_hours', 0):.2f}h")
                
                input("\nPressione Enter para continuar...")
                
            elif choice == '6':
                active_alerts = monitor.get_active_alerts()
                
                if active_alerts:
                    print(f"\n🚨 ALERTAS ATIVOS ({len(active_alerts)}):")
                    print("-" * 40)
                    
                    for alert in active_alerts:
                        severity_icon = "🔴" if alert["severity"] == "CRITICAL" else "🟡"
                        print(f"{severity_icon} {alert['service']}")
                        print(f"   Tipo: {alert['type']}")
                        print(f"   Mensagem: {alert['message']}")
                        print(f"   Severidade: {alert['severity']}")
                        print()
                else:
                    print("✅ Nenhum alerta ativo no momento")
                
                input("\nPressione Enter para continuar...")
                
            elif choice == '7':
                print("\n💾 EXPORTANDO RELATÓRIO...")
                report = monitor.generate_health_report()
                
                output_file = f"health_report_{int(time.time())}.json"
                try:
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(report, f, indent=2, ensure_ascii=False)
                    
                    print(f"✅ Relatório exportado: {output_file}")
                    
                except Exception as e:
                    print(f"❌ Erro ao exportar: {e}")
                
                input("\nPressione Enter para continuar...")
                
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            print("\n👋 Encerrando...")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main()