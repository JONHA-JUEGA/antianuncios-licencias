"""
╔═══════════════════════════════════════════════════════════════╗
║     API DE LICENCIAS ANTIANUNCIOS - VERSIÓN UNIFICADA VERCEL  ║
║         Panel Admin + Registro CLIENT_ID + Resend API          ║
╚═══════════════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template_string, request, jsonify
import hmac
import hashlib
from datetime import datetime, timedelta
import os
import resend

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN
# ============================================

CLAVE_SECRETA = os.environ.get("CLAVE_SECRETA", "antianuncios_ipdroid_2024")
TU_EMAIL_PAYPAL = os.environ.get("PAYPAL_EMAIL", "Ithan150395@gmail.com")

# Cargar API Key de Resend desde variables de entorno
resend.api_key = os.environ.get("RESEND_API_KEY")

# Datos en memoria
clientes_en_memoria = {}
licencias_en_memoria = {}

# ============================================
# FUNCIONES AUXILIARES
# ============================================

def cargar_clientes():
    return clientes_en_memoria

def guardar_clientes(clientes):
    global clientes_en_memoria
    clientes_en_memoria = clientes

def cargar_licencias():
    return licencias_en_memoria

def guardar_licencias(licencias):
    global licencias_en_memoria
    licencias_en_memoria = licencias

# ============================================
# FUNCIONES DE LICENCIAS Y ENVÍO DE EMAIL
# ============================================

def generar_codigo_licencia(client_id, email, dias=180):
    mensaje = f"{client_id}|{email}|{dias}"
    firma = hmac.new(CLAVE_SECRETA.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
    return f"{client_id}|{email}|{dias}|{firma}"

def generar_codigo_ilimitado(client_id, email):
    dias = 99999
    mensaje = f"{client_id}|{email}|{dias}"
    firma = hmac.new(CLAVE_SECRETA.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
    return f"{client_id}|{email}|{dias}|{firma}"

def validar_codigo_licencia(codigo):
    try:
        partes = codigo.split("|")
        if len(partes) != 4:
            return False, "Formato inválido"
        
        client_id, email, dias_str, firma_proporcionada = partes
        dias = int(dias_str)
        
        mensaje = f"{client_id}|{email}|{dias}"
        firma_esperada = hmac.new(CLAVE_SECRETA.encode(), mensaje.encode(), hashlib.sha256).hexdigest()
        
        if firma_proporcionada != firma_esperada:
            return False, "Firma inválida"
        
        if dias not in [180, 365, 99999]:
            return False, "Días inválidos"
        
        return True, (client_id, email, dias)
    except:
        return False, "Error al validar"

def enviar_email(email_cliente, codigo, tipo_licencia="normal"):
    """Envía el correo a través de Resend API (Inmune a bloqueos SMTP de Vercel)"""
    try:
        if not resend.api_key:
            print("❌ Error: RESEND_API_KEY no está configurada en Vercel.")
            return False, "Falta RESEND_API_KEY"

        asunto = "🎉 Tu Licencia Antianuncios iP&Droid"
        
        if tipo_licencia == "ilimitada":
            duracion_texto = "ILIMITADA (SIN EXPIRACIÓN)"
        elif tipo_licencia == "1año":
            duracion_texto = "1 AÑO (365 días)"
        else:
            duracion_texto = "6 MESES (180 días)"
        
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px;">
                    <h1 style="color: #4CAF50; text-align: center;">🛡️ Antianuncios iP&Droid</h1>
                    <h2 style="text-align: center;">¡Licencia Activada!</h2>
                    <p><strong>Duración:</strong> {duracion_texto}</p>
                    <p>Tu código de licencia:</p>
                    <div style="background: #f0f0f0; padding: 15px; border-radius: 5px; word-break: break-all; font-family: monospace; font-size: 13px; font-weight: bold;">
                        {codigo}
                    </div>
                    <p style="margin-top: 20px; color: #666;">
                        Copia este código y regístralo en la app Antianuncios iP&Droid.
                    </p>
                    <p style="color: #999; font-size: 12px; text-align: center; margin-top: 30px;">
                        Contacto de soporte: {TU_EMAIL_PAYPAL}
                    </p>
                </div>
            </body>
        </html>
        """
        
        params = {
            "from": "Antianuncios iP&Droid <onboarding@resend.dev>",
            "to": [email_cliente],
            "subject": asunto,
            "html": cuerpo_html
        }
        
        resend.Emails.send(params)
        return True, "Enviado con éxito"
    except Exception as e:
        print(f"❌ Error enviando email vía Resend: {e}")
        return False, str(e)

# ============================================
# RUTAS API
# ============================================

@app.route('/registrar-cliente', methods=['POST'])
def registrar_cliente():
    try:
        datos = request.get_json()
        client_id = datos.get('client_id')
        email = datos.get('email', '')
        
        if not client_id:
            return jsonify({'exito': False, 'mensaje': 'ID vacío'})
        
        clientes = cargar_clientes()
        if client_id in clientes:
            if email:
                clientes[client_id]['email'] = email
                guardar_clientes(clientes)
            return jsonify({'exito': True, 'mensaje': 'Cliente actualizado'})
        
        clientes[client_id] = {
            'fecha_registro': datetime.now().isoformat(),
            'email': email,
            'estado': 'pendiente'
        }
        guardar_clientes(clientes)
        return jsonify({'exito': True, 'mensaje': 'Cliente registrado'})
    except Exception as e:
        return jsonify({'exito': False, 'mensaje': str(e)})

@app.route('/generar-licencia', methods=['POST'])
def generar_licencia():
    try:
        datos = request.get_json()
        client_id = datos.get('client_id')
        email = datos.get('email')
        tipo = datos.get('tipo', 'normal')
        
        if not client_id or not email:
            return jsonify({'exito': False, 'mensaje': 'Datos incompletos'})
        
        if tipo == 'ilimitada':
            codigo = generar_codigo_ilimitado(client_id, email)
            dias = 99999
            fecha_expiracion = "ILIMITADA"
        elif tipo == '1año':
            codigo = generar_codigo_licencia(client_id, email, 365)
            dias = 365
            fecha_expiracion = (datetime.now() + timedelta(days=365)).isoformat()
        else:
            codigo = generar_codigo_licencia(client_id, email, 180)
            dias = 180
            fecha_expiracion = (datetime.now() + timedelta(days=180)).isoformat()
        
        licencias = cargar_licencias()
        licencias[client_id] = {
            'email': email,
            'codigo': codigo,
            'fecha_compra': datetime.now().isoformat(),
            'dias': dias,
            'fecha_expiracion': fecha_expiracion,
            'tipo': tipo,
            'activa': True
        }
        guardar_licencias(licencias)
        
        # Envío de correo mediante API HTTP
        exito_mail, msg_mail = enviar_email(email, codigo, tipo)
        
        clientes = cargar_clientes()
        if client_id in clientes:
            clientes[client_id]['email'] = email
            clientes[client_id]['estado'] = 'activo'
            guardar_clientes(clientes)
        
        return jsonify({
            'exito': True,
            'mensaje': f'Licencia generada. Email: {msg_mail}',
            'codigo': codigo,
            'tipo': tipo
        })
    except Exception as e:
        return jsonify({'exito': False, 'mensaje': str(e)})

@app.route('/validar-licencia', methods=['POST'])
def validar_licencia():
    try:
        datos = request.get_json()
        codigo = datos.get('codigo')
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
        
        if dias == 99999:
            return jsonify({'exito': True, 'mensaje': 'Licencia válida (ILIMITADA)', 'dias_restantes': 99999})
        
        fecha_expiracion = datetime.fromisoformat(licencia['fecha_expiracion'])
        if datetime.now() > fecha_expiracion:
            return jsonify({'exito': False, 'mensaje': 'Licencia expirada'})
        
        dias_restantes = (fecha_expiracion - datetime.now()).days
        return jsonify({'exito': True, 'mensaje': 'Licencia válida', 'dias_restantes': dias_restantes})
    except Exception as e:
        return jsonify({'exito': False, 'mensaje': str(e)})

@app.route('/lista-clientes', methods=['GET'])
def lista_clientes():
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
                'tipo': lic.get('tipo', 'ninguna'),
                'expiracion': lic.get('fecha_expiracion')
            })
        return jsonify({'clientes': resultado})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/panel-admin')
def panel_admin():
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Panel Admin - Antianuncios</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f5f5f5; padding: 20px; }
            .contenedor { max-width: 1200px; margin: 0 auto; }
            h1 { color: #333; margin-bottom: 30px; text-align: center; }
            .panel { background: white; border-radius: 10px; padding: 20px; margin-bottom: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            .formulario { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px; }
            input, select { padding: 10px; border: 2px solid #ddd; border-radius: 5px; font-size: 14px; }
            button { background: #4CAF50; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; grid-column: 1 / -1; }
            button.ilimitada { background: #FF9800; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; }
            table th { background: #4CAF50; color: white; padding: 12px; text-align: left; }
            table td { padding: 12px; border-bottom: 1px solid #ddd; }
            .resultado { background: #E8F5E9; border-left: 4px solid #4CAF50; padding: 15px; margin-top: 15px; border-radius: 5px; display: none; }
            .resultado.activo { display: block; }
            .codigo { background: #f0f0f0; padding: 10px; border-radius: 5px; word-break: break-all; font-family: monospace; font-size: 12px; margin-top: 10px; }
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
                    <select id="tipo">
                        <option value="normal">6 Meses (180 días) - $100 MXN</option>
                        <option value="1año">1 Año (365 días) - $200 MXN</option>
                        <option value="ilimitada">ILIMITADA - SIN EXPIRACIÓN ⭐</option>
                    </select>
                    <button onclick="generarLicencia()">Generar Licencia Normal</button>
                    <button class="ilimitada" onclick="generarLicenciaIlimitada()">🔓 Generar ILIMITADA</button>
                </div>
                <div class="resultado" id="resultado">
                    <h3>✅ Licencia Generada</h3>
                    <p id="tipo_licencia_texto"></p>
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
                            <th>Tipo</th>
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
                const tipo = document.getElementById('tipo').value;
                if (!client_id || !email) { alert('Completa todos los campos'); return; }
                await enviarGenerarLicencia(client_id, email, tipo);
            }
            
            async function generarLicenciaIlimitada() {
                const client_id = document.getElementById('client_id').value;
                const email = document.getElementById('email').value;
                if (!client_id || !email) { alert('Completa CLIENT_ID y Email'); return; }
                await enviarGenerarLicencia(client_id, email, 'ilimitada');
            }
            
            async function enviarGenerarLicencia(client_id, email, tipo) {
                try {
                    const response = await fetch('/generar-licencia', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify({client_id, email, tipo})
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
                                <td>${cliente.tipo}</td>
                                <td>${cliente.dias || '-'}</td>
                                <td>${cliente.expiracion ? cliente.expiracion.substring(0, 10) : '-'}</td>
                            </tr>
                        `;
                        tbody.innerHTML += fila;
                    });
                } catch (error) { console.error('Error:', error); }
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
    return jsonify({'mensaje': 'API Antianuncios funcionando', 'admin': '/panel-admin'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
