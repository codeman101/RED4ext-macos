// GogFixes: RED4ext plugin with fixes for the GOG macOS build (2.5.0) that cannot be done by patching other plugins.
//
// inkLogicController::OnUninitialize native impl (GOG 0x1340b20, Steam 0x41a9754) reads the handle at
// controller+0x50 as a layer proxy and calls into it. For Codeware's App::inkComponent that slot holds an unrelated
// object on GOG, so the call faults (ldr w9,[x8] with x8=6 in 0x1476efc). Skip the native impl for objects whose
// vtable lives in the Codeware plugin; every other controller runs the original.
#include <RED4ext/RED4ext.hpp>

#include <dlfcn.h>
#include <crt_externs.h>
#include <mach-o/dyld.h>
#include <mach-o/loader.h>

#include <cstdint>
#include <cstdio>
#include <cstring>

namespace
{
constexpr uint8_t kGogUuid[16] = {0x1D, 0xFA, 0x00, 0x5C, 0xED, 0x12, 0x30, 0x6F, 0xB3, 0x49, 0x67, 0xBE, 0x55, 0x5F, 0x2F, 0x72};
constexpr uint8_t kSteamUuid[16] = {0x7D, 0x73, 0x82, 0xD0, 0xEA, 0xDD, 0x36, 0xF0, 0xBA, 0x1C, 0xCE, 0xBE, 0xC1, 0xD5, 0xBE, 0xBC};
constexpr uintptr_t kGogOnUninitialize = 0x1340B20;
constexpr uintptr_t kSteamOnUninitialize = 0x41A9754;

using OnUninitialize_t = void (*)(void*);
OnUninitialize_t g_original = nullptr;

bool IsCodewareObject(void* aThis)
{
    if (!aThis)
        return false;
    Dl_info info{};
    if (!dladdr(*static_cast<void**>(aThis), &info) || !info.dli_fname)
        return false;
    return std::strstr(info.dli_fname, "Codeware") != nullptr;
}

// The native impl locks the object at controller+0x50 through its weak handle at +0x38/+0x40 (refcount block pointer).
// A small non-null value there is not a pointer: the controller holds the wrong kind of object and the call would fault.
bool HasBadLayerHandle(void* aThis)
{
    const auto object = *reinterpret_cast<char**>(static_cast<char*>(aThis) + 0x50);
    if (!object)
        return false;
    const auto block = *reinterpret_cast<uintptr_t*>(object + 0x40);
    return block != 0 && block < 0x10000;
}

void OnUninitialize_Hook(void* aThis)
{
    if (IsCodewareObject(aThis) || HasBadLayerHandle(aThis))
        return;
    g_original(aThis);
}

const mach_header_64* MainImage()
{
    return reinterpret_cast<const mach_header_64*>(_NSGetMachExecuteHeader());
}

bool ImageUuid(const mach_header_64* aHeader, uint8_t (&aOut)[16])
{
    auto* command = reinterpret_cast<const load_command*>(aHeader + 1);
    for (uint32_t i = 0; i < aHeader->ncmds; ++i)
    {
        if (command->cmd == LC_UUID)
        {
            std::memcpy(aOut, reinterpret_cast<const uuid_command*>(command)->uuid, 16);
            return true;
        }
        command = reinterpret_cast<const load_command*>(reinterpret_cast<const char*>(command) + command->cmdsize);
    }
    return false;
}
} // namespace

RED4EXT_C_EXPORT void RED4EXT_CALL Query(RED4ext::v1::PluginInfo* aInfo)
{
    aInfo->name = L"GogFixes";
    aInfo->author = L"cyberpunk-gog-port";
    aInfo->version = RED4EXT_V1_SEMVER(1, 0, 0);
    aInfo->runtime = RED4EXT_V1_RUNTIME_VERSION_INDEPENDENT;
    aInfo->sdk = RED4EXT_V1_SDK_VERSION_CURRENT;
}

RED4EXT_C_EXPORT uint32_t RED4EXT_CALL Supports()
{
    return RED4EXT_API_VERSION_1;
}

RED4EXT_C_EXPORT bool RED4EXT_CALL Main(RED4ext::v1::PluginHandle aHandle, RED4ext::v1::EMainReason aReason,
                                        const RED4ext::v1::Sdk* aSdk)
{
    if (aReason != RED4ext::v1::EMainReason::Load)
        return true;

    const auto* header = MainImage();
    uint8_t uuid[16];
    uintptr_t offset = 0;
    if (ImageUuid(header, uuid))
    {
        if (std::memcmp(uuid, kGogUuid, 16) == 0)
            offset = kGogOnUninitialize;
        else if (std::memcmp(uuid, kSteamUuid, 16) == 0)
            offset = kSteamOnUninitialize;
    }
    if (!offset)
    {
        std::fprintf(stderr, "[GogFixes] unknown game build, nothing hooked\n");
        return true;
    }

    const auto target = reinterpret_cast<void*>(reinterpret_cast<uintptr_t>(header) + offset);
    const bool ok = aSdk->hooking->Attach(aHandle, target, reinterpret_cast<void*>(&OnUninitialize_Hook),
                                          reinterpret_cast<void**>(&g_original));
    std::fprintf(stderr, "[GogFixes] inkLogicController::OnUninitialize hook at %p: %s\n", target,
                 ok ? "attached" : "FAILED");
    return true;
}
