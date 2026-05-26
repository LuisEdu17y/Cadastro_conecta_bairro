"""
email_service.py
----------------
Envio de e-mails. Duas opções (em ordem de preferência):

1. RESEND_API_KEY definida → usa API HTTP do Resend (recomendado)
2. SMTP_HOST + SMTP_USER + SMTP_PASS → usa SMTP clássico

Configure no Render (ou .env local):
    RESEND_API_KEY   chave da API do Resend (começa com re_...)
    EMAIL_FROM       remetente (ex: onboarding@resend.dev)
    --- ou ---
    SMTP_HOST / SMTP_PORT / SMTP_USER / SMTP_PASS / EMAIL_FROM
"""

import os
import json
import smtplib
import logging
import urllib.request
import urllib.error
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Envio
# ──────────────────────────────────────────────

def _enviar_sync(para: str, assunto: str, html: str) -> None:
    brevo_key = os.getenv("BREVO_API_KEY", "")
    if brevo_key:
        _via_brevo_api(para, assunto, html, brevo_key)
        return

    resend_key = os.getenv("RESEND_API_KEY", "")
    if resend_key:
        _via_resend_api(para, assunto, html, resend_key)
        return

    host  = os.getenv("SMTP_HOST", "")
    port  = int(os.getenv("SMTP_PORT", "587"))
    user  = os.getenv("SMTP_USER", "")
    senha = os.getenv("SMTP_PASS", "")

    if not (host and user and senha):
        logger.info(
            "[EMAIL - sem configuração]\n"
            f"  Para:    {para}\n"
            f"  Assunto: {assunto}\n"
            f"  Corpo:   {html[:200]}..."
        )
        return

    remetente = os.getenv("EMAIL_FROM", user)
    msg = MIMEMultipart("alternative")
    msg["Subject"] = assunto
    msg["From"]    = remetente
    msg["To"]      = para
    msg.attach(MIMEText(html, "html", "utf-8"))

    TIMEOUT = 15
    if port == 465:
        with smtplib.SMTP_SSL(host, port, timeout=TIMEOUT) as smtp:
            smtp.login(user, senha)
            smtp.sendmail(remetente, [para], msg.as_string())
    else:
        with smtplib.SMTP(host, port, timeout=TIMEOUT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(user, senha)
            smtp.sendmail(remetente, [para], msg.as_string())

    logger.info(f"[EMAIL SMTP] Enviado para {para}: {assunto}")


def _via_brevo_api(para: str, assunto: str, html: str, api_key: str) -> None:
    remetente = os.getenv("EMAIL_FROM", "")
    payload = json.dumps({
        "sender":      {"name": "Conecta Bairro", "email": remetente},
        "to":          [{"email": para}],
        "subject":     assunto,
        "htmlContent": html,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=payload,
        headers={"api-key": api_key, "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resultado = json.loads(resp.read())
            print(f"[EMAIL Brevo OK] para={para} id={resultado.get('messageId')}", flush=True)
    except urllib.error.HTTPError as exc:
        corpo_erro = exc.read().decode("utf-8", errors="replace")
        print(f"[EMAIL Brevo ERRO] status={exc.code} body={corpo_erro}", flush=True)
        raise


def _via_resend_api(para: str, assunto: str, html: str, api_key: str) -> None:
    remetente = os.getenv("EMAIL_FROM", "onboarding@resend.dev")
    payload = json.dumps({
        "from":    remetente,
        "to":      [para],
        "subject": assunto,
        "html":    html,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type":  "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resultado = json.loads(resp.read())
            logger.info(f"[EMAIL Resend] Enviado para {para} — id: {resultado.get('id')}")
            print(f"[EMAIL Resend OK] para={para} id={resultado.get('id')}", flush=True)
    except urllib.error.HTTPError as exc:
        corpo_erro = exc.read().decode("utf-8", errors="replace")
        print(f"[EMAIL Resend ERRO] status={exc.code} body={corpo_erro}", flush=True)
        raise


def _enviar_sync_seguro(para: str, assunto: str, html: str) -> None:
    try:
        _enviar_sync(para, assunto, html)
    except Exception as exc:
        print(f"[EMAIL FALHA] para={para} erro={exc}", flush=True)
        logger.error(f"Falha ao enviar e-mail para {para}: {exc}")


# ──────────────────────────────────────────────
# Interface assíncrona (fire-and-forget)
# ──────────────────────────────────────────────

def enviar_email_bg(background_tasks, para: str, assunto: str, html: str) -> None:
    """Registra envio como BackgroundTask do FastAPI (retorna imediatamente)."""
    background_tasks.add_task(_enviar_sync_seguro, para, assunto, html)


# ──────────────────────────────────────────────
# Templates
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


def _html_inscricao_confirmada(nome: str, titulo: str, local: str, data: str) -> str:
    return _base_template("Inscrição Confirmada!", f"""
    <p>Olá, <strong>{nome}</strong>! 🎉</p>
    <p>Sua inscrição no evento <strong>{titulo}</strong> foi confirmada.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr><td style="padding:8px;color:#555;width:80px;">📍 Local</td>
          <td style="padding:8px;"><strong>{local}</strong></td></tr>
      <tr style="background:#f9f9f9;">
          <td style="padding:8px;color:#555;">📅 Data</td>
          <td style="padding:8px;"><strong>{data}</strong></td></tr>
    </table>
    <p>Nos vemos lá! 🌿</p>
    """)


def _html_inscricao_cancelada(nome: str, titulo: str) -> str:
    return _base_template("Inscrição Cancelada", f"""
    <p>Olá, <strong>{nome}</strong>.</p>
    <p>Sua inscrição no evento <strong>{titulo}</strong> foi cancelada com sucesso.</p>
    <p>Se mudar de ideia, você pode se inscrever novamente pelo app.</p>
    """)


def _html_evento_atualizado(nome: str, titulo: str, local: str, data: str) -> str:
    return _base_template("Evento Atualizado", f"""
    <p>Olá, <strong>{nome}</strong>!</p>
    <p>O evento <strong>{titulo}</strong> em que você está inscrito foi atualizado.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr><td style="padding:8px;color:#555;width:80px;">📍 Local</td>
          <td style="padding:8px;"><strong>{local}</strong></td></tr>
      <tr style="background:#f9f9f9;">
          <td style="padding:8px;color:#555;">📅 Data</td>
          <td style="padding:8px;"><strong>{data}</strong></td></tr>
    </table>
    <p>Acesse o app para ver todos os detalhes atualizados.</p>
    """)


def _html_evento_cancelado(nome: str, titulo: str) -> str:
    return _base_template("Evento Cancelado", f"""
    <p>Olá, <strong>{nome}</strong>.</p>
    <p>Infelizmente o evento <strong>{titulo}</strong> foi cancelado pelo organizador.</p>
    <p>Fique de olho nos próximos eventos na plataforma!</p>
    """)


def _html_vaga_disponivel(nome: str, titulo: str, local: str, data: str) -> str:
    return _base_template("Vaga Disponível!", f"""
    <p>Olá, <strong>{nome}</strong>! 🎉</p>
    <p>Uma vaga abriu no evento <strong>{titulo}</strong> e você foi inscrito automaticamente por estar na lista de espera.</p>
    <table style="width:100%;border-collapse:collapse;margin:16px 0;">
      <tr><td style="padding:8px;color:#555;width:80px;">📍 Local</td>
          <td style="padding:8px;"><strong>{local}</strong></td></tr>
      <tr style="background:#f9f9f9;">
          <td style="padding:8px;color:#555;">📅 Data</td>
          <td style="padding:8px;"><strong>{data}</strong></td></tr>
    </table>
    <p>Sua presença está confirmada. Nos vemos lá! 🌿</p>
    """)


def _html_redefinir_senha(nome: str, link: str) -> str:
    return _base_template("Redefinição de Senha", f"""
    <p>Olá, <strong>{nome}</strong>!</p>
    <p>Recebemos um pedido de redefinição de senha para sua conta.</p>
    <p style="text-align:center;margin:24px 0;">
      <a href="{link}"
         style="background:#0d9488;color:#fff;padding:12px 24px;border-radius:8px;
                text-decoration:none;font-weight:bold;">
        Redefinir minha senha
      </a>
    </p>
    <p style="color:#888;font-size:13px;">
      Este link expira em <strong>1 hora</strong>.
      Se você não solicitou isso, ignore este e-mail.
    </p>
    """)


# ──────────────────────────────────────────────
# Funções públicas (compatíveis com routers)
# ──────────────────────────────────────────────

async def email_inscricao_confirmada(para, nome, titulo, local, data):
    import asyncio
    await asyncio.to_thread(
        _enviar_sync_seguro, para,
        f"Inscrição confirmada: {titulo}",
        _html_inscricao_confirmada(nome, titulo, local, data),
    )


async def email_inscricao_cancelada(para, nome, titulo):
    import asyncio
    await asyncio.to_thread(
        _enviar_sync_seguro, para,
        f"Inscrição cancelada: {titulo}",
        _html_inscricao_cancelada(nome, titulo),
    )


async def email_evento_atualizado(para, nome, titulo, local, data):
    import asyncio
    await asyncio.to_thread(
        _enviar_sync_seguro, para,
        f"Evento atualizado: {titulo}",
        _html_evento_atualizado(nome, titulo, local, data),
    )


async def email_evento_cancelado(para, nome, titulo):
    import asyncio
    await asyncio.to_thread(
        _enviar_sync_seguro, para,
        f"Evento cancelado: {titulo}",
        _html_evento_cancelado(nome, titulo),
    )


async def email_redefinir_senha(para, nome, link):
    import asyncio
    await asyncio.to_thread(
        _enviar_sync_seguro, para,
        "Redefinição de senha — Conecta Bairro",
        _html_redefinir_senha(nome, link),
    )


async def email_vaga_disponivel(para, nome, titulo, local, data):
    import asyncio
    await asyncio.to_thread(
        _enviar_sync_seguro, para,
        f"Vaga disponível: {titulo}",
        _html_vaga_disponivel(nome, titulo, local, data),
    )
