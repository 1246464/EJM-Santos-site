#!/usr/bin/env python3
# ============================================
# test_backups.py — Testes do Sistema de Backup
# ============================================

import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime
import shutil

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_imports():
    """Verifica se todos os módulos podem ser importados"""
    print("🧪 Testando imports...")
    
    try:
        from backup_manager import BackupManager
        from backup_scheduler import BackupScheduler
        print("  ✅ Imports OK")
        return True
    except ImportError as e:
        print(f"  ❌ Erro de import: {e}")
        return False


def test_backup_manager_init():
    """Verifica inicialização do BackupManager"""
    print("\n🧪 Testando inicialização do BackupManager...")
    
    try:
        from backup_manager import BackupManager
        
        # Criar diretório temporário para testes
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = BackupManager(base_dir=Path(tmpdir))
            
            # Verificar diretórios criados
            assert manager.backup_dir.exists(), "Diretório de backups não foi criado"
            assert manager.base_dir == Path(tmpdir), "Base dir incorreto"
            
            print("  ✅ BackupManager inicializado corretamente")
            return True
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_create_simple_backup():
    """Testa criação de backup simples"""
    print("\n🧪 Testando criação de backup...")
    
    try:
        from backup_manager import BackupManager
        
        # Criar estrutura temporária
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Criar estrutura de diretórios
            instance_dir = tmpdir / 'instance'
            instance_dir.mkdir()
            static_dir = tmpdir / 'static' / 'imagens'
            static_dir.mkdir(parents=True)
            
            # Criar banco de dados de teste
            db_path = instance_dir / 'test.db'
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)')
            cursor.execute('INSERT INTO users (name) VALUES (?)', ('João',))
            conn.commit()
            conn.close()
            
            # Criar imagem de teste
            img_path = static_dir / 'test.jpg'
            img_path.write_bytes(b'fake image data')
            
            # Criar backup
            manager = BackupManager(base_dir=tmpdir)
            backup_path = manager.create_backup(
                include_db=True,
                include_images=True,
                description="Backup de teste"
            )
            
            # Verificações
            assert backup_path.exists(), "Arquivo de backup não foi criado"
            assert backup_path.suffix == '.zip', "Backup não é um arquivo ZIP"
            assert backup_path.stat().st_size > 0, "Backup está vazio"
            
            print(f"  ✅ Backup criado: {backup_path.name}")
            print(f"  ✅ Tamanho: {backup_path.stat().st_size} bytes")
            return True
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_list_backups():
    """Testa listagem de backups"""
    print("\n🧪 Testando listagem de backups...")
    
    try:
        from backup_manager import BackupManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Criar estrutura mínima
            (tmpdir / 'instance').mkdir()
            (tmpdir / 'static' / 'imagens').mkdir(parents=True)
            
            # Criar banco de teste
            db_path = tmpdir / 'instance' / 'test.db'
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test (id INTEGER)')
            conn.close()
            
            manager = BackupManager(base_dir=tmpdir)
            
            # Criar múltiplos backups
            backup1 = manager.create_backup(description="Backup 1")
            backup2 = manager.create_backup(description="Backup 2")
            
            # Listar backups
            backups = manager.list_backups()
            
            assert len(backups) == 2, f"Esperado 2 backups, encontrado {len(backups)}"
            assert backups[0]['description'] == "Backup 2", "Ordem incorreta (mais recente primeiro)"
            
            print(f"  ✅ {len(backups)} backups listados corretamente")
            return True
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_backup_validation():
    """Testa validação de integridade do banco"""
    print("\n🧪 Testando validação de banco de dados...")
    
    try:
        from backup_manager import BackupManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Criar banco válido
            db_path = tmpdir / 'valid.db'
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test (id INTEGER PRIMARY KEY, name TEXT)')
            conn.execute('INSERT INTO test (name) VALUES (?)', ('Teste',))
            conn.commit()
            conn.close()
            
            manager = BackupManager(base_dir=tmpdir)
            
            # Validar banco válido
            is_valid = manager._validate_db(db_path)
            assert is_valid, "Banco válido foi marcado como inválido"
            
            # Criar banco corrompido (arquivo vazio)
            corrupt_db = tmpdir / 'corrupt.db'
            corrupt_db.write_bytes(b'not a valid sqlite database')
            
            # Validar banco corrompido
            is_valid = manager._validate_db(corrupt_db)
            assert not is_valid, "Banco corrompido foi marcado como válido"
            
            print("  ✅ Validação de banco funcionando")
            return True
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_cleanup_old_backups():
    """Testa limpeza de backups antigos"""
    print("\n🧪 Testando limpeza de backups antigos...")
    
    try:
        from backup_manager import BackupManager
        import time
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Criar estrutura mínima
            (tmpdir / 'instance').mkdir()
            (tmpdir / 'static' / 'imagens').mkdir(parents=True)
            
            # Criar banco de teste
            db_path = tmpdir / 'instance' / 'test.db'
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test (id INTEGER)')
            conn.close()
            
            manager = BackupManager(base_dir=tmpdir)
            
            # Criar 5 backups
            for i in range(5):
                manager.create_backup(description=f"Backup {i+1}")
                time.sleep(0.1)  # Pequeno delay para timestamps diferentes
            
            # Verificar que 5 backups foram criados
            backups_before = manager.list_backups()
            assert len(backups_before) == 5, f"Esperado 5 backups, encontrado {len(backups_before)}"
            
            # Limpar, mantendo apenas 3
            removed = manager.cleanup_old_backups(keep_count=3, keep_days=0)
            
            # Verificar que 2 foram removidos
            backups_after = manager.list_backups()
            assert len(backups_after) == 3, f"Esperado 3 backups, encontrado {len(backups_after)}"
            assert removed == 2, f"Esperado 2 removidos, removido {removed}"
            
            print(f"  ✅ Limpeza funcionou: {removed} backups removidos")
            return True
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_restore_backup():
    """Testa restauração de backup"""
    print("\n🧪 Testando restauração de backup...")
    
    try:
        from backup_manager import BackupManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Criar estrutura
            instance_dir = tmpdir / 'instance'
            instance_dir.mkdir()
            static_dir = tmpdir / 'static' / 'imagens'
            static_dir.mkdir(parents=True)
            
            # Criar banco original
            db_path = instance_dir / 'test.db'
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)')
            conn.execute('INSERT INTO users (name) VALUES (?)', ('Original',))
            conn.commit()
            conn.close()
            
            # Criar imagem original
            img_path = static_dir / 'original.jpg'
            img_path.write_bytes(b'original image')
            
            # Criar backup
            manager = BackupManager(base_dir=tmpdir)
            backup_path = manager.create_backup()
            
            # Modificar arquivos originais
            conn = sqlite3.connect(db_path)
            conn.execute('DELETE FROM users')
            conn.execute('INSERT INTO users (name) VALUES (?)', ('Modificado',))
            conn.commit()
            conn.close()
            
            img_path.write_bytes(b'modified image')
            
            # Restaurar backup (sem criar backup de segurança para teste)
            success = manager.restore_backup(
                backup_file=backup_path,
                create_backup_before=False
            )
            
            assert success, "Restauração falhou"
            
            # Verificar se dados foram restaurados
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT name FROM users')
            name = cursor.fetchone()[0]
            conn.close()
            
            assert name == 'Original', f"Dados não foram restaurados: {name}"
            assert img_path.read_bytes() == b'original image', "Imagem não foi restaurada"
            
            print("  ✅ Restauração funcionou corretamente")
            return True
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_backup_manifest():
    """Testa leitura do manifesto do backup"""
    print("\n🧪 Testando manifesto do backup...")
    
    try:
        from backup_manager import BackupManager
        
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            
            # Criar estrutura mínima
            (tmpdir / 'instance').mkdir()
            (tmpdir / 'static' / 'imagens').mkdir(parents=True)
            
            # Criar banco
            db_path = tmpdir / 'instance' / 'test.db'
            conn = sqlite3.connect(db_path)
            conn.execute('CREATE TABLE test (id INTEGER)')
            conn.close()
            
            manager = BackupManager(base_dir=tmpdir)
            backup_path = manager.create_backup(description="Teste Manifesto")
            
            # Ler manifesto
            manifest = manager._read_manifest(backup_path)
            
            assert 'timestamp' in manifest, "Manifesto sem timestamp"
            assert 'description' in manifest, "Manifesto sem descrição"
            assert manifest['description'] == "Teste Manifesto", "Descrição incorreta"
            assert 'includes' in manifest, "Manifesto sem includes"
            assert 'files' in manifest, "Manifesto sem lista de arquivos"
            
            print("  ✅ Manifesto lido corretamente")
            print(f"     - Timestamp: {manifest['timestamp']}")
            print(f"     - Total de arquivos: {len(manifest['files'])}")
            return True
            
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_format_size():
    """Testa formatação de tamanho de arquivo"""
    print("\n🧪 Testando formatação de tamanho...")
    
    try:
        from backup_manager import BackupManager
        
        assert BackupManager._format_size(0) == "0.00 B"
        assert BackupManager._format_size(1024) == "1.00 KB"
        assert BackupManager._format_size(1024 * 1024) == "1.00 MB"
        assert BackupManager._format_size(1024 * 1024 * 1024) == "1.00 GB"
        
        print("  ✅ Formatação de tamanho OK")
        return True
        
    except AssertionError as e:
        print(f"  ❌ Erro: {e}")
        return False


def test_configs():
    """Testa se configurações de backup estão no config.py"""
    print("\n🧪 Testando configurações...")
    
    # Definir EJM_SECRET antes de importar
    if 'EJM_SECRET' not in os.environ:
        os.environ['EJM_SECRET'] = 'test_secret_for_backup_testing_minimum_32chars'
    
    try:
        from config import Config
        
        # Verificar configurações de backup
        assert hasattr(Config, 'BACKUP_ENABLED'), "BACKUP_ENABLED não configurado"
        assert hasattr(Config, 'BACKUP_DIR'), "BACKUP_DIR não configurado"
        assert hasattr(Config, 'BACKUP_KEEP_COUNT'), "BACKUP_KEEP_COUNT não configurado"
        assert hasattr(Config, 'BACKUP_KEEP_DAYS'), "BACKUP_KEEP_DAYS não configurado"
        
        print("  ✅ Configurações de backup presentes")
        print(f"     - BACKUP_ENABLED: {Config.BACKUP_ENABLED}")
        print(f"     - BACKUP_KEEP_COUNT: {Config.BACKUP_KEEP_COUNT}")
        print(f"     - BACKUP_KEEP_DAYS: {Config.BACKUP_KEEP_DAYS}")
        return True
        
    except Exception as e:
        print(f"  ❌ Erro: {e}")
        return False


def run_all_tests():
    """Executa todos os testes"""
    print("="*60)
    print("💾 TESTES DO SISTEMA DE BACKUP - EJM SANTOS")
    print("="*60)
    
    tests = [
        ("Imports", test_imports),
        ("Inicialização BackupManager", test_backup_manager_init),
        ("Criação de Backup", test_create_simple_backup),
        ("Listagem de Backups", test_list_backups),
        ("Validação de Banco", test_backup_validation),
        ("Limpeza de Backups", test_cleanup_old_backups),
        ("Restauração de Backup", test_restore_backup),
        ("Manifesto do Backup", test_backup_manifest),
        ("Formatação de Tamanho", test_format_size),
        ("Configurações", test_configs),
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n  ❌ ERRO CRÍTICO: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Resumo
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print("="*60)
    print(f"Resultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 Todos os testes de backup passaram!")
        return 0
    else:
        print("⚠️ Alguns testes falharam. Verifique as implementações.")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
