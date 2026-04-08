
"""
修改任务指令：你想在附近2公里内找一家酒店，打车过去不超过10分钟。酒店的评分要至少4.7分，而且酒店附近500米内需要有一个地铁站，且直线距离不能超过500米。你善于使用强制和协商的策略来达到目的。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边筛选：调用 maps_around_search，以用户坐标 115.920554,28.719297 为中心、radius=2000、keywords=酒店；验证返回pois中包含目标POI(id=B0IRLUGFCC)。
2) 评分校验：对目标POI调用 maps_search_detail(id=B0IRLUGFCC)，读取 biz_ext.rating，验证 rating>=4.7。
3) 打车时间校验：用 maps_search_detail 获取目标POI坐标destination=115.916435,28.702200；调用 maps_driving_by_coordinates(origin=115.920554,28.719297, destination=115.916435,28.702200)，验证 total_duration_seconds<=600。
4) 地铁站邻近校验：以目标POI坐标 115.916435,28.702200 为中心调用 maps_around_search(radius=500, keywords=地铁站)，确认返回pois非空（例如包含"起凤路(地铁站)"）。然后对每个返回地铁站POI，调用 maps_distance(origins=地铁站location用'|'拼接, destination=酒店location)，取最小distance，验证 min_distance<=500。
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
    maps_driving_by_coordinates,
    maps_distance
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.920554,28.719297",
    search_radius: int = 2000,  # 2km
    keywords: str = "酒店",
    min_rating: float = 4.7,
    max_driving_duration: int = 600,  # 10 minutes = 600 seconds
    subway_search_radius: int = 500,  # 500m
    subway_keywords: str = "地铁站",
    max_distance_to_subway: int = 500  # 500m
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边筛选：调用 maps_around_search，验证返回pois中包含目标POI。
    2) 评分校验：对目标POI调用 maps_search_detail，读取 biz_ext.rating，验证 rating>=4.7。
    3) 打车时间校验：用 maps_search_detail 获取目标POI坐标；调用 maps_driving_by_coordinates，验证 total_duration_seconds<=600。
    4) 地铁站邻近校验：以目标POI坐标为中心调用 maps_around_search，确认返回pois非空。然后对每个返回地铁站POI，调用 maps_distance，取最小distance，验证 min_distance<=500。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.920554,28.719297"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最低评分，默认4.7
        max_driving_duration: 最大驾车时长（秒），默认600（10分钟）
        subway_search_radius: 地铁站搜索半径（米），默认500
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_distance_to_subway: 到地铁站的最大直线距离（米），默认500

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边筛选（2公里内的酒店）
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

    # 步骤3: 验证评分>=4.7
    if not poi_detail.biz_ext:
        print(f"❌ POI没有biz_ext信息")
        return False

    rating = poi_detail.biz_ext.get('rating')
    if rating is None:
        print(f"❌ POI没有rating信息")
        return False

    try:
        rating_value = float(rating)
    except (ValueError, TypeError):
        print(f"❌ 无法解析rating值: {rating}")
        return False

    if rating_value < min_rating:
        print(f"❌ 评分{rating_value}分，低于{min_rating}分")
        return False
    print(f"✅ 评分{rating_value}分，符合要求（>= {min_rating}分）")

    # 步骤4: 打车时间校验（<=10分钟）
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    driving_duration = driving_result.total_duration_seconds
    if driving_duration > max_driving_duration:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    # 步骤5: 搜索酒店附近500米内的地铁站
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 酒店附近{subway_search_radius}米内未找到地铁站")
        return False

    print(f"✅ 酒店附近{subway_search_radius}米内找到{len(subway_search_result.pois)}个地铁站")

    # 步骤6: 计算到每个地铁站的直线距离，找到最小值
    min_distance = float('inf')
    closest_subway = None

    for subway in subway_search_result.pois:
        if not subway.location:
            continue

        distance_result = maps_distance(origins=subway.location, destination=poi_location)
        if distance_result.error:
            continue

        if not distance_result.results or len(distance_result.results) == 0:
            continue

        distance_meters = distance_result.results[0].distance_meters
        # print(f"  - {subway.name}: 直线距离{distance_meters}米")

        if distance_meters < min_distance:
            min_distance = distance_meters
            closest_subway = subway

    if closest_subway is None:
        print(f"❌ 无法计算到地铁站的直线距离")
        return False

    print(f"✅ 找到最近的地铁站: {closest_subway.name}，直线距离{min_distance}米")

    if min_distance > max_distance_to_subway:
        print(f"❌ 到最近地铁站的直线距离{min_distance}米，超过{max_distance_to_subway}米")
        return False

    print(f"✅ 到最近地铁站的直线距离符合要求（<= {max_distance_to_subway}米）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 725.py 文件...\n")
    result = verify_poi(poi_id="B0IRLUGFCC")
    print(f"\n验证结果: {result}")
