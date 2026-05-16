"""
cloudinary_service.py
---------------------
Upload de imagens para Cloudinary (produção) com fallback para sistema
de arquivos local (desenvolvimento).

Configure as variáveis de ambiente para ativar o Cloudinary:
    CLOUDINARY_CLOUD_NAME
    CLOUDINARY_API_KEY
    CLOUDINARY_API_SECRET

Se não estiverem definidas, o upload continua usando a pasta /uploads local.
"""

import os

_pronto = False


def _configurar() -> bool:
    global _pronto
    if _pronto:
        return True
    nome = os.getenv("CLOUDINARY_CLOUD_NAME")
    chave = os.getenv("CLOUDINARY_API_KEY")
    segredo = os.getenv("CLOUDINARY_API_SECRET")
    if nome and chave and segredo:
        import cloudinary
        cloudinary.config(cloud_name=nome, api_key=chave, api_secret=segredo, secure=True)
        _pronto = True
    return _pronto


def disponivel() -> bool:
    """Retorna True se o Cloudinary está configurado."""
    return _configurar()


def fazer_upload(conteudo: bytes, public_id: str) -> str:
    """
    Faz upload de imagem para o Cloudinary.
    Retorna a URL segura (https) da imagem.
    public_id determina o caminho no Cloudinary (ex: 'conecta_bairro/evento_5').
    """
    import cloudinary.uploader
    _configurar()
    resultado = cloudinary.uploader.upload(
        conteudo,
        public_id=public_id,
        overwrite=True,
        resource_type="image",
    )
    return resultado["secure_url"]


def deletar(public_id: str) -> None:
    """Remove uma imagem do Cloudinary pelo public_id."""
    import cloudinary.uploader
    _configurar()
    cloudinary.uploader.destroy(public_id, resource_type="image")


def public_id_do_evento(evento_id: int) -> str:
    """Retorna o public_id padrão para um evento."""
    return f"conecta_bairro/evento_{evento_id}"
