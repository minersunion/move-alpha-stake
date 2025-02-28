import argparse
import asyncio
from typing import Optional

from bittensor.core.async_subtensor import AsyncSubtensor, StakeInfo, get_async_subtensor
from bittensor.utils.balance import Balance
from bittensor.utils.btlogging import logging
from bittensor_wallet import Wallet
from bittensor_wallet.errors import KeyFileError

# Edit your wallets.py file to add your wallet names
from wallets import get_holding_wallet, get_miner_wallets

logging.on()
logging.set_debug(True)


class StakeHandler:
    muv_hotkey = "5DQ2Geab6G25wiZ4jGH6wJM8fekrm1QhV9hrRuntjBVxxKZm"  # Miners Union Validator hotkey for staking your alpha token and earn yield
    miner_wallets: list[Wallet]  # Miner wallets where the alpha tokens are unsafely stored and not earning yield
    holding_wallet: Wallet  # Wallet where the alpha tokens will be stored safely and earn yield
    netuid: int  # Subnet id of the Alpha stake you want to move
    subtensor: AsyncSubtensor

    def __init__(self, miner_wallets: list[Wallet], holding_wallet: Wallet, netuid: int, subtensor: AsyncSubtensor):
        self.miner_wallets = miner_wallets
        self.holding_wallet = holding_wallet
        self.netuid = netuid
        self.subtensor = subtensor

    async def get_miner_stake(self, miner_wallet: Wallet) -> Balance:
        """
        Get the alpha stake of the miner wallet. (The alpha tokens that the miner has mined)
        """
        coldkey = miner_wallet.coldkeypub.ss58_address
        hotkey = miner_wallet.hotkey.ss58_address
        netuid = self.netuid

        stake: dict[int, StakeInfo] = await self.subtensor.get_stake_for_coldkey_and_hotkey(
            coldkey_ss58=coldkey,
            hotkey_ss58=hotkey,
            netuids=[netuid],
        )
        alpha_stake: StakeInfo = stake.get(netuid, None)

        logging.debug(f"Stake for {hotkey}: {alpha_stake}")
        return alpha_stake.stake if alpha_stake else Balance.from_float(0, netuid=netuid)

    async def get_holding_wallet_stake(self) -> Balance:
        """
        Get the alpha stake of the holding wallet that is delegated to MUV.
        """
        coldkey = self.holding_wallet.coldkeypub.ss58_address
        netuid = self.netuid

        stakes: list[StakeInfo] = await self.subtensor.get_stake_for_coldkey(coldkey_ss58=coldkey)
        alpha_stake: Optional[StakeInfo] = next((s for s in stakes if s.netuid == netuid and s.hotkey_ss58 == self.muv_hotkey), None)
        stake: Balance = alpha_stake.stake if alpha_stake else Balance.from_float(0, netuid=netuid)

        logging.debug(f"Stake for {coldkey} on {netuid} with MUV: {stake}")
        return stake

    async def send_alpha_stake_to_secure_wallet(self, miner_wallet: Wallet):
        """
        Transfer all the stake from the miner wallet to your holding wallet.
        Context: The holding wallet is a coldkey that is not used for mining and is considered secure, unlike a miner coldkey.
        """
        alpha_amount: Balance = await self.get_miner_stake(miner_wallet)

        origin_hotkey: str = miner_wallet.hotkey.ss58_address
        holding_wallet_coldkey: str = self.holding_wallet.coldkeypub.ss58_address

        return await self.subtensor.transfer_stake(
            wallet=miner_wallet,
            destination_coldkey_ss58=holding_wallet_coldkey,
            hotkey_ss58=origin_hotkey,
            origin_netuid=self.netuid,
            destination_netuid=self.netuid,
            amount=alpha_amount,
        )

    async def delegate_alpha_stake_to_muv(self, miner_wallet: Wallet) -> bool:  # type: ignore
        """
        Delegate all the subnet alpha stake found on the holding wallet to the MUV hotkey to earn yield.
        """
        results: list[bool] = []

        stakes: list[StakeInfo] = await self.subtensor.get_stake_for_coldkey(self.holding_wallet.coldkeypub.ss58_address)

        stakes_to_delegate: list[StakeInfo] = [s for s in stakes if s.netuid == self.netuid and s.hotkey_ss58 != self.muv_hotkey]

        if len(stakes_to_delegate) > 0:
            try:
                logging.info(f"🔓 Unlocking wallet {self.holding_wallet.name}")
                self.holding_wallet.unlock_coldkey()
            except KeyFileError as e:
                logging.error(f"Error unlocking wallet {self.holding_wallet.name}: {e}")
                return False

        for s in stakes_to_delegate:
            logging.debug(f"Stake on {self.holding_wallet.name} that needs to be delegated to MUV: {s}")

            stake_to_delegate: Balance = s.stake  # Alpha tokens to delegate to MUV

            success: bool = await self.subtensor.move_stake(
                wallet=self.holding_wallet,
                origin_hotkey=miner_wallet.hotkey.ss58_address,
                origin_netuid=self.netuid,
                destination_hotkey=self.muv_hotkey,
                destination_netuid=self.netuid,
                amount=stake_to_delegate,
            )

            results.append(success)

        return all(results)

    async def secure_alpha_tokens_and_stake_to_muv(self):
        """
        To avoid keeping too much value on a miner coldkey, we need to secure the alpha tokens by sending them to the holding wallet.
        So the logic is this: Transfer the alpha tokens from miner coldkey to holding coldkey.
        Then, to earn yield on your alpha holdings, we delegate the alpha tokens to the muv hotkey from the holding wallet.
        This operation does not affect the alpha token's chart because actions are treated in the same block.
        """

        logging.info(f"Moving stake from miner wallets to holding wallet {self.holding_wallet.name}")

        for miner_wallet in self.miner_wallets:
            logging.info(f"Processing wallet {miner_wallet.name}")

            await self.send_alpha_stake_to_secure_wallet(miner_wallet)
            await self.delegate_alpha_stake_to_muv(miner_wallet)

            delegated_stake_after_ops = await self.get_holding_wallet_stake()
            logging.info(f"New stake delegated to MUV = {delegated_stake_after_ops}")


def get_cli_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()

    parser.add_argument("--netuid", type=int, help="Subnet ID of the Alpha stake you want to move (ex: 64).", required=True)

    args = parser.parse_args()
    logging.debug(f"CLI args: {args}")

    return args


async def main():
    args: argparse.Namespace = get_cli_args()

    netuid: int = args.netuid

    miner_wallets: list[Wallet] = get_miner_wallets()
    holding_wallet: Wallet = get_holding_wallet()

    subtensor: AsyncSubtensor = await get_async_subtensor(network="finney")

    stake_handler = StakeHandler(miner_wallets=miner_wallets, holding_wallet=holding_wallet, netuid=netuid, subtensor=subtensor)

    await stake_handler.secure_alpha_tokens_and_stake_to_muv()


if __name__ == "__main__":
    asyncio.run(main())
