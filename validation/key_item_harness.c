#include <stdio.h>
#include <string.h>
#include "key_items.h"

extern int32_t key_item_slots[KFIV_VALIDATION_ITEM_SLOTS];
void Menu_ClearKeyItems(void);
void Menu_AddKeyItem(int32_t key);

static uint32_t random_state = 0x1234567u;
static long cases;
static long mismatches;

static int32_t next_value(void) {
    random_state = random_state * 1103515245u + 12345u;
    return (int32_t)(random_state >> 8) % 20 - 4;
}

static void compare_slots(const int32_t *model_slots) {
    ++cases;
    if (memcmp(model_slots, key_item_slots, sizeof key_item_slots) != 0)
        ++mismatches;
}

static void load_slots(int32_t *model_slots, const int32_t *saved_slots) {
    memcpy(model_slots, saved_slots, sizeof key_item_slots);
    memcpy(key_item_slots, saved_slots, sizeof key_item_slots);
}

static void differential(void) {
    int32_t model_slots[KFIV_VALIDATION_ITEM_SLOTS];
    static const int32_t extremes[] = {INT32_MIN, -48, -1, 0, 46, 60, 61, INT32_MAX};
    for (int trial = 0; trial < 4000; ++trial) {
        for (int i = 0; i < KFIV_VALIDATION_ITEM_SLOTS; ++i)
            model_slots[i] = next_value();
        if (trial % 4 == 0) {
            int occupied = trial / 4 % 13;
            for (int i = 0; i < KFIV_VALIDATION_ITEM_SLOTS; ++i)
                model_slots[i] = i < occupied ? i % 12 : -1;
        }
        int32_t saved_slots[KFIV_VALIDATION_ITEM_SLOTS];
        memcpy(saved_slots, model_slots, sizeof saved_slots);
        for (int32_t id = 40; id <= 66; ++id) {
            load_slots(model_slots, saved_slots);
            kfiv_model_add_item(id, model_slots);
            Menu_AddKeyItem(id);
            compare_slots(model_slots);
        }
        for (unsigned index = 0; index < sizeof extremes / sizeof *extremes; ++index) {
            load_slots(model_slots, saved_slots);
            kfiv_model_add_item(extremes[index], model_slots);
            Menu_AddKeyItem(extremes[index]);
            compare_slots(model_slots);
        }
        load_slots(model_slots, saved_slots);
        kfiv_model_clear_items(model_slots);
        Menu_ClearKeyItems();
        compare_slots(model_slots);
    }
}

/* Preserve state between operations, unlike the independent cases above. */
static void sequences(void) {
    int32_t model_slots[KFIV_VALIDATION_ITEM_SLOTS];
    for (int trial = 0; trial < 4000; ++trial) {
        for (int i = 0; i < KFIV_VALIDATION_ITEM_SLOTS; ++i)
            model_slots[i] = key_item_slots[i] = i == 0 ? INT32_MIN : next_value();
        for (int step = 0; step < 32; ++step) {
            if (step == 16) {
                kfiv_model_clear_items(model_slots);
                Menu_ClearKeyItems();
            } else {
                int32_t id = 40 + (trial + step) % 27;
                kfiv_model_add_item(id, model_slots);
                Menu_AddKeyItem(id);
            }
            compare_slots(model_slots);
        }
    }
}

int main(void) {
    differential();
    printf("differential cases=%ld mismatches=%ld\n", cases, mismatches);
    long baseline_cases = cases, baseline_mismatches = mismatches;
    sequences();
    printf("sequence cases=%ld mismatches=%ld\n",
           cases - baseline_cases, mismatches - baseline_mismatches);
    return mismatches != 0;
}
