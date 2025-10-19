# 🍯 EJM Santos — Mel Puro e Natural

Site institucional e loja simples desenvolvida em **HTML, CSS e Flask**, representando a marca **EJM Santos**, produtora de mel artesanal e natural.

## 🌿 Sobre o Projeto
O projeto foi criado com o objetivo de apresentar os produtos da marca **EJM Santos** de forma clara e moderna, transmitindo a identidade natural e artesanal do mel produzido.

A estrutura do site inclui uma página inicial com destaque visual e uma seção de produtos com links de compra integrados ao **Mercado Pago**.

## 🧩 Estrutura do Site
- **Home (index.html):** Apresentação da marca e chamada para ação “Ver Produtos”.  
- **Produtos:** Lista de tipos de mel disponíveis com imagem, descrição e botão de compra.  
- **Estilo:** Layout moderno e responsivo, com cores que remetem ao mel e à natureza.  
- **Banco de dados:** Utiliza **SQLite via Flask SQLAlchemy** apenas para armazenar produtos.  
- **Integração de pagamento:** Cada produto contém um link direto do **Mercado Pago**.

## 🚀 Tecnologias Utilizadas
- **Python + Flask**
- **HTML5 e Jinja2**
- **CSS3**
- **SQLite (armazenamento simples de produtos)**
- **Mercado Pago (links de pagamento)**

## 🧾 Funcionalidades Principais
- Exibição de produtos com imagem, preço e descrição.  
- Sistema de templates do Flask para facilitar a manutenção.  
- Organização de arquivos em pastas (`static/`, `templates/`, `instance/`).  
- Banco de dados inicial populado via `init_db.py`.

## ⚙️ Como Rodar Localmente
```bash
python -m venv .venv
.venv\Scripts\activate
pip install flask flask_sqlalchemy
python init_db.py
python app.py
