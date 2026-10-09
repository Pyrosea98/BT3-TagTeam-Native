// No-console entry point; the temporary embedded controller has no system dependency.
#define NOMINMAX
#include <windows.h>
#include <string>
int WINAPI wWinMain(HINSTANCE,HINSTANCE,PWSTR,int){wchar_t path[32768];DWORD size=GetModuleFileNameW(nullptr,path,32768);if(!size || size>=32768)return 1;
    std::wstring root(path,size);root.resize(root.find_last_of(L"\\/"));auto executable=root+L"\\runtime\\pythonw.exe";auto command=L"\""+executable+L"\" -I \""+root+L"\\app.pyw\"";
    STARTUPINFOW startup{};startup.cb=sizeof(startup);PROCESS_INFORMATION process{};
    if(!CreateProcessW(executable.c_str(),command.data(),nullptr,nullptr,FALSE,CREATE_NO_WINDOW,nullptr,root.c_str(),&startup,&process)){MessageBoxW(nullptr,L"The app runtime is missing. Please reinstall.",L"BT3 Tag Team",MB_OK|MB_ICONERROR);return 1;}
    CloseHandle(process.hThread);CloseHandle(process.hProcess);return 0;
}
