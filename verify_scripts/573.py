"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 半径约束验证：调用 maps_around_search(location="119.671296,29.052934", radius="2000", keywords="百货商店")，验证返回pois中包含目标poi_id=B0JD47SYDY（且该around_search返回的pois数量>=8）。
2) 金华站可达性（打车/驾车时间）：调用 maps_text_search(keywords="金华站", city="金华") 拿到 poi_id，再 maps_search_detail(poi_id) 得到 location_station；再调用 maps_driving_by_coordinates(origin="119.667521,29.056070", destination=location_station) 获取驾车时长 t_drive，验证 t_drive<=15分钟(900秒)。
3) 第十五中学可达性（步行时间）：调用 maps_text_search(keywords="金华市第十五中学", city="金华") 拿到 poi_id，再 maps_search_detail(poi_id) 得到 location_school；再调用 maps_walking_by_coordinates(origin="119.667521,29.056070", destination=location_school) 获取步行时长 t_walk，验证 t_walk<=25分钟(1500秒)。
4) 充电桩邻近验证：调用 maps_around_search(location="119.667521,29.056070", radius="600", keywords="充电桩站点")，验证返回pois数量>=1（表示目标店600米内存在充电桩站点）。
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
    maps_search_detail,
    maps_driving_by_coordinates,
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    search_location: str = "119.671296,29.052934",
    search_radius: int = 2000,  # 2km
    keywords: str = "百货商店",
    min_poi_count: int = 8,
    poi_location: str = "119.667521,29.056070",
    station_address: str = "金华站",
    station_city: str = "金华",
    max_driving_duration: int = 900,  # 15 minutes = 900 seconds
    school_address: str = "金华市第十五中学",
    school_city: str = "金华",
    max_walking_duration: int = 1500,  # 25 minutes = 1500 seconds
    charging_station_search_radius: int = 600,  # 600 meters
    charging_station_keywords: str = "充电桩站点",
    min_charging_station_count: int = 1
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 半径约束验证：调用 maps_around_search，验证返回pois中包含目标poi_id且数量>=8
    2) 金华站可达性：调用 maps_text_search 获取金华站 poi_id，再 maps_search_detail 获取坐标，调用 maps_driving_by_coordinates 验证驾车时长<=900秒
    3) 第十五中学可达性：调用 maps_text_search 获取学校 poi_id，再 maps_search_detail 获取坐标，调用 maps_walking_by_coordinates 验证步行时长<=1500秒
    4) 充电桩邻近验证：调用 maps_around_search，验证返回pois数量>=1

    Args:
        poi_id: POI ID
        search_location: 搜索中心坐标，格式为"经度,纬度"，默认"119.671296,29.052934"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"百货商店"
        min_poi_count: 最少POI数量，默认8
        poi_location: POI坐标，格式为"经度,纬度"，默认"119.667521,29.056070"
        station_address: 火车站地址，默认"金华站"
        station_city: 火车站所在城市，默认"金华"
        max_driving_duration: 最大驾车时长（秒），默认900（15分钟）
        school_address: 学校地址，默认"金华市第十五中学"
        school_city: 学校所在城市，默认"金华"
        max_walking_duration: 最大步行时长（秒），默认1500（25分钟）
        charging_station_search_radius: 充电桩搜索半径（米），默认600
        charging_station_keywords: 充电桩搜索关键词，默认"充电桩站点"
        min_charging_station_count: 最少充电桩数量，默认1

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 半径约束验证（2公里内的百货商店）
    around_search_result = maps_around_search(
        location=search_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False

    if not around_search_result.pois or len(around_search_result.pois) == 0:
        print(f"❌ 未找到符合条件的POI")
        return False

    # 检查返回POI数量是否>=8
    poi_count = len(around_search_result.pois)
    if poi_count < min_poi_count:
        print(f"❌ 返回POI数量{poi_count}个，少于{min_poi_count}个")
        return False
    print(f"✅ 返回POI数量{poi_count}个，符合要求（>= {min_poi_count}个）")

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

    # 步骤2: 金华站可达性验证
    station_text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if station_text_search_result.error:
        print(f"❌ 获取{station_address}坐标失败: {station_text_search_result.error}")
        return False

    if not station_text_search_result.pois or len(station_text_search_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    station_poi_id = station_text_search_result.pois[0].id
    station_detail_result = maps_search_detail(id=station_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取{station_address}详情失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print(f"❌ {station_address}无坐标信息")
        return False
    station_location = station_detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    # 驾车时间验证（<= 15分钟）
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_address}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤3: 第十五中学可达性验证
    school_text_search_result = maps_text_search(keywords=school_address, city=school_city)
    if school_text_search_result.error:
        print(f"❌ 获取{school_address}坐标失败: {school_text_search_result.error}")
        return False

    if not school_text_search_result.pois or len(school_text_search_result.pois) == 0:
        print(f"❌ 未找到{school_address}坐标")
        return False

    school_poi_id = school_text_search_result.pois[0].id
    school_detail_result = maps_search_detail(id=school_poi_id)
    if school_detail_result.error:
        print(f"❌ 获取{school_address}详情失败: {school_detail_result.error}")
        return False
    if not school_detail_result.location:
        print(f"❌ {school_address}无坐标信息")
        return False
    school_location = school_detail_result.location
    print(f"✅ 获取{school_address}坐标: {school_location}")

    # 步行时间验证（<= 25分钟）
    walking_result = maps_walking_by_coordinates(origin=poi_location, destination=school_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 到{school_address}步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 到{school_address}步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤4: 充电桩邻近验证
    charging_station_search_result = maps_around_search(
        location=poi_location,
        radius=str(charging_station_search_radius),
        keywords=charging_station_keywords
    )
    if charging_station_search_result.error:
        print(f"❌ 搜索周边充电桩失败: {charging_station_search_result.error}")
        return False

    charging_station_count = 0
    if charging_station_search_result.pois:
        charging_station_count = len(charging_station_search_result.pois)

    if charging_station_count < min_charging_station_count:
        print(f"❌ {charging_station_search_radius}米范围内充电桩数量{charging_station_count}个，少于{min_charging_station_count}个")
        return False
    print(f"✅ {charging_station_search_radius}米范围内找到{charging_station_count}个充电桩站点")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 573.py 文件...\n")
    result = verify_poi(poi_id="B0JD47SYDY")
    print(f"\n验证结果: {result}")
