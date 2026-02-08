import sqlite3
import os

db_path = os.path.join('instance', 'loja.db')

if not os.path.exists(db_path):
    print("❌ Banco de dados não encontrado!")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar se a tabela product existe
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product'")
    if not cursor.fetchone():
        print("❌ Tabela 'product' não existe no banco de dados!")
    else:
        # Contar produtos
        cursor.execute("SELECT COUNT(*) FROM product")
        total = cursor.fetchone()[0]
        print(f"Total de produtos no banco: {total}")
        
        # Listar produtos
        cursor.execute("SELECT id, titulo, preco, estoque, imagem FROM product")
        produtos = cursor.fetchall()
        
        if produtos:
            print("\nProdutos cadastrados:")
            for p in produtos:
                print(f"  - ID: {p[0]} | {p[1]} | Preço: R$ {p[2]} | Estoque: {p[3]} | Imagem: {p[4]}")
        else:
            print("\n❌ Nenhum produto cadastrado no banco de dados!")
            print("\n💡 SOLUÇÃO: Você precisa cadastrar produtos através do painel admin.")
            print("   Acesse: http://localhost:5000/admin e faça login para adicionar produtos.")
    
    conn.close()
