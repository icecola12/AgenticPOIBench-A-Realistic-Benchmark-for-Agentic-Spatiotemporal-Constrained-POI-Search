
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边候选集验证（数量与范围）
- 使用 maps_around_search，参数：location=114.443123,23.126334，radius=2000，keywords=购物中心。
- 断言返回的 pois 数量 > 8。
- 断言目标 poi_id(B0FFIQCX0J) 出现在该 pois 列表中。

2) 骑行时间验证（用户位置 -> 目标购物中心）
- 调用 maps_bicycling_by_coordinates，origin=114.443123,23.126334，destination=目标POI的location(114.433086,23.129102)。
- 断言 total_duration_seconds <= 12*60。

3) 打车/驾车时间验证（目标购物中心 -> 惠州火车站）
- 调用 maps_text_search(keywords=惠州火车站, city=惠州) 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取车站坐标。
- 调用 maps_driving_by_coordinates，origin=目标POI的location(114.433086,23.129102)，destination=车站坐标。
- 断言 total_duration_seconds <= 8*60。
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
    maps_bicycling_by_coordinates,
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "114.443123,23.126334",
    search_radius: int = 2000,  # 2km
    keywords: str = "购物中心",
    min_poi_count: int = 8,
    max_bicycling_duration: int = 720,  # 12 minutes = 720 seconds
    station_address: str = "惠州火车站",
    station_city: str = "惠州",
    max_driving_duration: int = 480  # 8 minutes = 480 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边候选集验证：调用 maps_around_search，确认返回POI数量>8，且目标poi_id在返回列表中
    2) 目标POI类型与坐标验证：调用 maps_search_detail 获取其location
    3) 骑行时间验证：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 12*60 秒
    4) 打车/驾车时间验证：调用 maps_text_search 获取 poi_id，再用 maps_search_detail 获取火车站坐标，调用 maps_driving_by_coordinates 验证 total_duration_seconds <= 8*60 秒

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"114.443123,23.126334"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"购物中心"
        min_poi_count: 最少POI数量，默认8
        max_bicycling_duration: 最大骑行时长（秒），默认720（12分钟）
        station_address: 火车站地址，默认"惠州火车站"
        station_city: 火车站所在城市，默认"惠州"
        max_driving_duration: 最大驾车时长（秒），默认480（8分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边候选集验证（附近2公里内的购物中心）
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

    # 步骤2: 获取目标POI详情
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 骑行时间验证（<= 12分钟）
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False

    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_duration:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_duration}秒（{max_bicycling_duration // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")

    # 步骤4: 用 maps_text_search + maps_search_detail 获取火车站坐标并验证驾车时间
    text_search_result = maps_text_search(keywords=station_address, city=station_city)
    if text_search_result.error:
        print(f"❌ 获取{station_address}坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到{station_address}坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error or not detail_result.location:
        print(f"❌ 获取{station_address}坐标失败: {detail_result.error or '无location'}")
        return False

    station_location = detail_result.location
    print(f"✅ 获取{station_address}坐标: {station_location}")

    # 步骤4: 驾车时间验证（<= 8分钟）
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

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 502.py 文件...\n")
    result = verify_poi(poi_id="B0FFIQCX0J")
    print(f"\n验证结果: {result}")
