
INV_CATEGORIES = {
    0: [0, 'Warehouse', 'map_icon_warehouse'],
    1: [1, 'Small Munitions', 'map_icon_factory_small_munitions'],
    2: [2, 'Large Munitions', 'map_icon_factory_large_munitions'],
    3: [3, 'Turrets', 'map_icon_factory_turrets'],
    4: [4, 'Utility', 'map_icon_factory_utility'],
    5: [5, 'Surface Chassis', 'map_icon_factory_chassis_land'],
    6: [6, 'Air Chassis', 'map_icon_factory_chassis_air'],
    7: [7, 'Fuel', 'map_icon_factory_fuel'],
    8: [8, 'Barge', 'map_icon_factory_barge'],
}


def update_get_resource_inventory_category_count():
    print("update_get_resource_inventory_category_count")
    return len(INV_CATEGORIES)

def update_get_resource_inventory_category_data(idx):
    if idx in INV_CATEGORIES:
        cat_idx, name, icon = INV_CATEGORIES[idx]
        print(f"update_get_resource_inventory_category_data({idx}) -> ", cat_idx, name, icon)
        return cat_idx, name, icon
    print(f"update_get_resource_inventory_category_data({idx}) is nil")
    return None