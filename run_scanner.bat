@echo off
cd /d C:\TradingHQ

echo [%date% %time%] Scanner started >> C:\TradingHQ\output\scanner_log.txt

py scanner.py >> C:\TradingHQ\output\scanner_log.txt 2>&1

echo [%date% %time%] Scanner finished >> C:\TradingHQ\output\scanner_log.txt
echo. >> C:\TradingHQ\output\scanner_log.txt