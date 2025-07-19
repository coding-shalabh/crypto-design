@echo off
echo Testing Binance API Connection...
echo.
echo Installing required dependencies...
pip install certifi cryptography aiohttp
echo.
echo Running connection test...
python test_binance_connection.py
echo.
pause