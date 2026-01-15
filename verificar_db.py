import sqlite3

conn = sqlite3.connect('instance/ejm.db')
cursor = conn.cursor()

# Verificar estrutura da tabela product
cursor.execute('PRAGMA table_info(product)')
print('Colunas da tabela product:')
for row in cursor.fetchall():
    print(f"  {row[1]} ({row[2]})")

# Contar produtos
cursor.execute('SELECT COUNT(*) FROM product')
total = cursor.fetchone()[0]
print(f'\nTotal de produtos: {total}')

if total > 0:
    cursor.execute('SELECT id, titulo, preco FROM product LIMIT 5')
    print('\nPrimeiros produtos:')
    for row in cursor.fetchall():
        print(f"  ID {row[0]}: {row[1]} - R${row[2]}")

conn.close()
