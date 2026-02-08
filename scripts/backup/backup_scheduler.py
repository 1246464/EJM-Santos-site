#!/usr/bin/env python3
# ============================================
# backup_scheduler.py — Agendador de Backups Automáticos
# EJM Santos - Loja de Mel Natural 🍯
# ============================================

"""
Script para agendar backups automáticos do sistema.

Uso:
    python backup_scheduler.py                    # Executar backup agora
    python backup_scheduler.py --schedule daily   # Agendar backup diário
    python backup_scheduler.py --schedule weekly  # Agendar backup semanal
"""

import os
import sys
import schedule
import time
from pathlib import Path
from datetime import datetime
import argparse
import logging

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from backup_manager import BackupManager

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupScheduler:
    """
    Agendador de backups automáticos.
    """
    
    def __init__(self, keep_count: int = 10, keep_days: int = 30):
        """
        Inicializa o agendador.
        
        Args:
            keep_count: Número de backups a manter
            keep_days: Dias de backups a manter
        """
        self.manager = BackupManager()
        self.keep_count = keep_count
        self.keep_days = keep_days
        logger.info("🕐 Agendador de backups inicializado")
    
    def run_backup(self):
        """Executa um backup completo."""
        try:
            logger.info("="*60)
            logger.info("🔄 Iniciando backup agendado")
            logger.info("="*60)
            
            # Criar backup
            backup_path = self.manager.create_backup(
                include_db=True,
                include_images=True,
                include_logs=False,
                description="Backup automático agendado"
            )
            
            # Limpeza automática de backups antigos
            logger.info("\n🧹 Executando limpeza de backups antigos...")
            removed = self.manager.cleanup_old_backups(
                keep_count=self.keep_count,
                keep_days=self.keep_days
            )
            
            logger.info("="*60)
            logger.info("✅ Backup agendado concluído com sucesso")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"❌ Erro no backup agendado: {e}")
    
    def schedule_daily(self, time_str: str = "03:00"):
        """
        Agenda backup diário.
        
        Args:
            time_str: Horário no formato HH:MM (padrão: 03:00)
        """
        schedule.every().day.at(time_str).do(self.run_backup)
        logger.info(f"📅 Backup diário agendado para {time_str}")
        self._run_scheduler()
    
    def schedule_weekly(self, day: str = "sunday", time_str: str = "03:00"):
        """
        Agenda backup semanal.
        
        Args:
            day: Dia da semana (monday, tuesday, etc.)
            time_str: Horário no formato HH:MM
        """
        day_map = {
            'monday': schedule.every().monday,
            'tuesday': schedule.every().tuesday,
            'wednesday': schedule.every().wednesday,
            'thursday': schedule.every().thursday,
            'friday': schedule.every().friday,
            'saturday': schedule.every().saturday,
            'sunday': schedule.every().sunday
        }
        
        if day.lower() not in day_map:
            logger.error(f"❌ Dia inválido: {day}")
            return
        
        day_map[day.lower()].at(time_str).do(self.run_backup)
        logger.info(f"📅 Backup semanal agendado para {day} às {time_str}")
        self._run_scheduler()
    
    def schedule_hourly(self):
        """Agenda backup a cada hora (apenas para testes)."""
        schedule.every().hour.do(self.run_backup)
        logger.info("📅 Backup agendado a cada hora")
        self._run_scheduler()
    
    def _run_scheduler(self):
        """Executa o loop do agendador."""
        logger.info("🚀 Agendador iniciado. Pressione Ctrl+C para parar.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
        except KeyboardInterrupt:
            logger.info("\n⏹️  Agendador interrompido pelo usuário")


def main():
    """Interface de linha de comando."""
    parser = argparse.ArgumentParser(
        description='🍯 EJM Santos - Agendador de Backups Automáticos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s                              # Executar backup agora
  %(prog)s --schedule daily             # Agendar backup diário às 03:00
  %(prog)s --schedule daily --time 02:30  # Agendar backup diário às 02:30
  %(prog)s --schedule weekly --day sunday  # Agendar backup semanal aos domingos
  %(prog)s --keep 5 --days 15           # Manter apenas 5 backups ou 15 dias
        """
    )
    
    parser.add_argument(
        '--schedule',
        choices=['daily', 'weekly', 'hourly'],
        help='Tipo de agendamento'
    )
    parser.add_argument(
        '--time',
        default='03:00',
        help='Horário do backup no formato HH:MM (padrão: 03:00)'
    )
    parser.add_argument(
        '--day',
        default='sunday',
        choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
        help='Dia da semana para backup semanal (padrão: sunday)'
    )
    parser.add_argument(
        '--keep',
        type=int,
        default=10,
        help='Número de backups a manter (padrão: 10)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Dias de backups a manter (padrão: 30)'
    )
    
    args = parser.parse_args()
    
    # Criar diretório de logs
    logs_dir = Path(__file__).parent / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    # Criar agendador
    scheduler = BackupScheduler(keep_count=args.keep, keep_days=args.days)
    
    if args.schedule == 'daily':
        scheduler.schedule_daily(time_str=args.time)
    elif args.schedule == 'weekly':
        scheduler.schedule_weekly(day=args.day, time_str=args.time)
    elif args.schedule == 'hourly':
        scheduler.schedule_hourly()
    else:
        # Executar backup imediatamente
        scheduler.run_backup()


if __name__ == '__main__':
    main()
