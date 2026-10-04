"""Data Vault entry point and backwards-compatible storage API."""
from vault_app.storage import DataVault
from vault_app.cli import main

__all__ = ["DataVault", "main"]

if __name__ == "__main__":
    raise SystemExit(main())
