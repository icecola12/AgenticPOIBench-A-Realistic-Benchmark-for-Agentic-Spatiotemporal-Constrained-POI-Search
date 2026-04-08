
"""
修改任务指令：你要找一个附近3公里内的医院，步行过去别超过20分钟。你从医院离开之后还要赶地铁去见人，所以医院周边300米内必须有地铁站，并且从医院走到那个地铁站的步行时间不要超过15分钟。你依赖心强，希望智能体能为自己处理和决定一切。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
我将按照四个步骤进行验证：
1) 周边候选集验证：调用 maps_around_search，参数 location=118.133229,24.499832 radius=3000 keywords=医院，验证返回的pois数量>=8，且目标poi_id=B0K1PAC8YG 在pois列表中。
2) 目标POI信息获取：对poi_id=B0K1PAC8YG 调用 maps_search_detail 获取其location与基础信息。
3) 用户步行可达性验证：调用 maps_walking_by_coordinates，参数 origin=118.133229,24.499832 destination=目标POI的location；验证 total_duration_seconds <= 1200（20分钟）。
4) 地铁站邻近与步行时间验证：以目标POI的location为中心调用 maps_around_search，参数 radius=300 keywords=地铁站，验证pois数量>=1；选取其中最近的一个地铁站POI的location，调用 maps_walking_by_coordinates( origin=目标POI.location, destination=地铁站.location )，验证 total_duration_seconds <= 900（15分钟）。
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
    user_location: str = "118.133229,24.499832",
    search_radius: int = 3000,  # 3km
    keywords: str = "医院",
    min_poi_count: int = 8,
    max_walking_duration_to_poi: int = 1200,  # 20 minutes = 1200 seconds
    metro_search_radius: int = 300,  # 300 meters
    metro_keywords: str = "地铁站",
    max_walking_duration_to_metro: int = 900  # 15 minutes = 900 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 周边候选集验证：验证返回的pois数量>=8，且目标poi_id在pois列表中
    2) 目标POI信息获取：获取其location与基础信息
    3) 用户步行可达性验证：验证 total_duration_seconds <= 1200（20分钟）
    4) 地铁站邻近与步行时间验证：验证pois数量>=1，验证 total_duration_seconds <= 900（15分钟）

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"118.133229,24.499832"
        search_radius: 搜索半径（米），默认3000（3公里）
        keywords: 搜索关键词，默认"医院"
        min_poi_count: 最少POI数量，默认8
        max_walking_duration_to_poi: 到POI的最大步行时长（秒），默认1200（20分钟）
        metro_search_radius: 地铁站搜索半径（米），默认300
        metro_keywords: 地铁站搜索关键词，默认"地铁站"
        max_walking_duration_to_metro: 到地铁站的最大步行时长（秒），默认900（15分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 周边候选集验证（附近3公里内的医院）
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

    # 步骤2: 目标POI信息获取
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 步骤3: 用户步行可达性验证（<= 20分钟）
    walking_to_poi_result = maps_walking_by_coordinates(origin=user_location, destination=poi_location)
    if walking_to_poi_result.error:
        print(f"❌ 计算到POI步行路线失败: {walking_to_poi_result.error}")
        return False

    if walking_to_poi_result.total_duration_seconds is None:
        print(f"❌ 无法获取到POI步行时长")
        return False

    walking_to_poi_duration = walking_to_poi_result.total_duration_seconds
    if walking_to_poi_duration > max_walking_duration_to_poi:
        print(f"❌ 到POI步行时长{walking_to_poi_duration}秒，超过{max_walking_duration_to_poi}秒（{max_walking_duration_to_poi // 60}分钟）")
        return False
    print(f"✅ 到POI步行时长{walking_to_poi_duration}秒，符合要求（<= {max_walking_duration_to_poi}秒，即{max_walking_duration_to_poi // 60}分钟）")

    # 步骤4: 地铁站邻近与步行时间验证
    # 搜索POI周边300米内的地铁站
    metro_search_result = maps_around_search(
        location=poi_location,
        radius=str(metro_search_radius),
        keywords=metro_keywords
    )
    if metro_search_result.error:
        print(f"❌ 搜索周边地铁站失败: {metro_search_result.error}")
        return False

    if not metro_search_result.pois or len(metro_search_result.pois) == 0:
        print(f"❌ {metro_search_radius}米范围内未找到地铁站")
        return False

    metro_count = len(metro_search_result.pois)
    print(f"✅ {metro_search_radius}米范围内找到{metro_count}个地铁站")

    # 选取第一个地铁站（最近的）
    nearest_metro = metro_search_result.pois[0]
    print(f"✅ 选取最近的地铁站: {nearest_metro.name} (ID: {nearest_metro.id})")

    # 获取地铁站详细坐标
    metro_detail = maps_search_detail(id=nearest_metro.id)
    if metro_detail.error:
        print(f"❌ 获取地铁站详情失败: {metro_detail.error}")
        return False

    if not metro_detail.location:
        print(f"❌ 地铁站没有location信息")
        return False

    metro_location = metro_detail.location
    print(f"✅ 获取地铁站坐标: {metro_location}")

    # 验证从POI到地铁站的步行时间（<= 15分钟）
    walking_to_metro_result = maps_walking_by_coordinates(origin=poi_location, destination=metro_location)
    if walking_to_metro_result.error:
        print(f"❌ 计算到地铁站步行路线失败: {walking_to_metro_result.error}")
        return False

    if walking_to_metro_result.total_duration_seconds is None:
        print(f"❌ 无法获取到地铁站步行时长")
        return False

    walking_to_metro_duration = walking_to_metro_result.total_duration_seconds
    if walking_to_metro_duration > max_walking_duration_to_metro:
        print(f"❌ 到地铁站步行时长{walking_to_metro_duration}秒，超过{max_walking_duration_to_metro}秒（{max_walking_duration_to_metro // 60}分钟）")
        return False
    print(f"✅ 到地铁站步行时长{walking_to_metro_duration}秒，符合要求（<= {max_walking_duration_to_metro}秒，即{max_walking_duration_to_metro // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 618.py 文件...\n")
    result = verify_poi(poi_id="B0K1PAC8YG")
    print(f"\n验证结果: {result}")
