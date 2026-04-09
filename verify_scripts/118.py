
"""
修改任务指令：你想找一个附近1公里内的酒店，今晚要临时住一晚并且方便明早通勤。这个酒店在平台上的评分得不低于4.7分。你希望从酒店附近1200米有地铁站，并且步行到最近的地铁站不要超过15分钟。你还要求自己开车从当前位置到酒店的时间不超过6分钟、路程不超过3公里。你情绪化，时而冷静时而愤怒，态度变化快。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离约束：调用 maps_around_search(location=113.634117,34.764156, radius=1000, keywords=酒店)，验证返回pois中包含 target_poi_id=B017319Q88。
2) 评分约束：调用 maps_search_detail(id=B017319Q88)，读取 biz_ext.rating，验证 rating >= 4.7。
3) 驾车时间/距离约束：用 maps_search_detail 获取酒店坐标destination=113.634185,34.756425；调用 maps_driving_by_coordinates(origin=113.634117,34.764156, destination=113.634185,34.756425)，验证 total_duration_seconds <= 360 且 total_distance_meters <= 3000。
4) 地铁步行时间约束：以酒店坐标为中心调用 maps_around_search(location=113.634185,34.756425, radius=1200, keywords=地铁站) 获取候选地铁站；分别对每个候选地铁站调用 maps_walking_by_coordinates(origin=酒店坐标, destination=地铁站坐标)，取最小 total_duration_seconds，验证最小值 <= 900。
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
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "113.634117,34.764156",
    search_radius: int = 1000,  # 1km
    keywords: str = "酒店",
    min_rating: float = 4.7,
    max_driving_duration: int = 360,  # 6 minutes = 360 seconds
    max_driving_distance: int = 3000,  # 3km = 3000 meters
    subway_search_radius: int = 1200,  # 1200m
    subway_keywords: str = "地铁站",
    max_walking_duration_to_subway: int = 900  # 15 minutes = 900 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束：调用 maps_around_search，验证返回pois中包含 target_poi_id。
    2) 评分约束：调用 maps_search_detail，读取 biz_ext.rating，验证 rating >= 4.7。
    3) 驾车时间/距离约束：用 maps_search_detail 获取酒店坐标；调用 maps_driving_by_coordinates，验证 total_duration_seconds <= 360 且 total_distance_meters <= 3000。
    4) 地铁步行时间约束：以酒店坐标为中心调用 maps_around_search 获取候选地铁站；分别对每个候选地铁站调用 maps_walking_by_coordinates，取最小 total_duration_seconds，验证最小值 <= 900。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"113.634117,34.764156"
        search_radius: 搜索半径（米），默认1000（1公里）
        keywords: 搜索关键词，默认"酒店"
        min_rating: 最低评分，默认4.7
        max_driving_duration: 最大驾车时长（秒），默认360（6分钟）
        max_driving_distance: 最大驾车距离（米），默认3000（3公里）
        subway_search_radius: 地铁站搜索半径（米），默认1200
        subway_keywords: 地铁站搜索关键词，默认"地铁站"
        max_walking_duration_to_subway: 到地铁站的最大步行时长（秒），默认900（15分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（1公里内的酒店）
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

    # 步骤4: 驾车时间/距离约束（<=6分钟且<=3公里）
    driving_result = maps_driving_by_coordinates(origin=user_location, destination=poi_location)
    if driving_result.error:
        print(f"❌ 计算驾车路线失败: {driving_result.error}")
        return False

    if driving_result.total_duration_seconds is None:
        print(f"❌ 无法获取驾车时长")
        return False

    if driving_result.total_distance_meters is None:
        print(f"❌ 无法获取驾车距离")
        return False

    driving_duration = driving_result.total_duration_seconds
    driving_distance = driving_result.total_distance_meters

    if driving_duration > max_driving_duration:
        print(f"❌ 驾车时长{driving_duration}秒，超过{max_driving_duration}秒（{max_driving_duration // 60}分钟）")
        return False
    print(f"✅ 驾车时长{driving_duration}秒，符合要求（<= {max_driving_duration}秒，即{max_driving_duration // 60}分钟）")

    if driving_distance > max_driving_distance:
        print(f"❌ 驾车距离{driving_distance}米，超过{max_driving_distance}米（{max_driving_distance / 1000}公里）")
        return False
    print(f"✅ 驾车距离{driving_distance}米，符合要求（<= {max_driving_distance}米，即{max_driving_distance / 1000}公里）")

    # 步骤5: 搜索酒店附近1200米内的地铁站
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

    # 步骤6: 找到步行时间最短的地铁站
    closest_subway = None
    min_walking_duration = float('inf')

    for subway in subway_search_result.pois:
        if not subway.location:
            continue

        walking_result_to_subway = maps_walking_by_coordinates(origin=poi_location, destination=subway.location)
        if walking_result_to_subway.error or walking_result_to_subway.total_duration_seconds is None:
            continue

        walking_duration = walking_result_to_subway.total_duration_seconds
        # print(f"  - {subway.name}: 步行时长{walking_duration}秒（{walking_duration // 60}分钟）")

        if walking_duration < min_walking_duration:
            min_walking_duration = walking_duration
            closest_subway = subway

    if closest_subway is None:
        print(f"❌ 无法找到可步行到达的地铁站")
        return False

    print(f"✅ 找到最近的地铁站: {closest_subway.name}，步行时长{min_walking_duration}秒（{min_walking_duration // 60}分钟）")

    if min_walking_duration > max_walking_duration_to_subway:
        print(f"❌ 到最近地铁站的步行时长{min_walking_duration}秒，超过{max_walking_duration_to_subway}秒（{max_walking_duration_to_subway // 60}分钟）")
        return False

    print(f"✅ 到最近地铁站的步行时长符合要求（<= {max_walking_duration_to_subway}秒，即{max_walking_duration_to_subway // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 731.py 文件...\n")
    result = verify_poi(poi_id="B017319Q88")
    print(f"\n验证结果: {result}")
