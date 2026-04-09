
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边命中验证：调用 maps_around_search(location="113.638441,34.756676", radius="2700", keywords="政务服务中心")，在返回的pois中核对是否包含目标poi_id=B0FFHCMDB5。
2) POI详情与评分验证：调用 maps_search_detail(id="B0FFHCMDB5")，读取其location与biz_ext.rating，验证 rating>=4.0。
3) 到出发地步行/骑行时长验证：
- 用步骤2得到的POI坐标destination=location。
- 调用 maps_walking_by_coordinates(origin="113.638441,34.756676", destination=destination)，验证 total_duration_seconds<=25*60。
- 调用 maps_bicycling_by_coordinates(origin="113.638441,34.756676", destination=destination)，验证 total_duration_seconds<=10*60。
4) 到火车站打车(驾车)时间验证：
- 调用 maps_text_search(keywords="郑州站", city="郑州") 取 poi_id，再 maps_search_detail(id=poi_id) 获取 郑州站坐标 station_loc。
- 调用 maps_driving_by_coordinates(origin=destination, destination=station_loc)，验证 total_duration_seconds<=8*60。
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
    maps_walking_by_coordinates,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "113.638441,34.756676",
    search_radius: int = 2700,
    keywords: str = "政务服务中心",
    min_rating: float = 4.0,
    max_walking_seconds: int = 1500,  # 25 minutes = 1500 seconds
    max_bicycling_seconds: int = 600,  # 10 minutes = 600 seconds
    train_station_address: str = "郑州站",
    train_station_city: str = "郑州",
    max_driving_seconds: int = 480  # 8 minutes = 480 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边命中验证：调用 maps_around_search，在返回的pois中核对是否包含目标poi_id。
    2) POI详情与评分验证：调用 maps_search_detail，读取location与biz_ext.rating，验证 rating>=4.0。
    3) 到出发地步行/骑行时长验证：调用 maps_walking_by_coordinates 和 maps_bicycling_by_coordinates，验证时长符合要求。
    4) 到火车站打车时间验证：调用获取火车站坐标，再调用 maps_driving_by_coordinates，验证时长符合要求。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"113.638441,34.756676"
        search_radius: 搜索半径（米），默认2700
        keywords: 搜索关键词，默认"政务服务中心"
        min_rating: 最低评分，默认4.0
        max_walking_seconds: 最大步行时长（秒），默认1500（25分钟）
        max_bicycling_seconds: 最大骑行时长（秒），默认600（10分钟）
        train_station_address: 火车站地址，默认"郑州站"
        train_station_city: 火车站所在城市，默认"郑州"
        max_driving_seconds: 最大驾车时长（秒），默认480（8分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边命中验证
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

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

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

    # 步骤3: 步行时长验证
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
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

    # 步骤3: 骑行时长验证
    bicycling_result = maps_bicycling_by_coordinates(origin=user_location, destination=poi_location)
    if bicycling_result.error:
        print(f"❌ 计算骑行路线失败: {bicycling_result.error}")
        return False

    if bicycling_result.total_duration_seconds is None:
        print(f"❌ 无法获取骑行时长")
        return False

    bicycling_duration = bicycling_result.total_duration_seconds
    if bicycling_duration > max_bicycling_seconds:
        print(f"❌ 骑行时长{bicycling_duration}秒，超过{max_bicycling_seconds}秒（{max_bicycling_seconds // 60}分钟）")
        return False
    print(f"✅ 骑行时长{bicycling_duration}秒，符合要求（<= {max_bicycling_seconds}秒，即{max_bicycling_seconds // 60}分钟）")

    # 步骤4: 到火车站打车时间验证（用 maps_text_search + maps_search_detail 替代 maps_geo）
    station_text_result = maps_text_search(keywords=train_station_address, city=train_station_city)
    if station_text_result.error:
        print(f"❌ 获取火车站坐标失败: {station_text_result.error}")
        return False

    if not station_text_result.pois or len(station_text_result.pois) == 0:
        print(f"❌ 未找到火车站坐标")
        return False

    first_poi_id = station_text_result.pois[0].id
    station_detail_result = maps_search_detail(id=first_poi_id)
    if station_detail_result.error:
        print(f"❌ 获取坐标失败: {station_detail_result.error}")
        return False
    if not station_detail_result.location:
        print("❌ 未获取到坐标")
        return False

    station_location = station_detail_result.location
    print(f"✅ 获取火车站坐标: {station_location} ({train_station_address})")

    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_seconds:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_seconds}秒（{max_driving_seconds // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_seconds}秒，即{max_driving_seconds // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 707.py 文件...\n")
    result = verify_poi(poi_id="B0FFHCMDB5")
    print(f"\n验证结果: {result}")
