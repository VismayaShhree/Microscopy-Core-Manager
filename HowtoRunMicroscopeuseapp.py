#Create new conda environment
conda create --name microscope_use  python=3.8

#Activate the new conda environment so can isntall the package necessary to run the particular ptogram
conda activate microscope_use

cd Documents/GitHub/Microscope_use

#Install pyinstaller in the conda
pip install pyinstaller
pip install tkcalendar
pip install babel


# Run pyinstaller to create standalone executable
#--onefile bundles everything into a single executable.
#--noconsole prevents a command prompt window from appearing (useful for GUI applications).
pyinstaller --onefile --noconsole Microscope_use.py

#check the dist directory inside your project folder. 
# You should find the Microscope_use executable there.
#Also the folder with all the deveolper files and other necessary folders 
#run the app and check if there is any issue 
./dist/Microscope_use/Microscope_use

# if there is an erroer running the app or have some issues with the complete file  check with .spec file

nano Microscope_use.spec


#check the file and add the path where the script is and also check for hiddenimports like bable 
# Use the following information to update the .spec file
block_cipher = None

a = Analysis(
    ['Microscope_use.py'],
    pathex=['/Users/Dhanashree/Documents/GitHub/Microscope_use'],
    binaries=[],
    datas=[],
    hiddenimports=['tkcalendar', 'babel', 'babel.numbers', 'babel.dates', 'babel.localedata'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Microscope_use',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='Microscope_use'
)
app = BUNDLE(
    exe,
    name='Microscope_use.app',
    icon=None,
    bundle_identifier=None,
)

#save the file ctrO--> Enter --> ctrlx

#rebuild the application
pyinstaller Microscope_use.spec

#repeat the run line 22





