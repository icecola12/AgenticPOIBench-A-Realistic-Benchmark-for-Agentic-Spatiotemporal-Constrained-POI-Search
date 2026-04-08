
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边性验证：调用 maps_around_search(location='117.19579,34.220826', radius='2000', keywords='酒店')，验证返回pois中包含 target_poi_id='B0LGJDJZHI'。
2) 评分验证：调用 maps_search_detail(id='B0LGJDJZHI')，读取 biz_ext.rating，验证 rating >= 4.7。
3) 获取目标地铁站：调用 maps_text_search(keywords='矿大文昌校区地铁站', city='徐州', citylimit='true')，取地铁站poi的id（应为 BV10779232），再调用 maps_search_detail(id='BV10779232') 获取其 location。
4) 步行时间验证：调用 maps_walking_by_coordinates(origin=酒店location, destination=地铁站location)，验证 total_duration_seconds <= 900（15分钟）。
5) 直线距离验证：调用 maps_distance(origins=酒店location, destination=地铁站location)，验证 distance_meters <= 350。
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
    maps_walking_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "117.19579,34.220826",
    search_radius: int = 2000,
    keywords: str = "酒店",
    min_rating: float = 4.7,
    metro_station_keywords: str = "矿大文昌校区地铁站",
    metro_station_city: str = "徐州",
    max_walking_seconds: int = 900,  # 15 minutes = 900 seconds
    max_distance_meters: int = 350
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边性验证：调用 maps_around_search，验证返回pois中包含 target_poi_id。
    2) 评分验证：调用 maps_search_detail，读取 biz_ext.rating，验证 rating >= 4.7。
    3) 获取目标地铁站：调用 maps_text_search，取地铁站poi的id，再调用 maps_search_detail 获取其 location。
    4) 步行时间验证：调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 900（15分钟）。
    5) 直线距离验证：调用 maps_distance，验证 distance_meters <= 350。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.19579,34.220826"
        search_radius: 搜索半径（米），默认2000
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最低评分，默认4.7
        metro_station_keywords: 地铁站搜索关键词，默认"矿大文昌校区地铁站"
        metro_station_city: 地铁站所在城市，默认"徐州"
        max_walking_seconds: 最大步行时长（秒），默认900（15分钟）
        max_distance_meters: 最大直线距离（米），默认350

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

    # 步骤2: 获取目标POI详情并验证评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    hotel_location = poi_detail.location
    print(f"✅ 获取酒店坐标: {hotel_location}")

    # 验证评分
    if not poi_detail.biz_ext or "rating" not in poi_detail.biz_ext:
        print(f"❌ POI没有评分信息")
        return False

    try:
        rating = float(poi_detail.biz_ext["rating"])
    except (ValueError, TypeError):
        print(f"❌ 无法解析评分信息")
        return False

    if rating < min_rating:
        print(f"❌ POI评分{rating}分，低于要求的{min_rating}分")
        return False
    print(f"✅ POI评分{rating}分，符合要求（>= {min_rating}分）")

    # 步骤3: 获取目标地铁站
    text_search_result = maps_text_search(
        keywords=metro_station_keywords,
        city=metro_station_city,
        citylimit="true"
    )
    if text_search_result.error:
        print(f"❌ 搜索地铁站失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False

    metro_station_id = text_search_result.pois[0].id
    print(f"✅ 找到地铁站: {text_search_result.pois[0].name} (ID: {metro_station_id})")

    # 获取地铁站详情
    metro_detail = maps_search_detail(id=metro_station_id)
    if metro_detail.error:
        print(f"❌ 获取地铁站详情失败: {metro_detail.error}")
        return False

    if not metro_detail.location:
        print(f"❌ 地铁站没有location信息")
        return False

    metro_location = metro_detail.location
    print(f"✅ 获取地铁站坐标: {metro_location}")

    # 步骤4: 步行时间验证
    walking_result = maps_walking_by_coordinates(origin=hotel_location, destination=metro_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_seconds:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_seconds}秒（{max_walking_seconds // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_seconds}秒，即{max_walking_seconds // 60}分钟）")

    # 步骤5: 直线距离验证
    distance_result = maps_distance(origins=hotel_location, destination=metro_location)
    if distance_result.error:
        print(f"❌ 计算直线距离失败: {distance_result.error}")
        return False

    if not distance_result.results or len(distance_result.results) == 0:
        print(f"❌ 未找到距离信息")
        return False

    distance_meters = distance_result.results[0].distance_meters
    if distance_meters > max_distance_meters:
        print(f"❌ 直线距离{distance_meters}米，超过{max_distance_meters}米")
        return False
    print(f"✅ 直线距离{distance_meters}米，符合要求（<= {max_distance_meters}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 732.py 文件...\n")
    result = verify_poi(poi_id="B0LGJDJZHI")
    print(f"\n验证结果: {result}")
