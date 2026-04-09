"""
修改任务指令：你要在附近2公里内找一家药店。你准备骑车过去，所以骑行时间要在10分钟以内。你想让药店离珠村地铁站步行15分钟内能到。另外你还需要药店到珠村地铁站的步行时间，和你从当前位置走到珠村地铁站的步行时间相比，最多只能多9分钟。你说话时会夹杂英语单词，有些不耐烦。
根据给定的验证方法验证POI是否符合要求。
输入：poi_id
输出：bool值（True表示验证通过，False表示验证失败）

验证方法：
1) 半径约束：调用 maps_around_search(location="113.423215,23.121308", radius="2000", keywords="药店")，验证返回pois中包含poi_id=B0LG9HR2GI。
2) 获取目标POI坐标：调用 maps_search_detail(id="B0LG9HR2GI")，读取location="113.423258,23.117534"。
3) 获取"珠村地铁站"坐标：调用 maps_geo(address="珠村地铁站", city="广州")，读取location="113.419463,23.117718"。
4) 骑行时间约束：调用 maps_bicycling_by_coordinates(origin="113.423215,23.121308", destination="113.423258,23.117534")，验证 total_duration_seconds <= 600。
5) 地铁站步行可达约束：调用 maps_walking_by_coordinates(origin="113.423258,23.117534", destination="113.419463,23.117718")，验证 total_duration_seconds <= 900。
6) 时间拓扑差值约束：
   a) 调用 maps_walking_by_coordinates(origin="113.423215,23.121308", destination="113.419463,23.117718") 得到t_user_to_metro。
   b) 复用步骤5得到t_poi_to_metro。
   c) 验证 t_poi_to_metro - t_user_to_metro <= 540(秒)，即最多多9分钟。
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
    maps_bicycling_by_coordinates,
    maps_walking_by_coordinates,
    maps_geo
)
from tools.amap_tools import maps_around_search


def verify_poi(
    poi_id: str,
    user_location: str = "113.423215,23.121308",
    poi_location: str = "113.423258,23.117534",
    station_address: str = "珠村地铁站",
    station_city: str = "广州",
    station_location: str = "113.419463,23.117718",
    search_radius: int = 2000,
    keywords: str = "药店",
    max_bicycling_duration: int = 600,  # 10分钟 = 600秒
    max_walking_duration: int = 900,  # 15分钟 = 900秒
    max_time_difference: int = 540  # 9分钟 = 540秒
) -> bool:
    """
    验证POI是否符合要求
    
    验证步骤：
    1) 半径约束：调用 maps_around_search，验证返回pois中包含目标poi_id。
    2) 获取目标POI坐标：调用 maps_search_detail，读取location。
    3) 获取"珠村地铁站"坐标：调用 maps_geo，读取location。
    4) 骑行时间约束：调用 maps_bicycling_by_coordinates，验证 total_duration_seconds <= 600（10分钟）。
    5) 地铁站步行可达约束：调用 maps_walking_by_coordinates，验证 total_duration_seconds <= 900（15分钟）。
    6) 时间拓扑差值约束：计算两个步行时间的差值，验证差值 <= 540秒（9分钟）。
    
    Args:
        poi_id: POI ID，默认"B0LG9HR2GI"
        user_location: 用户坐标，格式为"经度,纬度"，默认"113.423215,23.121308"
        poi_location: POI坐标，格式为"经度,纬度"，默认"113.423258,23.117534"
        station_address: 地铁站地址，默认"珠村地铁站"
        station_city: 地铁站所在城市，默认"广州"
        station_location: 地铁站坐标，格式为"经度,纬度"，默认"113.419463,23.117718"
        search_radius: 搜索半径（米），默认2000（2公里）
        keywords: 搜索关键词，默认"药店"
        max_bicycling_duration: 最大骑行时长（秒），默认600（10分钟）
        max_walking_duration: 最大步行时长（秒），默认900（15分钟）
        max_time_difference: 最大时间差值（秒），默认540（9分钟）
    
    Returns:
        bool: True表示验证通过，False表示验证失败
    """
    # 步骤1: 半径约束
    print(f"【步骤1】验证半径约束（{search_radius}米范围内，关键词：{keywords}）")
    print("-" * 80)
    around_search_result = maps_around_search(
        location=user_location,
        radius=str(search_radius),
        keywords=keywords
    )
    if around_search_result.error:
        print(f"❌ 搜索周边POI失败: {around_search_result.error}")
        return False
    
    if not around_search_result.pois:
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
    
    # 步骤2: 获取目标POI坐标
    print(f"\n【步骤2】获取目标POI坐标")
    print("-" * 80)
    poi_detail = maps_search_detail(id=poi_id)
    if poi_detail.error:
        print(f"❌ 获取POI详情失败: {poi_detail.error}")
        return False
    
    if poi_detail.location:
        poi_location = poi_detail.location
        print(f"✅ 获取POI坐标: {poi_location} ({poi_detail.name})")
    else:
        print(f"⚠️  POI详情中没有location信息，使用默认坐标: {poi_location}")
    
    # 步骤3: 获取"珠村地铁站"坐标
    print(f"\n【步骤3】获取\"{station_address}\"坐标")
    print("-" * 80)
    geo_result = maps_geo(address=station_address, city=station_city)
    if geo_result.error:
        print(f"❌ 获取地铁站坐标失败: {geo_result.error}")
        return False
    
    if not geo_result.results or len(geo_result.results) == 0:
        print(f"❌ 未找到地铁站地址")
        return False
    
    if geo_result.results[0].location:
        station_location = geo_result.results[0].location
        print(f"✅ 获取地铁站坐标: {station_location} ({station_address})")
    else:
        print(f"⚠️  地铁站地理编码结果中没有location信息，使用默认坐标: {station_location}")
    
    # 步骤4: 骑行时间约束
    print(f"\n【步骤4】验证骑行时间（<={max_bicycling_duration}秒，即{max_bicycling_duration // 60}分钟）")
    print("-" * 80)
    bicycling_result = maps_bicycling_by_coordinates(
        origin=user_location,
        destination=poi_location
    )
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
    
    # 步骤5: 地铁站步行可达约束
    print(f"\n【步骤5】验证地铁站步行可达（<={max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    print("-" * 80)
    walking_result_poi_to_metro = maps_walking_by_coordinates(
        origin=poi_location,
        destination=station_location
    )
    if walking_result_poi_to_metro.error:
        print(f"❌ 计算从POI到地铁站步行路线失败: {walking_result_poi_to_metro.error}")
        return False
    
    if walking_result_poi_to_metro.total_duration_seconds is None:
        print(f"❌ 无法获取从POI到地铁站的步行时长")
        return False
    
    t_poi_to_metro = walking_result_poi_to_metro.total_duration_seconds
    if t_poi_to_metro > max_walking_duration:
        print(f"❌ 从POI到地铁站步行时长{t_poi_to_metro}秒，超过{max_walking_duration}秒（{max_walking_duration // 60}分钟）")
        return False
    print(f"✅ 从POI到地铁站步行时长{t_poi_to_metro}秒，符合要求（<= {max_walking_duration}秒，即{max_walking_duration // 60}分钟）")
    
    # 步骤6: 时间拓扑差值约束
    print(f"\n【步骤6】验证时间拓扑差值（差值<={max_time_difference}秒，即{max_time_difference // 60}分钟）")
    print("-" * 80)
    walking_result_user_to_metro = maps_walking_by_coordinates(
        origin=user_location,
        destination=station_location
    )
    if walking_result_user_to_metro.error:
        print(f"❌ 计算从用户位置到地铁站步行路线失败: {walking_result_user_to_metro.error}")
        return False
    
    if walking_result_user_to_metro.total_duration_seconds is None:
        print(f"❌ 无法获取从用户位置到地铁站的步行时长")
        return False
    
    t_user_to_metro = walking_result_user_to_metro.total_duration_seconds
    print(f"📊 从用户位置到地铁站步行时长: {t_user_to_metro}秒")
    print(f"📊 从POI到地铁站步行时长: {t_poi_to_metro}秒")
    
    time_difference = t_poi_to_metro - t_user_to_metro
    if time_difference > max_time_difference:
        print(f"❌ 时间差值{time_difference}秒，超过{max_time_difference}秒（{max_time_difference // 60}分钟）")
        return False
    print(f"✅ 时间差值{time_difference}秒，符合要求（<= {max_time_difference}秒，即{max_time_difference // 60}分钟）")
    
    print(f"\n✅ 所有验证通过！")
    return True


if __name__ == "__main__":
    # 测试用例
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python 588.py <poi_id> [user_location] [poi_location]")
        print("示例: python 588.py B0LG9HR2GI")
        print("示例: python 588.py B0LG9HR2GI 113.423215,23.121308")
        print("示例: python 588.py B0LG9HR2GI 113.423215,23.121308 113.423258,23.117534")
        print("未传参，使用示例默认值运行。")
        poi_id = "B0LG9HR2GI"
        user_location = "113.423215,23.121308"
    else:
        poi_id = sys.argv[1]
        user_location = sys.argv[2] if len(sys.argv) > 2 else "113.423215,23.121308"
        poi_location = sys.argv[3] if len(sys.argv) > 3 else "113.423258,23.117534"
        

    print(f"开始验证POI: {poi_id}")
    print(f"用户坐标: {user_location}")
    print(f"POI坐标: {poi_location}")
    print("=" * 80)
    
    result = verify_poi(poi_id, user_location=user_location, poi_location=poi_location)
    
    print("=" * 80)
    print(f"验证结果: {'通过' if result else '失败'}")
