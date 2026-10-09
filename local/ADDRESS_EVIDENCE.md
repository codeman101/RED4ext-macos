# Address rows for the R30 trial (local edit of cyberpunk2077_addresses.json)

Local only, branch `local-trial`. For a later pull request to jackmaxwil/RED4ext-macos, after Frank decides (and after the license reminder).

Game: Cyberpunk 2077 2.3.1 Mac, the build his database names. Offsets are `segment:offset` as in his file (segment 1 = `__TEXT`, offset = VA - 0x100000000).

## Rows marked verified with our offset (21)

Each was unverified in his database, is compiled into at least one of our plugins, and our evidence checker (`tools/addr-match/check-rows.py`: Mac body against the Windows twin by strings, struct offsets, call shape; STRONG = shared strings or most offsets, OK = some evidence or a tiny body that is a function start, REVIEWED = a hand-written reason in `check-rows.reviewed.tsv`) rates it STRONG, OK or REVIEWED.

| hash | name | our offset | verdict | his entry before | plugins | Windows RVA |
|---|---|---|---|---|---|---|
| 68817558 | CEnum_ToString | 1:0x21A3BC0 | OK | 1:0x2214898 (unverified) | ArchiveXL,Codeware | 0x599BFC |
| 422530722 | UpdateRegistrar_RegisterBucketUpdate | 1:0x3D95924 | OK | 1:0x2000100 (unverified) | ArchiveXL,Codeware | 0x62575C |
| 489494088 | EntityBuilder_ExtractComponentsJob | 1:0xCA41E0 | OK | 1:0xD4DC20 (unverified) | ArchiveXL,Codeware | 0x1CD4A8 |
| 566894273 | CEnum_FromString | 1:0x21A3D4C | OK | 1:0x21B13AC (unverified) | ArchiveXL,Codeware | 0x75DF94 |
| 633871992 | MorphTargetManager_ApplyMorphTarget | 1:0xC6C0C4 | OK | 1:0x1C5226C (unverified) | ArchiveXL,Codeware | 0x1607FC |
| 898639042 | ScriptValidator_Validate | 1:0x21FBF90 | OK | 1:0x3D96BF4 (unverified) | Codeware | 0x3CCBA0 |
| 1087575974 | CEnum_Unserialize | 1:0x21A39B0 | OK | 1:0x2213FD4 (unverified) | ArchiveXL,Codeware | 0x1487A4 |
| 1411585028 | CBitfield_ToString | 1:0x2196930 | OK | 1:0x21E9C58 (unverified) | ArchiveXL,Codeware | 0x2076F18 |
| 1828854026 | IPlacedComponent_SetTransform | 1:0xC417F0 | OK | 1:0x1443324 (unverified) | ArchiveXL,Codeware | 0x574FC8 |
| 2182550867 | Entity_Assemble | 1:0xC97E28 | STRONG | 1:0xCCEDEC (unverified) | ArchiveXL,Codeware | 0x8AB708 |
| 2263681375 | Entity_Detach | 1:0xC996C0 | OK | 1:0x15EDE88 (unverified) | ArchiveXL,Codeware | 0x1B3A1C |
| 2296260874 | Entity_RequestComponents | 1:0xC95E24 | OK | 1:0xD4DC20 (unverified) | ArchiveXL,Codeware | 0x8B116C |
| 2349406410 | ResourceToken_Fetch | 1:0x21C4D4C | REVIEWED | 1:0x12F06B0 (unverified) | ArchiveXL,Codeware | 0x261F24 |
| 2515274237 | Entity_Dispose | 1:0xC999E0 | OK | 1:0xCF5E98 (unverified) | ArchiveXL,Codeware | 0x8B5540 |
| 2694518184 | CBitfield_FromString | 1:0x2196A2C | OK | 1:0x21FC47C (unverified) | ArchiveXL,Codeware | 0x2076E00 |
| 2794985748 | CBitfield_Unserialize | 1:0x21967A0 | REVIEWED | 1:0x21F7FC0 (unverified) | ArchiveXL,Codeware | 0x33B6C0 |
| 3121353053 | Handle_ctor | 1:0x2104788 | OK | 1:0x243C88 (unverified) | ArchiveXL,Codeware,TweakXL | 0x1456C0 |
| 3490519617 | Entity_Initialize | 1:0xC985EC | OK | 1:0x3641A50 (unverified) | ArchiveXL,Codeware | 0x8B0190 |
| 3596356635 | Entity_Uninitialize | 1:0xC992C4 | OK | 1:0xCC45EC (unverified) | ArchiveXL,Codeware | 0x402F74 |
| 4248638169 | Entity_Attach | 1:0xC99368 | OK | 1:0x180C9D8 (unverified) | ArchiveXL,Codeware | 0x1CDBB0 |
| 4254156293 | UpdateRegistrar_RegisterGroupUpdate | 1:0x3D95800 | OK | 1:0x1FFFF8C (unverified) | ArchiveXL,Codeware | 0x624D54 |

Evidence detail per row (checker output):

- `CEnum_ToString` 1:0x21A3BC0 OK: offsets:1/6~17%, calls w6 m7, size w137 m396
- `UpdateRegistrar_RegisterBucketUpdate` 1:0x3D95924 OK: offsets:3/8~38%, calls w7 m7, size w333 m304
- `EntityBuilder_ExtractComponentsJob` 1:0xCA41E0 OK: offsets:16/35~46%, calls w49 m159, size w1800 m4632
- `CEnum_FromString` 1:0x21A3D4C OK: offsets:1/6~17%, calls w2 m1, size w79 m528
- `MorphTargetManager_ApplyMorphTarget` 1:0xC6C0C4 OK: offsets:1/11~9%, calls w4 m11, size w201 m972
- `ScriptValidator_Validate` 1:0x21FBF90 OK: offsets:1/6~17%, calls w10 m19, size w302 m532
- `CEnum_Unserialize` 1:0x21A39B0 OK: offsets:1/7~14%, calls w5 m2, size w186 m528
- `CBitfield_ToString` 1:0x2196930 OK: offsets:1/2~50%, calls w6 m5, size w192 m252
- `IPlacedComponent_SetTransform` 1:0xC417F0 OK: offsets:4/13~31%, calls w2 m0, size w198 m204
- `Entity_Assemble` 1:0xC97E28 STRONG: offsets:5/9~56%, calls w6 m7, size w162 m176
- `Entity_Detach` 1:0xC996C0 OK: offsets:3/20~15%, calls w5 m11, size w192 m320
- `Entity_RequestComponents` 1:0xC95E24 OK: offsets:1/4~25%, calls w2 m2, size w85 m88
- `ResourceToken_Fetch` 1:0x21C4D4C REVIEWED: ResourceToken_Fetch: the IsFinished test and the add x0,x19,#0x28 return match Windows 0x261f24; Mac 312 bytes against 85 because the waiting path is inlined; the SDK calls it as a direct function [heuristic: WEAK offsets:0/7~0%, calls w3 m9, size w85 m312]
- `Entity_Dispose` 1:0xC999E0 OK: offsets:3/7~43%, calls w4 m7, size w96 m208
- `CBitfield_FromString` 1:0x2196A2C OK: offsets:1/6~17%, calls w9 m11, size w278 m508
- `CBitfield_Unserialize` 1:0x21967A0 REVIEWED: CBitfield_Unserialize: Windows 144 bytes, Mac 400 bytes (stream reads inlined); the reflect matcher found it in the CBitfield vtable (Mac 0x6FFBEC8, slot 0x68 = Windows 0x60 + 8) next to CBitfield_ToString and FromString, and it is the exact twin of the CEnum_Unserialize shape; not run live (no bitfield is deserialized in a boot) [heuristic: WEAK offsets:0/3~0%, calls w2 m4, size w144 m400]
- `Handle_ctor` 1:0x2104788 OK: offsets:1/4~25%, calls w1 m8, size w262 m312
- `Entity_Initialize` 1:0xC985EC OK: offsets:21/75~28%, calls w34 m111, size w994 m3028
- `Entity_Uninitialize` 1:0xC992C4 OK: offsets:2/10~20%, calls w7 m6, size w225 m160
- `Entity_Attach` 1:0xC99368 OK: offsets:7/20~35%, calls w8 m16, size w336 m508
- `UpdateRegistrar_RegisterGroupUpdate` 1:0x3D95800 OK: offsets:3/8~38%, calls w8 m7, size w332 m292

## Rows NOT changed: trap rows of our plugins (63)

These hashes are compiled into our plugins but have no Mac address in our port: the plugin resolves them to a named trap stub (`macos/MacTrapTable.inc`; status of each in `macos/NOT_YET.md`: unreached or not applicable on Mac). We have no evidence for an address, so they stay unverified in the database, and his plugin gate refuses a plugin that contains any of them. Decision needed (see the R30 note).

| hash | trap name | kind | his entry (unverified) | plugins |
|---|---|---|---|---|
| 15404457 | ResourceReference_Load | TRAP_FUNC | 1:0x12F04E4 | ArchiveXL,Codeware |
| 302583262 | IRenderProxy_sub_00 | TRAP_FUNC | 1:0x1000100 | ArchiveXL,Codeware |
| 364779332 | CBaseRTTIType_sub_88 | TRAP_FUNC | 1:0x22EEC0 | ArchiveXL,Codeware |
| 434901863 | Memory_Vault_Unk1 | TRAP_FUNC | 1:0x246E0 | ArchiveXL,Codeware,TweakXL |
| 458427884 | Memory_Vault | TRAP_DATA | 1:0x24400 | ArchiveXL,Codeware,TweakXL |
| 510274732 | IRenderProxy_sub_80 | TRAP_FUNC | 1:0x1000480 | ArchiveXL,Codeware |
| 586028847 | CRTTIScriptReferenceType_Set | TRAP_FUNC | 1:0x2200100 | ArchiveXL,Codeware |
| 587736171 | ResourceReference_Reset | TRAP_FUNC | 1:0x12F0604 | ArchiveXL,Codeware |
| 627643257 | CNamePool_RegisterName | TRAP_FUNC | 1:0x1E3ED04 | ArchiveXL |
| 677908004 | LaunchParameters | TRAP_DATA | 1:0x7600000 | ArchiveXL,Codeware |
| 678894266 | TPPRepresentationComponent_IsAffectedSlot | TRAP_FUNC | 1:0x23D9DF4 | ArchiveXL |
| 716262863 | CharacterCustomizationState_FinalizePart | TRAP_FUNC | 1:0x3D783B8 | ArchiveXL |
| 787099588 | CharacterCustomizationSystem_EnsureState | TRAP_FUNC | 1:0x2F2D360 | ArchiveXL |
| 837947027 | CClass_ClearScriptedData | TRAP_FUNC | 1:0x21EA8A4 | ArchiveXL,Codeware |
| 859968306 | Memory_Vault_Free | TRAP_FUNC | 1:0x2478C | ArchiveXL,Codeware,TweakXL |
| 956641309 | GarmentAssemblerState_ChangeCustomItem | TRAP_FUNC | 1:0x36FE44C | ArchiveXL |
| 1003499294 | AppearanceChanger_GetSuffixValue | TRAP_FUNC | 1:0x370E9AC | ArchiveXL |
| 1147149338 | ResourceSerializer_OnResourceReady | TRAP_FUNC | 1:0x20AB510 | ArchiveXL,Codeware |
| 1163138096 | CommandListContext_Close | TRAP_FUNC | 1:0xF040F8 | ArchiveXL,Codeware |
| 1168449474 | CharacterCustomizationSystem_InitializeOptionsFromState | TRAP_FUNC | 1:0x453C2D4 | ArchiveXL |
| 1239944840 | g_DeviceData | TRAP_DATA | 1:0x0 | ArchiveXL,Codeware |
| 1303056161 | ResourceLoader_OnUpdate | TRAP_FUNC | 1:0x2D9766C | ArchiveXL |
| 1350901460 | ResourceSerializer_PostLoad | TRAP_FUNC | 1:0x21AC670 | ArchiveXL,Codeware |
| 1365841885 | Memory_Vault_AllocAligned | TRAP_FUNC | 1:0x24668 | ArchiveXL,Codeware,TweakXL |
| 1452677801 | Memory_Vault_ReallocAligned | TRAP_FUNC | 1:0x246E0 | ArchiveXL,Codeware,TweakXL |
| 1459046115 | DeferredDataBuffer_LoadRefAsync | TRAP_FUNC | 1:0x2189040 | ArchiveXL,Codeware |
| 1468405902 | IRenderProxy_sub_B0 | TRAP_FUNC | 1:0x1000680 | ArchiveXL,Codeware |
| 1518151849 | CBaseFunction_Handlers | TRAP_DATA | 1:0x6E50000 | ArchiveXL,Codeware |
| 1693194103 | InkWorldLayer_UpdateComponents | TRAP_DATA | 1:0x3DA0574 | ArchiveXL |
| 1894391003 | IRenderProxy_sub_90 | TRAP_FUNC | 1:0x1000580 | ArchiveXL,Codeware |
| 1926836641 | GetFreeCommandList | TRAP_FUNC | 1:0x163F010 | ArchiveXL,Codeware |
| 1997150124 | Memory_Vault_Realloc | TRAP_FUNC | 1:0x2478C | ArchiveXL,Codeware,TweakXL |
| 2347184335 | CharacterCustomizationGenitalsController_CheckState | TRAP_FUNC | 1:0x2DEAC58 | ArchiveXL |
| 2396396482 | CBaseRTTIType_sub_A0 | TRAP_FUNC | 1:0x3228 | ArchiveXL,Codeware |
| 2418676960 | Memory_Vault_Alloc | TRAP_FUNC | 1:0x24584 | ArchiveXL,Codeware,TweakXL |
| 2462126272 | IRenderProxy_sub_58 | TRAP_FUNC | 1:0x1000300 | ArchiveXL,Codeware |
| 2508272872 | Allocator_CreateResource | TRAP_FUNC | 1:0x0 | ArchiveXL,Codeware |
| 2508398574 | ResourceToken_DestructUnk38 | TRAP_FUNC | 1:0x12F080C | ArchiveXL,Codeware |
| 2542474580 | IRenderProxy_sub_78 | TRAP_FUNC | 1:0x1000400 | ArchiveXL,Codeware |
| 2589919757 | ResourceToken_dtor | TRAP_FUNC | 1:0x12F066C | ArchiveXL,Codeware |
| 2756580845 | IRenderProxy_sub_18 | TRAP_FUNC | 1:0x1000200 | ArchiveXL,Codeware |
| 2757309857 | CBaseRTTIType_sub_90 | TRAP_FUNC | 1:0x22F04C | ArchiveXL,Codeware |
| 2786924000 | CommandListContext_FlushPendingBarriers | TRAP_FUNC | 1:0xF041BC | ArchiveXL,Codeware |
| 2814122829 | CommandListContext_AddPendingBarrier | TRAP_FUNC | 1:0xF040F8 | ArchiveXL,Codeware |
| 2878476560 | CNamePool_GetStringView | TRAP_FUNC | 1:0x1E3F8F4 | ArchiveXL |
| 2930319133 | CBaseRTTIType_sub_98 | TRAP_FUNC | 1:0x3228 | ArchiveXL,Codeware |
| 3063747982 | ResourceReference_Fetch | TRAP_FUNC | 1:0x12F055C | ArchiveXL,Codeware |
| 3410956665 | BasePackageReader_ReadHeader | TRAP_FUNC | 1:0x21005D4 | ArchiveXL,Codeware |
| 3414699684 | CharacterCustomizationHelper_GetHairColor | TRAP_FUNC | 1:0x1441630 | ArchiveXL |
| 3414823260 | CRTTIScriptReferenceType_ctor | TRAP_FUNC | 1:0x2200000 | ArchiveXL,Codeware |
| 3491501770 | IRenderProxy_sub_60 | TRAP_FLT | 1:0x1000380 | ArchiveXL,Codeware |
| 3505328647 | IRenderProxy_sub_08 | TRAP_FUNC | 1:0x1000180 | ArchiveXL,Codeware |
| 3516862860 | IRenderProxy_sub_98 | TRAP_FUNC | 1:0x1000600 | ArchiveXL,Codeware |
| 3578730042 | Memory_PoolStorage_OOM | TRAP_FUNC | 1:0x24298 | ArchiveXL,Codeware,TweakXL |
| 3628731410 | ObjectPackageReader_ctor | TRAP_FUNC | 1:0x2100250 | ArchiveXL,Codeware |
| 3724941976 | IRenderProxy_sub_88 | TRAP_FUNC | 1:0x1000500 | ArchiveXL,Codeware |
| 3740082313 | GarmentAssemblerState_ChangeItem | TRAP_FUNC | 1:0x36FE44C | ArchiveXL |
| 3832485534 | CBaseRTTIType_sub_80 | TRAP_FUNC | 1:0x22EEAC | ArchiveXL,Codeware |
| 3842971216 | AISpotPersistentDataArray_Reserve | TRAP_FUNC | 1:0x3040DEC | ArchiveXL |
| 4002093843 | ImpostorComponent_OnAttach | TRAP_FUNC | 1:0x37DCB7C | ArchiveXL |
| 4096926792 | IRenderProxy_sub_A8 | TRAP_FUNC | 1:0x1000680 | ArchiveXL,Codeware |
| 4219677283 | AppearanceChanger_GetBaseMeshOffset | TRAP_FUNC | 1:0xAD043C | ArchiveXL |
| 4228123904 | CommandListContext_dtor | TRAP_FUNC | 1:0xF03F70 | ArchiveXL,Codeware |
