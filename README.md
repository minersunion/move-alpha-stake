# move-alpha-stake
Helper to safely secure Alpha from miners to another coldkey and earn yield with MUV.

This script provides an automated, efficient, and secure method to manage your Alpha token holdings while optimizing rewards.


## Prerequisites

Before you start, make sure you have the following installed on your system:

- Python 3.12 or higher
- `git`
- `pip`

---

## Installation Steps

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/minersunion/move-alpha-stake.git
cd move-alpha-stake
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install the Project in Editable Mode
```bash
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
```


## How to use?

### 1.
Edit the `wallets.py` file with your wallet names.

#### get_holding_wallet()
This is the secure coldkey you want to send your alpha stake to from the miners.

#### get_miner_wallets()
This is a list of your miner wallets that you want to move mined alpha stake from to the secure wallet.

### 2.

In your terminal, use this command to run the script:
```sh
python src/stake_move.py --netuid 64
```

You can pass the CLI arg `netuid` with a valid Bittensor subnet number.


## Description

This Python script automates the process of securing your staked Alpha tokens while ensuring they are generating yield. 

The script executes a two-step transaction sequence designed to minimize exposure on the miner coldkey while seamlessly delegating tokens for yield generation.

### Workflow

#### 1. Secure Alpha Tokens
Transfers Alpha tokens from the miner coldkey to the holding coldkey to reduce risk of holding large amounts on a miner.

#### 2. Delegate for Yield
Delegates the transferred Alpha tokens from the holding coldkey to the MUV hotkey, ensuring yield generation.

### Key Benefits

#### Enhanced Security: 
Reduces the amount of Alpha tokens stored on the miner coldkey, lowering risk.

#### Seamless Yield Generation: 
Delegated tokens will start to earn yield.

#### Zero Market Impact: 
Both actions (transfer & delegation) occur within the same block, ensuring they do not affect the Alpha token’s price chart.
