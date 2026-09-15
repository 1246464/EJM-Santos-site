# ============================================
# email_service.py — Serviço de Email
# ============================================

import smtplib
import os
from html import escape
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

class EmailService:
    def __init__(self):
        """Inicializa o serviço de email com configurações do .env"""
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.email_from_name = os.getenv("EMAIL_FROM_NAME", "EJM Santos - Mel Natural")
        
    def _send_email(self, to_email, subject, html_content):
        """Método interno para enviar email"""
        if not self.email_user or not self.email_password:
            print("⚠️ Configuração de email não encontrada. Email não enviado.")
            return False
        
        if not to_email or "@" not in to_email:
            print(f"❌ Email inválido: {to_email}")
            return False
            
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.email_from_name} <{self.email_user}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=30) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
                
            print(f"✅ Email enviado com sucesso para {to_email}")
            return True
        
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Erro de autenticação SMTP: {e}")
            return False
        
        except smtplib.SMTPException as e:
            print(f"❌ Erro SMTP ao enviar email: {e}")
            return False
        
        except TimeoutError as e:
            print(f"❌ Timeout ao conectar ao servidor SMTP: {e}")
            return False
            
        except Exception as e:
            print(f"❌ Erro inesperado ao enviar email: {e}")
            import traceback
            print(traceback.format_exc())
            return False
    
    def send_welcome_email(self, user_name, user_email):
        """Envia email de boas-vindas após cadastro"""
        subject = "🍯 Bem-vindo à EJM Santos!"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #f6b800 0%, #ff9800 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .button {{ display: inline-block; background: #f6b800; color: #000; 
                          padding: 12px 30px; text-decoration: none; border-radius: 5px; 
                          font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🍯 Bem-vindo à EJM Santos!</h1>
                </div>
                <div class="content">
                    <p>Olá, <strong>{user_name}</strong>!</p>
                    
                    <p>Seja muito bem-vindo à nossa loja de mel natural! 🎉</p>
                    
                    <p>Estamos felizes em tê-lo conosco. Aqui você encontra:</p>
                    <ul>
                        <li>🍃 Mel 100% natural e puro</li>
                        <li>🚫 Sem conservantes ou aditivos</li>
                        <li>🐝 Direto da colmeia para sua casa</li>
                    </ul>
                    
                    <p style="text-align: center;">
                        <a href="http://127.0.0.1:5000/produtos" class="button">Ver Nossos Produtos</a>
                    </p>
                    
                    <p>Se tiver alguma dúvida, estamos à disposição!</p>
                    
                    <p>Atenciosamente,<br><strong>Equipe EJM Santos</strong></p>
                </div>
                <div class="footer">
                    <p>Este é um email automático. Por favor, não responda.</p>
                    <p>© 2026 EJM Santos - Mel Natural</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, html_content)

    def send_password_reset_code(self, user_name, user_email, code, expires_minutes=15):
        """Envia o código temporário de recuperação usado pelo aplicativo."""
        safe_name = escape(str(user_name))
        safe_code = escape(str(code))
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; color: #241a0e;">
            <div style="max-width: 560px; margin: 0 auto; padding: 24px;">
                <h1 style="color: #7a4e00;">Recuperação de senha</h1>
                <p>Olá, <strong>{safe_name}</strong>.</p>
                <p>Use o código abaixo no aplicativo EJM Santos:</p>
                <p style="font-size: 30px; font-weight: bold; letter-spacing: 8px;
                          background: #fff2bf; padding: 18px; text-align: center;">
                    {safe_code}
                </p>
                <p>O código expira em {int(expires_minutes)} minutos.</p>
                <p>Se você não solicitou a recuperação, ignore este email.</p>
            </div>
        </body>
        </html>
        """
        return self._send_email(
            user_email,
            "Código de recuperação — EJM Santos",
            html_content,
        )
    
    def send_order_confirmation(self, user_name, user_email, order_id, order_items, total, 
                                endereco_completo=None):
        """Envia email de confirmação de pedido"""
        subject = f"✅ Pedido #{order_id} Confirmado - EJM Santos"
        
        # Monta lista de produtos
        items_html = ""
        for item in order_items:
            items_html += f"""
            <tr>
                <td style="padding: 10px; border-bottom: 1px solid #ddd;">{item['titulo']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: center;">
                    {item['quantidade']}
                </td>
                <td style="padding: 10px; border-bottom: 1px solid #ddd; text-align: right;">
                    R$ {item['preco']:.2f}
                </td>
            </tr>
            """
        
        endereco_html = ""
        if endereco_completo:
            endereco_html = f"""
            <div style="background: #fff; padding: 15px; border-left: 4px solid #f6b800; margin: 20px 0;">
                <h3 style="margin-top: 0;">📍 Endereço de Entrega:</h3>
                <p style="margin: 5px 0;">{endereco_completo}</p>
            </div>
            """
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #4caf50 0%, #2e7d32 100%); 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                table {{ width: 100%; border-collapse: collapse; background: white; margin: 20px 0; }}
                .total {{ font-size: 1.3em; font-weight: bold; color: #2e7d32; text-align: right; 
                         padding: 15px; background: #e8f5e9; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>✅ Pedido Confirmado!</h1>
                    <p style="margin: 0;">Pedido #{order_id}</p>
                </div>
                <div class="content">
                    <p>Olá, <strong>{user_name}</strong>!</p>
                    
                    <p>Seu pedido foi confirmado com sucesso! 🎉</p>
                    
                    <h3>📦 Itens do Pedido:</h3>
                    <table>
                        <thead>
                            <tr style="background: #f6b800;">
                                <th style="padding: 10px; text-align: left;">Produto</th>
                                <th style="padding: 10px; text-align: center;">Qtd</th>
                                <th style="padding: 10px; text-align: right;">Valor</th>
                            </tr>
                        </thead>
                        <tbody>
                            {items_html}
                        </tbody>
                    </table>
                    
                    <div class="total">
                        Total: R$ {total:.2f}
                    </div>
                    
                    {endereco_html}
                    
                    <p><strong>Status:</strong> Pendente (aguardando pagamento)</p>
                    
                    <p>Você receberá atualizações por email conforme seu pedido for processado.</p>
                    
                    <p>Atenciosamente,<br><strong>Equipe EJM Santos</strong></p>
                </div>
                <div class="footer">
                    <p>Para acompanhar seu pedido, acesse seu perfil no site.</p>
                    <p>© 2026 EJM Santos - Mel Natural</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, html_content)
    
    def send_order_status_update(self, user_name, user_email, order_id, old_status, new_status):
        """Envia email quando o status do pedido é atualizado"""
        
        # Define mensagens por status
        status_messages = {
            "Pago": {
                "icon": "💳",
                "title": "Pagamento Confirmado!",
                "message": "Seu pagamento foi confirmado e seu pedido está sendo preparado.",
                "color": "#2196f3"
            },
            "Enviado": {
                "icon": "🚚",
                "title": "Pedido Enviado!",
                "message": "Seu pedido está a caminho! Em breve você receberá seu mel.",
                "color": "#ff9800"
            },
            "Entregue": {
                "icon": "✅",
                "title": "Pedido Entregue!",
                "message": "Seu pedido foi entregue com sucesso! Esperamos que aproveite nosso mel.",
                "color": "#4caf50"
            },
            "Cancelado": {
                "icon": "❌",
                "title": "Pedido Cancelado",
                "message": "Seu pedido foi cancelado. Se tiver dúvidas, entre em contato conosco.",
                "color": "#f44336"
            }
        }
        
        status_info = status_messages.get(new_status, {
            "icon": "ℹ️",
            "title": "Status Atualizado",
            "message": f"O status do seu pedido foi atualizado para: {new_status}",
            "color": "#9e9e9e"
        })
        
        subject = f"{status_info['icon']} Pedido #{order_id} - {status_info['title']}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: {status_info['color']}; 
                          color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }}
                .status-box {{ background: white; padding: 20px; border-left: 4px solid {status_info['color']}; 
                              margin: 20px 0; }}
                .button {{ display: inline-block; background: #f6b800; color: #000; 
                          padding: 12px 30px; text-decoration: none; border-radius: 5px; 
                          font-weight: bold; margin: 20px 0; }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{status_info['icon']} {status_info['title']}</h1>
                    <p style="margin: 0;">Pedido #{order_id}</p>
                </div>
                <div class="content">
                    <p>Olá, <strong>{user_name}</strong>!</p>
                    
                    <div class="status-box">
                        <h3 style="margin-top: 0;">Atualização de Status</h3>
                        <p><strong>Status anterior:</strong> {old_status}</p>
                        <p><strong>Novo status:</strong> {new_status}</p>
                    </div>
                    
                    <p>{status_info['message']}</p>
                    
                    <p style="text-align: center;">
                        <a href="http://127.0.0.1:5000/perfil" class="button">Ver Meus Pedidos</a>
                    </p>
                    
                    <p>Atenciosamente,<br><strong>Equipe EJM Santos</strong></p>
                </div>
                <div class="footer">
                    <p>Para dúvidas ou suporte, entre em contato conosco.</p>
                    <p>© 2026 EJM Santos - Mel Natural</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return self._send_email(user_email, subject, html_content)


# Instância global do serviço
email_service = EmailService()
