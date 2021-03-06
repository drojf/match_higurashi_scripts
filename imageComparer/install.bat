setlocal

:: Fix if batch file is run as administrator
pushd %~dp0

@echo off

:: Print whether the user already has python installed on path
where py >nul 2>&1
if errorlevel 1 (
    echo INFORMATION: No Python found on path
) else (
    echo WARNING: An existing Python was found on path
)

:: Running with -E disables checking of environment variables for python libs
:: This should prevent conflicts with any Python dists already on the user's computer.
echo INFORMATION: Using bundled Python to run installer
py -E compareImages.py

echo ----------------------------------------------------------- 
echo ------------ Batch file has finished executing ------------
echo ------------ Press any key to close this window -----------  
echo ----------------------------------------------------------- 
pause

popd