// Read-only: after a delay, find globals in the main image that point to heap objects with a vtable.
#include <mach-o/dyld.h>
#include <mach-o/loader.h>
#include <mach/mach.h>
#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include <unistd.h>

#define DIR "/private/tmp/claude-501/-Applications-Cyberpunk-2077/1b644566-a78d-4c62-a2b9-9aa0ddf5cd6e/scratchpad/probe/"

static uintptr_t base, text_lo, text_hi, img_hi;
static struct { uintptr_t lo, hi; char name[17]; } data[16];
static int ndata;

static int rd(uintptr_t a, void *buf, size_t n) {
    vm_size_t o = 0;
    return vm_read_overwrite(mach_task_self(), a, n, (vm_address_t)buf, &o) == KERN_SUCCESS && o == n;
}
static int in_text(uintptr_t p) { return p >= text_lo && p < text_hi; }
static int in_data(uintptr_t p) {
    for (int i = 0; i < ndata; i++) if (p >= data[i].lo && p < data[i].hi) return 1;
    return 0;
}

static void *scan(void *arg) {
    int delay = getenv("PROBE_DELAY") ? atoi(getenv("PROBE_DELAY")) : 75;
    sleep(delay);
    FILE *out = fopen(DIR "probe2.log", "w");
    if (!out) return NULL;
    setvbuf(out, NULL, _IOLBF, 0);
    fprintf(out, "base=%#lx text=[%#lx,%#lx) delay=%d\n", base, text_lo, text_hi, delay);
    enum { CH = 1 << 20 };
    uint8_t *buf = malloc(CH);
    long hits = 0;
    for (int s = 0; s < ndata; s++) {
        fprintf(out, "# segment %s %#lx-%#lx\n", data[s].name, data[s].lo - base, data[s].hi - base);
        for (uintptr_t a = data[s].lo; a < data[s].hi; a += CH) {
            size_t n = data[s].hi - a < CH ? data[s].hi - a : CH;
            if (!rd(a, buf, n)) continue;
            for (size_t i = 0; i + 8 <= n; i += 8) {
                uintptr_t w = *(uintptr_t *)(buf + i);
                if (w < 0x100000000ULL || w >= 0x400000000000ULL || (w & 7) || (w >= base && w < img_hi)) continue;
                uintptr_t vt;
                if (!rd(w, &vt, 8) || !in_data(vt) || (vt & 7)) continue;
                uintptr_t e[6];
                if (!rd(vt, e, sizeof e)) continue;
                int k = 0;
                for (int j = 0; j < 6; j++) k += in_text(e[j]);
                if (k < 3) continue;
                char nm[80] = "-";
                uintptr_t ti, np;
                if (rd(vt - 8, &ti, 8) && ti >= base && ti < img_hi && rd(ti + 8, &np, 8) && np >= base && np < img_hi) {
                    memset(nm, 0, sizeof nm);
                    rd(np, nm, 64);
                    for (int c = 0; c < 64; c++) if (nm[c] && (nm[c] < 0x20 || nm[c] > 0x7e)) nm[c] = '?';
                }
                fprintf(out, "G %#lx obj=%#lx vt=%#lx ti=%s e:", a + i - base, w, vt - base, nm);
                for (int j = 0; j < 6; j++) fprintf(out, " %#lx", in_text(e[j]) ? e[j] - base : 0);
                fprintf(out, "\n");
                hits++;
            }
        }
    }
    fprintf(out, "done hits=%ld\n", hits);
    fclose(out);
    free(buf);
    return NULL;
}

__attribute__((constructor)) static void init(void) {
    uint32_t idx = 0;
    for (uint32_t i = 0; i < _dyld_image_count(); i++)
        if (strstr(_dyld_get_image_name(i), "MacOS/Cyberpunk2077")) { idx = i; break; }
    const struct mach_header_64 *mh = (const void *)_dyld_get_image_header(idx);
    intptr_t slide = _dyld_get_image_vmaddr_slide(idx);
    base = (uintptr_t)mh;
    const struct load_command *lc = (const void *)(mh + 1);
    for (uint32_t i = 0; i < mh->ncmds; i++, lc = (const void *)((const char *)lc + lc->cmdsize)) {
        if (lc->cmd != LC_SEGMENT_64) continue;
        const struct segment_command_64 *sg = (const void *)lc;
        uintptr_t lo = sg->vmaddr + slide, hi = lo + sg->vmsize;
        if (hi > img_hi) img_hi = hi;
        if (!strcmp(sg->segname, "__TEXT")) { text_lo = lo; text_hi = hi; }
        else if (strncmp(sg->segname, "__DATA", 6) == 0 && ndata < 16) {
            data[ndata].lo = lo; data[ndata].hi = hi;
            strncpy(data[ndata].name, sg->segname, 16);
            ndata++;
        }
    }
    pthread_t t;
    pthread_create(&t, NULL, scan, NULL);
    pthread_detach(t);
}
