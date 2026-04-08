
"""
修改任务指令：你要找一个附近2公里的便利店。你准备走过去取点东西，所以步行过去不能超过18分钟。为了方便回程转公交，这家便利店附近400米 内要有公交站。另外这家店的评分要在3.4分及以上。你虽然心情不好，但仍然保持礼貌和独立的姿态。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边可达性：以用户坐标115.071145,35.69492为中心，调用maps_around_search(location='115.071145,35.69492', radius='2000', keywords='便利店')，验证返回pois中包含目标poi_id=B0L14P1AAY。
2) 步行时间约束：对目标poi_id调用maps_search_detail(id='B0L14P1AAY')获取其location；再调用maps_walking_by_coordinates(origin='115.071145,35.69492', destination=目标location)，验证total_duration_seconds <= 1080秒(18分钟)。
3) 公交站距离约束：以目标location为中心调用maps_around_search(location=目标location, radius='400', keywords='公交站')，验证返回pois列表非空（表示400米范围内存在公交站）。
4) 评分约束：对目标poi_id调用maps_search_detail(id='B0L14P1AAY')，读取biz_ext.rating，验证rating >= 3.4。
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
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.071145,35.69492",
    search_radius: int = 2000,  # 2km
    keywords: str = "便利店",
    max_walking_duration: int = 1080,  # 18 minutes = 1080 seconds
    bus_stop_search_radius: int = 400,  # 400m
    bus_stop_keywords: str = "公交站",
    min_rating: float = 3.4
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边可达性：调用maps_around_search，验证返回pois中包含目标poi_id。
    2) 步行时间约束：对目标poi_id调用maps_search_detail获取其location；再调用maps_walking_by_coordinates，验证total_duration_seconds <= 1080秒。
    3) 公交站距离约束：以目标location为中心调用maps_around_search，验证返回pois列表非空。
    4) 评分约束：对目标poi_id调用maps_search_detail，读取biz_ext.rating，验证rating >= 3.4。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.071145,35.69492"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"便利店"
        max_walking_duration: 最大步行时长（秒），默认1080（18分钟）
        bus_stop_search_radius: 公交站搜索半径（米），默认400
        bus_stop_keywords: 公交站搜索关键词，默认"公交站"
        min_rating: 最低评分，默认3.4

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边可达性（2公里内的便利店）
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

    # 步骤3: 步行时间约束（<=18分钟）
    walking_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_result.error:
        print(f"❌ 计算步行路线失败: {walking_result.error}")
        return False

    if walking_result.total_duration_seconds is None:
        print(f"❌ 无法获取步行时长")
        return False

    walking_duration = walking_result.total_duration_seconds
    if walking_duration > max_walking_duration:
        print(f"❌ 步行时长{walking_duration}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 步行时长{walking_duration}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")

    # 步骤4: 公交站距离约束（400米内有公交站）
    bus_stop_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_stop_search_radius),
        keywords=bus_stop_keywords
    )
    if bus_stop_search_result.error:
        print(f"❌ 搜索公交站失败: {bus_stop_search_result.error}")
        return False

    if not bus_stop_search_result.pois or len(bus_stop_search_result.pois) == 0:
        print(f"❌ 便利店附近{bus_stop_search_radius}米内未找到公交站")
        return False

    print(f"✅ 便利店附近{bus_stop_search_radius}米内找到公交站: {bus_stop_search_result.pois[0].name} (共{len(bus_stop_search_result.pois)}个)")

    # 步骤5: 验证评分>=3.4
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

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 734.py 文件...\n")
    result = verify_poi(poi_id="B0L14P1AAY")
    print(f"\n验证结果: {result}")
