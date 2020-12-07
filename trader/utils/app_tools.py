from pathlib import Path

from trader.credentials import Credentials


def project_root() -> Path:
    """
    返回项目根路径
    """
    return Path(__file__).parent.parent


def load_dev_credentials() -> Credentials:
    """
    开发时装载用户凭证
    """
    credentials_path = project_root() / '.local/credentials.json'
    if not credentials_path.exists():
        raise RuntimeError(f"【错误】用户凭证文件不存在: {credentials_path}")

    return Credentials.load_from_json(credentials_path)
