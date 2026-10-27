#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "key_item_save.h"

extern int32_t key_item_slots[KFIV_SAVE_SLOT_COUNT];
size_t kfiv_game_pack_slice(uint8_t *base);
size_t kfiv_game_unpack_slice(uint8_t *base);

enum { CASES = 4096, BUFFER_BYTES = 64 };
static uint32_t state = UINT32_C(0x19660707);

static uint32_t next_word(void) {
    state = state * UINT32_C(1664525) + UINT32_C(1013904223);
    return state;
}

static int32_t word_as_signed(uint32_t word) {
    int32_t result;
    memcpy(&result, &word, sizeof result);
    return result;
}

static void prepare_slots(int case_index, int32_t slots[KFIV_SAVE_SLOT_COUNT]) {
    static const int32_t boundaries[] = {
        INT32_MIN, INT32_MAX, -1, 0, 1, 2, 11, 12, -12, -47, 47, 59
    };
    for (unsigned i = 0; i < KFIV_SAVE_SLOT_COUNT; ++i) {
        if (case_index == 0) slots[i] = -1;
        else if (case_index == 1) slots[i] = boundaries[i];
        else if (case_index == 2) slots[i] = (int32_t)i;
        else slots[i] = word_as_signed(next_word());
    }
}

static int tail_intact(const uint8_t buffer[BUFFER_BYTES]) {
    for (unsigned i = KFIV_SAVE_SLOT_BYTES; i < BUFFER_BYTES; ++i) {
        if (buffer[i] != UINT8_C(0xA5)) return 0;
    }
    return 1;
}

int main(void) {
    int save_errors = 0;
    int restore_errors = 0;
    const uint16_t endian_test = 1;
    if (*(const uint8_t *)&endian_test != 1) {
        fputs("little-endian host required for retail memcpy comparison\n", stderr);
        return 2;
    }

    for (int trial = 0; trial < CASES; ++trial) {
        int32_t original[KFIV_SAVE_SLOT_COUNT];
        int32_t expected[KFIV_SAVE_SLOT_COUNT];
        uint8_t model[KFIV_SAVE_SLOT_BYTES];
        uint8_t buffer[BUFFER_BYTES];

        prepare_slots(trial, original);
        memcpy(key_item_slots, original, sizeof original);
        memset(buffer, 0xA5, sizeof buffer);
        if (kfiv_model_pack_key_items(original, model) != 0) return 2;
        size_t packed = kfiv_game_pack_slice(buffer);
        if (packed != KFIV_SAVE_SLOT_BYTES ||
            memcmp(model, buffer, KFIV_SAVE_SLOT_BYTES) != 0 ||
            !tail_intact(buffer) ||
            memcmp(original, key_item_slots, sizeof original) != 0) {
            ++save_errors;
        }

        memcpy(buffer, model, sizeof model);
        memset(buffer + KFIV_SAVE_SLOT_BYTES, 0xA5,
               BUFFER_BYTES - KFIV_SAVE_SLOT_BYTES);
        memset(key_item_slots, 0xCE, sizeof original);
        if (kfiv_model_unpack_key_items(model, expected) != 0) return 2;
        size_t unpacked = kfiv_game_unpack_slice(buffer);
        if (unpacked != KFIV_SAVE_SLOT_BYTES ||
            memcmp(expected, key_item_slots, sizeof expected) != 0 ||
            memcmp(model, buffer, sizeof model) != 0 ||
            !tail_intact(buffer)) {
            ++restore_errors;
        }
    }
    printf("save cases=%d mismatches=%d\n", CASES, save_errors);
    printf("restore cases=%d mismatches=%d\n", CASES, restore_errors);
    return (save_errors || restore_errors) ? 1 : 0;
}
