@echo off
echo NONMS Local WGS Explorer
echo Installing requirements if needed...
python -m pip install -r requirements_local.txt
echo.
echo Starting local app...
python -m streamlit run local_wgs_app.py
pause
