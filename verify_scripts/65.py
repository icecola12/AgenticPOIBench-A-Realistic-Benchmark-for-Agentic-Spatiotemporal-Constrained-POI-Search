
"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 距离与候选集验证（附近2.5km餐厅）
- 调用 maps_around_search({location: '117.219625,39.050582', radius: '2500', keywords: '餐厅'})。
- 验证返回的 pois 数量 > 8。
- 验证目标 poi_id = 'B0FFG8B0X1' 出现在 pois 列表中（满足"附近2.5km内找餐厅"）。

2) 餐厅自身信息验证（评分）
- 调用 maps_search_detail({id: 'B0FFG8B0X1'})。
- 从返回的 biz_ext.rating 读取评分，验证 rating >= 4.7。

3) 从用户位置到餐厅的步行时间验证
- 取步骤2中返回的餐厅坐标 destination = location。
- 调用 maps_walking_by_coordinates({origin: '117.219625,39.050582', destination}) 得到 total_duration_seconds。
- 验证 total_duration_seconds <= 1320（22分钟）。

4) 从用户位置到餐厅的骑行时间验证 + 周边建行验证
- 调用 maps_bicycling_by_coordinates({origin: '117.219625,39.050582', destination}) 得到 total_duration_seconds。
- 验证 total_duration_seconds <= 480（8分钟）。
- 以餐厅坐标为中心，调用 maps_around_search({location: destination, radius: '500', keywords: '中国建设银行'})。
- 验证返回 pois 非空且长度 >= 1（满足"餐厅周边500米内有中国建设银行网点"）。
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
    user_location: str = "117.219625,39.050582",
    search_radius: int = 2500,  # 2.5km
    keywords: str = "餐厅",
    min_poi_count: int = 8,
    min_rating: float = 4.7,
    max_walking_duration: int = 1320,  # 22 minutes = 1320 seconds
    max_bicycling_duration: int = 480,  # 8 minutes = 480 seconds
    bank_search_radius: int = 500,  # 500 meters
    bank_keywords: str = "中国建设银行"
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 距离与候选集验证（附近2.5km餐厅）：验证返回的 pois 数量 > 8，验证目标 poi_id 出现在 pois 列表中
    2) 餐厅自身信息验证（评分）：验证 rating >= 4.7
    3) 从用户位置到餐厅的步行时间验证：验证 total_duration_seconds <= 1320（22分钟）
    4) 从用户位置到餐厅的骑行时间验证 + 周边建行验证：验证 total_duration_seconds <= 480（8分钟），验证返回 pois 非空且长度 >= 1

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"117.219625,39.050582"
        search_radius: 搜索半径（米），默认2500（2.5公里）
        keywords: 搜索关键词，默认"餐厅"
        min_poi_count: 最少POI数量，默认8
        min_rating: 最低评分，默认4.7
        max_walking_duration: 最大步行时长（秒），默认1320（22分钟）
        max_bicycling_duration: 最大骑行时长（秒），默认480（8分钟）
        bank_search_radius: 银行搜索半径（米），默认500
        bank_keywords: 银行搜索关键词，默认"中国建设银行"

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 距离与候选集验证（附近2.5km内的餐厅）
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

    # 检查返回POI数量是否>8
    poi_count = len(around_search_result.pois)
    if poi_count <= min_poi_count:
        print(f"❌ 返回POI数量{poi_count}个，不大于{min_poi_count}个")
        return False
    print(f"✅ 返回POI数量{poi_count}个，符合要求（> {min_poi_count}个）")

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

    # 步骤2: 餐厅自身信息验证（评分）
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    poi_location = poi_detail.location
    print(f"✅ 获取POI坐标: {poi_location}")

    # 验证评分（rating >= 4.7）
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

    # 步骤3: 从用户位置到餐厅的步行时间验证（<= 22分钟）
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

    # 步骤4: 从用户位置到餐厅的骑行时间验证 + 周边建行验证
    # 4.1 骑行时间验证（<= 8分钟）
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

    # 4.2 周边建行验证（500米内有中国建设银行）
    bank_search_result = maps_around_search(
        location=poi_location,
        radius=str(bank_search_radius),
        keywords=bank_keywords
    )
    if bank_search_result.error:
        print(f"❌ 搜索周边{bank_keywords}失败: {bank_search_result.error}")
        return False

    if not bank_search_result.pois or len(bank_search_result.pois) == 0:
        print(f"❌ {bank_search_radius}米范围内未找到{bank_keywords}")
        return False

    bank_count = len(bank_search_result.pois)
    print(f"✅ {bank_search_radius}米范围内找到{bank_count}个{bank_keywords}网点，符合要求")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 634.py 文件...\n")
    result = verify_poi(poi_id="B0FFG8B0X1")
    print(f"\n验证结果: {result}")
