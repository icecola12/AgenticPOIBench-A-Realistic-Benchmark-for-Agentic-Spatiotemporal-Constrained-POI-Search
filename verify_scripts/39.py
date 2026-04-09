
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边可达性：调用 maps_around_search(location=用户坐标, radius=1500, keywords='干洗店')，验证返回pois中包含 target_poi_id。
2) 评分约束：调用 maps_search_detail(id=target_poi_id)，读取 biz_ext.rating，验证其为非空且数值>=4.0（若为空/缺失则判失败）。
3) 步行时间约束：调用 maps_walking_by_coordinates(origin=用户坐标, destination=POI.location)，验证 total_duration_seconds<=1500(25分钟)。
4) 步行实际路径距离约束：同第3步，验证 total_distance_meters<=1600。
5) 到火车站驾车时间约束：调用 maps_text_search(keywords='长春站', city='长春') 获取 poi_id，再调用 maps_search_detail(id=poi_id) 获取长春站坐标；再调用 maps_driving_by_coordinates(origin=POI.location, destination=长春站坐标)，验证 total_duration_seconds<=900(15分钟)。
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
    maps_driving_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "125.282863,43.857330",  # 长春市默认坐标（POI附近）
    search_radius: int = 1500,  # 1.5km
    keywords: str = "干洗店",
    min_rating: float = 4.0,
    max_walking_duration: int = 1500,  # 25 minutes = 1500 seconds
    max_walking_distance: int = 1600,  # 1.6km = 1600 meters
    station_address: str = "长春站",
    station_city: str = "长春",
    max_driving_duration: int = 900  # 15 minutes = 900 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边可达性：验证返回pois中包含 target_poi_id
    2) 评分约束：验证rating为非空且数值>=4.0
    3) 步行时间约束：验证步行时长<=25分钟
    4) 步行实际路径距离约束：验证步行距离<=1600米
    5) 到火车站驾车时间约束：验证驾车时长<=15分钟

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"125.324501,43.886841"
        search_radius: 搜索半径（米），默认1500（1.5公里）
        keywords: 搜索关键词，默认"干洗店"
        min_rating: 最低评分，默认4.0
        max_walking_duration: 最大步行时长（秒），默认1500（25分钟）
        max_walking_distance: 最大步行距离（米），默认1600
        station_address: 火车站地址，默认"长春站"
        station_city: 火车站所在城市，默认"长春"
        max_driving_duration: 最大驾车时长（秒），默认900（15分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边可达性（附近1.5公里内的干洗店）
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

    # 步骤2: 评分约束
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分（rating >= 4.0，且不能为空）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = poi_detail.biz_ext['rating']
        if rating is None or rating == '':
            print(f"❌ 评分为空")
            return False
        try:
            rating_value = float(rating)
            if rating_value < min_rating:
                print(f"❌ 评分{rating_value}低于{min_rating}")
                return False
            print(f"✅ 评分{rating_value}，符合要求（>= {min_rating}）")
        except (ValueError, TypeError):
            print(f"❌ 无法解析评分值: {rating}")
            return False
    else:
        print(f"❌ 未找到评分信息")
        return False

    # 步骤3和4: 步行时间和距离约束
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    if walking_result.total_distance_meters is None:
        print(f"❌ 无法获取步行距离")
        return False

    walking_duration = walking_result.total_duration_seconds
    walking_distance = walking_result.total_distance_meters

    # 验证步行时长（<= 25分钟）
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 验证步行距离（<= 1600米）
    if walking_distance > max_walking_distance:
        print(f"❌ 步行距离{walking_distance}米，超过{max_walking_distance}米")
        return False
    print(f"✅ 步行距离{walking_distance}米，符合要求（<= {max_walking_distance}米）")

    # 步骤5: 用 maps_text_search + maps_search_detail 获取长春站坐标，到火车站驾车时间约束
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

    # 验证驾车时间（<= 15分钟）
    driving_result = maps_driving_by_coordinates(origin=poi_location, destination=station_location)
    if driving_result.error:
        print(f"❌ 计算到{station_address}驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取到{station_address}驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 到{station_address}驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 到{station_address}驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 569.py 文件...\n")
    # 注意：需要根据实际测试用例提供正确的 poi_id 和 user_location
    result = verify_poi(poi_id="B0HAMU1LZ9")
    print(f"\n验证结果: {result}")
