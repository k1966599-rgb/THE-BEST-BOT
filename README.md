# THE-BEST-BOT: Elliott Wave Trading Bot

This is a sophisticated Telegram bot designed to perform Elliott Wave analysis on cryptocurrency markets to identify potential trading opportunities. It connects to the Bybit exchange to fetch market data and provides a user interface through Telegram for both automated scanning and manual analysis.

## ✨ Features

- **Automated Background Scanning:** Continuously scans a list of cryptocurrencies defined in `config.yaml`.
- **Elliott Wave Analysis:** Utilizes a complex engine to identify Elliott Wave patterns (Impulse, Zigzag, Flat, etc.).
- **Manual Analysis:** Allows users to request on-demand wave analysis for specific symbols and timeframes.
- **Telegram Interface:** All interactions are handled through a clean, button-based Telegram interface (in Arabic).
- **Auto-deployment:** Includes a shell script (`auto_bot.sh`) to keep the bot running and automatically update it with the latest code from the `main` branch.

## 🚀 Getting Started

Follow these steps to set up and run the bot on your own server.

### 1. Prerequisites

- Python 3.8+
- Git

### 2. Clone the Repository

```bash
git clone <your-repository-url>
cd <repository-directory>
```

### 3. Configure Environment Variables

The bot requires secret keys to function, such as the Telegram API token. These are managed through an environment file.

1.  **Create the environment file:** Copy the example file.
    ```bash
    cp .env.example .env
    ```

2.  **Edit the `.env` file:** Open the `.env` file with a text editor and add your secret keys.
    ```ini
    # .env
    TELEGRAM_TOKEN=YOUR_TELEGRAM_BOT_TOKEN_HERE
    BYBIT_API_KEY=YOUR_BYBIT_API_KEY_HERE
    BYBIT_API_SECRET=YOUR_BYBIT_API_SECRET_HERE
    ```

### 4. Install Dependencies

Install all the required Python packages using `pip`.

```bash
pip install -r requirements.txt
```

### 5. Running the Bot

You can run the bot directly for development or use the provided deployment script for a production-like environment.

#### Development

To run the bot in the foreground and see live output:

```bash
python bot.py
```
You can now interact with your bot on Telegram. Press `Ctrl-C` to stop.

#### Production / Deployment

The `auto_bot.sh` script is designed to run the bot persistently. It runs the bot in the background, logs output to `bot.log`, and automatically pulls the latest changes from Git.

**To start the deployment script:**

```bash
nohup ./auto_bot.sh > auto_bot_runner.log 2>&1 &
```

This will run the script in the background. To stop it, you will need to find its Process ID (PID) and kill it.

## ⚙️ Configuration

Most of the bot's behavior can be configured in `config.yaml`:
- `symbols_to_scan`: A list of all cryptocurrency symbols for the background scanner to analyze.
- `pivot_sensitivity`: Settings for pivot point detection.
- `elliott_wave`: Fine-tune the rules for identifying different wave patterns.
- `indicators`: Configure parameters for technical indicators like RSI and MACD.

## 📂 Project Structure

- `bot.py`: The main entry point for the application.
- `auto_bot.sh`: Deployment and auto-update script.
- `config.yaml`: Main configuration file for strategies and symbols.
- `.env.example`: Template for environment variables (secrets).
- `requirements.txt`: List of Python dependencies.
- `src/`: Contains all the core application logic.
  - `bot_interface/`: Manages the Telegram UI and command handlers.
  - `data/`: Handles data fetching from Bybit.
  - `elliott_wave_engine/`: The core Elliott Wave analysis logic.
  - `strategies/`: Defines trading strategies based on analysis.
  - `utils/`: Utility functions, including the configuration loader.
- `tests/`: Contains unit tests for the project.
