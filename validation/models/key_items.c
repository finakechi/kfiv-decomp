/*
 * Adapted from finakechi/KF4AncientCity at 04d294f52fd0df96e13027e74933094d11dce1a2:
 * src/common_item_effects/kf_common_item_effects.c: kf_effect_1dc120 (C15)
 * src/common_item_effects/kf_common_item_list.c: kf_list_reset (C16)
 * Only these two independent model bodies are retained, with renamed symbols
 * and slot-count macro. Provenance and host-only guards: ../README.md.
 */
#include <stddef.h>
#include "key_items.h"

int kfiv_model_clear_items(int32_t slots[KFIV_VALIDATION_ITEM_SLOTS]) {
    if (slots == NULL) return -1;
    for (unsigned i = KFIV_VALIDATION_ITEM_SLOTS; i != 0; --i) slots[i - 1] = -1;
    return 0;
}

int kfiv_model_add_item(int32_t id, int32_t slots[KFIV_VALIDATION_ITEM_SLOTS]) {
    static const int32_t dispatch[13] = {2, 1, 0, 4, 9, 3, 11, -1, 8, 7, 6, 5, 10};
    if (slots == NULL) return -1;
    unsigned slot = 0;
    while (slot < KFIV_VALIDATION_ITEM_SLOTS && slots[slot] >= 0) slot++;
    uint32_t index = (uint32_t)id - 47u;
    if (slot < KFIV_VALIDATION_ITEM_SLOTS && index < 13u && dispatch[index] >= 0)
        slots[slot] = dispatch[index];
    return 0;
}
