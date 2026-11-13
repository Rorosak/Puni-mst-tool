@echo off
chcp 65001 > nul
title Mst Tool - Yo-kai Watch Puni Puni / Wibble Wobble
cd /d "%~dp0"

echo ===================================================================
echo             Lancement de Mst Tool (Yo-kai Editor)
echo ===================================================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERREUR] Python n'a pas ete trouve dans votre variable d'environnement PATH.
    echo Veuillez installer Python ou verifier qu'il est bien coche dans le PATH.
    echo.
    pause
    exit /b 1
)

python mainFr17.py
if %errorlevel% neq 0 (
    echo.
    echo ===================================================================
    echo [ATTENTION] L'application s'est fermee avec une erreur (Code: %errorlevel%).
    echo ===================================================================
    pause
)
