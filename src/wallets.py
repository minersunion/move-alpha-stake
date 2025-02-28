from bittensor_wallet.wallet import Wallet


def get_holding_wallet() -> Wallet:
    # Secure holding wallet where the alpha tokens will be stored and earn yield
    return Wallet(name="my-hodl", hotkey=None)


def get_miner_wallets() -> list[Wallet]:
    # Wallets where the alpha tokens are mined and not earning yield
    return [Wallet(name="miner1", hotkey="miner1"), Wallet(name="miner2", hotkey="miner2")]


def get_miner_wallet_names() -> list[str]:
    return [wallet.name for wallet in get_miner_wallets()]


if __name__ == "__main__":
    print(get_miner_wallet_names())
