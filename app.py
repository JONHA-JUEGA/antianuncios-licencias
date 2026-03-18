"""
╔═══════════════════════════════════════════════════════════════╗
║     API DE LICENCIAS - Sistema Profesional con SQLite         ║
║  Recibe IDs, guarda clientes, genera y valida licencias       ║
╚═══════════════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template_string, request, jsonify
import sqlite3
import os
import hmac
import hashlib
from datetime import datetime, timedelta
import uuid

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================

CLAVE_SECRETA = "antianuncios_ipdroid_2024"
DB_FILE = "licencias.db"

# ============================================
# BASE DE DATOS SQLite
# ============================================

def inicializar_db():
    """Crea las tablas si no existen"""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Tabla de clientes
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            fecha_registro TEXT,
            email TEXT,
            estado TEXT
        )
    """)
    
    # Tabla de licencias
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS licencias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id TEXT UNIQUE,
            email TEXT,
            codigo_licencia TEXT,
            fecha_compra TEXT,
            dias INTEGER,
            fecha_expiracion TEXT,
            activa INTEGER,
            FOREIGN KEY(client_id) REFERENCES clientes(client_id)
        )
    """)
    
    conn.commit()
    conn.close()

inicializar_db()

# ============================================
# FUNCIONES DE LICENCIAS
# ============================================

def generar_codigo_licencia(client_id, email, dias=180):
    """Genera código de licencia único"""
    mensaje = f"{client_id}|{email}|{dias}"
    firma = hmac.new(
        CLAVE_SECRETA.encode(),
        mensaje.encode(),
        hashlib.sha256
    ).hexdigest()
    
    codigo = f"{client_id}|{email}|{dias}|{firma}"
    return codigo

def validar_codigo_licencia(codigo):
    """Valida un código de licencia"""
    try:
        partes = codigo.split("|")
        if len(partes) != 4:
            return False, "Formato inválido"
        
        client_id, email, dias_str, firma_proporcionada = partes
        dias = int(dias_str)
        
        # Recalcular firma esperada
        mensaje = f"{client_id}|{email}|{dias}"
        firma_esperada = hmac.new(
            CLAVE_SECRETA.encode(),
            mensaje.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if firma_proporcionada != firma_esperada:
            return False, "Firma inválida"
        
        return True, (client_id, email, dias)
    except:
        return False, "Error al validar"

# ============================================
# RUTAS API
# ============================================

@app.route('/registrar-cliente', methods=['POST'])
def registrar_cliente():
    """Recibe el ID del cliente cuando abre la app"""
    try:
        datos = request.get_json()
        client_id = datos.get('client_id')
        
        if not client_id:
            return jsonify({'exito': False, 'mensaje': 'ID vacío'})
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Verificar si ya existe
        cursor.execute("SELECT * FROM clientes WHERE client_id = ?", (client_id,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'exito': True, 'mensaje': 'Cliente ya registrado'})
        
        # Insertar nuevo cliente
        cursor.execute("""
            INSERT INTO clientes (client_id, fecha_registro, estado)
            VALUES (?, ?, ?)
        """, (client_id, datetime.now().isoformat(), 'pendiente'))
        
        conn.commit()
        conn.close()
        
        return jsonify({'exito': True, 'mensaje': 'Cliente registrado'})
    except Exception as e:
        return jsonify({'exito': False, 'mensaje': str(e)})

@app.route('/generar-licencia', methods=['POST'])
def generar_licencia():
    """Genera una licencia para un cliente (ADMIN)"""
    try:
        datos = request.get_json()
        client_id = datos.get('client_id')
        email = datos.get('email')
        dias = int(datos.get('dias', 180))
        
        if not client_id or not email:
            return jsonify({'exito': False, 'mensaje': 'Datos incompletos'})
        
        if dias not in [180, 365]:
            return jsonify({'exito': False, 'mensaje': 'Días inválidos'})
        
        # Generar código
        codigo = generar_codigo_licencia(client_id, email, dias)
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Guardar licencia
        fecha_expiracion = (datetime.now() + timedelta(days=dias)).isoformat()
        cursor.execute("""
            INSERT OR REPLACE INTO licencias 
            (client_id, email, codigo_licencia, fecha_compra, dias, fecha_expiracion, activa)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (client_id, email, codigo, datetime.now().isoformat(), dias, fecha_expiracion, 1))
        
        # Actualizar cliente
        cursor.execute("""
            UPDATE clientes SET email = ?, estado = ? WHERE client_id = ?
        """, (email, 'activo', client_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'exito': True,
            'mensaje': 'Licencia generada',
            'codigo': codigo
        })
    except Exception as e:
        return jsonify({'exito': False, 'mensaje': str(e)})

@app.route('/validar-licencia', methods=['POST'])
def validar_licencia():
    """Valida una licencia desde main.exe"""
    try:
        datos = request.get_json()
        codigo = datos.get('codigo')
        
        # Validar formato
        valido, resultado = validar_codigo_licencia(codigo)
        if not valido:
            return jsonify({'exito': False, 'mensaje': resultado})
        
        client_id, email, dias = resultado
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Buscar licencia
        cursor.execute("""
            SELECT fecha_expiracion, activa FROM licencias 
            WHERE client_id = ? AND email = ?
        """, (client_id, email))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if not resultado:
            return jsonify({'exito': False, 'mensaje': 'Licencia no encontrada'})
        
        fecha_exp, activa = resultado
        
        if not activa:
            return jsonify({'exito': False, 'mensaje': 'Licencia desactivada'})
        
        # Verificar expiración
        fecha_expiracion = datetime.fromisoformat(fecha_exp)
        if datetime.now() > fecha_expiracion:
            return jsonify({'exito': False, 'mensaje': 'Licencia expirada'})
        
        dias_restantes = (fecha_expiracion - datetime.now()).days
        
        return jsonify({
            'exito': True,
            'mensaje': 'Licencia válida',
            'dias_restantes': dias_restantes
        })
    except Exception as e:
        return jsonify({'exito': False, 'mensaje': str(e)})

@app.route('/lista-clientes', methods=['GET'])
def lista_clientes():
    """Lista todos los clientes (ADMIN)"""
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT c.client_id, c.email, c.estado, c.fecha_registro,
                   l.dias, l.fecha_expiracion
            FROM clientes c
            LEFT JOIN licencias l ON c.client_id = l.client_id
            ORDER BY c.fecha_registro DESC
        """)
        
        resultados = cursor.fetchall()
        conn.close()
        
        clientes = []
        for row in resultados:
            clientes.append({
                'client_id': row[0],
                'email': row[1],
                'estado': row[2],
                'fecha_registro': row[3],
                'dias': row[4],
                'expiracion': row[5]
            })
        
        return jsonify({'clientes': clientes})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/panel-admin')
def panel_admin():
    """Panel admin para generar licencias"""
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel Admin - Antianuncios</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: #f5f5f5;
                padding: 20px;
            }
            .contenedor {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
                margin-bottom: 30px;
                text-align: center;
            }
            .panel {
                background: white;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .formulario {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin-bottom: 20px;
            }
            input, select {
                padding: 10px;
                border: 2px solid #ddd;
                border-radius: 5px;
                font-size: 14px;
            }
            input:focus, select:focus {
                outline: none;
                border-color: #4CAF50;
            }
            button {
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                font-weight: bold;
                grid-column: 1 / -1;
            }
            button:hover {
                background: #45a049;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            table th {
                background: #4CAF50;
                color: white;
                padding: 12px;
                text-align: left;
            }
            table td {
                padding: 12px;
                border-bottom: 1px solid #ddd;
            }
            table tr:hover {
                background: #f9f9f9;
            }
            .resultado {
                background: #E8F5E9;
                border-left: 4px solid #4CAF50;
                padding: 15px;
                margin-top: 15px;
                border-radius: 5px;
                display: none;
            }
            .resultado.activo {
                display: block;
            }
            .codigo {
                background: #f0f0f0;
                padding: 10px;
                border-radius: 5px;
                word-break: break-all;
                font-family: monospace;
                font-size: 12px;
                margin-top: 10px;
            }
        </style>
    </head>
    <body>
        <div class="contenedor">
            <h1>🛡️ Panel Admin - Antianuncios</h1>
            
            <div class="panel">
                <h2>Generar Licencia</h2>
                <div class="formulario">
                    <input type="text" id="client_id" placeholder="CLIENT_ID del cliente">
                    <input type="email" id="email" placeholder="Email del cliente">
                    <select id="dias">
                        <option value="180">6 Meses (180 días)</option>
                        <option value="365">1 Año (365 días)</option>
                    </select>
                    <button onclick="generarLicencia()">Generar Licencia</button>
                </div>
                <div class="resultado" id="resultado">
                    <h3>✅ Licencia Generada</h3>
                    <p>Código para el cliente:</p>
                    <div class="codigo" id="codigo_generado"></div>
                    <button onclick="copiarCodigo()" style="margin-top: 10px;">📋 Copiar Código</button>
                </div>
            </div>
            
            <div class="panel">
                <h2>Lista de Clientes</h2>
                <table id="tabla_clientes">
                    <thead>
                        <tr>
                            <th>CLIENT_ID</th>
                            <th>Email</th>
                            <th>Estado</th>
                            <th>Licencia (días)</th>
                            <th>Expira</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
        
        <script>
            async function generarLicencia() {
                const client_id = document.getElementById('client_id').value;
                const email = document.getElementById('email').value;
                const dias = document.getElementById('dias').value;
                
                if (!client_id || !email) {
                    alert('Completa todos los campos');
                    return;
                }
                
                try {
                    const response = await fetch('/generar-licencia', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({client_id, email, dias})
                    });
                    
                    const data = await response.json();
                    
                    if (data.exito) {
                        document.getElementById('codigo_generado').textContent = data.codigo;
                        document.getElementById('resultado').classList.add('activo');
                        cargarClientes();
                    } else {
                        alert('Error: ' + data.mensaje);
                    }
                } catch (error) {
                    alert('Error: ' + error);
                }
            }
            
            function copiarCodigo() {
                const codigo = document.getElementById('codigo_generado').textContent;
                navigator.clipboard.writeText(codigo);
                alert('✅ Código copiado');
            }
            
            async function cargarClientes() {
                try {
                    const response = await fetch('/lista-clientes');
                    const data = await response.json();
                    
                    const tbody = document.querySelector('#tabla_clientes tbody');
                    tbody.innerHTML = '';
                    
                    data.clientes.forEach(cliente => {
                        const fila = `
                            <tr>
                                <td>${cliente.client_id}</td>
                                <td>${cliente.email || '-'}</td>
                                <td>${cliente.estado}</td>
                                <td>${cliente.dias || '-'}</td>
                                <td>${cliente.expiracion ? cliente.expiracion.substring(0, 10) : '-'}</td>
                            </tr>
                        `;
                        tbody.innerHTML += fila;
                    });
                } catch (error) {
                    console.error('Error:', error);
                }
            }
            
            // Cargar clientes al abrir
            cargarClientes();
            setInterval(cargarClientes, 5000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
