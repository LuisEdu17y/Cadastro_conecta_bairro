"""
email_service.py
----------------
Serviço de envio de e-mails via SMTP.

Configure as variáveis de ambiente para habilitar:
    SMTP_HOST   (ex: smtp.gmail.com)
    SMTP_PORT   (ex: 587)
    SMTP_USER   (seu e-mail)
    SMTP_PASS   (senha ou app password)
    EMAIL_FROM  (remetente exibido — padrão: SMTP_USER)

Se as variáveis não estiverem configuradas, os e-mails são apenas logados
no terminal (útil para desenvolvimento sem conta SMTP real).
"""

import os
import smtplib
import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
EMAIL_FROM = os.getenv("EMAIL_FROM", SMTP_USER)

_smtp_configurado = bool(SMTP_HOST and SMTP_USER and SMTP_PASS)


def _enviar_sync(para: str, assunto: str, html: str) -> None:
    """Envia e-mail de forma síncrona (chamado em thread separada)."""
    if not _smtp_configurado:
        logger.info(
            "[EMAIL - sem SMTP configurado]\n"
            f"  Para:    {para}\n"
            f"  Assunto: {assunto}\n"
            f"  Corpo:   {html[:200]}..."
        )
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"] = EMAIL_FROM
    msg["To"] = para
    msg.attach(MIMEText(html, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_PASS)
        smtp.sendmail(EMAIL_FROM, [para], msg.as_string())


async def enviar_email(para: str, assunto: str, html: str) -> None:
    """Envia e-mail de forma assíncrona (não bloqueia o event loop)."""
    try:
        await asyncio.to_thread(_enviar_sync, para, assunto, html)
    except Exception as exc:
        logger.error(f"Falha ao enviar e-mail para {para}: {exc}")


# ──────────────────────────────────────────────
# Templates de e-mail
# ──────────────────────────────────────────────

def _base_template(titulo: str, corpo: str) -> str:
    return f"""
    <html><body style="font-family:sans-serif;background:#f5f5f5;padding:24px;">
      <div style="max-width:560px;margin:0 auto;background:#fff;border-radius:12px;
                  padding:32px;box-shadow:0 2px 8px rgba(0,0,0,.08);">
        <h2 style="color:#0d9488;margin-top:0;">{titulo}</h2>
        {corpo}
        <hr style="border:none;border-top:1px solid #eee;margin:24px 0;">
        <p style="color:#888;font-size:12px;margin:0;">
          Conecta Bairro · Plataforma comunitária
        </p>
      </div>
    </body></html>
    """


async def email_inscricao_confirmada(
    para: str, nome_usuario: str, titulo_evento: str, local: str, data: str
) -> None:
    corpo = f"""
    <p>Olá, <strong>{nome_usuario}</strong>! 🎉</p>
    <p>Sua inscrição no evento <strong>{titulo_evento}</strong> foi confirmada.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr><td style="padding:8px;color:#555;width:80px;">📍 Local</td>
          <td style="padding:8px;"><strong>{local}</strong></td></tr>
      <tr style="background:#f9f9f9;">
          <td style="padding:8px;color:#555;">📅 Data</td>
          <td style="padding:8px;"><strong>{data}</strong></td></tr>
    </table>
    <p>Nos vemos lá! 🌿</p>
    """
    await enviar_email(
        para, f"Inscrição confirmada: {titulo_evento}",
        _base_template("Inscrição Confirmada!", corpo)
    )


async def email_inscricao_cancelada(
    para: str, nome_usuario: str, titulo_evento: str
) -> None:
    corpo = f"""
    <p>Olá, <strong>{nome_usuario}</strong>.</p>
    <p>Sua inscrição no evento <strong>{titulo_evento}</strong> foi cancelada com sucesso.</p>
    <p>Se mudar de ideia, você pode se inscrever novamente pelo app.</p>
    """
    await enviar_email(
        para, f"Inscrição cancelada: {titulo_evento}",
        _base_template("Inscrição Cancelada", corpo)
    )


async def email_evento_atualizado(
    para: str, nome_usuario: str, titulo_evento: str, local: str, data: str
) -> None:
    corpo = f"""
    <p>Olá, <strong>{nome_usuario}</strong>!</p>
    <p>O evento <strong>{titulo_evento}</strong> em que você está inscrito foi atualizado.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr><td style="padding:8px;color:#555;width:80px;">📍 Local</td>
          <td style="padding:8px;"><strong>{local}</strong></td></tr>
      <tr style="background:#f9f9f9;">
          <td style="padding:8px;color:#555;">📅 Data</td>
          <td style="padding:8px;"><strong>{data}</strong></td></tr>
    </table>
    <p>Acesse o app para ver todos os detalhes atualizados.</p>
    """
    await enviar_email(
        para, f"Evento atualizado: {titulo_evento}",
        _base_template("Evento Atualizado", corpo)
    )


async def email_evento_cancelado(
    para: str, nome_usuario: str, titulo_evento: str
) -> None:
    corpo = f"""
    <p>Olá, <strong>{nome_usuario}</strong>.</p>
    <p>Infelizmente o evento <strong>{titulo_evento}</strong> foi cancelado pelo organizador.</p>
    <p>Fique de olho nos próximos eventos na plataforma!</p>
    """
    await enviar_email(
        para, f"Evento cancelado: {titulo_evento}",
        _base_template("Evento Cancelado", corpo)
    )


async def email_redefinir_senha(
    para: str, nome_usuario: str, link_reset: str
) -> None:
    corpo = f"""
    <p>Olá, <strong>{nome_usuario}</strong>!</p>
    <p>Recebemos um pedido de redefinição de senha para sua conta.</p>
    <p style="text-align:center;margin:24px 0;">
      <a href="{link_reset}"
         style="background:#0d9488;color:#fff;padding:12px 24px;border-radius:8px;
                text-decoration:none;font-weight:bold;">
        Redefinir minha senha
      </a>
    </p>
    <p style="color:#888;font-size:13px;">
      Este link expira em <strong>1 hora</strong>. Se você não solicitou isso, ignore este e-mail.
    </p>
    """
    await enviar_email(
        para, "Redefinição de senha — Conecta Bairro",
        _base_template("Redefinição de Senha", corpo)
    )
