"""
╔═══════════════════════════════════════════════════════════════╗
║     API DE LICENCIAS - VERSIÓN VERCEL (Sin SQLite)            ║
║  Funciona sin base de datos, datos en memoria                 ║
╚═══════════════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template_string, request, jsonify
import hmac
import hashlib
from datetime import datetime, timedelta
import json
import os

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================

# Credenciales de Gmail desde variables de entorno
EMAIL_GMAIL = os.environ.get('EMAIL_GMAIL', 'ip.and.droid@gmail.com')
PASSWORD_GMAIL = os.environ.get('PASSWORD_GMAIL', 'addgxvmqoywvytht')
EMAIL_PAYPAL = os.environ.get('EMAIL_PAYPAL', 'Ithan150395@gmail.com')

import os

CLAVE_SECRETA = "antianuncios_ipdroid_2024"

# Datos en memoria (se pierden si Vercel reinicia, pero funciona)
clientes_en_memoria = {}
licencias_en_memoria = {}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def cargar_clientes():
    """Carga clientes de memoria"""
    return clientes_en_memoria

def guardar_clientes(clientes):
    """Guarda clientes en memoria"""
    global clientes_en_memoria
    clientes_en_memoria = clientes

def cargar_licencias():
    """Carga licencias de memoria"""
    return licencias_en_memoria

def guardar_licencias(licencias):
    """Guarda licencias en memoria"""
    global licencias_en_memoria
    licencias_en_memoria = licencias

def guardar_clientes(clientes):
    """Guarda lista de clientes"""
    try:
        with open(CLIENTES_FILE, 'w') as f:
            json.dump(clientes, f, indent=2)
    except:
        pass

def cargar_licencias():
    """Carga lista de licencias"""
    try:
        if os.path.exists(LICENCIAS_FILE):
            with open(LICENCIAS_FILE, 'r') as f:
                return json.load(f)
    except:
        pass
    return {}

def guardar_licencias(licencias):
    """Guarda lista de licencias"""
    try:
        with open(LICENCIAS_FILE, 'w') as f:
            json.dump(licencias, f, indent=2)
    except:
        pass

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
        
        clientes = cargar_clientes()
        
        # Verificar si ya existe
        if client_id in clientes:
            return jsonify({'exito': True, 'mensaje': 'Cliente ya registrado'})
        
        # Insertar nuevo cliente
        clientes[client_id] = {
    'fecha_registro': datetime.now().isoformat(),
    'email': datos.get('email'),  # ← Ahora recibe el email
    'estado': 'pendiente'
}
        
        guardar_clientes(clientes)
        
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
        
        # Guardar licencia
        licencias = cargar_licencias()
        fecha_expiracion = (datetime.now() + timedelta(days=dias)).isoformat()
        
        licencias[client_id] = {
            'email': email,
            'codigo': codigo,
            'fecha_compra': datetime.now().isoformat(),
            'dias': dias,
            'fecha_expiracion': fecha_expiracion,
            'activa': True
        }
        
        guardar_licencias(licencias)

        # Enviar email con el código
        try:
            enviar_email(email, codigo)
        except:
            pass

        # Enviar email con el código
        try:
            enviar_email(email, codigo)
        except:
            pass
        
        # Actualizar cliente
        clientes = cargar_clientes()
        if client_id in clientes:
            clientes[client_id]['email'] = email
            clientes[client_id]['estado'] = 'activo'
            guardar_clientes(clientes)
        
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
        
        licencias = cargar_licencias()
        
        if client_id not in licencias:
            return jsonify({'exito': False, 'mensaje': 'Licencia no encontrada'})
        
        licencia = licencias[client_id]
        
        if not licencia.get('activa'):
            return jsonify({'exito': False, 'mensaje': 'Licencia desactivada'})
        
        # Verificar expiración
        fecha_expiracion = datetime.fromisoformat(licencia['fecha_expiracion'])
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
        clientes = cargar_clientes()
        licencias = cargar_licencias()
        
        resultado = []
        for client_id, cliente in clientes.items():
            lic = licencias.get(client_id, {})
            resultado.append({
                'client_id': client_id,
                'email': cliente.get('email'),
                'estado': cliente.get('estado'),
                'fecha_registro': cliente.get('fecha_registro'),
                'dias': lic.get('dias'),
                'expiracion': lic.get('fecha_expiracion')
            })
        
        return jsonify({'clientes': resultado})
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
            
            cargarClientes();
            setInterval(cargarClientes, 5000);
        </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/')
def index():
    return jsonify({'mensaje': 'API Antianuncios v1.2 funcionando', 'admin': '/panel-admin'})

def enviar_email(email_cliente, codigo):
    """Envía el código de licencia por email"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        asunto = "🎉 Tu Licencia Antianuncios iP&Droid"
        
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                    <h1 style="color: #4CAF50; text-align: center;">🛡️ Antianuncios iP&Droid</h1>
                    <h2 style="text-align: center;">¡Licencia Activada!</h2>
                    <p>Tu código de licencia:</p>
                    <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; word-break: break-all; font-family: monospace; font-size: 12px;">
                        {codigo}
                    </div>
                    <p style="margin-top: 20px; color: #666;">
                        Copia este código y regístralo en la app Antianuncios iP&Droid.
                    </p>
                </div>
            </body>
        </html>
        """
        
        mensaje = MIMEMultipart()
        mensaje['From'] = EMAIL_GMAIL
        mensaje['To'] = email_cliente
        mensaje['Subject'] = asunto
        
        mensaje.attach(MIMEText(cuerpo_html, 'html'))
        
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_GMAIL, PASSWORD_GMAIL)
        servidor.send_message(mensaje)
        servidor.quit()
        
        return True
    except Exception as e:
        return False

def enviar_email(email_cliente, codigo):
    """Envía el código de licencia por email"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        asunto = "🎉 Tu Licencia Antianuncios iP&Droid"
        
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                    <h1 style="color: #4CAF50; text-align: center;">🛡️ Antianuncios iP&Droid</h1>
                    <h2 style="text-align: center;">¡Licencia Activada!</h2>
                    <p>Tu código de licencia:</p>
                    <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; word-break: break-all; font-family: monospace; font-size: 12px;">
                        {codigo}
                    </div>
                    <p style="margin-top: 20px; color: #666;">
                        Copia este código y regístralo en la app Antianuncios iP&Droid.
                    </p>
                </div>
            </body>
        </html>
        """
        
        mensaje = MIMEMultipart()
        mensaje['From'] = EMAIL_GMAIL
        mensaje['To'] = email_cliente
        mensaje['Subject'] = asunto
        
        mensaje.attach(MIMEText(cuerpo_html, 'html'))
        
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(EMAIL_GMAIL, PASSWORD_GMAIL)
        servidor.send_message(mensaje)
        servidor.quit()
        
        return True
    except Exception as e:
        return False

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
