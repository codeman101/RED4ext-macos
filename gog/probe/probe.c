// Read-only probe: logs load info and checks candidate bytes. Patches nothing.
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#include <mach/mach.h>
#include <stdio.h>
#include <string.h>
#include <stdint.h>

#define LOG "/private/tmp/claude-501/-Applications-Cyberpunk-2077/1b644566-a78d-4c62-a2b9-9aa0ddf5cd6e/scratchpad/probe/probe.log"

static FILE *out;

static void region(const char *tag, uintptr_t addr) {
    vm_address_t a = addr;
    vm_size_t sz = 0;
    vm_region_basic_info_data_64_t info;
    mach_msg_type_number_t n = VM_REGION_BASIC_INFO_COUNT_64;
    mach_port_t obj;
    kern_return_t kr = vm_region_64(mach_task_self(), &a, &sz, VM_REGION_BASIC_INFO_64,
                                    (vm_region_info_t)&info, &n, &obj);
    fprintf(out, "%s addr=%#lx kr=%d region=%#lx+%#lx prot=%d max=%d\n", tag, (unsigned long)addr,
            kr, (unsigned long)a, (unsigned long)sz, info.protection, info.max_protection);
}

static void dump(const char *tag, uintptr_t addr) {
    fprintf(out, "%s %#lx:", tag, (unsigned long)addr);
    for (int i = 0; i < 16; i++) fprintf(out, " %02x", ((uint8_t *)addr)[i]);
    fprintf(out, "\n");
}

__attribute__((constructor)) static void probe(void) {
    out = fopen(LOG, "a");
    if (!out) return;
    setvbuf(out, NULL, _IOLBF, 0);
    uint32_t idx = 0;
    for (uint32_t i = 0; i < _dyld_image_count(); i++)
        if (strstr(_dyld_get_image_name(i), "MacOS/Cyberpunk2077")) { idx = i; break; }
    const struct mach_header_64 *mh = (const void *)_dyld_get_image_header(idx);
    intptr_t slide = _dyld_get_image_vmaddr_slide(idx);
    fprintf(out, "== image %u %s\nmh=%p slide=%#lx\n", idx, _dyld_get_image_name(idx), mh, (unsigned long)slide);
    const struct load_command *lc = (const void *)(mh + 1);
    for (uint32_t i = 0; i < mh->ncmds; i++, lc = (const void *)((const char *)lc + lc->cmdsize)) {
        if (lc->cmd == LC_UUID) {
            const uint8_t *u = ((const struct uuid_command *)lc)->uuid;
            fprintf(out, "uuid=");
            for (int k = 0; k < 16; k++) fprintf(out, "%02X", u[k]);
            fprintf(out, "\n");
        }
    }
    uintptr_t base = (uintptr_t)mh;
    region("text", base + 0x1000);
    // candidates: Main* 0xF7B728, CString_dtor 0x2912C, main() 0x32380
    dump("main", base + 0x32380);
    dump("Main*", base + 0xF7B728);
    dump("CString_dtor", base + 0x2912C);
    fclose(out);
}
