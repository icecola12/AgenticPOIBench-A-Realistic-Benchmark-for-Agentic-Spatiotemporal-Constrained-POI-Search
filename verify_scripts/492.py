"""
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 用 maps_around_search(location=115.938051,28.694744 radius=2000 keywords=银行) 验证 target_poi_id 在返回列表内，确保银行在2km范围内。
2) 用 maps_text_search(keywords=火炬广场地铁站, city=南昌) 拿到 poi_id，再用 maps_search_detail(poi_id) 获取地铁站坐标 metro_loc=115.949586,28.688182。
3) 用 maps_search_detail(id=B0FFFGX6QO) 获取银行坐标 bank_loc=115.936382,28.690326。
4) 用 maps_walking_by_coordinates(origin=115.938051,28.694744 destination=bank_loc) 得到 t_user_to_bank=347秒。
5) 用 maps_walking_by_coordinates(origin=metro_loc destination=bank_loc) 得到 t_metro_to_bank=1119秒。
6) 验证：t_metro_to_bank <= 1200秒(20分钟)；且 (t_metro_to_bank - t_user_to_bank) >= 300秒(5分钟)。本POI计算差值=1119-347=772秒，满足。
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
    maps_walking_by_coordinates
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "115.938051,28.694744",
    search_radius: int = 2000,  # 2km
    keywords: str = "银行",
    metro_address: str = "火炬广场地铁站",
    metro_city: str = "南昌",
    max_metro_to_bank_duration: int = 1200,  # 20 minutes = 1200 seconds
    min_time_difference: int = 300  # 5 minutes = 300 seconds
) -> bool:
    """
    验证POI是否符合要求

    验证步骤：
    1) 用 maps_around_search 验证 target_poi_id 在返回列表内，确保银行在2km范围内。
    2) 用 maps_text_search + maps_search_detail 获取地铁站坐标。
    3) 用 maps_search_detail 获取银行坐标。
    4) 用 maps_walking_by_coordinates 得到用户到银行的步行时间。
    5) 用 maps_walking_by_coordinates 得到地铁站到银行的步行时间。
    6) 验证：t_metro_to_bank <= 1200秒(20分钟)；且 (t_metro_to_bank - t_user_to_bank) >= 300秒(5分钟)。

    Args:
        poi_id: POI ID
        user_location: 用户坐标，格式为"经度,纬度"，默认"115.938051,28.694744"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"银行"
        metro_address: 地铁站地址，默认"火炬广场地铁站"
        metro_city: 地铁站所在城市，默认"南昌"
        max_metro_to_bank_duration: 地铁站到银行的最大步行时长（秒），默认1200（20分钟）
        min_time_difference: 地铁站到银行与用户到银行的最小时间差（秒），默认300（5分钟）

    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 验证银行在2km范围内
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

    # 步骤2: 获取地铁站坐标
    text_search_result = maps_text_search(keywords=metro_address, city=metro_city)
    if text_search_result.error:
        print(f"❌ 获取地铁站坐标失败: {text_search_result.error}")
        return False

    if not text_search_result.pois or len(text_search_result.pois) == 0:
        print(f"❌ 未找到地铁站坐标")
        return False

    first_poi_id = text_search_result.pois[0].id
    detail_result = maps_search_detail(id=first_poi_id)
    if detail_result.error:
        print(f"❌ 获取地铁站详情失败: {detail_result.error}")
        return False
    if not detail_result.location:
        print(f"❌ 地铁站没有location信息")
        return False
    metro_location = detail_result.location
    print(f"✅ 获取地铁站坐标: {metro_location} ({metro_address})")

    # 步骤3: 获取银行坐标
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False

    if not poi_detail.location:
        print(f"❌ POI没有location信息")
        return False

    bank_location = poi_detail.location
    print(f"✅ 获取银行坐标: {bank_location}")

    # 步骤4: 计算用户到银行的步行时间
    walking_user_to_bank = maps_walking_by_coordinates(origin=user_location, destination=bank_location)
    if walking_user_to_bank.error:
        print(f"❌ 计算用户到银行的步行路线失败: {walking_user_to_bank.error}")
        return False

    if walking_user_to_bank.total_duration_seconds is None:
        print(f"❌ 无法获取用户到银行的步行时长")
        return False

    t_user_to_bank = walking_user_to_bank.total_duration_seconds
    print(f"✅ 用户到银行步行时长: {t_user_to_bank}秒")

    # 步骤5: 计算地铁站到银行的步行时间
    walking_metro_to_bank = maps_walking_by_coordinates(origin=metro_location, destination=bank_location)
    if walking_metro_to_bank.error:
        print(f"❌ 计算地铁站到银行的步行路线失败: {walking_metro_to_bank.error}")
        return False

    if walking_metro_to_bank.total_duration_seconds is None:
        print(f"❌ 无法获取地铁站到银行的步行时长")
        return False

    t_metro_to_bank = walking_metro_to_bank.total_duration_seconds
    print(f"✅ 地铁站到银行步行时长: {t_metro_to_bank}秒")

    # 步骤6: 验证时间约束
    # 验证1: t_metro_to_bank <= 1200秒(20分钟)
    if t_metro_to_bank > max_metro_to_bank_duration:
        print(f"❌ 地铁站到银行步行时长{t_metro_to_bank}秒，超过{max_metro_to_bank_duration}秒（{max_metro_to_bank_duration // 60}分钟）")
        return False
    print(f"✅ 地铁站到银行步行时长{t_metro_to_bank}秒，符合要求（<= {max_metro_to_bank_duration}秒，即{max_metro_to_bank_duration // 60}分钟）")

    # 验证2: (t_metro_to_bank - t_user_to_bank) >= 300秒(5分钟)
    time_difference = t_metro_to_bank - t_user_to_bank
    if time_difference < min_time_difference:
        print(f"❌ 时间差{time_difference}秒，小于{min_time_difference}秒（{min_time_difference // 60}分钟）")
        return False
    print(f"✅ 时间差{time_difference}秒，符合要求（>= {min_time_difference}秒，即{min_time_difference // 60}分钟）")

    print(f"✅ 所有验证通过！")
    return True



if __name__ == "__main__":
    print("开始验证 492.py 文件...\n")
    result = verify_poi(poi_id="B0FFFGX6QO")
    print(f"\n验证结果: {result}")

