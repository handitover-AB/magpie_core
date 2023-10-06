#!/usr/bin/env pwsh

#Requires -Version 7.3

<#
    .SYNOPSIS
        * FOR WINDOWS USERS *
        
        Set up/rebuild a virtual Python environment for local test development with Magpie

        - Install a virtual Python environment with all third-party dependencies.
        - Install Playwright browsers
        - Check if Graphviz is installed, prompt the user to install it if not.
        
        Run from the project root.
#>


$ErrorActionPreference = "Stop"  # Stop on first error, if any

# Deactivate the current Python environment (if any)
try {
    deactivate
} catch {}


# Remove the .pyenv directory, if present:
try {
    Remove-Item ".pyenv" -Recurse
} catch {}


# Stop if there is no Python:
Write-Host "Checking Python version:"
python -V


# Create a Python environment and install dependencies:
try {
    Write-Host ""
    Write-Host "(Re-)building a virtual Python environment:"
    python -m venv .pyenv
    Write-Host "Done."

    Write-Host ""
    Write-Host "Activating the virtual environment:"
    .\.pyenv\Scripts\activate
    Write-Host "Done."

    Write-Host ""
    Write-Host "Upgrading pip:"
    python -m pip install --upgrade pip wheel
    Write-Host "Done."

    Write-Host ""
    Write-Host "Installing dependencies:"
    python -m pip install -r requirements.txt
    Write-Host "Done."

    Write-Host ""
    Write-Host "Installing Playwright browsers:"
    playwright install
    Write-Host "Done."
} catch {
    Write-Host ".--------------------------------------------------."
    Write-Host "|  ❌ Something went wrong during the creation of  |"
    Write-Host "|     the virtual Python environment. See output   |"
    Write-Host "|     above for clues of what to do next.          |"
    Write-Host "'--------------------------------------------------'"
    exit
}

Write-Host ""
Write-Host "Checking if graphviz is installed:"
try {
    dot -V
    Write-Host "Done."
} catch {
    Write-Host ".-------------------------------------------------------------------."
    Write-Host "|  You need to install Graphviz. Please follow these instructions:  |"
    Write-Host "|  https://www.graphviz.org/download                                |"
    Write-Host "'-------------------------------------------------------------------'"
    exit
}

Write-Host ""
Write-Host ".----------------------------------------."
Write-Host "|  OK - you're good to go! Have fun 😊!  |"
Write-Host "'----------------------------------------'"
