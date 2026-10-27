/*
 * Adapted from finakechi/KF4AncientCity at
 * 04d294f52fd0df96e13027e74933094d11dce1a2,
 * src/common_item_effects/kf_common_item_list.c:
 * kf_list_pack and kf_list_unpack (C16).
 * The source was checked against the ELF's bounded copy windows.
 * Only final non-overlapping 48-byte effects are modeled here.
 */
#include <stddef.h>
#include <stdint.h>
#include "key_item_save.h"

static int32_t signed_word(uint32_t value) {
    return value <= INT32_MAX ? (int32_t)value :
           (int32_t)((int64_t)value - INT64_C(0x100000000));
}

int kfiv_model_pack_key_items(const int32_t slots[KFIV_SAVE_SLOT_COUNT],
                              uint8_t bytes[KFIV_SAVE_SLOT_BYTES]) {
    if (slots == NULL || bytes == NULL) return -1;
    for (unsigned i = 0; i < KFIV_SAVE_SLOT_COUNT; ++i) {
        uint32_t value = (uint32_t)slots[i];
        for (unsigned j = 0; j < 4; ++j) {
            bytes[4 * i + j] = (uint8_t)(value >> (8 * j));
        }
    }
    return 0;
}

int kfiv_model_unpack_key_items(const uint8_t bytes[KFIV_SAVE_SLOT_BYTES],
                                int32_t slots[KFIV_SAVE_SLOT_COUNT]) {
    if (slots == NULL || bytes == NULL) return -1;
    for (unsigned i = 0; i < KFIV_SAVE_SLOT_COUNT; ++i) {
        uint32_t value = 0;
        for (unsigned j = 0; j < 4; ++j) {
            value |= (uint32_t)bytes[4 * i + j] << (8 * j);
        }
        slots[i] = signed_word(value);
    }
    return 0;
}
