from setuptools import setup

APP = ["launcher.py"]
OPTIONS = {
    "argv_emulation": False,
    "iconfile": "PremiumApps.icns",
    "packages": ["customtkinter"],
    "plist": {
        "CFBundleName": "Premium Apps",
        "CFBundleDisplayName": "Premium Apps",
        "CFBundleIdentifier": "com.ttmeticks.premiumapps",
        "CFBundleShortVersionString": "1.1.0",
        "LSMinimumSystemVersion": "12.0",
        "NSHighResolutionCapable": True,
    },
}

setup(
    name="Premium Apps",
    app=APP,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
