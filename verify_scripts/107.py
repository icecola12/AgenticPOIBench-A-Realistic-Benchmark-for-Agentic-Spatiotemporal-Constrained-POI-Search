
"""
修改任务指令：你要在附近2公里内找一个商场，步行过去不超过20分钟。这个商场的评分要达到4.7分及以上。另外你希望它离附近最近的地铁站距离不超过700米。你一个喜欢开玩笑的有趣的人，试图让对话变得轻松。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 调用 maps_around_search(location=用户坐标, radius=2000, keywords=商场)，验证返回的pois中包含 target_poi_id。
2) 调用 maps_search_detail(id=target_poi_id)，读取 biz_ext.rating，验证评分>=4.7，并获取POI坐标destination。
3) 调用 maps_walking_by_coordinates(origin=用户坐标, destination=POI坐标destination)，验证 total_duration_seconds<=1200（20分钟）。
4) 调用 maps_around_search(location=POI坐标destination, radius=700, keywords=地铁站) 验证返回中的pois非空，确保地铁站在700米范围内。
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
    user_location: str = "108.914083,34.234405",
    max_walking_duration: int = 1200,  # 20 minutes = 1200 seconds
    search_radius: int = 2000,  # 2km
    keywords: str = "商场",
    min_rating: float = 4.7,
    subway_search_radius: int = 700,
    subway_keywords: str = "地铁站"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离约束（附近2公里）：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 评分约束（>=4.7分）：调用 maps_search_detail，读取 biz_ext.rating，验证评分>=4.7，并获取POI坐标。
    3) 步行时间<=20分钟：调用 maps_walking_by_coordinates，验证 total_duration_seconds<=1200。
    4) 周边700米内有地铁站：调用 maps_around_search，验证返回pois非空。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"116.397428,39.90923"
        max_walking_duration: 最大步行时长（秒），默认1200（20分钟）
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"商场"
        min_rating: 最低评分，默认4.7
        subway_search_radius: 地铁站搜索半径（米），默认700
        subway_keywords: 地铁站搜索关键词，默认"地铁站"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离约束（附近2公里）
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

    # 步骤3: 步行时间<=20分钟
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

    # 步骤4: 周边700米内有地铁站
    subway_search_result = maps_around_search(
        location=poi_location,
        radius=str(subway_search_radius),
        keywords=subway_keywords
    )
    if subway_search_result.error:
        print(f"❌ 搜索地铁站失败: {subway_search_result.error}")
        return False

    if not subway_search_result.pois or len(subway_search_result.pois) == 0:
        print(f"❌ 未找到地铁站")
        return False

    print(f"✅ 找到地铁站: {subway_search_result.pois[0].name} (共{len(subway_search_result.pois)}个)")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 716.py 文件...\n")
    result = verify_poi(poi_id="B0FFGTHGDL")
    print(f"\n验证结果: {result}")
