
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边范围验证：调用 maps_around_search(location='118.892064,42.266341', radius='1000', keywords='公共厕所')，确认返回POI列表中包含目标POI id=B0JK7RR3RX。
2) 最大步行距离验证：调用 maps_walking_by_coordinates(origin='118.892064,42.266341', destination='118.892118,42.267929')，验证 total_distance_meters ≤ 900（实际为800m）。
3) 指定公交站点距离验证：调用 maps_text_search(keywords='海贝尔游乐场(公交站)', city='赤峰市', citylimit='true') 获取其poi id=BV11613237；再调用 maps_search_detail(id='BV11613237') 获取坐标=118.887553,42.267561；调用 maps_walking_by_coordinates(origin='118.892118,42.267929', destination='118.887553,42.267561')，验证 total_distance_meters ≤ 500（实际为402m）。
4) 途径点附近POI验证（沿途100m有便利店）：从步骤2的步行路线中遍历所有step的 to_coordinates 作为"途径点"，同时包括起点和终点（例如第一段to_coordinates='118.892305,42.264653'）；调用 maps_around_search(location='118.892305,42.264653', radius='100', keywords='便利店')，验证存在一个途径点返回的 pois 列表非空即可。
"""

import os
import sys

# 将 src 加入 sys.path，以便从 src/tools/amap_tools 导入
_current_file_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_file_dir)
_src_dir = os.path.join(_project_root, "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# 导入高德地图工具函数
from tools.amap_tools import (
    maps_search_detail,
    maps_text_search,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "118.892064,42.266341",
    search_radius: int = 1000,
    keywords: str = "公共厕所",
    max_walking_distance: int = 900,  # 900 meters
    bus_stop_name: str = "海贝尔游乐场(公交站)",
    city: str = "赤峰市",
    max_bus_stop_walking_distance: int = 500,  # 500 meters
    convenience_store_search_radius: int = 100,
    convenience_store_keywords: str = "便利店"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边范围验证：调用 maps_around_search，确认返回POI列表中包含目标POI。
    2) 最大步行距离验证：调用 maps_walking_by_coordinates，验证 total_distance_meters ≤ 900。
    3) 指定公交站点距离验证：调用 maps_text_search 获取公交站，调用 maps_search_detail 获取坐标，调用 maps_walking_by_coordinates，验证 total_distance_meters ≤ 500。
    4) 途径点附近POI验证（沿途100m有便利店）：从步骤2的步行路线中遍历所有step的 to_coordinates 作为"途径点"，调用 maps_around_search，验证存在一个途径点返回的 pois 列表非空。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"118.892064,42.266341"
        search_radius: 搜索半径（米），默认1000
        keywords: 搜索关键词，默认"公共厕所"
        max_walking_distance: 最大步行距离（米），默认900
        bus_stop_name: 公交站名称，默认"海贝尔游乐场(公交站)"
        city: 城市名称，默认"赤峰市"
        max_bus_stop_walking_distance: 到公交站最大步行距离（米），默认500
        convenience_store_search_radius: 便利店搜索半径（米），默认100
        convenience_store_keywords: 便利店搜索关键词，默认"便利店"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边范围验证
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到符合条件的POI")
        return False

    # 检查返回列表中是否包含目标POI ID
    poi_found = False
    for poi in around_search_result.pois:
        if poi.id == poi_id:
            poi_found = True
            print(f"✅ 在{search_radius}米范围内找到目标POI: {poi.name} (ID: {poi_id})")
            break

    if not poi_found:
        print(f"❌ 目标POI {poi_id} 不在{search_radius}米范围内的{keywords}列表中")
        return False

    # 步骤2: 获取目标POI坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 最大步行距离验证≤900米
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    walking_distance = walking_result.total_distance_meters
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（<= {max_walking_distance}米）")

    # 步骤4: 指定公交站点距离验证≤500米
    bus_stop_search_result = maps_text_search(
        keywords=bus_stop_name,
        city=city,
        citylimit="true"
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索{bus_stop_name}失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到{bus_stop_name}")
        return False

    # 获取公交站详情以获取坐标
    bus_stop_id = bus_stop_search_result.pois[0].id
    bus_stop_detail = maps_search_detail(id=bus_stop_id)
    if bus_stop_detail.error:
        print(f"❌ 获取{bus_stop_name}详情失败: {bus_stop_detail.error}")
        return False

    if not bus_stop_detail.location:
        print(f"❌ {bus_stop_name}没有location信息")
        return False

    bus_stop_location = bus_stop_detail.location
    print(f"✅ 获取{bus_stop_name}坐标: {bus_stop_location}")

    bus_stop_walking_result = maps_walking_by_coordinates(origin=poi_location, destination=bus_stop_location)
    if bus_stop_walking_result.error:
        print(f"❌ 计算到{bus_stop_name}步行路线失败: {bus_stop_walking_result.error}")
        return False

    if bus_stop_walking_result.total_distance_meters is None:
        print(f"❌ 无法获取到{bus_stop_name}步行距离")
        return False

    bus_stop_walking_distance = bus_stop_walking_result.total_distance_meters
    if bus_stop_walking_distance > max_bus_stop_walking_distance:
        print(f"❌ 到{bus_stop_name}步行距离{bus_stop_walking_distance}米，超过{max_bus_stop_walking_distance}米")
        return False
    print(f"✅ 到{bus_stop_name}步行距离{bus_stop_walking_distance}米，符合要求（<= {max_bus_stop_walking_distance}米）")

    # 步骤5: 途径点附近POI验证（沿途100m有便利店）
    if not walking_result.steps or len(walking_result.steps) == 0:
        print(f"❌ 步行路线没有步骤信息")
        return False

    print(f"✅ 步行路线共有{len(walking_result.steps)}个步骤")

    # 检查每个途径点周围是否有便利店
    convenience_store_found = False
    for i, step in enumerate(walking_result.steps):
        waypoint_location = step.to_coordinates
        convenience_store_search_result = maps_around_search(
            location=waypoint_location,
            radius=str(convenience_store_search_radius),
            keywords=convenience_store_keywords
        )

        if convenience_store_search_result.error:
            continue

        if convenience_store_search_result.pois and len(convenience_store_search_result.pois) > 0:
            convenience_store_found = True
            print(f"✅ 在途径点{i+1}（坐标: {waypoint_location}）周围{convenience_store_search_radius}米内找到{len(convenience_store_search_result.pois)}个便利店")
            print(f"   示例便利店: {convenience_store_search_result.pois[0].name} (ID: {convenience_store_search_result.pois[0].id})")
            break

    if not convenience_store_found:
        print(f"❌ 所有途径点周围{convenience_store_search_radius}米内都没有找到便利店")
        return False

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 809.py 文件...\n")
    result = verify_poi(poi_id="B0JK7RR3RX")
    print(f"\n验证结果: {result}")

