from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from database import init_database, get_db_connection
import sqlite3

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui_mude_em_producao'

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'

# Modelo de usuário para o Flask-Login
class User(UserMixin):
    def __init__(self, id, nome, email):
        self.id = id
        self.nome = nome
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (user_id,)).fetchone()
    conn.close()
    
    if user:
        return User(user['id'], user['nome'], user['email'])
    return None

# Rotas
@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['senha'], senha):
            user_obj = User(user['id'], user['nome'], user['email'])
            login_user(user_obj)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha inválidos!', 'danger')
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        confirmar_senha = request.form['confirmar_senha']
        
        if senha != confirmar_senha:
            flash('As senhas não coincidem!', 'danger')
            return render_template('cadastro.html')
        
        senha_hash = generate_password_hash(senha)
        
        try:
            conn = get_db_connection()
            conn.execute(
                'INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
                (nome, email, senha_hash)
            )
            conn.commit()
            conn.close()
            flash('Cadastro realizado com sucesso! Faça login.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Este email já está cadastrado!', 'danger')
    
    return render_template('cadastro.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logout realizado com sucesso!', 'success')
    return redirect(url_for('login'))

@app.route('/index')
@login_required
def index():
    conn = get_db_connection()
    
    # Estatísticas para o dashboard
    total_produtos = conn.execute('SELECT COUNT(*) as total FROM produtos').fetchone()['total']
    total_vendas = conn.execute('SELECT COUNT(*) as total FROM vendas').fetchone()['total']
    valor_total_vendas = conn.execute('SELECT SUM(preco_total) as total FROM vendas').fetchone()['total'] or 0
    
    # Últimos produtos cadastrados
    ultimos_produtos = conn.execute('''
        SELECT * FROM produtos 
        ORDER BY data_cadastro DESC 
        LIMIT 5
    ''').fetchall()
    
    # Últimas vendas
    ultimas_vendas = conn.execute('''
        SELECT v.*, u.nome as usuario_nome, p.nome as produto_nome 
        FROM vendas v
        JOIN usuarios u ON v.usuario_id = u.id
        JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.data_venda DESC 
        LIMIT 5
    ''').fetchall()
    
    conn.close()
    
    return render_template('index.html', 
                         total_produtos=total_produtos,
                         total_vendas=total_vendas,
                         valor_total_vendas=valor_total_vendas,
                         ultimos_produtos=ultimos_produtos,
                         ultimas_vendas=ultimas_vendas)

# Rotas para produtos (CRUD)
@app.route('/produtos')
@login_required
def listar_produtos():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos ORDER BY data_cadastro DESC').fetchall()
    conn.close()
    return render_template('produtos.html', produtos=produtos)

@app.route('/produto/novo', methods=['GET', 'POST'])
@login_required
def novo_produto():
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = float(request.form['preco'])
        quantidade = int(request.form['quantidade'])
        
        conn = get_db_connection()
        conn.execute(
            'INSERT INTO produtos (nome, descricao, preco, quantidade) VALUES (?, ?, ?, ?)',
            (nome, descricao, preco, quantidade)
        )
        conn.commit()
        conn.close()
        
        flash('Produto cadastrado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    
    return render_template('form_produto.html', produto=None)

@app.route('/produto/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_produto(id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (id,)).fetchone()
    
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        preco = float(request.form['preco'])
        quantidade = int(request.form['quantidade'])
        
        conn.execute(
            'UPDATE produtos SET nome = ?, descricao = ?, preco = ?, quantidade = ? WHERE id = ?',
            (nome, descricao, preco, quantidade, id)
        )
        conn.commit()
        conn.close()
        
        flash('Produto atualizado com sucesso!', 'success')
        return redirect(url_for('listar_produtos'))
    
    conn.close()
    return render_template('form_produto.html', produto=produto)

@app.route('/produto/deletar/<int:id>')
@login_required
def deletar_produto(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM produtos WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    
    flash('Produto deletado com sucesso!', 'success')
    return redirect(url_for('listar_produtos'))

# Rota para registrar venda
@app.route('/venda/registrar', methods=['GET', 'POST'])
@login_required
def registrar_venda():
    conn = get_db_connection()
    produtos = conn.execute('SELECT * FROM produtos WHERE quantidade > 0').fetchall()
    
    if request.method == 'POST':
        produto_id = request.form['produto_id']
        quantidade = int(request.form['quantidade'])
        
        # Buscar produto
        produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
        
        if produto and quantidade <= produto['quantidade']:
            preco_total = produto['preco'] * quantidade
            
            # Registrar venda
            conn.execute(
                'INSERT INTO vendas (usuario_id, produto_id, quantidade, preco_total) VALUES (?, ?, ?, ?)',
                (current_user.id, produto_id, quantidade, preco_total)
            )
            
            # Atualizar estoque
            nova_quantidade = produto['quantidade'] - quantidade
            conn.execute('UPDATE produtos SET quantidade = ? WHERE id = ?', (nova_quantidade, produto_id))
            
            conn.commit()
            flash('Venda registrada com sucesso!', 'success')
        else:
            flash('Quantidade indisponível em estoque!', 'danger')
        
        conn.close()
        return redirect(url_for('listar_vendas'))
    
    conn.close()
    return render_template('registrar_venda.html', produtos=produtos)

@app.route('/vendas')
@login_required
def listar_vendas():
    conn = get_db_connection()
    vendas = conn.execute('''
        SELECT v.*, u.nome as usuario_nome, p.nome as produto_nome 
        FROM vendas v
        JOIN usuarios u ON v.usuario_id = u.id
        JOIN produtos p ON v.produto_id = p.id
        ORDER BY v.data_venda DESC
    ''').fetchall()
    conn.close()
    return render_template('vendas.html', vendas=vendas)

if __name__ == '__main__':
    init_database()
    app.run(debug=True)