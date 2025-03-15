
CATEGORIES = [
    [1, "bay_marker"],
    [2, "icon_chassis_16_wheel_small"],
]


def update_get_resource_inventory_category_count():
    return len(CATEGORIES)

def update_get_resource_inventory_category_data(idx):
    try:
        cat_idx, name, icon = CATEGORIES[idx]
        return cat_idx, name, icon
    except:
        return 2, "seal", "icon_chassis_16_wheel_small"
