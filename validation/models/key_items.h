#ifndef KFIV_VALIDATION_KEY_ITEMS_H
#define KFIV_VALIDATION_KEY_ITEMS_H

#include <stdint.h>

#define KFIV_VALIDATION_ITEM_SLOTS 12

/* Host reference models, not replacements for the matching game functions. */
int kfiv_model_clear_items(int32_t slots[KFIV_VALIDATION_ITEM_SLOTS]);
int kfiv_model_add_item(int32_t id, int32_t slots[KFIV_VALIDATION_ITEM_SLOTS]);

#endif
