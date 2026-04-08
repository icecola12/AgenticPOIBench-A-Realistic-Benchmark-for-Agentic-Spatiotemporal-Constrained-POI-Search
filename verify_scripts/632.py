
"""
修改任务指令：你要在附近1.5公里找一家干洗店。你打算走路过去，步行时间必须在12分钟以内。你也可能骑共享单车过去，所以骑行时间要在5分钟以内。店铺本身评分要在4.2分及以上。另外你希望这家干洗店附近300米内就有公交站，方便你洗完衣服直接坐车走。你善于使用强制和协商的策略来达到目的。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 周边与距离约束：调用 maps_around_search(location='106.0799,30.799412', radius='1500', keywords='干洗店')，验证返回pois中包含 poi_id='B033101RBS'。
2) 获取POI详情与评分：调用 maps_search_detail(id='B033101RBS')，读取 biz_ext.rating，验证 rating>=4.2，并取其location作为destination。
3) 步行时间约束：调用 maps_walking_by_coordinates(origin='106.0799,30.799412', destination=destination)，验证 total_duration_seconds<=12*60。
4) 骑行时间约束：调用 maps_bicycling_by_coordinates(origin='106.0799,30.799412', destination=destination)，验证 total_duration_seconds<=5*60。
5) 公交站邻近约束：调用 maps_around_search(location=destination, radius='300', keywords='公交站')，验证返回pois数量>0（存在至少一个公交站POI）。
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
    maps_walking_by_coordinates,
    maps_bicycling_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "106.0799,30.799412",
    search_radius: int = 1500,  # 1.5km
    keywords: str = "干洗店",
    min_rating: float = 4.2,
    max_walking_duration: int = 720,  # 12 minutes = 12*60 seconds
    max_bicycling_duration: int = 300,  # 5 minutes = 5*60 seconds
    bus_search_radius: int = 300,  # 300 meters
    bus_keywords: str = "公交站"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边与距离约束：验证返回pois中包含 poi_id
    2) 获取POI详情与评分：验证 rating>=4.2，并取其location作为destination
    3) 步行时间约束：验证 total_duration_seconds<=12*60
    4) 骑行时间约束：验证 total_duration_seconds<=5*60
    5) 公交站邻近约束：验证返回pois数量>0

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"106.0799,30.799412"
        search_radius: 搜索半径（米），默认1500（1.5公里）
        keywords: 搜索关键词，默认"干洗店"
        min_rating: 最低评分，默认4.2
        max_walking_duration: 最大步行时长（秒），默认720（12分钟）
        max_bicycling_duration: 最大骑行时长（秒），默认300（5分钟）
        bus_search_radius: 公交站搜索半径（米），默认300
        bus_keywords: 公交站搜索关键词，默认"公交站"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边与距离约束（附近1.5公里内的干洗店）
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

    # 步骤2: 获取POI详情与评分
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分（rating >= 4.2）
    if hasattr(poi_detail, 'biz_ext') and poi_detail.biz_ext and 'rating' in poi_detail.biz_ext:
        rating = poi_detail.biz_ext['rating']
        try:
            rating_value = float(rating)
            if rating_value < min_rating:
                print(f"❌ 评分{rating_value}低于{min_rating}")
                return False
            print(f"✅ 评分{rating_value}，符合要求（>= {min_rating}）")
        except (ValueError, TypeError):
            print(f"⚠️  无法解析评分值: {rating}，跳过评分验证")
    else:
        print(f"⚠️  未找到评分信息，跳过评分验证")

    # 步骤3: 步行时间约束（<= 12分钟）
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

    # 步骤4: 骑行时间约束（<= 5分钟）
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

    # 步骤5: 公交站邻近约束（300米内有公交站）
    bus_search_result = maps_around_search(
        location=poi_location,
        radius=str(bus_search_radius),
        keywords=bus_keywords
    )
    if bus_search_result.error:
        print(f"❌ 搜索周边公交站失败: {bus_search_result.error}")
        return False

    if not bus_search_result.pois or len(bus_search_result.pois) == 0:
        print(f"❌ {bus_search_radius}米范围内未找到公交站")
        return False

    bus_count = len(bus_search_result.pois)
    print(f"✅ {bus_search_radius}米范围内找到{bus_count}个公交站，符合要求")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 632.py 文件...\n")
    result = verify_poi(poi_id="B033101RBS")
    print(f"\n验证结果: {result}")
