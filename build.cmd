if "%VIRTUAL_ENV%" == "" (
    echo "Command needs to be executed in a virtual env"
) else (
    pyinstaller --name "foxhole_stockpiles" --noconfirm --onefile --windowed --add-data "%~dp0/foxhole_stockpiles;foxhole_stockpiles/" "%~dp0/foxhole_stockpiles/main.py"
)
