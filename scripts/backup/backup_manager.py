#!/usr/bin/env python3
# ============================================
# backup_manager.py — Sistema de Backup Automático
# EJM Santos - Loja de Mel Natural 🍯
# ============================================

import os
import sys
import shutil
import zipfile
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import json
import argparse
from typing import List, Dict, Optional
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class BackupManager:
    """
    Gerenciador de backups do sistema EJM Santos.
    
    Funcionalidades:
    - Backup completo do banco de dados SQLite
    - Backup de arquivos estáticos (imagens)
    - Compressão em formato ZIP
    - Rotação automática de backups antigos
    - Restauração de backups
    - Validação de integridade
    """
    
    def __init__(self, base_dir: Path = None):
        """
        Inicializa o gerenciador de backups.
        
        Args:
            base_dir: Diretório base do projeto (padrão: diretório atual)
        """
        self.base_dir = base_dir or Path(__file__).resolve().parent
        self.backup_dir = self.base_dir / 'backups'
        self.instance_dir = self.base_dir / 'instance'
        self.static_dir = self.base_dir / 'static'
        self.logs_dir = self.base_dir / 'logs'
        
        # Criar diretórios necessários
        self.backup_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)
        
        logger.info(f"📦 BackupManager inicializado - Base: {self.base_dir}")
    
    def create_backup(self, 
                     include_db: bool = True,
                     include_images: bool = True,
                     include_logs: bool = False,
                     description: str = "") -> Path:
        """
        Cria um backup completo do sistema.
        
        Args:
            include_db: Incluir banco de dados
            include_images: Incluir imagens de produtos
            include_logs: Incluir arquivos de log
            description: Descrição opcional do backup
            
        Returns:
            Path: Caminho do arquivo de backup criado
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"ejm_backup_{timestamp}.zip"
        backup_path = self.backup_dir / backup_name
        
        logger.info("="*60)
        logger.info(f"🔄 Iniciando backup: {backup_name}")
        logger.info("="*60)
        
        try:
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_added = 0
                total_size = 0
                
                # Criar manifesto do backup
                manifest = {
                    'timestamp': timestamp,
                    'date': datetime.now().isoformat(),
                    'description': description,
                    'includes': {
                        'database': include_db,
                        'images': include_images,
                        'logs': include_logs
                    },
                    'files': []
                }
                
                # 1. Backup do banco de dados
                if include_db:
                    logger.info("📊 Fazendo backup do banco de dados...")
                    db_files = list(self.instance_dir.glob('*.db'))
                    
                    for db_file in db_files:
                        if db_file.exists():
                            # Validar integridade do DB antes do backup
                            if self._validate_db(db_file):
                                arcname = f"database/{db_file.name}"
                                zipf.write(db_file, arcname=arcname)
                                size = db_file.stat().st_size
                                files_added += 1
                                total_size += size
                                manifest['files'].append({
                                    'path': arcname,
                                    'size': size,
                                    'type': 'database'
                                })
                                logger.info(f"  ✅ {db_file.name} ({self._format_size(size)})")
                            else:
                                logger.warning(f"  ⚠️ {db_file.name} falhou na validação")
                
                # 2. Backup de imagens
                if include_images:
                    logger.info("🖼️  Fazendo backup das imagens...")
                    images_dir = self.static_dir / 'imagens'
                    
                    if images_dir.exists():
                        image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
                        
                        for img_file in images_dir.rglob('*'):
                            if img_file.is_file() and img_file.suffix.lower() in image_extensions:
                                rel_path = img_file.relative_to(self.static_dir)
                                arcname = f"static/{rel_path}"
                                zipf.write(img_file, arcname=arcname)
                                size = img_file.stat().st_size
                                files_added += 1
                                total_size += size
                                manifest['files'].append({
                                    'path': arcname,
                                    'size': size,
                                    'type': 'image'
                                })
                        
                        logger.info(f"  ✅ {files_added} imagens adicionadas")
                
                # 3. Backup de logs (opcional)
                if include_logs:
                    logger.info("📝 Fazendo backup dos logs...")
                    
                    if self.logs_dir.exists():
                        for log_file in self.logs_dir.glob('*.log'):
                            if log_file.exists() and log_file.name != 'backup.log':
                                arcname = f"logs/{log_file.name}"
                                zipf.write(log_file, arcname=arcname)
                                size = log_file.stat().st_size
                                files_added += 1
                                total_size += size
                                manifest['files'].append({
                                    'path': arcname,
                                    'size': size,
                                    'type': 'log'
                                })
                        
                        logger.info(f"  ✅ Logs adicionados")
                
                # 4. Salvar manifesto no backup
                manifest['total_files'] = files_added
                manifest['total_size'] = total_size
                manifest['total_size_formatted'] = self._format_size(total_size)
                
                zipf.writestr('MANIFEST.json', json.dumps(manifest, indent=2))
                
            # Resumo do backup
            backup_size = backup_path.stat().st_size
            logger.info("="*60)
            logger.info(f"✅ Backup criado com sucesso!")
            logger.info(f"📦 Arquivo: {backup_name}")
            logger.info(f"📊 {files_added} arquivos ({self._format_size(total_size)})")
            logger.info(f"💾 Tamanho comprimido: {self._format_size(backup_size)}")
            logger.info(f"📉 Compressão: {self._compression_ratio(total_size, backup_size):.1f}%")
            logger.info("="*60)
            
            return backup_path
            
        except Exception as e:
            logger.error(f"❌ Erro ao criar backup: {e}")
            if backup_path.exists():
                backup_path.unlink()
            raise
    
    def list_backups(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Lista todos os backups disponíveis.
        
        Args:
            limit: Número máximo de backups a listar (mais recentes primeiro)
            
        Returns:
            List[Dict]: Lista de informações dos backups
        """
        backups = []
        
        for backup_file in sorted(self.backup_dir.glob('ejm_backup_*.zip'), reverse=True):
            try:
                manifest = self._read_manifest(backup_file)
                size = backup_file.stat().st_size
                
                backup_info = {
                    'filename': backup_file.name,
                    'path': backup_file,
                    'size': size,
                    'size_formatted': self._format_size(size),
                    'date': manifest.get('date', 'desconhecido'),
                    'description': manifest.get('description', ''),
                    'total_files': manifest.get('total_files', 0),
                    'includes': manifest.get('includes', {})
                }
                
                backups.append(backup_info)
                
            except Exception as e:
                logger.warning(f"⚠️ Erro ao ler backup {backup_file.name}: {e}")
        
        return backups[:limit] if limit else backups
    
    def restore_backup(self, 
                      backup_file: Path,
                      restore_db: bool = True,
                      restore_images: bool = True,
                      restore_logs: bool = False,
                      create_backup_before: bool = True) -> bool:
        """
        Restaura um backup.
        
        Args:
            backup_file: Caminho do arquivo de backup
            restore_db: Restaurar banco de dados
            restore_images: Restaurar imagens
            restore_logs: Restaurar logs
            create_backup_before: Criar backup do estado atual antes de restaurar
            
        Returns:
            bool: True se restauração foi bem-sucedida
        """
        logger.info("="*60)
        logger.info(f"🔄 Iniciando restauração: {backup_file.name}")
        logger.info("="*60)
        
        # Criar backup de segurança antes de restaurar
        if create_backup_before:
            logger.info("💾 Criando backup de segurança antes da restauração...")
            try:
                safety_backup = self.create_backup(
                    description="Backup automático antes de restauração"
                )
                logger.info(f"✅ Backup de segurança criado: {safety_backup.name}")
            except Exception as e:
                logger.error(f"❌ Erro ao criar backup de segurança: {e}")
                return False
        
        try:
            with zipfile.ZipFile(backup_file, 'r') as zipf:
                # Ler manifesto
                manifest = json.loads(zipf.read('MANIFEST.json'))
                logger.info(f"📋 Backup de: {manifest['date']}")
                
                files_restored = 0
                
                # 1. Restaurar banco de dados
                if restore_db and manifest['includes'].get('database', False):
                    logger.info("📊 Restaurando banco de dados...")
                    
                    for file_info in manifest['files']:
                        if file_info['type'] == 'database':
                            source = file_info['path']
                            filename = Path(source).name
                            dest = self.instance_dir / filename
                            
                            # Extrair e restaurar
                            with zipf.open(source) as source_file:
                                dest.write_bytes(source_file.read())
                            
                            files_restored += 1
                            logger.info(f"  ✅ {filename} restaurado")
                
                # 2. Restaurar imagens
                if restore_images and manifest['includes'].get('images', False):
                    logger.info("🖼️  Restaurando imagens...")
                    
                    for file_info in manifest['files']:
                        if file_info['type'] == 'image':
                            source = file_info['path']
                            # Remover prefixo 'static/' para obter caminho relativo
                            rel_path = Path(source).relative_to('static')
                            dest = self.static_dir / rel_path
                            
                            # Criar diretórios se necessário
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            
                            # Extrair e restaurar
                            with zipf.open(source) as source_file:
                                dest.write_bytes(source_file.read())
                            
                            files_restored += 1
                    
                    logger.info(f"  ✅ Imagens restauradas")
                
                # 3. Restaurar logs (opcional)
                if restore_logs and manifest['includes'].get('logs', False):
                    logger.info("📝 Restaurando logs...")
                    
                    for file_info in manifest['files']:
                        if file_info['type'] == 'log':
                            source = file_info['path']
                            filename = Path(source).name
                            dest = self.logs_dir / filename
                            
                            with zipf.open(source) as source_file:
                                dest.write_bytes(source_file.read())
                            
                            files_restored += 1
                    
                    logger.info(f"  ✅ Logs restaurados")
            
            logger.info("="*60)
            logger.info(f"✅ Restauração concluída com sucesso!")
            logger.info(f"📊 {files_restored} arquivos restaurados")
            logger.info("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao restaurar backup: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count: int = 10, keep_days: int = 30) -> int:
        """
        Remove backups antigos, mantendo apenas os mais recentes.
        
        Args:
            keep_count: Número mínimo de backups a manter
            keep_days: Manter backups dos últimos N dias
            
        Returns:
            int: Número de backups removidos
        """
        logger.info(f"🧹 Limpando backups antigos (manter: {keep_count} ou {keep_days} dias)...")
        
        backups = self.list_backups()
        removed_count = 0
        total_freed = 0
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        for idx, backup in enumerate(backups):
            # Manter os N mais recentes
            if idx < keep_count:
                continue
            
            # Manter backups recentes (dentro do período)
            try:
                backup_date = datetime.fromisoformat(backup['date'])
                if backup_date > cutoff_date:
                    continue
            except:
                pass
            
            # Remover backup antigo
            try:
                size = backup['path'].stat().st_size
                backup['path'].unlink()
                removed_count += 1
                total_freed += size
                logger.info(f"  🗑️  Removido: {backup['filename']} ({backup['size_formatted']})")
            except Exception as e:
                logger.warning(f"  ⚠️ Erro ao remover {backup['filename']}: {e}")
        
        if removed_count > 0:
            logger.info(f"✅ {removed_count} backups removidos ({self._format_size(total_freed)} liberados)")
        else:
            logger.info("✅ Nenhum backup antigo para remover")
        
        return removed_count
    
    def get_backup_info(self, backup_file: Path) -> Dict:
        """
        Obtém informações detalhadas de um backup.
        
        Args:
            backup_file: Caminho do arquivo de backup
            
        Returns:
            Dict: Informações do backup
        """
        try:
            manifest = self._read_manifest(backup_file)
            size = backup_file.stat().st_size
            
            return {
                'filename': backup_file.name,
                'path': str(backup_file),
                'size': size,
                'size_formatted': self._format_size(size),
                'date': manifest.get('date'),
                'description': manifest.get('description', ''),
                'total_files': manifest.get('total_files', 0),
                'total_size': manifest.get('total_size', 0),
                'includes': manifest.get('includes', {}),
                'files': manifest.get('files', [])
            }
        except Exception as e:
            logger.error(f"❌ Erro ao ler backup: {e}")
            return {}
    
    def _validate_db(self, db_path: Path) -> bool:
        """Valida integridade do banco de dados SQLite."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("PRAGMA integrity_check")
            result = cursor.fetchone()
            conn.close()
            return result[0] == 'ok'
        except Exception as e:
            logger.warning(f"⚠️ Erro ao validar {db_path.name}: {e}")
            return False
    
    def _read_manifest(self, backup_file: Path) -> Dict:
        """Lê o manifesto de um arquivo de backup."""
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            return json.loads(zipf.read('MANIFEST.json'))
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Formata tamanho em bytes para formato legível."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    @staticmethod
    def _compression_ratio(original: int, compressed: int) -> float:
        """Calcula razão de compressão."""
        if original == 0:
            return 0
        return ((original - compressed) / original) * 100


def main():
    """Interface de linha de comando para gerenciamento de backups."""
    parser = argparse.ArgumentParser(
        description='🍯 EJM Santos - Gerenciador de Backups',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos:
  %(prog)s create                      # Criar backup completo
  %(prog)s create --no-images          # Backup apenas do banco
  %(prog)s list                        # Listar todos os backups
  %(prog)s restore ejm_backup_20260208_120000.zip  # Restaurar backup
  %(prog)s cleanup --keep 5            # Manter apenas os 5 mais recentes
  %(prog)s info ejm_backup_20260208_120000.zip    # Ver detalhes do backup
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comando a executar')
    
    # Comando: create
    create_parser = subparsers.add_parser('create', help='Criar novo backup')
    create_parser.add_argument('--no-db', action='store_true', help='Não incluir banco de dados')
    create_parser.add_argument('--no-images', action='store_true', help='Não incluir imagens')
    create_parser.add_argument('--logs', action='store_true', help='Incluir arquivos de log')
    create_parser.add_argument('--description', '-d', type=str, default='', help='Descrição do backup')
    
    # Comando: list
    list_parser = subparsers.add_parser('list', help='Listar backups')
    list_parser.add_argument('--limit', '-l', type=int, help='Limitar número de resultados')
    
    # Comando: restore
    restore_parser = subparsers.add_parser('restore', help='Restaurar backup')
    restore_parser.add_argument('backup', type=str, help='Nome do arquivo de backup')
    restore_parser.add_argument('--no-db', action='store_true', help='Não restaurar banco de dados')
    restore_parser.add_argument('--no-images', action='store_true', help='Não restaurar imagens')
    restore_parser.add_argument('--logs', action='store_true', help='Restaurar logs')
    restore_parser.add_argument('--no-safety-backup', action='store_true', help='Não criar backup de segurança antes')
    
    # Comando: cleanup
    cleanup_parser = subparsers.add_parser('cleanup', help='Remover backups antigos')
    cleanup_parser.add_argument('--keep', '-k', type=int, default=10, help='Número de backups a manter (padrão: 10)')
    cleanup_parser.add_argument('--days', '-d', type=int, default=30, help='Manter backups dos últimos N dias (padrão: 30)')
    
    # Comando: info
    info_parser = subparsers.add_parser('info', help='Ver informações de um backup')
    info_parser.add_argument('backup', type=str, help='Nome do arquivo de backup')
    
    args = parser.parse_args()
    
    # Criar gerenciador
    manager = BackupManager()
    
    # Executar comando
    if args.command == 'create':
        manager.create_backup(
            include_db=not args.no_db,
            include_images=not args.no_images,
            include_logs=args.logs,
            description=args.description
        )
    
    elif args.command == 'list':
        backups = manager.list_backups(limit=args.limit)
        
        if not backups:
            print("📦 Nenhum backup encontrado")
        else:
            print(f"\n📦 Backups disponíveis ({len(backups)}):")
            print("="*80)
            
            for backup in backups:
                print(f"📄 {backup['filename']}")
                print(f"   📅 Data: {backup['date']}")
                print(f"   💾 Tamanho: {backup['size_formatted']}")
                print(f"   📊 Arquivos: {backup['total_files']}")
                
                includes = []
                if backup['includes'].get('database'):
                    includes.append('BD')
                if backup['includes'].get('images'):
                    includes.append('Imagens')
                if backup['includes'].get('logs'):
                    includes.append('Logs')
                
                print(f"   📦 Inclui: {', '.join(includes)}")
                
                if backup['description']:
                    print(f"   📝 {backup['description']}")
                
                print()
    
    elif args.command == 'restore':
        backup_path = manager.backup_dir / args.backup
        
        if not backup_path.exists():
            print(f"❌ Backup não encontrado: {args.backup}")
            return 1
        
        manager.restore_backup(
            backup_path,
            restore_db=not args.no_db,
            restore_images=not args.no_images,
            restore_logs=args.logs,
            create_backup_before=not args.no_safety_backup
        )
    
    elif args.command == 'cleanup':
        manager.cleanup_old_backups(
            keep_count=args.keep,
            keep_days=args.days
        )
    
    elif args.command == 'info':
        backup_path = manager.backup_dir / args.backup
        
        if not backup_path.exists():
            print(f"❌ Backup não encontrado: {args.backup}")
            return 1
        
        info = manager.get_backup_info(backup_path)
        
        print(f"\n📦 Informações do Backup")
        print("="*80)
        print(f"📄 Arquivo: {info['filename']}")
        print(f"📅 Data: {info['date']}")
        print(f"💾 Tamanho: {info['size_formatted']}")
        print(f"📊 Total de arquivos: {info['total_files']}")
        
        if info['description']:
            print(f"📝 Descrição: {info['description']}")
        
        print(f"\n📦 Conteúdo:")
        print(f"   {'Tipo':<15} {'Arquivos':<10} {'Tamanho':<15}")
        print(f"   {'-'*15} {'-'*10} {'-'*15}")
        
        # Agrupar por tipo
        by_type = {}
        for file_info in info['files']:
            file_type = file_info['type']
            if file_type not in by_type:
                by_type[file_type] = {'count': 0, 'size': 0}
            by_type[file_type]['count'] += 1
            by_type[file_type]['size'] += file_info['size']
        
        for file_type, data in by_type.items():
            print(f"   {file_type.capitalize():<15} {data['count']:<10} {manager._format_size(data['size']):<15}")
        
        print()
    
    else:
        parser.print_help()


if __name__ == '__main__':
    sys.exit(main() or 0)
