# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(1, 5, 0, 0),
        prodvers=(1, 5, 0, 0),
        mask=0x3f,
        flags=0x0,
        OS=0x40004,
        fileType=0x1,
        subtype=0x0,
        date=(0, 0)
    ),
    kids=[
        StringFileInfo(
            [
                StringTable(
                    u'040904B0',
                    [
                        StringStruct(u'CompanyName', u'Scribe4me'),
                        StringStruct(u'FileDescription', u'Scribe4me — Speech-to-text com IA'),
                        StringStruct(u'FileVersion', u'1.5.0.0'),
                        StringStruct(u'InternalName', u'Scribe4me'),
                        StringStruct(u'LegalCopyright', u'Copyright 2026 Scribe4me. All rights reserved.'),
                        StringStruct(u'OriginalFilename', u'Scribe4me.exe'),
                        StringStruct(u'ProductName', u'Scribe4me'),
                        StringStruct(u'ProductVersion', u'1.5.0.0'),
                    ]
                )
            ]
        ),
        VarFileInfo([VarStruct(u'Translation', [0x0409, 1200])])
    ]
)
