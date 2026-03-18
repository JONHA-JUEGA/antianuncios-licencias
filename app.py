"""
╔═══════════════════════════════════════════════════════════════╗
║   APP WEB PARA RAILWAY.APP - Licencias desde cualquier lugar  ║
║        Accede desde tu celular sin estar en casa              ║
╚═══════════════════════════════════════════════════════════════╝
"""

from flask import Flask, render_template_string, request, jsonify
import hmac
import hashlib
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

app = Flask(__name__)

# ============================================
# CONFIGURACIÓN - EDITA ESTOS DATOS
# ============================================

CLAVE_SECRETA = "antianuncios_ipdroid_2024"
TU_EMAIL_GMAIL = "ip.and.droid@gmail.com"  # ⭐ EDITA AQUÍ
TU_PASSWORD_GMAIL = "tkzr vwhz bnln zzst"  # ⭐ EDITA AQUÍ (APP PASSWORD)
TU_EMAIL_PAYPAL = "Ithan150395@gmail.com"  # ⭐ EDITA AQUÍ

# ============================================
# FUNCIÓN PARA GENERAR CÓDIGO
# ============================================

def generar_codigo_licencia(email, dias=180):
    """Genera un código de licencia válido"""
    mensaje = f"{email}|{dias}"
    firma = hmac.new(
        CLAVE_SECRETA.encode(),
        mensaje.encode(),
        hashlib.sha256
    ).hexdigest()
    
    codigo = f"{email}|{dias}|{firma}"
    return codigo


def enviar_email(email_cliente, codigo):
    """Envía el código de licencia por email al cliente"""
    try:
        asunto = "🎉 Tu Licencia Antianuncios iP&Droid - ¡Activada!"
        
        cuerpo_html = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    
                    <h1 style="color: #2196F3; text-align: center;">🛡️ Antianuncios iP&Droid</h1>
                    
                    <h2 style="color: #333; text-align: center;">¡Licencia Activada!</h2>
                    
                    <p style="color: #666; font-size: 16px;">
                        Hola, gracias por tu compra. Tu licencia ha sido generada y está lista para usar.
                    </p>
                    
                    <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #4CAF50;">
                        <p style="color: #999; font-size: 12px; margin: 0;">TU CÓDIGO DE LICENCIA:</p>
                        <p style="color: #000; font-size: 18px; font-weight: bold; word-break: break-all; margin: 10px 0;">
                            {codigo}
                        </p>
                    </div>
                    
                    <h3 style="color: #333;">📋 Cómo Activar tu Licencia:</h3>
                    
                    <ol style="color: #666; line-height: 1.8;">
                        <li>Abre la app <strong>Antianuncios iP&Droid</strong></li>
                        <li>Haz clic en <strong>"🔑 Registrar Licencia"</strong></li>
                        <li>COPIA el código de arriba</li>
                        <li>PEGA el código en la app</li>
                        <li>Haz clic en <strong>"✅ Guardar Licencia"</strong></li>
                        <li>¡LISTO! Tu licencia está activada por 6 meses ✅</li>
                    </ol>
                    
                    <div style="background-color: #FFF3E0; padding: 15px; border-radius: 5px; margin: 20px 0; border-left: 4px solid #FF9800;">
                        <p style="color: #E65100; margin: 0;">
                            <strong>⏰ IMPORTANTE:</strong> Tu licencia expira en <strong>180 días</strong>.
                        </p>
                    </div>
                    
                    <p style="color: #999; font-size: 14px; text-align: center; margin-top: 30px;">
                        Si tienes problemas, contáctanos en: {TU_EMAIL_PAYPAL}
                    </p>
                    
                </div>
            </body>
        </html>
        """
        
        mensaje = MIMEMultipart()
        mensaje['From'] = TU_EMAIL_GMAIL
        mensaje['To'] = email_cliente
        mensaje['Subject'] = asunto
        
        mensaje.attach(MIMEText(cuerpo_html, 'html'))
        
        servidor = smtplib.SMTP('smtp.gmail.com', 587)
        servidor.starttls()
        servidor.login(TU_EMAIL_GMAIL, TU_PASSWORD_GMAIL)
        servidor.send_message(mensaje)
        servidor.quit()
        
        return True, "Email enviado correctamente"
        
    except Exception as e:
        return False, f"Error al enviar email: {str(e)}"


# ============================================
# RUTAS WEB
# ============================================

@app.route('/')
def index():
    """Página principal"""
    html = """
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Generar Licencias - Antianuncios iP&Droid</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .contenedor {
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                max-width: 500px;
                width: 100%;
                padding: 40px;
            }
            
            .encabezado {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .encabezado h1 {
                font-size: 28px;
                color: #333;
                margin-bottom: 5px;
            }
            
            .encabezado .emoji {
                font-size: 40px;
                margin-bottom: 10px;
            }
            
            .encabezado p {
                color: #999;
                font-size: 14px;
            }
            
            .formulario {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .grupo-input {
                display: flex;
                flex-direction: column;
            }
            
            .grupo-input label {
                color: #333;
                font-weight: 600;
                margin-bottom: 8px;
                font-size: 14px;
            }
            
            .grupo-input input,
            .grupo-input select {
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 14px;
                transition: border-color 0.3s;
                font-family: inherit;
            }
            
            .grupo-input input:focus,
            .grupo-input select:focus {
                outline: none;
                border-color: #667eea;
                box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
            }
            
            .btn-generar {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 14px 20px;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                margin-top: 10px;
            }
            
            .btn-generar:hover {
                transform: translateY(-2px);
                box-shadow: 0 10px 20px rgba(102, 126, 234, 0.3);
            }
            
            .btn-generar.cargando {
                opacity: 0.7;
                cursor: not-allowed;
            }
            
            .resultado {
                display: none;
                background: #f0f7ff;
                border-left: 4px solid #4CAF50;
                padding: 15px;
                border-radius: 8px;
                margin-top: 20px;
            }
            
            .resultado.exito {
                background: #E8F5E9;
                border-left-color: #4CAF50;
            }
            
            .resultado.error {
                background: #FFEBEE;
                border-left-color: #f44336;
            }
            
            .resultado.activo {
                display: block;
            }
            
            .resultado-titulo {
                font-weight: 600;
                margin-bottom: 8px;
                color: #333;
            }
            
            .resultado-mensaje {
                color: #666;
                font-size: 14px;
                line-height: 1.6;
            }
            
            .codigo-generado {
                background: white;
                padding: 15px;
                border-radius: 5px;
                margin-top: 10px;
                word-break: break-all;
                font-family: 'Courier New', monospace;
                font-size: 12px;
                color: #000;
                border: 1px solid #ddd;
            }
            
            .btn-copiar {
                background: #4CAF50;
                color: white;
                border: none;
                padding: 8px 12px;
                border-radius: 5px;
                font-size: 12px;
                cursor: pointer;
                margin-top: 10px;
                transition: background 0.3s;
            }
            
            .btn-copiar:hover {
                background: #45a049;
            }
            
            .cargando-spinner {
                display: none;
                text-align: center;
                margin-top: 10px;
            }
            
            .spinner {
                border: 3px solid #f3f3f3;
                border-top: 3px solid #667eea;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .info {
                background: #FFF3E0;
                border-left: 4px solid #FF9800;
                padding: 12px;
                border-radius: 5px;
                margin-bottom: 20px;
                font-size: 13px;
                color: #E65100;
            }
            
            @media (max-width: 480px) {
                .contenedor {
                    padding: 25px;
                }
                
                .encabezado h1 {
                    font-size: 24px;
                }
            }
        </style>
    </head>
    <body>
        <div class="contenedor">
            <div class="encabezado">
                <div class="emoji">🛡️</div>
                <h1>Antianuncios iP&Droid</h1>
                <p>Generador de Licencias</p>
            </div>
            
            <div class="info">
                ℹ️ Genera códigos de licencia para tus clientes.
            </div>
            
            <form class="formulario" id="formulario">
                <div class="grupo-input">
                    <label for="email">📧 Email del Cliente:</label>
                    <input type="email" id="email" name="email" placeholder="cliente@example.com" required>
                </div>
                
                <div class="grupo-input">
                    <label for="dias">📅 Duración:</label>
                    <select id="dias" name="dias" required>
                        <option value="180">6 Meses (180 días)</option>
                        <option value="365">1 Año (365 días)</option>
                    </select>
                </div>
                
                <button type="submit" class="btn-generar" id="btnGenerar">
                    ⚡ GENERAR Y ENVIAR
                </button>
                
                <div class="cargando-spinner" id="cargando">
                    <div class="spinner"></div>
                    <p style="margin-top: 10px; color: #667eea; font-size: 14px;">Generando código...</p>
                </div>
            </form>
            
            <div class="resultado" id="resultado">
                <div class="resultado-titulo" id="resultadoTitulo"></div>
                <div class="resultado-mensaje" id="resultadoMensaje"></div>
            </div>
        </div>
        
        <script>
            const formulario = document.getElementById('formulario');
            const btnGenerar = document.getElementById('btnGenerar');
            const cargando = document.getElementById('cargando');
            const resultado = document.getElementById('resultado');
            const resultadoTitulo = document.getElementById('resultadoTitulo');
            const resultadoMensaje = document.getElementById('resultadoMensaje');
            
            formulario.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const email = document.getElementById('email').value;
                const dias = document.getElementById('dias').value;
                
                btnGenerar.disabled = true;
                btnGenerar.classList.add('cargando');
                cargando.style.display = 'block';
                resultado.classList.remove('activo', 'exito', 'error');
                
                try {
                    const response = await fetch('/generar', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            email: email,
                            dias: dias
                        })
                    });
                    
                    const data = await response.json();
                    
                    cargando.style.display = 'none';
                    btnGenerar.disabled = false;
                    btnGenerar.classList.remove('cargando');
                    
                    resultado.classList.add('activo');
                    
                    if (data.exito) {
                        resultado.classList.add('exito');
                        resultado.classList.remove('error');
                        resultadoTitulo.innerHTML = '✅ ¡ÉXITO!';
                        resultadoMensaje.innerHTML = `
                            <strong>${data.mensaje}</strong>
                            <div class="codigo-generado">${data.codigo}</div>
                            <button type="button" class="btn-copiar" onclick="copiarCodigo('${data.codigo}')">
                                📋 Copiar Código
                            </button>
                        `;
                        
                        formulario.reset();
                    } else {
                        resultado.classList.add('error');
                        resultado.classList.remove('exito');
                        resultadoTitulo.innerHTML = '❌ Error';
                        resultadoMensaje.innerHTML = data.mensaje;
                    }
                    
                } catch (error) {
                    cargando.style.display = 'none';
                    btnGenerar.disabled = false;
                    btnGenerar.classList.remove('cargando');
                    
                    resultado.classList.add('activo', 'error');
                    resultado.classList.remove('exito');
                    resultadoTitulo.innerHTML = '❌ Error de Conexión';
                    resultadoMensaje.innerHTML = 'No se pudo conectar al servidor.';
                }
            });
            
            function copiarCodigo(codigo) {
                navigator.clipboard.writeText(codigo).then(() => {
                    alert('✅ Código copiado');
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/generar', methods=['POST'])
def generar():
    """Genera un código de licencia"""
    try:
        datos = request.get_json()
        email = datos.get('email')
        dias = int(datos.get('dias', 180))
        
        if not email or '@' not in email:
            return jsonify({
                'exito': False,
                'mensaje': '❌ Email inválido'
            })
        
        if dias not in [180, 365]:
            return jsonify({
                'exito': False,
                'mensaje': '❌ Duración debe ser 180 o 365 días'
            })
        
        codigo = generar_codigo_licencia(email, dias)
        exito_email, mensaje_email = enviar_email(email, codigo)
        
        if exito_email:
            return jsonify({
                'exito': True,
                'mensaje': f'✅ Enviado a {email}',
                'codigo': codigo
            })
        else:
            return jsonify({
                'exito': False,
                'mensaje': f'Error al enviar: {mensaje_email}'
            })
        
    except Exception as e:
        return jsonify({
            'exito': False,
            'mensaje': f'❌ Error: {str(e)}'
        })


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
