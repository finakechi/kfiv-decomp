#ifndef KFIV_VALIDATION_KEY_ITEM_SAVE_H
#define KFIV_VALIDATION_KEY_ITEM_SAVE_H

#include <stdint.h>

#define KFIV_SAVE_SLOT_COUNT 12
#define KFIV_SAVE_SLOT_BYTES (KFIV_SAVE_SLOT_COUNT * 4)

/* Independent C16 byte-effects model, not the game's save implementation. */
int kfiv_model_pack_key_items(const int32_t slots[KFIV_SAVE_SLOT_COUNT],
                              uint8_t bytes[KFIV_SAVE_SLOT_BYTES]);
int kfiv_model_unpack_key_items(const uint8_t bytes[KFIV_SAVE_SLOT_BYTES],
                                int32_t slots[KFIV_SAVE_SLOT_COUNT]);

#endif
