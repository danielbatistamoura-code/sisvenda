import sqlite3
from werkzeug.security import generate_password_hash

def init_database():
    """Inicializa o banco de dados com as tabelas necessárias"""
    conn = sqlite3.connect('instance/vendas.db')
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            preco REAL NOT NULL,
            quantidade INTEGER DEFAULT 0,
            data_cadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de vendas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS vendas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            produto_id INTEGER,
            quantidade INTEGER,
            preco_total REAL,
            data_venda TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (usuario_id) REFERENCES usuarios (id),
            FOREIGN KEY (produto_id) REFERENCES produtos (id)
        )
    ''')
    
    # Criar usuário admin padrão se não existir
    cursor.execute("SELECT * FROM usuarios WHERE email = 'admin@admin.com'")
    if not cursor.fetchone():
        senha_hash = generate_password_hash('admin123')
        cursor.execute(
            "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
            ('Administrador', 'admin@admin.com', senha_hash)
        )
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Retorna uma conexão com o banco de dados"""
    conn = sqlite3.connect('instance/vendas.db')
    conn.row_factory = sqlite3.Row
    return conn