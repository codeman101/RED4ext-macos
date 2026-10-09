#include "App.hpp"
#include "Image.hpp"
#include "Platform.hpp"
#include "Utils.hpp"

#ifdef RED4EXT_PLATFORM_MACOS

void EnableBackgroundModeIfRequested(); // Platform/Background.cpp

#include <csignal>
#include <cstdio>
#include <cstdlib>
#include <execinfo.h>
#include <unistd.h>

// LOCAL DIAGNOSTIC (cp2077-mac R30, env-gated, not for upstream): RED4EXT_MAC_CRASHTRACE=1 prints the faulting address and a backtrace of a
// SIGSEGV/SIGBUS to stderr. Used to find why the loader dies before its first log line.
static void R30CrashTrace(int aSig, siginfo_t* aInfo, void*)
{
    char line[96];
    const int n = std::snprintf(line, sizeof(line), "[red4ext-diag] signal %d at %p\n", aSig, aInfo ? aInfo->si_addr : nullptr);
    write(2, line, n > 0 ? n : 0);
    void* frames[64];
    const int count = backtrace(frames, 64);
    backtrace_symbols_fd(frames, count, 2);
    _exit(128 + aSig);
}

__attribute__((constructor)) static void RED4extInit()
{
    if (const char* trace = std::getenv("RED4EXT_MAC_CRASHTRACE"); trace && trace[0] == '1')
    {
        struct sigaction action = {};
        action.sa_sigaction = &R30CrashTrace;
        action.sa_flags = SA_SIGINFO;
        sigaction(SIGSEGV, &action, nullptr);
        sigaction(SIGBUS, &action, nullptr);
        std::fprintf(stderr, "[red4ext-diag] constructor entered\n");
    }
    try
    {
        const auto image = Image::Get();
        if (!image->IsCyberpunk())
        {
            return;
        }

        EnableBackgroundModeIfRequested();

        // Construct only: App::Startup() (systems and plugins) runs from the hook on the game's main(), once the
        // game's static initializers have created its memory pools and singletons.
        App::Construct();
    }
    catch (const std::exception& e)
    {
        SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An exception occured while loading RED4ext.\n\n{}",
                                            Utils::Widen(e.what()));
    }
    catch (...)
    {
        SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An unknown exception occured while loading RED4ext.");
    }
}

__attribute__((destructor)) static void RED4extShutdown()
{
    try
    {
        const auto image = Image::Get();
        if (!image->IsCyberpunk())
        {
            return;
        }

        // Normally already done by the atexit handler registered from the main() hook; this covers a process
        // that exits before main() was reached.
        auto app = App::Get();
        if (!app)
        {
            return;
        }

        app->Shutdown();
        App::Destruct();
    }
    catch (const std::exception& e)
    {
        SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An exception occured while unloading RED4ext.\n\n{}",
                                            Utils::Widen(e.what()));
    }
    catch (...)
    {
        SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An unknown exception occured while unloading RED4ext.");
    }
}

#else

BOOL APIENTRY DllMain(HMODULE aModule, DWORD aReason, LPVOID aReserved)
{
    RED4EXT_UNUSED_PARAMETER(aReserved);

    switch (aReason)
    {
    case DLL_PROCESS_ATTACH:
    {
        DisableThreadLibraryCalls(aModule);

        try
        {
            const auto image = Image::Get();
            if (!image->IsCyberpunk())
            {
                break;
            }

            App::Construct();
        }
        catch (const std::exception& e)
        {
            SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An exception occured while loading RED4ext.\n\n{}",
                                                Utils::Widen(e.what()));
        }
        catch (...)
        {
            SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An unknown exception occured while loading RED4ext.");
        }

        break;
    }
    case DLL_PROCESS_DETACH:
    {
        if (aReserved != nullptr)
        {
            // DLL is being unloaded due to process termination, skip cleanup.
            // https://learn.microsoft.com/en-us/windows/win32/dlls/dllmain
            break;
        }

        try
        {
            const auto image = Image::Get();
            if (!image->IsCyberpunk())
            {
                break;
            }

            App::Destruct();
        }
        catch (const std::exception& e)
        {
            SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An exception occured while unloading RED4ext.\n\n{}",
                                                Utils::Widen(e.what()));
        }
        catch (...)
        {
            SHOW_MESSAGE_BOX_AND_EXIT_FILE_LINE("An unknown exception occured while unloading RED4ext.");
        }

        break;
    }
    }

    return TRUE;
}

#endif
