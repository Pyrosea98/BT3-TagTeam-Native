"""Verify every embedded launcher icon size matches the authored ICO bytes."""
import ctypes as c,struct
from ctypes import wintypes as w
from pathlib import Path
APP=Path(__file__).resolve().parent/'installer'
api=c.WinDLL('kernel32',use_last_error=True)
api.LoadLibraryExW.argtypes=[w.LPCWSTR,w.HANDLE,w.DWORD];api.LoadLibraryExW.restype=w.HMODULE
api.FindResourceW.argtypes=[w.HMODULE,c.c_void_p,c.c_void_p];api.FindResourceW.restype=w.HANDLE
api.LoadResource.argtypes=[w.HMODULE,w.HANDLE];api.LoadResource.restype=w.HANDLE
api.SizeofResource.argtypes=[w.HMODULE,w.HANDLE];api.SizeofResource.restype=w.DWORD
api.LockResource.argtypes=[w.HANDLE];api.LockResource.restype=c.c_void_p
api.FreeLibrary.argtypes=[w.HMODULE]
module=api.LoadLibraryExW(str(APP/'Play.exe'),None,2)
assert module, c.get_last_error()
def resource(kind,identity):
    handle=api.FindResourceW(module,identity,kind);assert handle,(kind,identity,c.get_last_error())
    size=api.SizeofResource(module,handle);data=api.LockResource(api.LoadResource(module,handle));assert data
    return c.string_at(data,size)
try:
    ico=(APP/'assets/BT3TagTeam.ico').read_bytes();group=resource(14,1)
    count=struct.unpack_from('<H',ico,4)[0];assert count==struct.unpack_from('<H',group,4)[0]==7
    for entry in range(count):
        source=struct.unpack_from('<BBBBHHII',ico,6+entry*16)
        target=struct.unpack_from('<BBBBHHIH',group,6+entry*14)
        # RC derives planes/bit-depth from the PNG/DIB payload; authored ICO
        # metadata may leave those two fields zero. Dimensions and bytes match.
        assert source[:4]==target[:4] and source[6]==target[6],(source,target)
        assert ico[source[7]:source[7]+source[6]]==resource(3,target[7])
    print('PASS: seven original authored icon sizes embedded byte-identically in Play.exe.')
finally:api.FreeLibrary(module)
