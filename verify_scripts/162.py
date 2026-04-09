
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边性验证：调用 maps_around_search(location='118.313358,33.970465', radius='1200', keywords='广场')，验证返回pois中包含目标poi_id=B0KRJ98N9C。
2) 到宿迁站驾车时间：调用 maps_text_search(keywords='宿迁站', city='宿迁') 取 poi_id，再 maps_search_detail(id=poi_id) 得到 宿迁站坐标；再调用 maps_driving_by_coordinates(origin=POI坐标, destination=宿迁站坐标)，验证 total_duration_seconds/60 ≤ 20。
3) 绕行增量验证（A->广场->宿迁站 vs A->宿迁站）：
- 设起点A为用户当前坐标(118.313358,33.970465)。
- 调用 maps_driving_by_coordinates(origin=A, destination=宿迁站) 得到 t_direct。
- 调用 maps_driving_by_coordinates(origin=A, destination=POI) 得到 t_A_to_poi；调用 maps_driving_by_coordinates(origin=POI, destination=宿迁站) 得到 poi_id，再 maps_search_detail(id=poi_id) 得到 t_poi_to_station。
- 验证 (t_A_to_poi + t_poi_to_station - t_direct)/60 ≤ 5。
4) 公交站"集合+最小步行时间"验证：
- 调用 maps_around_search(location=POI坐标, radius='1000', keywords='公交站') 获取 poi_id，再 maps_search_detail(id=poi_id) 获取 公交站集合S，验证S非空。
- 对S中每个公交站，调用 maps_walking_by_coordinates(origin=POI坐标, destination=该站坐标) 得到步行时长；取最小值 t_min_walk，验证 t_min_walk/60 ≤ 15。
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
    maps_text_search,
    maps_search_detail ,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "118.313358,33.970465",
    search_radius: int = 1200,
    keywords: str = "广场",
    station_address: str = "宿迁站",
    station_city: str = "宿迁",
    max_station_driving_duration: int = 1200,  # 20 minutes = 1200 seconds
    max_detour_increment: int = 300,  # 5 minutes = 300 seconds
    bus_stop_search_radius: int = 1000,
    bus_stop_keywords: str = "公交站",
    max_bus_stop_walking_duration: int = 900  # 15 minutes = 900 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边性验证：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 到宿迁站驾车时间：调用得到宿迁站坐标，再调用 maps_driving_by_coordinates，验证 total_duration_seconds/60 ≤ 20。
    3) 绕行增量验证：计算 A->POI->站 与 A->站 的时间差，验证差值/60 ≤ 5。
    4) 公交站验证：调用 maps_around_search 获取公交站集合，对每个公交站调用 maps_walking_by_coordinates，取最小值，验证/60 ≤ 15。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"118.313358,33.970465"
        search_radius: 搜索半径（米），默认1200
        keywords: 搜索关键词，默认"广场"
        station_address: 车站地址，默认"宿迁站"
        station_city: 车站所在城市，默认"宿迁"
        max_station_driving_duration: 到车站最大驾车时长（秒），默认1200（20分钟）
        max_detour_increment: 最大绕行增量（秒），默认300（5分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认1000
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        max_bus_stop_walking_duration: 到公交站最大步行时长（秒），默认900（15分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边性验证
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

    # 步骤3: 获取宿迁站坐标
    station_text_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_result.error:
        print(f"❌ 获取{station_address}坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    first_poi_id = station_text_result.pois[0].id

    detail_result = maps_search_detail(id=first_poi_id)

    if detail_result.error:

        print(f"❌ 获取坐标失败: {detail_result.error}")

        return False

    if not detail_result.location:

        print("❌ 未获取到坐标")

        return False

    station_location = detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    # 步骤4: 到宿迁站驾车时间≤20分钟
    poi_to_station_driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if poi_to_station_driving_result.error:
        print(f"❌ 计算POI到{station_address}驾车路线失败: {poi_to_station_driving_result.error}")
        return False

    if poi_to_station_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取POI到{station_address}驾车时长")
        return False

    poi_to_station_duration = poi_to_station_driving_result.total_duration_seconds
    poi_to_station_duration_minutes = poi_to_station_duration / 60
    if poi_to_station_duration_minutes > max_station_driving_duration / 60:
        print(f"❌ POI到{station_address}驾车时长{poi_to_station_duration_minutes:.2f}分钟，超过{max_station_driving_duration / 60:.0f}分钟")
        return False
    print(f"✅ POI到{station_address}驾车时长{poi_to_station_duration_minutes:.2f}分钟，符合要求（<= {max_station_driving_duration / 60:.0f}分钟）")

    # 步骤5: 绕行增量验证（A->广场->宿迁站 vs A->宿迁站）
    # 计算直达时间：A -> 宿迁站
    direct_driving_result = maps_driving_by_coordinates(origin=user_location, destination=station_location)
    if direct_driving_result.error:
        print(f"❌ 计算用户到{station_address}直达驾车路线失败: {direct_driving_result.error}")
        return False

    if direct_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取用户到{station_address}直达驾车时长")
        return False

    t_direct = direct_driving_result.total_duration_seconds
    print(f"✅ 用户到{station_address}直达驾车时长: {t_direct}秒（{t_direct / 60:.2f}分钟）")

    # 计算绕行时间：A -> POI
    user_to_poi_driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if user_to_poi_driving_result.error:
        print(f"❌ 计算用户到POI驾车路线失败: {user_to_poi_driving_result.error}")
        return False

    if user_to_poi_driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取用户到POI驾车时长")
        return False

    t_A_to_poi = user_to_poi_driving_result.total_duration_seconds
    t_poi_to_station = poi_to_station_duration

    # 计算绕行增量
    detour_increment = (t_A_to_poi + t_poi_to_station - t_direct)
    detour_increment_minutes = detour_increment / 60

    if detour_increment_minutes > max_detour_increment / 60:
        print(f"❌ 绕行增量{detour_increment_minutes:.2f}分钟，超过{max_detour_increment / 60:.0f}分钟")
        print(f"   详情: A->POI={t_A_to_poi}秒, POI->站={t_poi_to_station}秒, A->站={t_direct}秒")
        return False
    print(f"✅ 绕行增量{detour_increment_minutes:.2f}分钟，符合要求（<= {max_detour_increment / 60:.0f}分钟）")

    # 步骤6: 公交站"集合+最小步行时间"验证
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 未找到公交站")
        return False

    print(f"✅ 找到{len(bus_stop_search_result.pois)}个公交站")

    # 计算到每个公交站的步行时间，找到最小值
    min_bus_stop_walking_duration = None
    for bus_stop in bus_stop_search_result.pois:
        if not bus_stop.location:
            continue

        bus_stop_walking_result = maps_walking_by_coordinates(
            origin=poi_location,
            destination=bus_stop.location
        )
        if bus_stop_walking_result.error or bus_stop_walking_result.total_duration_seconds is None:
            continue

        duration = bus_stop_walking_result.total_duration_seconds
        if min_bus_stop_walking_duration is None or duration < min_bus_stop_walking_duration:
            min_bus_stop_walking_duration = duration

    if min_bus_stop_walking_duration is None:
        print(f"❌ 无法计算到公交站的步行时间")
        return False

    min_bus_stop_walking_duration_minutes = min_bus_stop_walking_duration / 60
    if min_bus_stop_walking_duration_minutes > max_bus_stop_walking_duration / 60:
        print(f"❌ 到最近公交站步行时长{min_bus_stop_walking_duration_minutes:.2f}分钟，超过{max_bus_stop_walking_duration / 60:.0f}分钟")
        return False
    print(f"✅ 到最近公交站步行时长{min_bus_stop_walking_duration_minutes:.2f}分钟，符合要求（<= {max_bus_stop_walking_duration / 60:.0f}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 821.py 文件...\n")
    result = verify_poi(poi_id="B0KRJ98N9C")
    print(f"\n验证结果: {result}")


